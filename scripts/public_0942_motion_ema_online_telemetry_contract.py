# Embedded final contract for the telemetry-only fixed-alpha-0.4 diagnostic.
_EXPERIMENT_ID = "__CONTROLLER_EXPERIMENT_ID__"
_PROTOCOL = "public_0941_frozen_train16_stratified_proxy_v1"
_ABS_TOL = 1e-12

def _telemetry_close(actual, expected):
    return _contract_math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=_ABS_TOL)

if len(validator_summary_rows) != 1:
    raise RuntimeError("Expected exactly one train16 summary")
_summary = validator_summary_rows[0]
_specimens = {}
for _specimen in ("44b6", "6bba"):
    _rows = [row for row in validator_sample_rows if row["stem"].startswith(_specimen + "_")]
    _aggregate = aggregate_official(_rows)
    _specimens[_specimen] = {
        "primary_metric": float(_aggregate["proxy_score"]),
        "adjusted_edge_jaccard": float(_aggregate["adjusted_edge_jaccard"]),
        "division_jaccard": float(_aggregate["division_jaccard"]),
        "samples": [row["stem"] for row in _rows],
    }
_overall = aggregate_official(validator_sample_rows)
_video_metrics = {
    row["stem"]: {
        "adjusted_edge_jaccard": float(row["adjusted_edge_jaccard"]),
        "div_tp": int(row["div_tp"]), "div_fp": int(row["div_fp"]), "div_fn": int(row["div_fn"]),
    }
    for row in validator_sample_rows
}
_telemetry_fields = (
    "motion_relink_telemetry_eligible_updates",
    "motion_relink_telemetry_innovation_q10", "motion_relink_telemetry_innovation_q50",
    "motion_relink_telemetry_innovation_q90", "motion_relink_telemetry_innovation_q95",
    "motion_relink_telemetry_innovation_q99", "motion_relink_telemetry_track_age_q50",
    "motion_relink_telemetry_track_age_q90", "motion_relink_telemetry_assignment_margin_q50",
    "motion_relink_telemetry_assignment_margin_q90",
    "motion_relink_telemetry_proposed_gt_1000", "motion_relink_telemetry_proposed_gt_1250",
    "motion_relink_telemetry_proposed_gt_1500", "motion_relink_telemetry_proposed_gt_2000",
    "motion_relink_telemetry_proposed_gt_3000", "motion_relink_telemetry_guarded_gt_1000",
    "motion_relink_telemetry_guarded_gt_1250", "motion_relink_telemetry_guarded_gt_1500",
    "motion_relink_telemetry_guarded_gt_2000", "motion_relink_telemetry_guarded_gt_3000",
)
_validation_telemetry = {
    stem: {key: stats.get(key) for key in _telemetry_fields}
    for stem, stats in VALIDATION_STAGE_STATS.items()
}
_telemetry_complete = (
    set(_validation_telemetry) == set(val_stems)
    and all(all(value is not None and _contract_math.isfinite(float(value)) for value in values.values())
            for values in _validation_telemetry.values())
    and all(values["motion_relink_telemetry_eligible_updates"] > 0
            for values in _validation_telemetry.values())
)
_threshold_codes = (1000, 1250, 1500, 2000, 3000)
_telemetry_monotonic = all(
    all(values[f"motion_relink_telemetry_proposed_gt_{left}"]
        >= values[f"motion_relink_telemetry_proposed_gt_{right}"]
        and values[f"motion_relink_telemetry_guarded_gt_{left}"]
        >= values[f"motion_relink_telemetry_guarded_gt_{right}"]
        for left, right in zip(_threshold_codes, _threshold_codes[1:]))
    for values in _validation_telemetry.values()
) if _telemetry_complete else False
_ema_execution = {
    specimen: {
        "ema_predictions": int(sum(row.get("motion_relink_ema_predictions", 0)
            for row in validator_sample_rows if row["stem"].startswith(specimen + "_"))),
        "one_frame_fallbacks": int(sum(row.get("motion_relink_one_frame_fallbacks", 0)
            for row in validator_sample_rows if row["stem"].startswith(specimen + "_"))),
    }
    for specimen in ("44b6", "6bba")
}
_behavior_checks = {
    "aggregate_primary_exact": _telemetry_close(_summary["proxy_score"], TELEMETRY_EXPECTED["aggregate"]["primary_metric"]),
    "aggregate_adjusted_edge_exact": _telemetry_close(_summary["adjusted_edge_jaccard"], TELEMETRY_EXPECTED["aggregate"]["adjusted_edge_jaccard"]),
    "aggregate_division_exact": _telemetry_close(_summary["division_jaccard"], TELEMETRY_EXPECTED["aggregate"]["division_jaccard"]),
    "specimens_exact": all(
        _telemetry_close(_specimens[s][key], TELEMETRY_EXPECTED["specimens"][s][key])
        for s in _specimens for key in ("primary_metric", "adjusted_edge_jaccard", "division_jaccard")),
    "videos_exact": set(_video_metrics) == set(TELEMETRY_EXPECTED["videos"]) and all(
        all(_telemetry_close(_video_metrics[stem][key], expected)
            for key, expected in values.items())
        for stem, values in TELEMETRY_EXPECTED["videos"].items()),
    "division_counts_exact": {key: int(_overall[key]) for key in ("div_tp", "div_fp", "div_fn")}
        == TELEMETRY_EXPECTED["division_counts"],
    "ema_execution_exact": _ema_execution == TELEMETRY_EXPECTED["ema_execution"],
}
_contract_checks = {
    **_inference_checks,
    **_behavior_checks,
    "experiment_id_injected": _EXPERIMENT_ID == "diag_044_public_0942_motion_ema_online_telemetry",
    "frozen_samples_and_order": all(_specimens[s]["samples"] == FROZEN_SAMPLES[s] for s in FROZEN_SAMPLES),
    "frozen_strata": all(set(row["stem"] for row in validator_sample_rows
        if row["stem"].startswith(s + "_") and division_flags[row["stem"]]) == set(FROZEN_POSITIVES[s])
        for s in FROZEN_SAMPLES),
    "sample_count": len(validator_sample_rows) == int(_summary["n_samples"]) == 16,
    "candidate_submission_unchanged_after_validation": _sha256_file(SUBMISSION_PATH)
        == TELEMETRY_EXPECTED["submission_sha256"],
    "stage_stats_complete": set(VALIDATION_STAGE_STATS) == set(val_stems),
    "online_telemetry_complete": _telemetry_complete,
    "prospective_threshold_counts_monotonic": _telemetry_monotonic,
}
_diagnostic_passed = all(_contract_checks.values())
_metrics = {
    "schema_version": 1, "experiment_id": _EXPERIMENT_ID,
    "primary_metric": float(_summary["proxy_score"]),
    "baseline_primary_metric": TELEMETRY_EXPECTED["aggregate"]["primary_metric"],
    "runtime_seconds": _run_time.perf_counter() - RUN_STARTED_AT,
    "reproducible": False,
    "validation": {
        "protocol": _PROTOCOL, "sample_count": 16,
        "adjusted_edge_jaccard": float(_summary["adjusted_edge_jaccard"]),
        "division_jaccard": float(_summary["division_jaccard"]),
        "selection_and_scorer_reference": "val_039_public_0941_train16",
        "warning": "Frozen models saw training videos; this is a behavior-preservation telemetry diagnostic.",
    },
    "specimen_metrics": _specimens,
    "metrics": {
        "validation_contract_passed": all(_contract_checks.values()),
        "telemetry_diagnostic_passed": _diagnostic_passed,
        "checks": _contract_checks,
        "failed_checks": [key for key, value in _contract_checks.items() if not value],
        "online_telemetry": _validation_telemetry,
        "motion_relink_ema_execution": _ema_execution,
        "motion_relink_velocity_estimator": "per_track_ema",
        "motion_relink_velocity_weight": MOTION_RELINK_VELOCITY_WEIGHT,
        "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,
        "inference_identity": _inference_receipt,
        "parent_experiment": "repro_041_public_0941_motion_ema",
        "candidate_submission_sha256": _inference_receipt["submission_sha256"],
        "division_counts": {key: int(_overall[key]) for key in ("div_tp", "div_fp", "div_fn")},
    },
}
(WORKING_DIR / "validation_stage_stats.json").write_text(
    json.dumps(VALIDATION_STAGE_STATS, indent=2, sort_keys=True), encoding="utf-8")
(WORKING_DIR / "metrics.json").write_text(json.dumps(_metrics, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(_metrics, indent=2, sort_keys=True))
