# Selected experiments

Only experiments that changed the modeling conclusion are retained here. Detailed run artifacts and checkpoints are kept outside Git.

| Approach | Public LB | Conclusion |
|---|---:|---|
| Classical peak detection + nearest-neighbor linking | 0.669 | End-to-end anchor |
| 3D U-Net detector + nearest-neighbor linking | 0.768 | Learned detection transferred well |
| U-Net + motion-aware two-pass association | 0.827 | Better linking produced the largest early gain |
| High-recall detection with the same linker | 0.786 | Excess detection density was harmful |
| Geometric post-hoc divisions | 0.822 | Division false positives outweighed the bonus |
| Converged U-Net + motion-aware association | **0.844** | Retained public solution |
| Isotropic-grid detector | 0.838 | XY pooling lost localization precision |
| Wider full-resolution detector | 0.844 | Width was neutral |
| Wider detector with augmentation | 0.836 | Augmentation did not transfer |
| Public learned graph pipeline, controlled reproduction | 0.933 | Reproduced baseline and established a frozen 16-video comparison protocol |
| Motion EMA, independently reproduced | 0.933 | Internal train16 improved by 0.002064, but no Public LB change at displayed precision |
| Exact public `analyticaobscura` 0.941 copy | Pending (`56044403`) | Uses released pretrained weights without training; source, checkpoint load, and graph integrity passed |

## Current controlled evidence

The frozen train16 baseline scores 0.925252 overall, with 44b6 at 0.903658 and 6bba at 0.932950. The independently reproduced motion-EMA candidate scores 0.927316 and improves both specimens, but both its parent and its leaderboard submission score 0.933. This establishes a reproducible internal effect without evidence of a leaderboard gain.

The exact public-copy probe is a full configuration reproduction, not a causal ablation and not a model trained by this project. Its unchanged four-video validator scored 0.941822, but that small training-derived proxy is not comparable with train16 or Public LB. Submission 56044403 remains pending. A confirmed 0.941 would trigger a new train16 comparison that keeps public inference fixed and tests whether the complete configuration transfers across both specimens; it would not automatically become the project baseline.

## Retained configuration

- Full-resolution anisotropic 3D U-Net centroid detector
- Conservative heatmap threshold and no physical NMS
- Motion-aware two-pass Hungarian association
- Single-frame gap closing, isolated-node pruning, and minimum track length 4
- Geometric division recovery disabled

The main lesson is that local validation on sparse annotations can overvalue detection recall and permissive graph edits. Leaderboard gains came from better detector convergence and conservative association, not from emitting more nodes or divisions.
