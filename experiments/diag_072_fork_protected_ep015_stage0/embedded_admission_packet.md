# Independent admission review packet

Return exactly `VERDICT: PASS`, `VERDICT: REVISE`, or `VERDICT: BLOCK`. Review only
the evidence embedded here; do not call shell tools. This is a Tier C, one-run,
non-submitting diagnostic.

Hypothesis: prune learned edges below 0.15 except both outgoing edges from every
source whose out-degree is exactly two on the graph immediately before pruning.
Parent is immutable exp065 notebook SHA
`6baeb36bd9d66a3f556c75741192f6e30320e065a1c51f7c213e101aeb1043be`.
Candidate notebook SHA is
`5b7c0249547c213127909e69bd319e1a0ff4f1cb623ba97cf428f06cf3090c0d`.
Adjudicator SHA is
`c467eaaaf0fc07b75b643e450bfbf1f6fc8d163167bd5096a6ced2a3c9ce4597`.

Strategy provenance: Claude packet SHA c3c8bae02c557268f1dab81274f352464300b444a3fbdece876b604c283e8b1b;
Claude revision SHA 8901e362094d41631b6d45b73f168c4e3fa9b601f23da2c0f18e0e114b8bb4f9;
Codex challenge/CONSENSUS SHA f0f44cbe62240979905fc3d064590bc897cee3e6ce0dde55e3ad7063b576a3fd.

Runtime implementation:

```python
_weak_floor = max(OUTPUT_MIN_EDGE_PROB, FORK_PROTECTED_EP_MIN_EDGE_PROB)
_pre_out_degree = {}
for edge in edges:
    source = int(edge["source_id"])
    _pre_out_degree[source] = _pre_out_degree.get(source, 0) + 1
_protected_sources = {s for s, degree in _pre_out_degree.items() if degree == 2}
# finite learned prob below floor is dropped unless its source is protected
# protected pairs are counted before filtering and asserted all retained afterward
assert stats["fork_protection_complete"] == 1
```

Fail-closed runtime gates:

- Explicit cache path is the exp065 kernel output validator cache.
- Old preset discovery is disabled; runtime receipt asserts no preset loaded.
- Exact stems are asserted as 44b6_12dfb391, 44b6_267148e4,
  44b6_2a2eff9f, 44b6_341df25f, 6bba_062c8d37, 6bba_07e24132,
  6bba_085bf656, 6bba_09961292; exactly four per prefix.
- `_v7_val_pred_cache_hit` is asserted true before the inherited inference block;
  cache miss terminates rather than falling back.
- A daemon watchdog calls `os._exit(124)` at 3540 seconds from cell zero.
- Fast tier is exactly `("fork_protected_ep015",)`; evaluated configs are asserted
  exactly `["base", "fork_protected_ep015"]`.
- Flat floor is asserted zero, candidate fork floor 0.15, selection margin is 99,
  selected label must remain base, confirmatory status is derived from evaluated
  configs, and leaderboard authorization is false.
- Every sample reports node/edge/fork counts and expected/retained protected edges.
- Smoke executed the extracted real filter: weak fork daughter retained, strong
  fork daughter retained, weak non-fork edge removed, probability-free edge kept.

Immutable adjudicator enforces: 8 exact stems and schemas; <=3/36 negative draws;
worst movie >=-0.002; intervention nonvoid on >=4 movies; every base-underpredicted
movie must be structurally void under the frozen label-free policy; prefix adjusted
edge delta >=-0.0005; division TP not down/FN not up; every prefilter fork edge
retained; every leave-one-movie-out proxy delta >=+0.0015; positive delta when the
44b6 prefix is omitted. It writes one sealed PASS/FAIL receipt. Any failure stops.

Budget: user explicitly reopened admission and authorized one Kaggle diagnostic
push after prior NO_CONSENSUS. New evidence is the recovered immutable raw cache
and exact eight GT graphs, making this fork-specific rather than a flat-floor retry.
Cap 1.0 GPU hour with the 3540-second kill; ledger has 27.6068 h and no reservation.
Zero LB submissions; no retry; exp064 remains baseline.

Prior reviewer confirmed the fork implementation, pre-filter semantics, telemetry,
strategy hashes, and notebook hashes. Its remaining findings were cache fallback,
budget enforcement, split sealing, adjudicator snapshotting, and authorization
reconciliation; all are addressed above. The last standard review could not read
files because its shell failed during setup, so this packet supplies the evidence.
