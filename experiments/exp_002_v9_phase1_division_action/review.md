I have a complete picture. Here is my review.

---

## Summary

The config declares `exp_002_v9_phase1_division_action` as a **Phase 1** experiment: replace geometric safe-divisions with a *learned division-action scorer*, one variable changed, validated under `v9_leave_one_specimen_out`. **The snapshot notebook does not implement any of that.** The only change vs. the last commit is a single `metrics.json` contract cell prepended to the *unchanged Phase 0 oracle audit*. There is no learned scorer, no GBDT/3D-CNN, no `add_safe_divisions_postlink` swap, no leave-one-specimen-out split, no `Ï„`/cap decision logic. The pipeline that produces edges is byte-for-byte the Phase 0 oracle already run and recorded as `exp_001` (EVALUATED / KEEP). So the experiment as staged **cannot test its stated hypothesis**, and it substantially duplicates `exp_001`.

## Methodology

- **Hypothesis testable / single variable?** No. The declared variable (`from: geometric safe-divisions â†’ to: learned division-action scorer`) is absent from the code. The actual diff changes *zero* pipeline variables; it only emits a metrics artifact. Attribution is impossible because there is no treatment.
- **Validation trustworthiness / domain split.** The oracle audit itself has good hygiene: it scores on `split_0` held-out test, reports `44b6`/`6bba` separately, uses the official scorer, and explicitly discounts absolute numbers (frozen extractors saw all 199 train videos â†’ deltas only). But the config's `v9_leave_one_specimen_out` protocol is **not implemented** â€” nothing trains on one specimen and tests on the other. With ~84% of divisions in `6bba`, a real LOSO Phase 1 would have almost no positives training on `44b6`; that risk is unaddressed because the code never gets there.
- **adj-vs-div risk.** The plan correctly identifies the Version-7 landmine (added `Mâ†’D2` becoming an edge-FP on dense hidden GT), and the family C oracle does move `adj`. The oracle reports per-specimen `Î”adj` as first-class â€” the right guard. But the *delivered* artifact measures only an oracle ceiling, not a candidate, so "improves divisions while hurting adj" is not yet being tested at all.
- **Duplicate / contradicted?** Largely a duplicate of `exp_001` (same oracle, same 16 division-rich videos, gate already PASSED at family-A Î”score 0.0606/0.0556). The only genuinely new content is the family B/C ceiling numbers â€” a Phase 0.9 extension, not Phase 1.

## Implementation risks

1. **Fatal cell ordering.** The new `controller-metrics-contract` cell is inserted at **index 0**, above the title, but references `agg`, `famA`, `famB`, `famC`, `videos`, `specimen_of` â€” all defined ~1200 lines later (Phase 0.6â€“0.9). On Kaggle Run-All (topâ†’bottom) this cell raises `NameError` immediately, `metrics.json` is never written, and the `--require-metrics-contract` smoke test / controller readback fails. Must be moved to the end.
2. **Wrong primary_metric semantics.** `primary_metric = overall_base` is the mean *baseline* score over the 16 videos (~0.90), not any division-action result. Against parent `0.9188` with `minimum_improvement: 0.002` and `per_specimen_max_regression: 0.0`, the controller would read this as a regression on a metric that has nothing to do with the hypothesis.
3. **Identity mismatch.** The cell defaults `experiment_id='exp_001_v9_phase0_oracle'` and `protocol='v9_phase0_oracle_train16_delta_only'`, contradicting `config.yaml` (`exp_002` / `v9_leave_one_specimen_out`). It relies on `BIOHUB_EXPERIMENT_ID` / `BIOHUB_VALIDATION_PROTOCOL` env vars the config does not set.
4. **Trivial gate.** `gate_0_passed = all(mean_d_score > 0)` over the *oracle* Î”score is near-tautological (the oracle only adds correct edges), so it will report PASS regardless â€” fine for a ceiling read, misleading as an exp_002 "result."
5. **Dataset provenance not launch-ready.** `dataset_sources: []` with `required_dataset_sources: 4`; the four inputs are pinned only by numeric version IDs, which `kernel-metadata.json` cannot reproduce (the config comment admits this).

## Budget

`expected_gpu_hours: 2.0`, tier 1 â€” within `max_single_experiment_hours: 4.0` and the 30 h remaining, so no approval needed. But **incremental information gain is low**: it re-generates 16 baseline `.geff` and re-runs an oracle already recorded in `exp_001`. The only new signal is B/C ceilings, which per the plan (Â§ caching note) can be obtained by re-scoring cached predictions without a fresh GPU pass. Spending 2 GPU-h to not advance the stated hypothesis is poor ROI.

## Required changes

Pick one of two coherent framings, then fix the contract:

- **Option A â€” make it the honest experiment it actually is (Phase 0.9 B/C ceiling):** relabel `config.yaml` (`hypothesis`, `change.component/from/to`, `variables_changed: 0`, `protocol: v9_phase0_oracle_*`, `parent`), set `evaluation.mode` to a screening/audit mode, and reuse cached preds to avoid the GPU pass. Acknowledge it extends `exp_001`.
- **Option B â€” actually build Phase 1:** implement the learned division-action scorer, the `add_safe_divisions_postlink` swap, the candidate generator, and true leave-one-specimen-out CV with `Ï„`/cap chosen on inner folds â€” then the config is correct.

In **either** case, before launch:
- Move the metrics-contract cell to the **end** of the notebook (after `famA/B/C` exist), or make it self-contained.
- Set `primary_metric` to the quantity the hypothesis is judged on (`Î”score = Î”adj + 0.1Â·Î”div_J` per specimen for a real candidate; not the baseline mean), and populate `specimen_metrics` with that quantity.
- Reconcile `experiment_id` / `protocol` with `config.yaml` (or have the controller inject the env vars).
- Fill `dataset_sources` with `owner/slug` references so the launch is reproducible.
- Run the local smoke test (`scripts/validate_notebook.py --require-metrics-contract`) and confirm a clean top-to-bottom execution actually writes `metrics.json`.

## Recommendation

The experiment is mislabeled: its code is the Phase 0 oracle (a near-duplicate of `exp_001`), not the Phase 1 learned scorer its config and hypothesis claim, so it cannot test the stated hypothesis. On top of that, the metrics-contract cell would `NameError` on Run-All and never emit the required artifact, and the reported `primary_metric` is the wrong quantity. These are fundamental (identity + contract + non-executability), not cosmetic.

VERDICT: BLOCK
