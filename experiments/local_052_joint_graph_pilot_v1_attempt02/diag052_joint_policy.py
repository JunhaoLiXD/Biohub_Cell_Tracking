"""GT-blind fixed-node joint association policy. No scorer or label imports."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
import gzip
import json
from pathlib import Path
import sys

import numpy as np

# Optional project-local dependency; no global environment mutation is needed.
_deps = Path(__file__).resolve().parents[1] / '.private/runtime/graph_pilot'
if _deps.exists():
    sys.path.insert(0, str(_deps))
from scipy.optimize import linear_sum_assignment

SCALE = np.array([1.625, .40625, .40625])
STAGES = ['raw_post_ilp', 'distance_filtered', 'motion_relinked', 'degree_repaired',
          'gap1', 'gap2', 'safe_divisions', 'geometry_and_isolated', 'short_track_filtered']


def persistent_original_ids(ids, coords, final_nodes, stage_nodes):
    """A numeric ID alone does not prove identity after recovery ID reuse."""
    valid = {int(n) for n, xyz in zip(ids, coords)
             if n in final_nodes and int(xyz[0]) == int(final_nodes[n][0])}
    original_frame = {int(n): int(xyz[0]) for n, xyz in zip(ids, coords)}
    for nodes in stage_nodes:
        valid = {n for n in valid if n in nodes and int(nodes[n]['t']) == original_frame[n]}
    return valid


@dataclass(frozen=True)
class Candidate:
    probability: float
    threshold: float
    cosine: float
    motion: float | None
    unique_best: bool


def adjacency(edges):
    incoming, outgoing = defaultdict(set), defaultdict(set)
    for s, t in edges:
        outgoing[s].add(t)
        incoming[t].add(s)
    return incoming, outgoing


def motion_features(nodes, edges):
    """Require unbranched t-2,t-1,t and t+1,t+2 on the frozen parent."""
    inc, out = adjacency(edges)
    pos = {n: np.asarray(v[1:], dtype=float) * SCALE for n, v in nodes.items()}
    past_velocity, future_velocity = {}, {}
    for n in sorted(nodes):
        if len(inc[n]) == 1:
            p = next(iter(inc[n]))
            if len(out[p]) == 1 and len(inc[p]) == 1:
                pp = next(iter(inc[p]))
                if len(out[pp]) == 1:
                    past_velocity[n] = (pos[n] - pos[pp]) / 2
        if len(out[n]) == 1:
            f = next(iter(out[n]))
            if len(inc[f]) == 1:
                future_velocity[n] = pos[f] - pos[n]
    return pos, past_velocity, future_velocity


def load_candidates(folder, nodes, edges, params):
    """Read every frame and source. GT/matching files are never opened here."""
    with np.load(folder / 'pre_ilp_nodes.npz', allow_pickle=False) as reg:
        ids = reg['graph_node_ids']
        coords = reg['coords']
    stages = [dict(json.loads(gzip.decompress((folder/(s+'.json.gz')).read_bytes()))['nodes'])
              for s in STAGES]
    persistent = persistent_original_ids(ids, coords, nodes, stages)
    pos, past, future = motion_features(nodes, edges)
    node_ids = np.array(sorted(persistent), dtype=np.int64)
    result = {}
    counts = Counter()
    counts['persistent_original_nodes'] = len(persistent)
    counts['final_ids_rejected_for_identity'] = len(set(map(int, ids)) & nodes.keys()) - len(persistent)
    for frame in range(99):
        with np.load(folder / f'pair_{frame:03d}_{frame+1:03d}.npz', allow_pickle=False) as z:
            ij = z['pair_indices']
            src = ids[z['source_ids']][ij[:, 0]]
            tgt = ids[z['target_ids']][ij[:, 1]]
            prob = z['probabilities']
            counts['exported_pairs'] += len(ij)
            rows = np.flatnonzero(np.isin(src, node_ids) & np.isin(tgt, node_ids))
            counts['final_node_pairs'] += len(rows)
            order = rows[np.lexsort((tgt[rows], -prob[rows], src[rows]))]
            by_source = defaultdict(list)
            for row in order:
                by_source[int(src[row])].append(int(row))
            counts['sources_with_candidates'] += len(by_source)
            kept = []
            unique = set()
            for source, group in by_source.items():
                if len(group) == 1 or prob[group[0]] > prob[group[1]]:
                    unique.add(group[0])
                kept.extend(r for i, r in enumerate(group)
                            if i < params['top_k'] or (source, int(tgt[r])) in edges)
            kept = np.asarray(kept, dtype=int)
            if not len(kept):
                continue
            a = z['secondary_source_features'][ij[kept, 0]]
            b = z['secondary_target_features'][ij[kept, 1]]
            cosines = np.sum(a * b, axis=1) / np.maximum(
                np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-12)
            threshold = float(z['threshold'])
            for row, cosine in zip(kept, cosines):
                s, t = int(src[row]), int(tgt[row])
                residual = None
                if s in past and t in future:
                    displacement = pos[t] - pos[s]
                    residual = float((np.linalg.norm(displacement - past[s]) +
                                      np.linalg.norm(displacement - future[t])) / 2)
                    counts['complete_context_pairs'] += 1
                assert nodes[t][0] == nodes[s][0] + 1
                assert (s, t) not in result
                result[s, t] = Candidate(float(prob[row]), threshold, float(cosine),
                                         residual, int(row) in unique)
    counts['candidate_pairs'] = len(result)
    return result, dict(counts)


def logit(value):
    value = min(max(value, 1e-6), 1-1e-6)
    return math.log(value / (1-value))


def utility(c, arm, params):
    value = max(0.0, logit(c.probability) - logit(c.threshold))
    if arm == 'context' and c.motion is not None:
        value += params['appearance_weight'] * c.cosine
        value -= params['motion_weight'] * min(c.motion / params['motion_scale_um'],
                                               params['motion_cap'])
    assert math.isfinite(value)
    return value


def protected_edges(edges, candidates, params):
    _, outgoing = adjacency(edges)
    fork_nodes = {s for s, targets in outgoing.items() if len(targets) == 2}
    fork_nodes |= {t for s in list(fork_nodes) for t in outgoing[s]}
    protected = set()
    for e in edges:
        c = candidates.get(e)
        if (e[0] in fork_nodes or e[1] in fork_nodes or c is None or
                (c.probability >= params['protected_probability'] and c.unique_best)):
            protected.add(e)
    return protected, fork_nodes


def difference_components(added, removed):
    """Components in bipartite slot space, not full temporal graph space."""
    adj = defaultdict(set)
    incident = defaultdict(set)
    for s, t in added | removed:
        a, b = ('s', s), ('t', t)
        adj[a].add(b)
        adj[b].add(a)
        incident[a].add((s, t))
        incident[b].add((s, t))
    seen = set()
    for root in sorted(adj):
        if root in seen:
            continue
        stack, component = [root], set()
        seen.add(root)
        while stack:
            n = stack.pop()
            component.update(incident[n])
            for nxt in adj[n]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        yield component & added, component & removed


def validate_graph(nodes, edges):
    assert all(s in nodes and t in nodes and nodes[t][0] == nodes[s][0] + 1 for s, t in edges)
    assert max(Counter(s for s, t in edges).values(), default=0) <= 2
    assert max(Counter(t for s, t in edges).values(), default=0) <= 1


def solve_policy(nodes, edges, candidates, params, arm):
    """Maximum-weight joint assignment with explicit keep/no-edge alternatives."""
    if arm not in {'no_change', 'original_score', 'context'}:
        raise ValueError(arm)
    edges = set(edges)
    validate_graph(nodes, edges)
    if arm == 'no_change':
        return edges, [], {'protected_edges': len(edges)}
    protected, fork_nodes = protected_edges(edges, candidates, params)
    blocked_sources = {s for s, t in protected}
    blocked_targets = {t for s, t in protected}
    available = {e: c for e, c in candidates.items()
                 if e[0] not in blocked_sources and e[1] not in blocked_targets
                 and e[0] not in fork_nodes and e[1] not in fork_nodes}
    by_frame = defaultdict(dict)
    for e, c in available.items():
        by_frame[int(nodes[e[0]][0])][e] = c
    assert edges - protected <= available.keys()
    result = set(edges)
    actions = []
    penalty = params['edit_penalty']
    for frame, pool in sorted(by_frame.items()):
        sources = sorted({s for s, t in pool})
        targets = sorted({t for s, t in pool})
        si, ti = {s: i for i, s in enumerate(sources)}, {t: i for i, t in enumerate(targets)}
        values = np.full((len(sources), len(targets) + len(sources)), -1e12)
        values[np.arange(len(sources)), len(targets) + np.arange(len(sources))] = 0
        weights = {e: utility(c, arm, params) for e, c in pool.items()}
        current = edges & pool.keys()
        for (s, t), value in weights.items():
            # Dropped-current penalties are constant after adding a retention bonus.
            values[si[s], ti[t]] = value + (penalty if (s, t) in current else -penalty)
        rr, cc = linear_sum_assignment(values, maximize=True)
        proposed = {(sources[r], targets[c]) for r, c in zip(rr, cc) if c < len(targets)}
        for added, removed in difference_components(proposed - current, current - proposed):
            gain = sum(weights[e] for e in added) - sum(weights[e] for e in removed)
            gain -= penalty * (len(added) + len(removed))
            if not added or gain <= 1e-10:
                continue
            result.difference_update(removed)
            result.update(added)
            actions.append({'frame': frame, 'added': sorted(added), 'removed': sorted(removed),
                            'objective_gain': gain})
    validate_graph(nodes, result)
    assert protected <= result
    _, old_out = adjacency(edges)
    _, new_out = adjacency(result)
    assert {s: ts for s, ts in old_out.items() if len(ts) == 2} == {
        s: ts for s, ts in new_out.items() if len(ts) == 2}
    return result, actions, {'protected_edges': len(protected), 'fork_protected_nodes': len(fork_nodes),
                              'solver_pairs': len(available)}
