"""One bounded response to the substantive Codex critique, never automatic retry."""
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_controller.core import command_prefix, utc_now
folder = ROOT / 'docs/research/ep015_continuation_2026-09-26'
assert not (folder / 'claude_strategy_run_v2.json').exists()
prompt = '''You are Claude Code, the strategy author. Revise your ep015 proposal after Codex's independent critique. No implementation, no launch, no model delegation. Read ONLY docs/research/ep015_continuation_2026-09-26/claude_strategy_v1.md and codex_critique_v1.md, plus targeted sources if necessary. Output <=1000 words as a v2 amendment responding to all ten findings. If you agree to the corrected implementation plan and CPU protocol say AUTHOR ACCEPTS REVISIONS; do not claim Codex consensus or admission PASS. If you disagree explain and say NO_CONSENSUS. In particular accept no polling, a 5400-second existing-style watchdog with 2h reservation including margin (not whole-platform absolute bound), an assertion-only effective-global guard immediately before base inference output and a final metrics contract, immutable snapshot before formal review, no historical overwrites, one already user-authorized submission after audit. Correct all factual errors about 8 movies/2 prefixes, runtimes, identical aggregate columns, division impacts and Q1 vs WHY. This is a substantive revision, not a retry after timeout/quota. Do not edit files; your stdout is captured. End AUTHOR ACCEPTS REVISIONS or NO_CONSENSUS.'''
(folder / 'claude_strategy_prompt_v2.md').write_text(prompt, encoding='utf-8')
cmd = [*command_prefix('claude', env_name='CLAUDE_COMMAND'), '--print', '--permission-mode', 'plan', '--output-format', 'text', '--max-turns', '6']
try:
    r = subprocess.run(cmd, cwd=ROOT, input=prompt, text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=360)
    out, err, code = r.stdout, r.stderr, r.returncode
except subprocess.TimeoutExpired as e:
    out, err, code = e.stdout or '', e.stderr or '', 124
    if isinstance(out, bytes): out = out.decode('utf-8', errors='replace')
    if isinstance(err, bytes): err = err.decode('utf-8', errors='replace')
(folder / 'claude_strategy_v2.md').write_text(out, encoding='utf-8')
(folder / 'claude_strategy_run_v2.json').write_text(json.dumps({'command': cmd, 'exit_code': code, 'stderr': err, 'completed_at': utc_now()}, indent=2), encoding='utf-8')
print('Revision saved; exit code:', code)
raise SystemExit(code)
