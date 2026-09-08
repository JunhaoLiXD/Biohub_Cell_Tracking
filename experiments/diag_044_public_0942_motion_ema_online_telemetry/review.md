I have everything needed. The review is complete — this is a read-only analysis and its deliverable is the verdict below, so I'm presenting it directly rather than as an implementation plan.

---

# Independent Review — `diag_044_public_0942_motion_ema_online_telemetry`

## Summary
A pure-instrumentation diagnostic on the terminal-KEEP parent `repro_041_public_0941_motion_ema` (fixed motion-relink EMA α=0.4, velocity weight 0.5, user-reported Public LB 0.942). It adds read-only online telemetry inside `motion_relink_edges` — normalized velocity innovation, track age, local assignment-cost margin, and prospective/guarded trigger counts at thresholds {1.0, 1.25, 1.5, 2.0, 3.0} — while asserting byte-identical predictions. It is the exact next step recommended by the exp_043 REJECT analysis, which found the offline final-graph replay estimate (14.12%) badly under-predicted the true online hard-reset rate (39.32%); measuring the real online distribution before designing a rare label-free soft gate is well-motivated.

## Methodology
- **Single variable, testable:** `variables_changed: instrumentation_only_no_prediction_change`. The velocity update (lines 989–994) is byte-identical to the parent EMA formula; telemetry (982–988) and `assignment_margin` (929–932) are read-only computations appended to separate lists and never fed back into `cost`, `linear_sum_assignment`, `unmatched_*`, or `selected_edges`. Attribution is clean.
- **Validation trustworthy:** same `public_0941_frozen_train16_stratified_proxy_v1` protocol, frozen sample identities/order and division strata enforced (`frozen_samples_and_order`, `frozen_strata`). The optimistic-proxy caveat ("frozen models saw training videos") is stated. This is a behavior-preservation diagnostic, not a generalization claim — correctly framed.
- **44b6/6bba split & leakage:** telemetry consumes only runtime positions and assignment costs; the validator statically asserts `motion_relink_edges` text contains none of `specimen`, `ground_truth`, `validator`, `stem`, and the config prohibits `specimen_id`/`video_id`/`ground_truth`. Per-video aggregation is a property of the per-run `stats` dict, not an identity input. No leakage path found.

## Implementation risks
- **Behavior preservation is doubly guaranteed:** by construction (deterministic `build()` regenerates the notebook from the SHA-pinned parent, and `validate()` asserts snapshot == rebuild) and at runtime by hard gates: `submission_bytes_exact_parent` (fd1162…5515), aggregate/specimen/video metrics via `_telemetry_close`, `division_counts_exact` (4/8/8), and `ema_execution_exact` (255602 / 137643) — all sourced directly from the parent `metrics.json`/`validator_results.csv`, not from prose. Guards check *effective* runtime values (`motion_ema_alpha`, velocity weight, EMA alpha env), not stale comments.
- **Output-contract fields:** complete — telemetry completeness, `>0` eligible updates per stem, prospective/guarded threshold monotonicity, experiment-ID injection, submission-unchanged-after-validation. No missing fields identified.
- **Minor, non-blocking:** the per-video telemetry summary raises `RuntimeError` if any of innovation/track_age/finite-margin lists is empty. Given parent execution (100k+ predictions/specimen) this cannot fire in practice; it is a correct guard, not a defect. The added `alternatives` margin computation is O(targets) per match — negligible runtime impact.

## Budget
2.0 GPU-h reserved against 23.72 remaining; 6-hour reserve untouched (parent ran in ~1.06 h, so headroom is ample). Claude allowance is unknown — this is the single bounded review; do not retry on timeout/quota stop. `submission.user_authorized_count: 0` and no LB submission is performed. Diff scope is limited to tracking docs plus the new immutable experiment directory; no training/scoring code is touched outside the snapshot. Information gain (true online innovation/age/margin distributions to calibrate a genuinely rare gate) directly resolves the exp_043 failure mode and justifies the cost.

## Required changes
None. The experiment satisfies every gate for advancing to the next controller stage.

## Recommendation
Proceed to snapshot smoke test and, on smoke PASS, the single authorized launch. No leaderboard submission, formal promotion, milestone v06, or push is authorized.

VERDICT: PASS
