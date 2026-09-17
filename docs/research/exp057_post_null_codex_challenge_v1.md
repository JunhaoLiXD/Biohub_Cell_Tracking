# Codex Challenge v1 — Post-exp_057 "B then A" Strategy

Reviewer: Codex (gpt-5.6-sol), read-only sandbox, 2026-09-16.
Target: `docs/research/exp057_post_null_strategy_proposal.md` (v1) and
`docs/research/exp057_division_bottleneck_diagnostic.md`.
Raw transcript preserved at session tool-results `b7e3moehm.txt`.

## Verdict

**VERDICT: REVISE** — (1) retract the erroneous edge-exhaustion and
six-run-independence claims; (2) add an exact-0.944-lineage zero-GPU edge/division
A0 audit; (3) narrow B to the two tested branches; (4) redefine A1 as
feasibility-only unless new independent specimens exist; (5) preserve reproducible
pooled-analysis artifacts and reconcile state/provenance.

Codex agreed the **operational** core of B is justified: stop spending GPU on
EMA/joint-repair retuning; retain `repro_048` (0.944) as the best verified LB
parent. It rejected the broader claims as unsupported.

## Findings (Claude's independent verification in brackets)

1. **The edge-denominator argument is factually wrong.** The proposal claimed
   adjusted-edge has "hundreds of thousands of edges per movie" so changes round
   away. Actual train16 scored union = **10,055 edges** (TP 9137 / FP 481 / FN
   437); 1-edge Jaccard scale ≈ 0.0001. Only **8 wrong-association edges** exist —
   a small, causally-specific class that could move a 3-decimal LB if corrected
   cleanly. Two LB nulls do **not** prove edge/detection exhaustion; a 3714-edge
   symdiff can be score-neutral because changes are unmatched/compensating/in
   irrelevant regions. **[VERIFIED by Claude: scored_union=10055, wrong_assoc=8.]**

2. **Cheap division diagnostics dismissed prematurely.** The causal audit records
   only *retained* safe_division edges, so it cannot show which earlier gate
   rejected the missing GT sites — "geometry almost never nominates true sites" is
   stronger than the artifact supports. Also a **directionality** issue: diag_013's
   exclusive-label AUC gives DeepCenter ≈0.848 in the **low-score** direction (low
   score ⇒ true), N=2. So "no signal" is wrong; the defensible statement is
   "an apparent *reversed* signal, untrustworthy at N=2." Since the production gate
   accepts *high* scores, it may be **anti-selecting** useful repairs — worth a
   direct exact-lineage check.

3. **The six-run pooled result is pseudo-replication.** diag_013/014/019 causal
   files are byte-identical; repro_036/exp_035 are another identical pair; all
   contain the **same two** mapped-positive sites (both 6bba). Pooling does not
   raise the positive experimental unit above 2. Also the audit runs report
   `deepcenter_safe_div_veto: false`, whereas val_049 (0.944) has the veto enabled
   at 0.25 — different population. The pooled script was also not preserved.
   **[VERIFIED by Claude: 3 distinct file hashes across the 6, same 2 sites.]**

4. **Division FP semantics overstated.** `FP = max(0, matched_pred_divisions − TP)`
   mixes two matching procedures; the 8 FP are not proven to be 8 forks on
   continuing non-dividing cells (5 clearly misplaced in division-negative videos,
   3 need direct mapping). `3/11` is not clean event-site precision. Per-event
   leverage: FN→TP ≈ +0.005; division_jaccard 0.15→0.30 ≈ +0.015 (this part
   matched the proposal).

5. **A1 cannot manufacture a trustworthy substrate.** With 2 specimens,
   cross-specimen gives 2 high-variance evals (~5 and ~7 events); if both
   directions inform any decision, nothing is held out. LOVO holds out only
   post-processing calibration, not model generalization (frozen models already
   saw these videos). Event-only bootstrap omits the FP-generating population →
   anti-conservative CIs. A trustworthy framework-selection gate probably needs
   **new labeled specimens**; otherwise A2 stays a pre-registered one-shot bet.

6. **Governance/provenance.** Do not call 0.944 "reproducible" (`metrics.json`
   sets `reproducible: false`; models saw the validation videos). "B falsified only
   by LB movement" wrongly makes the LB the falsification mechanism (LB is
   secondary evidence). Preserve the pooled script + inputs/hashes. Reconcile
   `STATE.json` (still lists exp_055 as `active_experiment` while exp_057 is
   closed).

## Claude's disposition

Accept the REVISE. Both load-bearing factual claims (edge denominator; pooled
independence) were independently verified as wrong. See
`exp057_post_null_strategy_proposal.md` v2 for the revised plan (narrowed B,
zero-GPU A0 audit inserted, A1 reframed as feasibility-only, governance fixes).
