# Tier C strategy packet: protected adaptive pruning

## Decision context

- Retained parent: exp064, Public LB 0.953, submission 56535761.
- exp066: the same compatible base plus count-excess pruning `cx03`; the lever
  removed 988 nodes and 1,242 edges and returned 0.953 (valid null).
- exp071: the same compatible base plus global `OUTPUT_MIN_EDGE_PROB=0.15`;
  authenticated Public LB 0.950. The transport repair was source-bound and the
  scored output was byte-identical to exp068, so this is a valid -0.003 result.
- exp071 removed 4,163 weak edges, 5,472 nodes and 7,335 final edges; structural
  forks fell 62 to 47. No fallback or degradation occurred.
- Prior eight-movie held-out evidence for flat ep015 estimated +0.00236
  test-reweighted adjusted edge but was heterogeneous: 44b6 prefix about -0.0085,
  and 10/36 two-per-prefix test-shaped draws were negative. The LB result proves
  this average did not transfer.
- Pre-registered rule was applied: revert, retain exp064, close global
  ep010/ep015/ep020. Do not run ep_cx (negative lever plus null lever).
- Competition deadline: 2026-09-29 23:59 New York. GPU ledger records about
  27.607 h remaining, but time/evidence quality and LB overfitting are binding.

## Proposed new direction

This is Tier C because it changes graph pruning eligibility and adds adaptive
behavior. It is not an ep threshold retry.

Hypothesis: low-confidence edges sometimes belong to false-positive fragments,
but a global floor destroys true lineage/division structure. Precision benefit
may survive only when pruning is disabled for under-predicted cases and division
topology is protected.

Stage 0 is zero GPU and uses exp064 plus existing held-out TRAIN artifacts:

1. `fork_protected_ep015`: apply floor 0.15 except to both outgoing edges of every
   pre-pruning out-degree-two source.
2. `lineage_protected_ep015`: additionally protect one or two frames around each
   fork, with radius frozen before aggregate results are read.
3. `adaptive_protected_ep`: activate protected pruning only from a pre-registered
   label-free density signal such as node density, edge/node ratio or isolated
   short-track fraction. It may not use movie identity, prefix, ground truth,
   hidden-test statistics or Public LB.

Required evaluation: official held-out scorer; aggregate, both prefixes, all
movies, division TP/FP/FN, node/edge/fork deltas and all 36 test-shaped draws.
Controls: exp064, exp066/cx03 and flat ep015. Threshold/radius selection must be
frozen before candidate aggregates are read or use nested leave-one-movie-out;
selection and evaluation on the same eight movies is forbidden.

At most one candidate advances only if all pass:

- pooled proxy >= exp064 +0.0015;
- each prefix adjusted-edge delta >= -0.0005;
- division TP does not fall and FN does not rise;
- no loss of forks receiving official division credit;
- negative test-shaped draws <=3/36 (flat ep015: 10/36);
- worst movie delta >= -0.002;
- non-void on >=4/8 movies and bypasses known under-predicted cases using only
  the frozen label-free rule;
- deterministic leakage, rollback, output-contract and graph tests pass.

Any failed gate closes the direction with zero GPU and zero submissions. Passing
Stage 0 permits only a compact implementation card and independent admission
review, not launch. Later launch/submission needs explicit user authorization,
immutable snapshot, smoke PASS, budget reservation, source binding and live
submission-history checks. Realistic target is displayed +0.001. If Stage 0
does not yield a robust candidate, freeze exp064 and stop accuracy work.

## Review request

Act as Tier C strategy author. Decide whether this is scientifically justified,
scorer-aligned, sufficiently protected against eight-movie overfitting, and
feasible before the deadline. Identify exact required refinements. End exactly
with `VERDICT: CONSENSUS`, `VERDICT: REVISE`, or `VERDICT: NO_CONSENSUS`.
