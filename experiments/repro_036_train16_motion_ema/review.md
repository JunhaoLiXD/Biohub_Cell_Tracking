# Review â€” repro_036_train16_motion_ema

## Summary
`repro_036` is a **reproducibility gate**, not a hypothesis-driven improvement: it re-runs the accepted `exp_035` motion-EMA algorithm unchanged and adds only a controller-owned contract requiring exact aggregate + per-specimen metrics and a **byte-identical submission SHA256** versus `exp_035`. Its purpose is to flip `exp_035`'s recorded `reproducible: false` to true before any promotion â€” a legitimate, GOAL-mandated step (promotion criterion 5). The contract's embedded expected values were verified against `exp_035/metrics.json` and match exactly. No blocking issues.

## Methodology
1. **One variable, testable.** `variables_changed: diagnostic_reproducibility_contract_only`; the algorithm cells are retained from the 0.933 upstream. The gate is a clean exact-equality test (`abs_tol=1e-12` on primary/adjusted/division/per-specimen + submission-SHA equality). For a reproduction, exact-equality-to-parent is the *correct* contract â€” unlike the diagnostic-only equality checks that made `exp_034` a REVISE.
2. **Validation trustworthy for its purpose.** Same `public_0933_embedded_train16_stratified_proxy_v1`, 8 samples/specimen, both `44b6`/`6bba`, with `reproduction_specimens_exact` per-specimen checks. Train-leakage is acknowledged (optimistic absolute score) but is irrelevant to an equality gate that compares to the parent rather than making a science claim.
3. **Guards verify effective config, not prose.** The environment cell (lines 178â€“226) explicitly assigns every `BIOHUB_*` var; the guard (254â€“297) reads `os.environ`, requires presence, and raises on drift â€” closing the `exp_010`-class "unassigned guard" failure. Runtime EMA is surfaced (`ema_predictions` 255467/137518, `one_frame_fallbacks` 0), and the guard's `_EXPECTED_NUMERIC` now includes the learned-bonus (1.0) and EMA alpha (0.4) that the `exp_034` review flagged as missing.
4. **Parent justifies it; not a bad duplicate.** `exp_035` is KEEP (+0.002064; 44b6 +0.0014, 6bba +0.0026, no adjusted-edge regression) but `reproducible: false`. A reproduction is the required next step, and `repro_003/004` set precedent (byte-identical submissions) for the 0.933 base.

## Implementation risks
- **Determinism assumption (primary risk).** The byte-identical SHA gate assumes the EMA/relinkâ†’ILP path is bitwise-deterministic on T4Ã—2. This config differs from the `repro_003/004` base that proved determinism, so if any nondeterminism exists the gate fails â€” but it fails *cleanly* (no false-positive science).
- **SHA provenance not independently checkable.** The expected `93eec4â€¦` submission digest could not be cross-checked from the files read (`exp_035/metrics.json` stores no submission SHA). The five expected metric values all match `exp_035` exactly, strongly corroborating real-artifact provenance; still, confirm the SHA was pulled from `exp_035`'s collected submission guard report, not hand-entered.
- **Env-injection dependency.** The guard aborts on any missing/drifted `BIOHUB_*` var; the launch env must not shadow the environment cell.

## Budget
Tier-1, 2.0 h reservation (`exp_035` actual â‰ˆ1.2 h). Remaining 16.49 h with a 6.0 h reserve and 4.0 h single-experiment cap â†’ comfortably within budget. Information gain is modest (it confirms reproducibility of a small, train-leaky delta) but is a cheap, required prerequisite to promotion.

## Required changes
None blocking. Recommended verifications only (no code edits during review): (1) confirm the expected submission SHA256 originates from `exp_035`'s collected guard report; (2) confirm the launch harness injects env exactly matching `_EXPECTED_NUMERIC`/`_EXPECTED_TEXT`.

## Recommendation
Safe to proceed to the next controller stage (local smoke test / remote launch). The gate is well-scoped, self-verifying against real `exp_035` artifacts, and correctly enforces exact reproduction rather than stale prose.

VERDICT: PASS
