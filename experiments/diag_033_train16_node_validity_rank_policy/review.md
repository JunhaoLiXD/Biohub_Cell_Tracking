Review complete. Findings below.

# Independent Review â€” diag_033_train16_node_validity_rank_policy

## Summary

diag_033 is the logical, well-attributed successor to diag_032. The parent recovered the full Family-A oracle **in-sample** (44b6 `+0.005664`, 6bba `+0.011380`) but transferred **zero** held-out metric effect because every held-out top-ranked action had unmatched endpoints (`selected_both_endpoints_matched: 0`, `test_delta_score: 0.0` in both directions). diag_033 attacks exactly that bottleneck: it swaps the sparse candidate-**pair** validity classifier (0â€“6 positives per video in the parent audit) for **separate source-node and target-node validity models learned from every frozen prediction node** (hundredsâ€“1300 positives/video). Action score becomes `P(source valid)Â·P(target valid)Â·P(division edge)`; the division model and the training-optimal action-count transfer are held identical to diag_032. Zero GPU. It is the designated gate before committing the Phase 2 GPU budget.

## Methodology

- **One variable** (`endpoint_validity_learning_unit_only`): division model and rank/count-transfer unchanged vs diag_032 â€” clean and attributable.
- **Leakage / domain split:** leave-one-specimen-out; `_fit_model` masks to `train_specimen` before fitting (no cross-specimen model leakage); action count chosen on the *train* specimen and applied to held-out (no held-out peeking).
- **GT is label/diagnostic only:** node-validity target = `int(node_id in pred_to_gt)`; `both_endpoints_matched` feeds only diagnostics. Model features are all structural/inference-available; runtime flags (`feature_contract_valid`, `gt_matching_is_not_a_model_feature`) assert this and are checked in the contract cell.
- **Gate is correctly strict:** `passed = baseline_reproduced AND (test_delta_score > 0 AND test_delta_adjusted_edge_jaccard >= 0)` for **both** directions. The `adj >= 0` clause directly guards the v9-plan non-orthogonality / Version-7 edge-FP risk; `baseline_reproduced` compares the runtime aggregate to the parent's frozen per-specimen metrics with `abs_tol` â€” a genuine effective-config check, not stale prose.
- **Acceptable caveat:** frozen extractors saw these train videos â†’ absolute scores and the node-validity AUC are optimistic; the gate uses deltas + cross-specimen, per GOAL.md.

## Implementation risks

- **Low â€” unguarded diagnostics:** held-out `roc_auc_score`/`average_precision_score` aren't guarded for a single-class specimen and would abort the gate if it ever occurred (practically impossible at thousands of nodes). Non-blocking.
- **No stale-execution hazard:** one `execute` cell + one `contract` cell; diag_025â€“032 functions are defined-but-not-run, so `metrics.json` is written once.
- **Contract complete:** `experiment_id`, `primary_metric` (min held-out delta), `specimen_metrics` for both specimens, gate_field `node_validity_policy_gate_passed` (matches config). Smoke validator checks all required markers, which are present. Held-out `selected_both_endpoints_matched`/`selected_true_division_edges` are carried in `test_policy`, keeping a zero-delta result interpretable.
- **Deeper (not a bug):** the held-out oracle has only ~1â€“2 beneficial actions among ~29k candidates. Denser validity supervision improves endpoint ranking but doesn't change that target sparsity, so success probability is modest even though the hypothesis is sound.

## Budget

Zero GPU (`enable_gpu: false`, tier-1); weekly 17.69h and 6h reserve unaffected. Parent ran ~224s on CPU. Cost is one CPU slot + this review; information gain (does node-level supervision break the endpoint-validity transfer bottleneck before Phase 2 GPU spend) is high relative to ~zero cost.

## Required changes

None blocking. Optional: wrap the two held-out ranking diagnostics (`roc_auc_score`/`average_precision_score`) so a single-class specimen can't abort an otherwise-valid gate.

## Recommendation

Proceed to the next controller stage (local smoke test â†’ CPU launch). Testable single-variable hypothesis, leakage-safe protocol, correctly strict per-specimen + adj-guard gate, complete metrics contract, and parent evidence that directly justifies the change. PASS on methodology/safety â€” not a prediction the gate will pass.

VERDICT: PASS
