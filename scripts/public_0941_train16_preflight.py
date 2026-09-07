# Embedded after test inference and audit, before training-derived validation.
import math as _contract_math

_loaded = DEEPCENTER_VETO_DETECTOR
if _loaded is None:
    raise RuntimeError("Required DeepCenter model was not loaded")
_loaded_path = Path(_loaded["path"])
_loaded_hash = _sha256_file(_loaded_path)
_verified = _runtime_integrity_receipt
_inference_checks = {
    "submission_sha256_exact": _sha256_file(SUBMISSION_PATH) == EXPECTED_SUBMISSION_SHA,
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
}
_inference_checks.update({
    "effective_" + k: _contract_math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12)
    for k, (actual, expected) in _expected_effective.items()
})
_inference_receipt = {
    "parent": "repro_038_public_0941_exact_copy",
    "submission_sha256": _sha256_file(SUBMISSION_PATH),
    "actual_checkpoint": {"path": str(_loaded_path), "epoch": _loaded["checkpoint_epoch"],
                          "sha256": _loaded_hash},
    "checks": _inference_checks,
    "configuration": _guard_report["configuration"],
    "environment": {k: v for k, v in os.environ.items() if k.startswith("BIOHUB_")},
}
(WORKING_DIR / "inference_identity.json").write_text(
    json.dumps(_inference_receipt, indent=2, sort_keys=True), encoding="utf-8")
if not all(_inference_checks.values()):
    raise RuntimeError({"inference_identity_failed": [k for k, v in _inference_checks.items() if not v]})
print("Inference identity PASS: exact repro_038 submission and actual epoch-2 checkpoint")
