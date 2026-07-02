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

**Notebooks:** `src/v0_baseline.ipynb` (dev), `src/v0_submit.ipynb` (submission).

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
| sweep | thr=0.08, gate=8 | **0.748** (micro, 10 train samples) | _pending_ | FP=0 on all samples; loss is all FN |

**Observations.**
- FP = 0 everywhere → NN linking never makes wrong links; `J ≈ edge recall`.
- Two comparable bottlenecks: (1) detection misses ~16% of GT nodes (node-match ~91.5%,
  caps edge recall ≈ node-match² ≈ 84%); (2) linking loses ~9–10% (both endpoints detected but
  linked to the wrong neighbor / identity switch in dense fields).
- Implication: even a perfect detector caps ~0.85 with current NN linking → linking matters.

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

**Status.** Pipeline validated by a smoke test (1 epoch × 30 steps ran end-to-end after fixing a
float32/AMP dtype issue in inference). Full 30-epoch training underway. ~5–6 min/epoch observed
(→ ~3 h for 30 epochs). Checkpoint/resume + time-budget safe-exit enabled.

**Results.** _pending full training + submission._

| run | epochs | local edge-Jaccard | matched/n_gt | LB | notes |
|-----|--------|--------------------|--------------|----|-------|
| _tbd_ | | | | | |

---

## How to log a new experiment

Copy a version block, bump the version (`vN`), and record: notebook, method summary, the full
hyper-parameter table (only note what changed from the previous version if it's a minor tweak),
then fill **Results** (local edge-Jaccard + LB) and **Observations** after the run.
