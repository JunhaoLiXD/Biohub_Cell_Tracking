# Research handoff and traceability

Current working parent (2026-09-06): the reproduced public
`analyticaobscura/biohub-lb-941` configuration, `repro_038_public_0941_exact_copy`.
Submission 56044403 completed at Public LB **0.941** using released pretrained
weights without training. The source, actual epoch-2 checkpoint and submission
graph were audited.

The completed validation step was `val_039_public_0941_train16`: it established a fixed
16-video validation baseline with the val_008 selector/scorer while preserving
the parent test submission bytes. This is a validation gate, not an optimization
or an additional leaderboard submission. Historical train16 scores (0.925252 for
the original 0.933 parent and 0.927316 for EMA) are descriptive controls.

The run completed as KEEP after an experiment-specific Claude PASS, smoke pass and
46 local tests. Train16 score is 0.935978 (adjusted edge 0.916930, division 0.190476),
with 44b6 at 0.921800 and 6bba at 0.940332. All runtime identity checks passed and
the test submission remained byte-identical to the Public LB 0.941 parent. Runtime
was 1.295755 tracked GPU hours; no reservation remains. The baseline is published
as `src/biohub_v05_public_0941_train16_baseline.ipynb`.

The proposed next controlled test adds only per-track motion EMA (alpha 0.4) to
this parent while retaining velocity weight 0.5 and protecting division TP/FP/FN.
It has not been created or launched.

## Local evidence chain

The local research workspace intentionally excludes agent documents, configs,
controller scripts, experiment records and large artifacts from Git. Their presence
on this machine does not mean they have been backed up to the remote repository.
Public milestone notebooks and this compact overview remain shareable artifacts.

Resume by reading AGENTS.md, GOAL.md, .private/current/CONTINUATION.md and
.private/current/MEMORY.md, then inspect the active experiment.json. Each experiment
records its parent, hypothesis, exact change, protocol, immutable source/config
hashes, independent review, smoke checks, remote identity, budget and final evidence.
The detailed evidence map is research/WORKING_BASELINE.md in the local workspace.

Old handoffs and auto-memory entries have been preserved under
.private/archive/checkpoints/. Current entry points explicitly supersede them.
Claude's automatic project memory index points back to the same current handoff.
CURRENT_BEST.json remains the legacy formal promotion record, not the active work queue.

## Interpretation

The native parent train4 proxy is not comparable with train16. Released models saw
training videos, so absolute train-derived scores are optimistic. Public leaderboard
evidence does not identify which individual component caused a gain. Later changes
must be paired against the new baseline with both specimens and both score components
reported. Fresh experiment-specific review, smoke and budget gates apply to each launch.
