"""Assert-only runtime contract, embedded in the ep015 notebook; standard library only."""
import csv
import hashlib
import json
import math
import os
import time
from collections import Counter
from pathlib import Path

EXP068_EXPECTED = {'OUTPUT_MIN_EDGE_PROB': .15, 'COUNT_EXCESS_FRAC': 0.,
                  'SEG_PRUNE_MIN_PROB': 0., 'LEAF_PRUNE_MIN_EDGE_PROB': 0.,
                  'GAP_CLOSE_DIV_UM': 0., 'REPAIR_PARENT_MAX_UM': 0., 'LINEFIT_MAX_SHIFT_UM': 0.}
EXP068_CHECKPOINTS = {
    'deepcenter': '8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0',
    'primary': '12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771',
    'secondary': '9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f'}
EXP068_PARENT = 'd52a5da2ae5cb0d1b22499f6ca51a00838a6c32ae9a1986ec756ea72e7909e03'
EXP068_CX03 = '135172dfefda1b5c8c43aca30eb8cc1357a84b7826ac0ada3bf80c0b53f11fef'


def exp068_preflight(ns):
    observed = {}
    for key, value in EXP068_EXPECTED.items():
        assert key in ns and type(ns[key]) in (int, float), ('missing resolved setting', key)
        assert float(ns[key]) == value, ('resolved setting drift', key, ns[key])
        assert float(os.environ['BIOHUB_' + key]) == value, ('environment drift', key)
        observed[key] = ns[key]
    assert os.environ['BIOHUB_VALIDATOR_ENABLE'] == '0'
    assert ns['_V9_AUTO_SET_ENV'] == {} and ns['FROZEN_PRESET_OVERRIDES'] is None
    root = Path(ns['WORKING_DIR'])
    receipts = list(root.glob('*runtime_integrity*.json'))
    assert len(receipts) == 1, 'Exactly one current runtime integrity receipt required'
    receipt = json.loads(receipts[0].read_text())
    assert receipt['checkpoint_sha256'] == EXP068_CHECKPOINTS
    assert receipt['support_repo_python_manifest_sha256'] == '978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029'
    return observed


def exp068_audit_csv(path, discovered):
    expected = ['id', 'dataset', 'row_type', 'node_id', 't', 'z', 'y', 'x', 'source_id', 'target_id']
    nodes, edges, row_ids = {}, [], set()
    with Path(path).open(newline='') as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == expected, 'Submission schema mismatch'
        for row in reader:
            assert None not in row and all(v is not None for v in row.values()), 'Malformed CSV row'
            rid = int(row['id'])
            assert rid >= 0 and rid not in row_ids, 'Duplicate/negative row id'
            row_ids.add(rid)
            ds = row['dataset']
            if row['row_type'] == 'node':
                nid, frame = int(row['node_id']), int(row['t'])
                key = (ds, nid)
                assert nid >= 0 and frame >= 0 and key not in nodes
                xyz = tuple(float(row[a]) for a in ('z', 'y', 'x'))
                assert all(math.isfinite(v) and 0 <= v <= 32767 for v in xyz)
                nodes[key] = (frame, xyz)
            else:
                assert row['row_type'] == 'edge'
                edges.append((ds, int(row['source_id']), int(row['target_id'])))
    assert nodes and edges and set(d for d, _ in nodes) == set(discovered)
    assert len(set(edges)) == len(edges)
    incoming, outgoing = Counter(), Counter()
    for ds, a, b in edges:
        assert (ds, a) in nodes and (ds, b) in nodes
        assert nodes[ds, b][0] == nodes[ds, a][0] + 1
        incoming[ds, b] += 1
        outgoing[ds, a] += 1
    assert max(incoming.values()) <= 1 and max(outgoing.values()) <= 2
    counts = {ds: {'nodes': sum(d == ds for d, _ in nodes),
                   'edges': sum(d == ds for d, _, _ in edges),
                   'forks': sum(d == ds and n == 2 for (d, _), n in outgoing.items())}
              for ds in sorted(set(discovered))}
    assert all(v['edges'] > 0 for v in counts.values())
    return counts


def exp068_finalize(ns):
    observed = exp068_preflight(ns)
    assert ns['VALIDATOR_ENABLE'] is False and ns['val_stems'] == []
    root = Path(ns['WORKING_DIR'])
    report = json.loads((root / 'biohub_v9_runtime_report.json').read_text())
    assert report['deadline_degraded'] is False
    assert report['frozen_preset_applied'] is False and report['auto_attached'] == {}
    assert report['sweep_results_count'] == 0 and report['shipped_config'] == 'base'
    assert report['shipped_overrides'] == {} and report['val_pred_cache_used'] is False
    stats = list(csv.DictReader((root / 'run_stats.csv').open(newline='')))
    assert stats and len(stats) == len(ns['test_stems'])
    assert {r['dataset'] for r in stats} == set(ns['test_stems'])
    for row in stats:
        for key in ('repair_fallback', 'deadline_degraded', 'count_target_removed', 'leaf_prune_nodes', 'seg_prune_nodes', 'repairs_added', 'divgap_added'):
            assert float(row[key]) == 0, (key, row['dataset'])
    dropped = sum(int(r['weak_edge_dropped']) for r in stats)
    assert dropped > 0, 'VOID: no weak edges dropped'
    sub = root / 'submission.csv'
    digest = hashlib.sha256(sub.read_bytes()).hexdigest()
    assert digest not in (EXP068_PARENT, EXP068_CX03), 'VOID: known duplicate output'
    assert (root / 'submission_arm.csv').read_bytes() == sub.read_bytes()
    counts = exp068_audit_csv(sub, ns['test_stems'])
    for row in stats:
        assert int(row['nodes']) == counts[row['dataset']]['nodes']
        assert int(row['edges']) == counts[row['dataset']]['edges']
    runtime = time.monotonic() - ns['_exp068_started']
    assert 0 < runtime < 5400
    metrics = {'schema_version': 1, 'experiment_id': 'exp_068_ep015_single_probe',
               'validation': {'protocol': 'ep015_single_probe_v1'},
               'primary_metric': 1., 'primary_metric_meaning': 'Engineering integrity only; no accuracy claim',
               'ep015_probe_integrity_passed': True, 'runtime_seconds': runtime, 'reproducible': False,
               'submission_sha256': digest, 'effective_config': observed, 'weak_edge_dropped': dropped,
               'per_dataset': counts, 'checkpoint_sha256': EXP068_CHECKPOINTS,
               'quality_status': 'Unknown until separately audited authorized LB probe; never auto-promote.'}
    print('EXP068 postflight PASS', digest, flush=True)
    return metrics
