## Summary

The EMA algorithm port is semantically correct, but the experiment is not admission-ready. The required runtime off/on integrity contract is only described, not implemented. A launch would produce no `metrics.json` containing `exp057_ema_integrity_passed`; generic collection would therefore fail or remain inconclusive.

## Per-item findings

1. **EMA correctness — PASS.**  
   `velocity_um`, branch ordering, both counters, and accepted source→target EMA propagation match repro_041 semantics. The added `MOTION_RELINK_EMA_ALPHA is not None` guard correctly enables the off path.

2. **Off-switch parity — code-level PASS, runtime proof MISSING.**  
   With the environment variable explicitly set to `''`, `velocity_um` is never populated and edge selection follows repro_048. The fallback counter only affects `run_stats.csv`, not graph construction. However, no execution currently proves submission SHA `0319ba6d…`.

3. **`setdefault` semantics — PASS, documentation incorrect.**  
   [build_exp057_0944_motion_ema.py](E:/Project/Biohub_CellTracking/scripts/build_exp057_0944_motion_ema.py:31) defaults an unset variable to `0.4`; a pre-set empty string disables EMA. Therefore “unset/empty means off” in the builder/config prose is false: only explicit empty means off.

4. **Static validator — passes current artifact, but overclaims.**  
   Reverse-patching establishes exact equality of the changed code cell, and I independently confirmed that the produced notebook differs structurally from the base only in that cell’s source. The validator itself ignores markdown, outputs, metadata, cell ordering/type manipulation, and imports mutable patch definitions from the builder. It therefore does not generally prove whole-notebook single-variable equality.

5. **Parity proof — insufficient.**  
   The fixture design correctly exercises the expected flip, but:

   - `ema_used` is computed and never asserted ([verify_exp057_ema_parity.py](E:/Project/Biohub_CellTracking/scripts/verify_exp057_ema_parity.py:153)).
   - Only endpoint pairs are compared, not complete ordered edge records or submission bytes.
   - Configuration parsing and `setdefault` behavior are bypassed by manually injecting globals.
   - It is not wired into smoke/tests and could not run in the available project or system Python because NumPy is absent.

6. **Config/gates — declarations correct, implementation missing.**  
   `gate_field`, Codex admission, zero authorized submissions, and explicit-authorization flags are correct. But neither the notebook nor a collector:

   - produces EMA-off and EMA-on submissions,
   - verifies the off SHA,
   - computes canonical added/removed edges,
   - asserts EMA telemetry,
   - emits `exp057_ema_integrity_passed`,
   - or writes a controller-compatible `metrics.json`.

   The generic collector requires `metrics.json`; thus this is a required gap before launch, not post-launch cleanup.

7. **Other checks.**  
   Base SHA and current notebook provenance are correct; no GT leakage was found. The 1 GPU-hour reservation would preserve the six-hour reserve. The notebook’s inherited runtime report still identifies the base experiment and provides no effective-alpha receipt. Also, `gate_submission` enforces cap/duplicate checks but does not itself enforce the config’s explicit-user-authorization field, so that authorization remains a mandatory human/process gate.

## Required changes before launch

- Implement and test a fail-closed exp_057 runtime adapter/collector that obtains off and on outputs from the same immutable snapshot, verifies off SHA `0319ba6d…`, requires canonical edge difference ≥1, validates topology and EMA telemetry, records effective alpha/source hashes, and emits `metrics.exp057_ema_integrity_passed`.
- Make the parity test assert EMA execution and compare complete ordered edge records; run it in a declared dependency-capable test environment.
- Strengthen static validation to compare the entire parsed notebook except the one exact source field and require one unique relink definition.
- Correct all “unset/empty means off” prose to “unset defaults on; explicit empty disables.”
- Repeat fresh Codex admission review after those implementation changes. No launch or leaderboard submission before the remaining smoke, reservation, and explicit user authorization gates.

## Recommendation

Revise before controller proposal/snapshot/smoke. The algorithmic edit can be retained; the blocking work is the missing executable integrity and collection contract.

VERDICT: REVISE (wire the EMA-off/on runtime collector and fail-closed metrics gate; strengthen the parity/static checks and correct off-switch provenance)
