# Biohub — Cell Tracking During Development

Detecting, linking, and reconstructing cell lineages across time in 3D microscopy of
developing embryos — a solution for the [Biohub Cell Tracking During Development](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development)
Kaggle competition.

## Overview

Time-lapse 3D microscopy lets biologists watch how cells grow, move, and divide during
development, but analyzing this data by hand is a major bottleneck. The task: given 3D+time
image volumes, **detect every cell, associate cells across frames, and identify division
events** to reconstruct accurate cell lineages.

The problem is framed as **tracking-by-detection**:

1. **Detect** cell centroids in each 3D timepoint.
2. **Link** detections across consecutive frames into tracks.
3. **Divisions / lineage** — resolve splits and reconstruct the lineage graph.

## Repository structure

```
src/
  util_inspect_data.ipynb     inspect the raw data (image/graph structure, sparsity stats)
  util_download_wheels.ipynb  build an offline dependency bundle for no-internet submission
  v0_baseline.ipynb           v0 — classical baseline (dev: detect + link + local scoring)
  v1_unet_train.ipynb         v1 — learned detector: training + evaluation + resume
  v2_fusion_eval.ipynb        v2 — local eval: v1 detector + stronger (two-pass motion) linking
  submit.ipynb                submission notebook (offline): UNet detector + two-pass motion linking -> submission.csv
docs/
  experiments.md              experiment log: config, hyper-parameters, results per version
```

Notebooks are **self-contained** and run standalone on Kaggle (single upload each). They are
version-prefixed (`vN_`) so each modeling iteration is tracked independently, which also makes
later model ensembling/fusion straightforward.

## Data & evaluation

- Paired samples: a 3D+time image volume and a ground-truth tracking graph (nodes = cell
  centroids over time, edges = temporal links; divisions = a node with 2+ children).
- Ground truth is **sparsely annotated** (only a subset of cells is labeled), which the metric
  accounts for.
- Scored by a combined tracking metric emphasizing **edge accuracy** (correct temporal links)
  plus a smaller **division-detection** term.

## Progress

- [x] **Data inspection** — confirmed volume/graph formats, physical scale, label sparsity.
- [x] **v0 — classical baseline** — peak detection + optimal nearest-neighbor linking.
      End-to-end pipeline + local scorer + **leaderboard anchor: 0.669** (local micro edge-Jaccard
      ~0.75; the ~0.08 gap reflects the leaderboard's density penalty + no division term).
- [x] **v1 — learned detector (UNet)** — 3D heatmap-regression detector trained on the sparse
      labels (30 epochs); reuses the v0 linking + scoring. **Local val edge-Jaccard 0.808 > classical
      ~0.75; leaderboard 0.768 (+0.099 over the v0 anchor 0.669).** The local→LB gap also narrowed
      from ~0.08 (v0) to ~0.04, i.e. the detector generalizes better than expected to the unseen specimen.
- [x] **v2 — stronger linking** — same v1 detector, but nearest-neighbour linking replaced by a
      two-pass motion-aware association + single-frame gap-closing + short-track filtering.
      **Local val edge-Jaccard 0.859 > 0.808** — a pure recall gain (recovered links the NN missed,
      still no false links). Folded into the submission notebook; leaderboard submission pending.
- [ ] **Detection recall** — denser detection + physical (µm-space) non-max suppression to recover
      the cells still missed by the detector.
- [ ] **Division / lineage refinement**.

See [`docs/experiments.md`](docs/experiments.md) for per-experiment configuration and results.

## Getting started

Each notebook in `src/` is designed to run on Kaggle: add the competition dataset as input,
enable GPU/Internet where noted, and Run All. No local data or setup is required.
