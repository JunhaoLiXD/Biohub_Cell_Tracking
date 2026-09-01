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

## Retained configuration

- Full-resolution anisotropic 3D U-Net centroid detector
- Conservative heatmap threshold and no physical NMS
- Motion-aware two-pass Hungarian association
- Single-frame gap closing, isolated-node pruning, and minimum track length 4
- Geometric division recovery disabled

The main lesson is that local validation on sparse annotations can overvalue detection recall and permissive graph edits. Leaderboard gains came from better detector convergence and conservative association, not from emitting more nodes or divisions.
