# Latest Codex Review

Experiment: `exp_057_0944_motion_ema`  
Captured: 2026-09-16T04:33:00+00:00

## Summary

The current snapshot is safe to advance to local smoke testing. The hypothesis isolates one major variable—motion EMA α=0.4—on the verified repro_048 Public LB 0.944 bundle. Explicit strategy `CONSENSUS` is recorded after four Codex challenges and Claude revisions.

## Methodology

- Parent choice is logical: repro_048 has authenticated Public LB 0.944 evidence, while the train16 proxy is acknowledged as contaminated and diagnostic-only.
- The primary hypothesis is falsifiable at displayed leaderboard precision: `>0.944` succeeds; `≤0.944` terminates this recipe without an α sweep.
- No ground truth, video identity, or specimen-specific branching enters inference.
- The four test movies cover both 44b6 and 6bba, although Public LB supplies only aggregate quality. Per-movie runtime statistics remain available for post-run domain audit.
- This is not a duplicate: EMA was validated on the weaker 0.941 lineage but has not been tested on the complete 0.944 bundle.

## Implementation risks

- The snapshot differs from repro_048 only in the authorized code cell: EMA configuration/state, prediction and propagation, telemetry, timing, and the fail-closed integrity block.
- Effective α is checked numerically at runtime; stale prose or a pre-existing non-0.4 environment value cannot pass.
- EMA-off must reproduce the exact parent submission SHA-256 `0319ba6d…`; EMA-on must execute EMA prediction and change at least one canonical edge.
- Existing graph checks cover all four datasets, contiguous rows, dangling/nonconsecutive edges, maximum indegree 1, maximum outdegree 2, and checkpoint hashes.
- The emitted metrics satisfy the controller’s required schema and gate lookup. Omitting `reproducible` safely prevents promotion because the controller treats it as false.
- Admission v4 cites an obsolete pre-final notebook hash (`8a1436…`). The actual snapshot, working notebook, parity receipt, and manifest now consistently match `38fb52c2…`. This formal review covers that current snapshot; the older admission record should remain historical rather than be rewritten.

## Budget

The 1.0-hour reservation is proportionate to the parent’s 0.357-hour run and remains below the four-hour cap. With 26.9027 hours remaining, the protected six-hour reserve is preserved. Exact weekly model allowance remains unknown, but this was one bounded review.

## Required changes

No implementation revision is required. Before remote launch:

1. Record this formal PASS against the current snapshot.
2. Run the configured local snapshot smoke.
3. Reserve 1.0 GPU hour and reach controller `READY`.
4. Obtain explicit user authorization for the Kaggle launch.
5. Treat any Public LB submission as a separate authorization after runtime integrity passes and remote submission history is checked.

## Recommendation

Proceed only to the next controller stage—local smoke testing. PASS does not authorize launch, leaderboard submission, or promotion, and it does not predict that EMA will improve the score.

VERDICT: PASS
