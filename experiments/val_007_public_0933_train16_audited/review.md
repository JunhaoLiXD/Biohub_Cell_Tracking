Working tree is clean (no diff; the experiment is committed as snapshot files at `bbe1466`). I have everything needed. Here is the review.

---

# Independent Review â€” `val_007_public_0933_train16_audited`

## Summary
This experiment replaces the 4-video proxy validator (parent `repro_005`) with a deterministic, specimen- and division-stratified **16-video** validator (8 per specimen, target 4 div-positive + 4 div-negative), while holding the reproduced team-fusion-v6 inference pipeline fixed. It is explicitly a **validation-infrastructure gate** (`evaluation.mode: gate`, `gate_field: validation_contract_passed`, `minimum_improvement: 0.0`), not a metric-beating claim â€” which is exactly the "broader frozen validation baseline (16 videos) before any detector/linker ablation" that `GOAL.md` names as the recommended next step. Scope, single-variable discipline, leakage handling, and the dynamic metrics contract are all sound. The one real defect is **stale hardcoded validation prose** carried over from the 4-video run; it does not corrupt the contract gate but should be cleaned to avoid misleading the human no-metric-hack review.

## Methodology
- **Single variable (Q1): yes.** `variables_changed: validation_sample_selection_only`. Inference config is frozen and *guard-verified*, not just asserted in prose: the contract checks `preset_exact == team_fusion_v6_optimal_balance` and `det_threshold_exact == 0.965` (notebook 4382â€“4383). The hypothesis (a 16-video stratified validator is a materially more stable estimator than the 4-video proxy) is testable and attributable.
- **Validation trust / leakage / domain split (Q2): appropriately handled for its stated purpose.** The models trained on all 199 train videos, so this is a *stability estimator*, not held-out generalization â€” and the config, `GOAL.md`, and the `metrics.json` warning field all say decisions must use deltas + per-specimen consistency, never absolute local score. Leakage against the 4 test copies is guarded (`test_stem_set` exclusion, nb 3633â€“3637). Both specimens are scored and enforced separately: `required_specimens_present`, `per_specimen_sample_count_exact == 8`, and `division_strata_present_per_specimen` (nb 4410â€“4423). Selection is deterministic via a seeded SHA256 order independent of directory/alphabetical order.
- **Duplicate/contradicted (Q5): no.** It supersedes `repro_005`'s 4-video proxy and is the direction `GOAL.md` recommends. Nothing in history contradicts it.
- **Preserves upstream algorithm + guards check effective config (Q4): yes.** The metrics contract is built dynamically from the actual val scoring (`_controller_aggregate`/`_controller_summary`, nb 4349â€“4442) and written to `/kaggle/working/metrics.json` in the final code cell (nb 4481â€“4486). The smoke test (`experiment_controller.core.validate_notebook`) requires `metrics.json` in the last code cell and zero saved error outputs â€” it does not key on printed prose. The controller reads the contract, not the stale print.

## Implementation risks
- **Stale hardcoded validation prose (should fix; non-blocking to smoke test).** `print("VALIDATION: PROXY 0.9382 | ADJ_EDGE 0.9215 | DIV 0.1667")` (nb 4320), the top markdown "Embedded validation proxy: **0.9382**" (nb 126), and `BIOHUB_SCORE_AXIS = '... | train16 validation pending'` (nb 156) are all carried over from the 4-video proxy (0.9382 == `repro_005` score). The train16 run will produce different numbers, so these lines will contradict the real result. They are outside the contract, so the gate is safe, but they can mislead the human review and violate the "verify effective config, not stale prose" principle.
- **44b6 division-stratum scarcity (interpretation caveat, not a bug).** GT divisions are ~84% in 6bba; 44b6 has only ~26 events. `_stem_has_gt_division` flags a video on any out-degreeâ‰¥2 node, and the strata check requires only **â‰¥1** div-positive per specimen (not 4), with deterministic backfill. So the run may legitimately select <4 division-positive 44b6 videos, making the **per-specimen 44b6 div_J estimate rest on very few events and be near-meaningless**. This is inherent to the data and is captured (`division_positive_count` per specimen, nb 4373), but downstream division decisions must not be gated on 44b6 div_J.
- **`_stem_has_gt_division` swallows exceptions â†’ `False` (nb 3645â€“3648).** A GT read failure would silently mark a video division-negative, biasing stratification. Low risk (GT present/valid) but worth a logged warning rather than a silent `False`.
- **Multi-prefix assumption.** Selection loops over every prefix in `by_prefix` and takes 8 each; a stray third prefix would inflate `n_samples`. This is caught by `validation_sample_count_exact == 16`, so it fails closed. Fine.
- **Output contract fields (Q3): complete.** Per-specimen and aggregate `adjusted_edge_jaccard`, `division_jaccard`, `proxy_score`, sample lists, division strata counts, `validation_contract_passed`, and `failed_checks` are all present. No missing contract field found.

## Budget
- `expected_gpu_hours: 2.0`, tier 1. 16 videos â‰ˆ 4Ã— the 4-video proxy (which ran 0.52h) but dual-T4 sharding halves wall-clock â†’ ~2h is credible and within `max_single_experiment_hours: 4.0`, so no user approval needed. Remaining 26.5h vs 6h reserve leaves ample headroom.
- **Information gain vs cost (Q6): worth it.** This is a one-time infrastructure investment that becomes the frozen protocol for every subsequent ablation; a stratified 16-video, per-specimen estimator is materially less noisy than 4 videos. High leverage, cheap, in budget.

## Required changes
1. **Before the Kaggle launch:** remove or make-live the stale hardcoded numbers â€” `VALIDATION: PROXY 0.9382 | ADJ_EDGE 0.9215 | DIV 0.1667` (nb 4320), the top-markdown "Embedded validation proxy: 0.9382" (nb 126), and the `BIOHUB_SCORE_AXIS` string (nb 156). Print the values computed from `_controller_summary` instead, so no cell reports 4-video numbers for a 16-video run.
2. **Interpretation guardrail (doc, not code):** when reading results, treat 44b6 per-specimen `div_J` as low-confidence (possibly 1â€“3 events) and make division-related conclusions from 6bba / aggregate only; confirm the printed per-specimen `division_positive_count` before trusting any 44b6 division delta.
3. **Optional hardening:** have `_stem_has_gt_division` log on exception rather than silently returning `False`.

None of these affect the smoke-test gate (contract structure, final-cell placement, no error outputs), so they can be applied before the Kaggle run without re-review.

## Recommendation
The experiment is correctly scoped (single variable), leakage-aware, per-specimen, and backed by dynamic contract guards that verify the effective inference config rather than prose. It is the recommended next gate and is not a duplicate. The only substantive issue is stale hardcoded validation prose, which is non-blocking to local smoke testing and should be cleaned before the Kaggle launch. Safe to proceed to local smoke testing.

VERDICT: PASS
