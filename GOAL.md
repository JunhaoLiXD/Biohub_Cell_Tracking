# Project Goal

## Current authorization and status: v4 Kaggle run, 2026-09-23 UTC

The user explicitly instructed Codex to push and run the v4 notebook after being told formal admission remained BLOCK. This is a one-time user waiver of the Codex PASS launch gate for `exp_061_zon_lb_submission_repair_v4`; it is not a PASS or a change to future gates. The immutable snapshot passed direct local smoke. Kaggle accepted kernel version 1 at `https://www.kaggle.com/code/lingxd/biohub-exp061-zon-deploy-v4` at 2026-09-23T01:50:17Z. The controller record truthfully shows the review waiver and SUBMITTED state; two GPU hours are reserved, preserving the six-hour floor. The frozen inference policy is unchanged. No leaderboard submission was authorized or made. Wait for the user's completion notice, then check and collect once, audit the current-run CSV and receipts, and reconcile GPU time. The hidden rerun failure cause of v2 remains unknown.

## Current status: exp061 three-submission failure diagnosis, 2026-09-22 UTC

The one user-authorized zon resubmission was consumed by submission 56454236.
Two earlier copy-only submissions (56442230 zon and 56447637 byte-identical
repro_059 xyonly) failed with incorrect-format errors. The full-inference v2
submission reached hidden rerun and failed with an unhandled error, no score, and
totalBytes=0. Its visible run and development audits passed. Kaggle withholds the
hidden traceback, so the exact cause is unknown; extra replay workload under the
two-hour watchdog is a hypothesis only. No leaderboard resubmission or GPU launch
is currently authorized. Preserve all three receipts and frozen prediction
strategy. Diagnosis: `docs/research/exp061_three_submission_failure_diagnosis.md`;
authenticated error: `experiments/exp_061_zon_lb_submission_repair_v2/leaderboard-error.json`.

## Canonical workflow authorization (current)

The detailed operational handoff is `docs/research/PROJECT_HANDOFF.md`. For the
next research cycle, Claude Code is the strategy author and implementation lead;
Codex is the independent strategy challenger and implementation reviewer.
Claude Code must state the actual parent, one falsifiable hypothesis, exact
change, validation protocol, budget, artifacts, risks, and rollback/stop rule.
Codex must independently challenge methodology, leakage, graph semantics,
provenance, numerical stability, tests, reproducibility, and budget. Claude Code
revises until a versioned strategy record explicitly says `CONSENSUS`; without
consensus, execution stops and the disagreement returns to the user.

After consensus, all existing experiment gates remain in force: explicit
tracked hypothesis/change/parent, local and snapshot smoke, fresh
experiment-specific review, controller admission, resource reservation, and
independent Codex artifact/metric audit. Future experiment configs must set
`admission.require_codex_review: true` (optionally `reviewer_provider: codex`),
use `scripts/request_codex_review.py`, and require a fresh Codex `PASS` before
execution. Historical Claude-based configs and receipts, including exp_055,
remain preserved evidence and are not rewritten. The late-stage accuracy push may
include explicitly authorized high-risk/high-reward experiments, including
potentially framework-changing designs. They may fail, but must be bounded,
reversible, fail-fast, leakage-free, reproducible, and honestly distinguish
local proxy evidence from Public LB evidence. Preserve budgets, the six-hour GPU
reserve, model allowance reserves, and no-automatic-LB/promotion rules. The
migrated controller accepts the Codex admission field while remaining
backward-compatible with historical records.

## Active execution directive

`exp_055_original_score_joint_bootstrap_smoke_fix` is the only active experiment
and remains `SUBMITTED`. Until the user provides its completion notice, wait and
do not poll, collect, relaunch, rebuild, request another review, prepare a
successor, submit to the leaderboard, or promote. After the notice, check and
collect exactly once and independently audit the graph hashes, score rows,
solver receipt, metrics, and submission integrity. Only after a valid terminal
result and audit may Claude Code author the next strategy for Codex challenge
and revision to explicit `CONSENSUS`.

All dated experiment sections below this directive are historical unless they
match `STATE.json` and the active experiment record. Their former "current" or
"next" wording does not supersede this directive.

## Current launch: exp_053 SUBMITTED, 2026-09-13

exp_053_original_score_joint_repair launched once at 2026-09-13T04:15:17Z as
lingxd/biohub-exp053-original-score-joint-repair. Two GPU hours are reserved
from the user-reconciled 30-hour balance; preserve six protected hours.
Fresh Claude formal PASS was recovered verbatim from the SAME review session's
full assistant message after final stdout omitted the required verdict line.
Prompt/session/timestamps and unchanged snapshot were verified; original MISSING
stdout and recovery provenance are preserved in review-recovery.json and
review-same-call-events.json. No additional model call occurred. Snapshot smoke
passed at 04:14:49Z. All 16 final-stage prediction-only repair fixtures match
exactly and 13 combined tests passed. The separate upstream Windows smoothing
replay differs by <=1.71e-13; remote input/output graph hashes remain strict.

Wait for user completion notice, then check and collect once and independently
audit. Do not poll, relaunch, rebuild, review again, relax hash gates, submit to
leaderboard or promote. Context remains REJECT_LOCAL_POLICY. The remote run also
tests cross-platform solver parity; no remote quality result is available yet.
Older preparation text below is historical and superseded by this launch.


## Current preparation: exp_053, 2026-09-13

Fixed original-score integration is snapshotted as exp_053_original_score_joint_repair.
All 16 prediction-only final-stage repair fixtures match exact nodes and edges;
13 combined tests and preliminary smoke passed. The separate upstream Windows
smoothing replay differs by <=1.71e-13; remote input/output graph hash gates remain
strict. See docs/research/exp053_original_score_integration.md for scope and the
isolated hash-pinned Linux SciPy 1.18.1 solver. Fresh Claude review is pending.
GPU balance is 30 hours including six protected hours; no reservation or launch.


## Active authorization: original-score joint repair, 2026-09-12

The user reported 30 GPU hours remaining and authorized the next step from the
concrete original-score successor design. Implement the fixed original-score
policy with prediction-only provenance, prove exact parity on all 16 local
graphs, then obtain one fresh experiment-specific Claude review and snapshot
smoke before one bounded remote validation with a two-hour reservation.
Preserve six GPU hours. The context hypothesis remains REJECT_LOCAL_POLICY;
no parameter sweep, training, leaderboard submission or promotion is authorized.
Exact model allowance is unavailable; disclose before the bounded review and
never automatically retry timeout or quota stops.


## Current result: local joint graph pilot completed

The zero-GPU joint graph pilot completed and all 48 output graphs passed independent audit. Original-score repair scores 0.9535869213120838 (+0.01485368362467987); context repair scores 0.9519261693422604 (+0.013192931654856466). Division remains 4/8/8. The preregistered context-increment gate failed; retain REJECT_LOCAL_POLICY for that hypothesis. The original-score control is a promising separate candidate, not a Public LB result. GPU balance was reconciled to 30 hours by user report on 2026-09-12, including six protected hours.

Review the concrete original-score joint-repair successor design in .private/research/diag052_original_score_successor_design.md. Preserve the rejected context gate and fixed parameters; no sweep. Before any remote validation, integrate prediction-only provenance-safe inference, prove exact parity with all 16 local graphs, and obtain a fresh experiment-specific Claude PASS plus snapshot smoke and budget admission. No leaderboard submission or promotion. Results: experiments/local_052_joint_graph_pilot_v1_attempt02/result.json.

Thirteen focused tests passed. Initial attempt stopped on reused recovery node IDs; attempt02 checks identity through all stages and passed all 1,776 input hashes. Identity-checked residual v3 reproduces 242 residuals, 85 accepted and original probability top1/top3/top8=109/212/241. Grouped fixed-rule panels are not independent heldout generalization. No remote run or model review occurred.

Report: `.private/research/diag052_completed_analysis.md`. Older diag_051 preparing and rank-repair work-queue text below is historical and superseded.


## Active authorization: local joint graph pilot, 2026-09-11

The user accepted the bounded continuation plan: finish rank-diagnostic tests,
then compare no-change, original-score joint repair, and five-frame-context joint
repair using the existing diag_051 cache. This supersedes the stale secondary-
appearance-first checkpoint. Run one fixed zero-GPU screen, with video-grouped
discovery/confirmation panels, full graph scoring, conflict and fork protection,
and no GT in action generation. Preregistered specification:
`.private/research/diag052_protocol_v1.json`; local record:
`experiments/local_052_joint_graph_pilot_v1/experiment.json`.

Timebox local exploration to two days. No post-result parameter sweep. Only a
successful gate permits preparing one bounded remote validation, which still
requires a fresh experiment-specific Claude PASS, snapshot smoke, and budget
reservation while preserving six GPU hours. No leaderboard submission, promotion,
new training architecture or public-source diversion is included. Exact model
allowance is unavailable; no external model review is needed for the local screen.
The earlier one-child Luna repair assignment belongs to the prior interrupted
task, not a standing requirement to delegate this new implementation.

## Completed diag_051 result, 2026-09-10

diag_051 completed as valid diagnostic KEEP at 0.9387332376874039, with exact
repro_041 test/validation CSV bytes. Independent snapshot, submission, 176
graph/matching payload and 1600 NPZ audits passed; all 16 final graph scores
reproduce the frozen CSV. Runtime was 1.163561077056389 tracked GPU hours;
15.667408447732495 remain including the protected six hours.

The measured pool covers 242/258 fragmentation edges, but only three connect
free endpoints. Seventy-five accepted true links disappear during motion
relinking. Joint sparse GT repair gives +0.0862015291 proxy and division 9/8/3;
this is conditional structural headroom, not a deployable gain. Simple appearance
and motion ranks remain weak. Recommend a grouped offline five-frame
cut-and-reconnect feasibility proposal with conflict and division handling.
Retain EMA 0.4 and the separate verified Public LB 0.944 candidate. No successor,
training, review, remote launch, LB submission or promotion is authorized by this
completed analysis. Do not rerun diag_051 or add telemetry. Full report:
`.private/research/diag051_completed_analysis_2026-09-10.md`.

The user subsequently authorized the offline pilot and explicitly requested
Luna medium for code work. Review found a masked-row alignment bug in the initial
rank diagnostic; `offline_feasibility.json` is invalid historical output and its
grouped-feasibility PASS interpretation is withdrawn. Independent probability
top-1/top-3/top-8 counts are 109/212/241 of 242 residuals, with 85 accepted.
One bounded `gpt-5.6-luna` medium task repairs extraction and adds regression
tests. Use a versioned corrected residual-conditioned diagnostic before any
GT-blind full-graph policy screen, with original-score and no-change controls.
No grouped holdout or graph-editing feasibility pass has been established.
See `.private/research/diag051_next_step_review_2026-09-10.md`. Remote launch,
leaderboard submission and promotion remain outside this local authorization.

## Active authorization: diag_051 retained-parent evidence export

The user's latest request authorizes the next experiment under the agreed plan:
one behavior-preserving evidence export from repro_041, as specified in
`.private/research/diag051_tracklet_evidence_design.md`. This supersedes older
no-successor wording below. The matched negative exp_050 closes TTA composition;
the next priority is the retained-parent reachable-error audit before a
longer-context association pilot. Reserve two GPU hours, protect six hours,
require fresh experiment-specific Claude PASS and snapshot smoke, then launch
once. No leaderboard submission, promotion or training launch is included.
Exact weekly model allowance is unavailable; use one bounded review and do not
automatically retry a timeout/quota stop. After launch wait for user completion
notice; check and collect once, without repeated polling or relaunch.

<!-- BEGIN EXP050 HANDOFF -->
## Current exp_050 handoff, 2026-09-09

exp_050 completed as valid contract-only KEEP at 0.9359778132422281. The matched feature-TTA effect B-A is -0.004908183342538841; both specimen combined scores decline with TTA. Division explains 82.47% of the loss (off 4/9/8 versus on 3/8/9). All 29 runtime checks passed; independent CSV arithmetic, receipts and 16 final graph audits passed. Both validation CSV and test submission are byte-identical to historical val_039. Retain reproduced EMA 0.4 as the train16 reference and verified Public LB 0.944 as a separate candidate. Close the TTA/EMA composition screen under the accepted negative-effect stopping rule.

Do not launch C/D, repeat exp_050, resubmit identical bytes, or promote. Propose a bounded residual association/division audit on the retained EMA reference before a separately specified structural intervention. No new architecture or training launch is authorized. Runtime was 1.0982387771125 tracked GPU hours; 16.830969524788884 hours remain including the protected six hours. Full analysis: .private/research/exp050_completed_analysis_2026-09-09.md.

Strategy: `.private/research/val049_next_strategy_resolution.md`. Local audit: `.private/research/val049_source_audit/README.md`. Three-new-arm ceiling with 2-hour reservations each; preserve six GPU hours. Current arm state: KEEP. Any advancement to independent reproduction must clear the retained repro_041 quality floor; contract KEEP alone is not advancement.
<!-- END EXP050 HANDOFF -->
## Completed authorization record: post-val_049 discussion and conditional execution, 2026-09-09

The user authorized Codex to discuss the proposed source/error audit and bounded
TTA/EMA factorial plan with Claude, reach agreement, and then execute it. First
perform the local audit after strategy agreement; choose remote arms from its
evidence. Every arm still needs its own fresh Claude PASS, snapshot smoke, tracked
hypothesis, actual parent, exact change, and sufficient budget. Retain the six-hour
GPU reserve. No leaderboard submission, promotion, training pilot, alpha/threshold
sweep or important-branch push is included. Record accepted strategy amendments
in `.private/research/val049_next_strategy_resolution.md`. Older no-successor text
describes prior authorization and does not override this new permission.

## Completed result record: val_049 baseline, 2026-09-09

val_049 completed as contract-only KEEP at train16 0.9310696298996892, down 0.0076636077877147 versus reproduced EMA 0.4 and 0.0049081833425389 versus val_039. All 25 runtime checks and the independent CSV arithmetic audit passed; test bytes exactly match the verified Public LB 0.944 submission. Division TP/FP/FN is 3/8/9 versus 4/8/8; division explains 65.24% of the loss. Both specimen combined scores fall. Retain the Public LB candidate and the EMA train16 reference separately; no promotion.

Audit common-source equivalence and the division/node-count differences before specifying matched TTA/EMA controls. The complete configuration comparison cannot isolate TTA. Do not resubmit identical output or relaunch val_049. No new remote experiment is part of this result analysis.

Runtime: 1.1696664033688888 tracked GPU hours. This record is superseded by
exp_050; current remaining budget is 16.830969524788884 hours including the
six-hour reserve. Raw GEFF artifacts are not the final filtered validation graphs.
The full report is `.private/research/val049_completed_analysis_2026-09-09.md`.


## Completed authorization record: 2026-09-09 research continuation

The user authorized substantive discussion with Claude Code followed by experiments.
First establish val_049_public_0944_train16 on behavior parent repro_048 with
unchanged test inference and frozen val_039 selector/scorer. Obtain fresh Claude
PASS and snapshot smoke before one Kaggle launch, budgeted at 2 GPU hours.
Discuss NEXT_RESEARCH_PRIORITIES.md, including the subsequent matched TTA/EMA
factorial design. Subsequent choices depend on the completed baseline evidence.
No leaderboard submission or promotion is included in this validation launch.

<!-- BEGIN AUTO-CHECKPOINT (generated by scripts/render_checkpoint.py — edit STATE.json, not this block) -->
## Active checkpoint (single source of truth: `STATE.json`)

- **Active experiment:** `exp_061_zon_lb_submission_repair_v4`
- **Controller state (from `experiments/exp_061_zon_lb_submission_repair_v4/experiment.json`):** COLLECTING
- **Phase:** EXP061_V4_LB_PENDING_AND_V5_KERNEL_SUBMITTED
- **Leaderboard submission:** NOT authorized
- **Summary:** The v4 zon-only deployment kernel (lingxd/biohub-exp061-zon-deploy-v4 version 1) ran COMPLETE in 32.5 minutes and was audited read-only by Claude: the current-run zon CSV reproduces the historical development hash 2593a543 exactly, config_equal_frozen_parent is true, checkpoint provenance is verified, 16 views per frame including 8 Z-reflected executed, and there are no nonfinite or cache-integrity events. On that audit the user authorized one Public LB submission, made at 2026-09-23T03:47:28Z as submission 56481730, now PENDING. The v4 kernel itself still carries no Codex PASS (one-time user waiver of a formal admission BLOCK). A corrected v5 was then built and pushed as a fallback: kernel lingxd/biohub-exp061-zon-deploy-v5 version 1 at 2026-09-23T04:08:52Z, fixing the two scale hazards the audit found (rerun-aware deadline, view cache off the collected output path) with no change to any predicted value. v5 also runs under a one-time user waiver, not a Codex PASS.
- **Next action:** Two things are outstanding and neither should be polled. (1) Public LB submission 56481730 (v4): wait for the user notice, then query the authenticated history once and apply the decision rule against repro_059 0.947 (>=0.948 adopt zon as new parent; ==0.947 sub-precision null, which fires the ARMED option-B reminder; <=0.946 revert). (2) v5 kernel lingxd/biohub-exp061-zon-deploy-v5 version 1: wait for the user completion notice, then check status and collect once, verifying the current-run zon CSV still reproduces 2593a543, that feasibility_worksheet.view_cache_outside_working_dir is true and the kernel output is now small, and reconcile actual GPU time. If 56481730 returns a score, v5 is a spare and needs no LB submission. If 56481730 errors again, v5 becomes the next LB candidate and needs its own explicit authorization plus a cap check. Do not change the frozen inference strategy.

_Generated from `STATE.json` (updated 2026-09-23T04:10:12.711283+00:00). Do not hand-edit this block; edit `STATE.json` and rerun `python scripts/render_checkpoint.py`. Full authorization detail lives once in `GOAL.md`._
<!-- END AUTO-CHECKPOINT -->

## Active authorization detail (repro_048) — canonical

On 2026-09-08 the user authorized one copy-and-edit execution of the current
credible public 0.946 notebook and one leaderboard score submission after valid
output. Only unavailable owner-specific dataset mount paths may differ from the
archived upstream bytes; no algorithm or parameter edits are authorized.

`repro_047_public_0946_edge_feature_tta_exact_copy` is an unlaunched preflight
REVISE record. Claude found that its collector incorrectly required an upstream
train4 metric artifact that this notebook does not create. The corrected immutable
successor is `repro_048_public_0946_exact_copy`: local evaluation is limited to
execution, pinned artifact identity, and submission graph integrity, while quality
is decided by the external leaderboard. Claude returned PASS and snapshot smoke
passed. The private Kaggle kernel launched once at 2026-09-08T18:58:39Z with a
2.0-hour reservation.

The user reported completion on 2026-09-08. The run was checked and collected
once, passed the declared integrity contract, and consumed 0.35718106635611113
GPU hours. Immediately before submission, remote and local history both showed
zero submissions for the local day and the output hash was nonduplicate. Kaggle
submission 56105868 completed at Public LB 0.944. The current public notebook's
saved output is byte-identical to ours, so the advertised 0.946 is not reproducible
from the shared materials. No training occurred during either inference run.
Do not resubmit, relaunch, promote, start a follow-on experiment, publish a
milestone, or push without new authorization.

## Active completed-result detail (exp_046) — canonical

The user authorized one bounded Claude review and one conditional Kaggle validation
launch for `exp_046_public_0942_motion_ema_sparse_soft`. Claude returned formal PASS
with no required changes, the immutable snapshot smoke passed, and the experiment
launched once. The only algorithmic change from terminal KEEP behavior parent
`repro_041_public_0941_motion_ema` was alpha 0.6 on updates satisfying innovation
greater than 1.25, source age at least 3, a finite second assignment candidate, and
assignment margin at least 0.5; alpha 0.4 remained the default.

The completed score is 0.9387340065001502, a delta of only
+0.000000768812746243519 versus repro_041 and below the preregistered +0.0001 gate,
so the terminal controller state is valid REJECT. All contract checks passed.
Division remained 4/8/8, both specimens changed only microscopically, and no video
changed edge TP/FP/FN. Four videos rose, two fell, and ten were exactly unchanged;
the tiny aggregate gain came from six fewer predicted nodes through the adjusted
edge density term, not better association confusion counts.

The runtime policy fired on 4240 of 345908 validation updates (1.2258 percent) and
1295 of 109993 test updates (1.1773 percent). Per-video soft counts exactly matched
the guarded-1.25 telemetry, proving implementation fidelity. Runtime was
1.1107059715155556 GPU hours and 19.456055771626385 tracked hours remain including
the protected 6-hour reserve. Retain fixed alpha 0.4 and close the EMA-alpha tuning
branch. No relaunch, reproduction, leaderboard submission, stronger/denser EMA
sweep, Claude call, successor, promotion, milestone v06, or push is authorized.
Detailed evidence is in
`.private/research/exp046_completed_analysis_2026-09-07.md`.

## Active authorization detail (diag_045) — canonical

On 2026-09-07 the user authorized validation of the corrected successor to the
failed telemetry diagnostic. `diag_045_public_0942_motion_ema_telemetry_v2` uses
terminal KEEP `repro_041_public_0941_motion_ema` as its actual behavior parent;
`diag_044_public_0942_motion_ema_online_telemetry` is retained only as the failed
diagnostic predecessor. Fixed EMA alpha 0.4, velocity weight 0.5, models,
checkpoints, assignment decisions, output graph, frozen train16 samples, and scorer
remain unchanged.

The only change is read-only observability: all telemetry counts are converted to
native Python integers, both test and validation payloads require strict JSON
serialization, finite/nonfinite assignment-margin coverage is recorded, guard
effects are decomposed into innovation-only, age, finite-margin, margin-at-least-0.5,
and joint counts, and thresholds are 1.0, 1.25, 1.5, and 1.75. Telemetry must not
branch on specimen, video identity, or ground truth. Exact parent submission bytes,
aggregate/specimen/video metrics, division counts, and EMA execution counts remain
hard gates. The complete local suite passed 70 tests.

The one authorized fresh experiment-specific Claude review returned formal
`VERDICT: PASS` at 2026-09-07T22:13:04Z with no required change. Snapshot smoke
passed at 22:13:31Z. The experiment launched once at 22:14:09Z as
`lingxd/biohub-diag045-public0942-ema-telemetry-v2`; 2.0 GPU hours are reserved
from 21.715319265786388 tracked hours, preserving the 6-hour reserve. Do not poll,
relaunch, rebuild, or review again. Wait for the user completion notice, then check
and collect once. No leaderboard submission, promotion, milestone v06, successor
experiment, or push is authorized.

## Active failed-result detail (diag_044) — canonical

The user authorized one fresh Claude review of
`diag_044_public_0942_motion_ema_online_telemetry` and continuation to one Kaggle
launch if the review returned formal `VERDICT: PASS` with no required change and
snapshot smoke passed. The parent is terminal KEEP
`repro_041_public_0941_motion_ema`; fixed EMA alpha 0.4, velocity weight 0.5, all
models, checkpoints, inference decisions, samples, and scoring remain frozen.

The only change is read-only online telemetry inside motion relinking. It records
per-video innovation quantiles, track-age quantiles, local assignment-cost-margin
quantiles, and prospective trigger counts at thresholds 1.0, 1.25, 1.5, 2.0, and
3.0, including a label-free guard requiring track age at least 3 and margin at least
0.5. The telemetry must not use specimen, video identity, or ground truth. Exact
parent test submission SHA256, aggregate/specimen/video metrics, division counts,
and EMA execution counts are hard gates. The full local suite passed 65 tests.

The one bounded Claude review returned formal `VERDICT: PASS` at
2026-09-07T20:18:15Z with no required changes. Snapshot smoke passed at 20:18:45Z,
and the experiment launched once at 20:19:02Z as
`lingxd/biohub-diag044-public0942-ema-telemetry`.

Kaggle later reported `ERROR`; the controller recorded terminal `REMOTE_FAILED` at
21:34:26Z. Test inference and all 16 validation videos completed, but the final
contract failed at `json.dumps(VALIDATION_STAGE_STATS)` because a new guarded
telemetry count was `numpy.int64`. The candidate submission and validator-results
hashes exactly match repro_041, proving prediction behavior was unchanged. Test
telemetry was saved, but validation telemetry and `metrics.json` were not persisted,
so this is not a complete diagnostic result. The controller conservatively charged
2.0 GPU hours, leaving 21.715319265786388 tracked hours including reserve. See
`.private/research/diag044_remote_failure_analysis_2026-09-07.md`.

Do not repair, relaunch, rebuild, request another review, create a successor,
submit to the leaderboard, promote, publish milestone v06, or push without explicit
user authorization. Any later retry must be a new experiment with explicit native
integer conversion, an end-to-end JSON-serialization regression test, a fresh
experiment-specific Claude PASS, and snapshot smoke PASS.

## Active result detail (exp_043) — canonical

`exp_043_public_0942_motion_ema_adaptive_reset` completed and was independently
audited as terminal REJECT. It scored 0.9368238444059783, down
0.0019093932814255865 from its exactly reproduced fixed-alpha-0.4 parent and down
0.0008569896754508921 from the rejected global-alpha-0.6 experiment. All execution,
identity, checkpoint, frozen-protocol, submission-stability, and adaptive-branch
checks passed, so this is a valid negative result rather than a failed run.

The adjusted-edge contribution fell by 0.0009570123290446597 and the weighted
division contribution fell by 0.0009523809523809545. Division TP/FP/FN changed
from 4/8/8 to 4/9/8. The worst video was `44b6_c15fded2` at
-0.016110659649892112 adjusted-edge delta versus val_039. Actual online execution
used 135,998 hard resets and 209,874 base updates: a 39.3203% reset fraction, far
above the explicitly approximate 14.1216% prelaunch final-graph replay estimate.

Reject the threshold-1.0, alpha-1.0 hard-reset rule and retain fixed alpha 0.4.
Recommended next step, not authorized or created: a byte-identical no-effect
online-telemetry experiment to measure the true runtime innovation distribution
and calibrate a genuinely rare label-free soft-update gate. Do not relaunch,
reproduce, or submit exp_043. No leaderboard submission, formal promotion,
milestone v06, successor experiment, review, remote launch, or push is authorized.
See `.private/research/exp043_completed_analysis_2026-09-07.md`.

## Prior result detail (exp_042) — canonical

`exp_042_public_0942_motion_ema_alpha06` completed and was independently audited
as terminal REJECT. Alpha 0.6 scored 0.9376808340814292, a
-0.0010524036059746944 change versus the exactly reproduced alpha-0.4 parent.
All execution, identity, frozen-protocol, checkpoint, and submission-stability checks
passed. The failed research gates were aggregate non-inferiority, worst-video delta
at least -0.002, and division FP at most 8. Division counts changed 4/8/8 to 4/9/8;
the extra FP on `6bba_0c7fa718` accounts for most of the score loss.

Alpha 0.4 remains the leading reproducible candidate with user-reported Public LB
0.942. Do not submit or reproduce alpha 0.6 and do not run a dense global-alpha
sweep. The later adaptive hard-reset branch was attempted as exp_043 and rejected;
the newer active result section owns the current recommendation. See
`.private/research/exp042_completed_analysis_2026-09-07.md`.

## Prior authorization detail (exp_042) — canonical

The user authorized one controlled Kaggle launch of
`exp_042_public_0942_motion_ema_alpha06` on 2026-09-07. Its actual parent is
terminal KEEP `repro_041_public_0941_motion_ema`. The only algorithmic change is
motion-relink EMA alpha 0.4 to 0.6; velocity multiplier remains 0.5, and all models,
checkpoints, detector, association, ILP, gap closing, division logic, frozen train16
samples, and scoring functions remain fixed.

The deterministic local suite passed 45 tests; the fresh
experiment-specific Claude review returned formal `VERDICT: PASS`; snapshot smoke
passed; and the 16 embedded val_039 per-video adjusted-edge baselines exactly match
the source artifact with SHA256
44f3f7942943bbc2315acd2824604524fbec68d0b0409da84f553fc196b075e5.
The experiment launched once at 2026-09-07T15:24:10Z as
`lingxd/biohub-exp042-public0942-ema-alpha06`; controller state is SUBMITTED and
2.0 GPU hours are reserved. Do not poll, relaunch, rebuild, or request another
review. Wait for the user to report completion, then check and collect once. No
leaderboard submission, formal promotion, milestone v06, successor experiment, or
remote push is authorized.

## Active leaderboard result detail (repro_041) — canonical

The user reported on 2026-09-07 that Kaggle submission 56067514 completed at
displayed Public LB 0.942, a displayed +0.001 over the reproduced 0.941 parent.
The required post-notification Kaggle lookup was attempted, but the current CLI
could not authenticate and returned no submission row. Record 0.942 only as the
user-reported three-decimal Kaggle display value; do not claim API verification or
greater precision.

The leaderboard direction agrees with the exactly reproduced frozen-train16 gain
of +0.002755424445175847. Motion EMA alpha 0.4 is now the leading reproducible
inference candidate with positive local and Public LB evidence. The recommended
next controlled experiment is alpha 0.6 with velocity multiplier 0.5 and everything
else fixed, explicitly gating aggregate, both specimens, division counts and the
video-level regression tail. This is a proposal only. No successor experiment,
new leaderboard submission, formal promotion, milestone v06, or remote push is
authorized. See `.private/research/repro041_leaderboard_analysis_2026-09-07.md`.

## Prior leaderboard submission detail (repro_041)

The user explicitly authorized one format-correction Claude review and one
conditional leaderboard submission. The retry returned formal `VERDICT: PASS` at
2026-09-07T02:48:44Z. The live submission gate then passed for 2026-09-06 in
America/New_York: remote count 0/3, local count 0/3, and no duplicate submission
SHA256. Kaggle submission 56067514 was created at 2026-09-07T02:54:59.363000Z
from kernel `lingxd/biohub-repro041-public0941-motion-ema`, version 1, output
`submission.csv`. Its current status is PENDING and no score is available.

The single authorized submission has been consumed. Do not submit again or poll.
Wait for the user to report scoring completion, then query submission 56067514 once,
record its score, and compare it with the reproduced 0.941 parent. No promotion,
milestone v06, successor experiment, or remote push is authorized.

The completed-run detail below remains evidence but is superseded as the active
instruction.

## Completed reproduction detail (repro_041)

`repro_041_public_0941_motion_ema` completed as controller `KEEP` at
0.9387332376874039. Independent raw-artifact analysis passed: aggregate and both
specimen metrics match exp_040 within absolute tolerance 1e-12 and zero relative
tolerance; division counts, EMA telemetry, validator CSV, inference identity,
validation stage statistics and submission bytes match exactly. Submission SHA256
is fd1162bfc09b6d06413701aa898eb14bc5df9cc5bfd999fe598bf81fbf125515.
Runtime was 1.060321672935 GPU hours, leaving 10.073829110627782 hours including
the 6-hour reserve. The analysis is recorded in
`.private/research/repro041_completed_analysis_2026-09-06.md`.

The authorized one-time post-run Claude process completed successfully and its text
substantively stated PASS, but it omitted the required final `VERDICT: PASS` line.
The deterministic receipt therefore correctly records `MISSING` and
`CHANGES_REQUESTED`. Do not infer formal PASS and do not retry automatically. No
leaderboard submission, promotion, milestone v06, new experiment, or remote push is
authorized. Await explicit user direction after reporting this format failure.

The launch instructions below are historical and superseded.

## Prior authorization detail (repro_041)

Launched once at 2026-09-06T20:54:36Z as
`lingxd/biohub-repro041-public0941-motion-ema`. Fresh prelaunch Claude PASS at
20:54:10Z and snapshot smoke PASS at 20:54:14Z. Two GPU hours are reserved.
Do not launch or poll again. Wait for the user to report completion, then collect,
independently audit and perform the one-time final Claude review below. Its pending
receipt and instructions are in the experiment's post-run-review files.

The user authorized `repro_041_public_0941_motion_ema`, an independent identical
reproduction of terminal KEEP exp_040. Reference score: 0.9387332376874039;
submission SHA256: fd1162bfc09b6d06413701aa898eb14bc5df9cc5bfd999fe598bf81fbf125515.
Only the final evidence contract changes; aggregate and specimen metrics use
absolute tolerance 1e-12 with zero relative tolerance, while division counts,
EMA execution telemetry and submission bytes must match exactly. The deterministic
validator passes six negative controls and confirms all earlier cells are identical.
Budget estimate: 2.0 GPU hours, preserving the 6-hour reserve.

Follow normal fresh prelaunch Claude PASS and smoke rules. This run additionally
requires ONE post-run Claude review of collected artifacts and Codex analysis,
recorded separately as post-run-review.md and post-run-review.json so the prelaunch
review is preserved. This additional review is explicitly limited to repro_041;
future experiment/code review rules remain unchanged. The post-run review is pending
until the remote run completes and artifacts are audited. A controller KEEP alone
must not be described as final Claude approval. No leaderboard submission authorized.
Wait for the user to announce Kaggle completion; do not poll. The experiment record
owns execution state. Older proposals below are superseded by this authorization.


## Current checkpoint - 2026-09-06: EMA transfer screen KEEP

`exp_040_public_0941_motion_ema` completed as `KEEP`. Independent raw-artifact
analysis confirmed train16 score 0.9387332376874039, a +0.002755424445175847
improvement over val_039. Adjusted edge improved by +0.0018030434927949202 and
division Jaccard improved by +0.009523809523809545. Both specimen aggregates
improved; division TP/FP/FN changed from 4/9/8 to 4/8/8. All gates and runtime
checks passed, and EMA executed on both specimens. Runtime was 1.0788346668808333
GPU hours, leaving 11.134150783562783 hours including the 6-hour reserve.

This is a positive screening result, not yet reproducible or leaderboard evidence.
Video-level adjusted-edge deltas were heterogeneous: 8 positive, 1 zero, 7 negative,
with a worst decline of -0.003731827704801738. The recommended next step is one
independent exact reproduction of exp_040, gating on byte-identical candidate test
submission and exact aggregate/per-specimen metrics. This is a proposal only; no
reproduction, leaderboard submission, formal promotion, milestone v06, or push has
been authorized or created. See
`.private/research/exp040_completed_analysis_2026-09-06.md`.

The submitted-run instructions below are historical and superseded.

## Prior checkpoint - 2026-09-06: EMA transfer experiment submitted

The user authorized the next controlled experiment after discussing its meaning and
expected iteration count. `exp_040_public_0941_motion_ema` was submitted once at
2026-09-06T19:02:47Z to `lingxd/biohub-exp040-public0941-motion-ema` after a fresh
Claude PASS and smoke PASS. Its terminal KEEP parent is
`val_039_public_0941_train16`. It changes only the motion-relink
velocity estimator from latest one-frame displacement to per-track EMA alpha 0.4;
retain velocity multiplier 0.5 and every other inference and train16 scoring setting.
This is a validation run only, not a leaderboard submission or promotion.

Admission gates are explicit: frozen train16 protocol, aggregate improvement at least
+0.001 over 0.9359778132422281, per-specimen adjusted-edge regression no worse than
-0.002, division totals TP >= 4, FP <= 9, FN <= 8, and EMA runtime execution on both
specimens. Two GPU hours are reserved, leaving the 6-hour reserve untouched. The user
will report when the run completes; do not poll, relaunch, rebuild, or request another
review meanwhile.

The completed-baseline narrative below is historical context and remains authoritative
for the parent evidence.

## Prior checkpoint - 2026-09-06: frozen 0.941 baseline complete

The user resumed after the allowance reset. `val_039_public_0941_train16` is
COMPLETE/KEEP and is the controlled working parent for subsequent research.
Train16 score is 0.9359778132422281 (adjusted edge 0.916930194194609,
division 0.19047619047619047); 44b6 is 0.9217996822478786 and 6bba is
0.9403315937448887. All 26 runtime checks passed, including exact repro_038
test submission bytes before/after validation and actual epoch-2 best.pt identity.
The result is published as `src/biohub_v05_public_0941_train16_baseline.ipynb`.

The authorized next experiment is isolated motion-relink EMA on val_039:
alpha 0.4, velocity multiplier unchanged at 0.5, and all other 0.941 inference
and validation settings fixed. It must protect division counts (TP at least 4,
FP at most 9, FN at most 8), improve aggregate score by at least +0.001, and
avoid material adjusted-edge regression in either specimen. Its active execution state
is owned by `experiments/exp_040_public_0941_motion_ema/experiment.json` after creation.

The PAUSED/RUNNING narratives below are historical and superseded.

## Historical checkpoint - 2026-09-06: establish the 0.941 train16 baseline

The user authorized this step and synchronization of agent documents and memory.
Latest instruction: the user will report Kaggle completion. Stop polling and wait
for that notification before checking and collecting the existing run.
Remote history confirms submission 56044403 is COMPLETE at Public LB 0.941.
The working research parent is now `repro_038_public_0941_exact_copy`.
The old 0.933 pipeline and EMA are historical controls. Do not optimize the old parent
by default or require the new baseline to beat its train16 score to be admissible.

Historical run state: `val_039_public_0941_train16` was RUNNING after launch at 2026-09-06T13:34:05Z,
Claude PASS 13:32:23Z, smoke PASS 13:32:37Z; inspect experiment.json for latest state).
Preserve public inference and require test
submission SHA256 bf66c879298e71c5cce0326fbac5956ca567a344ae28f0d402dfc5003fba52bd
before and after validation. Reuse the exact val_008 train16 sample identities/order,
division strata and scoring functions. Bind the actual epoch-2 best.pt path/hash and
fix reporting from effective variables. Per-video stage statistics support later diagnosis.
This establishes a baseline; it is not an EMA or DeepCenter ablation. No further LB
submission or optimization is authorized in this step. Formal promotion remains separate.

Success is complete valid train16 evidence plus preserved inference, irrespective of
historical metric deltas. On completion collect, audit, publish the completed validation
milestone, and update the handoff. On failure retain evidence and diagnose; do not retry
a remote launch or a timed-out/quota-stopped Claude review automatically.

Model allowance is not visible. Use one bounded experiment-specific Claude review and
retain the 10 percent reserve policy. GPU budget allows the planned 2.0-hour run.
See `.private/current/MEMORY.md` and `research/WORKING_BASELINE.md` for the evidence map.

## Objective and evidence rules

Improve beyond the reproduced Public LB 0.941 working parent using controlled,
reproducible experiments. Primary metric: `adjusted_edge_jaccard + 0.1 * division_jaccard`.
Report both components and both specimens (44b6 and 6bba); compare only matching
sample/scorer protocols and explicitly describe changes to frozen inputs.
Training-derived absolute scores are optimistic. Public LB is secondary evidence.
Prefer one major variable per optimization; baseline establishment is a separate gate.
Formal promotion requires an explicit request, matching protocol, configured improvement,
per-specimen regression checks, methodology/leakage review, reproducibility evidence,
and required independent review. Do not silently promote CURRENT_BEST.json.

## Historical archive

Earlier checkpoints and superseded plans are preserved in `.private/archive/checkpoints/GOAL_before_train16_039.md`.
They are historical evidence and do not override this current handoff.
