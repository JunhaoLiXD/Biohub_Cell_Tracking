Here is my review.

# Independent Review — `diag_045_public_0942_motion_ema_telemetry_v2`

## Summary
diag_045 is the corrected successor to the failed diag_044 online-telemetry diagnostic. Its behavior parent is terminal-KEEP, reproducible `repro_041` (train16 0.9387332376874039, user-reported Public LB 0.942, submission SHA256 `fd1162…5515`). The stated change is instrumentation-only: fixed EMA alpha 0.4, velocity weight 0.5, models, checkpoints, assignments, output graph, frozen samples, and scorer are all held fixed and enforced by hard gates. The single purpose is to measure the true runtime innovation/age/margin distribution and guard-trigger rates. I verified this against the notebook, contract, preflight, validator, and test files.

## Methodology
- **One variable, testable, attributable.** The only delta versus repro_041 is read-only telemetry. Behavior preservation is a hard contract, not a hope: exact parent submission bytes, aggregate/specimen/per-video metrics at abs_tol 1e-12, division counts, and EMA execution counts must all match.
- **Validation trustworthy / leakage.** Same `public_0941_frozen_train16_stratified_proxy_v1` protocol, frozen 8+8 samples per specimen with the 4-positive division strata, verified via `frozen_samples_and_order` and `frozen_strata` checks. The 44b6/6bba split is preserved and telemetry is provably label-free — the `motion_relink_edges` body is statically asserted to contain no `specimen`/`ground_truth`/`validator`/`stem` tokens, and telemetry reads only `step_velocity`, `previous_velocity`, `source_track_age`, and `assignment_margin`. The optimistic-proxy warning is retained.
- **Parent justifies successor.** exp_043 (adaptive hard reset) was rejected specifically because its offline replay estimated a 14.1% trigger rate while the true online rate was 39.3% (~3×). Measuring the real runtime distribution is the logically correct next diagnostic, and the recorded evidence supports it.

## Implementation risks
- **diag_044 root cause is closed with defense-in-depth.** (1) Native conversion at source — `_native_true_count → int(sum(bool(v)…))`, `int(len(...))`, `float(np.percentile(...))`; (2) a contract check `telemetry_count_types_native_int` asserting `type(x) is int` on every count field; (3) strict `json.dumps(..., allow_nan=False)` serialization gates for test telemetry, `VALIDATION_STAGE_STATS`, and final metrics, with a fail-fast `RuntimeError` before writing. The required end-to-end regression test exists (`test_numpy_boolean_regression_serializes_as_native_int`, which reproduces the `numpy.integer` TypeError and asserts the native-int fix).
- **Telemetry is genuinely read-only:** it appends to lists and never mutates `velocity_um`; the EMA update remains `0.4*step + 0.6*prev`.
- **Contract is self-consistent by construction:** `0 ≤ guarded ≤ age_ge3 ≤ proposed ≤ eligible` and `guarded ≤ margin_ge0500 ≤ finite_margin ≤ proposed` all follow from the nested predicates; the innovation ratio is `≤ 2.0` by triangle inequality, matching the `q99 ≤ 2.0` invariant. Monotonicity across thresholds 1.0/1.25/1.5/1.75 is also checked. Uninformative diag_044 thresholds (2.0/3.0) are explicitly forbidden.
- No missing output-contract fields found; `telemetry_diagnostic_passed` gates on the full check set and metrics/inference receipts are written.

## Budget
2.0 GPU hours charged from 21.715 tracked, preserving the 6.0-hour reserve; within the tier-1 and 4-hour single-experiment cap. `submission.user_authorized_count: 0`; no leaderboard submission is in scope. Information gain (calibrating a rare label-free soft-update gate) is worth the cost given the exp_043 miscalibration.

## Required changes
None blocking.

## Recommendation
Not a duplicate — diag_044 never produced a valid result (validation telemetry and metrics were never persisted), and this is the authorized repair-as-new-experiment. All admission requirements (`require_claude_review: true`, native-int conversion, JSON regression test, exact behavior gates) are satisfied. Proceed to snapshot smoke, and if smoke passes, the single authorized launch. No leaderboard submission, promotion, milestone v06, successor experiment, or push is authorized.

VERDICT: PASS
