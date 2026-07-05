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
  v1_unet_train.ipynb         v1 — learned detector: training (cosine LR, to convergence) + eval + resume
  v2_fusion_eval.ipynb        v2 — local eval: v1 detector + stronger (two-pass motion) linking
  v2_5_highrecall_eval.ipynb  v2.5 — local eval: high-recall detection + physical (µm) NMS
  v3_divisions_eval.ipynb     v3 — local eval: post-hoc division detection (earn the 0.1 division term)
  v4_isotropic_train.ipynb    v4 — detector on an isotropic (XY-pooled) 64³ grid: training + eval
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
      **Local val edge-Jaccard 0.859 > 0.808; leaderboard 0.827 (+0.059 over v1)** — a pure recall gain
      (recovered links the NN missed, still no false links) that generalized cleanly to the hidden set.
      **Current leaderboard best.**
- [x] **v2.5 — high-recall detection (leaderboard regression)** — denser detection (lower threshold) +
      physical (µm-space) non-max suppression + *relaxed* linking. **Local val edge-Jaccard rose to 0.866,
      but the leaderboard DROPPED to 0.776 — below v2's 0.827.** Key lesson: the local metric is blind to
      false-positive links on the densely-labeled hidden test set and to the leaderboard's over-prediction
      penalty, so relaxing the linker looked free locally while costing real precision on the leaderboard.
- [x] **v2.5b — isolate the cause** — keep v2.5's high-recall detection, but revert *only* the linking
      back to v2's leaderboard-proven precision (the single variable). **Local edge-Jaccard 0.8588 ≈ v2's
      0.859**, so it ties v2 locally — meaning any leaderboard difference is purely what local scoring can't
      see. **Leaderboard 0.786** (between v2.5's 0.776 and v2's 0.827). Because the linking is identical to
      v2, the entire **0.041 gap below v2 is the high-recall detection's density** — over-prediction penalty
      plus false links on the dense hidden test set. **Verdict: the high-recall detection is a net negative
      on the leaderboard; detection is saturated for this metric, so the code is locked back to v2's
      detector (higher threshold, no NMS).**
- [x] **v3 — post-hoc division detection** — the two-pass Hungarian linker is strictly 1-to-1, so it can
      never emit a division (a node with 2 children) and the `0.1 · division_jaccard` term was always 0.
      v3 adds a rule-based step *after* linking that attaches a second daughter to a mother when a
      persistent, opposite-side detection sits nearby. **Result: edge-score-safe but division-score-worthless.**
      Local edge-Jaccard is unchanged (0.8588 → 0.8633, no new false links — the added edges land on
      unmatched detections), but division-Jaccard is only **~0.002** (≈400 false divisions per true one):
      the high-recall detection floods dense regions with spurious tracks, so "a nearby opposite-side track"
      is not a distinctive signal for a real division. Conclusion: divisions need a global/learned tracker,
      not post-hoc geometry. **Follow-up (v2+v3 fusion): the division step was moved onto the leaderboard-best
      v2 detector** (sparser detections → fewer spurious tracks) to test whether a cleaner field makes the
      geometric division signal usable. **Result: leaderboard 0.822 — below v2's 0.827.** The division-score
      bonus is negligible, and the extra division edges — which look free against the sparse *local* labels
      (they land on unlabeled detections) — become real false links on the *densely*-labeled hidden test set.
      **Rule-based divisions are closed: net negative on the leaderboard, so submissions ship with divisions
      off and v2 (0.827) remains best.**
- [x] **Detector quality — convergence run (new leaderboard best 0.844)** — with detection *density* and
      rule-based *divisions* both closed as leaderboard-negative, the remaining detector lever is *quality*.
      Training the existing detector to convergence (60 epochs + cosine learning-rate decay; the first run had
      stopped early on a flat rate with the validation curve still improving) and feeding the **unchanged**
      leaderboard-best post-processing scored **0.844 — +0.017 over v2's 0.827 from nothing but better-trained
      weights**, and it **matches a public reference detector's 0.843 that uses the same linking as ours**. This
      confirms detector quality is a real, open lever (the reference's edge was training, not tracking).
- [~] **Detector quality — isotropic grid (v4, in progress)** — **v4**, a detector on an **isotropic grid**
      (pool the fine XY axes so the voxel is equal on all three axes, giving the network symmetric 3D context;
      the depth axis is 4× coarser and the hardest to localize), is trained and wired into the submission
      notebook as a one-flag detector swap that keeps the same post-processing (so any change is attributable to
      the detector alone). *Local eval + leaderboard comparison to 0.844: pending.* Next architectural steps
      (wider base channels, batch-norm) follow if the isotropic grid helps.
- [~] **Detector quality — wider residual net (v5, in progress)** — a wider, residual, better-normalized
      detector (base channels 16→24, batch-norm, residual blocks, plus augmentation that actually reaches the
      model) on the leaderboard-best full-resolution geometry. **Runs 1 and 2 both failed to converge**: the
      training loss collapses to a floor after the first epoch and never descends, with best validation ~2.5×
      worse than the converged v1. Run 1 used batch-norm; run 2 swapped *only* the normalization to instance-norm
      (everything else held) and stalled identically — so **batch-norm at batch size 2 is ruled out**; the stall
      is normalization-independent. The train and validation curves track each other (underfitting, not
      overfitting), which points at the newly-added photometric augmentation raising the loss floor. Run 3 holds
      the net fixed and *disables* that augmentation to confirm. *Retrain + comparison to 0.844: pending.*
- [ ] **Better linking (Phase 2)** — learned or globally-optimal association to convert the ~97%
      detection into more correct temporal edges; this is also the principled route to the division term.

See [`docs/experiments.md`](docs/experiments.md) for per-experiment configuration and results.

## Getting started

Each notebook in `src/` is designed to run on Kaggle: add the competition dataset as input,
enable GPU/Internet where noted, and Run All. No local data or setup is required.
