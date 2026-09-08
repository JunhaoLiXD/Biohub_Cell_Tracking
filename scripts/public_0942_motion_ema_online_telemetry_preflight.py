# Embedded after candidate test inference and before training-derived validation.
import math as _contract_math

_loaded = DEEPCENTER_VETO_DETECTOR
if _loaded is None:
    raise RuntimeError("Required DeepCenter model was not loaded")
_loaded_path = Path(_loaded["path"])
_loaded_hash = _sha256_file(_loaded_path)
_verified = _runtime_integrity_receipt
_candidate_submission_sha = _sha256_file(SUBMISSION_PATH)
_test_stats = pd.read_csv(RUN_STATS_PATH)
_telemetry_required = (
    "motion_relink_telemetry_eligible_updates",
    "motion_relink_telemetry_innovation_q50",
    "motion_relink_telemetry_track_age_q50",
    "motion_relink_telemetry_assignment_margin_q50",
    "motion_relink_telemetry_proposed_gt_1000",
    "motion_relink_telemetry_guarded_gt_1000",
)
_inference_checks = {
    "submission_created": SUBMISSION_PATH.is_file() and SUBMISSION_PATH.stat().st_size > 0,
    "submission_bytes_exact_parent": _candidate_submission_sha
        == "fd1162bfc09b6d06413701aa898eb14bc5df9cc5bfd999fe598bf81fbf125515",
    "deepcenter_path_bound": str(_loaded_path) == _verified["materialized_paths"]["deepcenter"],
    "deepcenter_best_pt": _loaded_path.name == "best.pt",
    "deepcenter_epoch2": _loaded["checkpoint_epoch"] == DEEPCENTER_EXPECTED_EPOCH == 2,
    "deepcenter_hash_bound": _loaded_hash == _loaded["checkpoint_sha256"]
        == _verified["checkpoint_sha256"]["deepcenter"]
        == "8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0",
    "primary_hash_exact": _verified["checkpoint_sha256"]["primary"]
        == "12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771",
    "secondary_hash_exact": _verified["checkpoint_sha256"]["secondary"]
        == "9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f",
    "dual_t4": torch.cuda.device_count() == 2
        and all("T4" in torch.cuda.get_device_name(i) for i in range(2)),
    "test_telemetry_four_videos": len(_test_stats) == 4,
    "test_telemetry_fields_complete": set(_telemetry_required).issubset(_test_stats.columns),
}
_expected_effective = {
    "det_threshold": (DET_THRESHOLD, 0.965),
    "secondary_detection_weight": (float(os.environ["BIOHUB_SECONDARY_DETECTION_WEIGHT"]), 0.8),
    "bidirectional_weight": (float(os.environ["BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT"]), 0.15),
    "gap_close_um": (GAP_CLOSE_UM, 5.0),
    "division_parent_um": (SAFE_DIV_MAX_UM, 9.0),
    "division_sister_um": (SAFE_DIV_SISTER_MAX_UM, 14.0),
    "sister_symmetry": (SAFE_DIV_SISTER_SYMMETRY_TAU, 0.6),
    "deepcenter_division_threshold": (DEEPCENTER_SAFE_DIV_THRESHOLD, 0.25),
    "motion_velocity_weight": (MOTION_RELINK_VELOCITY_WEIGHT, 0.5),
    "motion_ema_alpha": (MOTION_RELINK_EMA_ALPHA, 0.4),
}
_inference_checks.update({
    "effective_" + key: _contract_math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12)
    for key, (actual, expected) in _expected_effective.items()
})
_inference_receipt = {
    "parent": "repro_041_public_0941_motion_ema",
    "change": "online_motion_telemetry_only",
    "parent_submission_sha256": "fd1162bfc09b6d06413701aa898eb14bc5df9cc5bfd999fe598bf81fbf125515",
    "submission_sha256": _candidate_submission_sha,
    "actual_checkpoint": {"path": str(_loaded_path), "epoch": _loaded["checkpoint_epoch"],
                          "sha256": _loaded_hash},
    "checks": _inference_checks,
    "configuration": _guard_report["configuration"],
    "environment": {key: value for key, value in os.environ.items() if key.startswith("BIOHUB_")},
    "test_online_telemetry": _test_stats[["dataset", *_telemetry_required]].to_dict(orient="records")
        if set(_telemetry_required).issubset(_test_stats.columns) else [],
}
(WORKING_DIR / "inference_identity.json").write_text(
    json.dumps(_inference_receipt, indent=2, sort_keys=True), encoding="utf-8")
if not all(_inference_checks.values()):
    raise RuntimeError({"inference_identity_failed": [key for key, value in _inference_checks.items() if not value]})
print("Candidate inference integrity PASS: telemetry-only fixed alpha 0.4 and exact parent submission")
