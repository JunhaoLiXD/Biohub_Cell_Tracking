"""One text-only author response after the tool-turn ceiling; no new inspection."""
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_controller.core import command_prefix, utc_now
folder = ROOT / 'docs/research/ep015_continuation_2026-09-26'
assert not (folder / 'claude_strategy_run_v3.json').exists()
prior = json.loads((folder / 'claude_strategy_run_v2.json').read_text())
assert prior['exit_code'] == 1 and (folder / 'claude_strategy_v2.md').read_text().strip() == 'Error: Reached max turns (6)'
prompt = '''You are Claude Code, original strategy author. Your prior revision hit a six-tool-turn ceiling, NOT a quota/timeout, without a final response. All necessary text follows. Tools are disabled; no repository access, no file edits. Respond directly in <=650 words with your revised proposal accepting or rejecting EACH substantive Codex correction. End AUTHOR ACCEPTS REVISIONS if you agree, otherwise NO_CONSENSUS. You do not grant Codex consensus or admission PASS. No further calls will be attempted on a failure.\n\nORIGINAL PROPOSAL:\n''' + (folder / 'claude_strategy_v1.md').read_text(encoding='utf-8') + '\n\nCODEX CRITIQUE:\n' + (folder / 'codex_critique_v1.md').read_text(encoding='utf-8')
cmd = [*command_prefix('claude', env_name='CLAUDE_COMMAND'), '--print', '--tools', '', '--output-format', 'text', '--max-turns', '2']
(folder / 'claude_strategy_prompt_v3.md').write_text(prompt, encoding='utf-8')
try:
    r = subprocess.run(cmd, cwd=ROOT, input=prompt, text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=180)
    out, err, code = r.stdout, r.stderr, r.returncode
except subprocess.TimeoutExpired as e:
    out, err, code = e.stdout or '', e.stderr or '', 124
    if isinstance(out, bytes): out = out.decode('utf-8', errors='replace')
    if isinstance(err, bytes): err = err.decode('utf-8', errors='replace')
(folder / 'claude_strategy_v3.md').write_text(out, encoding='utf-8')
(folder / 'claude_strategy_run_v3.json').write_text(json.dumps({'command': cmd, 'exit_code': code, 'stderr': err, 'completed_at': utc_now(), 'reason': 'Single text-only resolution of substantive corrections after tool-turn ceiling; not quota/timeout retry.'}, indent=2), encoding='utf-8')
print('Text-only response saved; exit:', code)
raise SystemExit(code)
