Review complete. Findings below.

# Independent Review â€” exp_034_train16_motion_ema

## Summary

Single-variable test replacing the motion-relink velocity estimator (latest one-frame displacement) with a per-track EMA (alpha 0.4), velocity weight held at 0.5 and everything else frozen against parent `val_008` (train16 stratified proxy, 0.925252). The hypothesis is testable and cleanly attributable, and it implements the pre-registered candidate #1 in `research/BASELINE_CANDIDATES.md`. The code diff versus the parent is exactly the EMA addition. **One launch-blocking defect:** the metrics contract re-introduces `baseline_output_preserved` / `baseline_specimen_outputs_preserved` checks that assert the new run reproduces the val_008 baseline to 1e-12 â€” for a change experiment these fail by design. The prior change experiment (exp_011) correctly omitted them.

## Methodology

- **Attributable single variable:** Diffing the two `motion_relink_edges` functions, the only change is the EMA branch (`velocity_um` dict, EMA prediction, EMA update). Cost function, tight/relaxed passes, gates, and `LEARNED_BONUS` are identical. Parent and candidate both set `LEARNED_BONUS=1.0` and `VELOCITY_WEIGHT=0.5`, so those are genuinely constant. The EMA is seeded from the first one-frame step, so candidate and parent agree on links 1â€“2 of each track and diverge only from link 3 â€” a conservative, well-scoped change.
- **Provenance framing correct:** GOAL.md and the config state the 0.940 fork changed several params, so its LB is provenance only. Note the 0.940 fork's documented mechanism is a *4-frame averaged velocity*, while this tests a per-track EMA(0.4); it validates "a" smoothing rule, not the exact 0.940 rule. Acceptable for an isolated test.
- **Validation trust / domain split:** Same frozen train16 stratified proxy as parent (leaky â€” extractors saw train videos), correctly acknowledged; decisions use paired deltas. Both `44b6` (dense) and `6bba` (sparse) reported, 8 samples each, 4 div-positive / 4 div-negative. Strict success gate (`min_improvement 0.001`, `per_specimen_max_regression 0.0`) is appropriate.
- **Not duplicate / not contradicted:** Prior motion_relink work (v8 bonus sweep) tuned the learned-prob bonus, not the velocity estimator; the optimization audit shows motion_relink is the wholesale topology decider on this base, so improving its velocity model is a sensible, new lever.

## Implementation risks

1. **[BLOCKER] Baseline-preservation checks in the contract.** `_controller_checks` includes `baseline_output_preserved` (isclose to `0.9252519785518039`) and `baseline_specimen_outputs_preserved`. Any real EMA effect makes the primary differ from baseline â†’ `failed_checks` non-empty â†’ `validation_contract_passed=False`. exp_011 has no such keys and reported `failed_checks: []`. Copy-paste leftover from the diagnostic notebooks; will self-contradict the metrics.json or trigger a methodology rejection after GPU is spent.
2. **[MEDIUM] Config guard omits `LEARNED_BONUS`.** Guard checks `EMA_ALPHA` and `VELOCITY_WEIGHT` but not `BIOHUB_MOTION_RELINK_LEARNED_BONUS`. Module default is `0.75`; `1.0` is applied only by the top env cell. If that cell is skipped/reordered, the bonus silently reverts to 0.75 â€” an uncontrolled second variable the guard won't catch.
3. **[LOW] Estimator label is prose, not runtime-verified.** The contract hardcodes `motion_relink_velocity_estimator: "per_track_ema"`; no runtime check that the EMA branch executed (`motion_relink_ema_predictions` is computed but never asserted/surfaced). On dense `44b6`, frames > `MAX_FRAME_NODES=2600` are skipped, so EMA may not run there â€” an `ema_predictions>0` check would confirm the change was exercised and explain a possibly-zero `44b6` delta.
4. **[INFO] Dead fallback branch.** `velocity_um` and `predecessor_position_um` are always set together, so the one-frame `else` branch (and its `one_frame_fallbacks` counter) is effectively unreachable after link 1. Harmless, but the counter will read ~0.

Output-contract fields are otherwise present and correct (per-specimen `primary_metric`/`samples`/division strata; `adjusted_edge_jaccard` and `division_jaccard` reported separately; specimen and sample-count checks) â€” satisfies GOAL.md's reporting contract.

## Budget

Reservation 2.0 GPU h; parent actually took 1.14 h (â‰ˆ1.1 h expected). Remaining 17.69 h vs 6.0 h reserve and 4.0 h single-experiment cap â€” comfortably within budget, no user approval needed. Information gain justifies the cost *provided* the blocker is fixed so the run isn't wasted.

## Required changes

1. **Remove `baseline_output_preserved` and `baseline_specimen_outputs_preserved` from `_controller_checks`** (mirror exp_011). Keeping the baseline values as reported deltas is fine; they must not be pass/fail checks. Re-run the local contract validator afterward.
2. **Add `BIOHUB_MOTION_RELINK_LEARNED_BONUS: 1.0` to the guard `_EXPECTED_NUMERIC`** so the held-constant bonus cannot drift to the 0.75 default.
3. **(Recommended) Add a runtime EMA-execution check** â€” assert/report aggregated `motion_relink_ema_predictions > 0` and surface `ema_predictions`/`one_frame_fallbacks`/`skipped_large_frame` per specimen.

## Recommendation

Science, attribution, validation, and budget are sound, and the EMA faithfully preserves the parent algorithm. But the reintroduced baseline-preservation checks fail by design once the EMA changes the output, corrupting the contract and risking a wasted GPU run. Fix change #1 (and preferably #2), then re-run the local contract validator before smoke testing or launch.

VERDICT: REVISE
