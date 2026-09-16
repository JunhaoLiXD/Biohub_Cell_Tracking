## Summary

v2 improves the proposal substantially and resolves the fork-protection contradiction and LB go-gate. It is still not consensus-ready: the division objective remains undefined, the candidate family remains ambiguous, and the MILP formulation does not yet guarantee valid atomic forks, deterministic equivalence, or Kaggle deployability.

## Per-item resolution

1. **Partially resolved.** Post-pruning, existing-node-only generation is provenance-safe. However, eligibility remains ambiguous: zero-child versus one-child parents, occupied daughter targets, permitted removals, mutual-NN/divergence predicates, frame/global caps, and DeepCenter evaluation across both daughters are not precisely specified.

2. **Not resolved.** §9.2 does not provide a mathematical objective. The geometric term, coefficient, combination with the two `utility()` values, numeric `division_edit_penalty`, and treatment of unavailable cache rows are deferred to a future contract. Calling the existing DeepCenter threshold a “physical feasibility” veto does not define or justify it.

3. **Partially resolved.** Set-packing/MILP is the correct solver class, but the formulation permits two independent single-edge variables from one source, creating a non-atomic fork. It also lacks explicit residual-capacity constraints around fixed edges, complete retention/removal objective terms, an exact tie-breaking construction, and a credible proof of LSAP equivalence.

4. **Resolved.** Existing two-out forks remain immutable and excluded. This removes the original contradiction without weakening their protection.

5. **Partially resolved.** The four arms and combined-versus-edge-only primary contrast are correct. The division-only arm must explicitly prohibit ordinary edge repair except any preregistered edge displacement intrinsic to a division move. Section 10 also incorrectly schedules the factorial before implementation and consensus.

6. **Partially resolved.** Most requested gates and receipts were added, but:

   - §5 still contains the false `division_jaccard > 0.2, i.e. FP+FN < 16` equivalence, contradicting §9.6.
   - The `−0.0005` adjusted-edge allowance contradicts §3’s “without regressing adjusted-edge” hypothesis.
   - Per-specimen countwise non-inferiority needs its exact TP/FP/FN inequalities.
   - The manifest should explicitly bind the pre-solver node/edge graph, solver source and complete dependency binaries/environment, scorer, and final submission—not only the listed intermediate artifacts.

7. **Resolved.** The pending exp_055 LB score remains a hard gate requiring a score strictly above 0.942.

8. **Partially resolved.** §9.9 preserves the restrictions declaratively, but §10 places implementation-dependent factorial execution before consensus and implementation, contrary to the project review contract.

## New risks

- exp_055 bundled only `_lsap`; it did not ship an importable SciPy installation. The cached full wheel contains MILP/HiGHS components, but v2 has no packaging, shared-library, hash, or clean-Kaggle import plan.
- MILP tie-breaking is only asserted. Canonical input ordering does not make multiple optimal solutions deterministic. Use a formally defined lexicographic/integerized objective or equivalent second-stage solve.
- Exact division-disabled parity should dispatch to the existing LSAP path; solving an equivalent floating MILP does not guarantee identical assignments or action decomposition.
- Per-frame candidate counts could make exact branch-and-bound expensive. Preregister candidate/variable limits, worst-frame scale, optimal-status requirements, timeouts, and fail-closed behavior.

## Remaining required changes

1. Freeze the exact candidate family, occupancy/removal rules, all numerical feasibility predicates, and DeepCenter aggregation rule.
2. State the complete numerical objective as an equation, including every coefficient and penalty.
3. Formalize binary variables and constraints so only a triple can create two outgoing edges and fixed-edge capacities are respected.
4. Define deterministic tie resolution, MILP optimality tolerances, full-wheel deployment, and bounded scaling tests.
5. Use the existing LSAP path when division is disabled and require byte-identical outputs and actions.
6. Correct §5, reconcile the edge gate with §3, complete the manifest, and reorder §10 to consensus → implementation/review → factorial/smoke → admission.

## Recommendation

Revise the design document once more. The research direction remains viable, but implementation and execution should remain blocked independently of the pending LB gate.

VERDICT: REVISE
