## Summary

v3 resolves several major architectural issues—especially HiGHS deployment, atomic triple selection, and LSAP parity—but is not yet CONSENSUS-ready. The candidate family remains underspecified relative to the real safe-division topology, the B&B determinism/optimality claim is incomplete, fixed-edge capacity handling is asymmetric, and §10 still misorders admission review.

## Per-item resolution

1. **Partially resolved.** §11.1 defines pair-cache availability, next-frame daughters, DeepCenter aggregation across both daughters, occupancy, and removals. However:

   - `K_div` and `V_max` remain examples (“e.g. 64/24”), not frozen values.
   - Numerical geometry thresholds and precise predicates are referenced but not stated.
   - The real safe-division routine only considers a parent with exactly one existing child plus one currently unoccupied daughter. §11.1 instead appears to permit zero-child parents, two replacement daughters, and displacement of occupied edges.
   - The stage/coordinates are ambiguous: the existing predicates run before later pruning/smoothing, while exp_055 repair runs after smoothing.
   - “Protected as a single edge/target” is not defined against the actual edge-based `protected_edges()` result.

   Thus the exact candidate family is still not reproducible from the proposal alone. See [proposal §11.1](E:/Project/Biohub_CellTracking/docs/research/exp056_division_aware_joint_repair_proposal.md:285) and [current protection logic](E:/Project/Biohub_CellTracking/scripts/original_score_joint_repair.py:102).

2. **Resolved, with one required invariant.** §11.2 now supplies a complete equation and fixes both penalties at 0.25. The removal term does not inherently double-count: triple additions and removals are distinct, while `E(S)` is defined as single-edge moves only. Implementation must enforce that an implied triple edge cannot simultaneously appear in `E(S)`, and must define the canonical representation of `Objective(C)`. Under those invariants, the `D={}` difference matches the current gain calculation in [solve_policy](E:/Project/Biohub_CellTracking/scripts/original_score_joint_repair.py:178).

3. **Partially resolved.** The `x/y` formulation makes triples atomic and prevents two independent singles from producing a fork. Target-side `fixed_in(t)` is also directionally correct. Remaining gaps:

   - No symmetric `fixed_out(s)` accounting is formalized.
   - “Protected/out-of-pool” is not translated into an exact fixed-edge set.
   - Candidate eligibility does not clearly guarantee that a source with a retained fixed outgoing edge cannot receive a triple.
   - Conflict-component construction is not fully specified. The cited “existing slot-space component logic” is `difference_components()`, which decomposes an already selected edit difference; it is not a candidate-hypergraph decomposition routine.

4. **Partially resolved.** Pure-Python exact B&B removes MILP tolerances and deployment concerns, but determinism and bounded execution remain incomplete:

   - Ascending variable exploration does not prove that the first optimum is the lexicographically canonical optimum; inclusion/exclusion order and explicit full-key comparison are missing.
   - Float64 summation order, equality treatment, near-tie treatment, admissible bound, pruning rules, and optimal-status definition are unspecified.
   - No timeout/node limit or worst-case fail-closed rule is defined below `V_max`.
   - The proposed scale check only measures observed components; it does not test adversarial cap-sized components or establish a runtime bound.
   - The v1-required brute-force optimality, permutation, exact/near-tie, overlapping-triple, and triple-versus-single tests are not explicitly retained.

5. **Resolved.** §11.4 and §11.6 dispatch every no-triple/division-disabled case to the unchanged LSAP implementation and require byte-identical graphs and ordered actions on all 16 fixtures. This directly addresses equivalence risk rather than relying on an equivalent optimization formulation.

6. **Partially resolved.** The corrected score gates, exact per-specimen TP/FP/FN inequalities, and expanded manifest are adequate. Sequencing is not:

   - §10 places the “fresh Codex admission review” before factorial and snapshot-smoke evidence, although the required order was implementation/code review → factorial/smoke → admission review.
   - §9.8 says the LB gate blocks entry into implementation, while §10 places the LB gate after implementation and factorial. The authoritative order must be stated once and consistently.

## v2 new risks

- **(a) HiGHS/full-SciPy deployment — Resolved.** Triple-containing components use pure Python; the existing `_lsap` bundle remains the only compiled solver dependency.
- **(b) Tie-breaking determinism — Partially resolved.** The desired lexicographic result is defined, but the algorithm does not yet guarantee it.
- **(c) LSAP parity dispatch — Resolved.** Empty division sets explicitly execute unchanged `solve_policy()`.
- **(d) B&B scaling — Partially resolved.** Caps and fail-closed intent help, but their values are unfrozen and no cap-sized runtime/optimality test or timeout policy is specified.

## New defects

- The proposal’s generic two-daughter family does not match the actual one-existing-child-plus-orphan safe-division routine.
- “Reusing existing predicates” is insufficient because those predicates depend on topology, orphan occupancy, successors at `t+2`, mutual-nearest-orphan construction, exact coordinates, and multiple numerical caps.
- The claimed canonical-optimum proof from variable order is invalid without an explicit leaf comparator and pruning rules preserving all secondary objectives.
- Fixed incoming capacity is formalized, but fixed outgoing capacity is only implied through ambiguous eligibility wording.
- Fail-closed behavior must specify whether an oversized combined component falls back to unchanged edge-only LSAP or leaves the entire frame unchanged.
- Current tests cover exp_055 LSAP behavior and bootstrap only; the proposal does not yet bind the necessary division/B&B test matrix.

## Remaining required changes

1. Freeze the exact candidate topology, stage and coordinate state, all numerical thresholds, and exact `K_div`/`V_max` values.
2. Define protected/fixed source and target sets algebraically, including fixed outgoing capacity.
3. Specify candidate-hypergraph component construction and oversized-component fallback behavior.
4. Replace the variable-order determinism claim with an explicit full-key comparison, deterministic summation/equality policy, admissible bounds, and pruning rules.
5. Require brute-force-oracle, permutation, near-tie, conflict, atomicity, and adversarial cap-sized scaling tests with a bounded runtime/fail-closed rule.
6. Correct §10 to distinguish code review from final admission review and reconcile the LB gate’s position with §9.8.

## Recommendation

Revise once more before declaring strategy consensus. Implementation, factorial execution, admission, and launch remain blocked.

VERDICT: REVISE
