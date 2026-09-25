# exp_062 — Codex strategy challenge v1

Reviewer: Codex `gpt-6-astra`, reasoning effort low, read-only sandbox. Date: 2026-09-23.
Target: `docs/research/exp062_mutual_best_edge_association_proposal.md` v1.
Invocation: `codex exec --ephemeral --sandbox read-only --skip-git-repo-check -m gpt-6-astra
-c model_reasoning_effort=low` (config not swapped; model passed on the command line).
Tokens used: 103,581.

**VERDICT: REVISE**

---

## Verdict (verbatim)

> **REVISE. Mutual-best is worth one bounded probe, but the proposal's rationale, activity test, and
> deployment plan need correction.** Parent-source inspection rules out mathematical equivalence
> with harmonic fusion; it does **not** establish useful additional signal.
>
> The strongest factual error is that earlier interventions were division-only. exp_055's gain was
> entirely adjusted-edge, with division preserved; exp_057 changed 3,714 edges. This is another edge
> hypothesis, not the project's first.
>
> Review performed strictly read-only; no files created or changed.

## Answers to the six questions

1. **Axis check.** A constructed matrix alone is insufficient unless it exercises the actual patched
   source. The layout is `[n_src, n_tgt]`: dim 0 chooses a source for each target; dim 1 chooses a
   target for each source. The proposal's "source (column), target (row)" explanation **reverses
   this**. Test an asymmetric rectangular matrix through the extracted activation block, including
   ties and single-source/target cases.
   (`references/biohub-tracking-support-pack/repo/scripts/predict_unet_transformer.py:452`)

2. **β = 0 control.** Keep it. Source stripping cannot establish effective configuration, cache
   isolation, or real-pipeline parity. However, run it as **development validation**; do not require
   the historical public CSV hash during hidden reruns with different input data. **The submitted
   notebook should run only the candidate.** Budget that deployment separately if it requires
   another visible run.

3. **First β.** 0.20 is defensible as an *exploratory* choice, not a calibrated optimum. Its maximum
   bonus is 0.4 logits; the largest within-column bonus difference is 0.44, an odds multiplier of
   ≈1.55 under softmax. Nothing presented establishes 0.12 is better. **Retain 0.20, but remove the
   automatic doubling after a displayed null.**

4. **Dropping the proxy gate.** Defensible as a *resource* decision, **not** on the claimed "two
   large-margin transfer failures". exp_055 is genuine evidence (+0.0148537 proxy, zero displayed LB
   gain). exp_057 **explicitly skipped proxy scoring**; its 3,714 changed edges measure *activity,
   not quality*. The third-party evolution table remains independently unverified — the notebook was
   inaccessible through web retrieval. Keep correctness and graph-integrity gates; **acknowledge
   there is no pre-LB quality estimate.**

5. **Redundancy with harmonic fusion.** **Not mathematically redundant, but potentially empirically
   redundant.** In the parent notebook (code cell 2, source lines 1345–1363) reverse logits are
   transposed, aligned and normalised along the **same source axis** as forward logits; weighted
   harmonic fusion uses reverse weight 0.15 and **does not enforce simultaneous row/column
   winners**. The new prior therefore adds *target competition within each source*.
   Nevertheless it **reinforces the existing fused ranking rather than supplying independent
   evidence**. It can strengthen a confidently wrong winner, disadvantage a legitimate second
   daughter, and depends on across-column logit calibration. Adding a constant to each column leaves
   parent softmax probabilities unchanged but can change the proposed row winners.
   **Call it a rank-sharpening heuristic, not a ratio test or established anti-hijacking mechanism.**

6. **Bounded gate.** Accept with amendments (below). Runtime-only evidence must not be demanded
   before the authorized runtime exists.

## Findings

### 1. [CORRECTNESS] The required monotonicity test contradicts the patch

Net bonuses are:

| pair status | bonus |
|---|---:|
| mutual | `2β` |
| column-best only | `0.8β` |
| row-best only | `0.3β` |
| neither | `−0.2β` |

So "every non-mutual pair decreases" is **false**. Replace that test with this truth table plus
post-activation checks. **H2 must also drop the requirement that mutual-best status changes** — an
effective confidence adjustment can preserve all winners. Measure patch execution, changed
probabilities / candidate edges, and canonical final-graph differences **separately**.
(proposal lines 60–71, 193–198)

### 2. [CORRECTNESS] The deployment specification contradicts its own precedent

"Two arms in one kernel" is **not** the promised single-config submission. The successful exp_060
receipt also says the PP sweep **selected tight55** — it does **not** support "validator disabled,
tight55 pinned, as in exp_060". Specify separate development-control and candidate-only execution,
exact input/cache isolation, and total budget.
(proposal line 126; `experiments/exp_060_.../leaderboard-submission.json:30`)

### 3. [CORRECTNESS] The historical argument and weight interpretation are wrong

exp_055 **preserved division and improved adjusted-edge**; exp_057 was a motion/edge intervention.
The official score is **`adjusted_edge + 0.1 × division`**, *not* a 0.9/0.1 convex mixture. The
asymmetry is real, but the coefficients **do not establish remaining headroom** or guarantee
sub-precision division effects. The cited ceiling audit actually gives **division the largest
optimistic headroom** and explicitly records an earlier fragmentation-transfer failure.
(`experiments/exp_055_.../metrics.json:145`; `docs/research/exp057_A0_edge_upper_bound_results.md:24`)

### 4. [CORRECTNESS] The null-result interpretation does not justify β = 0.40

Changed predictions plus an unchanged displayed score can mean beneficial/harmful **cancellation**,
changes **outside sparse annotations**, or **rounding** — not necessarily "too weak". Equal
three-decimal scores also do **not** establish an absolute delta below 0.0005. Replace automatic
escalation with closing the probe or a separately justified follow-up; **skip submission entirely
for an identical final candidate.** (proposal line 221)

### 5. [VERIFICATION-DEPTH] Deployment success is verified; exclusivity is not

exp_060 submission 56361673 scored 0.947 — but **repro_059 and exp_057 also have successful
code-submission records**. "Only transport in this project" is too broad; "closest successful
minimal-change deployment precedent" is supported. The proposed two-arm arrangement does not
inherit that success automatically. (`experiments/exp_057_.../leaderboard-submission.json:17`)

### 6. [VERIFICATION-DEPTH] Public pedigree does not establish selection success

An `e-mutual-best` identifier proves **neither** that E beat A–D **nor** that it "survived" a
measured comparison. Low votes establish neither novelty nor limited adoption. Absence above a
0.949 cutoff does not discredit a 0.948 claim. Treat all of this as **unverified context**, not
positive efficacy evidence. (proposal line 83)

## Ruling on the bounded-gate contract (§9): ACCEPT, AMENDED

- One consolidated strategy correction, then **one** scoped implementation/admission review against
  the exact snapshot.
- **Block** on concrete correctness, leakage, provenance, fail-closed, graph-validity or budget
  defects.
- **Record without blocking**: speculative efficacy and additional verification depth.
- Put real-GPU parity and execution evidence **inside the authorized development run**; require them
  before submission.
- Re-review **fixes and newly introduced defects only**. A round limit cannot make a known defect
  acceptable.
- Preserve fresh experiment-specific Codex PASS and separate submission authorization.

Correction to the proposal's premise: the record documents **five custom plus four formal**
admission rounds for exp_060, not simply five.
(`experiments/exp_060_.../formal_admission_status.md:55`)

## Recommendation on lever choice for the remaining six days

> **Keep corrected mutual-best β = 0.20 first, for one scored probe.** Its advantage is small
> implementation scope and a mechanism distinct from harmonic fusion — **not** verified public
> superiority or an untouched metric term.
>
> After a null or regression, prefer **density-adaptive relinking** over automatic β doubling,
> subject to inspecting the actual thresholds and policy. **Keep option B available: the evidence
> does not justify dismissing division categorically.** DivNet remains a larger integration and
> model-provenance commitment.
>
> The ledger supports 20.398674 h remaining, of which **14.398674 are unprotected**. The proposed
> 2.6-hour development run fits, but candidate-only deployment and any follow-up must be explicitly
> included in the spending plan.

---

## Claude's independent verification of the three load-bearing corrections

Per the project contract these were checked against the repository rather than accepted on the
reviewer's word. **All three are confirmed; the proposal v1 was wrong on each.**

1. **exp_055 was an EDGE intervention, not division.** `experiments/exp_055_.../metrics.json`:
   `specimen_metrics/44b6/adjusted_edge_delta = 0.0033374477`,
   `specimen_metrics/6bba/adjusted_edge_delta = 0.0189239316`, while `division_jaccard = 0.2`
   is **unchanged in every specimen block**. The entire proxy gain was adjusted-edge, and the LB
   moved 0.000. `HANDOUT.md` itself labels it "exp_055 edge (0.942==0.942)" — proposal v1 therefore
   contradicted our own handout. **This materially weakens the proposal's core motivation: the
   "edge side is untried" framing is false.**
2. **Axis labels reversed.** `predict_unet_transformer.py:452` annotates the returned tensor
   `# (1, n_src, n_tgt)`, so rows are sources and columns are targets; the parent then applies
   `softmax(raw, dim=0)` (line 456), i.e. it normalises **over sources**. Proposal v1's "best choice
   of its source (column) and of its target (row)" is backwards. The upstream anchor block
   (lines 454–458) does exist verbatim in our reference copy, which does confirm the patch is
   portable.
3. **exp_060's lb-submit kernel did NOT disable the sweep.** `STATE.json.exp060_0p18_lb.run_completed`
   records "ppsweep re-selected tight55 (MOTION_RELINK_TIGHT_UM=5.5, same as parent)". Proposal v1's
   budget rationale ("adaptive PP-sweep is disabled … as in exp_060's lb-submit kernel") is false,
   and the 1.3 h reference figure **includes** the sweep.

Findings 5 and 6 are also confirmed as overstatements: `repro_059` (56313491), `exp_057` (56281129)
and `exp_055` (56261282) all returned scores via code submission, so exp_060 is not the unique
working transport; and "E survived the A–E series" was inferred from an environment-variable name,
not from any measurement.

**Status: proposal v1 is superseded. A consolidated v2 correction is required before any build.
No CONSENSUS. Nothing is authorized.**
