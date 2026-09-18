# Strategy Proposal — Post-exp_057 Direction: "B then A"

Record type: versioned strategy proposal (Valid-KEEP branch, post-two-null)
Author: Claude Code. Date: 2026-09-16.
Status: **v2 — revised after Codex challenge v1 (VERDICT: REVISE).** No
implementation, GPU, launch, promotion, or LB submission is authorized by this
record. Execution of any phase requires a versioned `CONSENSUS` plus the standard
admission gates.

## Changelog v1 → v2 (all in response to Codex challenge v1; two claims verified wrong by Claude)

Codex challenge: `docs/research/exp057_post_null_codex_challenge_v1.md`.

* **RETRACTED — "edge layer exhausted by denominator scale."** Verified wrong: the
  train16 scored edge union is **10,055 edges** (not "hundreds of thousands per
  movie"), and there are only **8 wrong-association edges** — a small, specific
  class that *could* move a 3-decimal LB. The two nulls prove only that *those two*
  interventions did not transfer, not that the edge/detection layer is exhausted.
* **RETRACTED — the "6-run pooled separability" confirmation.** Verified
  pseudo-replication: the 6 causal-audit files are 3 distinct files (identical
  triples/pairs) with the **same 2 positive sites**; pooling does not escape N=2.
  Also they run with `safe_div_veto=false`, unlike the 0.944 production gate. The
  DeepCenter "no signal" claim is downgraded to "an apparent *reversed* signal
  (low-score⇒true) that is untrustworthy at N=2, and may mean the gate
  *anti-selects*." (The invalid script is preserved at
  `docs/research/scripts/div_separability_pooled_INVALID.py`.)
* **NARROWED B** to only the two tested branches (see §1).
* **INSERTED a zero-GPU A0 audit** before A1 (see §4).
* **REFRAMED A1** as feasibility-only; a trustworthy framework-selection gate
  probably needs new labeled specimens (see §4a).
* **GOVERNANCE fixes:** 0.944 is *verified*, not *reproducible* (`metrics.json`
  sets `reproducible:false`); the LB is not the falsification mechanism; `STATE.json`
  active-experiment pointer to be reconciled.

Inputs this proposal rests on:
- `docs/research/exp057_division_bottleneck_diagnostic.md` (the division diagnostic;
  note its §4/§6/§6a/§7 conclusions are WITHDRAWN/CORRECTED — the **option-C pooled
  separability "confirmation" is NOT a valid input** and is excluded here).
- The verified scoring facts: score = adjusted_edge_jaccard + 0.1·division_jaccard;
  train16 scored edge union ~10,055 edges incl. 8 wrong-association edges; division
  3/8/9 on the 0.944 line.
- exp_055 LB 0.942 == repro_041 0.942 (Δ0); exp_057 LB 0.944 == repro_048 0.944
  (Δ0), both causally isolated.

## 1. The decision (v2)

Adopt a phased posture: **B → A0 → (A1 → A2)**.

* **Phase B (now): stop spending GPU on the two mechanisms just tested.** Retain
  `repro_048` (Public LB 0.944, submission 56105868, SHA 0319ba6d…) as the best
  **verified** LB parent. **B is narrowed** to: *motion-EMA retuning and the tested
  post-smoothing joint-repair branch are closed LB dead-ends.* B does **not** claim
  the whole edge/detection layer or all division tuning is exhausted — that is not
  established.
* **Phase A0 (next, zero-GPU): a scorer-aware audit that decides where any lever
  actually is**, before spending GPU or committing to a framework bet. A0 is the
  circuit-breaker and is the only phase this proposal asks to authorize *now*
  (analysis only). See §4.
* **Phase A1 (gated on A0): a feasibility/power audit** of whether a division (or
  other) improvement can be *measured at all* on the available data — explicitly
  not a promise to build a trustworthy substrate. See §4a.
* **Phase A2 (gated on A0+A1 + CONSENSUS + admission): the actual modeling bet**,
  only if A0 finds a lever and A1 finds a way to measure it. Otherwise B is final.

The ordering is the point: no GPU and no framework commitment until a zero-GPU
audit (A0) shows a lever exists and A1 shows we can measure it.

## 2. Why B (narrowed) is the honest default (evidence)

1. **The two tested interventions do not transfer to the LB.** exp_055 (500
   actions/video) and exp_057 (3714-edge symdiff) each produced Δ0 at the LB. This
   establishes that *these two* mechanisms are dead ends — **not** that the whole
   edge/detection layer is exhausted. A 3714-edge symdiff can be score-neutral
   because the changed edges are unmatched, compensating, or in scorer-irrelevant
   regions (train16 scored union is only ~10,055 edges, so the changes are *not*
   negligibly small — they simply do not touch the matched TP/FP/FN).
2. **Division is a high-leverage term** (denominator ~12–20 events × 0.1 weight ⇒
   moving division_jaccard 0.15→0.30 ≈ **+0.015** of score), and its current state
   on the 0.944 line is poor (TP/FP/FN 3/8/9). But the *nature* of the failure
   (pure mis-localization vs. also candidate-generation) is **not yet proven** —
   the existing causal audit only sees *retained* candidates, and its apparent
   DeepCenter "no signal" is really a reversed low-score signal at N=2 (possible
   gate anti-selection). This is exactly what A0 must resolve.
3. **We currently cannot trustworthily validate a division change.** ~12 true
   divisions on 2 specimens; the train16 proxy is falsified by two proxy→LB
   transfer failures. Without a measurement we can trust, a division experiment is
   a blind LB gamble.

Given (1)–(3), continued GPU spend on **EMA/joint-repair retuning** is unjustified.
0.944 is **verified** (submission identity confirmed) but **not reproducible**
generalization (`val_049 metrics.json: reproducible=false`; frozen models saw the
validation videos). B is a GPU stop on the tested branches, not a claim that no
lever remains.

## 3. Why A is still worth queuing (not abandoning)

Two candidate levers survive B and are worth a zero-GPU look before any bet:
(i) the **8 wrong-association edges** and other bounded edge/detection/pruning
sub-targets on the 0.944 line (small, causally-specific, possibly LB-movable); and
(ii) **division-detection quality**, the highest-upside but hardest lever. Whether
either is real and measurable is an empirical question A0/A1 answer — not an
assumption.

## 4. Phase A0 — zero-GPU scorer-aware audit (the ONLY phase authorized to run now)

A0 is analysis only (no training, no launch, no LB). Deliverables:

1. **Edge upper-bound audit (exact 0.944 lineage, val_049 artifacts).** Using the
   frozen scorer, compute the *scorer-aware* score ceiling from correcting each
   bounded error class: the **8 wrong-association edges**, the fragmented-edge and
   detection-loss classes, and node-pruning of spurious predicted nodes (which feed
   the per-sample node-count adjustment). Output: max achievable Δscore per class,
   ranked — to decide whether any edge/detection sub-target is even worth pursuing.
2. **Exact-0.944-lineage division candidate audit, pre-filter → output.** Instrument
   (locally, on retained artifacts where possible; otherwise specify the minimal
   diagnostic export) every division candidate through mutual-NN → distance →
   divergence → symmetry → DeepCenter veto → ranking → caps, recording which gate
   rejects each of the missing GT sites. This directly tests the (currently
   unproven) "geometry rarely nominates true sites" claim.
3. **Scorer-aware fork audit + directionality.** First **enumerate and GT-map the
   predicted fork nodes directly** under the official scorer — do not assume the 8
   aggregate FP correspond to 8 distinct false fork sites (`FP = max(0,
   matched_pred_divisions − TP)` mixes two matching procedures). From that faithful
   population, test one-at-a-time suppression/addition under the scorer, and test
   **both** high- and low-score directions of the DeepCenter score (the reversed
   N=2 hint). Deduplicate by physical candidate/site (no pseudo-replication) and
   record `safe_div_veto` state.
   A0 outcomes are phrased as **"no actionable evidence with current data"** on a
   null — never as proof that no signal exists.
4. **Provenance:** every A0 script, its exact inputs + SHA256s, and outputs are
   preserved under `docs/research/` (not scratchpad), versioned before CONSENSUS.

A0 stop rule: if no edge sub-target clears a meaningful Δscore ceiling **and** the
division audit shows no separable signal at true sites, then B is final and A
closes with zero GPU spent.

## 4a. Phase A1 — feasibility/power audit ONLY (gated on A0 finding a lever)

A1 does **not** claim to build a trustworthy held-out substrate; with 2 specimens
that likely requires **new labeled specimens**. A1 only quantifies *how inadequate*
the current evidence is and what, if anything, can be measured:

* It must **distinguish calibration holdout from model holdout** (the frozen
  detector/association models already saw all 16 videos; LOVO/cross-specimen test
  only post-processing calibration, not model generalization).
* **Prohibit iterative reuse** of cross-specimen folds: two specimens give two
  high-variance evaluations (~5 and ~7 events); if both directions inform any
  feature/threshold/stopping decision, nothing is held out. Usable only for a
  *fully frozen* algorithm as a descriptive cross-fit.
* **Reject event-only bootstrap CIs** (they omit the FP-generating population and
  are anti-conservative); at most a hierarchical specimen/video bootstrap, with the
  explicit caveat that 2 specimen clusters cannot estimate between-specimen
  uncertainty.
* Deliverable: a written feasibility verdict — "what effect size, if any, is
  detectable, and under what frozen-algorithm constraints." If nothing credible is
  detectable without new data, A2 is either abandoned or explicitly declared a
  pre-registered one-shot LB bet (never a locally-validated improvement).

## 5. Falsifiable checkpoints / stop rules

* B (narrowed) stands unless A0 surfaces a bounded lever with a real Δscore ceiling.
  The LB is **not** the falsification mechanism (it is secondary evidence); the
  scorer-aware A0 audit is.
* A0 self-terminates to "B final" if no edge sub-target and no division signal
  clears its ceiling — zero GPU spent.
* A1 self-terminates if ~12 events under a frozen-algorithm constraint cannot
  distinguish a realistic improvement from zero.
* No phase advances without a versioned `CONSENSUS` and (for any launch) fresh
  Codex admission, smoke, and budget gates. Six protected GPU hours and ≥10% weekly
  allowance preserved throughout.

## 6. Risks and honest unknowns

* **A2 may still fail even with A0/A1 green:** test-movie division density/topology
  is unknown; 2 specimens is thin. A framework A2 without new labeled specimens
  stays a high-risk one-shot bet, not a validated improvement.
* **Candidate-generation may be the real blocker:** if A0 confirms the geometry
  rarely nominates true sites, a fix needs a learned proposal (real modeling + GPU);
  A0/A1 gate that investment.
* **Opportunity cost:** A0/A1 are cheap (analysis); A2 is not. A0 is the
  circuit-breaker.

## 7. Review status

* **Codex challenge v1 → REVISE** (`exp057_post_null_codex_challenge_v1.md`). Two
  load-bearing claims independently verified wrong by Claude and retracted
  (edge-denominator exhaustion; 6-run pooled independence).
* **Codex challenge v2 → REVISE**, but the three **substantive** items CLOSED
  (B narrowed; A0 audit added; A1 reframed feasibility-only) and Codex called the
  revised structure "otherwise sound." Two **documentation/provenance** items were
  left open and are now addressed in this v2.1:
  - diagnostic §4/§6/§6a/§7 conclusions marked **inline as withdrawn/corrected**;
    the pooled "confirmation" removed from this proposal's valid inputs;
  - a frozen provenance manifest for the invalid analysis
    (`docs/research/scripts/div_separability_pooled_INVALID_manifest.json`: 6 exact
    paths + SHA256s + 3 distinct-hash groups + captured output);
  - A0 fork population made metric-faithful (enumerate/GT-map predicted forks
    first; 8 aggregate FP ≠ 8 distinct false sites); A0 nulls phrased as "no
    actionable evidence," not "no signal exists."
  - Remaining Codex note: `STATE.json` still points `active_experiment` at terminal
    exp_055. This is retained by existing controller convention (no new experiment
    record exists yet); it will be repointed when the A2 experiment record is
    created. This is a deliberate, documented deferral, not an oversight.
* **Status: substantively at CONSENSUS on the B→A0→A1→A2 structure; A0 is
  analysis-only.** A confirming 3rd Codex pass is optional. No GPU/launch/LB is
  implied; A2 needs its own experiment record + fresh Codex admission + smoke +
  budget gates.
