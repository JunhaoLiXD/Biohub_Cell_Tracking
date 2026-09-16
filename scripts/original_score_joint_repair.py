"""Prediction-only original-score joint repair; frozen solver from local_052 attempt02."""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import math
import numpy as np
from scipy.optimize import linear_sum_assignment

PARAMETERS = dict(top_k=8, protected_probability=0.9, edit_penalty=0.25)


class DetectionProvenance:
    """Carry original detection identity; recovery nodes never acquire an old token."""

    def __init__(self, ids, coords, nodes):
        self.tokens = {int(n): (int(i), int(xyz[0]))
                       for i, (n, xyz) in enumerate(zip(ids, coords))}
        self.alive = set()
        for n, node in nodes.items():
            token = self.tokens.get(n)
            if token is not None and token[1] == int(node['t']):
                node['_original_detection'] = token
                self.alive.add(n)

    def observe(self, nodes):
        self.alive = {n for n in self.alive if n in nodes
                      and nodes[n].get('_original_detection') == self.tokens[n]
                      and int(nodes[n]['t']) == self.tokens[n][1]}
        return self.alive.copy()


def load_original_candidates(folder, nodes, edges, persistent):
    """Only read prediction probabilities and detection indices, never context or labels."""
    folder = Path(folder)
    with np.load(folder / 'pre_ilp_nodes.npz', allow_pickle=False) as reg:
        ids = reg['graph_node_ids']
    node_ids = np.array(sorted(persistent), dtype=np.int64)
    result = {}
    for frame in range(99):
        with np.load(folder / f'pair_{frame:03d}_{frame+1:03d}.npz', allow_pickle=False) as z:
            ij = z['pair_indices']
            src = ids[z['source_ids']][ij[:, 0]]
            tgt = ids[z['target_ids']][ij[:, 1]]
            prob = z['probabilities']
            if not np.isfinite(prob).all() or np.any((prob < 0) | (prob > 1)):
                raise ValueError('Invalid prediction probabilities')
            threshold = float(z['threshold'])
            if not math.isfinite(threshold) or not 0 < threshold < 1:
                raise ValueError('Invalid prediction threshold')
            rows = np.flatnonzero(np.isin(src, node_ids) & np.isin(tgt, node_ids))
            order = rows[np.lexsort((tgt[rows], -prob[rows], src[rows]))]
            by_source = defaultdict(list)
            for row in order:
                by_source[int(src[row])].append(int(row))
            for source, group in by_source.items():
                unique = len(group) == 1 or prob[group[0]] > prob[group[1]]
                for i, row in enumerate(group):
                    target = int(tgt[row])
                    if i >= PARAMETERS['top_k'] and (source, target) not in edges:
                        continue
                    assert nodes[target][0] == nodes[source][0] + 1
                    assert (source, target) not in result
                    result[source, target] = Candidate(float(prob[row]), threshold, 0.0,
                                                       None, bool(i == 0 and unique))
    return result


def repair_graph(folder, nodes, edges, persistent):
    candidates = load_original_candidates(folder, nodes, edges, persistent)
    return solve_policy(nodes, edges, candidates, PARAMETERS, 'original_score')


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
