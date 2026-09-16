Here is my review.

# Review — exp_054_original_score_joint_bootstrap_fix

## Summary
exp_054 is the corrective re-run of exp_053. exp_053 died at ~311 s with a `NameError` because the isolated-solver self-test called `np.array(...)` before `import numpy as np` (notebook line 1666) executed — an infrastructure failure that produced no `metrics.json`, `submission.csv`, or score rows, so it yielded no quality conclusion. exp_054's only change is a local numpy import in the bootstrap cell. The fix is present, minimal, correct, and backed by a genuine execution-level regression guard. Contract, parity gates, and prediction-only provenance are preserved.

## Methodology
1. **Testable, single attributable variable (vs exp_053):** Yes. Line 1112 adds `import numpy as _jr_np`; the self-test at line 1126 now uses `_jr_np.array(...)`. Nothing else in the bootstrap changed. Note the experiment is *not* a single-variable change relative to the recorded parent repro_041 — it introduces the entire joint-repair system — but that design was already reviewed for exp_053 and locally audited (local_052, 48 graphs). exp_054's remote decision is a parity/coverage **gate**, not a fresh single-variable claim.
2. **Validation protocol / domain split:** Trustworthy for its stated (limited) purpose. Frozen train16 stratified proxy, required specimens 44b6 + 6bba, 8+8 = 16 samples — identical to repro_041. Optimistic-proxy leakage is disclosed (`warning` field, `_metrics['reproducible']=False`). Prediction-only provenance is statically guarded (core rejects `final_scored`/`scorer_matching`/secondary features; fixed `PARAMETERS(top_k=8, protected_probability=0.9, edit_penalty=0.25)` — no sweep).

## Implementation risks
3. **Bugs / missing contract fields:** The final contract cell writes `metrics.json` and `validation_stage_stats.json` with `allow_nan=False` and explicit `int(...)`/`float(...)` conversions — avoiding the `numpy.int64` `json.dumps` failure that killed diag_044. `_jr_checks` covers `solver_pinned==1.18.1`, `exact_validation_graphs`, `exact_score_rows` (abs_tol 1e-12), `aggregate_expected` (0.9535869…), `aggregate_gain ≥ 0.005`, `division_preserved` (4/8/8), with `joint_repair_passed=all(...)` and `failed_checks`. Complete.
4. **Guards verify effective config, not stale prose:** Yes. Every gate is computed from runtime artifacts (receipt SHA256s, validator score rows, `_summary['proxy_score']`, `_overall` division counts, runtime `_jr_solver_version`). The **new** guard is the real strength: `validate_original_score_joint_repair_v2.py::execute_clean_namespace_solver_probe` extracts the actual bootstrap cell, asserts import-before-use ordering, then *executes* `[numpy_import, solver_call, solver_assert]` in a namespace with no ambient numpy and checks the LSAP output — a faithful reproduction of the exp_053 failure class, exactly as STATE required. It is wired into `tests/test_original_score_joint_repair_bootstrap.py`.
5. **Duplicate / contradicted:** No. exp_053 gave zero quality signal (infra failure), so this is not a re-run of a settled result. local_052 retained original-score as a promising *separate* candidate (the context-increment gate was the one rejected), so the design has standing authorization.

## Budget
6. 2.0 GPU h reserved from 28 remaining; the 6 protected hours are preserved; within the 4.0 h single-experiment cap. Given prior sunk investment and that exp_053 returned no information, the expected gain (first cross-platform execution + parity confirmation of the retained candidate) justifies the cost. Caveat: the return is a frozen-proxy parity confirmation, not independent generalization — appropriately framed.

## Required changes
7/8. **None blocking.** Parent result (repro_041 KEEP) and the recorded local_052 evidence logically justify this corrective re-run, and the stated change matches the recorded exp_053 failure analysis. Recommended (non-blocking) before launch:
- Controller should confirm the launched **snapshot** notebook hash equals the smoke-target working copy `.private/current/original_score_joint_repair_v2.ipynb` — the config `smoke_test` and bootstrap test point at the working copy, not the snapshot. (I could not run hash tooling under the sandbox.)
- Ensure the v2 smoke actually runs (currently `status: PENDING`) and the clean-namespace probe passes before READY.

## Recommendation
The bug attribution is exact, the fix is minimal and provably guarded, the output contract is intact and NaN/numpy-safe, and budget/authorization are in order. Safe to proceed to the next controller stage (local smoke, then the single authorized remote launch). This is not a prediction that the parity gate will pass — a cross-platform numerical drift beyond 1e-12 would produce an honest negative.

VERDICT: PASS
