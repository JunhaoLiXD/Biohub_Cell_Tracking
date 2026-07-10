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
  v5_base24_aug_train.ipynb   v5 — wider (base24) detector; residual ablated out; run 5 augmentation = LB 0.836 (negative)
  v6_trackastra_eval.ipynb    v6 — Phase 2: learned linking (Trackastra `ctc`) vs the rule-based linker
  util_trackastra_offline_test.ipynb  utility: validate offline packaging of the Trackastra dependency
  submit.ipynb                submission notebook (offline): UNet detector + two-pass motion linking -> submission.csv
docs/
  experiments.md              experiment log: config, hyper-parameters, results per version
  external_ideas.md           survey of public/competitor approaches to steal from (Phase 2 backlog)
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
- [x] **Detector quality — isotropic grid (v4, closed — mildly negative)** — **v4**, a detector on an **isotropic
      grid** (pool the fine XY axes so the voxel is equal on all three axes, giving the network symmetric 3D context;
      the depth axis is 4× coarser and the hardest to localize), trained and wired into the submission notebook as a
      one-flag detector swap that keeps the same post-processing (so any change is attributable to the detector
      alone). **Leaderboard result: 0.838 — 0.006 below the 0.844 base.** The XY pooling discards native localization
      precision at peak-detection time, which the full-resolution refinement afterward can't fully recover, so the
      isotropic grid is mildly leaderboard-negative and full-resolution stays the base.
- [x] **Detector quality — wider residual net (v5, closed — width neutral, augmentation negative)** — a wider, residual, better-normalized
      detector (base channels 16→24, batch-norm, residual blocks, plus augmentation that actually reaches the
      model) on the leaderboard-best full-resolution geometry. **Runs 1, 2 and 3 all failed to converge**: the
      training loss collapses to a floor after the first epoch and never descends, with best validation ~2.5×
      worse than the converged v1. Run 1 used batch-norm; run 2 swapped *only* the normalization to instance-norm
      and stalled identically (**batch-norm at batch size 2 ruled out**); run 3 then *disabled* the photometric
      augmentation (everything else held) and stalled again (**the augmentation is ruled out too**). Decisively,
      run 3's evaluation produced **zero detections on every validation sample** — the predicted heatmap never
      crosses the peak threshold, i.e. the network has collapsed to an all-background output and the loss floor is
      that trivial solution. That narrows the cause to the only two remaining differences from v1 — the **residual
      blocks** and the wider base channels — and since extra width should only help fitting, the **residual skip is
      the prime suspect**. The next run disables the residual (holding width and everything else) to confirm; if
      that also stalls, the width is the last suspect and the experiment reverts to the v1 configuration.
      **Run 4 (residual removed) converged cleanly** — the training loss fell all the way down instead of
      stalling, confirming the **residual connection was the cause**. With the residual gone the detector is
      simply a *wider* version of the best detector, and it reaches a **better validation loss than that detector**
      at matched training length (a clean width-only comparison). **Leaderboard result: 0.844 — an exact tie with
      the best detector.** The ~6% better validation loss did **not** transfer, so **the extra width is
      leaderboard-neutral** (validation loss really is only a loose proxy) — width is not a lever, and the detector
      line now looks **saturated around 0.844** (best detector 0.844, isotropic 0.838, wider 0.844, reference 0.843).
      **Run 5 (done):** the one detector factor never actually tested was **augmentation** — earlier runs only
      ruled it out as the *cause of the stall*, never checked whether it *helps*. Augmentation is the only detector
      change with a plausible leaderboard mechanism: better generalization to the **unseen second specimen** (local
      validation is all one specimen, so this is invisible locally and only the leaderboard can judge it). Run 5
      turns augmentation on as a single variable on the converged run-4 configuration (notebook renamed to
      `v5_base24_aug_train.ipynb`). **Leaderboard result: 0.836 — down 0.008 from the 0.844 base.** Augmentation
      reached a slightly *better* validation loss yet a *worse* leaderboard (the third time a validation gain has
      failed to transfer), so **augmentation is leaderboard-negative**: it pushes the detector toward
      intensity-invariance, which shifts peak height/sharpness against the fixed detection threshold (implicitly
      moving detection density, which the leaderboard charges for) and slightly blurs centroid localization, while
      the hoped-for cross-specimen generalization never appeared because the two specimens differ structurally, not
      photometrically. This was the last untested detector factor, so **the detector line is now confirmed saturated
      around 0.844** and all remaining effort moves to learned linking (Phase 2).
- [~] **Divisions / lineage (Phase 3)** — only reachable through a tracker that models cell splits jointly; a
      byproduct of the Phase-2 learned tracker rather than a separate step (rule-based division detection was shown
      to hurt the leaderboard and is closed).
- [x] **Better linking (Phase 2) — learned association via Trackastra (closed — did not beat the rule-based linker)** — with the detector
      plateauing, the next lever is replacing the rule-based linker with a learned one. The whole public field
      is stuck around the same score using the *same* rule-based linker we do, so the headroom is in linking.
      **Offline-packaging feasibility confirmed:** the Trackastra dependency installs and its pretrained model
      loads and runs with the network fully blocked (the competition reruns with no internet), and its greedy
      linker needs no heavyweight solver. A probe of the available pretrained models found one (`ctc`) that
      **accepts 3D input**, so a **zero-shot** trial on our data is possible without training from scratch.
      A/B'd this learned linker against the rule-based one on identical detections. **Zero-shot result: a wash-to-loss.**
      The first run marginally edged the rule-based linker overall but *lost on the densest samples* and emitted a flood
      of false divisions; the follow-up (built-in no-division mode + guaranteed mask regions) came out **slightly below**
      the rule-based linker. Conclusion: the pretrained model, used as-is, does **not** beat our tuned rule-based linker,
      so **zero-shot is closed**. The one remaining option for the learned tracker is **fine-tuning it on our 199
      labelled pairs** (to close the imagery domain gap and learn our own motion/division statistics).
- [x] **Fine-tuning the learned tracker — a loss; the learned-linking direction is closed.**
      `v6_trackastra_train.ipynb` converts our data into the standard tracking-benchmark format (synthesizing per-cell
      masks + a lineage file from our centroid+link labels) and continues training the pretrained model from its
      released weights. A mixed-specimen fine-tune trained cleanly, but on identical detections the fine-tuned tracker
      scored **below** the rule-based linker — and *below* even the zero-shot pretrained model. **Fine-tuning made it
      worse.** The loss is entirely on the **densest movies**: the learned tracker actually beats the rule-based linker
      on sparse movies but collapses where our detector fires most. The reason is a **train/inference mismatch** — the
      tracker is trained on clean masks built from one label per true cell, but at inference it must link our heavily
      **over-detected** points (tens of thousands of candidate detections where the truth has a few hundred links),
      which it never saw in training. This exposes a **fundamental tension**: the scoring metric rewards over-detection
      (extra detections are nearly free), which is exactly what our strategy exploits — but over-detection is *poison*
      to a learned attention tracker, while the rule-based motion-gated linker is naturally *robust* to it (spurious
      points simply never get linked). **All three learned-linking attempts (two zero-shot, one fine-tuned) fail to
      beat the rule-based linker**, so the learned-tracking bet did not pay off and the rule-based linker looks near the
      metric ceiling (the whole public field plateaus at the same score with the same rule-based linker). The best
      leaderboard score stays **0.844**.
- [x] **Global integer-program linking (tracksdata) — global optimisation alone is not the lever.** After confirming an
      offline ILP solver is packageable for the internet-off rerun, we swapped only the linker: same detector, a global
      integer program over the whole spatiotemporal graph instead of frame-to-frame matching. With a plain distance-based
      edge cost it *tied-to-lost* against the tuned rule-based linker (local edge-Jaccard 0.8508 vs 0.8594), losing on the
      densest videos. The rule-based linker already adds motion prediction and gap-closing that a pure-distance program
      lacks, so the headroom is in the **edge signal**, not the optimiser.
- [~] **Learned detector + learned edge scorer + global linker (planned, deferred).** The stronger public solutions pair a
      *learned* temporal detector and a *learned* pairwise edge-scoring model with the global linker (with native division
      handling), trained on the labelled pairs — replacing the "over-detect + rule-link" pipeline. This is the next planned
      direction; design is tracked privately and implementation is deferred.

See [`docs/experiments.md`](docs/experiments.md) for per-experiment configuration and results.

## Getting started

Each notebook in `src/` is designed to run on Kaggle: add the competition dataset as input,
enable GPU/Internet where noted, and Run All. No local data or setup is required.
