I have completed a thorough read-only inspection: the project handoff files, the parent `repro_048` record/metrics, the `val_049` config/experiment record/manifest, the deterministic builder and validator (both working and snapshotted copies), the generated notebook's cell structure and cross-cell global dependencies, the validation prediction command/env, the contract cell, the research roadmap, and the git diff. Here is my review.

---

# Review — `val_049_public_0944_train16`

## Summary
This is a frozen-train16 **baseline-establishment** experiment on behavior parent `repro_048_public_0946_exact_copy` (the independently verified Public LB **0.944** configuration, byte-identical to the public output; the advertised 0.946 is correctly rejected). It reuses `val_039`'s exact selector/scorer donor cells and adds only checkpoint-load telemetry plus a runtime timer. It is explicitly authorized by the 2026-09-09 `GOAL.md` block as the first launch, budgeted at 2.0 GPU hours, with **no leaderboard submission** (`user_authorized_count: 0`). The construction is deterministic, the required globals resolve, and the validation inference faithfully reuses the 0.944 configuration. I found no blocker.

## Methodology
- **Testable / one variable (Q1):** Yes. `change.variables_changed = "Validation instrumentation only; no training or inference parameter change."` The hypothesis is scoped to *contract validity*, not superiority — appropriate for an establishment step and consistent with the parent's INCONCLUSIVE status.
- **Protocol trust / leakage / 44b6-6bba split (Q2):** Reuses `public_0941_frozen_train16_stratified_proxy_v1` unchanged; `FROZEN_SAMPLES` = 8 stems each for 44b6 and 6bba; sample identity/order is guarded (raises `"Frozen train16 sample identity/order changed"`). The optimistic-because-leaky caveat (pretrained models saw train videos) is stated in config and notebook; the panel is a deltas-only regression proxy versus val_039 (0.9359778) and repro_041 (0.9387332), not an absolute score. Trustworthy for its stated purpose.
- **Parent justifies successor (Q7):** Yes. `repro_048`'s own next-action ("design an explicitly authorized frozen-train16 reproduction … before adopting it as the research parent") is exactly this experiment, and the user authorized it. Stated reasons match recorded evidence: edge-feature TTA on (`BIOHUB_EDGE_FEATURE_TTA=1`, line 132), no EMA var set — the bundled 0.944 config, and the record does **not** overclaim isolated TTA causation.
- **Duplicate / contradicted (Q5):** No. No prior train16 establishment of the 0.944 config exists; history supports it.

## Implementation risks (Q3, Q4)
- **Global compatibility (the flagged concern):** Verified statically that every global the donor validation cells consume is defined earlier in the repro_048 inference cell: `WORKING_DIR`(195), `SUBMISSION_PATH`(197), `METHOD`/`WEIGHTS_RELATIVE`(199-200), `TEST_DIR`(194), `COMP_DIR`/`REPO_DIR`(193/196), `DET_THRESHOLD`/ILP weights(205-211), `DEEPCENTER_EXPECTED_EPOCH`(284), `DEEPCENTER_VETO_DETECTOR`(2787), and `_runtime_integrity_receipt` with `checkpoint_sha256:{primary,secondary,deepcenter}`(813). The pre-validation gate reads exactly those subkeys. `TRAIN_DIR`(3039) is defined in the selector cell before the validation cell uses it. No missing-global or structural mismatch found.
- **Effective-config guards, not stale prose (Q4):** A configuration-drift guard (148-165) re-reads env keys at runtime and raises on drift; the pre-validation gate enforces DeepCenter epoch==2 and matching primary/secondary/deepcenter hashes; the contract enforces `test_submission_unchanged_after_validation` and `EXPECTED_SUBMISSION_SHA == 0319ba…`. Validation inference (cell 5) reuses `predict_unet_transformer.py` with the same `--weights/--det-threshold/--ilp-*` flags and `env={**os.environ,"PYTHONPATH":"src"}`, so edge-feature TTA propagates — the train16 panel reflects the 0.944 config, not the 0.941 one.
- **Upstream algorithm preserved:** Inference cell is byte-identical to `repro_048` except an additive telemetry patch (adds `checkpoint_epoch`/`checkpoint_sha256` to the DeepCenter return dict); `checkpoint_epoch`(1772) and `_sha256_file`(789) are defined before use, patch applied exactly once. The validator asserts `nb == build()`, `cells[4:6] == donor[10:12]` (scorer frozen), adapted cell minus the patch equals the parent, and exactly one `__CONTROLLER_EXPERIMENT_ID__`.
- **Contract fields (Q3):** Gate field `validation_contract_passed = all(_checks.values())`(3741) matches config `gate_field`; `metrics.json`(3750), `validation_stage_stats.json`, and `inference_identity.json` are written; `experiment_id_injected` and `stage_stats_complete` checks present.
- **Residual risk (not a blocker):** The smoke test is **static-only** (deterministic build equality + `ast.parse`); it does not execute the pipeline. The edge-feature-TTA path on the train/validation volumes runs for the first time only remotely. Integrity guards catch identity/output drift, but a validation-specific runtime failure (e.g. TTA memory on train volumes) would surface only after GPU spend. Acceptable given the identical-shape `val_039` precedent.

## Budget (Q6)
2.0 GPU-hr against 19.10 tracked / ~13.10 spendable (6-hr reserve intact); `val_039` ran 1.30 hr, so the estimate is reasonable. Information gain is high: it produces the frozen-train16 anchor and per-video/edge/division panel required before the TTA/EMA factorial (arms A–D). No submission consumed. Worthwhile.

## Required changes before launch
None are blocking. Advisory only:
1. `success.minimum_improvement: 0.001` and `regression_threshold: 0.0` are inert under `evaluation.mode: gate`; confirm the controller keys solely on `validation_contract_passed` for this establishment (it should) so the KEEP is not misread as a superiority claim.
2. Preserve the framing in the record: `val_049` establishes the **bundled** 0.944 configuration, not isolated edge-feature TTA — the isolation belongs to the later factorial. This is already correctly stated; keep it that way in the collected analysis.
3. For awareness (not a defect): the contract's `selection_and_scorer_reference` still literally reads `val_008_public_0933_train16_launchable` — accurate sample-lineage provenance, not a bug.

## Recommendation
Well-constructed, deterministic, correctly scoped, adequately guarded, and logically justified by the parent. Safe to proceed to the next controller stage (local smoke, then the single authorized launch). Treat the collected result as a contract-valid baseline anchor, not evidence of superiority, and honor the no-submission constraint.

VERDICT: PASS
