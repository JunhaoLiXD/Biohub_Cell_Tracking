"""Refresh current handoffs from the tracked ep068 record, without remote actions."""
import json
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
exp = 'exp_068_ep015_single_probe'
record = json.loads((ROOT / 'experiments' / exp / 'experiment.json').read_text(encoding='utf-8'))
phase = record['state']
review = record['review'].get('verdict', record['review']['status'])
budget = json.loads((ROOT / 'GPU_BUDGET.json').read_text(encoding='utf-8'))
state_path = ROOT / 'STATE.json'
state = json.loads(state_path.read_text(encoding='utf-8'))
running = phase in ('SUBMITTED', 'RUNNING')
next_action = ('Wait for user completion notice; do not poll, rebuild or relaunch. Then check/collect once, run scripts/audit_exp068_collection_v2.py (verify admission_supplement_manifest.json), bind remote version/source, check remote history and conservative three/day cap, and perform the one already authorized LB submission if all gates pass.' if running else
               'Complete fresh experiment-specific Codex PASS and snapshot smoke before one controller launch. No waiver or automatic failed-review retry. CPU diagnostic is complete; no exp067 training authorized.')
state.update(active_experiment=exp, phase='EP068_' + phase + '__CPU_COUNTERFACTUAL_COMPLETE',
             updated_at=datetime.now(timezone.utc).isoformat(),
             summary=f'ep015 one-probe continuation: experiment {phase}, review {review}. GPU ledger {budget["remaining_hours"]:.6f} h; reservations {budget["reserved_hours"]}. CPU GT-assisted 128-subset diagnostic reproduces baseline 3/2/9 and reaches 9/2/3 under true-edge edits; not deployable performance or LB evidence. Retain exp064 submission 56535761 at recorded 0.953.',
             next_action=next_action)
state['ep068_status'] = {'experiment': exp, 'state': phase, 'review': review,
                         'cpu_report': 'docs/research/ep015_continuation_2026-09-26/division_counterfactual_report.md',
                         'strategy': 'docs/research/ep015_continuation_2026-09-26/strategy_consensus_v1.md',
                         'user_authorized_one_submission_after_audit': True,
                         'final_selection_change_authorized': False}
state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
begin, end = '<!-- BEGIN EP068 CURRENT -->', '<!-- END EP068 CURRENT -->'
notice = f'''{begin}
## Current ep068 continuation - {state['updated_at']}

Experiment `{exp}`: **{phase}**. Fresh review: **{review}**.
The user authorized one ep015 run and one audited LB submission; 30 GPU hours were
reported at the new epoch. Ledger now {budget['remaining_hours']:.6f} h, reservations
`{json.dumps(budget['reserved_hours'])}`. No final re-selection, second probe or public push.

{next_action}

CPU counterfactual is complete: all 128 subsets audited; original full per-movie
metrics reproduced. True-edge repair can change TP/FP/FN from 3/2/9 to 9/2/3 in this
restricted family. This is GT-assisted TRAIN diagnosis, not a learned result or LB
forecast. Report: `docs/research/ep015_continuation_2026-09-26/division_counterfactual_report.md`.
Older ep015-OFF and exp067-current instructions below are historical. exp067 training
remains stopped. Final retained submission remains 56535761 (recorded Public LB 0.953).
{end}
'''
for name in ['GOAL.md', 'PLAN.md', 'HANDOUT.md', 'EXP067_STATUS.md', '.private/current/CONTINUATION.md', '.private/current/MEMORY.md', 'docs/research/PROJECT_HANDOFF.md']:
    p = ROOT / name
    text = p.read_text(encoding='utf-8')
    if begin in text:
        text = text.split(begin)[0] + notice + text.split(end, 1)[1].lstrip('\n')
    else:
        first, rest = text.split('\n', 1)
        text = first + '\n\n' + notice + '\n' + rest
    p.write_text(text, encoding='utf-8')
print('Updated active experiment and handoffs:', phase, review)
