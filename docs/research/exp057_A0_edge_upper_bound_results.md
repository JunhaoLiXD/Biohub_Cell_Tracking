# A0 Part 1 — Edge/detection/node upper-bound audit (results)

Zero-GPU, 2026-09-16. Script: `docs/research/scripts/a0_edge_upper_bound_audit.py`
(scorer reconstruction validated **exactly** against val_049
`primary_metric = 0.9310696298996892`, match=True). Data: val_049 (exact 0.944
lineage) `validator_results.csv`.

**All Δ below are OPTIMISTIC ceilings on the 16-video train16 proxy** — perfect
correction, zero collateral. They are NOT achievable gains and NOT Public LB gains.
Purpose: rank levers / measure headroom.

## Baseline decomposition (0.944 lineage, train16)

* Score 0.931070 = adj_edge 0.916070 + 0.1·div_jaccard(0.15).
* Edge TP/FP/FN = 9137 / 481 / **437**; scored union 10,055 edges.
* **FN decomposes exactly:** 271 fragmentation + 166 detection-loss = 437.
* Wrong-association edges = **8** (a subset of FP). Division 3/8/9.
* Spurious predicted nodes = 394,812; node ratio is **negative** (under-prediction).

## Ceilings, ranked

| Lever | Δscore ceiling | Addressable by | Note |
| --- | --- | --- | --- |
| Division perfect (12/0/0) | **+0.085** | division model | fantasy ceiling |
| Division FP→0 + ½ FN recovered (8/0/4) | **+0.052** | division model | hard (mis-localized) |
| Fix ALL edge FN (frag+lost) | +0.045 | mixed | includes detection |
| **Fragmentation (271 edges)** | **+0.027** | **post-processing / relink** | biggest *edge* lever |
| Detection-loss (166 edges) | +0.017 | **detector** (not post-proc) | needs model change |
| Division remove all FP (3/0/9) | +0.010 | division gate | |
| **Wrong-association (8 edges)** | **+0.0015** | association/relink | small |
| Perfect node count (ratio→0) | **−0.007** | — | **HURTS** (see below) |

## What this establishes

1. **The edge layer is NOT exhausted (I was wrong; Codex was right to force this).**
   Fragmentation alone has a +0.027 proxy ceiling.
2. **But the biggest edge lever already failed to transfer.** Fragmentation
   reconnection is exactly what exp_055's post-smoothing joint repair targeted —
   and exp_055 scored LB 0.942 == 0.942 (Δ0). So proxy headroom in fragmentation
   has a *demonstrated* transfer failure; it is not a fresh opportunity.
3. **Wrong-association (Codex's highlighted "causally specific" class) is real but
   small:** +0.0015 ceiling. Above LB rounding in principle, but an optimistic
   train-proxy ceiling on only 8 edges — not a compelling standalone bet.
4. **Node pruning is counterproductive.** The scorer's node-count adjustment
   *rewards under-prediction* (negative ratio boosts adj_edge). Forcing perfect node
   count costs −0.007. So the 394,812 "spurious" nodes are NOT a prune-for-points
   lever — the opposite. (Corrects a direction Codex asked to check.)
5. **Division still holds the most headroom** (+0.05 to +0.085) but remains the
   hardest to both localize and validate.

## Honest boundary of A0 that is doable locally

A0 Part 1 (this) is fully local. **A0 Parts 2–3 (exact-0.944-lineage division
candidate pre-filter audit + scorer-aware fork audit) require the GT graphs**, which
live on the Kaggle scorer side and are NOT in local artifacts (val_049 shipped only
the production submission, not a diagnostic export). Doing Parts 2–3 on the exact
0.944 lineage therefore needs a **minimal GPU diagnostic export** (~0.4–1 GPU hr, in
the style of exp_057), not zero-GPU. The only local division-candidate data is the
0.941/0.942 diag exports, which have `safe_div_veto=false` and the pseudo-replication
problem — not a substitute.

## Bottom line for the strategy

The A0 Part-1 evidence **weakens the case for a cheap edge win** (the one big edge
lever already failed to transfer; the specific small one is +0.0015; pruning hurts)
and **leaves division as the only large-headroom lever**, consistent with the
original diagnostic's direction — but now on corrected, exact-lineage, scorer-faithful
footing rather than the withdrawn claims. Whether division is *reachable/measurable*
is the A0 Part 2–3 + A1 question, and Parts 2–3 need a small GPU diagnostic export
decision from the user.
