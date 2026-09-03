# Milestone Notebooks

Milestone notebooks are cleaned, local snapshots of substantial completed research stages. Routine
fixes and inconclusive experiments remain in the experiment controller history and are not copied
here. Existing milestone versions are immutable and must not be overwritten.

| Version | Notebook | Source experiment | Status | Summary |
|---|---|---|---|---|
| v01 | `biohub_v01_train16_baseline.ipynb` | `val_008_public_0933_train16_launchable` | Frozen internal baseline | Deterministic 16-video stratified validator; score 0.925252, 44b6 0.903658, 6bba 0.932950. |
| v02 | `biohub_v02_deepcenter_causal_calibration.ipynb` | `diag_013_train16_deepcenter_causal_calibration` | Completed diagnostic milestone | Exact baseline preservation plus 1,130 retained-edge ablations; scalar DeepCenter thresholding rejected as non-discriminative. |
| v03 | `biohub_v03_candidate_oracle_gate.ipynb` | `diag_025_train16_frozen_scorer_candidate_oracle` | Phase 0 gate passed | Exact frozen-baseline reproduction; candidate-reachable family A and ABC oracle headroom is positive on both specimens. |
| v04 | `biohub_v04_motion_ema.ipynb` | `repro_036_train16_motion_ema` | Reproducible method improvement | Per-track motion EMA improved train16 score from 0.925252 to 0.927316 on both specimens; an independent run reproduced exact metrics and a byte-identical submission. |
