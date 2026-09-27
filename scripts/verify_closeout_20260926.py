"""Verify closeout documentation and preservation of pre-existing evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
backup = ROOT / '.private/closeout_20260926_before'
manifest = json.loads((backup / 'manifest.json').read_text(encoding='utf-8'))
for path, digest in manifest.items():
    assert hashlib.sha256((backup / path).read_bytes()).hexdigest() == digest, path
for name in ('GPU_BUDGET.json', 'SUBMISSION_BUDGET.json'):
    before = json.loads((backup / name).read_text(encoding='utf-8'))
    after = json.loads((ROOT / name).read_text(encoding='utf-8'))
    after.pop('closeout_audit_2026_09_26')
    assert before == after, name
audit = json.loads((ROOT / 'docs/research/closeout_audit_2026-09-26.json').read_text())
for path, digest in audit['input_sha256'].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
for old, new in [('PLAN.md', 'docs/research/PLAN_v3_2026-09-26_superseded.md'),
                 ('docs/research/exp067_stage0_result_2026-09-26.md', 'docs/research/exp067_stage0_result_2026-09-26_v1_superseded.md')]:
    assert (backup / old).read_bytes() == (ROOT / new).read_bytes()
state = json.loads((ROOT / 'STATE.json').read_text(encoding='utf-8'))
assert state['closeout']['local_complete'] and not state['leaderboard_submission_authorized']
assert not state['closeout']['final_selection_remote_verified']
print('PASS: pre-edit archive hashes, both complete historical ledgers, 16 graph/label input hashes,')
print('verbatim superseded versions, closeout state and authorization scope verified.')
