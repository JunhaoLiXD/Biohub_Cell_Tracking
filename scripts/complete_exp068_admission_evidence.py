"""Resolve two concrete review findings without altering the inference snapshot."""
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import build_exp066_probe as historical
from experiment_controller.core import load_record, verify_snapshot, utc_now
folder = ROOT / 'experiments/exp_068_ep015_single_probe'
archive = folder / 'admission_round2'
assert not archive.exists()
archive.mkdir()
for name in ('review.md', 'codex-review-run.json', 'codex-prompt.md'):
    (archive / name).write_bytes((folder / name).read_bytes())
original = (ROOT / 'scripts/audit_exp068_collection.py').read_text(encoding='utf-8')
old = "    deltas = {d: {'nodes': counts[d]['nodes'] - pn[d], 'edges': counts[d]['edges'] - pe[d]} for d in counts}"
new = '''    parent_stats_path = ROOT / 'experiments/exp_064_x138_verbatim_repro/collection/run_stats.csv'
    parent_stats = list(csv.DictReader(parent_stats_path.open(newline='')))
    parent_forks = {r['dataset']: int(r['division_like_sources']) for r in parent_stats}
    assert set(parent_forks) == set(counts) and len(parent_stats) == len(counts)
    for row in parent_stats:
        assert int(row['nodes']) == pn[row['dataset']] and int(row['edges']) == pe[row['dataset']]
    for row in stats:
        assert int(row['division_like_sources']) == counts[row['dataset']]['forks']
    deltas = {d: {'nodes': counts[d]['nodes'] - pn[d], 'edges': counts[d]['edges'] - pe[d],
                  'parent_forks': parent_forks[d], 'candidate_forks': counts[d]['forks'],
                  'fork_delta': counts[d]['forks'] - parent_forks[d]} for d in counts}'''
assert original.count(old) == 1
new_source = original.replace(old, new)
anchor = "    record = load_record(ROOT, 'exp_068_ep015_single_probe')"
new_source = new_source.replace(anchor, '''    supplement = json.loads((ROOT / 'experiments/exp_068_ep015_single_probe/admission_supplement_manifest.json').read_text())
    for entry in supplement['files']:
        assert hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest() == entry['sha256'], entry['path']
''' + anchor)
path = ROOT / 'scripts/audit_exp068_collection_v2.py'
assert not path.exists()
path.write_text(new_source, encoding='utf-8')
record = load_record(ROOT, folder.name)
verify_snapshot(ROOT, record)
snap = json.loads((ROOT / record['snapshot_manifest']).read_text())
executed = []
for entry in snap['files']:
    if entry['role'] != 'extra_file': continue
    working = ROOT / 'scripts' / Path(entry['path']).name
    digest = hashlib.sha256(working.read_bytes()).hexdigest()
    assert digest == entry['sha256']
    executed.append({'workspace_path': str(working.relative_to(ROOT)), 'snapshot_path': entry['path'], 'sha256': digest, 'match': True})
comparison = ROOT / 'experiments/exp_066_probe_cx03/kaggle_kernel/biohub-exp066-cx03.ipynb'
original_root, original_args = historical.ROOT, sys.argv
with tempfile.TemporaryDirectory(prefix='exp068_provenance_') as td:
    historical.ROOT = Path(td)
    sys.argv = ['build_exp066_probe.py', 'cx03']
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            historical.main()
        rebuilt = Path(td) / 'experiments/exp_066_probe_cx03/kaggle_kernel/biohub-exp066-cx03.ipynb'
        assert rebuilt.read_bytes() == comparison.read_bytes(), 'Historical comparison vehicle does not reproduce byte-for-byte'
    finally:
        historical.ROOT, sys.argv = original_root, original_args
run = subprocess.run([sys.executable, 'scripts/smoke_exp068.py', str(ROOT / record['snapshot_source'])], cwd=ROOT, text=True, capture_output=True, check=True)
for entry in executed:
    assert hashlib.sha256((ROOT / entry['workspace_path']).read_bytes()).hexdigest() == entry['sha256']
receipt = {'at_utc': utc_now(), 'status': 'PASSED', 'command': run.args, 'stdout': run.stdout,
           'executed_workspace_to_snapshot_hash_matches': executed,
           'comparison_vehicle_provenance': {'archive': str(historical.VEHICLE.relative_to(ROOT)),
               'archive_sha256': historical.VEHICLE_SHA, 'builder_sha256': hashlib.sha256((ROOT / 'scripts/build_exp066_probe.py').read_bytes()).hexdigest(),
               'comparison_path': str(comparison.relative_to(ROOT)), 'comparison_sha256': hashlib.sha256(comparison.read_bytes()).hexdigest(),
               'byte_exact_reproduction': True},
           'core_sha256': hashlib.sha256((ROOT / 'experiment_controller/core.py').read_bytes()).hexdigest(),
           'python_executable': sys.executable}
(folder / 'direct_snapshot_smoke_v2.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
files = ['scripts/audit_exp068_collection_v2.py', 'scripts/exp068_contract.py', 'scripts/collect_exp064_x138.py',
         'experiments/exp_064_x138_verbatim_repro/collection/run_stats.csv',
         'experiments/exp_064_x138_verbatim_repro/collection/metrics.json']
supplement = {'at_utc': utc_now(), 'purpose': 'Versioned local post-collection audit supplement; frozen Kaggle notebook unchanged.',
              'files': [{'path': p, 'sha256': hashlib.sha256((ROOT / p).read_bytes()).hexdigest()} for p in files]}
(folder / 'admission_supplement_manifest.json').write_text(json.dumps(supplement, indent=2), encoding='utf-8')
packet = (folder / 'admission_evidence_v2.md').read_text(encoding='utf-8')
packet += '\n\n# Revision 3 supplement (supersedes audit v1 for post-collection use)\n'
for p in ['admission_round2/review.md','direct_snapshot_smoke_v2.json','admission_supplement_manifest.json']:
    packet += '\n## ' + p + '\n' + (folder / p).read_text(encoding='utf-8')
packet += '\n## Required local audit v2, complete source\n' + new_source
packet += '\n## Resolution\nBoth requested gaps resolved without changing frozen notebook or config. Workspace smoke dependencies match their immutable snapshot extras before/after execution; historical comparison notebook reproduced byte-for-byte from pinned archive with unchanged builder in a disposable directory. Required collection audit is now scripts/audit_exp068_collection_v2.py, bound by admission_supplement_manifest.json; it checks parent/current fork counts and emits their difference. Fork counts are structural, not TEST TP/FP labels. No GPU or LB submission yet.\n'
(folder / 'admission_evidence_v3.md').write_text(packet, encoding='utf-8')
print('Evidence complete: workspace/snapshot binding, byte-exact historical vehicle reproduction, fork-delta audit supplement.')
