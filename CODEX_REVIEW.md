# Latest Codex Review

Experiment: `exp_060_deepcenter_safe_div_threshold_sweep`  
Captured: 2026-09-18T19:28:12+00:00

## Summary

**REVISE.** Explicit strategy **CONSENSUS** is recorded in the Claude proposal and Codex v1–v3 objection/revision history. The experiment is reasonable, but required isolation verification remains incomplete.

Read-only checks passed: all six snapshot hashes, stripped-parent source parity, embedded-module equality, and the structural validator. Git diff was inspected. No files were changed.

## Methodology

- The fixed **0.20/0.18/0.22** bracket tests one variable on the correct parent, repro_059.
- The parent’s bundled +0.003 does not establish a threshold benefit. Likewise, 316 accepted/414 rejected candidates do not establish how many scores lie near the proposed boundaries.
- No new test-label leakage was identified. Public-LB selection provides tuning evidence, not independent generalization or demonstrated transfer between **44b6 and 6bba**.
- Parent selection artifacts contain **eight crops, four per specimen**, contradicting the four-sample summary.
- Historical failures on different checkpoints do not directly invalidate this probe.

## Implementation risks

- **Consensus-required isolation evidence is missing.** Arm-order testing uses a mock `filter_output_graph`; only the scalar acceptance function is extracted from the actual parent. This does not verify real postprocessing order invariance.
- The runtime input fingerprint hashes **paths, sizes and modification times**, not graph contents. Cached heatmaps remain mutable and are neither content-verified nor protected against mutation.
- Effective configuration checks now compare 74 live globals, environment settings and assigned thresholds. Immediate control-SHA rejection, required metrics fields, strict telemetry serialization, and exact fork/edge differences are present.
- The watchdog now raises `KeyboardInterrupt` and attempts child termination, fixing the earlier swallowable `TimeoutError`. Python signal handling can nevertheless be delayed during native computation.
- Implementation reruns full postprocessing and the parent’s adaptive sweep; descriptions claiming only appended cells or downstream-only replay are stale.

## Budget

The recorded **26.493 hours** accommodates a two-hour reservation while preserving six protected hours. No reservation exists.

Information gain is reasonable for one bounded run, but the runtime estimate must include parent sweep execution and duplicated heatmap computation. Exact weekly model allowance remains unavailable.

## Required changes

1. Verify arm-order invariance using **actual extracted postprocessing** with deterministic cached inputs, including competing candidates and downstream filtering.
2. Verify graph and heatmap **content immutability** across arms; protect cached arrays or compare content digests.
3. Reconcile strategy/config descriptions with the implemented replay and cost model. Correct the validation-panel count.
4. Rebuild the snapshot after changes and obtain fresh admission review, then complete smoke and reservation gates. Keep leaderboard submission and promotion separately authorized.

## Recommendation

Do not launch this snapshot yet. Strategy consensus is satisfied; implementation verification is the remaining substantive gap. The behavioral suite was inspected but not executed because it creates temporary files, contrary to this review’s read-only restriction.

VERDICT: REVISE
