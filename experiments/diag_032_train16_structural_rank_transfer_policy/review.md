I have everything I need. Here is my review.

---

# Review: diag_032_train16_structural_rank_transfer_policy

## Summary
A CPU-only (tier-1, 0 GPU h) diagnostic that keeps the diag_031 structural factorized Family-A scorer, features, labels, action constraints, and frozen scoring **unchanged**, and alters only the cross-specimen calibration: instead of transferring an absolute probability threshold, it selects the **training-optimal global action count** and applies that count to the highest-ranked held-out actions. This is a faithful, single-variable follow-up to diag_031, which recovered the full in-sample Family-A oracle on both specimens but selected zero held-out actions because source-specimen absolute thresholds did not transfer across probability scales. The parent explicitly named "cross-specimen probability calibration" as the next bottleneck; rank-count transfer is scale-free and directly targets it. Integrity guards are strong. I found no correctness defect. Prior evidence makes a PASS of the gate itself unlikely, but the diagnostic is cheap and closes the route cleanly either way.

## Methodology
- **One variable, attributable.** `change.variables_changed = cross_specimen_calibration_only`. Verified in source: the only new logic is `_score_rank_policy` (rank by `-probability`, take `ranked[:action_count]`) and `_rank_transfer_direction` (sweep `action_count âˆˆ [0, len(train_actions)]` on the **train** specimen, pick max train `delta_score` with fewer-actions tie-break, apply that count to test). Models (`_fit_model`, `_factorized_best_actions`), features, eligibility constraint, and `_score` are inherited verbatim.
- **No test leakage into calibration.** The action count is chosen solely from `train_specimen` deltas; test uses only the transferred integer count over probability-ranked test actions. Confirmed.
- **No GT leakage into features.** In `_load_structural_dataset`, `feature_row = [*edge_features, *structural]` (pre-ILP audit + graph topology). `valid`/`division` (GT-match derived) are used only as **labels** and for scoring bookkeeping (`both_endpoints_matched`, `true_division_edge`), never appended to features. The `gt_matching_is_not_a_model_feature` claim holds by construction.
- **Domain split is respected.** Equal 8/8 specimen splits; `_fit_model` masks `domain == specimen`; both directions (44b6â†’6bba, 6bbaâ†’44b6) reported separately, per GOAL.md.
- **Frozen-baseline reproduction is a real runtime guard.** `_baseline_matches` compares recomputed per-specimen `adjusted_edge_jaccard` and `division_jaccard` against the **diag_019** frozen baseline at `BASELINE_ABS_TOL = 1e-10`. `PARENT_EXPERIMENT_ID` (data parent) is correctly `diag_019_...` (attached via `kernel_sources`), distinct from the lineage `parent` (diag_031). The local `_score` reimplementation is thereby validated against the frozen pack-metric numbers (matches val_008 44b6=0.903658, 6bba=0.932950).
- **Gate is conservative and correct.** `passed = baseline_reproduced AND (both directions: test_delta_score > 0 AND test_delta_adjusted_edge_jaccard >= 0)`. The `>= 0` adjusted-edge guard correctly protects against the Version-7 failure mode (a transferred "division" edge landing on two matched-but-not-GT-linked nodes = edge-FP), so a division bonus cannot mask an edge regression.

## Implementation risks
- **Notebook carries ~2,500 lines of dead prior-experiment code** (diag_027â€“031 gate functions, each with its own `metrics.json` writer). Not a runtime bug: only one execution cell runs (`run_rank_transfer_policy_gate()` at the end), and only the final `metrics.json` write survives. `PARENT_EXPERIMENT_ID`/`_fit_model`/etc. are redefined identically (last-def wins). It is, however, a large and unnecessary audit surface.
- **Two attestation flags are hardcoded, not runtime-verified.** `all_features_available_at_inference: True` and `gt_matching_is_not_a_model_feature: True` are static literals (as in diag_031). The underlying properties are genuinely enforced by the feature-construction code (I verified), and the smoke validator only string-greps for them â€” so these are provenance claims, not effective-config guards. The meaningful guard (`baseline_reproduced` at 1e-10) is real.
- **Contract completeness: OK.** Metrics write `metrics.rank_transfer_policy_gate_passed` (bool), matching `config.evaluation.gate_field`; the contract cell asserts it plus the two attestations and `experiment_id`. `specimen_metrics` carries both test specimens. Smoke test PASSED (exit 0), state READY.
- **Prior-evidence prior for the gate is negative.** diag_028/030/031 repeatedly found the top-ranked held-out action had **zero matched endpoints / zero metric effect** (only ~3 beneficial actions among ~29k candidates). The most probable outcome is `test_delta_score = 0` (gate fails), not a regression. This is an expected diagnostic outcome, not a defect.

## Budget
- `expected_gpu_hours: 0.0`, `enable_gpu: false`, `enable_internet: false`, tier 1. diag_031 (same shape) ran ~372 s wall. No GPU budget consumed; `remaining_hours â‰ˆ 17.7`, reserve 6.0 untouched. ROI is favorable: near-zero cost to conclusively settle whether scale-free rank transfer resurrects the structural Family-A route or closes it, which gates the much larger Phase-2 GPU commitment.

## Required changes
1. **Governance flag (should-fix):** `admission.require_claude_review: false` contradicts GOAL.md ("Claude review is required before the first remote launch under the research director's updated policy"). This review satisfies the requirement in practice, but set the flag to `true` (or record this review in the experiment record) so the controller's config reflects the policy and cannot silently auto-launch a sibling without review.
2. **Recommended (non-blocking):** Convert `all_features_available_at_inference` / `gt_matching_is_not_a_model_feature` from hardcoded literals into runtime assertions (e.g., assert the feature-column count equals `len(FEATURE_NAMES)+len(STRUCTURAL_FEATURE_NAMES)+2` and that label arrays are not among the feature columns) so the attestations verify the effective build rather than restating prose.
3. **Recommended (hygiene, non-blocking):** Prune the dead diag_027â€“031 cells from the snapshot notebook to shrink the audit surface; not required for correctness since they never execute.

None of these alter the science or block the run.

## Recommendation
The hypothesis is testable and cleanly attributable to a single calibration variable; the validation protocol is trustworthy (train-only count selection, 8/8 specimen split, per-specimen reporting, 1e-10 frozen-baseline reproduction, conservative dual-direction adjusted-edge gate); no leakage or output-contract defect was found; the parent result logically justifies it and the stated rationale ("avoid probability-scale mismatch") matches diag_031's recorded failure mode; it is neither a duplicate nor contradicted; and the GPU cost is zero. Address the `require_claude_review` flag for policy consistency; the remaining items are recommendations. Safe to proceed to remote launch.

VERDICT: PASS
