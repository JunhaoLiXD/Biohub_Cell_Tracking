"""Final targeted admission revision for two now-resolved evidence requirements."""
import json
import runpy
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
from experiment_controller import review
from experiment_controller.core import utc_now
folder = ROOT / 'experiments/exp_068_ep015_single_probe'
assert not (folder / 'admission_final_revision_invocation.json').exists()
(folder / 'admission_final_revision_invocation.json').write_text(json.dumps({'at_utc': utc_now(), 'reason': 'Resolve concrete workspace-hash provenance and fork-delta requirements; not timeout/quota retry.'}))
original = review.codex_command
review.codex_command = lambda: original()[:-1] + ['--model', 'gpt-6-astra', '-c', 'model_reasoning_effort="low"', '-']
review.build_review_prompt = lambda root, record: '''Independent admission review of exp_068_ep015_single_probe. Read-only, no shell/tool calls (helper failure already documented). Supplied evidence includes complete original source delta and tests plus final supplement resolving your two remaining requirements: executed workspace dependency hashes equal frozen extras, byte-exact reconstruction of cx03 comparison from pinned archive, and versioned/hashed local audit v2 with required parent/current fork deltas. Notebook and snapshot remain immutable. Six-hour reserve enforced, one user-authorized run/submission, no promotion, no retries. Evaluate independently; do not assume PASS. If evidence is insufficient identify concrete missing evidence. Review all safety/correctness implications of the supplement. Conserve quota; short answer ending exactly VERDICT: PASS, REVISE, or BLOCK (full line VERDICT: PASS / VERDICT: REVISE / VERDICT: BLOCK). PASS permits controller smoke and launch, not a quality claim.\n\n''' + (folder / 'admission_evidence_v3.md').read_text(encoding='utf-8')
orig_run = subprocess.run
def bounded(*args, **kwargs):
    kwargs.setdefault('timeout', 360)
    return orig_run(*args, **kwargs)
review.subprocess.run = bounded
sys.argv = ['scripts/request_codex_review.py', folder.name]
try:
    runpy.run_path(str(ROOT / 'scripts/request_codex_review.py'), run_name='__main__')
except subprocess.TimeoutExpired:
    (folder / 'codex-review-timeout-v3.json').write_text(json.dumps({'status': 'TIMEOUT_NO_VERDICT', 'at_utc': utc_now(), 'retry_allowed': False}))
    raise SystemExit(124)
