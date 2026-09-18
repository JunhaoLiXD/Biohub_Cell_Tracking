# exp_060 — Codex ADMISSION review v1 (verdict: BLOCK)

Reviewer: Codex `gpt-6-astra`, low, read-only. Date: 2026-09-18.
Scope: implementation admission of the built exp_060 threshold-sweep notebook + module + config
+ validator. Strategy was already CONSENSUS (exp060_codex_challenge_v3.md).

## Verdict: BLOCK (core mechanism VERIFIED sound; 5 contract/robustness/telemetry defects)

### Codex-VERIFIED correct (non-blocking positives)
- **Byte-parity crux OK**: CSV columns/row fields, z/y/x rounding, `sorted(nodes_by_id)`, edge
  order, `DictWriter` `newline=''` all match the parent `write_test_submission`. The .tmp/replace
  and preview/run_stats do not affect submission.csv bytes.
- **Global rebinding correct**: setting `DEEPCENTER_SAFE_DIV_THRESHOLD`/`MOTION_RELINK_TIGHT_UM`
  and the `deepcenter_heatmap_for_frame` monkeypatch take effect for parent callers; fresh
  per-call caches do not defeat persistent reuse; patches restored in `finally`.
- Gap threshold stays 0.25 (invariant across arms). Output path, gate-field wiring, admission
  flags, no-auto-submit all appropriate.

## Blocking defects (fix for admission PASS)

1. **metrics.json missing required `validation` object.** `experiment_controller/metrics.py:56`
   rejects the payload before the gate is evaluated. Add a `validation` object (e.g.
   `{"protocol": "public_0947_deepcenter_safe_div_threshold_sweep_v1"}`) and verify the whole
   payload against the ACTUAL controller parser.

2. **Telemetry lacks candidate node identities (violates CONSENSUS §3).** dataset+t+point cannot
   distinguish competing parents. Capture parent / existing-child / candidate-child node IDs AT
   the safe-division call site, plus bypass reason and final survival. Fork deltas from diffing
   CSVs also miss changed daughters under an unchanged parent ID.

3. **Runtime + budget enforcement incomplete.** `predict_seconds + sweep_elapsed` excludes parent
   setup, validation inference, PP-sweep, submission postprocessing; the persistent heatmap cache
   only starts at the sweep, so DeepCenter inference done during the parent run is REPEATED.
   `expected_gpu_hours: 2.0` reserves but does not ENFORCE a deadline. Measure full execution
   time, enforce the 2.0-h hard stop, and reconcile the still-enabled parent adaptive PP-sweep
   with the agreed plan (it re-runs and re-selects, wasting time).

4. **Failure handling ≠ stop contract.** Parity is checked only AFTER all three arms run (should
   check the 0.20 control immediately and stop). Nonfinite scores become `None` and pass
   `telemetry_finite`; scoring exceptions are swallowed; conversely a retained NaN makes telemetry
   serialization (`allow_nan=False`) raise BEFORE metrics.json is written. Check control parity
   first; distinguish missing / nonfinite / error; emit VALID failure metrics before stopping.

5. **Isolation/config verification absent.** No test establishes arm-order invariance, unchanged
   shared heatmaps, or threshold-only effective-config differences; only `MOTION_RELINK_TIGHT_UM`
   is asserted. Add BEHAVIORAL tests using extracted parent functions + frozen inputs, full
   effective-config assertions, heatmap/input fingerprints, and GPU-call counters. Validate the
   embedded notebook logic, not merely strings in the separate module.

## v2 RESOLUTION (2026-09-18) — all 5 defects addressed; local gates pass

1. **metrics.json `validation` object** — added `validation: {protocol: public_0947_deepcenter_
   safe_div_threshold_sweep_v1}` (matches config), plus experiment_id from the injected global.
   Verified against `experiment_controller/metrics.py` fields.
2. **Call-site node-ID telemetry** — the builder now injects (strippable `# exp060`) a no-op stub
   before `def add_safe_divisions_postlink` and a logger call immediately before the safe-div gate
   (line 2699), capturing parent/existing-child/candidate-child IDs + DeepCenter score + status.
   The module rebinds the stub to a real logger only while an arm is active (parent run unaffected).
3. **Runtime + hard stop** — runtime_seconds measured from process start
   (`_exp060_process_start_seconds`, psutil/proc fallback); a 2.0-h deadline is ENFORCED between
   arms. Adaptive-sweep reconciled: the parent sweep runs as part of the byte-frozen pipeline;
   exp_060 does not use it for selection (documented). Heatmap-recompute limitation documented.
4. **Fail-closed stop contract** — the 0.20 control parity is checked IMMEDIATELY after the 0.20
   arm and STOPS before 0.18/0.22 on mismatch; missing/nonfinite/error scores are distinguished
   and never serialized as NaN; metrics.json is always written (gate False on failure), no crash.
5. **Behavioral isolation test** — `scripts/test_exp060_behavioral.py` runs the module against a
   mock parent namespace and behaviorally verifies: heatmap computed once/frame across 3 arms
   (GPU-call counter), arm-order invariance, threshold-only effect (0.18 admits >= 0.22),
   fail-closed early-stop, metrics contract, full-ID telemetry.

Local gate suite (all pass): compile; builder parity guard; structural validator
(`validate_exp060_notebook.py`); behavioral test. Rebuilt notebook parity guard PASSES (strip
appended cells + `# exp060` lines == parent). NEXT: fresh Codex admission on the v2 build.

## Plan → v2 revision, then fresh Codex admission

Fix 1/4 (quick: validation object, early-parity stop, missing/nonfinite/error distinction,
failure-metrics-before-raise). Fix 2 (instrument the safe-div call site for parent/child IDs +
survival). Fix 3 (full-run timing + enforced hard stop + decide whether to disable the parent
adaptive PP-sweep). Fix 5 (behavioral isolation test harness with extracted parent functions,
config fingerprints, GPU-call counter). Then rebuild + re-validate + fresh Codex admission.
