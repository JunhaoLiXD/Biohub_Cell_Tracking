I have everything I need. This is a read-only review deliverable, so I'll return the review directly.

---

## Summary

`exp_040_public_0941_motion_ema` is a clean, single-variable transfer test: it replaces only the motion-relink velocity estimator in the frozen Public-LB-0.941 pipeline (parent `val_039_public_0941_train16`, train16 = 0.9359778132422281) — moving from latest one-frame displacement to the previously reproduced per-track EMA (alpha 0.4), while holding the velocity multiplier at 0.5 and everything else fixed. The hypothesis, gates, guards, and output contract are well-formed and directly enforce `GOAL.md`. I verified at the code level that the parent used one-frame displacement and the candidate uses per-track EMA, so the change is genuinely one variable. State is `PROPOSED`; review `PENDING`, smoke `PENDING`. No launch has occurred.

## Methodology

- **Testable, single variable (Q1):** Confirmed. Parent notebook `public_0941_train16.ipynb` computes `predicted = source_pos + WEIGHT*(source_pos - prev_pos)` with no `velocity_um`/`step_velocity`; the candidate adds the per-track EMA (`velocity_um[target] = alpha*step + (1-alpha)*prev`, alpha 0.4) and keeps weight 0.5. The static validator (`validate_public_0941_motion_ema.py`) AST-compares every postprocessing function and requires all except `motion_relink_edges` to be byte-identical to the parent, plus the scorer functions unchanged — a strong single-variable guarantee.
- **Validation trust / leakage / domain split (Q2):** The protocol reuses the exact frozen `val_039` selection (`FROZEN_SAMPLES`/`FROZEN_POSITIVES`, 8/specimen, 4 division-positive), the 44b6/6bba split, and the frozen scorer, with runtime asserts that fail if sample identity/order or division strata drift. Baseline per-specimen adjusted-edge values are hardcoded from `val_039` (44b6 0.90180, 6bba 0.92215 — both match `metrics.json`). The train-leakage caveat is explicitly carried ("optimistic paired screening proxy, not held-out generalization"), and decisions are delta-based on matched protocol — consistent with the project's evidence rules.
- **Preserves claimed algorithm / guards verify effective config, not prose (Q4):** Multiple layers: (a) a config-drift guard that `isclose`-checks env vars including `BIOHUB_MOTION_RELINK_EMA_ALPHA=0.4`; (b) effective-parameter checks (`motion_velocity_weight`→0.5, `motion_ema_alpha`→0.4, det_threshold 0.965, etc.) against actual runtime values; (c) `motion_ema_exercised_both_specimens` requiring `ema_predictions > 0` per specimen; (d) actual epoch-2 checkpoint path/hash binding. These verify the *effective* run, not notebook text.
- **Parent justifies successor; reasons evidence-backed (Q7):** The alpha-0.4/weight-0.5 EMA earned KEEP on the sibling 0.933 pipeline (`exp_035` +0.002064; `repro_036` reproduced it), while weight 1.0 was REJECTED (`exp_037` +0.000425). Carrying the *accepted* configuration to the 0.941 parent is the logical next step; transfer across a different pipeline is genuinely uncertain, which is the information the run buys.
- **Duplicate/contradiction (Q5):** Not a duplicate — prior EMA runs were on the 0.933 pipeline (parent `val_008`); this is the first EMA test on the 0.941 pipeline (parent `val_039`). Not contradicted by history.

## Implementation risks

- **No output-contract gaps found (Q3):** `ema_candidate_gate_passed` (the config `gate_field`) is present and equals `all(contract_checks) and all(research_gates)`; `validation_contract_passed`, `research_gates`, `failed_checks`, per-specimen deltas, `division_counts`, and `motion_relink_ema_execution` are all emitted to `WORKING_DIR/metrics.json`.
- **Division gates sit exactly on the parent's totals** (parent = TP 4 / FP 9 / FN 8; gates = TP≥4 / FP≤9 / FN≤8). This is the intended "no-worse-than-parent" division protection, but with only 4 positives/specimen the division counts are noisy — a single flipped division decides the gate. This is inherent protocol fragility, not a defect; interpret a division-driven REJECT accordingly rather than as a strong negative.
- **`reproducible: false` is expected** for a screening run; `admission.require_reproducible_for_promotion: true` correctly defers a reproduction run to any future promotion. Not a launch blocker.
- Candidate submission SHA is correctly checked for *validity and non-mutation during validation* (not equality to parent), which is right for an inference-changing optimization.

## Budget (Q6)

Expected 2.0 GPU-h; `remaining_hours` 12.21 with a 6.0 reserve leaves ~6.2 available and the single-experiment cap is 4.0 — comfortably within limits and below the 4.0 user-approval threshold. Information gain (single-variable transfer of a previously-KEEP mechanism, with explicit accept/reject gates) justifies the ~2 GPU-h. Claude allowance: this is the one bounded, read-only review; no retry on timeout/quota.

## Required changes

No code changes are required — the notebook, guards, and contract are correct as staged. Before launch, complete the standard controller steps:
1. Record this review as **PASS** and set `admission.require_claude_review` satisfied (config already sets it `true`).
2. Run the deterministic **smoke test** (`validate_public_0941_motion_ema.py`), which enforces `build()` equality, the confined AST diff, English-only, and no saved outputs — currently `PENDING`.
3. Reserve the 2.0 GPU-h in the budget ledger (`reserved: false` today), then a single tracked Kaggle launch. Do not poll continuously after launch; the user reports completion.

## Recommendation

Methodology is sound, the change is provably single-variable, validation is frozen and leakage-aware, guards verify the effective configuration, and the decision gates faithfully encode the authorized admission criteria. Proceed to the next controller stage (deterministic smoke test, then the single authorized launch).

VERDICT: PASS
