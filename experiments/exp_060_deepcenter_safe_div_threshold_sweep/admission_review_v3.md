# exp_060 — Codex ADMISSION review v3 (verdict: BLOCK, converging to 2 hardening items)

Reviewer: Codex `gpt-6-astra`, low, read-only. Date: 2026-09-18.
Scope: v3 implementation (after admission BLOCK v2). Codex ran the extracted-gate test + verified
embedded-module equality.

## Verdict: BLOCK (core + v2 fixes #1/#3 accepted; 2 hardening items remain)

### Codex-VERIFIED resolved (non-blocking)
Score-anomaly rejection, filtering-exception handling, metrics-before-telemetry ordering, and
candidate attribution all address their v2 defects. Builder check-only, structural validation,
embedded-module equality, and the extracted real-gate checks pass.

## Remaining blockers (→ v4)

1. **Whole-run deadline not enforced over the PARENT run.** The SIGALRM watchdog is armed only in
   the appended sweep (after the parent's ~1.3h run) and cancelled before finalization; the final
   elapsed check precedes metrics writing. A run that crosses 2.0h during the parent (or finishes
   an arm just over budget) can still persist. Fix: arm the watchdog BEFORE parent execution (a
   top-of-notebook injected `# exp060` line), retain it through finalization, fail closed if
   installation fails, and recheck elapsed when committing metrics.
   NOTE (tension to reconcile): a hard SIGALRM firing DURING the parent run would crash before the
   appended metrics writer runs (=> no metrics.json), which conflicts with the fail-closed
   "always write metrics" requirement. v4 must reconcile (e.g., top-level handler writes a minimal
   over-budget failure metrics.json before exiting, or the budget guard is a hard kernel-level
   stop accepted as REMOTE_FAILED).

2. **Behavioral coverage incomplete.** The deadline probe starts already overdue (never tests
   interruption DURING execution or a final-arm overrun); the fingerprints check only two config
   fields + hard-coded candidate IDs, not heatmap INPUT content. Fix: add mid-execution
   interruption + final-arm-overrun probes, an unreliable-clock probe, a telemetry-serialization
   fault probe, and assertions over the full effective configuration + the heatmap input set.

No launch until these clear fresh admission + snapshot smoke.

## v4 RESOLUTION (2026-09-18) — both blockers addressed; local gates pass

1. **Whole-run deadline now enforced over the PARENT run.** The builder injects (strippable
   `# exp060`) a 16-line block immediately AFTER `from __future__`: it records `_EXP060_RUN_START`
   and arms a POSIX SIGALRM whole-run watchdog (`alarm(7200)`) BEFORE the parent runs. Its handler
   writes a fail-closed over-budget metrics.json (schema/experiment_id/validation/gate=False) to
   /kaggle/working/metrics.json THEN raises — reconciling the hard-interrupt vs always-write-metrics
   tension exactly as Codex suggested. The appended module uses `_EXP060_RUN_START` as the
   whole-run clock, adds a `whole_run_watchdog_armed` gate check, and DISARMS the watchdog only at
   the very end (after metrics+telemetry). A final `within_hard_stop_and_timing_reliable` recheck
   fails closed on overrun OR unreliable timing.
2. **Behavioral coverage extended.** `test_exp060_behavioral.py` now additionally asserts:
   heatmap INPUT content (exact (dataset,t) frame set), a FINAL-ARM OVERRUN via a patched moving
   clock (all pre-arm checks pass, the final elapsed gate fails closed, not a pre-arm stop), an
   unreliable-timing probe, a whole-run-watchdog-not-armed probe, and a telemetry-serialization
   fault probe (metrics written first, telemetry absent, gate not masked). 26 checks pass, incl.
   the extracted real parent gate.

Local gate suite (all pass): compile; builder parity (18 injected `# exp060` lines strip to
parent); structural validator; behavioral test (26 checks). NEXT: fresh Codex admission on v4.
