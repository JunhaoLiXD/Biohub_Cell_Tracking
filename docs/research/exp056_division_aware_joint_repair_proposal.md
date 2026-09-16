# Strategy Proposal — exp_056 Division-Aware Joint Lineage Repair

Record type: versioned strategy proposal (Valid-KEEP branch successor)
Status: **v3 authored; three Codex challenges, all VERDICT: REVISE** (v1 →
`exp056_codex_challenge_v1.md`, v2 → `_v2.md`, v3 → `_v3.md`). v3 resolved the
solver deployment (pure-Python B&B, no HiGHS), atomic-triple formulation, and
byte-exact LSAP-dispatch parity. **Still not CONSENSUS-ready:** v4 must align the
division candidate family to the ACTUAL runtime `safe_division` topology (one
existing child + one unoccupied orphan daughter with t+2 successors and
mutual-nearest-orphan construction — NOT a generic two-daughter family), freeze
`K_div`/`V_max` and all numerical predicates, formalize fixed-out(s) capacity and
candidate-hypergraph component construction with oversized-component fallback,
give an explicit B&B canonical-optimum comparator/pruning + deterministic
summation, bind the division/B&B test matrix, and finalize §10 ordering (code
review vs final admission review; LB-gate position vs §9.8). Writing v4 requires
studying the real `safe_division` implementation (runtime notebook +
`scripts/diag052_joint_policy.py`). Execution stays **hard-blocked** on (a) the
exp_055 Public LB (submission 56261282) > 0.942 and (b) a versioned `CONSENSUS`
plus a fresh Codex admission review of the implementation. Nothing is authorized
now.
**2026-09-15 GO-GATE FAILED — exp_056 HALTED.** The exp_055 Public LB
(submission 56261282) scored **0.942**, exactly equal to repro_041's 0.942 (zero
displayed-precision gain), while the frozen train16 proxy claimed +0.01485. The
proxy did not transfer. exp_056's hard go-gate required the exp_055 LB strictly
above 0.942, so it fails. This stacked division-aware repair is NOT justified to
launch: its structural parent (the edge repair) delivered no held-out LB gain.
exp_056 is halted pending user re-scope. The v1–v3 design and Codex challenges
remain valid engineering evidence for any future joint-repair work, but no
implementation, launch, or leaderboard submission is authorized.

Author: Claude Code. Date: 2026-09-15.
Posture: late-stage, deliberately **aggressive / framework-changing** (authorized
by the "Late-stage experimental posture" in `docs/research/PROJECT_HANDOFF.md`).

## 1. Why this, why now (the strategic bet)

Every train16 result on the learned 0.941 line has been stuck at
`division_jaccard = 0.2` with division TP/FP/FN = 4/8/8, and the error
decompositions repeatedly attribute most of the remaining loss to division, not
edges:

* `exp_050` TTA screen: "division explained most of the loss."
* `val_049`: "division explains 65.24% of the loss."
* `exp_055` (the just-audited KEEP): the original-score joint repair lifted
  adjusted-edge by +0.01485 but left division **completely unchanged** at 4/8/8.

So the biggest un-mined lever is division. The safe move (an exact reproduction
of exp_055) does not touch it. The aggressive, high-upside move is to take the
**one structural mechanism we have now proven transfers exactly** — the
protected joint cut-and-reconnect solver validated end-to-end in exp_055 (500
byte-identical actions per video, exact 16/16 parity) — and extend its objective
to also decide **division events**. This turns an edge-only repair into a joint
**lineage** repair inside a single objective, which is exactly the kind of
framework change the late-stage posture invites.

**Precondition / go-gate.** exp_055 leaderboard scoring (submission 56261282) is
PENDING. This proposal is *authored* now but its execution gate depends on that
result:
* If exp_055's Public LB improves over repro_041's 0.942, the joint-repair
  framework is a validated transfer vehicle and exp_056 proceeds as the primary
  bet.
* If exp_055's LB is flat/negative, the proxy over-credits the joint repair; the
  same over-fitting risk then applies to a division extension, and exp_056 must
  be re-scoped (see §7) before any launch. We do not launch exp_056 on proxy
  evidence alone.

## 2. Parent and lineage

* Behavior parent: `repro_041_public_0941_motion_ema` (LB 0.942, proxy 0.9387).
* Structural parent: the exp_055 original-score protected joint repair applied
  after smoothing (KEEP, proxy 0.9535, byte-exact vs `local_052`).
* exp_056 stacks **one** new structural variable on the exp_055 graph state:
  joint-optimized division events. Everything else (detector, association,
  motion EMA alpha 0.4, gap/relink, ILP selection, edge repair) is frozen
  identical to exp_055.

## 3. One falsifiable hypothesis

> Extending the protected joint cut-and-reconnect solver so it also proposes and
> scores parent→two-daughter **division events** under an original-score
> objective — moving the division accept/reject decision into the joint solver —
> **strictly raises `division_jaccard` above 0.2 with division TP >= 4**, and
> **raises the aggregate primary score above the exp_055 level without
> regressing adjusted-edge**, on the frozen train16 stratified proxy.
> (Note: `division_jaccard > 0.2` is NOT equivalent to `FP+FN < 16` once TP can
> move; the gate is the strict Jaccard improvement with the TP floor, see §5/§9.)

Falsifier: if `division_jaccard <= 0.2` OR adjusted-edge regresses beyond the
preregistered tolerance, the division-in-joint-objective hypothesis is rejected
and the branch closes (no parameter sweep to rescue it).

## 4. Exact change (scope-locked)

1. In the isolated joint solver (the same SciPy-1.18.1-pinned module validated in
   exp_055), add a **division move**: for a candidate parent node at frame *t*
   with two geometrically admissible successors at *t+1*, the solver may commit a
   protected (parent, daughterA, daughterB) triple as a single scored action,
   scored by the **original edge/division probabilities already in the graph**
   (no new learned model, no ground truth, no specimen/video identity).
2. The DeepCenter division gate's role changes from a hard geometric
   accept/reject to a **feasibility filter only** (it may still veto physically
   impossible triples); the accept/reject decision moves into the joint
   objective. DeepCenter checkpoint, epoch-2 `best.pt`, and all hashes stay
   frozen and identity-checked exactly as exp_055.
3. Division moves obey the existing conflict/fork/protection constraints: no node
   reused across incompatible triples, existing protected edges and
   fork-protected nodes preserved, node identity preserved through all stages.
4. Prediction-only provenance: the move set and scores derive solely from the
   frozen graph produced upstream; inference remains ground-truth-free.

Explicitly **out of scope** for exp_056: retraining any model, new learned
division features, the closed context-policy gate, EMA-alpha sweeps, and any
change to test-time detector/association settings.

## 5. Validation protocol, expected signal, gates

* Protocol: `public_0941_frozen_train16_stratified_proxy_v1` (same 16 stratified
  videos, same frozen scorer/selector as val_039/exp_055) so exp_056 is directly
  comparable to exp_055 and repro_041.
* Zero-GPU first: reproduce the division-aware policy on the 16 frozen local
  graphs and audit exact node/edge/division identity **before** any GPU launch,
  exactly as the `local_052 → exp_055` path did.
* Preregistered gates (compare mode, not just a boolean receipt) — see §11.7 for
  the corrected, binding version:
  * division: `division_jaccard` strictly `> 0.2` **and** div `TP >= 4` (the
    earlier "i.e. FP+FN < 16" equivalence was wrong once TP moves and is removed).
  * aggregate: primary score strictly `> exp_055` (0.9535869213120838).
  * adjusted-edge: `>= exp_055` (no edge regression, consistent with §3; the
    earlier −0.0005 allowance is withdrawn), plus a worst-video adjusted-edge
    bound `>= −0.002`.
  * per-specimen: primary and adjusted-edge deltas `>= −0.002`, and countwise
    division non-inferiority (per specimen, div FP and FN not worse than exp_055).
  * exact input/output graph hashes and the full integrity manifest of §11.7,
    submission SHA stable before/after validation, division moves receipted per
    video and reconciled to final TP/FP/FN.
* Expected signal: division is the dominant loss term, so even a modest FP
  reduction (e.g. 8→6) is a visible aggregate gain; the hypothesis is deliberately
  aimed at the point-rich region rather than another edge micro-gain.

## 6. Artifacts, budget, rollback/stop rule

* Artifacts: division-aware solver diff + isolated unit tests (clean-namespace
  bootstrap regression like exp_055), 16-graph parity fixtures, per-video
  division-move receipts, `metrics.json`, `submission.csv`, review + smoke logs.
* Budget: one bounded GPU validation, 2.0 GPU hours reserved from 26.9 tracked,
  six protected hours preserved, ≥10% per-model allowance kept. Zero-GPU parity
  work first at no GPU cost.
* Admission (mandatory before launch): `admission.require_codex_review: true`
  (`reviewer_provider: codex`), fresh Codex `PASS` via
  `scripts/request_codex_review.py`, snapshot smoke, tracked reservation,
  controller gates.
* Rollback/stop rule: exp_056 is a policy layer after smoothing, fully reversible
  to the exp_055 / repro_041 graph state. If any preregistered gate fails it is a
  terminal REJECT with no rescue sweep; retain repro_041 as behavior parent and
  exp_055 as the edge-repair reference.

## 7. Risks and how the falsifier protects us

* **Proxy over-optimism.** Frozen models saw training videos; division moves
  could exploit that. Mitigation: the exp_055 LB result is the go-gate (§1); if
  the proxy already over-credited edges, exp_056 is re-scoped to first LB-verify
  exp_055 before spending a division launch.
* **Coupling two structural changes.** exp_056 stacks division repair on the
  edge repair. If Codex judges causal attribution too entangled, the fallback
  arm is a division-only variant on the repro_041 graph (edge repair off) as the
  isolating control. Recorded here so the decision is explicit, not improvised.
* **Division move breaking edges.** The adjusted-edge non-regression gate and
  exact-hash receipts catch this deterministically.
* **Solver instability from a larger move set.** Same pinned SciPy 1.18.1, same
  protected-constraint invariants; the clean-namespace bootstrap regression from
  exp_055 is extended to the division move before any launch.

## 8. Codex challenge v1 — VERDICT: REVISE

Full text: `docs/research/exp056_codex_challenge_v1.md`. Codex judged the direction
promising but v1 not implementation-ready, citing: an undefined division
objective; an unstated hyperedge/set-packing solver reformulation (the exp_055
solver is a one-to-one Hungarian LSAP, not a MILP, and bundles only `_lsap`); a
contradiction between "preserve every fork" and "re-decide divisions"; a wrong
gate equation; missing causal/integrity controls; and it set the exp_055 Public
LB as a **hard execution go-gate**. Confirmed against the code: in
`scripts/original_score_joint_repair.py::solve_policy`, protected edges/forks are
excluded from the per-frame LSAP pool and lines 191–192 assert every existing
2-out fork is byte-identical before and after — so the current one-to-one
assignment structurally cannot create a division. Codex is correct.

## 9. v2 revisions (resolving each required change)

**9.1 Division candidate family, stage, feasibility (Codex #1).** The move is
**add-only**: create a new protected triple `(parent@t → daughterA@t+1,
daughterB@t+1)` only where *both* daughters are nodes that already exist in the
post-pruning graph at the solver stage (no resurrection of pruned/removed IDs;
if a needed daughter was pruned upstream the triple is simply infeasible and not
generated). Feasibility predicates, all reused from the frozen pipeline: same
next-frame constraint, existing geometric gap/parent/sister-distance and
symmetry caps, and the DeepCenter *feasibility* role defined in 9.4. Candidate
triples are generated deterministically from the same cached pair scores, after
pruning, before the solver — and their generation is hash-bound (9.6).

**9.2 Division-event evidence and objective (Codex #2).** A triple's score is a
fixed function of artifacts already in the graph: the two child edge
probabilities from the pair-score cache and the geometric sister-symmetry term,
combined by the same `utility()` original-score form used for edges, minus a
single fixed `division_edit_penalty` per created triple. No new learned model, no
GT, no calibrated "division probability" is invented — if such a calibrated score
does not exist in the cache, the triple score is defined purely from the two
child-edge original scores plus the geometric term. Every term, its source
artifact, exact formula, threshold/penalty, and stage is frozen and written to
the contract *before* any exp_056 GT metric is examined.

**9.3 Solver reformulation (Codex #3).** Replace the per-frame one-to-one LSAP
with a per-frame **deterministic weighted set-packing** over two move types:
single edges (as today) and division triples. Formulation: maximize total score
subject to — each source has at most one incoming and at most two outgoing
selected edges; a source selected as a division parent takes exactly its two
daughter edges atomically (no partial triple); each target has at most one
incoming selected edge; triples conflict with any single edge sharing a node;
protected edges/forks stay excluded from the pool (untouched). Deployment:
solve each frame's conflict graph exactly with a bounded branch-and-bound /
`scipy.optimize.milp` (pinned) with an integer 0/1 program, plus a brute-force
oracle path for small frames; canonical daughter ordering and deterministic tie
resolution fixed. **Division-disabled ⇒ the program reduces to the exact current
LSAP and must reproduce exp_055 byte-for-byte** (an explicit parity test, 9.5).

**9.4 DeepCenter as feasibility only.** DeepCenter no longer supplies the
accept/reject; it supplies a boolean feasibility veto on physically impossible
triples using its existing frozen center outputs and the existing threshold as a
*veto only*. The accept/reject moves entirely into the set-packing objective.
Checkpoint, epoch-2 `best.pt`, and hashes stay frozen and identity-checked.

**9.5 Four-arm zero-GPU factorial (Codex #5), replacing the single stack.** All
four run on the 16 frozen local graphs before any GPU: (1) repro_041 neither
repair; (2) exp_055 edge-only; (3) division-only on repro_041; (4) combined
edge+division. The **combined arm stays PRIMARY** for the *incremental* hypothesis
(division added to a byte-identical exp_055 policy); the division-only arm is the
mandatory control that separates the division main effect from interaction. The
division-only arm (arm 3) **prohibits ordinary single-edge repair** — it runs the
exp_055 pipeline with edge repair disabled and only the division move enabled, so
the only edge changes it may make are the daughter edges intrinsic to an accepted
division triple. The combined arm with division disabled must equal exp_055
byte-for-byte.

**9.6 Corrected and strengthened gates (Codex #4, #6).** Replace the false
equivalence with:
* division: `division_jaccard` strictly `> 0.2` **and** div `TP >= 4`
  (countwise per-specimen division non-inferiority vs exp_055, as in local_052);
* aggregate: primary score strictly `> exp_055` (0.9535869213120838), not merely
  division-up with tolerated edge loss;
* adjusted-edge: `>= exp_055` overall (no regression, consistent with the §3
  hypothesis; the earlier −0.0005 allowance is withdrawn) and a worst-video
  adjusted-edge regression bound `>= −0.002`;
* per-specimen: define the delta explicitly on primary, adjusted-edge, and
  division; each `>= −0.002` (primary/edge) and division non-inferior countwise;
* integrity manifests: hash candidate triples, pair-score cache, DeepCenter
  scores (or deterministic inputs), parameters, solver artifact, ordered actions,
  and final graph; exact final TP/FP/FN arithmetic reconciled to the action log;
  division move exercised on both specimens **and** on test inference;
  deterministic solver status/optimality/repeatability receipts;
* division-disabled byte-identical exp_055 output/action parity.

**9.7 Fork-protection contradiction (Codex #4).** Resolved by declaring the move
**add-only**: exp_056 never rejects or alters an existing protected fork; it may
only add new triples on parents that are not already forks. The existing
division-protection contract (freeze all current forks) is preserved verbatim,
not weakened.

**9.8 Hard LB go-gate (Codex proxy-vs-LB, #7).** Adopted as binding: exp_056 does
not enter implementation-to-launch until exp_055 submission 56261282 is scored
and is strictly above the displayed 0.942 baseline. A flat/negative exp_055 LB
re-opens the strategy (possibly making division-only primary) rather than
continuing the stacked design.

**9.9 Unrelaxed gates (Codex #8).** No leakage, provenance, hash-integrity,
budget, leaderboard, review, or promotion restriction is relaxed. No LB
submission is authorized for exp_056; KEEP would not imply promotion.

## 10. Status and next step (corrected ordering)

Correct project-contract order (Codex v2 #8): reach a versioned `CONSENSUS` on
this design → implement the solver → fresh Codex admission review of the actual
code → zero-GPU four-arm factorial + snapshot smoke → the exp_055 LB hard go-gate
→ 2.0h reservation → launch. The zero-GPU factorial is *implementation-dependent*
and therefore runs after consensus and implementation, not before. Two hard,
independent blockers remain: (a) design `CONSENSUS` on a fresh Codex challenge,
and (b) the exp_055 Public LB (submission 56261282) scoring strictly above 0.942.
If the LB is not above 0.942, return to the user before any further exp_056 work.

---

**Current status line:** v3 authored (§11 resolves Codex v2), **execution
hard-blocked** independently on (a) the exp_055 LB (submission 56261282) and (b) a
fresh Codex `CONSENSUS` plus an admission review of the implementation. No
implementation, launch, promotion, or leaderboard submission is authorized by this
document.

## 11. v3 revisions (resolving Codex v2 remaining items)

Full v2 challenge: `docs/research/exp056_codex_challenge_v2.md` (VERDICT: REVISE;
resolved #4 fork protection and #7 LB gate). §11 closes the rest and is grounded
in the actual solver `scripts/original_score_joint_repair.py` (single-edge original
score `w(s,t) = max(0, logit(p) − logit(τ))` from `utility()`; `edit_penalty = 0.25`;
`Candidate = (probability, threshold, cosine, motion, unique_best)`; per-component
gain accepted iff `> 1e-10`; existing 2-out forks excluded and asserted invariant).

**11.1 Exact candidate family and feasibility (Codex v2 #1).** A division triple
`d = (s@t -> a@t+1, b@t+1)` is generated iff ALL hold, deterministically, after
pruning and before the solver:
* `s` is NOT already a protected fork and NOT protected as a single edge (existing
  forks stay immutable, §9.7); `a != b`; `a, b` both exist in the post-pruning
  graph and are at frame `t+1`; neither `a` nor `b` is a protected target.
* both child pairs `(s,a)` and `(s,b)` are present in the frozen pair-score cache
  with finite probabilities (the same `load_original_candidates` source); a triple
  is infeasible (not generated) if either child pair is absent.
* geometry reuses the EXISTING frozen predicates only, evaluated on both daughters:
  the pipeline's division parent/sister distance caps, sister-symmetry ratio, and
  mutual-NN / divergence rules (the same `safe_division_*` predicates already in the
  runtime). No new geometric parameter is introduced.
* DeepCenter aggregation (Codex v2 #2 sub-point): the frozen DeepCenter center
  confidence is applied as a **veto only**, using the EXISTING deepcenter division
  threshold, required on BOTH daughters (a triple is vetoed unless both daughters
  pass the existing threshold). DeepCenter never contributes a magnitude to the
  objective. Occupancy: a daughter already consumed by a selected single edge or
  another triple cannot be reused (enforced by the target <=1-incoming constraint,
  §11.3). Removals: a triple may only displace non-protected single edges that
  share a node with it, and each such displacement is an edit counted in §11.2.
* Per-frame division candidate cap `K_div` (preregistered, e.g. 64) and per
  conflict-component variable cap `V_max` (preregistered, e.g. 24); exceeding
  either is **fail-closed** (frame/component aborts to no-division, logged), never
  a silent partial solve.

**11.2 Complete numerical objective (Codex v2 #2).** All coefficients frozen
before any exp_056 GT metric. Let `w(s,t) = max(0, logit(p_{s,t}) − logit(τ))`.
For a per-component selection `S` of single edges `E(S)` and triples `D(S)`,
relative to the component's current edges `C`:

```
Objective(S) = Σ_{e in E(S)} w(e) + Σ_{d in D(S)} [ w(d.a) + w(d.b) ]
             − edit_penalty · ( |E(S) \ C| + Σ_{d in D(S)} |{d.a,d.b} \ C| + |C \ edges(S)| )
             − division_edit_penalty · |D(S)|
```

where `edges(S)` is all edges implied by `S` (single edges plus both daughter
edges of each triple), `edit_penalty = 0.25` (frozen, unchanged), and
`division_edit_penalty = 0.25` (new, frozen a priori equal to `edit_penalty`; it is
NOT swept — one preregistered value, its sensitivity is only ever reported as the
factorial control, never tuned to the GT). A component's change is applied iff
`Objective(S*) − Objective(C) > 1e-10` (identical acceptance rule and tolerance to
the current code); otherwise the component keeps `C`. This reduces EXACTLY to the
current single-edge gain accounting when `D = {}`.

**11.3 Binary variables and constraints, atomic forks (Codex v2 #3).**
Per conflict component: `x_e in {0,1}` per single-edge candidate `e=(s,t)`,
`y_d in {0,1}` per triple `d=(s,{a,b})`. Constraints:
* source atomicity/exclusion: `Σ_{e=(s,·)} x_e + Σ_{d=(s,·)} y_d <= 1` for every
  source `s` in the component — a source takes at most ONE move (one single edge OR
  one triple), so two independent single edges from one source are forbidden and a
  triple is the only way to create two outgoing daughter edges (atomic by
  construction: both daughters live inside the single variable `y_d`).
* target capacity incl. fixed edges: `Σ_{e=(·,t)} x_e + Σ_{d: t in {a,b}} y_d
  + fixed_in(t) <= 1`, where `fixed_in(t) in {0,1}` counts any retained
  protected/out-of-pool edge already entering `t` (residual capacity around fixed
  edges, closing Codex v2 #3's capacity gap).
* protected edges/forks are excluded from the component pool entirely and are never
  variables (unchanged from exp_055).
With `D = {}` these constraints are exactly the bipartite assignment of the current
LSAP, so the division-disabled program is the same optimum.

**11.4 Deterministic solver and byte-exact parity by dispatch (Codex v2 #3, new-risk
#1,#3,#4).** No new solver dependency is added; exp_055's `_lsap`-only bundle stays
valid:
* Decompose each frame into independent conflict components (shared source/target),
  reusing the existing slot-space component logic.
* A component with NO triple variable dispatches to the EXISTING LSAP code path
  verbatim — byte-identical assignment, gain decomposition, and action records.
  This is how division-disabled arms reproduce exp_055 exactly (not by re-solving an
  equivalent MILP).
* A component containing >=1 triple is solved by **exact pure-Python branch-and-bound**
  over its `<= V_max` binary variables (fail-closed above the cap). Divisions are
  sparse and local, so components are tiny; exactness is cheap and needs no HiGHS.

**11.5 Deterministic tie resolution (new-risk #2).** Optima are made unique by a
frozen lexicographic key: maximize `Objective` at fixed float64 evaluation, then
among equal-objective selections choose (1) fewer total edits, then (2) fewer
triples, then (3) the selection whose sorted `(source,target)` edge list is
lexicographically smallest. B&B explores variables in ascending `(source,target)` /
`(source,a,b)` order so the first optimum found under this key is canonical;
repeatability is asserted by a receipt (§11.7).

**11.6 Division-disabled ⇒ existing LSAP path, byte-identical.** The four-arm
factorial's edge-only and neither arms, and any `division_candidates = {}`
invocation, execute the current `solve_policy` unchanged. A regression test asserts
byte-identical final graph and ordered actions vs exp_055 on all 16 graphs.

**11.7 Corrected gates and complete manifest (Codex v2 #6).** §5 and §9.6 are
corrected above (false `FP+FN<16` equivalence removed; adjusted-edge gate `>=
exp_055`, the −0.0005 allowance withdrawn; per-specimen countwise division
non-inferiority stated as `div_FP_spec <= exp_055 div_FP_spec` AND `div_FN_spec <=
exp_055 div_FN_spec` with `div_TP_spec >= exp_055`). The integrity manifest binds,
by hash: the pre-solver node/edge graph; the pair-score cache; the DeepCenter
scores or their deterministic inputs; every frozen parameter incl.
`division_edit_penalty`, `K_div`, `V_max`; the solver SOURCE and the complete
runtime dependency set / environment (so no unpinned binary can slip in); the
scorer; the candidate-triple set; the ordered actions; the final validation graphs;
and the final `submission.csv`. Final division TP/FP/FN is reconciled arithmetic-
exactly to the action log; the division move is asserted exercised on both
specimens and on test inference; and solver optimality-status + repeatability
receipts are recorded per component.

**11.8 Corrected sequencing (Codex v2 #8).** See §10: `CONSENSUS` -> implementation
-> fresh Codex admission review of the code -> zero-GPU four-arm factorial + smoke
-> exp_055 LB hard gate -> reservation -> launch. The factorial is implementation-
dependent and runs after consensus + implementation, not before.

**11.9 Deployment and scaling (new-risk #1, #4).** No new binary dependency (pure-
Python B&B); the existing pinned `_lsap` bundle is unchanged and its hash stays
gated. Per-frame `K_div` and per-component `V_max` caps with fail-closed behavior
bound worst-frame cost; the zero-GPU factorial reports observed worst-component
size and asserts it stays under the caps before any GPU launch.

---

**v3 status line:** v3 authored; resolves Codex v1 and v2. Awaiting a fresh Codex
challenge for a versioned `CONSENSUS`. Execution remains hard-blocked independently
on (a) the exp_055 Public LB (submission 56261282) scoring strictly above 0.942 and
(b) that `CONSENSUS` plus a fresh Codex admission review of the implementation. No
implementation, launch, promotion, or leaderboard submission is authorized now.
