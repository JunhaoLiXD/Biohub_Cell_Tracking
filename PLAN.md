# PLAN - v4, local closeout

<!-- BEGIN EP068 CURRENT -->
## Current ep068 continuation - 2026-09-27T02:26:01.458634+00:00

Experiment `exp_068_ep015_single_probe`: **SUBMITTED**. Fresh review: **PASS**.
The user authorized one ep015 run and one audited LB submission; 30 GPU hours were
reported at the new epoch. Ledger now 30.000000 h, reservations
`{"exp_068_ep015_single_probe": 2.0}`. No final re-selection, second probe or public push.

Wait for user completion notice; do not poll, rebuild or relaunch. Then check/collect once, run scripts/audit_exp068_collection_v2.py (verify admission_supplement_manifest.json), bind remote version/source, check remote history and conservative three/day cap, and perform the one already authorized LB submission if all gates pass.

CPU counterfactual is complete: all 128 subsets audited; original full per-movie
metrics reproduced. True-edge repair can change TP/FP/FN from 3/2/9 to 9/2/3 in this
restricted family. This is GT-assisted TRAIN diagnosis, not a learned result or LB
forecast. Report: `docs/research/ep015_continuation_2026-09-26/division_counterfactual_report.md`.
Older ep015-OFF and exp067-current instructions below are historical. exp067 training
remains stopped. Final retained submission remains 56535761 (recorded Public LB 0.953).
<!-- END EP068 CURRENT -->
## Active authorization - ep015 continuation, 2026-09-26

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
