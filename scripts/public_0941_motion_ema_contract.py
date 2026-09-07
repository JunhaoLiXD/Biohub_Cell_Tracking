# Embedded final contract for the single-variable EMA screening experiment.
_EXPERIMENT_ID = "__CONTROLLER_EXPERIMENT_ID__"
_PROTOCOL = "public_0941_frozen_train16_stratified_proxy_v1"
_BASELINE_PRIMARY = 0.9359778132422281
_MINIMUM_IMPROVEMENT = 0.001
_ADJUSTED_EDGE_TOLERANCE = 0.002
_BASELINE_SPECIMEN = {
    "44b6": {"primary_metric": 0.9217996822478786, "adjusted_edge_jaccard": 0.9017996822478785},
    "6bba": {"primary_metric": 0.9403315937448887, "adjusted_edge_jaccard": 0.9221497755630705},
}
if len(validator_summary_rows) != 1:
    raise RuntimeError("Expected exactly one train16 summary")
_summary = validator_summary_rows[0]
_specimens = {}
for _specimen in ("44b6", "6bba"):
    _rows = [row for row in validator_sample_rows if row["stem"].startswith(_specimen + "_")]
    _aggregate = aggregate_official(_rows)
    _baseline = _BASELINE_SPECIMEN[_specimen]
    _specimens[_specimen] = {
        "primary_metric": float(_aggregate["proxy_score"]),
        "baseline_primary_metric": float(_baseline["primary_metric"]),
        "delta": float(_aggregate["proxy_score"] - _baseline["primary_metric"]),
        "adjusted_edge_jaccard": float(_aggregate["adjusted_edge_jaccard"]),
        "baseline_adjusted_edge_jaccard": float(_baseline["adjusted_edge_jaccard"]),
        "adjusted_edge_delta": float(_aggregate["adjusted_edge_jaccard"] - _baseline["adjusted_edge_jaccard"]),
        "division_jaccard": float(_aggregate["division_jaccard"]),
        "samples": [row["stem"] for row in _rows],
        "division_positive_samples": [row["stem"] for row in _rows if division_flags[row["stem"]]],
        "division_negative_samples": [row["stem"] for row in _rows if not division_flags[row["stem"]]],
        "error_summary": _aggregate,
    }
_overall = aggregate_official(validator_sample_rows)
_ema_execution = {
    specimen: {
        "ema_predictions": int(sum(
            row.get("motion_relink_ema_predictions", 0)
            for row in validator_sample_rows if row["stem"].startswith(specimen + "_"))),
        "one_frame_fallbacks": int(sum(
            row.get("motion_relink_one_frame_fallbacks", 0)
            for row in validator_sample_rows if row["stem"].startswith(specimen + "_"))),
        "skipped_large_frames": int(sum(
            row.get("motion_relink_skipped_large_frame", 0)
            for row in validator_sample_rows if row["stem"].startswith(specimen + "_"))),
    }
    for specimen in ("44b6", "6bba")
}
_contract_checks = {
    **_inference_checks,
    "experiment_id_injected": _EXPERIMENT_ID == "exp_040_public_0941_motion_ema",
    "frozen_samples_and_order": all(_specimens[s]["samples"] == FROZEN_SAMPLES[s] for s in FROZEN_SAMPLES),
    "frozen_strata": all(set(_specimens[s]["division_positive_samples"]) == set(FROZEN_POSITIVES[s])
                         for s in FROZEN_SAMPLES),
    "sample_count": len(validator_sample_rows) == int(_summary["n_samples"]) == 16,
    "finite_scores": all(_contract_math.isfinite(float(row[key])) for row in validator_sample_rows
                         for key in ("weight", "adjusted_edge_jaccard", "div_tp", "div_fp", "div_fn")),
    "density_penalty_available": all(row["t_true"] is not None and float(row["t_true"]) > 0
                                     for row in validator_sample_rows),
    "candidate_submission_unchanged_after_validation": (
        _sha256_file(SUBMISSION_PATH) == _inference_receipt["submission_sha256"]),
    "stage_stats_complete": set(VALIDATION_STAGE_STATS) == set(val_stems),
    "motion_ema_exercised_both_specimens": all(
        values["ema_predictions"] > 0 for values in _ema_execution.values()),
}
_research_gates = {
    "aggregate_improvement_at_least_0_001": (
        float(_summary["proxy_score"]) - _BASELINE_PRIMARY >= _MINIMUM_IMPROVEMENT),
    "adjusted_edge_no_material_specimen_regression": all(
        metrics["adjusted_edge_delta"] >= -_ADJUSTED_EDGE_TOLERANCE
        for metrics in _specimens.values()),
    "division_tp_at_least_4": int(_overall["div_tp"]) >= 4,
    "division_fp_at_most_9": int(_overall["div_fp"]) <= 9,
    "division_fn_at_most_8": int(_overall["div_fn"]) <= 8,
}
_metrics = {
    "schema_version": 1,
    "experiment_id": _EXPERIMENT_ID,
    "primary_metric": float(_summary["proxy_score"]),
    "baseline_primary_metric": _BASELINE_PRIMARY,
    "runtime_seconds": _run_time.perf_counter() - RUN_STARTED_AT,
    "reproducible": False,
    "validation": {
        "protocol": _PROTOCOL, "sample_count": 16,
        "adjusted_edge_jaccard": float(_summary["adjusted_edge_jaccard"]),
        "division_jaccard": float(_summary["division_jaccard"]),
        "selection_and_scorer_reference": "val_039_public_0941_train16",
        "warning": "Frozen models saw training videos; this is an optimistic paired screening proxy.",
    },
    "specimen_metrics": _specimens,
    "metrics": {
        "validation_contract_passed": all(_contract_checks.values()),
        "ema_candidate_gate_passed": all(_contract_checks.values()) and all(_research_gates.values()),
        "checks": _contract_checks,
        "research_gates": _research_gates,
        "failed_checks": [key for key, value in _contract_checks.items() if not value],
        "failed_research_gates": [key for key, value in _research_gates.items() if not value],
        "motion_relink_ema_execution": _ema_execution,
        "motion_relink_velocity_estimator": "per_track_ema",
        "motion_relink_velocity_weight": MOTION_RELINK_VELOCITY_WEIGHT,
        "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,
        "inference_identity": _inference_receipt,
        "parent_experiment": "val_039_public_0941_train16",
        "parent_public_lb": 0.941,
        "candidate_submission_sha256": _inference_receipt["submission_sha256"],
        "division_counts": {key: int(_overall[key]) for key in ("div_tp", "div_fp", "div_fn")},
    },
}
(WORKING_DIR / "validation_stage_stats.json").write_text(
    json.dumps(VALIDATION_STAGE_STATS, indent=2, sort_keys=True), encoding="utf-8")
(WORKING_DIR / "metrics.json").write_text(json.dumps(_metrics, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(_metrics, indent=2, sort_keys=True))
