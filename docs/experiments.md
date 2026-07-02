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
| full | 30 | **0.000663** (epoch 29) | **0.808** (5 val, all `6bba_`) | 3658/3911 ≈ 93.5% | _pending_ | TP=3046 FP=6 FN=716 |

**Observations.**
- **+0.06 over classical** and detection recall up (≈93.5% vs ~91.5%). **FP≈0** (6/3052) → NN linking
  still perfectly precise, loss is all FN — same character as v0.
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

## How to log a new experiment

Copy a version block, bump the version (`vN`), and record: notebook, method summary, the full
hyper-parameter table (only note what changed from the previous version if it's a minor tweak),
then fill **Results** (local edge-Jaccard + LB) and **Observations** after the run.
