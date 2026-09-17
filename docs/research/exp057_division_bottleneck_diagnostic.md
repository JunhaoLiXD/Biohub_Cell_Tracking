# Division Bottleneck Diagnostic (post exp_057)

Record type: zero-GPU diagnostic / strategy input
Author: Claude Code. Date: 2026-09-16.
Status: analysis only. No experiment, launch, promotion, or LB submission is
authorized by this document. It exists to decide **whether and how** a division
strategy is worth proposing, before any GPU is spent.

## 0. Why this diagnostic exists

Two consecutive causally-isolated edge/motion-layer changes moved the graph but
produced **zero Public LB movement**:

| Experiment | Layer touched | Graph change | Public LB |
| --- | --- | --- | --- |
| exp_055 | post-smoothing joint edge repair | 500 actions/video, full graph | 0.942 == repro_041 0.942 (Δ 0.000) |
| exp_057 | motion EMA (velocity smoothing) | 3714 canonical-edge symdiff | 0.944 == repro_048 0.944 (Δ 0.000) |

The edge layer is a dead end for the LB (see §4 for *why* — denominator scale).
This diagnostic characterizes the one lever every error decomposition has pointed
at instead: **division**.

## 1. The scoring mechanic (exact, from the frozen scorer)

`biohub_tracking/metrics.py` and `division_metrics.py`:

```
score = adjusted_edge_jaccard + SCORE_DIVISION_WEIGHT * division_jaccard
SCORE_DIVISION_WEIGHT = 0.1
division_jaccard = TP / (TP + FP + FN)     # micro-averaged over the whole split
```

Verified on val_049 (0.944-source train16): 0.9160696 + 0.1·0.15 = 0.9310696 ✓.

Division event counting (`evaluate_divisions`, `max_distance = 7.0 µm`):

* **TP** — a GT division is recovered iff the prediction has a fork (out-degree≥2)
  whose matched nodes cover the pre-split (one-node) stage **and** ≥2 daughter
  lineages, all in one weakly-connected component; bipartite-matched 1:1 so one
  pred fork cannot be credited to several GT divisions.
* **FN** — GT divisions − TP.
* **FP** — `matched_pred_divisions − TP`, where `matched_pred_divisions` counts
  pred forks that (a) matched a GT node within 7 µm **and** (b) that GT node has
  ≥1 child. **A pred fork on a real, continuing cell that is not a GT division is
  an FP; a pred fork that matches nothing, or matches an annotation-terminal GT
  node, is NOT counted.**

This FP rule is the crux: FP measures **mis-placed forks on real cells**, not
sheer over-production.

## 2. The state of division on the 0.944 lineage (val_049, train16)

Aggregate: **TP/FP/FN = 3 / 8 / 9**, `division_jaccard = 0.15`, contributing only
**0.015** of the 0.1 the term can supply.

Per-video (from `experiments/val_049_public_0944_train16/artifacts/validator_results.csv`):

| specimen | video | TP | FP | FN | GT div (TP+FN) |
| --- | --- | --- | --- | --- | --- |
| 44b6 | c15fded2 | 0 | 0 | 0 | 0 |
| 44b6 | 7a302da0 | 0 | 0 | 1 | 1 |
| 44b6 | 1d530831 | 0 | 1 | 0 | 0 |
| 44b6 | 551a5dba | 0 | 1 | 0 | 0 |
| 44b6 | 7e557709 | 0 | 0 | 0 | 0 |
| 44b6 | 2a2eff9f | 1 | 1 | 0 | 1 |
| 44b6 | c50204e0 | 0 | 1 | 2 | 2 |
| 44b6 | aaf8b0ea | 0 | 0 | 1 | 1 |
| 6bba | fe670320 | 0 | 0 | 2 | 2 |
| 6bba | 55c70843 | 0 | 1 | 0 | 0 |
| 6bba | 372c8cb8 | 0 | 0 | 0 | 0 |
| 6bba | 337b1b3a | 1 | 1 | 1 | 2 |
| 6bba | ef7b4f7e | 0 | 0 | 2 | 2 |
| 6bba | 80d12824 | 1 | 0 | 0 | 1 |
| 6bba | 283bf9f1 | 0 | 1 | 0 | 0 |
| 6bba | 0c7fa718 | 0 | 1 | 0 | 0 |
| **agg** | | **3** | **8** | **9** | **12** |

## 3. Central finding — division is MIS-LOCALIZED, not under-produced

* GT divisions total **12**. Pred forks landing on a real continuing cell
  (TP+FP) total **11**. So the pipeline produces roughly the **right volume** of
  divisions — it is **not** starved by the caps.
* Of those ~11 forks, only **3** coincide with an actual GT division:
  **recall 3/12 = 25 %, on-cell precision 3/11 = 27 %.**
* **5 of the 8 FP videos have zero GT divisions** (44b6 1d530831, 551a5dba; 6bba
  55c70843, 283bf9f1, 0c7fa718): the pipeline invents a division where none
  exists. Where a TP does occur it usually drags an FP with it (2a2eff9f 1/1,
  337b1b3a 1/1); only 80d12824 is clean (1/0).

**Interpretation.** The DeepCenter `safe_division` gate fires about as often as it
should, but on **the wrong cells** — its choices are close to uncorrelated with
true division sites. This directly falsifies the naïve fixes:

* Loosening the frame/global fraction caps (`0.0076`/`0.00375`) or lowering
  `safe_div_threshold` → more forks in the same wrong places → **more FP, not more
  TP.**
* Tightening them → fewer FP but risks the 3 TP; upside ≤ +0.010 proxy and fragile.

A real division gain requires **better candidate scoring/localization**, not a
different operating point on the same mis-localized detector.

> **CORRECTION (2026-09-16, after Codex challenge v1).** §4 below overstates the
> edge case and §6a is methodologically invalid. Verified facts: the train16
> scored edge union is **10,055 edges** (not "hundreds of thousands per movie"),
> and there are only **8 wrong-association edges** — a small, specific class that
> *could* move a 3-decimal LB. The two LB nulls prove only that *those two*
> interventions did not transfer, not that the edge/detection layer is exhausted.
> §6a's "6-run pooling" is pseudo-replication (3 distinct files, same 2 positive
> sites, `safe_div_veto=false`), so it does not escape N=2 and its AUC is
> withdrawn. See `exp057_post_null_codex_challenge_v1.md` and the v2 strategy
> proposal; the A0 audit supersedes the conclusions flagged here.

## 4. [WITHDRAWN] Why edges can't move the LB but division might

> **WITHDRAWN (Codex challenge v1).** The premise below — that the edge
> denominator is so large that edge changes cannot move the LB — is false (scored
> union ~10,055 edges; 8 wrong-association edges could move a 3-decimal LB). Retained
> for history; superseded by A0 in the v2 strategy proposal. Do not cite.

`adjusted_edge_jaccard` is micro-averaged over **hundreds of thousands** of edges
per movie. exp_055's 500 actions/video and exp_057's 3714-edge symdiff are ~10⁻²–
10⁻³ of the denominator → invisible at the LB's 3-decimal display. That is exactly
what we observed twice.

`division_jaccard` has a denominator of **~12–20 events**. One event is worth
≈0.05 of the Jaccard, ≈**0.005** of the score after the 0.1 weight. A handful of
corrected events (jaccard 0.15→0.30) is **≈+0.015 of score** — enough to render
0.944 → 0.945/0.946 at 3 decimals **if it transfers**. Division is the only lever
with per-change LB leverage large enough to survive rounding.

## 5. The transfer problem is worse for division, not better

Everything above is on the **discredited train16 proxy**. Two independent reasons
for extra caution:

1. **We already saw the proxy mis-rank at the LB.** On train16 the 0.944 source
   (val_049, div 0.15, score 0.9311) scores *below* the 0.941+EMA parent
   (repro_041, div 0.20, score 0.9387), yet on the **LB the 0.944 source wins**
   (0.944 > 0.942). The proxy's division/score ordering is already known to
   disagree with the LB.
2. **Tiny event count.** Any threshold/geometry tuned on **12 GT divisions across
   2 training specimens** is extreme overfitting; the 4 held-out test movies have
   unknown, likely different, division density and topology. The two prior
   proxy→LB transfer failures were on far larger-denominator signals — a
   12-event tune is more fragile, not less.

## 6. [PARTLY WITHDRAWN] The separability question — reversed weak signal at N=2

> **WITHDRAWN/CORRECTED (Codex challenge v1).** "No signal / doubly hopeless" is
> too strong. The defensible reading: DeepCenter shows an *apparent reversed*
> signal (low score ⇒ true division) at N=2, i.e. the gate may be **anti-selecting**
> useful repairs — untrustworthy at this sample size, to be tested exactly in A0.
> The §6a pooled confirmation is fully withdrawn (pseudo-replication). The "gate
> almost never nominates true sites" claim relies on retained-candidate audits only
> and is not established. Superseded by A0.

The decisive GPU-free question is: **does any signal available at the
`safe_division` gate separate true divisions from false ones?** An existing causal
audit already tested this on the same 16 train16 videos with the same DeepCenter
epoch-2 checkpoint:
`experiments/diag_013_train16_deepcenter_causal_calibration/artifacts/deepcenter_causal_score_analysis.json`
(1130 candidate rows; causal one-edge-ablation labels).

Findings:

* **The DeepCenter safe-division score itself does NOT separate.**
  `auc_high_score_predicts_causal_tp = 0.44` (worse than chance in the
  "high score ⇒ true" direction); `tp-only vs fp-only AUC = 0.15`. There is **no
  threshold** that helps: `reject_all_causal_fp` needs a cutoff `> 0.853` which
  keeps **0** TP, and `preserve_all_causal_tp` keeps **23** FP. So re-thresholding
  or re-scoring on the DeepCenter confidence is **hopeless** — the gate's own
  confidence is uninformative about correctness. This is the mechanism behind the
  §3 mis-localization.
* **Two geometric features look separating — but on 2 positive events.**
  `sister_distance_um` AUC 1.0 and `geometric_rank_score` AUC 0.80, but with
  `positive_count = 2`, `negative_count = 23`. AUC on **two** positives is
  statistically meaningless and the archetype of the overfit we must avoid; the
  document itself warns the labels "are one-edge ablations and are not additive."

So the cheap lever is essentially closed: **no trustworthy signal at the current
gate separates true from false divisions.** A genuine division gain therefore
requires a *better division signal* — a learned division head or new feature —
which is a **large, framework-level change**, exactly the class we may take only
with explicit user authorization and a held-out design (never the train16 proxy).

### 6a. [FULLY WITHDRAWN — pseudo-replication] Pooled confirmation (option C)

> **WITHDRAWN (Codex challenge v1, verified by Claude).** The 6 pooled files are
> only 3 distinct byte streams sharing the SAME 2 positive sites, and run with
> `safe_div_veto=false` (not the 0.944 production gate). Pooling does NOT escape
> N=2; the AUCs below are not evidence. Provenance:
> `docs/research/scripts/div_separability_pooled_INVALID_manifest.json`. The text
> below is retained only to document what was (invalidly) computed.

To escape diag_013's N=2 weakness, the separability was recomputed over **all 6
locally available `validator_safe_division_causal_audit.jsonl` runs** (diag_013,
diag_014, diag_019, repro_036, exp_035, exp_037 — same 16 videos, identical
DeepCenter epoch-2 gate; `scratchpad/div_separability.py`). Result is stable and
worse than diag_013 alone:

* `AUC(deepcenter_score → source_maps_gt_division)` = **0.36** in every run (0.36–
  0.44 range); pooled 0.362. Below 0.5 ⇒ true-division candidates get, if anything,
  *lower* scores. Median score maps_gt=True `1.23e-7` **< ** maps_gt=False
  `2.90e-7`. **No separation.**
* `AUC(deepcenter_score → causal TP vs FP)` = **0.43** pooled (0.42–0.44 per run).
  Confirms diag_013's 0.44 was not a fluke of one config.
* **Deeper failure — candidate generation, not just scoring.** Across all 16
  videos (12 true divisions) the gate's candidate *source* maps a GT division only
  **~2 times per config**. The geometric admission (mutual-nearest orphan, t+2
  successors, distance/symmetry gates) **almost never nominates the true division
  sites in the first place.** Re-scoring is therefore doubly hopeless: no signal
  AND no candidates at the right places.

> **WITHDRAWN (Codex challenge v1).** The "lineage caveat resolved" sentence
> below is false — the 6 configs are pseudo-replicated (see §6a). The caveat is NOT
> resolved by this analysis; it is deferred to A0.

Lineage caveat now resolved: the effect is stable across 6 configs including the
EMA variants, and the `safe_division` gate + checkpoint are identical on the 0.944
line, so the conclusion carries to val_049/repro_048 with high confidence.

## 7. What is decided vs open — bottom line (CORRECTED after Codex challenge v1)

> The original §7 "Decided" list overstated three things. Corrected version below;
> the superseded text is struck through. Authoritative plan: the v2 strategy
> proposal (`exp057_post_null_strategy_proposal.md`) — B → A0 → A1 → A2.

* **Decided (corrected):**
  1. ~~The edge/motion-smoothing layer is exhausted for the LB.~~ **Only the two
     tested interventions (exp_055 joint repair, exp_057 EMA) failed to transfer.**
     The edge/detection layer is **not** proven exhausted; the 8 wrong-association
     edges are a live sub-target for A0.
  2. Division is a high-leverage term (§4 leverage math stands: 0.15→0.30 ≈
     +0.015); its 0.944-line state (3/8/9) is poor, but whether the failure is pure
     mis-localization vs. candidate-generation is **not yet established** — A0
     resolves it.
  3. ~~No trustworthy cheap lever exists.~~ **Not established.** The DeepCenter
     score shows an apparent *reversed* signal at N=2 (possible anti-selection);
     the geometric hints rest on 2 events. "No actionable evidence with current
     data" — not "no signal exists."
* **The plan (chosen by the user 2026-09-16): B → A0 → A1 → A2**, per the v2
  strategy proposal. B stops GPU on the two tested branches; A0 is a zero-GPU
  scorer-aware audit (edge upper-bounds incl. the 8 wrong-association edges +
  exact-0.944-lineage division candidate/fork audit with directionality); A1 is a
  feasibility/power audit only; A2 is a gated modeling bet.

No GPU, launch, promotion, or LB submission is authorized by this diagnostic. The
successor plan and its gates live in the v2 strategy proposal and its Codex
challenge records.
