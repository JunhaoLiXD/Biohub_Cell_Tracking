"""Invoke the required review entrypoint once, with explicit read-only model and timeout."""
import json
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from experiment_controller import review
from experiment_controller.core import utc_now

folder = ROOT / 'experiments/exp_068_ep015_single_probe'
assert not (folder / 'codex-review-run.json').exists(), 'No automatic admission retries'
assert not (folder / 'codex-review-timeout.json').exists(), 'No timeout retry'
original_command = review.codex_command
def explicit_command():
    command = original_command()
    return command[:-1] + ['--model', 'gpt-6-astra', '-c', 'model_reasoning_effort="low"', '-']
review.codex_command = explicit_command
original_run = subprocess.run
def bounded_run(*args, **kwargs):
    kwargs.setdefault('timeout', 600)
    return original_run(*args, **kwargs)
review.subprocess.run = bounded_run
sys.argv = ['scripts/request_codex_review.py', 'exp_068_ep015_single_probe']
try:
    runpy.run_path(str(ROOT / 'scripts/request_codex_review.py'), run_name='__main__')
except subprocess.TimeoutExpired:
    (folder / 'codex-review-timeout.json').write_text(json.dumps({'status': 'TIMEOUT_NO_VERDICT', 'at_utc': utc_now(), 'timeout_seconds': 600, 'retry_allowed': False}, indent=2))
    raise SystemExit(124)
