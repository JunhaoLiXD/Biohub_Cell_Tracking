# PLAN - v5, post-exp071 accuracy recovery proposal

## Current result and decision - 2026-09-27

Authenticated submission `56616854` from `exp_071_ep015_hidden_rerun_repair`
completed at Public LB **0.950**, down **0.003** from retained exp064 submission
`56535761` at **0.953**. The exp071 submission is byte-identical to the exp068
candidate (`f09854c3`), and the repaired code-submission transport returned a real
score, so this is a valid negative accuracy result rather than a transport failure.

The intervention demonstrably fired: `OUTPUT_MIN_EDGE_PROB=0.15` removed 4,163
weak edges, 5,472 nodes and 7,335 final edges, and reduced structural forks from
62 to 47. The harvested eight-movie proxy had estimated a test-reweighted
adjusted-edge gain of +0.00236, but it also showed strong heterogeneity: the 44b6
prefix regressed about -0.0085 and 10 of 36 test-shaped subset draws were negative.
The Public LB result establishes that the apparent average proxy gain did not
transfer. Apply the pre-registered `<=0.952` branch: **REVERT, retain exp064, and
close the global `ep010`/`ep015`/`ep020` output-edge-floor family.** Do not run
`ep_cx`; it combines exp071's measured negative lever with exp066's measured-null
count-pruning lever.

Evidence:

- `experiments/exp_071_ep015_hidden_rerun_repair/leaderboard-result.json`
- `experiments/exp_071_ep015_hidden_rerun_repair/independent_collection_audit.json`
- `SUBMISSION_BUDGET.json`, submission `56616854`

## Final accuracy-recovery direction - Tier C consensus reached

This is a new graph-policy direction, not a continuation or retuning of ep015.
It is **Tier C** because it changes which graph edges are eligible for pruning and
introduces adaptive behavior. Claude strategy input and the independent Codex
challenge have reached explicit `CONSENSUS`. Only the zero-GPU Stage 0 diagnostic
is authorized; no GPU launch or leaderboard submission is authorized.

### Hypothesis

Some low-confidence output edges belong to false-positive fragments, but a flat
movie-independent floor destroys true lineage structure and divisions. A pruning
policy may retain the useful precision effect only if it is disabled on
under-predicted movies/regions and explicitly protects division topology.

### Stage 0 - zero-GPU counterfactual only

Start from exp064 graphs and reuse existing held-out TRAIN artifacts. The single
pre-registered primary hypothesis is:

1. `fork_protected_ep015`: apply the 0.15 edge floor except to both outgoing edges
   of every pre-pruning out-degree-two source.

The following policies are confirmatory diagnostics only. They may explain the
result but cannot be promoted in this arc, even if they outscore the primary.
They must not be computed until the primary's metrics, gate decisions and terminal
PASS/FAIL disposition have been written to an immutable receipt:

2. `lineage_protected_ep015`: additionally protect the local lineage neighborhood
   one or two frames before and after each fork, with the exact radius frozen
   before aggregate metrics are read.
3. `adaptive_protected_ep`: enable protected pruning only when a pre-registered,
   label-free density signal indicates over-prediction. Candidate signals may use
   node density, edge/node ratio and short-isolated-track fraction, but may not use
   movie identity, prefix, ground truth, hidden-test statistics or Public LB.

The diagnostic must replay the official held-out scorer and report aggregate,
each embryo prefix, every movie, division TP/FP/FN, node/edge/fork deltas, and all
36 two-per-prefix test-shaped subset draws. It must include exp064, exp066/cx03 and
flat ep015 as frozen controls. Nested leave-one-movie-out evaluation is mandatory;
no threshold, radius or policy may be selected and evaluated on the same movies.

### Gate to one candidate experiment

Only the pre-registered `fork_protected_ep015` primary may advance. Gates are
adjudicated in the following order, with no discretion:

- test-shaped negative draws are at most 3 of 36, versus ep015's 10 of 36;
- worst movie delta is at least -0.002;
- intervention is non-void on at least four of eight movies and automatically
  bypasses the known under-predicted cases using only the frozen label-free rule;
- neither embryo prefix regresses by more than 0.0005 adjusted edge;
- division TP does not decrease and division FN does not increase;
- every individually credited held-out fork is preserved; losing one credited
  fork fails even if another credited fork is gained;
- pooled proxy improvement is at least +0.0015 over exp064 with each of the eight
  movies dropped in turn, and the delta remains positive with movie 44b6 dropped;
- deterministic output-contract, rollback and leakage tests pass.

Failure of any gate closes this direction with zero GPU and zero submissions.
The primary disposition is irreversible after its receipt is written; later
confirmatory results cannot reopen, promote or change it.
Passing the diagnostic budgets at most one future LB slot and permits only a
compact implementation card and independent
admission review; it does not itself authorize a launch. Any later Kaggle run and
LB submission require fresh explicit user authorization, budget reservation,
immutable snapshot, smoke PASS, independent implementation PASS, remote source
binding and authenticated submission-history checks.

### Claude strategy-review status - 2026-09-28

Claude judged the scientific direction, scorer coverage and feasibility sound,
but returned `REVISE` because selecting the best of three policies on the same
eight movies would leave a multiplicity/overfit path. This revision incorporates
all requested controls: one pre-registered promotable primary, mandatory nested
leave-one-movie-out evaluation, absolute preservation of each credited fork,
dispersion-first gate ordering, and at most one LB slot only when the primary
passes every gate. Its delta call correctly refused to self-certify under the
Tier C Claude-authors/Codex-challenges rule and flagged that visible confirmatory
results could still influence the primary decision. Codex independently confirmed
that finding and closed it structurally by requiring the primary disposition to
be sealed before confirmatory computation. **Tier C strategy status: CONSENSUS.**
This authorizes only the zero-GPU Stage 0 diagnostic; it does not authorize a
remote run or leaderboard submission.

### Expected value and stop rule

The realistic target is a displayed +0.001, not recovery of the full held-out
estimate. The mechanism could recover exp071's lost division/lineage score while
retaining a subset of its false-positive pruning benefit. Evidence is currently
insufficient to predict a gain. If Stage 0 does not produce a robust candidate,
freeze exp064 at 0.953 as the final result and stop accuracy work for this
competition. Do not fall back to threshold sweeps, `ep_cx`, tight-UM guessing,
additional public-notebook copying or unvalidated exp067 training.

<!-- BEGIN EP068 CURRENT -->
## Current ep068 status - 2026-09-27T04:40Z

**The authorized ep015 LB probe is DONE and SUBMITTED: `56597763`, PENDING.**
`exp_068_ep015_single_probe` is collected, independently audited **PASS**, remote-source bound,
controller state `KEEP`. 1415.64 s = 0.393 GPU h; ledger 29.606766 h, no reservations.
Output sha `f09854c3`, the lever fired (4163 weak edges dropped, -7335 edges, forks 62 -> 47).

**The single-submission authorization is now SPENT. Do not submit again.** Any earlier text in this
file directing you to carry out the pre-authorized ep015 leaderboard submission is **superseded** -
that action has been performed.

Next: **do not poll.** Wait for the user to report the score, read it back once from authenticated
`kaggle competitions submissions`, record it in `SUBMISSION_BUDGET.json` (entry 18) and
`STATE.json.exp068_ep015_submission`, then apply the pre-registered rule vs retained 0.953:
**>=0.955 adopt; 0.954 small real gain; 0.953 NULL keep exp_064 and close the `ep` family;
<=0.952 revert.** No second probe, no final re-selection, no exp067 training, no public push
without fresh authorization. Deadline 2026-09-29 23:59 NY.

**Full detail, gate evidence and the honest two-sided read of the ep015 evidence live in
`HANDOUT.md`'s CURRENT STATE block.** `STATE.json` remains authoritative.
Retained best is still 56535761 at recorded 0.953 until 56597763 resolves.
exp067 training remains stopped. The CPU counterfactual is complete and is GT-assisted TRAIN
diagnosis only: `docs/research/ep015_continuation_2026-09-26/division_counterfactual_report.md`.
<!-- END EP068 CURRENT -->
## Active authorization - ep015 continuation, 2026-09-26

The user reports 30 GPU hours remaining and accepts the proposed next steps: one ep015
candidate run and one leaderboard probe after the existing strategy/review/smoke/output
gates, plus a zero-GPU division scoring-potential diagnostic. This supersedes the
closeout's ep015-OFF/no-successor instruction only within this bounded scope.
Retain exp064 submission 56535761 as the final choice unless separately instructed.
No second probe, full exp067 training, broader data export or public push is authorized.
Use the conservative three-per-New-York-day submission cap and check remote history
before the single submission. Wait for the user completion notice after launch; do not poll.
Strategy and receipts: `docs/research/ep015_continuation_2026-09-26/`.
Exact model allowance is unavailable; no automatic review retry after timeout or quota stop.


2026-09-26. User accepted Codex's closeout recommendation. Prior v3 is preserved at
`docs/research/PLAN_v3_2026-09-26_superseded.md`. Evidence and qualifications:
`docs/research/closeout_review_2026-09-26.md`.

## 1. Current decision

- Retain exp064 x138, submission **56535761**, recorded Public LB **0.953**.
- User-reported final selection is retained; live site selection is not reverified.
- Stop exp067 for this competition because of sparse supervision and the remaining
  validation/deployment workload. Its architecture has not been falsified.
- No GPU work is pending in local records. Ledger remaining: **16.752765 h**; no reservations.
- ep015 defaults to OFF. No launch, submission, new training or public push is authorized.

## 2. Corrected evidence

The eight exports contain 12 GT divisions, nine fully matched triples, two exact
parent-to-daughters events and seven direct-edge deficits. The parent scorer instead
returns **3/2/9 TP/FP/FN**: one direct-edge deficit already receives component-level credit.
The seven are not seven scorer FNs. Existing Q1 reports candidate edges for six and
generated events for zero; candidate generation was not rerun during closeout.

On cached coordinates, disabling symmetry alone admits **4/7**, widening distance
alone admits **0/7**, and both changes admit **7/7** geometrically. This does not establish
event availability or decoded score gain. sym075 (tau 0.75) still rejects all seven;
its failed proxy does not test sufficient relaxation. The historical universal-cause
claim is withdrawn. See the corrected Stage 0 report and numerical audit.

## 3. Completed local closeout

- [x] Preserve original PLAN v3 and Stage 0 v1; publish the correction and reproducible CPU audit.
- [x] Reproduce parent TP/FP/FN on every movie and reconcile direct-edge versus component semantics.
- [x] Reconcile GPU charges and empty reservations; keep the documented rounding residual.
- [x] Check local submission receipts without rewriting historical scores or claiming remote verification.
- [x] Update STATE, EXP067_STATUS and current handoff notices; regenerate governance checkpoints.
- [x] Keep exp064 snapshots, predictions and historical experiment/review records unchanged.
- [x] Public GitHub publication remains deferred; no push is part of closeout.
- [ ] Before close, verify **56535761** is still selected on the competition site.

Q2/Q3 remain unrun and deferred unless a future separately authorized research effort needs them.
The decoder has not been certified by this closeout. No new milestone notebook is warranted
for a corrected diagnostic and stopped, untrained experiment.

## 4. Optional ep015 - not part of current work

One probe or none, approximately 0.5 GPU hours and one submission if separately authorized.
Use the exact cx03 implementation vehicle with cx03 disabled and
`BIOHUB_OUTPUT_MIN_EDGE_PROB=0.15`; the unmodified x138 notebook does not implement this lever.
Pin implementation provenance and confirm all other levers remain off.

The historical test-reweighted proxy delta is +0.00236; worst per-prefix adjusted-edge
regression is approximately -0.0085. cx03's +0.00115 proxy corresponded to a reported
0.953 Public LB, equal to the parent at reported precision. Neither result supplies
a reliable transfer function. The old ~0.955 extrapolation is not a bound or expectation.

Retain the conservative read rule: >=0.955 permits a separate final-selection review;
0.954 defaults to retaining exp064; 0.953 is a registered null; <=0.952 rejects the arm.
Public-score improvement does not certify private-score improvement. No second probe.

Required first: versioned proposal/critique/revisions and explicit strategy CONSENSUS,
fresh experiment-specific Codex PASS, snapshot smoke, budget reservation and explicit
launch/submission authorization. Past export waivers do not apply. Exact model allowance
is not visible; retain the ten-percent reserve and avoid repeated review calls.

## 5. Final checks and standing constraints

Research cutoff remains **2026-09-29 12:00 UTC**. The locally recorded competition
deadline is September 29 23:59 with unspecified timezone; verify the official timestamp
on the site rather than treating this local record as a fresh deadline confirmation.

Do not poll runs or start experiments. Final selection changes require a separate decision.
Before any future submission, check authenticated remote history and resolve the current
three/day AGENTS instruction versus the ledger's historical five/day waiver. Closeout
does not resolve this by silently changing either record. Keep English technical files,
immutable history, and private artifacts out of the public remote.
