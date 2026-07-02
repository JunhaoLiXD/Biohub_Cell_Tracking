# Biohub — Cell Tracking During Development (Kaggle)

Detect cells in 3D+time microscopy, link them across frames, detect divisions,
and reconstruct lineages. **Code competition**: submit a notebook that reruns on
a hidden test set (~same size as train) with **internet OFF**.

- Competition: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development
- Metric details: https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md
- Everything runs on **Kaggle** (2x T4 available). Data is NOT local.

## Data (confirmed by inspection)

- Kaggle path: `/kaggle/input/competitions/biohub-cell-tracking-during-development/{train,test}`
- **199 train pairs**: `<id>.zarr` (image) + `<id>.geff` (GT graph), ~0.46 GB each.
  Test example = 4 samples that are COPIES of train (so we can score locally).
  Two specimens: prefixes `44b6_` and `6bba_`.
- **Image `.zarr`** (OME-Zarr, single scale, array "0"): shape `(T=100, Z=64, Y=256, X=256)`,
  `uint16`, one full volume per chunk. Fits in memory. Intensity ~[12, 4319], mean ~219.
- **Voxel scale (z, y, x) µm = (1.625, 0.40625, 0.40625)** — anisotropic, z 4x coarser.
- **`.geff`** (zarr v3): nodes have ONLY props `t, z, y, x` (integer voxel coords, order z,y,x).
  NO seg_id / radius / track_id → **pure centroid points, no segmentation masks**.
  Directed edges source→target = t→t+1.
- **GT is sparsely annotated and density VARIES A LOT**: some samples ~1 cell/frame
  (~52 nodes), others hundreds (788 in `44b6_12dfb391`). Link motion: median 2.88,
  p90 4.67, max 7.81 µm. Divisions are rare.

## Metric

`score = adjusted_edge_jaccard + 0.1 * division_jaccard`

- `adjusted = max(0, jaccard * (1 - 0.1 * (T_pred - T_true) / T_true))`, `jaccard = TP/(TP+FP+FN)`.
- Node match: bipartite assignment per timepoint on scaled centroid distance, gate **7 µm**.
- Edge **TP**: both endpoints match GT nodes connected by a GT edge. **FP**: both matched but
  wrong GT link. **Unmatched predicted nodes/edges are NOT penalized as FP** (annotations
  intentionally incomplete).
- **Strategy consequences**: detect DENSELY (extra detections nearly free for base jaccard);
  link CONSERVATIVELY (wrong links are the real FP source). `T_true` = estimated true cell
  count, unknown locally → calibrate the density penalty via the leaderboard. Divisions only
  0.1 weight, ±1 frame tolerance → defer.

## Repo layout

`src/` holds ALL notebooks (no .py library — each notebook is SELF-CONTAINED so a single
upload runs standalone on Kaggle). Training/tuning runs with internet ON.

`src/` holds ALL notebooks, version-prefixed for tracking / tech-docs / later model fusion.
Each notebook is SELF-CONTAINED (single upload runs standalone on Kaggle).

```
src/
  v0_baseline.ipynb           v0 classical: peak-detect+link+local-scorer+param-sweep (dev)
  v0_submit.ipynb             v0 OFFLINE submission (installs zarr from wheels) [deferred]
  v1_unet_train.ipynb         v1 UNet detector training + eval + resume         <-- ACTIVE
  util_inspect_data.ipynb     utility: dump zarr/geff structure + sparsity stats
  util_download_wheels.ipynb  utility: build the offline zarr wheel dataset (internet ON)
```

Naming: `vN_` = a modeling iteration (v0 Gaussian baseline, v1 UNet, ...); `util_` =
cross-version one-off helpers. `v1_unet_train.ipynb` inlines everything: config, IO,
Gaussian-heatmap+ignore-mask targets,
HeatmapDataset, anisotropic UNet3D (pure PyTorch, no MONAI), masked_mse, Hungarian linking,
edge_jaccard scorer, AMP training loop, and a val edge-Jaccard sanity check vs classical ~0.75.
Just add competition data as input, GPU+internet ON, Run All. Offline submission is deferred.

## Offline submission (internet OFF on rerun!)

1. `download_wheels.ipynb` (internet ON) → `pip download zarr>=3` → save `wheels/` as
   Kaggle dataset **`zarr3-offline`**.
2. `CellTracking_submit.ipynb`: attach competition data + `zarr3-offline`, auto-installs
   zarr from the wheels (`pip install --no-index --find-links`). **Verify with internet OFF
   before submitting.** Writes `/kaggle/working/submission.csv`.
3. Only `zarr` is missing from the base image; scipy/scikit-image/pandas/numpy are present.

## Status log

- **[done] Data inspection** — confirmed shapes, sparsity, metric, no masks.
- **[done] Classical baseline** — peak detection (thr=0.08, gate=8µm) + Hungarian NN link.
  Local micro edge-Jaccard **~0.75** (10 train samples). **FP=0 everywhere** (NN never makes
  wrong links) → J = edge recall, all loss is FN. Submitted for LB anchor (rerun in progress).
- **Diagnosis**: two comparable bottlenecks — (1) detection misses ~16% of GT nodes
  (node-match plateaus ~91.5%; caps edge recall at ~node-match² ≈ 84%); (2) linking loses
  ~9-10% (both endpoints detected but NN links to wrong neighbor / gated). **Perfect detection
  alone caps ~0.85 with current NN linking** → learned linking (Phase 2) matters.

## Roadmap

- **Phase 1 (IN PROGRESS): UNet detector** — self-contained `src/v1_unet_train.ipynb`.
  3D heatmap-regression UNet (pure PyTorch) + ignore-region masked loss for sparse labels +
  anisotropic strides. Reuses peak_local_max post-proc, NN linking, edge_jaccard. Single-GPU+AMP.
  **TODO**: run on Kaggle; compare val edge-Jaccard to classical ~0.75; tune knobs
  (HM_THR peak threshold, SIGMA, FG_THR ignore cutoff, POS_WEIGHT, EPOCHS). Then (deployment
  phase) save weights as a dataset + build an offline UNet submission notebook.
- **Phase 2: better linking** — learned (Trackastra) or global ILP (motile/ultrack) to break
  the ~0.85 NN ceiling.
- **Phase 3: divisions** — out-degree≥2, ±1 frame tolerance (only 0.1 metric weight).
