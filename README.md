# Biohub Cell Tracking During Development

An end-to-end Kaggle solution for detecting and tracking cells through 3D time-lapse microscopy of developing zebrafish embryos.

## Current approach

For the authoritative project state, active-run restrictions, and the Claude
Code/Codex consensus workflow, read [the current project handoff](docs/research/PROJECT_HANDOFF.md).

The working research parent is the reproduced public `analyticaobscura/biohub-lb-941`
configuration: dual pretrained TemporalUNet3D detections, transformer association,
ILP tracking, motion/gap repair, and epoch-2 DeepCenter division gates.
`repro_041_public_0941_motion_ema` is the exactly reproduced train16 reference at
**0.9387332376874039** with fixed motion EMA alpha 0.4 and user-reported Public LB
0.942. A separate verified public reference, submission `56105868`, scored Public
LB **0.944**. The active run is `exp_055_original_score_joint_bootstrap_smoke_fix`,
which is pending the user's completion notice and has no leaderboard submission or
promotion authorization. See [the current project handoff](docs/research/PROJECT_HANDOFF.md).

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
