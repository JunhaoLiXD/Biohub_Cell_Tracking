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
_threshold_codes = (1000, 1250, 1500, 1750)
_quantile_fields = tuple(
    f"motion_relink_telemetry_{prefix}_q{quantile}"
    for prefix in ("innovation", "track_age", "assignment_margin")
    for quantile in (10, 50, 90, 95, 99)
)
_count_fields = (
    "motion_relink_telemetry_eligible_updates",
    "motion_relink_telemetry_finite_margin_updates",
    "motion_relink_telemetry_nonfinite_margin_updates",
) + tuple(
    f"motion_relink_telemetry_{prefix}_gt_{code}"
    for prefix in ("proposed", "age_ge3", "finite_margin", "margin_ge0500", "guarded")
    for code in _threshold_codes
)
_policy_fields = (
    "motion_relink_sparse_soft_updates",
    "motion_relink_sparse_base_updates",
    "motion_relink_sparse_initial_updates",
)
_telemetry_required = (*_quantile_fields, *_count_fields, *_policy_fields)
_telemetry_columns_complete = set(_telemetry_required).issubset(_test_stats.columns)
_test_records = (
    _test_stats[["dataset", *_telemetry_required]].to_dict(orient="records")
    if _telemetry_columns_complete else []
)
try:
    _test_telemetry_json = json.dumps(_test_records, allow_nan=False, sort_keys=True)
    _test_telemetry_json_serializable = True
except (TypeError, ValueError):
    _test_telemetry_json = ""
    _test_telemetry_json_serializable = False


def _telemetry_row_contract(row):
    eligible = int(row["motion_relink_telemetry_eligible_updates"])
    finite = int(row["motion_relink_telemetry_finite_margin_updates"])
    nonfinite = int(row["motion_relink_telemetry_nonfinite_margin_updates"])
    soft = int(row["motion_relink_sparse_soft_updates"])
    base = int(row["motion_relink_sparse_base_updates"])
    initial = int(row["motion_relink_sparse_initial_updates"])
    coverage_ok = eligible > 0 and finite >= 0 and nonfinite >= 0 and finite + nonfinite == eligible
    policy_ok = soft > 0 and base > 0 and initial >= 0 and soft + base == eligible
    policy_ok = policy_ok and soft == int(row["motion_relink_telemetry_guarded_gt_1250"])
    bounds_ok = True
    for code in _threshold_codes:
        proposed = int(row[f"motion_relink_telemetry_proposed_gt_{code}"])
        age = int(row[f"motion_relink_telemetry_age_ge3_gt_{code}"])
        finite_margin = int(row[f"motion_relink_telemetry_finite_margin_gt_{code}"])
        margin = int(row[f"motion_relink_telemetry_margin_ge0500_gt_{code}"])
        guarded = int(row[f"motion_relink_telemetry_guarded_gt_{code}"])
        bounds_ok = bounds_ok and (
            0 <= guarded <= age <= proposed <= eligible
            and 0 <= guarded <= margin <= finite_margin <= proposed
        )
    monotonic_ok = all(
        all(
            int(row[f"motion_relink_telemetry_{prefix}_gt_{left}"])
            >= int(row[f"motion_relink_telemetry_{prefix}_gt_{right}"])
            for left, right in zip(_threshold_codes, _threshold_codes[1:])
        )
        for prefix in ("proposed", "age_ge3", "finite_margin", "margin_ge0500", "guarded")
    )
    quantiles_ok = all(_contract_math.isfinite(float(row[field])) for field in _quantile_fields)
    innovation_bound_ok = float(row["motion_relink_telemetry_innovation_q99"]) <= 2.0 + 1e-12
    return coverage_ok and policy_ok and bounds_ok and monotonic_ok and quantiles_ok and innovation_bound_ok


_inference_checks = {
    "submission_created": SUBMISSION_PATH.is_file() and SUBMISSION_PATH.stat().st_size > 0,
    "submission_sha256_valid": len(_candidate_submission_sha) == 64
        and all(ch in "0123456789abcdef" for ch in _candidate_submission_sha),
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
    "test_telemetry_fields_complete": _telemetry_columns_complete,
    "test_telemetry_json_serializable": _test_telemetry_json_serializable,
    "test_sparse_policy_contract": _telemetry_columns_complete
        and all(_telemetry_row_contract(row) for row in _test_records),
    "test_sparse_policy_exercised_both_specimens": _telemetry_columns_complete and all(
        sum(int(row["motion_relink_sparse_soft_updates"])
            for row in _test_records if row["dataset"].startswith(specimen + "_")) > 0
        for specimen in ("44b6", "6bba")
    ),
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
    "motion_ema_base_alpha": (MOTION_RELINK_EMA_ALPHA, 0.4),
    "motion_ema_soft_alpha": (MOTION_RELINK_EMA_SOFT_ALPHA, 0.6),
    "motion_ema_innovation_threshold": (MOTION_RELINK_EMA_INNOVATION_THRESHOLD, 1.25),
    "motion_ema_min_track_age": (MOTION_RELINK_EMA_MIN_TRACK_AGE, 3),
    "motion_ema_min_assignment_margin": (MOTION_RELINK_EMA_MIN_ASSIGNMENT_MARGIN, 0.5),
}
_inference_checks.update({
    "effective_" + key: _contract_math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12)
    for key, (actual, expected) in _expected_effective.items()
})
_inference_receipt = {
    "parent": "repro_041_public_0941_motion_ema",
    "evidence_donor": "diag_045_public_0942_motion_ema_telemetry_v2",
    "change": "sparse_soft_ema_update_only",
    "parent_submission_sha256": PARENT_SUBMISSION_SHA,
    "submission_sha256": _candidate_submission_sha,
    "actual_checkpoint": {"path": str(_loaded_path), "epoch": _loaded["checkpoint_epoch"],
                          "sha256": _loaded_hash},
    "checks": _inference_checks,
    "configuration": _guard_report["configuration"],
    "environment": {key: value for key, value in os.environ.items() if key.startswith("BIOHUB_")},
    "test_online_telemetry": _test_records,
}
_inference_receipt_json = json.dumps(_inference_receipt, indent=2, sort_keys=True, allow_nan=False)
(WORKING_DIR / "inference_identity.json").write_text(_inference_receipt_json, encoding="utf-8")
if not all(_inference_checks.values()):
    raise RuntimeError({"inference_identity_failed": [key for key, value in _inference_checks.items() if not value]})
print("Candidate inference integrity PASS: sparse soft EMA and actual epoch-2 checkpoint")
