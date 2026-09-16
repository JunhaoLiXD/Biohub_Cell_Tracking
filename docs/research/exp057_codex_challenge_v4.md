V4 resolves the sole v3 defect:

- `velocity_um` state and `velocity_um.get(source_id)` prediction are exact.
- Both fallback branches and telemetry counters match the repro_041 reference.
- Accepted matches propagate EMA state from source to target using the specified alpha formula.
- The unset/empty off-switch preserves repro_048 submission behavior by never populating `velocity_um`.
- The canonical `|added ∪ removed| >= 1` gate remains deterministic and sufficient to prevent a null submission.
- No remaining material defect found. The stale “v1 authored” footer is cosmetic only.

VERDICT: PASS  (exp_057 v4 CONSENSUS-ready to proceed to implementation; not an authorization to launch/submit -- still needs fresh Codex admission review of the implementation, smoke, reservation, explicit user authorization for the one LB submission.)
