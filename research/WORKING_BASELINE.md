# Working research baseline and evidence map

## Current override: repro_041 SUBMITTED, 2026-09-06

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


Updated 2026-09-06. The research director selected the reproduced public 0.941
configuration as the basis for subsequent experiments. Its completed controlled
working parent is now `val_039_public_0941_train16`.

| Evidence | Record |
| --- | --- |
| Working inference parent | experiments/repro_038_public_0941_exact_copy/ |
| Public result | Submission 56044403, COMPLETE, Public LB 0.941, kernel version 1 |
| Upstream attribution | analyticaobscura/biohub-lb-941; released pilkwang pretrained weights |
| Source SHA256 | 24253cae5a958b83d69e201719388031f5758080c5d01ca1a8e374f3a8225389 |
| Submission SHA256 | bf66c879298e71c5cce0326fbac5956ca567a344ae28f0d402dfc5003fba52bd |
| Actual DeepCenter | best.pt, epoch 2, SHA256 8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0 |
| Working experiment parent | val_039_public_0941_train16, COMPLETE/KEEP, train16 0.9359778132422281 |
| Fixed selection/scorer | val_008_public_0933_train16_launchable; 8 videos per specimen, 4 positive/4 negative |
| Historical controls | val_008 train16 0.925252; repro_036 EMA train16 0.927316; both Public LB 0.933 |

The baseline gate completed successfully. Test inference matched before and after
validation, all 26 runtime checks passed, and both components/specimens were recorded.
The cleaned milestone is `src/biohub_v05_public_0941_train16_baseline.ipynb`.

The positive successor candidate is `exp_040_public_0941_motion_ema`, an isolated
per-track motion EMA test (alpha 0.4, velocity multiplier 0.5) on val_039. It
completed as KEEP at 0.9387332376874039, a +0.002755424445175847 matched-protocol
gain. Both specimen aggregates improved; division TP/FP/FN changed from 4/9/8 to
4/8/8. Independent raw-artifact audit passed. Because the screen is not yet marked
reproducible and video effects are heterogeneous, val_039 remains the frozen baseline
while exp_040 is the leading candidate. One exact reproduction is recommended but
not authorized or created. Do not submit to the leaderboard or promote yet.

The parent native train4 proxy is not comparable with train16. The released models
saw training videos; train-derived absolute scores are optimistic. A Public LB gain
does not identify which component caused it. No closed search branch is reopened.

## Traceability and resume order

1. AGENTS.md: responsibilities and hard gates.
2. GOAL.md and .private/current/CONTINUATION.md: current authority and next actions.
3. .private/current/MEMORY.md: compact cross-agent decisions and closed branches.
4. Active experiment.json and immutable snapshot: actual execution state and code.
5. Review, smoke, logs, artifacts, metrics and budget receipts: evidence of outcome.
6. results.json / EXPERIMENTS.md: controller local evaluation registry.
7. SUBMISSION_BUDGET.json and experiment leaderboard-submission.json: separate LB evidence.

Historical entries are retained and explicitly subordinate to the latest checkpoint.
CURRENT_BEST.json is an older formal promotion record, not the working parent pointer.
No formal promotion, optimization, leaderboard submission or important-branch push
is part of the current baseline-establishment authorization.
