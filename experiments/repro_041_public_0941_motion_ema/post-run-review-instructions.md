# One-time final Claude review

This user-requested review applies only to repro_041 and is additional to normal
prelaunch review. Do not invoke it until remote completion, collection, and Codex
artifact analysis. Do not use request_claude_review.py against the terminal record:
that command is for prelaunch review and must not overwrite review.md or its status.

Run one narrowly scoped read-only Claude review with explicit UTF-8 capture. Preserve
the prompt, stdout, exit status, and verdict in separate post-run-review artifacts.
Do not retry automatically after timeout or quota stop. Save the real verdict to
post-run-review.json only after completion; no inferred PASS.

Required evidence to inspect:

- GOAL.md and .private/current/CONTINUATION.md for current instructions.
- The immutable repro_041 and exp_040 configs, source manifests, and experiment records.
- Both raw validator_results.csv files, metrics.json, inference_identity.json,
  validation_stage_stats.json, submission.csv hashes and graph audit, and runtime logs.
- Codex's completed reproduction analysis and any deviations.

Verify aggregate/specimen metrics to absolute tolerance 1e-12 and zero relative
tolerance, exact division counts and EMA telemetry, byte-identical test output,
frozen inference and validation, actual checkpoint identity, no execution errors,
and honest limits: reproduction establishes repeatability, not generalization.
Return a concise evidence-backed review ending in exactly one of VERDICT: PASS,
VERDICT: REVISE, or VERDICT: BLOCK. PASS supports discussing a leaderboard submission;
it is not submission authorization. Finish by reporting results to the user.
