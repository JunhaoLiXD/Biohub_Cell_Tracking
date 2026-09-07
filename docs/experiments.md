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
| Exact public `analyticaobscura` 0.941 copy | **0.941** (`56044403`, COMPLETE) | Selected working research parent; released pretrained weights, source/load/graph audits passed |
| Public 0.941 frozen train16 baseline | No new submission | `val_039_public_0941_train16` KEEP: 0.935978 train16, exact test inference preserved; new controlled working parent |
| Motion EMA transferred to public 0.941 parent | No new submission | `exp_040_public_0941_motion_ema` KEEP: train16 0.938733 (+0.002755); both specimens improved, awaiting exact reproduction |

## Current controlled evidence

The frozen train16 baseline scores 0.925252 overall, with 44b6 at 0.903658 and 6bba at 0.932950. The independently reproduced motion-EMA candidate scores 0.927316 and improves both specimens, but both its parent and its leaderboard submission score 0.933. This establishes a reproducible internal effect without evidence of a leaderboard gain.

The exact public-copy probe reproduced Public LB 0.941 (submission 56044403 COMPLETE). Its native train4 score 0.941822 is not comparable with train16. `val_039_public_0941_train16` preserved those exact test bytes and established a fixed train16 score of 0.935978 (44b6 0.921800, 6bba 0.940332). Versus the old 0.933 configuration, the paired gain is +0.010726; division TP/FN stayed 4/8 while FP fell from 25 to 9. This complete configuration result does not identify individual causes.

`exp_040_public_0941_motion_ema` then changed only motion velocity estimation to per-track EMA (alpha 0.4, weight 0.5). It improved the matched train16 score to 0.938733 (+0.002755), with adjusted edge +0.001803 and division Jaccard +0.009524. Both specimen aggregates improved, and division TP/FP/FN moved from 4/9/8 to 4/8/8. The response was heterogeneous across videos, so the candidate requires one exact independent reproduction before any separately authorized leaderboard submission or formal promotion.

## Historical self-contained configuration (0.844)

- Full-resolution anisotropic 3D U-Net centroid detector
- Conservative heatmap threshold and no physical NMS
- Motion-aware two-pass Hungarian association
- Single-frame gap closing, isolated-node pruning, and minimum track length 4
- Geometric division recovery disabled

The main lesson is that local validation on sparse annotations can overvalue detection recall and permissive graph edits. Leaderboard gains came from better detector convergence and conservative association, not from emitting more nodes or divisions.
