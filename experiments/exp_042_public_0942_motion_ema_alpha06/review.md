Here is the review.

---

# Review — exp_042_public_0942_motion_ema_alpha06

## Summary
A well-formed, tightly-scoped single-variable sensitivity test: motion-relink EMA `alpha` 0.4 → 0.6, velocity multiplier held at 0.5, everything else frozen. The parent (`repro_041`, exactly reproduced alpha-0.4, user-reported LB 0.942) logically justifies a controlled alpha sweep, and the archived optimization audit independently identifies `motion_relink` as the decisive, highest-leverage module — so the expected information gain is real. Construction is deterministic and hash-pinned to the frozen parent, runtime guards verify the *effective* configuration (α = 0.6, weight = 0.5) rather than notebook prose, and the gates are appropriate and correctly tightened relative to exp_040. I found no methodology or implementation blocker. PASS is contingent on the separate user launch authorization (not currently granted) and on the local smoke test passing.

## Methodology
- **Testable / one variable (yes).** `build()` loads the SHA-pinned parent (`914104…`), asserts the cell count is unchanged, and applies exactly the three alpha replacements (env var, drift-guard, import default) plus the new preflight/contract cells. `validate()` asserts the notebook equals `build()` and that the `motion_relink_edges` postprocessing and the `t_true_source` scorer functions are byte-identical to the parent. The EMA update (`α·step + (1−α)·v_prev`, nb lines 963–969) confirms α = 0.6 means less historical inertia — matching the stated mechanism. Attribution to a single variable is strong.
- **Validation / leakage / 44b6–6bba split (trustworthy, with the standing caveat).** Reuses `public_0941_frozen_train16_stratified_proxy_v1` with the frozen 16-sample selection, per-specimen split, and division strata (`frozen_samples_and_order`, `frozen_strata` enforced). The optimistic-leakage warning ("frozen models saw training videos") is preserved — this is a paired sensitivity test, not held-out generalization. No new leakage is introduced since only α changes and all checkpoints stay frozen (hashes asserted in preflight).
- **Gates.** Aggregate ≥ alpha-0.4 (0.93873); per-specimen adjusted-edge regression ≥ −0.001 vs alpha-0.4; worst per-video adjusted-edge delta vs val_039 ≥ −0.002 (alpha-0.4's worst was −0.00373, so this is a genuine robustness target); division TP ≥ 4, FP ≤ 8, FN ≤ 8. Note FP ≤ 8 is *stricter* than exp_040's ≤ 9 — the EMA division-FP improvement must be maintained. EMA-exercised-on-both-specimens check retained.

## Implementation risks
- **No missing contract fields.** primary / specimen / validation / checks / research_gates / division_counts / ema_execution / inference_identity all present. `reproducible: false` is correct for a new experiment (not a reproduction). `gate_field: alpha06_candidate_gate_passed` matches the key written by the contract.
- **Submission identity handled correctly.** `PARENT_SUBMISSION_SHA` is repro_041's `fd1162…`; the only submission check is before/after-validation self-identity — there is (correctly) no false assertion that the α-0.6 candidate matches the parent bytes, which it should not.
- **Guards verify effective config, not prose.** Preflight `_expected_effective` asserts `MOTION_RELINK_EMA_ALPHA == 0.6` and `MOTION_RELINK_VELOCITY_WEIGHT == 0.5` against runtime values (abs_tol 1e-12), plus the drift-guard cell and env var. Good.
- **Minor / confirm (not blocking).** The embedded `_VAL039_VIDEO_ADJUSTED_EDGE` per-video baselines (some > 1.0, expected for the "adjusted" proxy) should be confirmed to originate from val_039 artifacts; `video_baseline_complete` enforces only the stem set, not the values.
- English-only, no saved outputs, and a single experiment-id placeholder are statically enforced. The Chinese `optimization_audit.md` is a permitted provenance archive, not an active working doc.

## Budget
2.0 GPU-h reserved; remaining 10.07 h includes the 6 h reserve → 4.07 h usable, under the 4.0 h single-experiment cap and preserving the reserve. Comparable EMA runs consumed ~1.06–1.20 h, so the reservation is safe. **Not a duplicate and not contradicted:** α = 0.6 has never been run (prior EMA work fixed α = 0.4; exp_037 varied the velocity *weight* 0.5→1.0 and was rejected at +0.00043 — a different knob). The archived audit points at `motion_relink` as the module worth probing, so the test is on-target.

## Required changes
None to methodology or code. Preconditions before launch:
1. **User launch authorization** — GOAL.md/STATE.json currently state no successor is authorized; this PASS is a methodology gate, not that authorization.
2. Ensure `.private/current/public_0942_motion_ema_alpha06.ipynb` is generated and the config smoke test (`validate_public_0942_motion_ema_alpha06.py`) passes locally before READY.
3. Confirm the `_VAL039_VIDEO_ADJUSTED_EDGE` values trace to val_039 artifacts.

## Recommendation
Methodologically and implementationally sound. Safe to proceed to the next controller stage (local smoke → remote launch) once explicit user authorization exists.

VERDICT: PASS
