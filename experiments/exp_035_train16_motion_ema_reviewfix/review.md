I have sufficient coverage of the configuration, EMA implementation, guards, validation protocol, output contract, budget, and justification. Here is the review.

# Review â€” exp_035_train16_motion_ema_reviewfix

## Summary
A clean, well-scoped single-variable test: replace the motion-relink velocity estimator (latest one-frame displacement) with a per-track EMA (Î±=0.4), holding the velocity multiplier at 0.5 and every other detector/fusion/ILP/gap/division/validation setting fixed against the parent `val_008` (fixed train16 stratified proxy, 0.925252). The implementation is faithful, the three `exp_034` REVISE defects are all corrected, the output contract is complete, and GPU cost is negligible against budget. This is admissible for the next controller stage.

## Methodology
- **Single variable (point 1): confirmed.** EMA blend at `motion_ema_train16_v2.ipynb:2341` (`Î±Â·step + (1âˆ’Î±)Â·prev`) reduces exactly to one-frame at Î±=1.0, so the parent is the Î±=1.0 special case â€” the cleanest possible attribution. Velocity weight, gates, learned bonus, and all env are held and enforced by the config guard (`:268â€“285`, `abs_tol=1e-12`, numeric + categorical), which reads effective `os.environ` values, not prose (point 4).
- **Validation (point 2): trustworthy for screening.** Same protocol as parent (`public_0933_embedded_train16_stratified_proxy_v1`), 8+8 division-stratified, per-specimen `adjusted_edge_jaccard`/`division_jaccard` reported, success gate = +0.001 aggregate **and** zero per-specimen regression on both 44b6/6bba. Leakage is real (frozen extractors saw train videos) but correctly handled via delta-only, cross-specimen decisions; `reproducible:false` + `require_reproducible_for_promotion:true` keep this a screening result, not a promotion.
- **Justification (point 7): supported.** Parent `val_008` is the fixed baseline; the private review lists "averaged-velocity/EMA relinking from the 0.940 fork as a single-variable test" as candidate #1 after reproduction. The 0.940 claim is explicitly scoped as provenance only (GOAL.md, config warning, contract), which is honest since the upstream fork changed several parameters.
- **Not duplicate/contradicted (point 5).** EMA velocity is untested; `exp_034` was never launched (absent from `GPU_BUDGET.json`) â€” this is its immutable corrected revision. Orthogonal to the closed DeepCenter-scalar and Family-A (pair/structural/node-validity) branches.

## Implementation risks
- **exp_034 REVISE items all fixed:** no baseline-equality gate remains in `_controller_checks` (baseline is used only for delta reporting, `:4796/:4937`); learned bonus is in the guard (`:249`, =1.0); runtime EMA is surfaced *and gated* via `motion_relink_ema_predictions` â†’ `motion_ema_exercised_both_specimens` requiring `>0` on both specimens (`:2274`, `:4810â€“4835`).
- **Output contract complete (point 3):** per-specimen `primary_metric`, `baseline_primary_metric`, `adjusted_edge_jaccard`, `division_jaccard`, `samples`, division strata (`:4794â€“4808`) plus aggregate `primary_metric`, `checks`, `failed_checks`, `validation_contract_passed`, `motion_relink_velocity_estimator:"per_track_ema"`, `ema_alpha` (`:4933â€“4991`) â€” matches the parent `metrics.json` shape. No missing fields.
- **Minor (non-blocking):** the one-frame fallback branch and `motion_relink_one_frame_fallbacks` stat (`:2278â€“2279`) are effectively dead, since `velocity_um` and `predecessor_position_um` are always populated together (`:2338â€“2346`); harmless. Attribution rests on the Î±=1.0-equivalence argument rather than a direct diff of the parent snapshot's relink code â€” sound, but a one-line provenance note would strengthen it.
- **Expected effect is small:** EMA smoothing on an already-tuned relink is plausible but likely near-zero; the strict zero-regression, both-specimen gate is appropriate and may correctly REJECT â€” that is a feature, not a flaw.

## Budget (point 6)
`expected_gpu_hours: 2.0`, tier 1; remaining 17.69h, reserve 6.0h, single-experiment cap 4.0h. Parent-class runs cost ~1.14h. Well within budget, no user approval needed. Information gain is worthwhile: the optimization audit / two-seeds finding establishes motion_relink as the real topology decider, so its velocity model is a well-targeted lever with a concrete mechanism (fewer dense-field identity swaps).

## Required changes
None blocking. Recommended before/at launch:
1. Run the configured local smoke test (`scripts/validate_motion_ema_notebook.py`) â€” AGENTS.md requires a smoke pass prior to launch (controller step, not a review blocker).
2. Optional: add a one-line note (or a parent-snapshot diff check) documenting that `val_008`'s relink used pure one-frame velocity, to make the single-variable attribution independent of the Î±=1.0 argument.

## Recommendation
The hypothesis is testable and cleanly attributable, the validation protocol and per-specimen/domain handling are sound, the guards verify effective configuration, the output contract is complete, all prior REVISE items are resolved, and the cost is trivial. Safe to proceed to the next controller stage (local smoke test â†’ launch).

VERDICT: PASS
