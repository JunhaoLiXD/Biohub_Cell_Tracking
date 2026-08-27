> **Superseded by `docs/v9_division_aware_tracking_plan.md`** (the authoritative plan). This
> document remains the detailed spec for **Phase 1** (post-link learned division recovery) of v9.

# Learned Division Recovery — Design & Implementation Plan (v2)

**Goal:** raise the `division_jaccard` term of the competition metric on top of the frozen
public-0.912 pipeline (`references/biohub-cell-tracking-two-seeds-logit-blend.ipynb`) **without
retraining the detector or the transformer**, and while spending the limited training compute
only where a cheap, no-training audit has already proven headroom exists.

**Metric:** `score = adjusted_edge_jaccard + 0.1 * division_jaccard`. The division term is
currently almost entirely untapped (local `div_J ≈ 0.040`, contributing `+0.004`), so most of the
`0.1` weight is available. This is the largest structural lever left after the detector line
(~0.844) and Trackastra linking both closed, and after the `motion_relink` learned-bonus sweep
saturated (~0.912, sub-threshold).

**This plan is deliberately gated:** no model is trained until a *no-training oracle audit* shows
the achievable `Δscore` clears a bar. The compute budget goes to (a) one cached inference pass of
the frozen pipeline over the train set, and (b) a tiny CPU classifier — never to per-candidate
metric recomputation or a from-scratch model.

---

## 1. Why this is the cleanest experiment

Everything needed already exists in the pipeline; the change is surgical, CPU-only, and
falsifiable locally before any LB slot.

1. **Injection point exists.** `add_safe_divisions_postlink` (v8 local-eval Cell ~2872) is the
   *only* division source in the final output (the ILP's native divisions are flattened away by
   `motion_relink`'s strict 1:1 relink). It already enumerates candidate triplets
   `(mother M, existing child D1, orphan D2)` under geometric gates. We replace its ranking rule
   `score = parent_dist + 0.15 * sister_dist` (+ fixed frac caps) with a learned probability.

2. **Feature source exists.** An auxiliary center-detection model (`deepcenter`) is already
   loaded; `deepcenter_score_point(dataset, t, point, ...)` (Cell ~2257) returns heatmap
   confidence at any coordinate/frame — the appearance signal for "mother rounds/brightens before
   division."

3. **Local scorer exists.** The support pack's `division_metrics.py` computes `div_J` TP/FP/FN.
   Baseline (exp0, geometric safe-div) = **TP 3 / FP 45 / FN 26 = 0.040**.

> **Correction vs the first draft — this edit is NOT orthogonal to `adjusted_edge_jaccard`.**
> The earlier claim that division edges are "edge-safe because they land on orphans" is wrong on
> the *dense hidden GT*. This is the documented Version 7 landmine: an added `M→D2` whose two
> endpoints both match annotated GT nodes that are *not* joined by a GT edge becomes an edge FP
> (v2+v3 fusion went LB 0.827 → 0.822). Locally-sparse GT hides this. Therefore every candidate
> and the final edit set must be scored on **both** components: `Δscore = Δadj + 0.1·Δdiv_J`.

---

## 2. Exact division metric (what any candidate must be judged against)

From `references/biohub-tracking-support-pack/repo/src/biohub_tracking/division_metrics.py`:

- **TP** — a predicted division node (out-degree ≥ 2) matched to a GT dividing node (within the
  7 µm gate), **and** whose matched prediction spans both the GT *pre-division single-node stage*
  (≥1 matched node) and the *post-division two-node stage* (≥2 matched nodes at the same
  timepoint), all in one weakly-connected component. Bipartite max-matching pairs each pred fork
  with at most one GT division.
- **FP** — a predicted division node whose matched GT node is matched but **not** dividing (the
  GT node must have ≥1 child; a childless matched GT node = end of annotation, excluded from FP).
  Forks on *unmatched* predicted nodes are not counted.
- **FN** — GT divisions not recovered.
- `div_J = TP / (TP + FP + FN)`.

**Consequences:** it is both a precision problem (cut the 45 FP) and a recall problem (TP 3 of
~29). **Daughter detection recall is a hard ceiling on `div_J`** — TP needs both daughters
detected and matched, so no post-hoc method can recover a division whose daughter was never
detected. Note the metric allows some slack (±1-frame / lineage-component coverage) that a strict
"both daughters match within 7 µm this frame" test does not — see §5 on labeling.

---

## 3. Methodology — a no-training oracle gate, then a tiny classifier

The expensive mistake would be to build a full conflict-aware division optimizer, or to train a
model, before knowing the ceiling. So the plan front-loads a **compute-free upper-bound audit**
and only escalates if it pays.

### 3.1 Compute budget (explicit, because it is limited)
- **One cached inference pass** of the frozen pipeline over the train split, dumped to disk (graph
  state just before `add_safe_divisions_postlink`, plus per-node features). This is the only heavy
  cost and it is *inference*, not training.
- **Classifier = `sklearn.ensemble.HistGradientBoostingClassifier`** on ~151 positives: seconds
  on CPU, no GPU, and it ships in the Kaggle base image → **zero new offline wheels**.
- **No per-candidate metric recomputation at training scale** (see §5) — that is reserved for the
  bounded oracle audit and for hard-negative mining, not for labeling every example.

### 3.2 Why a *cheap* oracle first, not the full conflict-aware oracle
A full oracle — enumerate top-k actions per mother, run the official scorer per candidate,
optimize a conflict-aware set — is essentially a second mini-ILP over division edits and costs as
much as the classifier it is meant to justify. Instead:

- **Step 1 (cheap upper bound, ~half a day, no training, no set optimization):** for every GT
  division whose *both* daughters were actually detected, add the oracle-correct `M→D2` edge and
  recompute `div_J` and `Δadj` **once** per candidate family. This yields the two numbers that
  decide everything: the **perfect-classifier `div_J` ceiling** and its **`adj` cost**, per
  specimen. No conflict-aware machinery is required to read a ceiling.
- The full conflict-aware oracle is built **only if** the cheap upper bound clears the gate.

### 3.3 Decision gates (relative + per-specimen, not LB-calibrated absolutes)
Because the frozen feature extractors have seen all 199 train videos, absolute local scores are
optimistic. Gates are therefore expressed as **local `Δscore` with a discount, and consistency
across both specimens**, never as raw thresholds treated as LB values:

- If the cheap upper bound gives orphan-only (family A) `Δscore` that is not clearly positive on
  **both** `44b6` and `6bba`, do not train — the injection point is spent.
- If A is weak but adding "steal a weak child" / "joint daughter selection" (families B/C, §4)
  lifts the ceiling materially and consistently across specimens, escalate to the full oracle +
  classifier.
- If even B/C is weak, stop and redirect compute to multi-frame tracklet association instead.

---

## 4. Candidate families (the recall ceiling lives in B/C, and so does the risk)

- **A — orphan-only (current).** `M` has one child `D1`; `D2` has no incoming edge; action = add
  `M→D2`. Lowest `adj` risk, but bounded by how often the true daughter is left an orphan.
- **B — steal a weakly-assigned child.** Allow a `D2` that already has parent `P` when `P→D2` is
  weak (low learned confidence / large motion residual) and `M→D2` evidence is stronger. Action is
  **atomic and scored as a whole**: remove `P→D2`, add `M→D2` (and account for `P` possibly
  becoming a dead-end).
- **C — jointly select both daughters.** Do not assume `D1` is correct. For `M`'s next-frame
  top-k candidates, enumerate {no change, single continuation, replace continuation, division,
  replace + division}. Only this reaches divisions where `motion_relink` already mis-assigned one
  or both daughters.

> **Key tension:** A is low-`adj`-risk but low-recall; B and C are the only way to break the
> recall ceiling, but they **modify existing edges → they directly move `adj` and are exactly the
> Version-7-style edits that can add FP edges on the dense hidden GT.** The oracle must therefore
> treat **per-specimen `Δadj` as a first-class output**, not just `div_J`. The real operating
> point sits between A and B/C.

---

## 5. Labels, learning target, and features

### 5.1 Labels — cheap positives, counterfactual only where it earns its cost
- **Training positives:** exact GT-division triplets, relaxed to ±1 frame to match the metric's
  slack — i.e. `M` matches a GT divider and both daughters match its GT daughters within the gate.
  Rationale: a true division with both daughters detected is almost always metric-positive to add,
  so this cheap label is low-noise for the *positive* class and needs **no per-example scorer
  call**. This is the deliberate compute saving.
- **Counterfactual `Δscore` labels** (apply action → rescore → record `Δadj`, `Δdiv_J`) are used
  **only** for (a) the bounded oracle audit and (b) hard-negative mining — not to label every
  training row. Per-edit metric-positivity is combinatorial (one pred fork can claim only one GT
  division), so per-example counterfactuals are both expensive and only approximate; spending the
  budget there is poor ROI.

### 5.2 Learning target
Predict `P(candidate edit is metric-positive)` and **rank the mutually-exclusive actions within
one mother/child group**; evaluate on the final graph's `adj + 0.1·div_J`, never on classifier
AUC alone.

### 5.3 Features (tabular → GBDT)

| Group | Features |
|---|---|
| Geometry | `parent_dist(M,D1)`, `parent_dist(M,D2)`, `sister_dist(D1,D2)`, split angle `∠D1-M-D2`, z-vs-xy anisotropic components, symmetry of the two daughter displacement vectors, density-normalized distances |
| Appearance | `deepcenter` heatmap **and its neighborhood shape** at `M`,`D1`,`D2` — peak-height history over `t-2..t+1`, half-maximum width, radial symmetry/concentration, 3D Laplacian/Hessian (single-point confidence alone does not express rounding) |
| Learned-edge evidence | see §5.4 — requires re-plumbing |
| Temporal | `M`'s tracklet length, velocity, acceleration, curvature; whether `M` was recently born; motion residual of `D2`'s current incoming edge (for family B) |
| Competition | number of competing parents/children within the gate; feature deltas of the split action vs the no-change action |

### 5.4 The `edge_prob` feature must be re-plumbed (implementation gap fixed)
The first draft listed transformer `edge_prob(M→D2)` as an available strong feature. **It is not
available from the solution graph.** The transformer scores candidate edges *before* the ILP; the
saved `.geff` holds only the ILP solution, and because `D2` is an orphan, `M→D2` was generally
*not* selected, so its score is gone (safe-div even writes `edge_prob=None`). To use it we must,
at inference time, **export the pre-ILP candidate edge table and cache the adjacent-frame
logits/probabilities**, keeping: raw logit, softmax probability, candidate rank, top-1/top-2
margin, and score difference vs the current parent/child. Softmax probability drifts with
candidate count and density, so never rely on it alone — the rank/margin/logit are the robust
carriers.

---

## 6. Cross-validation (two specimens is the real domain axis)

- **Outer = leave-one-specimen-out** (`44b6` vs `6bba`) as a domain-shift stress test; the ~125:26
  division skew makes this the generalization test that matters for the hidden set.
- **Inner = cross-fit within the training specimen** grouped by video / crop / density / time.
- **Threshold `τ` and any cap are chosen only on inner calibration folds**, never on the held-out
  specimen.
- **Always report both specimens separately.** Trust experiment deltas and per-specimen
  consistency over absolute local scores (leakage inflates absolutes).

---

## 7. Decision & caps (keep a prob-ranked cap in v1)

Add `M→D2` iff `P > τ`, but **retain a relaxed, probability-ranked frame/global cap in the first
version.** A probability threshold alone does not defend against calibration shift, sparse-label
false negatives, or hidden-test density shift. Only widen the cap after cross-fitted evaluation is
stable on both specimens.

---

## 8. Comparison with the original framework

| Dimension | Original (0.912) | With learned division (proposed) |
|---|---|---|
| Division source | `add_safe_divisions_postlink`, pure geometry (`parent_dist + 0.15·sister_dist`, frac caps); heatmap used only as a veto | Same/extended candidate enumeration; ranking/gating by a learned `P(metric-positive edit)` GBDT |
| Candidate set | orphan-only (A) | A + optionally B (steal weak child) + C (joint daughter selection) if the oracle justifies it |
| Features | 3 geometric distances + 1 heatmap max | geometry + heatmap **shape/history** + re-plumbed edge logit/rank/margin + tracklet motion + competition counts |
| Objective | geometric score ranking | `Δscore = Δadj + 0.1·Δdiv_J`, both components rescored |
| Training | none | HistGBDT on ~151 positives; leave-one-specimen-out CV; **CPU-only, seconds** |
| Compute | n/a | one cached inference pass + a tiny CPU classifier; no GPU, no new wheels |
| `div_J` target | 0.040 | 0.20 → `+0.016`; 0.35 → `+0.031` (net on `score`) |
| `adj` risk | Version-7 landmine, unmodeled | explicitly scored per specimen; B/C flagged as the risk carriers |

---

## 9. Honest ceilings & realistic contribution

- **Daughter detection recall caps `div_J`** → realistic `div_J ≈ 0.20–0.35`, i.e. `score`
  `+0.016` to `+0.031`. Optimistically this pushes `0.912 → ~0.943`, **not to 0.95 on its own.**
- Reaching 0.95 needs division recovery **plus** better association/detection. The larger
  architectural opportunity remains a tracklet-conditioned model trained on the detector's real
  proposal distribution (unmatched/duplicate detections as hard negatives) that jointly models
  continuation, no-match/death, and division. Learned division is the cheap, well-scoped first
  cut; if its oracle fails, redirect the limited compute straight to that association model.
- **Orphan limitation:** family A alone is bounded by how often the true `D2` is left an orphan by
  `motion_relink`'s 1:1 relink; B/C exist to break that but carry the `adj` risk above.
- **Incomplete annotation → noisy negatives:** draw negatives from well-annotated neighborhoods or
  use a PU-learning framing.

---

## 10. Step plan (gated; no training until Step 2 passes)

1. **Export + cheap oracle (no training).** One cached inference pass to the pre-safe-div graph;
   dump triplets + features + labels. Compute the perfect-classifier `div_J` ceiling and `Δadj`
   cost for family A, then B/C, **per specimen**. Read: is there a consistent positive `Δscore`?
2. **Gate.** Apply §3.3 gates. If A/B/C all fail, stop and pivot to tracklet association.
3. **Train the GBDT** (CPU) on cheap triplet positives + mined hard negatives; leave-one-specimen-out
   CV; report per-specimen precision/recall, post-swap `div_J` vs 0.040, and confirm `adj` holds.
4. **Tune `τ` + prob-ranked cap** on inner folds; pick the operating point; then, and only then,
   consider one LB submission.

---

## 11. Code anchors (v8 two-seeds local-eval notebook)

- `add_safe_divisions_postlink` — Cell ~2872 (injection point; only division source; writes
  `edge_prob=None`).
- `deepcenter_score_point` / `deepcenter_accept_repair_point` — Cell ~2257 / ~2285 (heatmap
  feature access).
- `motion_relink_edges` — Cell ~2319 (why ILP-native divisions are discarded; do not touch).
- `filter_output_graph` — Cell ~3175 (post-link ordering; safe-div is called from here).
- Pre-ILP candidate edges — must be exported before the ILP solve (§5.4); not in the saved graph.
- Division metric — `references/.../biohub_tracking/division_metrics.py`
  (`evaluate_divisions`, `match_divisions`, `count_matched_pred_divisions`).
- Local scorer output — v8 scoring cell ~3715 (`adj`, `div_J` per-embryo).

> Note: the support pack (`references/`) is gitignored and not ours to redistribute. This plan
> describes our design built on top of it and references its functions by role; it does not copy
> pack source.
