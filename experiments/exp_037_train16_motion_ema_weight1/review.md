I have everything I need. Here is my review.

---

# Independent Review â€” `exp_037_train16_motion_ema_weight1`

## Summary
The experiment changes exactly one model parameter â€” the motion-relink velocity multiplier `0.5 â†’ 1.0` â€” on top of the confirmed and independently reproduced motion-EMA base (`repro_036`, EMA Î±=0.4, weight 0.5, score `0.927316`). The EMA velocity estimator, detector, fusion, ILP, gap-closing, division, validation split, and scorer are all held fixed. The config, guard, runtime application, and metrics contract are internally consistent, and the notebook does **not** carry the reproduction/baseline-equality gate that caused the `exp_034` REVISE. The prior two Claude calls failed with exit 1 and no output (infrastructure, not evidence); this user-requested review supersedes them.

## Methodology
- **Single-variable & testable (Q1):** âœ… `config.yaml` and the hypothesis isolate `motion_relink_velocity_weight` only. Env cell sets `VELOCITY_WEIGHT=1.0`, `EMA_ALPHA=0.4`, `LEARNED_BONUS=1.0`; all other knobs match the parent (DET 0.965, sec-det 0.81, sec-edge 0.15, bidir 0.15, gap 5.8). The change is applied at line 2273 (`predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * velocity`), so the parameter genuinely acts on the prediction; the EMA update (2339â€“2346) is byte-for-byte the confirmed algorithm.
- **Validation trust / leakage / domain split (Q2):** âœ… Same `public_0933_embedded_train16_stratified_proxy_v1`, 8/specimen, 4-pos/4-neg division stratification, per-specimen `44b6`/`6bba` reported (`_CONTROLLER_BASELINE_SPECIMEN` and per-specimen metric rows). Leakage (frozen extractors saw train videos) is correctly flagged in `config.yaml` and the notebook prose; decisions are paired-delta + cross-specimen, matching `GOAL.md`. Paired baseline is the parent `repro_036` (0.927316 / 44b6 0.905017 / 6bba 0.935505), which is the correct reference for isolating the weight change (not val_008).
- **Parent justification & stated reasons (Q7):** âœ… Reasonable. `exp_035` showed EMA is beneficial; velocity weight is a distinct, untested free parameter of that mechanism. The "matches the public 0.940 fork" rationale is correctly labeled **provenance, not evidence** in both `config.yaml` and the hypothesis; the private review only records the 0.940 fork's averaged-velocity/EMA idea generally, not a specific weight=1.0, so treating it as provenance is accurate.
- **Duplicate / contradiction (Q5):** âœ… Not a duplicate. Historyâ€™s `motion_relink` sweep was on `LEARNED_BONUS` (1.0/1.5/2.0), a different parameter; velocity weight 1.0 has never been tested and no closed branch covers it.

## Implementation risks
- **No stale equality gate (Q4):** âœ… `_controller_checks` contains only config-drift and structural checks (`preset_exact`, `det_threshold_exact`, weight `_exact`s, audit/graph `_exact`s, `motion_ema_exercised_both_specimens`, `division_strata_present_per_specimen`, `validation_is_finite`, sample-count). There is **no** `reproduction_primary_exact` / submission-SHA gate and no assertion that the score equals the baseline â€” a real velocity-weight effect will not be rejected. `_controller_primary` is used only for `validation_is_finite`; `baseline_primary_metric` is reported for delta, not asserted.
- **Guard verifies effective config, not prose (Q4):** âœ… The guard compares `os.environ` numerically (`isclose`, abs_tol 1e-12) and the pipeline reads the *same* env vars (line 377), so the guard genuinely gates the effective value; `effective_configuration` re-exports the resolved Python vars (`velocity_weight`, `ema_alpha`, `estimator=per_track_ema`). `motion_ema_exercised_both_specimens` (>0 predictions/specimen) confirms the algorithm actually runs.
- **Output contract (Q3):** âœ… Submission header/row asserts present (3467â€“3471); per-specimen metrics, `failed_checks`/`checks`, `velocity_weight_change {from:0.5,to:1.0}`, and EMA execution counters all emitted. No missing contract field found.
- **Minor (non-blocking):** The notebook prose still calls this a "controlled reproduction gate" / "reproduction" in several markdown cells (105, 126, 149, 229, 300, 3957), inherited from the repro notebook. This is cosmetic â€” line 126 states "runtime variables are authoritative" and the guards are config-driven â€” but the labeling is misleading for a parameter-change experiment.

## Budget (Q6)
Expected 2.0 GPU-h (siblings actually ran ~1.1â€“1.2 h). Remaining 15.37 h, reserve 6.0 h, max-single 4.0 h â†’ 2.0 h < 4.0 h and leaves â‰¥13 h > reserve. No user approval needed. Information gain is favorable: one clean parameter with a plausible mechanism (larger extrapolation step in the motion cost that decides topology per the optimization audit), directly extending a confirmed +0.002 result; a null/negative result is itself decisive and cheap.

## Required changes
None blocking. Optional before launch:
1. (Cosmetic) Retitle the "reproduction gate" markdown to "parameter-ablation gate" to avoid implying an equality/reproduction contract this notebook intentionally does not enforce.
2. (Optional hardening) Add an explicit `motion_relink_velocity_weight_exact == 1.0` entry to `_controller_checks` so the effective multiplier is contract-checked at runtime, not only at the pre-run guard.

## Recommendation
The experiment is single-variable, correctly baselined against the confirmed parent, leakage-aware with per-specimen reporting, free of the stale reproduction/equality gate that sank `exp_034`, applies the intended change at the correct code path, and is within budget. Safe to proceed to the next controller stage (local smoke test / launch). This is not a prediction that weight 1.0 will win â€” only that the test is valid and attributable.

VERDICT: PASS
