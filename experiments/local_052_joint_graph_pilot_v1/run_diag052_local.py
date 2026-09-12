"""One preregistered zero-GPU screen; GT is used only after policy execution."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import time

from analyze_diag051_evidence import ART, EXP, aggregate, read_graph, score, sha
from diag052_joint_policy import load_candidates, solve_policy

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / '.private/research/diag052_protocol_v1.json'
OUT = ROOT / 'experiments/local_052_joint_graph_pilot_v1'


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def edit_labels(edges, gt_edges, p2g):
    """Use exact frozen scorer FP semantics, including partly matched endpoints."""
    gt_sources = {s for s, t in gt_edges}
    gt_targets = {t for s, t in gt_edges}
    counts = Counter(true=0, false=0, unknown=0)
    for s, t in edges:
        ms, mt = p2g.get(s), p2g.get(t)
        label = ('true' if (ms, mt) in gt_edges else 'false'
                 if ms in gt_sources or mt in gt_targets else 'unknown')
        counts[label] += 1
    return dict(counts)


def panel(records, stems, arm):
    return aggregate([records[s]['arms'][arm]['score'] for s in stems])


def main():
    started = time.perf_counter()
    protocol = json.loads(PROTOCOL.read_text(encoding='utf-8'))
    OUT.mkdir(exist_ok=False)
    (OUT / 'artifacts').mkdir()
    (OUT / 'protocol.json').write_bytes(PROTOCOL.read_bytes())
    source_files = [Path(__file__), ROOT/'scripts/diag052_joint_policy.py',
                    ROOT/'scripts/analyze_diag051_evidence.py',
                    EXP/'snapshot/source/public_0942_tracklet_evidence.ipynb']
    receipt = {'experiment_id': protocol['id'], 'execution': 'local_only', 'status': 'RUNNING',
               'parent': protocol['parent'], 'evidence_donor': protocol['evidence_donor'],
               'hypothesis': protocol['hypothesis'], 'admission': {'require_claude_review': True},
               'review': 'No remote admission review requested; local screen only.',
               'gpu_hours': 0, 'started_at': datetime.now(timezone.utc).isoformat(),
               'protocol_sha256': sha(PROTOCOL),
               'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in source_files}}
    for p in source_files[:3]:
        (OUT / p.name).write_bytes(p.read_bytes())
    write_json(OUT/'experiment.json', receipt)
    metrics = json.loads((ART/'metrics.json').read_text(encoding='utf-8'))['metrics']
    stems = sorted(metrics['evidence_graph_manifest'])
    discovery, confirmation = [], []
    for specimen in sorted({s.split('_')[0] for s in stems}):
        group = [s for s in stems if s.startswith(specimen+'_')]
        assert len(group) == 8
        discovery.extend(group[:4])
        confirmation.extend(group[4:])
    write_json(OUT/'splits.json', {'discovery': discovery, 'confirmation': confirmation,
                                  'fitted_parameters': False})
    records = {}
    verified_files = 0
    for stem in stems:
        folder = ART/'tracklet_evidence'/stem
        for stage, rec in metrics['evidence_graph_manifest'][stem].items():
            assert sha(folder/(stage+'.json.gz')) == rec['sha256']
            verified_files += 1
        # The original audit's worker manifest structure is checked below.
        for rec in metrics['evidence_worker_manifest'][stem]:
            p = folder/rec['name']
            assert p.stat().st_size == rec['bytes'] and sha(p) == rec['sha256']
            verified_files += 1
        final = read_graph(folder/'final_scored.json.gz')
        nodes = dict(final['pred_nodes'])
        edges = set(map(tuple, final['pred_edges']))
        candidates, population = load_candidates(folder, nodes, edges, protocol['parameters'])
        # Neither the policy signature nor its candidate loader accepts labels or IDs of residuals.
        outputs = {arm: solve_policy(nodes, edges, candidates, protocol['parameters'], arm)
                   for arm in protocol['arms']}
        matching = read_graph(folder/'scorer_matching.json.gz')
        p2g, g2p = dict(matching['p2g']), dict(matching['g2p'])
        gn, ge = dict(final['gt_nodes']), set(map(tuple, final['gt_edges']))
        arms = {}
        for arm, (edited, actions, coverage) in outputs.items():
            scored = score(nodes, edited, gn, ge, p2g, g2p, final['t_true'])
            if arm == 'no_change':
                assert edited == edges
                for k, value in scored.items():
                    assert abs(value-final['score_row'][k]) < 1e-12, (stem, k)
            added, removed = edited-edges, edges-edited
            payload = {'pred_nodes': sorted(nodes.items()), 'pred_edges': sorted(edited),
                       'actions': actions, 'arm': arm, 'video': stem}
            artifact = OUT/'artifacts'/f'{stem}_{arm}.json.gz'
            artifact.write_bytes(gzip.compress(json.dumps(payload, sort_keys=True).encode(), mtime=0))
            arms[arm] = {'score': scored, 'added': edit_labels(added, ge, p2g),
                         'removed': edit_labels(removed, ge, p2g),
                         'additions': len(added), 'removals': len(removed),
                         'actions': len(actions), 'edit_rate_per_parent_edge':
                         (len(added)+len(removed))/max(1, len(edges)),
                         'coverage': coverage, 'graph_sha256': sha(artifact)}
        records[stem] = {'population': population, 'nodes': len(nodes), 'parent_edges': len(edges), 'arms': arms}
        print(stem, {a: {'added': arms[a]['additions'], 'removed': arms[a]['removals']} for a in arms}, flush=True)
        write_json(OUT/'progress.json', records)
    panels = {'all': stems, 'discovery': discovery, 'confirmation': confirmation}
    panels.update({sp: [s for s in stems if s.startswith(sp+'_')]
                   for sp in sorted({s.split('_')[0] for s in stems})})
    summary = {name: {arm: panel(records, group, arm) for arm in protocol['arms']}
               for name, group in panels.items()}
    deltas = {name: {a: scores[a]['primary_metric']-scores['no_change']['primary_metric']
                     for a in protocol['arms']} for name, scores in summary.items()}
    worst = min(records[s]['arms']['context']['score']['adjusted_edge_jaccard']-
                records[s]['arms']['no_change']['score']['adjusted_edge_jaccard'] for s in stems)
    gates = protocol['gates']
    context = summary['all']['context']
    checks = {
        'aggregate_gain': deltas['all']['context'] >= gates['aggregate_delta_min'],
        'context_beats_original': (summary['all']['context']['primary_metric']-
                                   summary['all']['original_score']['primary_metric']) >= gates['context_minus_original_min'],
        'discovery_positive': deltas['discovery']['context'] > 0,
        'confirmation_positive': deltas['confirmation']['context'] > 0,
        'both_specimens_positive': all(deltas[sp]['context'] > 0 for sp in ['44b6', '6bba']),
        'worst_video': worst >= gates['worst_video_adjusted_edge_delta_min'],
        'division_global': context['div_tp'] >= gates['division_tp_min'] and
                           context['div_fp'] <= gates['division_fp_max'] and
                           context['div_fn'] <= gates['division_fn_max'],
        'division_specimens': all(summary[sp]['context']['div_tp'] >= summary[sp]['no_change']['div_tp'] and
                                 summary[sp]['context']['div_fp'] <= summary[sp]['no_change']['div_fp'] and
                                 summary[sp]['context']['div_fn'] <= summary[sp]['no_change']['div_fn']
                                 for sp in ['44b6', '6bba'])}
    assert abs(summary['all']['no_change']['primary_metric']-0.9387332376874039) < 1e-12
    decision = 'PASS_LOCAL_GATE' if all(checks.values()) else 'REJECT_LOCAL_POLICY'
    result = {'decision': decision, 'checks': checks, 'summary': summary, 'deltas': deltas,
              'worst_video_context_adjusted_delta': worst, 'videos': records,
              'verified_input_files': verified_files, 'protocol_sha256': sha(PROTOCOL),
              'limitations': protocol['limitations']}
    assert receipt['protocol_sha256'] == sha(PROTOCOL)
    assert all(sha(ROOT/p) == value for p, value in receipt['source_sha256'].items())
    write_json(OUT/'result.json', result)
    receipt.update(status='COMPLETED', decision=decision, elapsed_seconds=time.perf_counter()-started,
                   completed_at=datetime.now(timezone.utc).isoformat(), result_sha256=sha(OUT/'result.json'))
    write_json(OUT/'experiment.json', receipt)
    print(json.dumps({'decision': decision, 'checks': checks, 'summary': summary, 'deltas': deltas}, indent=2), flush=True)


if __name__ == '__main__':
    main()
