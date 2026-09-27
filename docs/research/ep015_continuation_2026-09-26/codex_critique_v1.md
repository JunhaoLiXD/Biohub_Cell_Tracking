# Codex independent strategy critique v1

2026-09-27 UTC (September 26 America/New_York). Status: REVISE, not CONSENSUS.

Source inspected independently: builder, archived vehicle weak-edge function and call
order, own exp065 CSV, cx03 runtime report, parent scorer, controller snapshot and
metrics contract, existing exp067 export watchdog.

1. Eight movies across two prefixes, not two movies. This is our collected exp065
   table; it numerically reproduces the harvested table where comparable. Equal
   aggregate score columns are not bit-identical output graphs; config, seconds,
   overrides differ. No evidence of quantized probability mass follows.
2. Correct runtime anchors: exp064 932.2 s = 0.258944 h; cx03 1116.4 s = 0.310111 h.
   The 1.727 h figure belongs to an older run, not exp064. Expected ep015 ~0.5 h.
3. Polling conflicts with the user's standing no-poll rule. Replace the proposed
   attended polling watchdog with the already used psutil/thread watchdog, 5400 s
   after first code-cell execution, killing descendants and exiting. Reserve 2 h
   including startup margin; platform startup time remains outside that timer.
   Same timeout on visible and hidden runs; accept failure if hidden work exceeds it,
   with no retry. Do not change algorithmic repair deadlines. Document infrastructure
   additions separately from the one scientific lever and bind them to the diff.
4. Checkpoint/vehicle identity and effective globals must be asserted, not only echoed.
   Add an assert-only guard immediately before the base write_test_submission call,
   and an additive final metrics.json controller contract with actual elapsed time,
   output hash, effective config, pruning counters and no-degradation checks. These
   additions must not modify predictions. Build in scratchpad, then controller creates
   the immutable experiment snapshot; do not pre-create its experiment directory.
5. Snapshot precedes admission review, which reviews that immutable source. Then smoke
   and controller launch. Include wrapper/contract/check scripts as snapshot extras.
   No new deployment adapter; notebook still performs the same full inference path.
6. Pruning also removes internal orphan nodes, is followed by existing short-track
   filtering and linefit smoothing, and can change division scores. Only the existing
   local table's division counts are unchanged; no universal division preservation.
7. Exact current metrics checks and local graph/provenance audit precede the ONE
   already authorized submission. No additional authorization request unless the
   accepted scope changes. No final re-selection; conservative three/day cap.
8. The Q1 HEADROOM script correctly converts node IDs to rows; the WHY script still
   misindexes candidates. Independently rederive deficits anyway and assert agreement
   with Q1; do not silently conflate their evidence. Removing conflicting edges may
   delete a true or a false edge; report which, without assuming either outcome.
9. CPU edits: build the union of requested true edges, remove conflicting incoming
   edges and every nonrequested outgoing edge of edited mothers (the two daughters
   exhaust out-degree two). Reject any selected-set conflict. Do not rely on edit
   order. No-op must reproduce full per-movie scalar metrics, not only division counts.
   Cache per-movie scores, enumerate all <=128 global subsets and call the existing
   aggregate scorer for exact weight changes; local greedy maxima are not equivalent.
10. Any display >=0.954 is an exploratory public gain only; retained 0.953 remains
    final. Result at 0.953 is a registered null, not precise equality.

No code or experiment has been built yet. Request one bounded revision responding
to these concrete issues; no retry of a timeout/quota stop.
