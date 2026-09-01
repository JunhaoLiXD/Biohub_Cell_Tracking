# Biohub Cell Tracking During Development

An end-to-end Kaggle solution for detecting and tracking cells through 3D time-lapse microscopy of developing zebrafish embryos.

## Approach

The pipeline follows a tracking-by-detection design:

1. A full-resolution anisotropic 3D U-Net predicts centroid heatmaps.
2. Local maxima are converted into cell detections in physical `(z, y, x)` coordinates.
3. Two-pass motion-aware Hungarian assignment links detections between frames.
4. Gap closing, isolated-node pruning, and short-track filtering repair fragmented tracks.
5. The final graph is serialized to the competition's `submission.csv` format.

The detector is trained with sparse annotations and cosine learning-rate decay. Distances are measured in microns using the competition voxel scale `(1.625, 0.40625, 0.40625)`. Geometric post-hoc division edges are disabled because they reduced the leaderboard score in controlled tests.

## Result

The retained self-contained pipeline achieved a public leaderboard score of **0.844**. Its main gains came from detector convergence and motion-aware association while keeping detection density conservative.

See [selected experiments](docs/experiments.md) for the compact evidence behind the retained configuration.

## Repository

```text
src/
  submit.ipynb                 offline Kaggle inference and submission notebook
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
