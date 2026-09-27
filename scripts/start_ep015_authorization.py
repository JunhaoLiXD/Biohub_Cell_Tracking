"""Record the user's bounded continuation and request one Claude strategy proposal."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_controller.core import command_prefix, utc_now

DIR = ROOT / 'docs/research/ep015_continuation_2026-09-26'


def main():
    DIR.mkdir(exist_ok=True)
    if (DIR / 'authorization.json').exists():
        raise RuntimeError('Authorization already recorded; do not duplicate reset or model call')
    now = utc_now()
    auth = {'at_utc': now, 'user_instruction': 'Then do as you recommended.',
            'scope': 'One ep015 candidate run and one LB probe after strategy consensus, admission PASS and output integrity; local CPU division scoring-potential diagnostic; no automatic final re-selection, second probe, exp067 training or public push.',
            'gpu_remaining_user_reported': 30.0, 'daily_submission_policy': 'Use conservative three/day from current user-supplied AGENTS; also obey remote cap. No burst authorized.',
            'completion_policy': 'After launch wait for user completion notice; no status polling. One check/collection then audit before authorized submission.',
            'model_allowance': 'Exact remaining allowance unavailable; disclosed; one bounded Claude proposal and one fresh formal Codex review, no automatic timeout/quota retry.'}
    (DIR / 'authorization.json').write_text(json.dumps(auth, indent=2) + '\n', encoding='utf-8')
    budget_path = ROOT / 'GPU_BUDGET.json'
    budget = json.loads(budget_path.read_text(encoding='utf-8'))
    assert not budget['reserved_hours'] and not budget.get('active_reservations')
    budget['reconciliations'].append({'at_utc': now, 'previous_remaining_hours': budget['remaining_hours'],
                                     'new_remaining_hours': 30.0, 'source': 'User explicitly reports 30 GPU hours now available; new epoch, not an inferred refund.'})
    budget.update(remaining_hours=30.0, latest_user_reported_remaining_hours=30.0,
                  latest_user_reported_at_utc=now)
    budget['budget_epoch_note'] = 'New epoch: user reports 30 GPU hours in the current conversation. Previous epoch, charges and closeout audit retained; no reservation yet. Only one bounded ep015 run is authorized.'
    budget_path.write_text(json.dumps(budget, indent=2) + '\n', encoding='utf-8')
    notice = '''## Active authorization - ep015 continuation, 2026-09-26

The user reports 30 GPU hours remaining and accepts the proposed next steps: one ep015
candidate run and one leaderboard probe after the existing strategy/review/smoke/output
gates, plus a zero-GPU division scoring-potential diagnostic. This supersedes the
closeout's ep015-OFF/no-successor instruction only within this bounded scope.
Retain exp064 submission 56535761 as the final choice unless separately instructed.
No second probe, full exp067 training, broader data export or public push is authorized.
Use the conservative three-per-New-York-day submission cap and check remote history
before the single submission. Wait for the user completion notice after launch; do not poll.
Strategy and receipts: `docs/research/ep015_continuation_2026-09-26/`.
Exact model allowance is unavailable; no automatic review retry after timeout or quota stop.

'''
    for name in ['GOAL.md', '.private/current/CONTINUATION.md', '.private/current/MEMORY.md', 'PLAN.md']:
        p = ROOT / name
        old = p.read_text(encoding='utf-8')
        first, rest = old.split('\n', 1)
        p.write_text(first + '\n\n' + notice + rest, encoding='utf-8')
    state_path = ROOT / 'STATE.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    state.update(updated_at=now, phase='EP015_STRATEGY_PREPARATION__CPU_DIVISION_DIAGNOSTIC_AUTHORIZED',
                 summary='User reopened one ep015 probe and a CPU-only division scoring-potential diagnostic. 30 GPU hours reported, no reservation or launch yet. exp064 0.953 retained; exp067 training remains stopped.',
                 next_action='Obtain Claude-authored proposal, independent Codex critique and explicit consensus; prepare tracked snapshot and fresh Codex admission PASS before one ep015 launch. No polling after launch.',
                 leaderboard_submission_authorized=True)
    state['ep015_authorization'] = auth
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    prompt = '''You are Claude Code, primary strategy author. The user has just authorized ONE ep015 run and ONE LB probe following existing gates, plus a zero-GPU division scoring-potential diagnostic; GPU remaining now 30h by explicit user report. No full exp067 training or promotion. Author a concise English proposal, not a review of your own work. Do not edit files or launch anything: output the complete proposal for Codex to persist and critique. End STRATEGY: PROPOSED (or NO_CONSENSUS if you object).

Read only these focused sources: GOAL.md top authorization, docs/research/closeout_review_2026-09-26.md, scripts/build_exp066_probe.py, experiments/exp_065_metric_aligned_pruning/collection/ppsweep_results.csv, scripts/exp067/parent_scorer.py compute_division_confusion, scripts/exp067_stage0_audit.py, and controller config configs/exp_064_x138_verbatim_repro.yaml as a format example. Conserve tokens: do not load whole notebooks or old histories.

Propose experiment exp_068_ep015_single_probe, behavior parent exp064 x138 (0.953, sha d52a5da2ae5cb0d1b22499f6ca51a00838a6c32ae9a1986ec756ea72e7909e03), implementation vehicle the same immutable optimized-biohub-max-score notebook used by exp066 cx03. One active lever BIOHUB_OUTPUT_MIN_EDGE_PROB=0.15, COUNT_EXCESS_FRAC=0, all other new levers off, validator off/no sweeps/no runtime selection. Existing builder supports ep015 but writes exp066 paths; propose a minimal new isolated wrapper, do not overwrite historical builds. Include concrete hypothesis, config and collection parity checks, expected ~0.5h runtime with conservative 1h planned reservation and honest enforcement limitation if using the unchanged vehicle, no automatic retry, existing review gates require_codex_review true, controller snapshot/smoke. One LB only if output is genuinely distinct, graph/provenance/activation/degradation checks pass and remote daily cap permits. No final re-selection. 0.954+ meets target at displayed precision only; 0.953 registered null; <=0.952 reject. Existing +0.00236 reweighted proxy is optimistic, per-prefix worst -0.0085; no reliable transfer forecast.

For CPU diagnostic: exact unchanged graph/no-op baseline must reproduce collected per-movie 3/2/9 scorer totals. Enumerate only the <=7 matched direct-edge deficits from preserved Q1, retain nodes and coordinates, insert true mother-daughter edges while removing conflicting incoming edges and excess outgoing continuations, preserve in-degree<=1/out-degree<=2/forward adjacency and all unrelated edges. Compare exact existing scorer on bounded subsets (<=128 total combinations, per-movie equivalent acceptable). Report attainable counterfactual under this restricted edit family, not a global upper bound or deployable score; GT never used in TEST inference or deployable policy. Include all changes, losses and per-prefix scores; if graph audit or baseline mismatch fails STOP. Diagnostic is not an exp067 training authorization. Explicitly critique whether this edit-family restriction can miss structural opportunities.

Do not call other models. Keep to <=1500 words. Codex will independently inspect code, record critique and revisions before CONSENSUS; do not claim consensus or admission PASS yourself.'''
    (DIR / 'claude_strategy_prompt_v1.md').write_text(prompt, encoding='utf-8')
    command = [*command_prefix('claude', env_name='CLAUDE_COMMAND'), '--print', '--permission-mode', 'plan', '--output-format', 'text', '--max-turns', '12']
    try:
        result = subprocess.run(command, cwd=ROOT, input=prompt, text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=480)
        text, err, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        text, err, code = exc.stdout or '', exc.stderr or '', 124
        if isinstance(text, bytes): text = text.decode('utf-8', errors='replace')
        if isinstance(err, bytes): err = err.decode('utf-8', errors='replace')
    (DIR / 'claude_strategy_v1.md').write_text(text, encoding='utf-8')
    (DIR / 'claude_strategy_run_v1.json').write_text(json.dumps({'command': command, 'exit_code': code, 'stderr': err, 'completed_at': utc_now()}, indent=2), encoding='utf-8')
    print('Claude proposal exit:', code)
    print(text[-14000:])
    return code


if __name__ == '__main__':
    raise SystemExit(main())
