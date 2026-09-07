# Independent Review — `val_039_public_0941_train16`

## Summary

The experiment adapts the frozen, LB-confirmed 0.941 inference (`repro_038`, submission 56044403, SHA `bf66c879…52bd`) onto the established val_008 train16 selector/scorer to produce a frozen train16 baseline for the new working parent. It is a **validation-and-instrumentation change only** — no inference hyperparameter or model is touched. The hypothesis is a **gate** (produce complete, identity-verified train16 evidence), not a metric-beating claim, correctly matching the current handoff where old 0.933/EMA train16 numbers are descriptive controls, never an admission threshold. Build is deterministic and the static validator asserts byte-equality against a reviewed build. Current state is PROPOSED / review PENDING / smoke PENDING — this is the gating fresh review.

## Methodology

- **Single attributable variable.** Inference cells 0–4 asserted identical to the parent; postprocessing functions identical except `load_deepcenter_veto_detector` (loader telemetry only); the 13 scorer functions and selector/runner asserted byte-identical to val_008. Only additions are telemetry, a runtime effective-config guard, frozen-identity checks, per-video stage stats, and the metrics contract. Attribution is clean.
- **Protocol trustworthy and leakage-honest.** Reuses val_008 frozen sample identities/order/strata (8/specimen, 4 division-positive/specimen) across both domains; `FROZEN_SAMPLES`/`FROZEN_POSITIVES` are re-derived from val_008 `metrics.json` and re-checked at runtime. The optimistic train-derived nature (released models saw training videos) is disclosed in config, header, and warning.
- **Domain split preserved.** `44b6` and `6bba` metrics are computed separately with per-specimen samples/positives/negatives and error summaries; the contract fails if either specimen's set or strata drift.

## Implementation risks

- **Guards check effective values, not stale prose (verified).** Preflight compares live variables (`DET_THRESHOLD`, `GAP_CLOSE_UM`, `SAFE_DIV_*`, `MOTION_RELINK_VELOCITY_WEIGHT`, `BIOHUB_*`) against expected constants at `abs_tol=1e-12`, and binds DeepCenter via a **freshly computed** load hash cross-checked against epoch==2 and the expected SHA. All referenced upstream symbols (`_runtime_integrity_receipt` @45, `_guard_report` @1872, `checkpoint_epoch`, `DEEPCENTER_EXPECTED_EPOCH`) are defined before use. The injected `VALIDATION_STAGE_STATS[stem] = _stage_stats` consumes a real return value of `filter_output_graph` — no NameError. No adaptation bug found.
- **Submission byte-integrity enforced both sides** (`submission_sha256_exact` before, `test_submission_unchanged_after_validation` after), satisfying the GOAL "before and after" requirement.
- **Output contract complete** for the gate field `validation_contract_passed`: inference identity, frozen samples/order/strata, `sample_count==16`, finite scores, density-penalty availability, stage-stats completeness, submission invariance; plus per-video stage stats and per-specimen error summaries.
- **Minor / non-blocking:** `primary_hash_exact`/`secondary_hash_exact` compare the upstream receipt to literals rather than to a recomputed load hash (DeepCenter does both) — weaker observability, not a correctness gap. `config.source_notebook` points at `.private/current/…` while the reviewed artifact is the snapshot; the validator's `actual == build()` equality closes that at smoke time.

## Budget

2.0 GPU-h ≤ 4.0h single-experiment cap, no approval needed; remaining 13.51h with 6.0h reserve leaves ~7.5h free, reserve intact. Parent train16 runs finished in ~1.1–1.2h, so 2.0h is a safe ceiling. Single bounded Claude review, no auto-retry. **Information gain is high:** the new 0.941 parent has only a non-comparable train4 probe (INCONCLUSIVE); this establishes the prerequisite frozen train16 baseline for any future single-variable optimization and for comparison against the 0.9273 EMA line.

## Required changes

None before proceeding. Optional future hardening (do not block): (1) recompute primary/secondary weight hashes at load time like DeepCenter; (2) align `config.source_notebook` to the snapshot or note the controller snapshots it.

## Recommendation

Proceed to the next controller stage — local smoke test (`scripts/validate_public_0941_train16.py`) then the single authorized 2.0h launch. The change is single-variable, leakage-honest, identity-guarded on effective runtime values, budget-safe, and warranted by the parent. Do not submit to LB, promote, or optimize in this step.

VERDICT: PASS
