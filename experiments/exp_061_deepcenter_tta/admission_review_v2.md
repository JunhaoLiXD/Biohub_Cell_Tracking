## Summary

**REVISE before launch.** Strategy consensus is explicitly recorded in the Claude-authored v5 proposal, Codex challenges v1–v5, and revision tables. The implementation does not fully satisfy that agreement.

Read-only checks confirmed all six manifest hashes, notebook parsing, embedded-module equality, and stripped-parent source parity. The behavioral suite reports PASS, but NumPy-dependent checks were skipped. I inspected the available git diff; no files were changed.

## Methodology

The three fixed arms isolate one major variable: DeepCenter TTA composition. Replaying from raw predictions reaches both gap1 and safe-division vetoes. This is distinct from exp_060’s threshold intervention and is not contradicted by earlier feature-TTA results.

The parent’s recorded 0.947 result motivates investigation but does not establish that DeepCenter TTA caused its improvement.

This is an **integrity-gated Public-LB probe**, not held-out biological validation. With the validator disabled, it provides no measured quality comparison across `44b6` and `6bba`. Historical proxies remain optimistic because frozen feature extractors saw training data. A displayed LB tie cannot establish zero effect or cross-domain generalization.

## Implementation risks

Findings refer to the [snapshotted harness](E:/Project/Biohub_CellTracking/experiments/exp_061_deepcenter_tta/snapshot/extra_files/exp061_deepcenter_tta.py).

- **Output audits do not cover experimental submissions.** The parent audits `submission.csv` before appended arms run. The arm writer checks dangling endpoints but omits the parent’s consecutive-frame and lineage-degree assertions. Apply those checks to every arm before declaring completion.

- **Effective-config equivalence is incorrectly inferred** at line 743: matching control configuration plus matching control CSV does not prove equality to the frozen parent configuration. Different settings can produce identical control output while changing treatment behavior. Compare live values directly against an explicit parent configuration.

- **Valid nulls are rejected** at lines 691–698. `executed = heatmap_differs` contradicts consensus: correct transforms can yield identical heatmaps. Execution evidence must come from actual views, inverses, counts, and provenance; response magnitude is a separate result.

- **Telemetry is incomplete and unnecessarily expensive.** The candidate logger calls the scorer with fresh `{}` caches for every candidate, repeating frame loading, normalization, and heatmap accumulation—even for bypassed gap candidates. Gap records omit endpoint identities; candidate records lack directly linked acceptance and final survival. Gap1/gap2-specific final deltas are absent. Detailed telemetry is persisted only after the arm loop, so completion receipts alone do not preserve the agreed per-arm evidence.

- **Cache rejection is deferred.** `_validate(arr)` returns failure, but callers still consume the array. Existing disk entries lack a persisted expected digest because `_view_sha` starts empty. Reject invalid/unverifiable entries before use and test this behavior.

- **Rollback does not restore parent behavior.** Setting `BIOHUB_EXP061_ENABLE=0` skips the appended probe but still disables the parent validator unconditionally. That can leave the base configuration instead of the parent’s selected `tight55` output.

## Budget

The ledger records **26.493 hours remaining**, six protected, with no reservation. A two-hour reservation is affordable on that ledger.

Feasibility remains unsupported: control cost initializes to zero, later admission uses previous total arm duration, and no measured frame-demand/forward-time/cache-capacity/I/O worksheet was located. This does not demonstrate preservation of the 20-minute reserve. Repeated telemetry scoring adds unbudgeted work. Separate LB promotion runs also need accounting.

## Required changes

1. Fix the output audits, explicit parent-config assertions, valid-null handling, cache rejection, telemetry, and rollback issues above.
2. Supply the agreed measured feasibility worksheet and conservative per-arm admission estimates.
3. Replace source-string/self-equality tests with bounded executions covering reordered arms, corrupt/stale caches, interrupted finalization, config drift, and valid zero-response cases. The current [arm-order test](E:/Project/Biohub_CellTracking/experiments/exp_061_deepcenter_tta/snapshot/extra_files/test_exp061_behavioral.py:216) never reorders execution.
4. Reconcile stale snapshot descriptions and state records, then obtain fresh snapshot-specific review and smoke evidence. Keep reservation, launch authorization, separate LB authorizations, duplicate checks, and promotion gates intact.

## Recommendation

Retain the agreed strategy; revise its implementation before execution. Fresh GPU control parity belongs in the authorized run and need not be demonstrated locally beforehand. The defects above are independently reviewable without that GPU run.

VERDICT: REVISE
