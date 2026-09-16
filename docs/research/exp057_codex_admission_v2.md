## Findings

1. **Runtime integrity — REVISE.** The off-SHA, canonical edge-difference, EMA telemetry, effective alpha, velocity weight, and fail-closed assertion are sound. However, `metrics.json` is not controller-compatible:

   - `primary_metric` is a string; the controller requires a finite number.
   - Required `validation.protocol` is absent.
   - Executed-source hashes requested in round 1 are not included.
   - `runtime_seconds` measures only initial prediction, excluding both postprocessing passes.

   See [build_exp057_0944_motion_ema.py](E:/Project/Biohub_CellTracking/scripts/build_exp057_0944_motion_ema.py:164) versus [metrics.py](E:/Project/Biohub_CellTracking/experiment_controller/metrics.py:53).

2. **Off-pass writer — PASS.** The current implementation mirrors dataset ordering, node ordering, edge ordering, field order, row IDs, rounding, and sentinel values. Any byte-relevant divergence will mismatch the pinned SHA and fail closed. The known reference hash is therefore meaningful.

3. **Scope, mutation, and materiality — mostly PASS.** All referenced globals are in scope. Each pass reconstructs fresh node/edge dictionaries, and the off pass does not overwrite `submission.csv` or `stats_rows`. The canonical edge-set symmetric difference and `>=1` gate correctly reject an EMA no-op.

   One design discrepancy remains: `filter_output_graph` creates fresh DeepCenter caches, and DeepCenter executes its Torch model on CUDA. Consequently, the off pass can repeat GPU inference despite the claimed “no second GPU pass.” This also strengthens the runtime-accounting concern.

4. **Static/parity validation — REVISE.**

   - Static validation passes, and independent comparison confirms the current artifact has exactly one differing raw cell, identical notebook metadata, and no saved errors.
   - The validator does not actually compare the complete parsed notebook excluding one exact source field. It filters code/non-code sources, ignores cell metadata, outputs, interleaving, and notebook structure, and imports mutable patch definitions from the builder.
   - Writer-mirror validation is token-count based and can miss semantic divergence.
   - The parity proof compares complete fields but sorts the outer record collection, discarding edge order ([verify_exp057_ema_parity.py](E:/Project/Biohub_CellTracking/scripts/verify_exp057_ema_parity.py:133)).
   - The static check ran successfully. The parity proof could not run in the declared local environment because NumPy is unavailable.

5. **Off-switch prose — PASS.** Builder and config now correctly state: unset defaults EMA on at `0.4`; explicit empty disables it.

6. **Gates/provenance — PASS except above blockers.** No GT leakage or relaxed review, promotion, submission, or authorization gate was found. `user_authorized_count: 0` and explicit submission authorization remain intact.

## Required changes

- Emit numeric `primary_metric`, the exact configured `validation.protocol`, full-run runtime, and source-provenance hashes.
- Either prevent repeated DeepCenter CUDA inference through shared cached evidence or explicitly account for and validate the second GPU postprocessing pass.
- Preserve edge-list order in the parity comparison and run it in a declared dependency-capable environment.
- Make static validation compare the complete parsed notebook after replacing only the authorized cell source; avoid relying solely on imported mutable patches and token counts.

## Recommendation

Do not proceed to controller proposal/snapshot/smoke yet. The runtime algorithm is fail-closed, but generic collection would currently produce `INVALID_METRIC`, and two round-1 validation requirements remain incompletely implemented.

VERDICT: REVISE (controller-incompatible metrics schema; incomplete runtime/source accounting; parity discards edge order; static validator does not prove full notebook identity)
