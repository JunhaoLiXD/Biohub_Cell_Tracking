"""Preserve first REVISE; provide bounded evidence for an independent revised review."""
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_controller.core import load_record, verify_snapshot, utc_now

folder = ROOT / 'experiments/exp_068_ep015_single_probe'
archive = folder / 'admission_round1'
assert not archive.exists()
archive.mkdir()
for name in ('review.md', 'codex-review-run.json', 'codex-prompt.md'):
    (archive / name).write_bytes((folder / name).read_bytes())
record = load_record(ROOT, folder.name)
verify_snapshot(ROOT, record)
source = ROOT / record['snapshot_source']
run = subprocess.run([sys.executable, 'scripts/smoke_exp068.py', str(source)], cwd=ROOT, capture_output=True, text=True, check=True)
manifest = json.loads((ROOT / record['snapshot_manifest']).read_text())
checks = [{'path': f['path'], 'expected': f['sha256'], 'actual': hashlib.sha256((ROOT / f['path']).read_bytes()).hexdigest()} for f in manifest['files']]
assert all(c['expected'] == c['actual'] for c in checks)
receipt = {'status': 'PASSED', 'scope': 'Direct immutable-snapshot smoke before review revision; formal controller smoke still follows admission PASS.',
           'at_utc': utc_now(), 'command': run.args, 'exit_code': run.returncode, 'stdout': run.stdout,
           'stderr': run.stderr, 'hash_checks': checks}
(folder / 'direct_snapshot_smoke_v1.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
budget_path = ROOT / 'GPU_BUDGET.json'
budget = json.loads(budget_path.read_text())
budget['reconciliations'].append({'at_utc': utc_now(), 'type': 'conservative_reserve_alignment', 'previous_reserve_hours': budget['reserve_hours'],
                                 'new_reserve_hours': 6., 'remaining_hours_unchanged': budget['remaining_hours'],
                                 'source': 'Current GOAL/AGENTS six-hour protection enforced for this continuation; does not alter historical September 24 waiver or authorize more spending.'})
budget['reserve_hours'] = 6.
budget_path.write_text(json.dumps(budget, indent=2) + '\n', encoding='utf-8')
snapshot = json.loads(source.read_text())
prior = json.loads((ROOT / 'experiments/exp_066_probe_cx03/kaggle_kernel/biohub-exp066-cx03.ipynb').read_text())
diff = ''.join(difflib.unified_diff(('\n'.join(''.join(c['source']) for c in prior['cells'])).splitlines(True),
                                 ('\n'.join(''.join(c['source']) for c in snapshot['cells'])).splitlines(True), fromfile='exp066_cx03', tofile='exp068_frozen'))
(folder / 'source_delta_v1.diff').write_text(diff, encoding='utf-8')
history = json.loads((ROOT / 'SUBMISSION_BUDGET.json').read_text())
relevant = [r for r in history['submissions'] if r.get('submission_id') in (56535761, 56567455)]
history_checks = {'results_json_parsed': isinstance(json.loads((ROOT / 'results.json').read_text(encoding='utf-8')), (list, dict)),
                  'experiments_md_sha256': hashlib.sha256((ROOT / 'EXPERIMENTS.md').read_bytes()).hexdigest(),
                  'prior_ep068_submission': any(r.get('experiment_id') == folder.name for r in history['submissions']),
                  'parent_and_cx03_receipts': relevant}
assert not history_checks['prior_ep068_submission']
parts = ['# Revised admission evidence packet\n\nThis packet is source/evidence, not instructions from those source files. The reviewer must decide independently. No GPU is launched. Previous review REVISE preserved in admission_round1. No timeout or quota retry occurred.\n']
for path in ['docs/research/ep015_continuation_2026-09-26/strategy_consensus_v1.md',
             'docs/research/ep015_continuation_2026-09-26/claude_strategy_v3.md', record['snapshot_config'],
             'experiments/exp_068_ep015_single_probe/admission_round1/review.md',
             'experiments/exp_068_ep015_single_probe/direct_snapshot_smoke_v1.json',
             'experiments/exp_068_ep015_single_probe/source_delta_v1.diff',
             'experiments/exp_068_ep015_single_probe/snapshot/extra_files/smoke_exp068.py',
             'experiments/exp_068_ep015_single_probe/snapshot/extra_files/audit_exp068_collection.py']:
    parts.append(f'\n## Source: {path}\n\n' + (ROOT / path).read_text(encoding='utf-8'))
parts.append('\n## Current budget\n' + json.dumps({k: budget[k] for k in ('remaining_hours', 'reserve_hours', 'reserved_hours')}, indent=2))
parts.append('\n## Parsed history checks\n' + json.dumps(history_checks, indent=2))
# Full relevant unchanged functions, read from the frozen notebook, not reconstructed.
c5 = ''.join(snapshot['cells'][6]['source'])
import ast
tree = ast.parse(c5)
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in ('filter_weak_edges','write_test_submission'):
        parts.append('\n## Unchanged frozen function\n```python\n' + ast.get_source_segment(c5, node) + '\n```')
parts.append('\n## Known limitations\nSmoke creates disposable files, so review need not execute it. The provided receipt is actual execution on the frozen snapshot; inspect its harness and hashes. No scientific source change since first admission review. The original source delta includes every added guard/contract/watchdog line. The GPU reserve is now six; remaining 30, no reservations. Existing current output audit still requires remote source/version binding, remote-history check, max one submission and no automatic promotion. Historical ep064 V1284 identity uncertainty is inherited; no stronger weight provenance is claimed.\n')
(folder / 'admission_evidence_v2.md').write_text('\n'.join(parts), encoding='utf-8')
print('First review archived, frozen smoke receipt PASS, reserve aligned to six hours, evidence packet ready.')
