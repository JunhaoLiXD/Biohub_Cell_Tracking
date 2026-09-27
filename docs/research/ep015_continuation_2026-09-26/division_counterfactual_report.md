# Restricted division counterfactual - completed CPU diagnostic

2026-09-27 UTC. No GPU, TEST predictions, learned policy or leaderboard submission.
Protocol: accepted Part B of strategy_consensus_v1.md. Script:
`scripts/diagnose_division_counterfactual.py`; raw results: `division_counterfactual.json`.

The no-op path reproduces all overlapping scalar fields of the collected eight-movie
validator table to absolute tolerance 1e-12 and division counts exactly. Seven direct-edge
deficits were independently re-derived and matched against corrected Q1. Every graph
preserves nodes/coordinates, forward adjacency, in-degree <=1 and out-degree <=2.
All 128 global subsets were enumerated, with exact parent aggregation and varying weights.
Original input hashes were checked again at completion; no prediction file was written.

| Counterfactual | TP / FP / FN | Adjusted edge Jaccard | Parent proxy |
|---|---|---|---|
| No changes | 3 / 2 / 9 | 0.9340604299821533 | 0.9554890014107248 |
| All seven direct-edge repairs (best) | 9 / 2 / 3 | 0.9360169675933591 | 1.0003026818790735 |

Best delta = +0.04481368046834866 in the local parent proxy. The worst aggregate
case is no-op (delta zero); inspect all per-prefix scores and edge removals in the raw
receipt rather than interpreting that as a risk-free deployable change. Seven direct
repairs recover six additional scorer TPs because one triple already had component credit.
The proxy is adjusted_edge + 0.1 * division, so it can exceed one; **1.0003 is not an LB
score, an accuracy claim, a forecast or an achievement of the user's +0.001 objective**.

This is attainable only under a restricted GT-assisted edit family. It does not constrain
edits to actual generated events or test learned discrimination. It is neither a global
upper bound nor a selection rule, and it does not justify a fresh training run by itself.
The next scientific question, if separately authorized, is whether a frozen GT-blind rule
can identify useful asymmetric candidates without admitting excessive false divisions.
Only five complete training positives and four holdout positives remain available in this
export; the historical eight movies have already been inspected and are not fresh holdout.

ep015 remains a separate fixed probe. Its choice and runtime policy do not use this
diagnostic, and no GT-dependent edit is ported into its notebook.
