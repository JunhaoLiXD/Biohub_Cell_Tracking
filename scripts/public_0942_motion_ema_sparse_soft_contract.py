# Embedded final contract for the sparse soft-EMA candidate.
_EXPERIMENT_ID = "__CONTROLLER_EXPERIMENT_ID__"
_PROTOCOL = "public_0941_frozen_train16_stratified_proxy_v1"
_MINIMUM_IMPROVEMENT = 0.0001
_SPECIMEN_ADJUSTED_EDGE_TOLERANCE = 0.001
_WORST_VIDEO_DELTA_FLOOR = -0.002

if len(validator_summary_rows) != 1:
    raise RuntimeError("Expected exactly one train16 summary")
_summary = validator_summary_rows[0]
_specimens = {}
for _specimen in ("44b6", "6bba"):
    _rows = [row for row in validator_sample_rows if row["stem"].startswith(_specimen + "_")]
    _aggregate = aggregate_official(_rows)
    _baseline = SPARSE_SOFT_EXPECTED["specimens"][_specimen]
    _specimens[_specimen] = {
        "primary_metric": float(_aggregate["proxy_score"]),
        "baseline_primary_metric": float(_baseline["primary_metric"]),
        "delta": float(_aggregate["proxy_score"] - _baseline["primary_metric"]),
        "adjusted_edge_jaccard": float(_aggregate["adjusted_edge_jaccard"]),
        "baseline_adjusted_edge_jaccard": float(_baseline["adjusted_edge_jaccard"]),
        "adjusted_edge_delta": float(
            _aggregate["adjusted_edge_jaccard"] - _baseline["adjusted_edge_jaccard"]),
        "division_jaccard": float(_aggregate["division_jaccard"]),
        "samples": [row["stem"] for row in _rows],
        "division_positive_samples": [
            row["stem"] for row in _rows if division_flags[row["stem"]]],
    }
_overall = aggregate_official(validator_sample_rows)
_video_deltas_vs_parent = {
    row["stem"]: float(
        row["adjusted_edge_jaccard"]
        - SPARSE_SOFT_EXPECTED["videos"][row["stem"]]["adjusted_edge_jaccard"])
    for row in validator_sample_rows
}
_worst_video = min(_video_deltas_vs_parent, key=_video_deltas_vs_parent.get)
_validation_telemetry = {
    stem: {key: stats.get(key) for key in _telemetry_required}
    for stem, stats in VALIDATION_STAGE_STATS.items()
}
_telemetry_complete = (
    set(_validation_telemetry) == set(val_stems)
    and all(all(value is not None for value in values.values())
            for values in _validation_telemetry.values())
    and all(_telemetry_row_contract(values) for values in _validation_telemetry.values())
)
_native_count_types = _telemetry_complete and all(
    type(values[field]) is int
    for values in _validation_telemetry.values()
    for field in (*_count_fields, *_policy_fields)
)
try:
    _validation_stage_stats_json = json.dumps(
        VALIDATION_STAGE_STATS, indent=2, sort_keys=True, allow_nan=False)
    _stage_stats_json_serializable = True
except (TypeError, ValueError):
    _validation_stage_stats_json = ""
    _stage_stats_json_serializable = False

_sparse_execution = {
    specimen: {
        "ema_predictions": int(sum(row.get("motion_relink_ema_predictions", 0)
            for row in validator_sample_rows if row["stem"].startswith(specimen + "_"))),
        "soft_updates": int(sum(row.get("motion_relink_sparse_soft_updates", 0)
            for row in validator_sample_rows if row["stem"].startswith(specimen + "_"))),
        "base_updates": int(sum(row.get("motion_relink_sparse_base_updates", 0)
            for row in validator_sample_rows if row["stem"].startswith(specimen + "_"))),
        "initial_updates": int(sum(row.get("motion_relink_sparse_initial_updates", 0)
            for row in validator_sample_rows if row["stem"].startswith(specimen + "_"))),
        "one_frame_fallbacks": int(sum(row.get("motion_relink_one_frame_fallbacks", 0)
            for row in validator_sample_rows if row["stem"].startswith(specimen + "_"))),
        "skipped_large_frames": int(sum(row.get("motion_relink_skipped_large_frame", 0)
            for row in validator_sample_rows if row["stem"].startswith(specimen + "_"))),
    }
    for specimen in ("44b6", "6bba")
}
_contract_checks = {
    **_inference_checks,
    "experiment_id_injected": _EXPERIMENT_ID == "exp_046_public_0942_motion_ema_sparse_soft",
    "frozen_samples_and_order": all(
        _specimens[s]["samples"] == FROZEN_SAMPLES[s] for s in FROZEN_SAMPLES),
    "frozen_strata": all(
        set(_specimens[s]["division_positive_samples"]) == set(FROZEN_POSITIVES[s])
        for s in FROZEN_SAMPLES),
    "video_parent_baseline_complete": set(_video_deltas_vs_parent)
        == set(SPARSE_SOFT_EXPECTED["videos"]),
    "sample_count": len(validator_sample_rows) == int(_summary["n_samples"]) == 16,
    "finite_scores": all(
        _contract_math.isfinite(float(row[key]))
        for row in validator_sample_rows
        for key in ("weight", "adjusted_edge_jaccard", "div_tp", "div_fp", "div_fn")),
    "candidate_submission_unchanged_after_validation": _sha256_file(SUBMISSION_PATH)
        == _inference_receipt["submission_sha256"],
    "stage_stats_complete": set(VALIDATION_STAGE_STATS) == set(val_stems),
    "online_telemetry_complete": _telemetry_complete,
    "telemetry_count_types_native_int": _native_count_types,
    "validation_stage_stats_json_serializable": _stage_stats_json_serializable,
    "sparse_soft_exercised_both_specimens": all(
        values["soft_updates"] > 0 for values in _sparse_execution.values()),
    "sparse_base_exercised_both_specimens": all(
        values["base_updates"] > 0 for values in _sparse_execution.values()),
}
_research_gates = {
    "aggregate_improvement_at_least_0_0001": float(_summary["proxy_score"])
        >= SPARSE_SOFT_EXPECTED["aggregate"]["primary_metric"] + _MINIMUM_IMPROVEMENT,
    "adjusted_edge_no_material_specimen_regression_vs_parent": all(
        metrics["adjusted_edge_delta"] >= -_SPECIMEN_ADJUSTED_EDGE_TOLERANCE
        for metrics in _specimens.values()),
    "worst_video_delta_vs_parent_at_least_minus_0_002": (
        _video_deltas_vs_parent[_worst_video] >= _WORST_VIDEO_DELTA_FLOOR),
    "division_tp_at_least_4": int(_overall["div_tp"]) >= 4,
    "division_fp_at_most_8": int(_overall["div_fp"]) <= 8,
    "division_fn_at_most_8": int(_overall["div_fn"]) <= 8,
}
_metrics = {
    "schema_version": 1,
    "experiment_id": _EXPERIMENT_ID,
    "primary_metric": float(_summary["proxy_score"]),
    "baseline_primary_metric": SPARSE_SOFT_EXPECTED["aggregate"]["primary_metric"],
    "runtime_seconds": _run_time.perf_counter() - RUN_STARTED_AT,
    "reproducible": False,
    "validation": {
        "protocol": _PROTOCOL,
        "sample_count": 16,
        "adjusted_edge_jaccard": float(_summary["adjusted_edge_jaccard"]),
        "division_jaccard": float(_summary["division_jaccard"]),
        "selection_and_scorer_reference": "val_039_public_0941_train16",
        "warning": "Frozen models saw training videos; this is an optimistic paired policy test.",
    },
    "specimen_metrics": _specimens,
    "metrics": {
        "validation_contract_passed": all(_contract_checks.values()),
        "sparse_soft_ema_candidate_gate_passed": (
            all(_contract_checks.values()) and all(_research_gates.values())),
        "checks": _contract_checks,
        "research_gates": _research_gates,
        "failed_checks": [key for key, value in _contract_checks.items() if not value],
        "failed_research_gates": [key for key, value in _research_gates.items() if not value],
        "video_response_vs_parent": {
            "deltas": _video_deltas_vs_parent,
            "positive": sum(value > 0 for value in _video_deltas_vs_parent.values()),
            "zero": sum(value == 0 for value in _video_deltas_vs_parent.values()),
            "negative": sum(value < 0 for value in _video_deltas_vs_parent.values()),
            "worst_video": _worst_video,
            "worst_delta": _video_deltas_vs_parent[_worst_video],
        },
        "online_telemetry": _validation_telemetry,
        "motion_relink_sparse_execution": _sparse_execution,
        "motion_relink_velocity_estimator": "sparse_soft_ema",
        "motion_relink_velocity_weight": MOTION_RELINK_VELOCITY_WEIGHT,
        "motion_relink_ema_base_alpha": MOTION_RELINK_EMA_ALPHA,
        "motion_relink_ema_soft_alpha": MOTION_RELINK_EMA_SOFT_ALPHA,
        "motion_relink_ema_innovation_threshold": MOTION_RELINK_EMA_INNOVATION_THRESHOLD,
        "motion_relink_ema_min_track_age": MOTION_RELINK_EMA_MIN_TRACK_AGE,
        "motion_relink_ema_min_assignment_margin": MOTION_RELINK_EMA_MIN_ASSIGNMENT_MARGIN,
        "inference_identity": _inference_receipt,
        "parent_experiment": "repro_041_public_0941_motion_ema",
        "evidence_donor": "diag_045_public_0942_motion_ema_telemetry_v2",
        "candidate_submission_sha256": _inference_receipt["submission_sha256"],
        "division_counts": {key: int(_overall[key]) for key in ("div_tp", "div_fp", "div_fn")},
    },
}
_metrics_json = json.dumps(_metrics, indent=2, sort_keys=True, allow_nan=False)
if not _stage_stats_json_serializable:
    raise RuntimeError("Validation stage statistics failed strict JSON serialization")
(WORKING_DIR / "validation_stage_stats.json").write_text(
    _validation_stage_stats_json, encoding="utf-8")
(WORKING_DIR / "metrics.json").write_text(_metrics_json, encoding="utf-8")
print(_metrics_json)
