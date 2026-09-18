# Automated Experiment Registry

This file is maintained by `scripts/update_results.py`. Detailed historical notebook notes remain
in `docs/experiments.md`.

| Experiment | State | Decision | Primary metric | Delta | Protocol |
|---|---|---|---:|---:|---|
| `baseline_public_0912` | EVALUATED | KEEP | 0.918800 | - | `v8_train40_leaky_delta_only` |
| `exp_001_v9_phase0_oracle` | EVALUATED | KEEP | - | - | `v9_phase0_oracle_train16_delta_only` |
| `repro_005_public_0933_contract_id` | KEEP | KEEP | 0.938165 | - | `public_0933_embedded_train4_proxy_v1` |
| `val_008_public_0933_train16_launchable` | KEEP | KEEP | 0.925252 | - | `public_0933_embedded_train16_stratified_proxy_v1` |
| `exp_011_train16_deepcenter_div_veto_envfix` | REJECT | REJECT | 0.916139 | -0.009113 | `public_0933_embedded_train16_stratified_proxy_v1` |
| `diag_012_train16_deepcenter_score_calibration` | KEEP | KEEP | 0.925252 | - | `public_0933_embedded_train16_stratified_proxy_v1` |
| `diag_013_train16_deepcenter_causal_calibration` | KEEP | KEEP | 0.925252 | - | `public_0933_embedded_train16_stratified_proxy_v1` |
| `diag_014_train16_preilp_edge_export` | KEEP | KEEP | 0.925252 | - | `public_0933_embedded_train16_stratified_proxy_v1` |
| `diag_018_train16_candidate_constrained_oracle_stageaware` | REJECT | REJECT | 0.062948 | - | `public_0933_train16_candidate_oracle_v1` |
| `diag_019_train16_final_validation_graph_export` | KEEP | KEEP | 0.925252 | - | `public_0933_embedded_train16_stratified_proxy_v1` |
| `diag_024_train16_stage_valid_final_graph_oracle` | REJECT | REJECT | 0.017193 | - | `public_0933_train16_candidate_oracle_v1` |
| `diag_025_train16_frozen_scorer_candidate_oracle` | KEEP | KEEP | 0.013152 | - | `public_0933_train16_candidate_oracle_v1` |
| `diag_026_train16_cross_specimen_feature_separability` | KEEP | KEEP | 0.797640 | - | `public_0933_train16_candidate_feature_separability_v1` |
| `diag_027_train16_cross_specimen_family_a_policy` | REJECT | REJECT | 0.000000 | - | `public_0933_train16_cross_specimen_family_a_policy_v1` |
| `diag_028_train16_deployment_complete_family_a_policy` | REJECT | REJECT | 0.000000 | - | `public_0933_train16_deployment_complete_family_a_policy_v1` |
| `diag_029_train16_factorized_family_a_policy` | REJECT | REJECT | 0.000000 | - | `public_0933_train16_factorized_family_a_policy_v1` |
| `diag_030_train16_eligible_validity_factorized_policy` | REJECT | REJECT | 0.000000 | - | `public_0933_train16_eligible_validity_factorized_policy_v1` |
| `diag_031_train16_structural_factorized_policy` | REJECT | REJECT | 0.000000 | - | `public_0933_train16_structural_factorized_policy_v1` |
| `diag_032_train16_structural_rank_transfer_policy` | REJECT | REJECT | 0.000000 | - | `public_0933_train16_structural_rank_transfer_policy_v1` |
| `diag_033_train16_node_validity_rank_policy` | REJECT | REJECT | 0.000000 | - | `public_0933_train16_node_validity_rank_policy_v1` |
| `exp_035_train16_motion_ema_reviewfix` | KEEP | KEEP | 0.927316 | +0.002064 | `public_0933_embedded_train16_stratified_proxy_v1` |
| `repro_036_train16_motion_ema` | KEEP | KEEP | 0.927316 | - | `public_0933_embedded_train16_stratified_proxy_v1` |
| `exp_037_train16_motion_ema_weight1` | REJECT | REJECT | 0.927742 | +0.000425 | `public_0933_embedded_train16_stratified_proxy_v1` |
| `repro_038_public_0941_exact_copy` | INCONCLUSIVE | INCONCLUSIVE | 0.941822 | - | `public_0941_unmodified_upstream_train4_lb_probe_v1` |
| `val_039_public_0941_train16` | KEEP | KEEP | 0.935978 | - | `public_0941_frozen_train16_stratified_proxy_v1` |
| `exp_040_public_0941_motion_ema` | KEEP | KEEP | 0.938733 | - | `public_0941_frozen_train16_stratified_proxy_v1` |
| `repro_041_public_0941_motion_ema` | KEEP | KEEP | 0.938733 | - | `public_0941_frozen_train16_stratified_proxy_v1` |
| `exp_042_public_0942_motion_ema_alpha06` | REJECT | REJECT | 0.937681 | - | `public_0941_frozen_train16_stratified_proxy_v1` |
| `exp_043_public_0942_motion_ema_adaptive_reset` | REJECT | REJECT | 0.936824 | - | `public_0941_frozen_train16_stratified_proxy_v1` |
| `diag_045_public_0942_motion_ema_telemetry_v2` | REJECT | REJECT | 0.938733 | - | `public_0941_frozen_train16_stratified_proxy_v1` |
| `exp_046_public_0942_motion_ema_sparse_soft` | REJECT | REJECT | 0.938734 | - | `public_0941_frozen_train16_stratified_proxy_v1` |
| `repro_048_public_0946_exact_copy` | INCONCLUSIVE | INCONCLUSIVE | 1.000000 | - | `public_0946_submission_integrity_lb_probe_v1` |
| `val_049_public_0944_train16` | KEEP | KEEP | 0.931070 | - | `public_0941_frozen_train16_stratified_proxy_v1` |
| `exp_050_public_0944_tta_off` | KEEP | KEEP | 0.935978 | - | `public_0941_frozen_train16_stratified_proxy_v1` |
| `diag_051_public_0942_tracklet_evidence` | KEEP | KEEP | 0.938733 | - | `public_0941_frozen_train16_stratified_proxy_v1` |
| `exp_055_original_score_joint_bootstrap_smoke_fix` | KEEP | KEEP | 0.953587 | - | `public_0941_frozen_train16_stratified_proxy_v1` |
| `exp_057_0944_motion_ema` | KEEP | KEEP | 1.000000 | - | `public_0944_plus_ema_submission_integrity_lb_probe_v1` |
