# Experiment Log

Living record of every experiment: method, model/hyper-parameters, and results.
Newest experiments at the bottom. Fill the **Results** block after each Kaggle run/submission.

---

## Background (shared context)

**Data.** Paired samples = a 3D+time image volume `(T, Z, Y, X)` (single channel, `uint16`)
and a ground-truth tracking graph. Nodes carry `t, z, y, x` (integer voxel centroids); edges
are directed temporal links (`t → t+1`); a division is a node with ≥2 outgoing edges.
- Physical voxel scale (z, y, x) = **(1.625, 0.40625, 0.40625) µm** — anisotropic (z ~4× coarser).
- Ground truth is **sparsely annotated** and its density varies a lot across samples
  (from ~1 labeled cell/frame up to hundreds). No segmentation masks — centroids only.

**Metric.** `score = adjusted_edge_jaccard + 0.1 · division_jaccard`.
- Nodes matched to GT per timepoint by optimal assignment on scaled distance (gate 7 µm).
- An edge is a TP only if **both** endpoints match GT nodes joined by a GT edge; wrong links
  between two matched nodes are FP. **Unmatched predictions are NOT penalized as FP** (labels
  are intentionally incomplete); over-prediction is only lightly penalized via a node-count term.
- Practical consequence: **detect densely (high recall), link conservatively (avoid wrong links).**

**Local validation.** We reproduce the base edge-Jaccard (`edge_jaccard` in the notebooks) on
held-out train samples. This is the number to compare across versions; training loss (heatmap
MSE) does not directly reflect tracking quality.

**Split.** Last `N_VAL = 20` samples held out for validation; remaining used for train.

---

## v0 — Classical baseline (peak detection + NN linking)

**Notebooks:** `src/v0_baseline.ipynb` (dev). Submission is now the model-agnostic
`src/submit.ipynb` (UNet detector; supersedes the old classical `v0_submit.ipynb`).

**Method.** Per-frame 3D peak detection on a Gaussian-smoothed, percentile-normalized volume;
consecutive frames linked by optimal (Hungarian) assignment on physically-scaled centroid
distance with a gate. No division handling.

**Hyper-parameters.**

| group | param | value |
|-------|-------|-------|
| detect | gaussian sigma (z,y,x) | (0.7, 2.0, 2.0) |
| detect | min_distance (voxels) | 3 |
| detect | threshold_abs (norm 0–1) | 0.08 |
| detect | norm percentiles | (50.0, 99.8) |
| detect | max peaks / frame | 2000 |
| link   | gate (µm) | 8.0 |
| score  | node-match radius (µm) | 7.0 |

**Results.**

| run | config | local edge-Jaccard | LB | notes |
|-----|--------|--------------------|----|-------|
| sweep | thr=0.08, gate=8 | **0.748** (micro, 10 train samples) | **0.669** | FP=0 on all samples; loss is all FN |

**Observations.**
- FP = 0 everywhere → NN linking never makes wrong links; `J ≈ edge recall`.
- Two comparable bottlenecks: (1) detection misses ~16% of GT nodes (node-match ~91.5%,
  caps edge recall ≈ node-match² ≈ 84%); (2) linking loses ~9–10% (both endpoints detected but
  linked to the wrong neighbor / identity switch in dense fields).
- Implication: even a perfect detector caps ~0.85 with current NN linking → linking matters.
- **LB vs local**: leaderboard **0.669** sits ~0.08 below local micro edge-Jaccard 0.748. The gap
  is the part local scoring can't see: the *adjusted* score's density penalty on over-prediction
  (`T_pred` ≫ `T_true`) plus the missing division term (we predict none → 0 of the 0.1 weight), and
  a possible train/test distribution shift. **This 0.669 is the anchor v1 must beat.** Calibration
  takeaway: expect the LB to read ~0.08 under local; over-detection likely costs the most, so watch
  `HM_THR` on v1.

---

## v1 — Learned detector (3D U-Net, heatmap regression)

**Notebook:** `src/v1_unet_train.ipynb` (self-contained: training + eval + resume).

**Method.** A 3D U-Net regresses a Gaussian centroid **heatmap**; peaks are extracted with the
same post-processing as v0, then linked with the v0 Hungarian NN linker. Trained on the sparse
point labels via an **ignore-region masked loss**: supervise positives (near GT) and confident
dark background toward their targets, but **ignore bright-but-unlabeled regions** so the network
is not taught to suppress unlabeled real cells. Anisotropic downsampling (xy first, z later).

**Model / training hyper-parameters.**

| group | param | value |
|-------|-------|-------|
| model | architecture | 3D U-Net, anisotropic strides ((1,2,2),(1,2,2),(2,2,2),(2,2,2)) |
| model | base channels | 16 |
| model | params | ~5.8 M |
| target | patch (Z,Y,X) | (64, 128, 128) |
| target | gaussian sigma (z,y,x) | (1.0, 3.0, 3.0) |
| target | fg_thr (ignore cutoff, norm 0–1) | 0.15 |
| target | positive weight | 10.0 |
| target | pos_frac (patches centered on GT) | 0.7 |
| loss  | masked MSE on sigmoid(heatmap) | — |
| optim | optimizer / lr | AdamW / 2e-4 |
| optim | AMP (mixed precision) | on |
| train | batch size | 2 |
| train | epochs | 30 |
| train | steps / epoch | 300 |
| train | early-stop patience | 6 |
| infer | heatmap peak threshold HM_THR | 0.3 |
| infer | min_distance (voxels) | 3 |
| link  | gate (µm) | 8.0 |

**Status.** Full 30-epoch training **complete** (`models/v1_UNet_best.pt`, `results/v1_history.csv`).
Ran ~120 s/epoch → ~1 h total (faster than the earlier 5–6 min/epoch estimate). Checkpoint/resume +
time-budget safe-exit enabled.

**Results.** Detector **beats classical**: local micro edge-Jaccard **0.808 > ~0.75**. (Eval via the
notebook's `EVAL_ONLY` flag with `models/v1_UNet_best.pt`.)

| run | epochs | val masked-MSE (best) | local edge-Jaccard | matched/n_gt | LB | notes |
|-----|--------|-----------------------|--------------------|--------------|----|-------|
| full | 30 | **0.000663** (epoch 29) | **0.808** (5 val, all `6bba_`) | 3658/3911 ≈ 93.5% | **0.768** | HM_THR=0.3, gate=8; TP=3046 FP=6 FN=716 |

**Observations.**
- **+0.06 over classical** and detection recall up (≈93.5% vs ~91.5%). **FP≈0** (6/3052) → NN linking
  still perfectly precise, loss is all FN — same character as v0.
- **LB 0.768 (submission "Version 2", HM_THR=0.3): +0.099 over the v0 anchor 0.669** — the detector's
  local gain carried through to the leaderboard. The **local→LB gap narrowed from ~0.08 (v0) to ~0.04**,
  even though the division term is *still* unaddressed (0 of the 0.1 weight). Implication: the *adjusted*
  density penalty is **milder than feared** — heavy over-detection (pred up to ~48k nodes) cost little —
  and much of v0's 0.08 gap was likely the classical detector generalizing poorly to the unseen `44b6_`
  specimen. The UNet generalizes better. **Takeaway: don't rush `HM_THR` up; over-detection is cheap.**
- Bottleneck split now: detection ~12.5% (node-match² ≈ 0.875 ceiling) > linking ~6.6% (0.875→0.808).
  Detection still the larger loss but the two are comparable → NN's ~0.85 ceiling is close → **Phase 2
  (better linking) is the next lever**.
- **Caveats**: only 5 val samples and **all one specimen** (`44b6_` unseen) → rerun `EVAL_N_VAL=20`
  for a firmer, specimen-balanced number. Heavy **over-detection** (pred up to ~48k nodes/sample) is
  free for local base-Jaccard but the LB *adjusted* score penalises high `T_pred` → watch the LB, may
  need a higher `HM_THR`.
- Training was **not fully converged** (val still trending down, no overfit, early-stop never fired) →
  more epochs (+ LR decay) could still help detection.

---

## v2 — Fusion: v1 detector + rule-based linking & post-processing

**Notebooks:** `src/v2_fusion_eval.ipynb` (local A/B eval). The winning stack is folded into
`src/submit.ipynb` (replacing the plain NN linker).

**Method.** Detection is **byte-identical to v1** (full-res U-Net heatmap → `peak_local_max`,
`HM_THR=0.3`, `min_distance=3`), so linking is the only variable. The v0/v1 nearest-neighbour linker is
replaced by a public rule-based stack:
- **`refine_centroids`** — intensity-weighted centre-of-mass sub-voxel refinement.
- **`link_twopass`** — two-pass Hungarian with constant-velocity prediction: pass 1 a tight 6 µm raw gate
  (kills "partner-stealing" matches), pass 2 a loose 8 µm gate on the leftovers (recovers fast cells).
- **`close_gaps`** — bridge a single-frame detection gap by interpolating a node (all GT edges are dt=1,
  so one recovered node yields two matchable edges).
- **`prune_isolated`** + **`filter_short_tracks(min_len=4)`** — drop unlinked / short-fragment noise.

**Hyper-parameters** (only linking/post-proc changed from v1):

| group | param | value |
|-------|-------|-------|
| link | tight gate (µm) | 6.0 |
| link | loose gate (µm) | 8.0 |
| link | velocity blend | 0.5 |
| post | close_gaps / max_gap / gap_dist (µm) | on / 1 / 6.0 |
| post | filter_short_tracks min_len | 4 |
| post | prune_isolated | on |
| detect | refine window (z,y,x) | (1, 3, 3) |

**Results.** Same detector, same 5 val samples (all `6bba_`) as v1's 0.808:

| run | linking | local edge-Jaccard | TP | FP | FN | LB | notes |
|-----|---------|--------------------|----|----|----|----|-------|
| v1  | plain NN Hungarian | 0.808 | 3046 | 6 | 716 | 0.768 | baseline |
| v2  | two-pass motion + gaps + filter | **0.859** | 3238 | 7 | 524 | **0.827** | **+0.051 local, +0.059 LB** |

**Observations.**
- **Pure recall gain.** FN dropped 716→524 (= TP +192) with **FP still ≈0** — the stronger linker
  recovers edges the NN missed/gated without introducing wrong links. `close_gaps`'s interpolated nodes
  also lifted node-match (they match GT cells missed in a single frame).
- **LB 0.827 (submission "Version 3"): +0.059 over v1's 0.768**, the biggest single-version LB jump so
  far, and the local→LB gap **narrowed further to −0.032** (v1 was −0.04). The linking upgrade generalized
  beautifully to the hidden set — including the unseen `44b6_` specimen. **This is the current LB best.**
- Remaining loss is now mostly **detection** (unmatched GT nodes on the weakest samples, J≈0.80) rather
  than linking → next lever tried was detection recall (denser peaks + physical NMS) in v2.5.

**Reference baselines studied** (`references/`, local only): a classical **DoG detector → same two-pass
linking (LB 0.835)** and a **U-Net-on-pooled-grid detector with physical (µm) NMS (LB 0.843)**. Both
confirm over-detection is cheap and converge on the two-pass motion linker adopted here; physical NMS is
the technique to borrow next.

---

## v2.5 — High-recall detection + physical NMS

**Notebooks:** `src/v2_5_highrecall_eval.ipynb` (local A/B eval). The preset is folded into
`src/submit.ipynb` (which now supersedes the v2 linking-only version).

**Method.** Same v1 detector + v2 linking, but the **detection front-end is pushed for recall** and
de-duplicated in physical space (borrowed from the LB 0.843 reference):
- lower `HM_THR` (0.3 → **0.15**) and `min_distance` (3 → **1**) → many more candidate peaks;
- **physical NMS** — greedy non-max suppression in micrometre space (`cKDTree`, radius `NMS_UM`),
  isotropic in real units, unlike the anisotropic voxel `min_distance` (z is 4× coarser than xy);
- linking relaxed slightly (loose gate 8 → **10** µm) and `filter_short_tracks` gentler (4 → **2**).

**Hyper-parameters** (changed from v2):

| group | param | v2 | v2.5 |
|-------|-------|----|------|
| detect | HM_THR | 0.3 | **0.15** |
| detect | min_distance (voxels) | 3 | **1** |
| detect | physical NMS radius (µm) | — | **3.0** |
| link | loose gate (µm) | 8.0 | **10.0** |
| post | filter_short_tracks min_len | 4 | **2** |

**Results** (same detector weights, same 5 val samples):

| run | detection | local edge-Jaccard | TP | FP | FN | detection recall | LB |
|-----|-----------|--------------------|----|----|----|------------------|----|
| v2   | HM_THR 0.3, no NMS | 0.859 | 3238 | 7 | 524 | ~94% | **0.827** |
| v2.5 | HM_THR 0.15 + physical NMS + relaxed linking | **0.8657** | 3262 | 6 | 500 | **96.9%** (3789/3911) | **0.776 ⬇** |

**Observations.**
- **Detection recall lifted ~94% → 96.9%** locally (biggest gains on the weakest samples, e.g. `e5e44988`
  matched 574→636, J 0.809→0.836), with **local FP still ≈0** and runtime unchanged (~52 s/sample).
- **⚠️ LB REGRESSION: 0.776 (submission "Version 4"), BELOW v2's 0.827** despite local edge-J *rising*
  0.859 → 0.866. The local→LB gap blew out to **−0.090** (v2 was −0.032). **This is the key lesson of the
  project so far:** the local metric is **blind to two things the LB charges for** — (1) **FP edges on the
  dense hidden GT** (local GT is sparse, so wrong links between unmatched predictions are not counted as
  FP; local FP was 6 for *both* v2.5 and its fix, i.e. local FP can't distinguish them), and (2) the
  **adjusted density penalty** on over-prediction (v2.5 predicts up to ~59k nodes/sample). v2.5 bundled
  **five** changes (HM_THR↓, min_dist↓, NMS, loose gate 8→10, filter_short 4→2), so the regression was
  un-attributable → follow-up isolates the cause (see v2.5b).
- **Corrected calibration**: "over-detection is cheap / LB ≈ local − 0.04" (from v1) **does NOT extrapolate**
  to the v2.5 aggressiveness. Detection-side tuning is now **negative ROI** unless proven otherwise on the LB.
- **Never bundle knobs across a submission again** — Kaggle submissions are the only ground truth for the
  FP/density effects local eval hides, so each must change one attributable variable.

---

## v2.5b — High-recall detection (v2.5) + v2 LB-proven linking (single-variable revert)

**Notebooks:** `src/v2_5_highrecall_eval.ipynb` (config reverted). Folded into `src/submit.ipynb`.

**Method.** Diagnostic follow-up to the v2.5 regression: **freeze v2.5's high-recall detection front-end**
(HM_THR=0.15, min_distance=1, physical NMS 3.0 µm) and **restore v2's LB-proven linking precision**
(loose gate 10 → **8**, `filter_short_tracks` 2 → **4**). The linking-precision module is the **only**
variable vs the 0.776 run, so the LB result attributes the regression to linking-vs-detection.

**Hyper-parameters** (changed from v2.5, = revert to v2 values):

| group | param | v2.5 | v2.5b |
|-------|-------|------|-------|
| link | loose gate (µm) | 10.0 | **8.0** |
| post | filter_short_tracks min_len | 2 | **4** |

**Results** (same detector weights, same 5 `6bba_` val samples):

| run | linking | local edge-Jaccard | TP | FP | FN |
|-----|---------|--------------------|----|----|----|
| v2     | HM_THR 0.3 + v2 linking | 0.859 | 3238 | 7 | 524 |
| v2.5   | HM_THR 0.15 + relaxed linking | 0.8657 | 3262 | 6 | 500 |
| v2.5b  | HM_THR 0.15 + v2 linking | **0.8588** | 3236 | 6 | 526 |

**Observations.**
- **Locally a tie with v2** (0.8588 ≈ 0.859): restoring v2's linking gave back v2's precision profile
  (FN 500→526, i.e. dropped the 26 extra edges v2.5 gained by relaxing linking — exactly the edges that
  came with LB-hurting FPs on the hidden set). Local FP unchanged at 6 (again: local can't see the real FP).
- Because v2.5b **ties v2 locally**, the two configs differ on the LB **only** via effects local eval is
  blind to: the density penalty (this predicts up to ~58k nodes/sample vs v2's far fewer) and any
  high-recall gain on the **unseen dense `44b6_` specimen** (absent from this all-`6bba_` val). So the LB
  is the only way to decide — worth one submission.
- **Decision rule for the LB result:** ≥0.827 → relaxed linking was the v2.5 culprit, high-recall detection
  is LB-safe (keep it, move to Phase 2 linking). ~0.776–0.82 → detection density is the cost, lock in v2
  (HM_THR=0.3, no NMS). >v2 clearly → high-recall detection genuinely helps on `44b6_`.

**LB result (submission "Version 5"): 0.786** — lands squarely in the "detection density is the cost" band.

| run | detection | linking | local edge-J | LB |
|-----|-----------|---------|--------------|----|
| v2    | HM_THR 0.3, no NMS | v2 | 0.859 | **0.827** |
| v2.5  | HM_THR 0.15 + NMS | relaxed | 0.8657 | 0.776 |
| v2.5b | HM_THR 0.15 + NMS | v2 | 0.8588 | **0.786** |

- **Clean single-variable isolation (the payoff of the revert).** v2 and v2.5b **tie locally** (0.859 vs
  0.8588) with **identical linking**, so the entire **−0.041 LB gap (0.827 → 0.786) is attributable to the
  high-recall detection density alone** — the adjusted over-prediction penalty + false links on the dense
  hidden GT, both invisible to local eval. Separately, v2.5b (0.786) vs v2.5 (0.776) shares the detection and
  differs only in linking → **restoring v2 linking bought +0.010**. So the original v2 → v2.5 drop of 0.051
  decomposes as **≈ −0.041 detection density (the dominant ~80%) + −0.010 relaxed linking**. Both knobs hurt;
  detection density is ~4× the cost.
- **Verdict: high-recall detection (HM_THR 0.15 + min_distance 1 + physical NMS) is LB-NEGATIVE.** Detection is
  **saturated** for this metric — more recall buys nothing the LB rewards and costs the density penalty.
  **Locked the code back to v2 detection** (HM_THR 0.3, min_distance 3, NMS off) in both `submit.ipynb` and
  `v3_divisions_eval.ipynb`. The only remaining lever is Phase 2 (learned/global linking).

---

## v3 — Post-hoc division detection (earn the 0.1 · division_jaccard term)

**Notebooks:** `src/v3_divisions_eval.ipynb` (local eval). Folded into `src/submit.ipynb` (`DIV_ENABLE`).

**Motivation.** `link_twopass` uses the Hungarian algorithm, which is strictly **1-to-1** → every node has
out-degree ≤ 1 → the graph can *never* contain a division (out-degree ≥ 2) → **`division_jaccard = 0` by
construction** for every submission so far. v3 adds divisions back *after* linking without touching the
LB-proven detection/linking (frozen v2.5b).

**Ground-truth divisions** (measured across all 199 train samples, new cell in `util_inspect_data.ipynb`):
**151 division events, only 0.117 % of edges**, and **84 % are in the `6bba` specimen** (125 vs 26 for
`44b6`). Geometry: mother→daughter displacement median 5.75 µm, p90 9.07, max 13.5; split angle median
138°, p10 88°. So the ceiling on the 0.1 term is small, and the gates below are set from these stats.

**Method (`detect_divisions`).** For each mother `M(t)` that already has exactly one daughter `D1(t+1)`,
scan the **orphan births** at `t+1` (nodes with no incoming edge) and add an edge `M→D2` when D2 passes
four gates: distance `‖D2−M‖ ≤ DIV_RADIUS_UM`, opposite-side symmetry (angle between `(D1−M)` and `(D2−M)`
`≥ MIN_ANGLE_DEG`), daughter persistence (D2 heads a chain `≥ MIN_DAUGHTER_LEN`), and mother persistence
(`≥ MIN_MOTHER_LEN`). One division per mother; nearest qualifying D2 wins. Adds edges only, never nodes.

**Hyper-parameters** (gates from the GT geometry above):

| group | param | value |
|-------|-------|-------|
| div | DIV_RADIUS_UM (µm) | 10.0 (≈ p90 of mother→daughter disp; intentionally > 8 µm motion gate) |
| div | MIN_ANGLE_DEG | 75 (GT p10 = 88° → keeps margin, rejects same-side) |
| div | MIN_DAUGHTER_LEN | 3 (persistence filter; effective floor is 4 via `filter_short_tracks`) |
| div | MIN_MOTHER_LEN | 3 |

**Eval design.** *Loop A* — edge-J OFF vs ON on the same last-5 `6bba_` val as v2 (safety check). *Loop B* —
division-J on the 8 **division-richest** train samples (where GT divisions actually exist; ±1 frame tol,
7 µm gate).

**Results.**

| loop | metric | OFF (v2.5b) | ON (+divisions) |
|------|--------|-------------|-----------------|
| A (last-5 val) | edge-Jaccard | 0.8588 (FP=6) | **0.8633 (FP=6)** |
| B (8 richest)  | division-Jaccard | 0.0 | **0.0024** (TP=13, FP=5293, FN=18) |
| B (8 richest)  | edge-Jaccard | 0.8953 | 0.8978 (edge-FP 14→17) |

- Divisions predicted: **5306** across the 8 richest samples to catch **13** real ones; Loop A added 2902
  across 5 val samples for 6 true. Division-J = 0.0024 → score contribution **0.1 · 0.0024 = +0.0002 ≈ 0**.
- Division **recall** is also only ~42 % (13 / 31 GT), so it is a precision *and* recall failure.

**Observations.**
- **Edge-score-SAFE (confirmed).** edge-J is unchanged→slightly up and edge-FP barely moves, because the
  added `M→D2` edges land on **over-detected orphans** (unmatched to GT) → not charged as edge FP. The small
  edge-J rise is real division edges that happened to match GT division edges. So divisions cannot hurt the
  0.827 main score.
- **Division-score-WORTHLESS.** The ~400:1 false-positive rate kills the term. **Root cause:** the
  high-recall detection (HM_THR 0.15) fills every dense region with persistent orphan tracks, so "an
  established mother with a nearby opposite-side persistent orphan" is **ubiquitous noise**, not a
  distinctive division signature. The very over-detection that makes edge recall cheap makes division
  precision impossible with geometry alone — the two goals conflict.
- **Gate tightening cannot close the gap.** Reaching a useful div-J (~0.2) would need a ~150× FP cut while
  holding recall; real-division geometry (disp 5.75 µm, angle 138°) overlaps the noise too heavily. The
  principled fix is a **global/learned tracker** (motile with a division cost, or Trackastra) that solves
  the lineage jointly — i.e. Phase 2 linking is also the route to the division term.
- **`filter_short_tracks(4)` runs before `detect_divisions`**, so an orphan daughter chain must actually
  survive ≥ 4 nodes; `MIN_DAUGHTER_LEN=3` is therefore partly dominated (consistent between v3 and submit).

**Note on the base.** The results above ran `detect_divisions` on the **v2.5b high-recall detection**. Once the
v2.5b LB (0.786) proved that detection density is a net negative, the division step was moved onto the LB-best
v2 detection — see the fusion below.

---

## v3 on v2 base — "fuse v2 + v3" (divisions on the leaderboard-best detector)

**Notebooks:** `src/v3_divisions_eval.ipynb` (config reverted to v2 detection) + `src/submit.ipynb`
(`DIV_ENABLE=True`).

**Method.** Identical `detect_divisions` (same gates: radius 10 µm, angle ≥ 75°, daughter ≥ 3, mother ≥ 3),
but the **detection front-end reverted from v2.5b to v2**: `HM_THR` 0.15 → **0.3**, `min_distance` 1 → **3**,
physical **NMS off** (`NMS_UM = 0`). Linking stays v2 (loose 8 / filter 4). Single attributable change vs v2:
the division rider on the LB-best base.

**Hyper-parameters** (changed from the v2.5b-base v3):

| group | param | v2.5b base | v2 base |
|-------|-------|------------|---------|
| detect | HM_THR | 0.15 | **0.3** |
| detect | min_distance (voxels) | 1 | **3** |
| detect | physical NMS radius (µm) | 3.0 | **0 (off)** |

**Hypothesis.** v2's sparser peaks leave **far fewer persistent orphans** than v2.5b's high-recall flood, so
the "established mother + nearby opposite-side persistent orphan" pattern should be **less ubiquitous → a
cleaner division signature**. Division-J may rise above the ~0.0024 seen on v2.5b detection. The division
edges still land on unmatched orphans, so the step stays **edge-safe** (expected edge-J ≥ v2's 0.827) with
divisions as free upside on top.

**Results.**

| run | base | divisions | LB | vs v2 |
|-----|------|-----------|----|-------|
| v2 (Version 3) | HM_THR 0.3 + v2 linking | OFF (1-to-1 linker) | **0.827** | — |
| v2+v3 (Version 7) | same v2 detection + linking | **ON** (`DIV_ENABLE`) | **0.822** | **−0.005 ⬇** |

**Observations.**
- **Divisions ON is net LB-NEGATIVE even on v2's sparser detection** (−0.005). This closes the rule-based
  division line: it was already worthless on v2.5b high-recall detection (div-J ≈ 0.0024), and on the LB-best
  v2 base it doesn't just fail to help — it *costs* a little.
- **Why it drops rather than merely ties.** The division term's contribution is negligible
  (`0.1 · division_jaccard ≈ +0.0002`), so it can't offset anything. Meanwhile the added `M→D2` edges are only
  **"edge-safe" against the sparse *local* GT**, where they land on unmatched orphans (not charged as FP). On
  the **dense hidden GT** those same orphan targets are frequently real, matched GT nodes that simply have no
  division edge → `M→D2` then joins two matched nodes not connected in GT = a genuine **edge-FP**. The result:
  tiny division bonus − small dense-GT edge-FP cost ≈ −0.005.
- **This is the exact v2.5 blind-spot again** (local rose, LB fell): local eval cannot see FP edges on the dense
  hidden GT, so a step that looks free locally can still cost real edge precision on the leaderboard. See the
  v2.5 / v2.5b sections.
- **Verdict / action.** Rule-based post-hoc divisions are **fully closed** — LB-negative on both detection bases.
  Ship submissions with **`DIV_ENABLE=False`**; the leaderboard best remains **v2 (Version 3, 0.827)**. Divisions
  are only worth pursuing as a byproduct of Phase 2 global/learned tracking (motile division cost / Trackastra).

---

## Strategy note — detector QUALITY is the next lever (not recall)

After v2.5b (detection density LB-negative) and v3/Version 7 (rule-based divisions LB-negative), the two
"obvious" detector knobs are both closed. But the studied reference **U-Net (LB 0.843) uses the SAME two-pass
linking we do** and still beats our 0.827 by **+0.016** — proof that a *better detector* (not more detections)
has real leaderboard headroom. The productive target is therefore **localization precision + generalization to
the unseen `44b6_` specimen**, NOT recall (already ~97%, and pushing it LB-regressed). Two detector experiments
follow from this: **v1b** (train the existing arch to convergence) and **v4** (adopt the reference's isotropic
grid). Both are evaluated as single-variable changes.

---

## v1b — Converged v1 detector (60-epoch cosine continuation)

**Notebook:** `src/v1_unet_train.ipynb` (same file, updated in place).

**Motivation.** The original v1 stopped at 30 epochs on a **flat LR** with val loss still trending down —
**never converged** (early-stop never fired, val ≤ train throughout). This run trains to convergence.

**Method / changes vs v1** (everything else identical — single variable = training schedule):

| group | param | v1 | v1b |
|-------|-------|----|-----|
| train | EPOCHS | 30 | **60** |
| optim | LR schedule | flat 2e-4 | **cosine 2e-4 → 4e-6** (eta_min = 2% of base, over the 60-ep horizon) |
| train | early-stop patience | 6 | **8** (room for the decay tail) |
| resume | scheduler state | — | **stored in ckpt**; old flat-lr ckpt is fast-forwarded to mid-cosine (~1e-4) |
| resume | warm-start (best-weights only) | — | **added**: fresh opt, continue from cosine midpoint (gentle lr), seed `best` from the warm model so it never ends worse |

**Deployment.** This is the detector behind the planned **submission "Version 8"** = converged weights + the
**unchanged v2 pipeline** (HM_THR 0.3 / min_dist 3 / NMS off + two-pass linking loose8/filter4, divisions OFF).
Single attributable variable vs Version 3 (0.827): only the detector weights changed.

**Results.** Training complete (user). **LB (submission "Version 8"): 0.844** — the converged detector + the
unchanged v2 pipeline. **+0.017 over v2's 0.827** from *nothing but better-trained weights* (single attributable
variable), and it **matches/edges the reference UNet's LB 0.843** using our *same* v2 linking.

| run | detector | pipeline | LB | vs v2 |
|-----|----------|----------|----|-------|
| v2 (Version 3) | v1 30-epoch flat-LR | v2 detect + v2 linking | 0.827 | — |
| v1b (Version 8) | **v1 60-epoch cosine (converged)** | same v2 detect + v2 linking | **0.844** | **+0.017** |

- **Verdict: detector QUALITY is a real, open lever** — the read was "LB ≥ 0.827 → keep pushing the detector",
  and 0.844 clears it decisively. Density (v2.5b) and rule-based divisions (Version 7) are both closed, but the
  *detector itself* still has headroom: convergence alone bought +0.017, and matching the reference 0.843 with
  our own linking means their remaining edge over us is detector, not tracking. **Next single-variable detector
  steps are now justified**: v4 isotropic grid (below), then base24 / BatchNorm.
- The gain also confirms the original v1 was genuinely under-trained (flat LR, val still descending at 30 ep) —
  cosine LR to 60 epochs was the fix, not more data or architecture.

---

## v4 — Isotropic pooled-grid detector

**Notebook:** `src/v4_isotropic_train.ipynb` (self-contained; reuses v1's training machinery).

**Method.** Adopt the reference LB-0.843 detector's representation: **max-pool XY by 4** so the network sees an
**isotropic 64³ grid** (voxel 1.625 µm on all three axes — z untouched, xy 0.40625×4 = 1.625). Symmetric strides
`(2,2,2)×4` (64→32→16→8→4). Trains on **whole 64³ volumes** (no cropping). At inference: peaks found on the 64³
grid → mapped back to ORIGINAL coords (xy ×4) → **refined by intensity-weighted CoM on the full-res volume** to
recover sub-pool xy precision. Linking + scoring run in ORIGINAL µm space, so the eval edge-Jaccard is directly
comparable to **v1's 0.808** (same NN linker) — the delta is purely the isotropic geometry.

**Single-variable (chosen).** vs v1: base16, InstanceNorm, sigma-in-µm, cosine LR all **unchanged**; ONLY the
grid geometry + symmetric strides change. (Reference config base24/BatchNorm deferred to later single steps.)
Pooling = **max** (chosen; preserves bright centroids vs mean/area).

**Hyper-parameters** (changed from v1):

| group | param | v1 (full-res) | v4 (isotropic) |
|-------|-------|---------------|----------------|
| grid | XY pooling | none (full-res) | **max-pool ×4 → 64³** |
| model | strides | ((1,2,2),(1,2,2),(2,2,2),(2,2,2)) | **((2,2,2)×4)** symmetric |
| target | SIGMA (voxels) | (1,3,3) anisotropic | **(1,1,1) isotropic** (~1.625 µm) |
| train | patch / batch | (64,128,128) / 2 | **whole 64³ / 8** |
| infer | min_distance | 3 (full-res voxels) | **1 (pooled voxel = 1.625 µm)** |
| infer | refine window | (1,3,3) | **(1,5,5)** on full-res (recovers xy after ×4 map) |

**Hypothesis.** Isotropic z-context (z is 4× coarser and the hardest axis to localize) should lift the weakest
samples — dense fields and especially the unseen **`44b6_`** specimen (absent from the all-`6bba_` first-5 val,
so eval with `EVAL_N_VAL=20`). Params ≈ 5.82 M (≈ v1's 5.8 M → same capacity, confirming single-variable).

**Results.** Built + locally smoke-tested (pool shape, 64³ forward, coord round-trip). **User training complete.**

**Wired into `submit.ipynb`** (a `DETECTOR = 'v1' | 'v4'` toggle): setting `'v4'` auto-switches to symmetric
STRIDES + the pool/detect front-end (`POOL_XY=4`, `MIN_DISTANCE=1` pooled voxels, `REFINE_WIN=(1,5,5)`) and
feeds the **identical v2 linking + divisions OFF**, so a v4 submission is a **clean single-variable detector
swap vs Version 8's 0.844**. HM_THR held at 0.3 for the first A/B (do NOT also move density — that would
re-bundle the v2.5 mistake). Weights auto-find is DETECTOR-aware and keyed on the exact filename first, so both
weight datasets can be attached at once without grabbing the wrong `.pt`.

**Weights / datasets.** v1 = `v1_UNet_best.pt` (Kaggle dataset `biohub-v1-unet-base16-heatmap`); v4 =
`v4_UNet_iso_best.pt` (`biohub-v4-unet-base16-iso-heatmap`). `submit.ipynb` is **currently set to `DETECTOR='v4'`**
for the pending A/B run.

**Results.** **LB (submission "Version 9"): 0.838** — v4 isotropic detector + the unchanged v2 pipeline, a
clean single-variable detector swap vs Version 8's **0.844**. So isotropic is **−0.006 vs the converged v1
full-res detector**: LB-NEGATIVE, below the decision gate (≥ 0.844).

| version | detector | pipeline | LB | vs Version 8 |
|---|---|---|---|---|
| v1b (Version 8) | v1 60-epoch cosine, full-res anisotropic | v2 detect + v2 linking | **0.844** | — |
| v4 (Version 9) | **isotropic 64³ pooled grid (XY max-pool ×4)** | same v2 detect + v2 linking | 0.838 | **−0.006** |

**Verdict: v1 full-res stays the base; isotropic geometry is a (mild) LB loss.** Because everything downstream
was identical, the −0.006 is purely the detector geometry. Most likely cause: **XY max-pool ×4 discards native
0.40625 µm localization precision** at the peak-detection stage (peaks are found on the coarse 64³ grid, then
refined on full-res — but merges/misses in dense XY regions can't be recovered by post-hoc refinement). The
isotropic z-context hypothesis (help the dense / `44b6_` samples) did not pay off enough to offset that XY loss.
The "keep pushing arch (base24 / BatchNorm)" path was gated on v4 winning, so it is **not** auto-justified by
this result — but base24 / BatchNorm can still be tried on the **v1 full-res** geometry as separate single-variable
experiments. HM_THR was held at 0.3 (density unchanged), so the gap is not a density-calibration artifact.

---

## v5 — ResUNet detector (base24 + BatchNorm + residual + effective 3D aug)

**Notebook:** `src/v5_resunet_train.ipynb` (self-contained; a copy of v1's machinery — identical cosine LR,
checkpoint/resume, eval, and downstream linking. ONLY the detector internals change).

**Motivation.** Density (v2.5b), rule-based divisions (Version 7), and isotropic geometry (v4, LB 0.838) are all
closed. The one detector axis still untested is raw **quality/capacity**: a wider, residual, better-normalized net
with augmentation that actually reaches the model. Built on the **LB-best v1 full-res anisotropic** geometry, not
the isotropic grid that just lost.

**Method (single notebook; each change is a flag for ablation).** Four bundled changes vs v1:

| knob | v1 | v5 default | note |
|---|---|---|---|
| `BASE` (width) | 16 (5.81M params) | **24 (13.25M)** | `32` = 23.56M available; `chs = base·2^i` |
| `NORM` | InstanceNorm3d | **BatchNorm3d** | ⚠️ BATCH=2 is small for BN → `'group'`/`'instance'` fallbacks |
| `RESIDUAL` | none | **True** | `ConvBlock = act(convs(x) + proj(x))`; False+instance == v1 |
| augmentation | flips + xy-swap + `v*=U(0.9,1.1)` | flips + **90° rot** + gamma/contrast/bright/noise | see below |

The intensity fix matters: v1 multiplied the raw volume by `U(0.9,1.1)` and *then* percentile-normalized — the
scale **cancels**, so v1 effectively trained with geometric augmentation only. v5 applies gamma / contrast /
brightness / additive-noise **after** the [0,1] normalization (so they persist), plus in-plane 90° rotations. This
targets **generalization to the unseen `44b6_` specimen** (our val is all `6bba_`, so raise `EVAL_N_VAL` toward 20
to actually observe it). Weights live in their own files (`v5_UNet_res_best.pt` / `unet_res_latest.pt`); v1/v4
weights are NOT loadable (conv shapes differ) → trains from scratch.

**Smoke test (local, CPU).** All four flag combinations forward correctly at full heatmap resolution; param counts
confirmed (BASE16/instance/no-residual = 5.81M = v1; BASE24/batch/residual = 13.25M; BASE32 = 23.56M).

**Results — run 1 (BASE24 + BatchNorm + Residual + aug): FAILED TO CONVERGE.** Trained on Kaggle
(`results/v5_history.csv`). The run **stalled almost immediately** and **early-stopped at epoch 17** (patience 8;
best val was epoch 9):

| run | detector | best val MSE | epochs | vs v1 |
|-----|----------|--------------|--------|-------|
| v1 (converged) | base16, InstanceNorm | **0.000663** (epoch 29, still trending down) | 30 → 60 | — |
| v5 run 1 | base24, **BatchNorm**, residual, aug | **0.001669** (epoch 9) | early-stop @17 | **~2.5× worse** |

- **Train loss went flat after epoch 1 and never descended.** v5 train dropped 0.0193 → 0.00168 in the first epoch,
  then sat at ~0.0016–0.0017 for the remaining 16 epochs (0.00162 at epoch 17). v1 by contrast falls smoothly and
  monotonically (0.0898 → 0.00089). This is **stall/underfitting, not slow convergence** — the net learns almost
  nothing after epoch 1.
- **v5's plateau ≈ v1's epoch-9 state.** v5 best val 0.001669 ≈ v1's epoch-9 val (0.001749). So 18 epochs of v5 only
  reached where v1 was at epoch 9, then stopped improving; early-stop (best @9, no gain for 8 epochs) correctly
  fired at 17. The resulting detector is far worse than v1b (0.844) → **no local eval / LB slot warranted**.
- **Prime suspect: `NORM='batch'` at `BATCH=2`.** The "train loss flat from epoch 1" signature points at the batch
  statistics (batch=2 is too small for BatchNorm3d — running stats are noisy and cap the regression; flagged in the
  config comment). Residual + BN interaction is a secondary suspect. Because run 1 bundled **four** knobs
  (base24 / batch / residual / aug), the cause is not yet attributable — same "never bundle" discipline as v2.5.

**Results — run 2 (ablation: `NORM='instance'`, BASE24 + Residual + aug held): ALSO STALLED → BN hypothesis
DISPROVED.** Changed **only** the norm (`'batch' → 'instance'`), so this run isolates BatchNorm-vs-InstanceNorm as
the single variable vs run 1 (`results/v5_instance_history.csv`, 25 epochs, stopped by patience at epoch 24).

| run | detector | best val MSE | epochs | vs v1 |
|-----|----------|--------------|--------|-------|
| v5 run 1 | base24, BatchNorm, residual, aug | 0.001669 (epoch 9) | early-stop @17 | ~2.5× worse |
| v5 run 2 | base24, **InstanceNorm**, residual, aug | **0.001624** (epoch 16) | patience @24 | **~2.5× worse (same stall)** |

- **Instance-norm behaves identically to batch-norm** — train loss again collapses to ~0.0017 in the first epoch
  (0.0238 → 0.00174) and then sits at ~0.0016 with train ≈ val (no gap) for the rest of the run; best val 0.001624
  vs run 1's 0.001669 is within noise. Both are ~2.5× v1's converged 0.000663.
- **Verdict: `NORM='batch'` at `BATCH=2` was NOT the culprit** — swapping to InstanceNorm did not lift the plateau.
  The stall is norm-independent, so the cause is a **shared factor** in the remaining bundle. The `train ≈ val`,
  flat-from-epoch-1 signature (underfit / over-regularization, not overfit) points at the **augmentation**: v5 adds
  strong post-normalization photometric aug (gamma 0.7–1.5 / contrast / brightness / noise σ=0.03, each p=0.5 every
  step) that v1 never had, which raises the loss floor and blocks sharpening the peak predictions. `RESIDUAL` is the
  secondary suspect (capacity `BASE24` should only help the fit, so it is unlikely to be the cause).

**Results — run 3 (isolate augmentation: photometric aug OFF, `NORM='instance'` + `RESIDUAL=True` + `BASE=24`
held): ALSO STALLED → AUGMENTATION DISPROVED.** Single variable vs run 2 = disabled the photometric aug
(`AUG_GAMMA=(1,1)`, `AUG_CONTRAST=(1,1)`, `AUG_BRIGHT=0`, `AUG_NOISE_STD=0`; geometric flips / 90° rot kept),
trained from scratch (`results/v5_noaug_history.csv`, early-stop @ epoch 27).

| run | detector | best val MSE | epochs | vs v1 |
|-----|----------|--------------|--------|-------|
| v5 run 1 | base24, BatchNorm, residual, aug | 0.001669 (epoch 9) | early-stop @17 | ~2.5× worse |
| v5 run 2 | base24, InstanceNorm, residual, aug | 0.001624 (epoch 16) | patience @24 | ~2.5× worse |
| v5 run 3 | base24, InstanceNorm, residual, **aug OFF** | **0.001643 (epoch 19)** | early-stop @27 | **~2.5× worse (same stall)** |

- **Turning the augmentation off did NOT lift the plateau** — train loss again collapses in epoch 0→1
  (0.0362 → 0.0017) and then sits at ~0.0016–0.0017 with train ≈ val for the rest of the run; best val
  0.001643 is within noise of runs 1 (0.001669) and 2 (0.001624), all ~2.5× v1's converged 0.000663.
  **Verdict: the augmentation is NOT the culprit either** — same as BatchNorm was disproved in run 2.
- **⚠️ New, decisive evidence — the detector is DEAD, not merely worse.** The eval cell produced **`pred=0`
  for all 5 val samples → edge-Jaccard 0.000** (TP=0, FP=0, FN=3762): the heatmap **never exceeds the 0.3 peak
  threshold anywhere**. The network has collapsed to a degenerate **all-background** output, and the ~0.0016
  loss floor IS that trivial solution's loss (the target heatmap is ~99% zero, so predicting ~0 everywhere
  scores a low masked-MSE and `POS_WEIGHT=10` on the tiny positive region doesn't pull it out). v1 escapes this
  floor (reaches 0.000663 by actually predicting peaks); every v5 run gets stuck in it.
- **Elimination is now down to two knobs.** Cleared: BatchNorm (run 2), norm-type dependence (run 2), and
  augmentation (run 3). The only remaining differences from v1 are **`RESIDUAL=True`** and **`BASE=24`**. Since
  `BASE=24` only adds capacity (should *help* the fit, not cause collapse), **`RESIDUAL` is the prime suspect**
  — the residual skip likely makes the trivial all-background/near-identity mapping an easy attractor under the
  sparse, imbalanced target (hypothesis, not a confirmed bug; no defect found in the block code).

**Run 4 (next): isolate the residual skip.** Set `RESIDUAL=False` and hold `NORM='instance'` / `BASE=24` /
aug OFF — single variable vs run 3, and this config differs from v1 **only by width (base24)**. Read: train loss
breaks below the ~0.0016 floor toward v1's 0.000663 → **`RESIDUAL` was the killer** (and base24 is fine — then
re-enable aug for the `44b6_` generalization test that is v5's only real upside); still stalls → base24 is the
last suspect, revert to base16 (== v1) and the whole v5 bundle is a dead end. ⚠️ train **from scratch** each run
(layer buffers differ; do not resume run-1/2/3 checkpoints). Save history as `v5_nores_history.csv`.

**Expectation to temper.** The reference UNet (base24 + BatchNorm) scored **0.843 ≈ our base16's 0.844** — i.e.
raw width + BN alone did NOT beat us. So the likely payoff here, if any, is the **residual + effective augmentation
+ 44b6_ generalization**, not the channel count. If a converged v5 still doesn't clear 0.844, the detector is
plateaued and the next real lever is Phase 2 learned linking (Trackastra).

---

## Phase 2 — learned linking (Trackastra): offline-packaging gate + model probe

**Notebook:** `src/util_trackastra_offline_test.ipynb` (utility). **Why now.** The detector has plateaued
(v1b 0.844; v4 and v5 did not beat it) and detection density / rule-based divisions are both closed as
LB-negative. The metric is edge-Jaccard-weighted, linking is now the larger loss (~7% vs detection ~6%), and
the whole public field sits around the same score using the *same* two-pass rule-based linker we use — so the
open headroom is **learned linking**. The competition host is Royer Lab (authors of ultrack / tracksdata,
Trackastra-adjacent), which further signals a global/learned tracker is the intended route. Idea survey:
`docs/external_ideas.md`. **Trackastra** was chosen first: it links *detections* (which we already have),
models divisions natively, and looked easiest to package for the internet-OFF rerun.

**Kill-criterion: can Trackastra run under internet OFF?** A two-phase notebook (`PHASE='download'` internet ON →
build a `trackastra-offline` Kaggle dataset of wheels + the pretrained model; `PHASE='offline_test'` internet OFF →
install from wheels + load the model + track a synthetic movie with all network sockets hard-blocked).

**Result — GATE PASSED.** All three feasibility questions are YES:

| question | result |
|---|---|
| Install offline (`pip --no-index` from wheels)? | **Yes** (returncode 0; wheels ~261 MB) |
| Load a pretrained model with the network blocked? | **Yes** (bundle from platformdirs `~/.local/share/trackastra/models`, load offline) |
| `mode='greedy'` without an ILP solver? | **Yes** (no motile/ilpy needed) |

**Environment facts / bugs fixed** (each a real finding): Kaggle base is **numpy 2.0.2 / scipy 1.16.3**,
**trackastra 0.5.3**. (1) `pip install trackastra` upgrades numpy 2.0.2→2.4.6 *inside the running kernel*, causing
a numpy python/C ABI skew (`_blas_supports_fpe` AttributeError) on import → **fix: run all Trackastra work in a
fresh subprocess** (a clean interpreter loads the upgraded numpy consistently). (2) Offline install
`ResolutionImpossible` when pinning `numpy==2.0.2` because `imagecodecs>=2.1` (the only wheel available) needs a
newer numpy → **fix: don't pin numpy offline** (the subprocess isolates the upgrade). (3) Model bundling was
initially empty (wrong cache dir) → **fix: copy from the platformdirs `user_data_dir`**.

**Pretrained-model probe** (Phase-1 cell). `_MODELS` has exactly **three** models
(weigertlab/trackastra-models): `ctc`, `general_2d`, `general_2d_w_SAM2_features`. A 2D-vs-3D acceptance test:

| model | 2D | 3D |
|---|---|---|
| `general_2d` | ✅ | ❌ ("Expected 2D data, got 3D data") |
| **`ctc`** | ✅ | **✅** |

**So there IS a usable 3D model — `ctc`.** Zero-shot 3D is therefore *on the table* (no from-scratch training
required to get a first signal). Caveat: `ctc` is trained on Cell-Tracking-Challenge data (not zebrafish
fluorescence) → a domain gap the real-data A/B must settle.

---

## v6 — Trackastra `ctc` zero-shot linking (local eval, built, run pending)

**Notebook:** `src/v6_trackastra_eval.ipynb` (local A/B). **Method.** Detection is **identical to v2** (v1
detector, `HM_THR=0.3`, `min_distance=3`, CoM refine) on the last-5 `6bba` val samples, so the **only variable is
the linker**. For each sample: v1 detector → per-frame centroids → **pseudo-masks** (small anisotropic balls
around each detection, painted paint-if-empty) → `Trackastra.from_pretrained('ctc').track(imgs, masks,
mode='greedy')` → map the resulting edges back to our detection nodes → score **edge-Jaccard + division-Jaccard**
vs GT. The baseline (v2 two-pass linker) is recomputed on the same detections in the same run (≈0.859). All heavy
work (detect + v2 + ctc + score) runs in **one fresh subprocess** launched after `pip install trackastra`, so the
in-kernel numpy upgrade never skews.

**Inputs:** competition data + `biohub-v1-unet-base16-heatmap` (`v1_UNet_best.pt`); internet ON (dev/eval — offline
packaging is validated separately). **Read:**
- **ctc edge-J ≥ v2 (~0.859)** → learned linking wins on identical detections *and* brings divisions for free →
  Phase-2 winner; next = run 20 samples (both specimens) + wire into `submit.ipynb`.
- **ctc edge-J < v2** → domain gap and/or first-pass crudeness → **fine-tune `ctc` on our 199 pairs** (we have GT
  edges + divisions).

**First-pass caveats (all fixable if the signal is promising), surfaced by the notebook's diagnostics:** pseudo-
masks are crude balls (dense-field detections can lose a region — watch `masks-present` / `mapped N/M nodes`);
anisotropy / physical scale is not passed to Trackastra (it sees voxel coords with z 4× coarser); division-J is an
approximate mother-match (no ±1-frame tolerance); and the trackastra output-graph node attributes are assumed
(`time` / `label`, with fallbacks + a printed `sample tra nodes:` for confirmation).

**Results.** *(pending — user to run.)*

---

## How to log a new experiment

Copy a version block, bump the version (`vN`), and record: notebook, method summary, the full
hyper-parameter table (only note what changed from the previous version if it's a minor tweak),
then fill **Results** (local edge-Jaccard + LB) and **Observations** after the run.
