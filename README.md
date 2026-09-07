# Biohub Cell Tracking During Development

An end-to-end Kaggle solution for detecting and tracking cells through 3D time-lapse microscopy of developing zebrafish embryos.

## Current approach

The working research parent is the reproduced public `analyticaobscura/biohub-lb-941`
configuration: dual pretrained TemporalUNet3D detections, transformer association,
ILP tracking, motion/gap repair, and geometry plus epoch-2 DeepCenter division gates.
Submission 56044403 completed at Public LB **0.941**. No new model was trained.
`val_039_public_0941_train16` established its fixed 16-video validation baseline at
**0.935978** with identical test inference (44b6 0.921800; 6bba 0.940332). See
[research handoff and traceability](docs/research_workflow.md).
The single-variable motion-EMA transfer `exp_040_public_0941_motion_ema` improved
that matched proxy to **0.938733** (+0.002755) and passed all configured gates.
It is a positive candidate awaiting exact reproduction, not yet leaderboard evidence.

## Historical self-contained approach

The pipeline follows a tracking-by-detection design:

1. A full-resolution anisotropic 3D U-Net predicts centroid heatmaps.
2. Local maxima are converted into cell detections in physical `(z, y, x)` coordinates.
3. Two-pass motion-aware Hungarian assignment links detections between frames.
4. Gap closing, isolated-node pruning, and short-track filtering repair fragmented tracks.
5. The final graph is serialized to the competition's `submission.csv` format.

The detector is trained with sparse annotations and cosine learning-rate decay. Distances are measured in microns using the competition voxel scale `(1.625, 0.40625, 0.40625)`. Geometric post-hoc division edges are disabled because they reduced the leaderboard score in controlled tests.

## Current research status

The original self-contained pipeline reached Public LB **0.844**. The current controlled research line reproduced a public learned detector/linker configuration at **0.933** and established a deterministic 16-video internal validation protocol. A motion-EMA change improved that internal score from 0.925252 to 0.927316 in two byte-identical runs, but its Public LB remained 0.933.

An exact copy of `analyticaobscura/biohub-lb-941` reproduced **0.941** under our account (submission `56044403`, COMPLETE). Source, actual epoch-2 DeepCenter loading and submission graph passed audits. The user selected this full configuration as the new working research parent. `val_039_public_0941_train16` established its fixed train16 baseline while preserving inference. On that frozen protocol, isolated motion EMA improved train16 from 0.935978 to 0.938733; both specimens improved and division FP fell by one. The result still needs exact reproduction and has not been submitted to the leaderboard. The parent train4 proxy is not comparable with train16. Formal promotion remains separate.

See [selected experiments](docs/experiments.md) for the compact evidence behind the retained configuration.

## Repository

```text
src/
  submit.ipynb                 offline Kaggle inference and submission notebook
  biohub_v01_*.ipynb           frozen train16 validation baseline
  biohub_v02_*.ipynb           DeepCenter causal calibration milestone
  biohub_v03_*.ipynb           candidate-oracle diagnostic milestone
  biohub_v04_*.ipynb           reproducible motion-EMA milestone
  util_inspect_data.ipynb      dataset and tracking-graph inspection
  util_download_wheels.ipynb   offline dependency-bundle builder
```

Large datasets, model checkpoints, generated outputs, run logs, and third-party reference material are intentionally excluded from Git.

## Running on Kaggle

1. Open `src/submit.ipynb` as a Kaggle notebook.
2. Attach the competition data, the offline dependency bundle, and the matching detector checkpoint dataset.
3. Select the detector configuration that matches the attached checkpoint.
4. Disable internet access and enable a GPU.
5. Run all cells and confirm that `/kaggle/working/submission.csv` is produced.

The notebook validates its inputs and prints per-movie node and edge counts. A movie with zero detections indicates a checkpoint or configuration mismatch and should not be submitted.

## Competition

[Biohub — Cell Tracking During Development](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development)
