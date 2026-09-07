You are the independent final reviewer for one completed Kaggle cell-tracking reproduction.

Work read-only. Do not edit or create files and do not run commands that change state.
Review only `repro_041_public_0941_motion_ema` under the one-time scope described in
`experiments/repro_041_public_0941_motion_ema/post-run-review-instructions.md`.

Read the required evidence listed in that instruction file, including GOAL.md,
.private/current/CONTINUATION.md, both experiment records/manifests and raw artifacts,
and `.private/research/repro041_completed_analysis_2026-09-06.md`. Independently verify:

1. aggregate and specimen metrics match exp_040 within absolute tolerance 1e-12 and zero relative tolerance;
2. division counts and EMA telemetry match exactly;
3. submission bytes and graph audit match exactly;
4. inference, validation samples/order, checkpoint identity, and runtime health are frozen and valid;
5. the interpretation is honest: repeatability is established, not generalization or leaderboard gain.

Return concise Markdown with sections Summary, Evidence, Limitations, and Recommendation.
End with exactly one line: VERDICT: PASS, VERDICT: REVISE, or VERDICT: BLOCK.
PASS supports discussing a leaderboard submission; it is not submission authorization.
