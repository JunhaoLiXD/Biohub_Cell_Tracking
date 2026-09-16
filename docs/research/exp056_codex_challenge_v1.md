## Summary

The direction is promising, but v1 is not implementation-ready. The principal defects are an undefined division objective, an unstated hyperedge-solver reformulation, contradictory division-protection semantics, and incomplete causal/integrity controls. Execution should wait for exp_055’s pending Public LB result.

## Methodology

The stacked arm can be the primary experiment if the hypothesis is explicitly incremental: “adding division variables to an otherwise byte-identical exp_055 policy improves division quality.” Combined-versus-exp_055 is then a valid single-change contrast.

The division-only arm should not replace it as primary, because that answers a different question: whether division repair works without edge repair. It should instead be a mandatory zero-GPU factorial control:

- repro_041: neither repair
- exp_055: edge repair only
- division-only on repro_041
- combined edge-plus-division repair

This separates the division main effect from interaction with exp_055. The revised solver must also reproduce exp_055 byte-for-byte with division moves disabled.

The exact move family is currently unclear: one existing child plus one orphan, two replacement daughters, deletion of existing forks, or some combination. Define it explicitly and freeze it before GT scoring.

## Leakage & provenance

Prediction-only operation is possible: pair probabilities, geometry, raw imagery, and frozen DeepCenter outputs do not inherently introduce GT, specimen, or video-identity dependence. However, v1 has not established the claimed inputs:

- The current cache loader contains pairwise edge probabilities and thresholds, not an identified division-event probability.
- DeepCenter supplies candidate-center confidence, not a calibrated parent→two-daughter probability.
- “DeepCenter as feasibility only” is undefined and conflicts with using a learned score threshold as accept/reject.
- Candidate generation currently occurs before pruning, while joint repair runs after pruning; rejected/orphan daughter nodes may no longer exist at solver time.

The revision must name every triple feature, its source artifact, exact score formula, threshold/penalty, and stage. Freeze these before examining exp_056 GT metrics. No specimen/video branching is permissible.

Input/output graph hashes are necessary but insufficient. Bind hashes for the candidate triples, pair-score caches, DeepCenter scores or their deterministic inputs, parameters, solver artifact, ordered actions, and final graph. Preserve node IDs and coordinates; do not resurrect or reuse removed IDs without an explicit provenance-safe design.

## Numerical/constraints

The existing SciPy 1.18.1 solver is a one-to-one Hungarian assignment. A two-daughter event is a hyperedge/set-packing decision and cannot simply be added to its assignment matrix while enforcing shared-daughter and single-edge conflicts. Moreover, exp_055 bundles only the `_lsap` implementation, not a general MILP solver.

The proposal must specify the actual optimization formulation and deployment dependency. It must enforce:

- Atomic selection of both daughter edges
- At most two outgoing edges and one incoming edge
- Conflicts between triples and ordinary edges
- Protected-edge and protected-fork invariants
- Next-frame constraints and all retained geometric/cap rules
- Canonical daughter ordering and deterministic tie resolution

Required tests include brute-force optimality on small graphs, permutation invariance, exact/near ties, extreme probabilities, overlapping triples, triple-versus-single conflicts, no partial triples, protected forks, caps, repeated clean-namespace runs, and exact division-disabled exp_055 parity.

## Gates

The stated equation is wrong: `division_jaccard > 0.2` is not equivalent to `FP+FN < 16` when TP can change. Define whether both are required or whether any strict Jaccard improvement with `TP >= 4` is acceptable.

Also add:

- Explicit aggregate primary-score improvement over exp_055, not merely division improvement plus tolerated edge loss
- Exact definition of the per-specimen delta—primary, adjusted-edge, or division
- Per-specimen division non-inferiority, preferably countwise as in local_052
- A worst-video adjusted-edge regression bound
- Division-disabled byte-identical exp_055 output/action parity
- Candidate-triple and objective-input hash checks
- Exact final TP/FP/FN arithmetic and action-to-output reconciliation
- Checks that the new move is exercised on both specimens and on test inference
- Deterministic solver status, optimality/tolerance, and repeatability receipts

There is also a contradiction to resolve: preserving every existing fork prevents re-rejecting current division events. Either declare an add-only protected-fork method or precisely define which forks can change. Do not weaken the existing division-protection contract silently.

## Proxy-vs-LB decision

Block exp_056 execution until submission 56261282 is scored and recorded. The train16 models saw these videos, the apparent gain is large and specimen-skewed, and the pending LB result is cheap, directly relevant evidence about the structural vehicle being extended.

Proceed only if exp_055 is strictly above the displayed 0.942 baseline under the preregistered interpretation. A flat or negative result requires a revised strategy—potentially making division-only the primary branch—not post-hoc continuation of the stacked design.

## Budget

One bounded 2.0-hour validation is justified after the LB go-gate, zero-GPU factorial evidence, consensus, fresh code review, and smoke. It would leave approximately 24.9 tracked hours and preserve the six-hour reserve. Verify the model-allowance reserve before the fresh review.

No leaderboard submission is authorized for exp_056, and KEEP must not imply promotion.

## Required changes before implementation

1. Specify the exact division candidate family, stage, feasibility predicates, and whether existing forks are immutable.
2. Define the division-event evidence and complete fixed objective mathematically.
3. Replace the unsupported “same solver” claim with a concrete deterministic hyperedge optimization design and pinned dependencies.
4. Make division-disabled execution exactly reproduce exp_055.
5. Add the four-arm zero-GPU factorial analysis, with the combined arm remaining primary only for the incremental hypothesis.
6. Correct and strengthen the gates and integrity manifests described above.
7. Retain the exp_055 LB result as a hard execution go-gate.
8. Preserve every leakage, provenance, hash, budget, submission, review, and promotion restriction; none may be relaxed.

VERDICT: REVISE
