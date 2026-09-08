I have everything needed. The implementation, contract, guards, parent evidence, and budget are all confirmed. Here is my review.

---

# Review — `exp_043_public_0942_motion_ema_adaptive_reset`

## Summary
A clean, single-variable successor to reproducible KEEP parent `repro_041_public_0941_motion_ema` (train16 0.9387332376874039; user-reported Public LB 0.942). It keeps base EMA alpha 0.4, velocity weight 0.5, and every model/detector/association/ILP/gap/division/scorer setting frozen, adding only a label-free runtime rule: when the normalized velocity-innovation ratio exceeds 1.0, that one velocity update uses alpha 1.0 instead of 0.4. The implementation matches the spec exactly, reduces to the parent when no reset fires, and the final contract enforces honest admission gates. I found no launch blocker.

## Methodology
- **One variable, testable, attributable.** The only algorithmic change is the reset branch (notebook cell, lines 972–989). The non-reset branch is the identical `alpha*step + (1-alpha)*prev` update at alpha 0.4, and the initial (no-prior) update sets `velocity = step`, so with zero triggers the run is byte-equivalent in logic to the parent EMA. Attribution is clean.
- **Label-free signal confirmed.** `step_velocity = position[target] - position[source]`, `previous_velocity = velocity_um.get(source_id)`, `ratio = ||step - prev|| / max(||step||, ||prev||, 1e-6)` — runtime selected positions only. No specimen id, video id, or ground truth enters the rule (config `prohibited_dependencies` honored).
- **Protocol and split preserved.** Same `public_0941_frozen_train16_stratified_proxy_v1`, 8 samples/specimen across 44b6 and 6bba, frozen sample identities/order and division strata checked (`frozen_samples_and_order`, `frozen_strata`), and the per-video val_039 adjusted-edge baseline is embedded and required complete (`_VAL039_VIDEO_ADJUSTED_EDGE`, `video_baseline_complete`). The optimistic "frozen models saw training videos" warning is retained — comparisons are paired deltas, not held-out generalization, which is the correct framing.
- **Gates are strict and honest.** `adaptive_ema_candidate_gate_passed` requires all contract checks AND: aggregate ≥ 0.9387332376874039, no per-specimen adjusted-edge regression beyond −0.001, worst-video delta vs val_039 ≥ −0.002, div TP≥4, FP≤8, FN≤8. This directly targets the parent's known heterogeneous tail (worst ≈ −0.0037) rather than only aggregate.

## Implementation risks
- **No missing contract fields.** Runtime guards verify effective config, not prose: `motion_velocity_weight=0.5`, `motion_ema_base_alpha=0.4`, `motion_ema_reset_alpha=1.0`, `motion_ema_innovation_threshold=1.0` are all asserted with `isclose(rel_tol=0, abs_tol=1e-12)` (lines 2363–2369). Checkpoint identity (DeepCenter epoch-2 best.pt SHA `8040999a…`, primary/secondary SHAs), dual-T4, submission creation, and `candidate_submission_unchanged_after_validation` are all enforced. Adaptive execution is instrumented (reset/base/initial update counters) with `adaptive_reset_exercised_both_specimens` and `adaptive_base_exercised_both_specimens` gates.
- **Learned-bonus default (minor, non-blocking).** The notebook default for `MOTION_RELINK_LEARNED_BONUS` is `0.75`, differing from the parent's effective `1.0`. This is *not* a drift: the notebook explicitly sets `os.environ["BIOHUB_MOTION_RELINK_LEARNED_BONUS"] = '1.0'` (line 46) before the value is read (line 233), so effective = 1.0, matching parent. It is simply not included in the `_expected_effective` assertion block — same as the parent's practice. Optional hardening: add it to the effective-config guard for defense-in-depth. Not required for launch.
- **Reset-fires assumption (low risk).** The `adaptive_reset_exercised_both_specimens` gate assumes resets occur on the validation specimens. The prelaunch diagnostic shows a 14.1% trigger rate on the frozen test graph (per-dataset 6.1%–21.6%; innovation-ratio p90≈1.08), so both branches will almost certainly exercise; if not, the gate fails safe.
- **Diagnostic scope stated honestly.** The 14.1% figure is a final-submission-graph replay, explicitly labeled trigger-selectivity evidence only, not score evidence. Correctly not used for tuning.

## Budget
Expected 2.0 GPU hours against 25.0 remaining, with the 6.0-hour reserve untouched (well under the 4.0-hour single-experiment cap and no user approval threshold hit). One launch only. Information gain is worthwhile: a plausible mechanism (trust fresh measurement on genuine direction changes/maneuvers) with a specific, falsifiable target (repair the parent's video tail without aggregate loss); even a REJECT cleanly closes the adaptive-reset direction. Not a duplicate — distinct from the rejected global alpha-0.6 (`exp_042`) and unrelated to the closed graph-oracle/Family-A routes. Parent evidence (reproducible KEEP, heterogeneous tail, Public LB 0.942) logically justifies this refinement.

## Required changes
None blocking. Optional, at author discretion:
1. Add `motion_relink_learned_bonus` (expected 1.0) to the `_expected_effective` runtime assertion for defense-in-depth.

## Recommendation
The hypothesis is testable and cleanly attributed to one variable; the validation protocol, leakage framing, and 44b6/6bba split are preserved; the implementation faithfully realizes the label-free adaptive rule and reduces to the parent absent triggers; runtime guards verify the effective configuration and artifact identity rather than stale prose; the contract carries all required fields with strict, honest gates; and the budget is affordable with reserve intact. Proceed to the next controller stage (snapshot smoke, then the single authorized launch). No leaderboard submission, formal promotion, milestone v06, additional successor, or push is authorized by this review.

VERDICT: PASS
