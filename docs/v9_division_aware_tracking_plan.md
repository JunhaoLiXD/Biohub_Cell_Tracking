# v9 — Division-Aware Tracking (plan)

**One-line goal:** on top of the frozen public-0.912 pipeline
(`references/biohub-cell-tracking-two-seeds-logit-blend.ipynb`), recover cell divisions and repair
dense-field identity swaps by adding a *division-aware* layer — first a low-risk post-link
recovery module (validation), then a division-aware retraining of the edge model that targets both
the `division_jaccard` and the `adjusted_edge_jaccard` terms.

**Metric:** `score = adjusted_edge_jaccard + 0.1 * division_jaccard`. Current local
`div_J ≈ 0.040` (contributes `+0.004`), so most of the `0.1` weight is unclaimed. This is the
largest structural lever left after the detector line (~0.844) and Trackastra linking both closed,
and after the `motion_relink` learned-bonus sweep saturated (~0.912).

**Compute:** 2× T4, ~30 h available. This is *not* the binding constraint. The binding constraint
is **data: only ~151 GT division events (~84% in `6bba`).** GPU cannot manufacture division
positives, so v9 is architected to make the division signal **borrow the representation learned
from the millions of continuation edges** (a shared-trunk multi-task model), not to train a large
division-only network that would overfit 151 events.

**This plan supersedes `docs/learned_division_plan.md`**, which becomes the detailed spec for
Phase 1 below.

---

## 0. Where divisions die in the 0.912 pipeline (the two failure points v9 must fix)

Frozen 0.912 pipeline:

```
detector (thr 0.99) → node feats (32 UNet + pos-embed) → SimpleNodeTransformer (edge logits)
   → tracksdata SCIP ILP (edge=-prob, appear, disappear, division=1.0)
   → [motion_relink: Hungarian, cost = motion + 0.05·raw − BONUS·prob, REPLACES edges 1:1]
   → add_safe_divisions_postlink (geometric, only surviving division source)
   → gap-close / prune / short-track filter / linefit
```

1. **`motion_relink` flattens everything to strict 1:1** → the ILP's native division forks are
   deleted at this stage. Any effort to "get divisions right inside the ILP" is wasted while this
   stands.
2. **The only surviving division source, `add_safe_divisions_postlink`, is pure geometry**
   (`score = parent_dist + 0.15·sister_dist`, frac caps) with precision ~6% (baseline exp0:
   **TP 3 / FP 45 / FN 26 = 0.040**).

v9 must address **both**: recover divisions post-link (Phase 1) *and* stop `motion_relink` from
deleting high-confidence learned forks (Phase 2).

> **This edit is NOT orthogonal to `adjusted_edge_jaccard`.** An added `M→D2` whose two endpoints
> both match annotated GT nodes not joined by a GT edge becomes an edge FP — the documented
> Version 7 landmine (v2+v3 fusion: LB 0.827 → 0.822). Sparse local GT hides this. **Every
> candidate and the final edit set is judged on `Δscore = Δadj + 0.1·Δdiv_J`, per specimen.**

---

## 1. Architecture overview

```
frozen 0.912:  detector(0.99) → node feats → SimpleNodeTransformer → ILP → [motion_relink 1:1] → geometric safe-div → post-proc
                                     │                                        ▲                       ▲
v9 additions:                        │                          (P2) division-aware relink   (P1) learned division recovery
                 (P0) pre-ILP feature export + counterfactual oracle audit ───┴───────────────────────┘
                 (P2) SimpleNodeTransformer + division action head, retrained on REAL proposals + hard negatives
```

Three phases, gated:

- **Phase 0** — enabler (pre-ILP feature export) + no-training counterfactual **oracle audit**.
  **Mandatory gate.**
- **Phase 1** — learned division-recovery module at the post-link stage (replaces geometric
  safe-div). Fast, low-risk, GPU-light. **Mandatory gate** (proves divisions carry real, positive
  `Δscore` locally on *both* specimens before committing the 30 h).
- **Phase 2** — division-aware retraining of the edge model on the detector's real proposals with
  hard negatives + division-aware `motion_relink` + learned division score in the ILP. The main
  GPU investment; the only path past the ~0.943 division-only ceiling toward 0.95.

Phases 1 and 2 share the Phase 0 export and oracle, so no work is duplicated. Phase 1's oracle
ceiling and feature-separability numbers are priors for Phase 2 even if Phase 2 later subsumes the
Phase 1 module.

---

## 2. Exact division metric (what every candidate is judged against)

From `references/biohub-tracking-support-pack/repo/src/biohub_tracking/division_metrics.py`:

- **TP** — a predicted division node (out-degree ≥ 2) matched to a GT dividing node (7 µm gate),
  **and** whose matched prediction spans both the GT pre-division single-node stage (≥1 matched
  node) and the post-division two-node stage (≥2 matched nodes at the same timepoint), in one
  weakly-connected component. Bipartite max-matching pairs each pred fork with one GT division.
- **FP** — a pred division node whose matched GT node is matched but **not** dividing (the GT node
  must have ≥1 child; a childless matched GT node = end of annotation, excluded from FP). Forks on
  *unmatched* pred nodes are not counted.
- **FN** — GT divisions not recovered.
- `div_J = TP / (TP + FP + FN)`.

**Consequences:** both a precision problem (cut the 45 FP) and a recall problem (TP 3 of ~29).
**Daughter detection recall is a hard ceiling on `div_J`** — TP needs both daughters detected and
matched, so no post-hoc method recovers a division whose daughter was never detected. The metric
allows ±1-frame / lineage-component slack a strict "both daughters match this frame" test lacks
(see §4.3 labels).

---

## 3. Phase 0 — enabler + oracle audit (no training) — MANDATORY GATE

### 3.1 Pre-ILP feature export (enabler)
The transformer scores candidate edges *before* the ILP; the saved `.geff` holds only the ILP
solution, and because a true daughter `D2` is usually an orphan, `M→D2` was generally not selected
→ its score is gone (`add_safe_divisions_postlink` even writes `edge_prob=None`). So, at inference
time, modify the frozen pipeline to export **before the ILP solve**:

- the full **candidate edge table** with, per edge: raw logit, softmax probability, candidate
  rank, top-1/top-2 margin, and score difference vs the node's current parent/child;
- cached **adjacent-frame heatmaps** (from `deepcenter`) and **raw image patches** (t-2..t+1)
  around each mother.

Nothing is retrained here — we only persist quantities already computed. Softmax probability
drifts with candidate count/density, so downstream code uses **rank/margin/logit** as the robust
carriers, not probability alone.

### 3.2 Counterfactual oracle audit (no training)
For every GT division whose *both* daughters were actually detected, apply the oracle-correct
edit and rescore with the official scorer, over three candidate families:

- **A — orphan-only (current):** `M` has one child `D1`; `D2` has no incoming edge; add `M→D2`.
  Lowest `adj` risk, lowest recall.
- **B — steal a weakly-assigned child:** `D2` already has parent `P` but `P→D2` is weak (low
  learned confidence / large motion residual); atomic edit: remove `P→D2`, add `M→D2` (account
  for `P` possibly becoming a dead-end).
- **C — jointly select both daughters:** do not assume `D1` is correct; for `M`'s next-frame
  top-k candidates enumerate {no change, single continuation, replace continuation, division,
  replace + division}. Only this reaches divisions where `motion_relink` already mis-assigned a
  daughter.

For A, then A+B, then A+B+C, report **per specimen**: recoverable GT divisions (count & fraction),
oracle `div_J`, oracle `Δadj`, oracle `Δscore`, and a **conflict-aware** oracle (each pred fork
claims ≤1 GT division, edits that clash are resolved). Also report how much of the positive
`Δscore` depends on the higher-risk B/C families.

> **Why a cheap upper bound first, not a full optimizer up front:** the conflict-aware set
> optimization is essentially a second mini-ILP over division edits. We first read the *ceiling*
> by adding oracle-correct edits and rescoring once per family — that needs no set optimization
> and already answers "is there meat here, and does it need the risky B/C?" The full conflict-aware
> resolver is built only after the ceiling clears the gate.

### 3.3 GATE 0 (relative + per-specimen, never LB-calibrated absolutes)
Frozen feature extractors have seen all 199 train videos → absolute local scores are optimistic;
gates use local `Δscore` (discounted) and cross-specimen consistency.

- **PASS to Phase 1** if orphan-only (A) gives a clearly positive `Δscore` on **both** `44b6` and
  `6bba`, **or** A+B/C lifts the ceiling materially and consistently across specimens.
- **STOP / redirect** if even A+B+C is not consistently positive → the injection point is spent;
  send the GPU budget to multi-frame tracklet association instead (see §7).

---

## 4. Phase 1 — learned division recovery (post-link) — MANDATORY GATE

Replaces the geometric `add_safe_divisions_postlink` with a learned **Division Action Scorer**.
Fast (≈1 day), low-risk, GPU-light — the validation that divisions carry real positive `Δscore`
before the 30 h Phase 2.

### 4.1 Candidate generator
Enumerate A (and, if GATE 0 required them, B/C) candidate edits per mother as **atomic edit sets**.
Remove the fixed frac-cap recall throttle; keep a relaxed, probability-ranked cap (see §4.5).

### 4.2 Model
- **Tabular trunk → GBDT (`sklearn.HistGradientBoostingClassifier`).** GBDT is more robust than a
  neural net on ~151 positives, trains in seconds on CPU, ships in the Kaggle base image (zero new
  offline wheels).
- **Appearance branch (GPU used here):** a lightweight 3D CNN over the mother's `t-2..t+1` patch →
  a low-dimensional "division appearance embedding" (captures pre-division rounding / brightening /
  two-nuclei). Concatenated with the tabular features. Overfit control on 151 positives: heavy
  augmentation, abundant negatives, and a deliberately small embedding.

### 4.3 Labels
- **Positives (cheap, low-noise):** GT-division triplets relaxed to ±1 frame to match the metric's
  slack. A true division with both daughters detected is almost always metric-positive to add, so
  this needs **no per-example scorer call**.
- **Hard negatives:** candidates whose Phase-0 counterfactual `Δscore ≤ 0` — real, metric-defined
  hard negatives, not random ones.
- Per-example counterfactual labels are *not* used for every row (metric-positivity is
  combinatorial and per-example counterfactuals are both expensive and approximate); the
  counterfactual budget is spent on the oracle and on hard-negative mining.

### 4.4 Features
| Group | Features |
|---|---|
| Geometry | `parent_dist(M,D1/D2)`, `sister_dist(D1,D2)`, split angle `∠D1-M-D2`, z-vs-xy anisotropic components, daughter-displacement symmetry, density-normalized distances |
| Appearance | 3D-CNN embedding + heatmap peak-height history (t-2..t+1), half-max width, radial symmetry, 3D Laplacian/Hessian at `M`,`D1`,`D2` |
| Learned-edge (re-plumbed §3.1) | logit / rank / top-1-2 margin for `M→D2`, and vs the current parent/child |
| Temporal | `M` tracklet length, velocity, acceleration, curvature; `D2` current-in-edge motion residual (family B); whether `M` was recently born |
| Competition | competing parents/children within the gate; feature deltas of split vs no-change |

### 4.5 Decision & objective
Add `M→D2` iff `P > τ`, **keep a relaxed probability-ranked frame/global cap in v1** (a threshold
alone does not defend against calibration shift, sparse-label FNs, or hidden-test density shift).
Objective for choosing `τ`/cap is `Δscore = Δadj + 0.1·Δdiv_J`, scored on both components — never
classifier AUC alone. The model ranks the mutually-exclusive actions within one mother group.

### 4.6 GATE 1
- **PASS to Phase 2** if the swapped-in module lifts local `div_J` well above 0.040 with `adj`
  held, **consistently across both specimens** (leave-one-specimen-out, §6), and the improvement
  survives the discount for local optimism. Realistic Phase-1 ceiling ≈ `div_J 0.20–0.35` →
  `score +0.016–0.031` → ~0.928–0.943.
- Phase 1 alone may warrant one LB submission (single attributable change vs 0.912) once GATE 1
  passes and `τ` is fixed on inner folds.

---

## 5. Phase 2 — division-aware edge model + division-aware relink (main GPU spend)

The only path past ~0.943, because it targets `div_J` **and** the dense-field identity swaps that
cap `adj`. Runs only after GATE 0 and GATE 1 pass.

### 5.1 Retrain the edge model on REAL proposals with hard negatives (C1)
- Run the frozen detector on the train set to produce **real detection proposals** (including
  unmatched / duplicate detections). Label candidate edges by GT as {continuation, division-fork,
  negative}, using **unmatched/duplicate detections as hard negatives** — the distribution the
  original transformer never trained on and the root cause of dense-field swaps.
- Keep the `SimpleNodeTransformer` trunk (proj→128, bidirectional cross-attention ×4, pairwise
  MLP); **add a division action head.** The ~151 division positives borrow the trunk's
  representation learned from the millions of continuation edges → sidesteps positive scarcity via
  shared multi-task learning.
- Loss = continuation focal-BCE + division-BCE + detection-BCE; AdamW; 199 videos; tens of epochs.
  This ~30 h on 2× T4 is the deliberate compute investment. Add checkpoint/resume (v1-style) for
  cross-session training and augmentation (brightness + flips, as in the pack).

### 5.2 Use a learned division score in the ILP + make `motion_relink` division-aware (C2)
- Replace the ILP's flat `division = 1.0` with the model's learned division score, so real forks
  are selected natively.
- **Division-aware `motion_relink`:** when the learned division score for a mother is high, allow
  out-degree 2 instead of forcing 1:1 — so C1's forks survive to the output, and the audit's
  "relink overrides high-confidence learned edges" `adj` leak is repaired at the same time.

### 5.3 Expected effect
`div_J` climbs on genuine learned division scores (not geometry), and dense-field `adj` recovers
from hard-negative training + preserving high-confidence learned edges → target `0.912 → 0.93–0.95`.

---

## 6. Cross-validation (two specimens is the real domain axis)

- **Outer = leave-one-specimen-out** (`44b6` vs `6bba`) — the ~125:26 division skew makes this the
  generalization test that matters for the hidden set.
- **Inner = cross-fit within the training specimen**, grouped by video / crop / density / time.
- **`τ` / caps / early-stop chosen only on inner calibration folds**, never on the held-out
  specimen.
- **Always report both specimens separately;** trust experiment deltas and per-specimen
  consistency over absolute local scores.

---

## 7. Honest ceilings, risks, and the fallback

- **Daughter detection recall caps `div_J`** → Phase-1 realistic `div_J 0.20–0.35`
  (`score +0.016–0.031`); ~0.943, not 0.95, from divisions alone. Phase 2 is required to approach
  0.95 because it also lifts `adj`.
- **B/C carry the `adj` risk.** A is low-risk / low-recall; B/C break the recall ceiling but modify
  existing edges → the Version 7 landmine. The oracle treats per-specimen `Δadj` as first-class.
- **Positive scarcity (151 events).** Handled by GBDT (Phase 1) and shared-trunk multi-task
  learning (Phase 2); a division-only large network is explicitly avoided.
- **Specimen skew / leakage.** Leave-one-specimen-out CV measures but cannot eliminate the risk;
  absolute local scores are optimistic (frozen features saw all 199 videos).
- **Fallback (if GATE 0 fails):** redirect the 30 h to a multi-frame **tracklet association**
  model on the detector's real proposal distribution, jointly modeling continuation, no-match /
  death, and division — Phase 2's C1 is already most of this, so the pivot reuses that work.

---

## 8. What is added on top of 0.912 (crisp summary)

| Phase | Added | Touches in 0.912 | GPU |
|---|---|---|---|
| 0 (gate) | pre-ILP candidate-edge + heatmap/patch export; counterfactual oracle audit (A/B/C) | inference-only export; read-only audit | no |
| 1 (gate) | Division Action Scorer (GBDT + 3D-CNN appearance embedding) replacing geometric safe-div | replaces `add_safe_divisions_postlink` | light |
| 2 | SimpleNodeTransformer + division action head, retrained on real proposals + hard negatives | extends & retrains the edge model | **~30 h main** |
| 2 | learned division score in ILP + division-aware `motion_relink` | ILP weight source + `motion_relink_edges` | no |

---

## 9. Execution order (gated)

1. **Phase 0** — build the pre-ILP export; run the counterfactual oracle audit; read per-specimen
   ceilings. **Apply GATE 0.**
2. **Phase 1** — train the Division Action Scorer; leave-one-specimen-out CV; swap in; report
   `div_J` vs 0.040 and confirm `adj`. **Apply GATE 1.** (Optional: one LB submission.)
3. **Phase 2** — export real proposals + hard negatives; add the division head; retrain (~30 h,
   checkpoint/resume); wire the learned division score into the ILP; make `motion_relink`
   division-aware; local-eval, then LB.

Nothing downstream of GATE 0 runs until it passes; the 30 h of Phase 2 is committed only after
GATE 1 confirms divisions carry real, per-specimen-consistent positive `Δscore`.

---

## 10. Code anchors (v8 two-seeds local-eval notebook)

- `add_safe_divisions_postlink` — Cell ~2872 (injection point / only division source; writes
  `edge_prob=None`).
- `deepcenter_score_point` / `deepcenter_accept_repair_point` — Cell ~2257 / ~2285 (heatmap
  feature access).
- `motion_relink_edges` — Cell ~2319 (flattens ILP divisions to 1:1; made division-aware in P2-C2).
- `filter_output_graph` — Cell ~3175 (post-link ordering; safe-div called from here).
- Pre-ILP candidate edges — must be exported before the ILP solve (P0-3.1; not in the saved graph).
- Edge model / training — `references/biohub-tracking-support-pack/repo/src/biohub_tracking/models/simple_node_transformer.py`, `scripts/train_unet_transformer.py`, `scripts/predict_unet_transformer.py` (extended in P2).
- Division metric — `references/.../biohub_tracking/division_metrics.py`
  (`evaluate_divisions`, `match_divisions`, `count_matched_pred_divisions`).
- Local scorer output — v8 scoring cell ~3715 (`adj`, `div_J` per-embryo).

> Note: the support pack (`references/`) is gitignored and not ours to redistribute. This plan
> describes our design built on top of it and references its functions/files by role; it does not
> copy pack source.
