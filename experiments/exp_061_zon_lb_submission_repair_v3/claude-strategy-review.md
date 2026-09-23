Acting as primary research strategist on this bounded, read-only review of the v3 zon-deployment amendment. Judgment on the merits:

**What holds up:**
- **Change is purely reductive and policy-frozen.** Removing the original-XY reference and `xyonly`/`xyd4` dev replays from the scoring path, with an AST-identical `_accept_wrapper`, a hash-bound byte-identical parent inference cell, and only additive telemetry/`per_dataset` fields, is a legitimate deployment-only edit. It cannot change the per-input zon output policy.
- **Evidence is honestly scoped.** It does not claim timeout is proven, labels ~97m as an illustrative screen, bounds the visible run at ≤60m40s rather than "~2h," and drops the unachievable 4× performance prerequisite while keeping a 4× deterministic correctness fixture plus the one remote run as the actual feasibility measurement. No overstated local↔hidden parity.
- **Publication is fail-closed and atomic.** Unlinking any pre-existing parent `submission.csv`, staging + digest-verifying the zon CSV, and refusing to let a fallback parent CSV survive a zon failure directly targets the earlier incorrect-format failure class, not just workload.
- **Budget/stop rule are conservative and unchanged in spirit:** ≤2.0 GPU h, hard 2-hour watchdog retained, 20-min finalization reserve, 6-hour ledger floor, single check, no auto-relaunch, and no LB submission.
- **The disclosed `arm_summaries` keys-vs-`.values()` regression** was caught by the validator, corrected against frozen v2 behavior, and re-hashed — transparency, not concealment.

**Required caveat (non-blocking):** the two byte-identical known-good CSVs that still returned incorrect-format errors are strong evidence the hidden failure may be mechanism/structural rather than workload. So the diagnostic must be read asymmetrically: success would support the workload-reduction path, but a repeat failure must **not** be recorded as confirming timeout or workload infeasibility — it would instead point to a structural/hidden-input cause. The proposal already frames this as diagnostic and accepts residual hidden-input risk, so this is a condition on interpretation, not a defect in the change.

This is strategy agreement only. It remains gated by fresh experiment-specific Codex admission (`require_codex_review`), snapshot smoke, explicit budget reservation, and the existing controller gates before any launch; and it authorizes no LB submission.

VERDICT: CONSENSUS
