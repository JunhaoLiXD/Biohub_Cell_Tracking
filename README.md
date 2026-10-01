# Biohub Cell Tracking During Development

An experiment-driven solution for the Kaggle **Biohub — Cell Tracking During
Development** competition. The repository preserves both successful and failed
approaches so the evolution of the tracking pipeline can be inspected rather
than presenting only the final model.

## Final result

The retained solution reached **Public LB 0.953**. Two independently executed
final candidates reached the same score:

- `exp_064_x138_verbatim_repro` — submission `56535761`
- `exp_066_probe_cx03` — submission `56567455`

Later public-notebook reproductions with runtime post-processing selection did
not transfer to the hidden rerun (`repro_074`: 0.901, `repro_081`: 0.904), so
the 0.953 result remained the final selection.

## How to read the repository

The notebooks are the primary record of the work:

- [`src/early_versions`](src/early_versions) contains the original `v0`–`v7`
  progression: baseline tracking, U-Net training, fusion, division handling,
  isotropic training, Trackastra, and ILP experiments.
- [`src/MILESTONES.md`](src/MILESTONES.md) indexes the cleaned milestone
  notebooks from the controlled validation phase.
- [`experiments`](experiments) contains immutable notebook snapshots for the
  full experiment sequence, including rejected and diagnostic branches.
- [`configs`](configs) records the declared parent, exact change, validation
  protocol, and decision rule for controlled experiments.
- [`docs/experiments.md`](docs/experiments.md) and [`EXPERIMENTS.md`](EXPERIMENTS.md)
  provide compact experiment summaries.
- [`docs/research`](docs/research) preserves scientific proposals, failure
  analyses, and decision records behind later branches.

Within an experiment directory, the most useful files are usually:

```text
snapshot/source/*.ipynb   exact notebook prepared for execution
snapshot/config.yaml      frozen experiment configuration
snapshot/manifest.json    provenance and file hashes
experiment.json           state, result, and decision history
STATUS.md                 concise human-readable outcome
metrics.json / result.json
review.md                 final independent review, when applicable
```

Transient launch logs, agent prompts, local environments, model weights,
downloaded Kaggle artifacts, and credentials are intentionally excluded.

## Method outline

The project developed through several stages:

1. 3D detector baselines and sparse-label training.
2. Learned detection with transformer-based association and ILP decoding.
3. Frozen 16-video validation and causal DeepCenter diagnostics.
4. Motion-EMA, TTA, division-gate, and graph-repair experiments.
5. Reproduction and controlled modification of strong public solutions.
6. Final selection using leaderboard evidence and hidden-rerun robustness.

The final family uses dual pretrained 3D detection, learned association, ILP
tracking, motion/gap repair, and guarded division handling. Distances are
computed in physical coordinates using the competition voxel scale
`(1.625, 0.40625, 0.40625)`.

## Running a notebook

The notebooks were designed for Kaggle's offline environment. In general:

1. Import the selected notebook into Kaggle.
2. Attach the competition dataset and the model/support datasets named in its
   frozen config or notebook metadata.
3. Disable internet, enable the required accelerator, and run all cells.
4. Confirm that `submission.csv` is produced and that the notebook's integrity
   checks pass.

Large datasets, checkpoints, generated predictions, third-party dependency
bundles, and downloaded run artifacts are not stored in Git.

## Repository note

Some notebooks are exact, attributed reproductions of public competition
notebooks. Their surrounding manifests and experiment records distinguish
upstream code from project-authored modifications.
