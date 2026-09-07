I have everything needed. All artifact dependencies are verified present in a single `diag_019` output root, the guards are strong, and the change is one-variable. Here is the review.

---

# Independent Review â€” `diag_023_train16_same_run_final_graph_oracle_reviewed`

## Summary
A CPU-only, zero-GPU counterfactual **oracle ceiling** audit for v9 Phase 0. It reconstructs the frozen `diag_019` post-filter validation graphs, applies GT-informed division edits over cumulative families **A / A+B / A+B+C** constrained to real pre-ILP candidate edges, and rescores with the pack's official metric per specimen. It is explicitly an upper bound (`reproducible: false`, `methodology_valid: true`), not a promotable result. The single change vs its failure-parent `diag_021` is `artifact_execution_identity_only`: candidate, pre-ILP source coordinates, and final graphs now **all come from one `diag_019` run** rather than mixing `diag_014` candidates with independently-executed graphs â€” the exact node-id-space defect that produced the broken `diag_018` (0.0629) and the `diag_021` sourcecoords failure. I verified the parent output on disk contains all three artifact families for the 16 validation datasets (`final_validation_graphs/`, `preilp_edge_audit/`, `tracking_repo/predictions/unknown/unet_transformer_val/split_0/*.geff`), with `diag_019` metrics recording hashes-match and stage-exact for each.

## Methodology
1. **Testable, one variable â€” yes.** Pure offline analysis; the only variable is artifact execution identity. The hypothesis (positive per-specimen A/B/C headroom under the same-run constraint) is falsifiable against the official scorer.
2. **Validation trustworthy â€” yes, with the expected oracle caveat.** Per-specimen 44b6/6bba reported separately; gate is the *minimum* specimen ABC Î”score (min-specimen), matching `GOAL.md`. The audit is GT-informed *by construction* â€” that is the point of an oracle ceiling, not leakage in the promotion sense; train-derived optimism is flagged and decisions use deltas + cross-specimen consistency. The `baseline_reproduced` guard (aggregate adj & div_J vs `diag_019` `specimen_metrics` to `abs_tol=1e-10`) is a genuine effective-configuration check, not prose trust: a faithless reconstruction fails the gate. `gt_to_pred` is built from bipartite `MATCHED_NODE_ID` (injective), so the id space is consistent and the two-daughters-to-one-pred crash path is unreachable.
3. **Candidate-reachability is honest.** Edits only count if their add-edge exists in the pre-ILP top-4/12Âµm export (`candidate_covered`), and `_load_relevant_candidates` re-derives `distance_um`/`t_src`/`t_tgt` from the same-run prediction coords and **raises** on any mismatch â€” a fail-safe same-run identity check, exactly what `diag_021` lacked. Empty-overlap and zero-relevant-candidate cases raise rather than silently reporting "no headroom."
4. **Not duplicate / not contradicted.** `exp_001` measured the *unconstrained* oracle (family A â‰ˆ +0.06 both specimens); this measures the tighter *candidate-reachable* ceiling that actually gates Phase 1. The `diag_018/020/021/022` predecessors failed on plumbing (infra, not hypothesis) â€” per research rules those are not evidence against the hypothesis.

## Implementation risks
- **Gate keys on ABC only.** `gate_passed = baseline_reproduced and abc_positive_both`; `a_positive_both` is computed but excluded. ABC contains edge *removals* ("steal child", "remove wrong child") â€” the Version-7 `adj` landmine that only bites on dense hidden GT. This is within the plan's "OR A+B/C lifts materially" branch and all per-family deltas are reported, so it is defensible for a ceiling audit â€” but the automated PASS can green-light the risky families while low-risk A is negative. Treat the A-vs-ABC decomposition as a mandatory human read before any Phase 1 commitment, not just the boolean.
- **Stale env-cell comment** says "this audit runs with internet ON" while `config.kaggle.enable_internet: false`. The offline wheel path (`--no-index --find-links`) is tried first and the same stack ran under `diag_019`, so it is functional; reconcile the comment to avoid a false expectation.
- **Output contract.** Payload writes nested `metrics.oracle_gate_passed` and the final assert cell checks the nested path; `config.evaluation.gate_field: oracle_gate_passed`. Confirm the controller resolves the gate field nested (as it parsed `diag_019`'s nested `metrics`), not at top level. Top-level `primary_metric` (min specimen ABC Î”score) and `specimen_metrics[*].primary_metric` are present and consistent with the config.
- **Doc drift (non-blocking):** `GOAL.md` still narrates work "paused at the `diag_014` boundary," but `results.json` shows `diag_019` already KEEP and the oracle lineage past it; the narrative lags reality but does not affect this experiment.

## Budget
Tier 1, `expected_gpu_hours: 0.0`, `enable_gpu: false`. Cost is one short Kaggle CPU session reusing attached `diag_019` kernel output plus this review. GPU budget (17.69 h remaining, 6 h reserve) is untouched. Information gain is high: it produces the mandatory GATE-0 candidate-reachable ceiling per specimen that decides whether *any* Phase 1 training is admissible. Clearly worth it.

## Required changes
None block local smoke testing. Before launch, confirm:
1. Local smoke test `scripts/validate_phase0_oracle_notebook.py` passes (guards against the `exp_010`-class unassigned-config error).
2. Controller resolves `gate_field: oracle_gate_passed` at `metrics.oracle_gate_passed`.
3. Reconcile the env-cell "internet ON" comment with `enable_internet: false`.
Recommended (methodology, not code-blocking): when reading results, gate the Phase-1 go/no-go on **family A** per-specimen sign and the Aâ†’ABC dependency, not the ABC-only boolean.

## Recommendation
Sound, low-risk, correctly single-variable, on the sanctioned v9 Phase-0 path, with strong same-run identity and baseline-reproduction guards, and all parent artifacts verified present. It corrects a known-broken lineage rather than repeating it. Safe to enter local smoke testing; PASS is not a prediction that A/B/C will clear the gate.

VERDICT: PASS
