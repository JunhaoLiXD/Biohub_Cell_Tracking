# Early notebook sequence

These notebooks preserve the project's initial iteration history before the
formal experiment-controller phase.

| Notebook | Main idea |
|---|---|
| `v0_baseline.ipynb` | Initial end-to-end tracking baseline |
| `v1_unet_train.ipynb` | First 3D U-Net training pipeline |
| `v2_fusion_eval.ipynb` | Detector/output fusion evaluation |
| `v2_5_highrecall_eval.ipynb` | Higher-recall detection variant |
| `v3_divisions_eval.ipynb` | Explicit cell-division experiments |
| `v4_isotropic_train.ipynb` | Isotropic-resampling training variant |
| `v5_base24_aug_train.ipynb` | Wider augmented detector training |
| `v6_trackastra_train.ipynb` | Trackastra-based association attempt |
| `v7_tracksdata_ilp_eval.ipynb` | TracksData/ILP evaluation |
| `v8_two_seeds_local_eval.ipynb` | Dual-seed detector and learned association evaluation |
| `v8_two_seeds_submit.ipynb` | Submission form of the dual-seed pipeline |

The two `util_*` notebooks document offline dependency and integration tests
used during this period. These are historical working notebooks, not polished
release artifacts.
