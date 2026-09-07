Here is my independent prelaunch review.

# Independent review — repro_041_public_0941_motion_ema

## Summary

`repro_041_public_0941_motion_ema` is a pure execution-reproduction of the accepted motion-EMA candidate `exp_040`. It changes only the final evidence contract (`variables_changed: evidence_contract_only`) and gates on exact reproduction of exp_040's aggregate + per-specimen metrics (abs_tol 1e-12, rel_tol 0), exact division and EMA-telemetry counts, and a byte-identical test submission. The build is deterministic and SHA-pinned to the frozen parent notebook and metrics; the contract wiring, gate-field resolution, and six negative controls all check out. It is the evidence-supported successor GOAL.md itself recommends (exp_040 is positive but `reproducible: false`, and reproducibility is a stated promotion prerequisite). Remaining items before launch are process gates, not code defects.

## Methodology

- **Testable, one variable:** Yes — the single variable is execution determinism, evaluated by a strict pass/fail gate (`evaluation.mode: gate`, `gate_field: reproduction_passed`).
- **Parent justifies it:** exp_040 KEEP at 0.9387332 (+0.002755 over val_039), both specimens up, division FP 9→8, but `reproducible: false` with heterogeneous video-level deltas (8+/1 zero/7−). GOAL/AGENTS explicitly name "one exact reproduction" as the next step; `require_reproducible_for_promotion: true`. Stated reasons match the recorded evidence.
- **Validation / leakage / split:** Same optimistic frozen train16 proxy; the training-leakage caveat is preserved in the config warning. For a reproduction that caveat is irrelevant — this measures determinism, not generalization. The 44b6/6bba 8+8 stratified split and scorer are inherited from val_039 and locked at runtime by `frozen_samples_and_order` / `frozen_strata`.
- **Not duplicate / not contradicted:** First reproduction of exp_040 on the 0.941 pipeline. Precedent `repro_036` reproduced the motion-EMA algorithm to 1e-12 with a byte-identical submission on the 0.933 pipeline, so bit-exact reproduction is plausible.

## Implementation risks

Verified — low risk:
- **Determinism:** `build_public_0941_ema_repro.py` asserts the parent notebook SHA (914104…) and reference metrics SHA (e90931…) before building; the smoke test asserts the whole notebook `== build()` and `cells[1:-1] == parent cells[:-1]`, so only the final contract cell plus an inserted markdown header differ.
- **Algorithm / effective-config guards:** parent runtime `effective_*` checks (motion_ema_alpha, velocity_weight, …) compare live values at abs_tol 1e-12, and `motion_relink_velocity_estimator == per_track_ema` is recorded — guards read effective config, not stale prose.
- **Contract completeness:** `REPRO_EXPECTED` is built from the frozen parent artifacts; all referenced names (`_metrics`, `_specimens`, `_ema_execution`, `_sha256_file`, `SUBMISSION_PATH`, `_contract_math`) are defined before use. Gate field resolves correctly — the controller reads `metrics["metrics"]["reproduction_passed"]`, which the contract sets.
- **Negative controls:** smoke exercises 6 faults (score, specimen, hash, ema, division, integrity) plus the clean case, asserting the pass flags flip exactly.

No blocking implementation defects found.

## Budget

Reserved 2.0 GPU h; parent ran ~1.08 h, so real cost ≈1.1 h. Budget shows 11.13 h remaining with the 6 h reserve untouched, within `max_single_experiment_hours: 4.0`. Information gain is high relative to cost — it converts exp_040 from `reproducible: false` to a reproducibility verdict, unblocking any later promotion. Worth it.

## Required changes (process gates before launch)

1. Record this review as **PASS** in the experiment record (`review.status: PENDING` → PASSED) — mandated before any launch.
2. Run and pass the local smoke test (`scripts/validate_public_0941_ema_repro.py`); `smoke_test.status` is PENDING and must be PASSED first.
3. Launch must use the deterministically built snapshot notebook (`.private/current/public_0941_ema_repro.ipynb`, 247852 B — matches the snapshot).
4. Keep it validation-only: `submission.user_authorized_count: 0`; **no leaderboard submission** is authorized.
5. After collection, produce the separate `post-run-review.md` / `post-run-review.json`; a controller KEEP alone is not final Claude approval.
6. Retain the ≥10% weekly Claude/Codex reserve; do not auto-retry this review after a timeout/quota stop.

## Recommendation

Methodology and implementation are sound, the step is justified, and the cost is small. Proceed to the next controller stage (record PASS → local smoke → the single authorized validation-only launch), subject to the process gates above.

VERDICT: PASS
