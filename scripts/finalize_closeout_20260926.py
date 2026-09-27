"""Apply the user-authorized documentation closeout, preserving prior versions."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAMP = datetime.now(timezone.utc).isoformat()
REPORT = 'docs/research/closeout_review_2026-09-26.md'
AUDIT = 'docs/research/closeout_audit_2026-09-26.json'


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def write(path, text):
    (ROOT / path).write_text(text, encoding='utf-8')


def main():
    targets = ['PLAN.md', 'STATE.json', 'GPU_BUDGET.json', 'SUBMISSION_BUDGET.json', 'EXP067_STATUS.md',
               'GOAL.md', 'AGENTS.md', 'CLAUDE.md', 'HANDOUT.md', '.private/current/CONTINUATION.md',
               '.private/current/MEMORY.md', 'docs/research/PROJECT_HANDOFF.md',
               'docs/research/exp067_stage0_result_2026-09-26.md']
    backup = ROOT / '.private/closeout_20260926_before'
    if backup.exists():
        raise RuntimeError('Refusing to overwrite the pre-closeout archive')
    manifest = {}
    for name in targets:
        data = (ROOT / name).read_bytes()
        dest = backup / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        manifest[name] = hashlib.sha256(data).hexdigest()
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    for source, dest in [('PLAN.md', 'docs/research/PLAN_v3_2026-09-26_superseded.md'),
                         ('docs/research/exp067_stage0_result_2026-09-26.md', 'docs/research/exp067_stage0_result_2026-09-26_v1_superseded.md')]:
        assert not (ROOT / dest).exists()
        (ROOT / dest).write_bytes((ROOT / source).read_bytes())

    report = '''# Closeout review and corrected Stage 0 interpretation

2026-09-26. User authorized local closeout after the Codex REVISE review. This is a
documentation and cached-evidence audit, not a fresh experiment admission PASS.
No training, prediction, decode, remote query, GPU launch, submission or public push occurred.

## Reproduced evidence

`scripts/audit_closeout_20260926.py` reads the eight frozen final graphs and labels,
calls the existing parent division scorer, and checks every movie against the collected
validator CSV. It also calls the existing geometry predicate on the seven direct-edge
deficits. Machine-readable results and input SHA256s: `closeout_audit_2026-09-26.json`.

| Question | Result |
|---|---|
| GT divisions / fully matched triples | 12 / 9 |
| Exact mother-to-both-daughters events already present | 2 |
| Fully matched direct-edge deficits | 7 |
| Parent scorer TP / FP / FN | 3 / 2 / 9, reproduced for all eight movies |
| Existing Q1 candidate-edge reachability | 6/7; preserved Q1 result, generation not rerun |
| Existing Q1 generated events for those triples | 0/7; preserved Q1 result |

The discrepancy is `44b6_2a2eff9f`: its single division lacks the exact daughter
edges but is already a scorer TP. `parent_scorer.compute_division_confusion` credits
a component containing an anchor (mother or its parent), matched descendants of both
daughter lineages, and any fork. It does not require a fork at the matched mother.
Thus seven direct-edge deficits are NOT seven scorer FNs. This independently confirms
the earlier `step0_division_audit_reconciliation_2026-09-25.md` explanation.

## Isolated geometry controls

All controls below are predicate checks on unchanged cached coordinates, not new
candidate-generation runs or decoded graphs. Sister distance remains at 14 micrometres.

| Mother-daughter maximum | Symmetry tau | Geometry passes |
|---|---|---|
| 9 | 0.60 (base) | 0/7 |
| 9 | 0.75 | 0/7 |
| 9 | 0 (disabled) | 4/7 |
| 14 | 0.60 | 0/7 |
| 14 | 0 (disabled) | 7/7 |

Three triples also fail the original 9 micrometre distance limit. The seven asymmetry
values are above 0.75. Therefore the public sym075 arm does not test the relaxation
needed to admit them. Its recorded TP=3, FP=6, FN=9 and lower proxy establish a failed
specific mild relaxation, not the failure of all relaxed-geometry policies.
Geometry feasibility is not edge availability, generated-event availability, decoder
selection, or scorer improvement. The Q1 causes artifact and why script still use
node IDs in row-indexed hypothesis lookups; their candidate lists and truncation
classification are not reliable evidence. They are preserved, not silently repaired.
The corrected Q1 headroom script explicitly converts IDs to rows. Its stored result
is cited as historical evidence, not claimed to have been regenerated in this audit.

## Decision and limits

Stop exp067 for this competition because supervision is sparse and a defensible
export/train/decode/validate/deploy cycle is not justified before the chosen cutoff.
The frozen split has five complete training positives and four complete holdout
positives. This is not proof that the architecture cannot work or that dense labels
are the unique solution. Q2/Q3 are not run and decoder effectiveness is not certified.
The claim that one prior explains all historical 3/12 results is withdrawn.

Keep exp064 submission 56535761, recorded Public LB 0.953, as the retained candidate.
The user previously reported it selected; the live final-selection state was NOT
verified by this closeout. Verify it on the site before the cutoff/competition close.
cx03 is a registered null at reported precision, not proof of exactly zero true delta.
ep015 remains optional and OFF. Its ~0.955 extrapolation is neither an expectation nor
an upper bound; its worst per-prefix adjusted-edge regression is approximately 0.0085.
A higher Public LB would not by itself establish private-score superiority.

## Ledger reconciliation and provenance

The recorded 20-hour budget epoch less exp064/065/066/067c/067d gives
16.752764732567776 hours. Ledger balance is 16.752765177012222 hours: residual
0.000000444444446 hours (0.0016 seconds), consistent with mixed rounding precision.
Each of the five charges appears exactly once across the two existing ledger lists.
No reservation remains. Preserve the ledger balance and historical entries.
This is local accounting, not a fresh assertion about the remote GPU quota.

Submission history remains unchanged; local receipts identify exp064 at 0.953 and
cx03 at 0.953. No remote history check or new submission occurred. The ledger records
a September 24 user ruling raising the daily project cap to five, while the AGENTS
instructions supplied in this session state three. This conflict does not affect
closeout; any future submission must resolve it and check remote usage first.
No new submission authorization is inferred from either cap.

Previous PLAN v3 and Stage 0 v1 are preserved in explicitly superseded files.
All pre-edit governance and handoff bytes are also archived privately with SHA256s.
Current summaries supersede stale historical directives without altering receipts,
snapshots, experiment metrics or past review verdicts. No public push is authorized.
'''
    write(REPORT, report)
    write('docs/research/exp067_stage0_result_2026-09-26.md', '# Stage 0 result - corrected closeout edition\n\n'
          '2026-09-26. This edition supersedes the causal interpretation in '
          '`exp067_stage0_result_2026-09-26_v1_superseded.md`, preserved verbatim.\n\n'
          'The current evidence, isolated geometry checks, metric reconciliation and stop decision '
          'are in [the closeout review](closeout_review_2026-09-26.md). '
          'Reproducible numerical receipt: [CPU audit](closeout_audit_2026-09-26.json).\n\n'
          'Confirmed: 12 GT divisions, 9 complete matches, 2 exact direct-edge events, '
          '7 direct-edge deficits; parent scorer TP/FP/FN = 3/2/9. The seven include one '
          'already-credited scorer TP. Disabling symmetry alone admits 4/7 geometrically; '
          'disabling it and raising the distance limit to 14 admits 7/7. sym075 admits 0/7.\n\n'
          'Stop exp067 for the competition on time/supervision/validation grounds. '
          'No claim of architecture impossibility or universal explanation of historical TP counts remains.\n')
    write('PLAN.md', '''# PLAN - v4, local closeout

2026-09-26. User accepted Codex's closeout recommendation. Prior v3 is preserved at
`docs/research/PLAN_v3_2026-09-26_superseded.md`. Evidence and qualifications:
`docs/research/closeout_review_2026-09-26.md`.

## 1. Current decision

- Retain exp064 x138, submission **56535761**, recorded Public LB **0.953**.
- User-reported final selection is retained; live site selection is not reverified.
- Stop exp067 for this competition because of sparse supervision and the remaining
  validation/deployment workload. Its architecture has not been falsified.
- No GPU work is pending in local records. Ledger remaining: **16.752765 h**; no reservations.
- ep015 defaults to OFF. No launch, submission, new training or public push is authorized.

## 2. Corrected evidence

The eight exports contain 12 GT divisions, nine fully matched triples, two exact
parent-to-daughters events and seven direct-edge deficits. The parent scorer instead
returns **3/2/9 TP/FP/FN**: one direct-edge deficit already receives component-level credit.
The seven are not seven scorer FNs. Existing Q1 reports candidate edges for six and
generated events for zero; candidate generation was not rerun during closeout.

On cached coordinates, disabling symmetry alone admits **4/7**, widening distance
alone admits **0/7**, and both changes admit **7/7** geometrically. This does not establish
event availability or decoded score gain. sym075 (tau 0.75) still rejects all seven;
its failed proxy does not test sufficient relaxation. The historical universal-cause
claim is withdrawn. See the corrected Stage 0 report and numerical audit.

## 3. Completed local closeout

- [x] Preserve original PLAN v3 and Stage 0 v1; publish the correction and reproducible CPU audit.
- [x] Reproduce parent TP/FP/FN on every movie and reconcile direct-edge versus component semantics.
- [x] Reconcile GPU charges and empty reservations; keep the documented rounding residual.
- [x] Check local submission receipts without rewriting historical scores or claiming remote verification.
- [x] Update STATE, EXP067_STATUS and current handoff notices; regenerate governance checkpoints.
- [x] Keep exp064 snapshots, predictions and historical experiment/review records unchanged.
- [x] Public GitHub publication remains deferred; no push is part of closeout.
- [ ] Before close, verify **56535761** is still selected on the competition site.

Q2/Q3 remain unrun and deferred unless a future separately authorized research effort needs them.
The decoder has not been certified by this closeout. No new milestone notebook is warranted
for a corrected diagnostic and stopped, untrained experiment.

## 4. Optional ep015 - not part of current work

One probe or none, approximately 0.5 GPU hours and one submission if separately authorized.
Use the exact cx03 implementation vehicle with cx03 disabled and
`BIOHUB_OUTPUT_MIN_EDGE_PROB=0.15`; the unmodified x138 notebook does not implement this lever.
Pin implementation provenance and confirm all other levers remain off.

The historical test-reweighted proxy delta is +0.00236; worst per-prefix adjusted-edge
regression is approximately -0.0085. cx03's +0.00115 proxy corresponded to a reported
0.953 Public LB, equal to the parent at reported precision. Neither result supplies
a reliable transfer function. The old ~0.955 extrapolation is not a bound or expectation.

Retain the conservative read rule: >=0.955 permits a separate final-selection review;
0.954 defaults to retaining exp064; 0.953 is a registered null; <=0.952 rejects the arm.
Public-score improvement does not certify private-score improvement. No second probe.

Required first: versioned proposal/critique/revisions and explicit strategy CONSENSUS,
fresh experiment-specific Codex PASS, snapshot smoke, budget reservation and explicit
launch/submission authorization. Past export waivers do not apply. Exact model allowance
is not visible; retain the ten-percent reserve and avoid repeated review calls.

## 5. Final checks and standing constraints

Research cutoff remains **2026-09-29 12:00 UTC**. The locally recorded competition
deadline is September 29 23:59 with unspecified timezone; verify the official timestamp
on the site rather than treating this local record as a fresh deadline confirmation.

Do not poll runs or start experiments. Final selection changes require a separate decision.
Before any future submission, check authenticated remote history and resolve the current
three/day AGENTS instruction versus the ledger's historical five/day waiver. Closeout
does not resolve this by silently changing either record. Keep English technical files,
immutable history, and private artifacts out of the public remote.
''')

    state = json.loads(read('STATE.json'))
    state.update(phase='LOCAL_CLOSEOUT_COMPLETE__EXP067_STOPPED_FOR_COMPETITION', updated_at=STAMP,
                 leaderboard_submission_authorized=False,
                 summary='Local closeout complete. Keep exp064 submission 56535761 at recorded Public LB 0.953. exp067 stopped for competition on time and supervision grounds, not falsified. CPU audit reproduces scorer 3/2/9 versus 2 exact direct-edge events; symmetry-off alone admits 4/7, distance14 plus symmetry-off admits 7/7 geometrically. sym075 admits none of these triples. No GPU reservations; ledger 16.752765 h. No remote state verified in closeout.',
                 next_action='Verify submission 56535761 remains selected on the competition site before close. No experiment or submission authorized; ep015 remains OFF. Read PLAN.md v4 and docs/research/closeout_review_2026-09-26.md. Research cutoff 2026-09-29 12:00 UTC.')
    state['stage0_result'] = {'status': 'CORRECTED_AT_CLOSEOUT', 'cost': 'zero additional GPU and submissions',
                             'direct_edge_deficits': 7, 'direct_events_present': 2, 'scorer_tp_fp_fn': [3, 2, 9],
                             'geometry_pass_counts': json.loads(read(AUDIT))['geometry_pass_counts'],
                             'interpretation': 'Current geometry blocks these triples; no universal historical cause or architecture impossibility established.',
                             'not_run': 'Q2/Q3; no learned decoder evaluation', 'report': REPORT, 'audit': AUDIT}
    state['exp067_arc']['stage'] = 'Export complete; local closeout complete; stopped for competition. No trained head.'
    state['exp067_arc']['recommendation'] = 'User accepted the local closeout recommendation. Stop competition work; future reopening requires separate authorization.'
    state['exp067_arc']['exp_067d']['reserved_gpu_hours'] = 0.0
    state['exp067_arc']['exp_067d']['historical_launch_reservation_hours'] = 2.0
    state['exp066_cx03_result']['interpretation'] = 'Registered null at reported score precision; exact unrounded delta is unknown. Retain exp064.'
    state['closeout'] = {'at_utc': STAMP, 'report': REPORT, 'audit': AUDIT, 'local_complete': True,
                         'final_selection_remote_verified': False, 'ep015_authorized': False,
                         'public_push_authorized': False, 'pre_edit_archive': '.private/closeout_20260926_before/manifest.json'}
    write('STATE.json', json.dumps(state, indent=2, ensure_ascii=False) + '\n')
    for ledger in ['GPU_BUDGET.json', 'SUBMISSION_BUDGET.json']:
        data = json.loads(read(ledger))
        data['closeout_audit_2026_09_26'] = {'at_utc': STAMP, 'report': REPORT, 'audit': AUDIT,
                                          'scope': 'Local records only; historical entries and balances unchanged; no remote query or new consumption/submission.'}
        write(ledger, json.dumps(data, indent=2, ensure_ascii=False) + '\n')

    notice = '''## Current closeout - 2026-09-26 (supersedes historical directives below)

Local closeout is complete. Read `PLAN.md` v4 and
`docs/research/closeout_review_2026-09-26.md`; `STATE.json` owns current status.
exp067d is EVALUATED, export complete; exp067 is stopped for this competition.
Retain exp064 submission 56535761, recorded Public LB 0.953. No training, GPU launch,
submission, successor preparation or public push is authorized. ep015 remains OFF.
Ledger remaining is 16.752765 h with no reservations. Next: verify the final selection
on the site before close; this closeout did not verify live selection or remote quota.
The corrected CPU audit reproduces scorer TP/FP/FN 3/2/9 and separates those semantics
from two exact direct-edge events. Geometry-only controls give 4/7 for tau-off alone
and 7/7 with distance14 plus tau-off; they do not establish decoded performance.
Historical RUNNING, next-launch and broad causal claims below are superseded.
Review waivers remain historical NO_PASS, never retroactively converted to PASS.

'''
    for name in ['EXP067_STATUS.md', 'GOAL.md', 'HANDOUT.md', '.private/current/CONTINUATION.md',
                 '.private/current/MEMORY.md', 'docs/research/PROJECT_HANDOFF.md']:
        old = read(name)
        first, rest = old.split('\n', 1)
        write(name, first + '\n\n' + notice + rest)
    print('Closeout documents updated; original bytes archived. Regenerate checkpoints next.')


if __name__ == '__main__':
    main()
