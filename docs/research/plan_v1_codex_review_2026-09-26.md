# Codex review of PLAN v1 - 2026-09-26

Read-only review of the 2026-09-26 v1 plan rewrite. Verdict REVISE. Every checkable claim was
verified against the repo before acceptance; three were hard errors in the plan (watchdog
arithmetic, the ~80 supervision forecast, and an unsupported causal claim about y3uanm).
PLAN.md v2 is the response. Review preserved verbatim below.

---

## Summary

**REVISE.** This is a legitimate low-probability experiment wrapped in an overstated risk-reduction story. The selected 0.953 makes exploration defensible; it does not make the proposed controls decisive. I would stop the competition arc unless a short, zero-GPU feasibility check supplies new evidence.

## What is right

- Keeping x138 selected, separating submission authorization from local success, and prohibiting automatic promotion are correct.
- Testing real decoder execution before substantial investment is sensible.
- Sparse supervision is a serious limitation, and the plan acknowledges low expected value.
- Fixed movie roles, parent-metric comparison, graph audits, and a calendar stop are useful foundations.

## What is wrong

1. **“Transport first” is contradicted by “launch B in parallel.”** If A fails, the export expenditure is already committed. More importantly, A tests visible-run integration, not hidden-rerun transport—the failure that actually killed exp061. Its visible run also passed. Calling A the cheapest test of the most dangerous unknown is rationalisation.

2. **Neutral-model byte parity is neither sufficient nor well-defined.**
   - In the [actual configuration](E:/Project/Biohub_CellTracking/configs/exp_067_temporal_joint_lineage.json), `tau0 = mu0 = beta0 = 0`. Zero logits therefore produce a tied objective, **not a uniquely optimal parent graph**. Correct decoding can change edges.
   - [Inference](E:/Project/Biohub_CellTracking/scripts/exp067/infer.py) returns parent edges for empty candidate pools and scoring deadlines; [the solver](E:/Project/Biohub_CellTracking/scripts/exp067/decode.py) also reverts failed components or whole movies. A broken or ineffective decoder can reproduce the parent perfectly.
   - CSV ordering, float serialization, or upstream nondeterminism can break byte parity without a transport defect.
   - Visible byte identity cannot certify hidden-input execution. The superseded plan explicitly recognised this.

3. **Forty positives is an engineering cutoff, not a defensible sufficiency threshold.** No learning curve, effective sample-size argument, or held-out precision calculation supports it. Forty events concentrated in a few movies differ materially from forty independent movies. Count distinct positives **after candidate generation and window filtering**, plus annotated negatives and movie/prefix coverage. The current executable floor remains three.

   The ~80 forecast is optimistic even before distribution shift: six training movies yielded five usable positives; approximately 54 training movies at that yield imply **45**, before further geometry losses. The existing sample was label-enriched, so extrapolating its raw mother density to new movies is especially weak.

4. **The split is not sufficiently specified to certify leakage freedom.** Which 64 movies? How many per prefix? What eligibility filter, indexing origin, prefix counter reset, and missing-file policy? Are movies independent acquisitions or overlapping crops? Preserve existing roles, but freeze an explicit manifest and acquisition grouping. Within-prefix holdout also leaves the documented backbone-overlap uncertainty intact.

5. **The scientific inference is too strong.** Thirty unchanged division counts and cx03’s registered null justify closing those tested interventions—not proving all post-processing exhausted or identifying supervision as the sole binding constraint. Matching annotated nodes does not prove the decoder contains useful missing-division hypotheses.

   The synthetic-label analogy is weaker still: an author’s 0.956 does not establish that these published training notebooks caused that score. The plan acknowledges that distinction, then violates it by saying the author “reached 0.956” through this method.

6. **Execution arithmetic is inconsistent.** At the plan’s rate, `24 × 227 = 5,448 seconds`, already beyond the 5,400-second watchdog. Runtime variation needs margin. “Eight existing plus 64 new” also does not explain three new 24-movie exports. Stages C/D lack a complete runtime and resource budget.

## Required changes

- Replace immediate launches with an explicit successor protocol: consensus, experiment-specific admission PASS, snapshot smoke, reservations, and launch authorization. The export-only waiver does not extend to training or TEST decoding.
- Start with cached TRAIN graphs: establish candidate-restricted division headroom under the preserved scorer, then exercise decoding with both a **uniquely parent-preserving control** and a **forced-change positive control**. Require scoring/solver receipts and reject unintended fallback.
- Treat historical CSV SHA equality as a reproducibility check, not the sole decoder or transport gate.
- Freeze the exact split manifest, post-filter supervision counts, training schedule, and one-shot evaluation rule. Specify minimum held-out information, division TP/FP/FN, aggregate weighting, and per-prefix regression limits.
- Either gate B on A or honestly call this parallel speculative spending. Resize shards with watchdog margin and budget the entire path.
- Preserve UNKNOWN-label masking, provenance checks, separate LB authorization, and no-promotion rules explicitly. **No explicit leakage or promotion waiver appears, but “launch immediately” omits required admission gates.** Reconcile the three-per-day standing instruction with the recorded later policy change rather than relying on the platform-cap sentence.

## Better alternative

**Timebox one CPU-only feasibility audit, then default to stopping.** Use existing training exports to determine whether feasible candidate edits can recover missed divisions under the actual scorer. This is diagnosis, not deployable oracle performance. If headroom is absent or decoding cannot reliably enact controlled changes, more labels will not rescue this architecture.

If the user still wants a competition probe, the superseded plan’s V1284-head ablation is a more concrete, smaller engineering bet than exp067. It has unknown upside and needs separate authorization and gates; cx03’s null does not dispose of it.

Otherwise, bank the export and leave GPU hours unused. That is preferable to spending the deadline validating a reassuring but non-discriminating control.

VERDICT: REVISE
