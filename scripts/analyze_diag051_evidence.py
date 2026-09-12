"""Bounded offline audit of diag_051. Oracle edits use GT, never deployable policy."""
from __future__ import annotations

import ast
import csv
import gzip
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / 'experiments/diag_051_public_0942_tracklet_evidence'
ART = EXP / 'artifacts'
OUT = ROOT / '.private/research/diag051_audit'
STAGES = ['raw_post_ilp', 'distance_filtered', 'motion_relinked', 'degree_repaired',
          'gap1', 'gap2', 'safe_divisions', 'geometry_and_isolated', 'short_track_filtered']
VOXEL_SCALE = np.array([1.625, .40625, .40625])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_graph(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def frozen_functions():
    nb = json.loads((EXP / 'snapshot/source/public_0942_tracklet_evidence.ipynb').read_text(encoding='utf-8'))
    source = next(''.join(c['source']) for c in nb['cells'] if 'def score_sample(' in ''.join(c['source']))
    names = {'compute_edge_confusion', 'edge_jaccard', 'adjusted_jaccard',
             'weakly_connected_components', 'compute_division_confusion', 'decompose_errors'}
    selected = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(selected) == len(names)
    ns = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<frozen scorer functions>', 'exec'), ns)
    return ns


F = frozen_functions()


def score(pn, pe, gn, ge, p2g, g2p, t_true):
    tp, fp, fn = F['compute_edge_confusion'](pe, ge, p2g, g2p)
    dtp, dfp, dfn = F['compute_division_confusion'](pn, pe, gn, ge, p2g, g2p)
    row = dict(edge_tp=tp, edge_fp=fp, edge_fn=fn, div_tp=dtp, div_fp=dfp, div_fn=dfn,
               weight=tp + fp + fn, adjusted_edge_jaccard=F['adjusted_jaccard'](
                   F['edge_jaccard'](tp, fp, fn), len(pn), t_true))
    row.update(F['decompose_errors'](pn, gn, pe, ge, p2g, g2p))
    return row


def aggregate(rows):
    w = sum(r['weight'] for r in rows)
    adj = sum(r['weight'] * r['adjusted_edge_jaccard'] for r in rows) / w
    tp, fp, fn = (sum(r[k] for r in rows) for k in ['div_tp', 'div_fp', 'div_fn'])
    div = tp / (tp + fp + fn) if tp + fp + fn else 0
    return dict(primary_metric=adj + .1 * div, adjusted_edge_jaccard=adj,
                division_jaccard=div, div_tp=tp, div_fp=fp, div_fn=fn)


def quantiles(values):
    return dict(zip(['min', 'p25', 'median', 'p75', 'max'],
                    np.quantile(values, [0, .25, .5, .75, 1]).tolist())) if values else None


def consistent_oracle(pe, additions, p2g, ge):
    """Insert all reachable GT edges jointly; remove conflicting non-GT edges only."""
    result = set(pe)
    ge = set(ge)
    incoming = defaultdict(set)
    outgoing = defaultdict(set)
    for s, t in result:
        incoming[t].add((s, t))
        outgoing[s].add((s, t))
    removed = set()
    for s, t in additions:
        for edge in incoming[t] | outgoing[s]:
            if (p2g.get(edge[0]), p2g.get(edge[1])) not in ge:
                removed.add(edge)
    result.difference_update(removed)
    result.update(additions)
    assert max(Counter(t for s, t in result).values(), default=0) <= 1
    assert max(Counter(s for s, t in result).values(), default=0) <= 2
    return result, len(removed)


def analyze_video(stem, manifest):
    folder = ART / 'tracklet_evidence' / stem
    for stage, rec in manifest['graph_manifest'][stem].items():
        assert sha(folder / (stage + '.json.gz')) == rec['sha256']
    records = manifest['worker_manifest'][stem]
    assert len(records) == 100
    assert sum(r['bytes'] for r in records) <= 128 * 1024**2
    for rec in records:
        path = folder / rec['name']
        assert path.stat().st_size == rec['bytes'] and sha(path) == rec['sha256']
    final = read_graph(folder / 'final_scored.json.gz')
    pn, gn = dict(final['pred_nodes']), dict(final['gt_nodes'])
    pe, ge = set(map(tuple, final['pred_edges'])), set(map(tuple, final['gt_edges']))
    assert len(pn) == len(final['pred_nodes']) and len(gn) == len(final['gt_nodes'])
    assert len(pe) == len(final['pred_edges']) and len(ge) == len(final['gt_edges'])
    assert all(s in pn and t in pn and pn[t][0] == pn[s][0]+1 for s, t in pe)
    assert max(Counter(t for s, t in pe).values(), default=0) <= 1
    assert max(Counter(s for s, t in pe).values(), default=0) <= 2
    matching = read_graph(folder / 'scorer_matching.json.gz')
    p2g, g2p = dict(matching['p2g']), dict(matching['g2p'])
    assert len(p2g) == len(g2p) and all(g2p[g] == p for p, g in p2g.items())
    assert set(p2g) <= pn.keys() and set(g2p) <= gn.keys()
    assert all(pn[p][0] == gn[g][0] and np.linalg.norm(
        (np.asarray(pn[p][1:])-np.asarray(gn[g][1:])) * VOXEL_SCALE) <= 7.0+1e-12 for p, g in p2g.items())
    baseline = score(pn, pe, gn, ge, p2g, g2p, final['t_true'])
    for k, v in baseline.items():
        assert math.isclose(v, final['score_row'][k], rel_tol=0, abs_tol=1e-12), (stem, k)
    stages = [read_graph(folder / (s + '.json.gz')) for s in STAGES]
    stage_edges = [{(e['source_id'], e['target_id']) for e in d['edges']} for d in stages]
    stage_nodes = [dict(d['nodes']) for d in stages]
    for nodes, edges in zip(stage_nodes, stage_edges):
        assert all(s in nodes and t in nodes and nodes[t]['t'] == nodes[s]['t'] + 1 for s, t in edges)
    stage_edges.append(pe)
    reg = np.load(folder / 'pre_ilp_nodes.npz', allow_pickle=False)
    graph_ids = reg['graph_node_ids']
    assert len(set(graph_ids.tolist())) == len(graph_ids) == len(reg['coords'])
    assert np.array_equal(reg['detection_ids'], np.arange(len(graph_ids)))
    frames = {int(n): int(c[0]) for n, c in zip(graph_ids, reg['coords'])}
    detection_support = Counter()
    missed_support_loss = Counter()
    for g, coord in gn.items():
        if g in g2p:
            continue
        select = reg['coords'][:, 0] == coord[0]
        distances = np.linalg.norm((reg['coords'][select, 1:] - np.asarray(coord[1:])) * VOXEL_SCALE, axis=1)
        nearby = set(graph_ids[select][distances <= 7].tolist())
        category = ('no_original_detection_within_radius' if not nearby else
                    'nearby_original_detection_survives_final' if nearby & pn.keys() else
                    'all_nearby_original_detections_removed')
        detection_support[category] += 1
        if category == 'all_nearby_original_detections_removed':
            support_presence = [True] + [bool(nearby & ns.keys()) for ns in stage_nodes] + [False]
            sequence = ['pre_ilp_nodes'] + STAGES + ['final_scored']
            losses = [sequence[i+1] for i in range(len(support_presence)-1)
                      if support_presence[i] and not support_presence[i+1]]
            missed_support_loss[losses[-1]] += 1
    fragments = {(g2p[s], g2p[t]) for s, t in ge if s in g2p and t in g2p and (g2p[s], g2p[t]) not in pe}
    assert len(fragments) == baseline['edges_fragmented']
    by_frame = defaultdict(list)
    for edge in fragments:
        if edge[0] in frames and edge[1] in frames:
            by_frame[(frames[edge[0]], frames[edge[1]])].append(edge)
    observed = {}
    pool_counts = Counter()
    feature_margins = defaultdict(list)
    pred_in, pred_out = defaultdict(list), defaultdict(list)
    for s, t in pe:
        pred_in[t].append(s)
        pred_out[s].append(t)

    def context_cost(source, target):
        # Five-frame maximum: source t-2,t-1,t and target t+1,t+2.
        past = source
        depth = 0
        for _ in range(2):
            if len(pred_in[past]) != 1:
                break
            past = pred_in[past][0]
            depth += 1
        if depth == 0 or len(pred_out[target]) != 1:
            return None
        future = pred_out[target][0]
        a, b = np.asarray(pn[source][1:]) * VOXEL_SCALE, np.asarray(pn[target][1:]) * VOXEL_SCALE
        velocity = (a - np.asarray(pn[past][1:]) * VOXEL_SCALE) / depth
        next_velocity = np.asarray(pn[future][1:]) * VOXEL_SCALE - b
        return float((np.linalg.norm(b-a-velocity) + np.linalg.norm(a-b+next_velocity)) / 2)
    for t in range(99):
        with np.load(folder / f'pair_{t:03d}_{t+1:03d}.npz', allow_pickle=False) as z:
            for key in z.files:
                a = z[key]
                assert a.dtype.kind != 'O'
                if a.dtype.kind == 'f':
                    assert np.isfinite(a).all(), (stem, t, key)
            src, tgt, ij = z['source_ids'], z['target_ids'], z['pair_indices']
            assert np.array_equal(z['frame_pair'], [t, t+1])
            assert ij.ndim == 2 and ij.shape[1] == 2
            assert np.all((ij[:, 0] >= 0) & (ij[:, 0] < len(src)))
            assert np.all((ij[:, 1] >= 0) & (ij[:, 1] < len(tgt)))
            assert len(set(map(tuple, ij.tolist()))) == len(ij)
            assert int(z['full_pair_count']) == len(src) * len(tgt)
            status = z['status']
            assert len(status) == len(ij) and set(status.tolist()) <= {0, 1, 2}
            assert int(np.sum(status == 2)) == int(z['accepted_count'])
            assert np.all(z['probabilities'][status == 0] <= z['threshold'])
            assert np.all(z['probabilities'][status > 0] > z['threshold'])
            for prefix in ['primary', 'secondary']:
                assert len(z[prefix + '_source_features']) == len(src)
                assert len(z[prefix + '_target_features']) == len(tgt)
            assert all(frames[int(graph_ids[int(i)])] == t for i in src)
            assert all(frames[int(graph_ids[int(i)])] == t+1 for i in tgt)
            assert np.array_equal((z['source_coords_downsampled'][:, 1:] * z['downsample']).astype(np.int16), reg['coords'][src, 1:])
            assert np.array_equal((z['target_coords_downsampled'][:, 1:] * z['downsample']).astype(np.int16), reg['coords'][tgt, 1:])
            pool_counts.update(full_pairs=int(z['full_pair_count']), observed_pairs=len(ij),
                               accepted_pairs=int(z['accepted_count']), above_threshold=int(z['above_threshold_count']))
            targets = by_frame.get((t, t+1), [])
            if not targets:
                continue
            si = {int(graph_ids[int(n)]): i for i, n in enumerate(src)}
            ti = {int(graph_ids[int(n)]): i for i, n in enumerate(tgt)}
            lookup = {tuple(pair): k for k, pair in enumerate(ij.tolist())}
            for edge in targets:
                i, j = si[edge[0]], ti[edge[1]]
                k = lookup.get((i, j))
                if k is None:
                    continue
                observed[edge] = dict(status=int(status[k]), probability=float(z['probabilities'][k]))
                js = ij[ij[:, 0] == i, 1]
                true_cost = context_cost(*edge)
                alt_costs = [context_cost(edge[0], int(graph_ids[int(tgt[jj])])) for jj in js
                             if jj != j and int(graph_ids[int(tgt[jj])]) in pn]
                alt_costs = [v for v in alt_costs if v is not None]
                if true_cost is not None and alt_costs:
                    margin = min(alt_costs) - true_cost
                    observed[edge]['five_frame_motion_margin'] = margin
                    feature_margins['five_frame_motion'].append(margin)
                for prefix in ['primary', 'secondary']:
                    a, b = z[prefix+'_source_features'][i], z[prefix+'_target_features']
                    sim = (b[js] @ a) / np.maximum(np.linalg.norm(b[js], axis=1) * np.linalg.norm(a), 1e-12)
                    true_sim = float(sim[js == j][0])
                    others = sim[js != j]
                    if len(others):
                        margin = true_sim - float(others.max())
                        observed[edge][prefix+'_cosine_margin'] = margin
                        feature_margins[prefix].append(margin)
    reach = Counter()
    loss = Counter()
    details = []
    for edge in sorted(fragments):
        obs = observed.get(edge)
        category = ('accepted_pre_ilp' if obs['status'] == 2 else
                    'degree_rejected' if obs['status'] == 1 else 'below_threshold') if obs else (
                        'generated_endpoint' if any(n not in frames for n in edge) else 'unmeasured_sparse_pair')
        reach[category] += 1
        present = [edge in es for es in stage_edges]
        disappeared = [STAGES[i+1] if i+1 < len(STAGES) else 'final_scored'
                       for i in range(len(present)-1) if present[i] and not present[i+1]]
        origin = disappeared[-1] if disappeared else 'never_present_in_exported_stages'
        if not disappeared and obs and obs['status'] == 2 and not present[0]:
            origin = 'pre_ilp_to_raw_post_ilp'
        loss[origin] += 1
        details.append(dict(source=edge[0], target=edge[1], category=category,
                            source_out_degree=len(pred_out[edge[0]]), target_in_degree=len(pred_in[edge[1]]),
                            free_tracklet_endpoints=not pred_out[edge[0]] and not pred_in[edge[1]],
                            last_disappearance=origin, stage_presence=present, **(obs or {})))
    oracles = {}
    for name, additions in [('fixed_accepted', {e for e, o in observed.items() if o['status'] == 2}),
                            ('expanded_sparse', set(observed)), ('all_fixed_nodes', fragments)]:
        edited, removed = consistent_oracle(pe, additions, p2g, ge)
        oracles[name] = dict(score=score(pn, edited, gn, ge, p2g, g2p, final['t_true']),
                             added=len(additions), removed=removed)
    gt_out, gt_in = defaultdict(set), {}
    for s, t in ge:
        gt_out[s].add(t)
        gt_in[t] = s
    components = F['weakly_connected_components'](pn, pe)
    fork_components = {components[s] for s, targets in pred_out.items() if len(targets) >= 2}
    division_events = []
    for source, children in gt_out.items():
        if len(children) < 2:
            continue
        anchors = [source] + ([gt_in[source]] if source in gt_in else [])
        common = {components[g2p[g]] for g in anchors if g in g2p} & fork_components
        for child in sorted(children)[:2]:
            lineage, queue = {child}, [child]
            while queue:
                for target in gt_out.get(queue.pop(), ()):
                    if target not in lineage:
                        lineage.add(target)
                        queue.append(target)
            common &= {components[g2p[g]] for g in lineage if g in g2p}
        direct = [(g2p[source], g2p[t]) for t in children if source in g2p and t in g2p]
        division_events.append(dict(gt_source=source, recovered=bool(common),
            direct_endpoints_all_matched=len(direct) == len(children),
            direct_edges_present=sum(e in pe for e in direct),
            direct_missing_sparse_reachable=sum(e not in pe and e in observed for e in direct)))
    assert sum(e['recovered'] for e in division_events) == baseline['div_tp']
    assert sum(not e['recovered'] for e in division_events) == baseline['div_fn']
    return dict(stem=stem, baseline=baseline, reachability=dict(reach),
                missed_node_geometric_support=dict(detection_support),
                missed_support_last_disappearance=dict(missed_support_loss),
                last_disappearance=dict(loss), pool_counts=dict(pool_counts),
                feature_margins={k: dict(n=len(v), positive=sum(x > 0 for x in v), quantiles=quantiles(v))
                                 for k, v in feature_margins.items()},
                oracles=oracles, fragments=details,
                division_events=division_events,
                stage_sizes={s: dict(nodes=len(n), edges=len(e)) for s, n, e in zip(STAGES, stage_nodes, stage_edges)})


def main():
    metrics = json.loads((ART / 'metrics.json').read_text())
    partial = '--partial' in sys.argv
    manifest = (dict(graph_manifest=metrics['metrics']['evidence_graph_manifest'],
                     worker_manifest=metrics['metrics']['evidence_worker_manifest'],
                     checks=metrics['metrics']['evidence_checks']) if partial else
                json.loads((ART / 'tracklet_evidence_manifest.json').read_text()))
    assert all(manifest['checks'].values()) and all(metrics['metrics']['checks'].values())
    expected = {'submission.csv': 'fd1162bfc09b6d06413701aa898eb14bc5df9cc5bfd999fe598bf81fbf125515',
                'validator_results.csv': '2e6b0bf3a02f3a74b2115b23342ddd22bd8340d0faa9db8893b4733dadb9da85'}
    for name, digest in expected.items():
        if not partial or (ART / name).exists():
            assert sha(ART / name) == digest
    videos = []
    for stem in sorted(manifest['graph_manifest']):
        if partial:
            folder = ART / 'tracklet_evidence' / stem
            required = [folder / (s + '.json.gz') for s in manifest['graph_manifest'][stem]]
            required += [folder / r['name'] for r in manifest['worker_manifest'][stem]]
            if not all(p.exists() for p in required):
                continue
        videos.append(analyze_video(stem, manifest))
        print('Audited ' + stem, flush=True)
    assert partial or len(videos) == 16
    if not partial:
        with (ART / 'validator_results.csv').open(encoding='utf-8', newline='') as stream:
            csv_rows = list(csv.DictReader(stream))
        assert len(csv_rows) == 16
        by_stem = {row['stem']: row for row in csv_rows}
        for video in videos:
            for key, value in video['baseline'].items():
                assert math.isclose(float(by_stem[video['stem']][key]), value, rel_tol=0, abs_tol=1e-12)
    summary = {}
    for scope in ['all', '44b6', '6bba']:
        selected = [v for v in videos if scope == 'all' or v['stem'].startswith(scope)]
        if not selected:
            continue
        baseline = aggregate([v['baseline'] for v in selected])
        target = metrics if scope == 'all' else metrics['specimen_metrics'][scope]
        if not partial:
            assert math.isclose(baseline['primary_metric'], target['primary_metric'], rel_tol=0, abs_tol=1e-12)
        result = dict(baseline=baseline)
        for field in ['reachability', 'last_disappearance', 'pool_counts', 'missed_node_geometric_support', 'missed_support_last_disappearance']:
            c = Counter()
            for v in selected:
                c.update(v[field])
            result[field] = dict(c)
        result['error_counts'] = {k: sum(v['baseline'][k] for v in selected) for k in
                                  ['edges_fragmented', 'edges_lost_to_detection', 'wrong_association_edges', 'missed_gt_nodes', 'edge_fp']}
        result['feature_margins'] = {}
        result['sparse_reachable_free_tracklet_endpoints'] = sum(f['free_tracklet_endpoints']
            for v in selected for f in v['fragments'] if f['category'] in ['accepted_pre_ilp', 'degree_rejected', 'below_threshold'])
        for name in ['primary', 'secondary', 'five_frame_motion']:
            key = name + '_cosine_margin' if name != 'five_frame_motion' else name + '_margin'
            values = [f[key] for v in selected for f in v['fragments'] if key in f]
            result['feature_margins'][name] = dict(n=len(values), positive=sum(x > 0 for x in values), quantiles=quantiles(values))
        result['oracles'] = {}
        for name in ['fixed_accepted', 'expanded_sparse', 'all_fixed_nodes']:
            agg = aggregate([v['oracles'][name]['score'] for v in selected])
            result['oracles'][name] = dict(**agg, delta=agg['primary_metric']-baseline['primary_metric'],
                added=sum(v['oracles'][name]['added'] for v in selected),
                removed=sum(v['oracles'][name]['removed'] for v in selected))
        summary[scope] = result
    OUT.mkdir(parents=True, exist_ok=True)
    report = dict(audit_passed=not partial, partial=partial, audited_videos=len(videos), hashes=expected,
                  audit_script_sha256=sha(Path(__file__)), runtime_hours=metrics['runtime_seconds']/3600,
                  manifest_graphs=176, manifest_worker_files=1600, summary=summary, videos=videos,
                  limitations=['GT-directed oracles are conditional structural headroom, not deployable policies.',
                               'These are jointly feasible constructed repairs, not globally optimal graph-score bounds.',
                               'Final scorer matching is held fixed because oracle nodes and coordinates do not change.',
                               'Sparse omitted pairs are unmeasured; all-fixed-nodes oracle is not cache-reachable.',
                               'No node-creation oracle was executed. Detection-related FN are a burden only.',
                               'Nearby original detections are geometric support, not established GT identities or causal deletion errors.',
                               'Five-frame motion samples existing final-graph coordinates, including parent smoothing; it is not a new five-frame encoder.',
                               'Appearance cosine ranks are descriptive and are not validated learned association scores.',
                               'Train16 uses pretrained features exposed to training data; it is not an independent generalization estimate.'])
    (OUT / ('partial_audit.json' if partial else 'audit.json')).write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
