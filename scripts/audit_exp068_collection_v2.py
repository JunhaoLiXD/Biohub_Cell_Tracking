"""Independent local audit after controller collection; does not submit or change selection."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exp068_contract import exp068_audit_csv, EXP068_CHECKPOINTS, EXP068_EXPECTED, EXP068_PARENT
from scripts.collect_exp064_x138 import DEGRADATION_STRINGS
from experiment_controller.core import load_record, verify_snapshot


def main():
    supplement = json.loads((ROOT / 'experiments/exp_068_ep015_single_probe/admission_supplement_manifest.json').read_text())
    for entry in supplement['files']:
        assert hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest() == entry['sha256'], entry['path']
    record = load_record(ROOT, 'exp_068_ep015_single_probe')
    verify_snapshot(ROOT, record)
    out = ROOT / 'experiments/exp_068_ep015_single_probe/artifacts'
    assert record.get('remote', {}).get('status') == 'COMPLETE'
    metrics = json.loads((out / 'metrics.json').read_text())
    assert metrics['experiment_id'] == record['experiment_id'] and metrics['ep015_probe_integrity_passed'] is True
    assert metrics['effective_config'] == EXP068_EXPECTED
    logs = '\n'.join(p.read_text(encoding='utf-8', errors='replace') for p in out.glob('*.log'))
    assert logs, 'Collected run log missing'
    assert not re.search(r'Traceback \(most recent call last\)|AssertionError|invalid V1284 displacement', logs)
    assert all(s not in logs for s, _ in DEGRADATION_STRINGS)
    assert 'V1284 head patched' in logs and re.search(r'mode\s*=\s*candidate', logs)
    assert 'EXP068 postflight PASS' in logs
    discovered = re.findall(r'Found\s+(\d+)\s+test videos', logs)
    assert discovered
    stats = list(csv.DictReader((out / 'run_stats.csv').open(newline='')))
    names = [r['dataset'] for r in stats]
    assert len(set(names)) == len(names) == int(discovered[-1])
    counts = exp068_audit_csv(out / 'submission.csv', names)
    assert counts == metrics['per_dataset']
    for row in stats:
        assert float(row['repair_fallback']) == float(row['deadline_degraded']) == 0
    receipt = json.loads((out / 'bidirectional_production_runtime_integrity.json').read_text())
    assert receipt['checkpoint_sha256'] == EXP068_CHECKPOINTS
    assert receipt['support_repo_python_manifest_sha256'] == '978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029'
    digest = hashlib.sha256((out / 'submission.csv').read_bytes()).hexdigest()
    assert digest == metrics['submission_sha256']
    assert (out / 'submission.csv').read_bytes() == (out / 'submission_arm.csv').read_bytes()
    ledger = json.loads((ROOT / 'SUBMISSION_BUDGET.json').read_text())
    assert digest != EXP068_PARENT and all(digest != r.get('submission_sha256') for r in ledger['submissions'])
    parent = json.loads((ROOT / 'experiments/exp_064_x138_verbatim_repro/collection/metrics.json').read_text())
    pn, pe = parent['details']['nodes_per_dataset'], parent['details']['edges_per_dataset']
    assert set(counts) == set(pn), 'Visible datasets differ; cannot certify isolated pruning direction'
    parent_stats_path = ROOT / 'experiments/exp_064_x138_verbatim_repro/collection/run_stats.csv'
    parent_stats = list(csv.DictReader(parent_stats_path.open(newline='')))
    parent_forks = {r['dataset']: int(r['division_like_sources']) for r in parent_stats}
    assert set(parent_forks) == set(counts) and len(parent_stats) == len(counts)
    for row in parent_stats:
        assert int(row['nodes']) == pn[row['dataset']] and int(row['edges']) == pe[row['dataset']]
    for row in stats:
        assert int(row['division_like_sources']) == counts[row['dataset']]['forks']
    deltas = {d: {'nodes': counts[d]['nodes'] - pn[d], 'edges': counts[d]['edges'] - pe[d],
                  'parent_forks': parent_forks[d], 'candidate_forks': counts[d]['forks'],
                  'fork_delta': counts[d]['forks'] - parent_forks[d]} for d in counts}
    assert all(v['edges'] <= 0 and v['nodes'] <= 0 for v in deltas.values())
    assert sum(v['edges'] for v in deltas.values()) < 0
    report = {'status': 'PASS', 'experiment_id': record['experiment_id'], 'submission_sha256': digest,
              'parent_deltas': deltas, 'per_dataset': counts, 'runtime_seconds': metrics['runtime_seconds'],
              'scope': 'Current collected output only. Before submission also bind authenticated remote kernel/version/source to staged snapshot and query remote submission history; this audit does not perform or waive those checks.'}
    path = out.parent / 'independent_collection_audit.json'
    assert not path.exists(), 'Preserve prior audit'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
