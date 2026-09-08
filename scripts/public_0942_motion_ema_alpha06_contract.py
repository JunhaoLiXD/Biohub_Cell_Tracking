# Embedded final contract for the single-variable EMA-alpha sensitivity experiment.
_EXPERIMENT_ID = "__CONTROLLER_EXPERIMENT_ID__"
_PROTOCOL = "public_0941_frozen_train16_stratified_proxy_v1"
_ALPHA04_PRIMARY = 0.9387332376874039
_SPECIMEN_ADJUSTED_EDGE_TOLERANCE = 0.001
_WORST_VIDEO_DELTA_FLOOR = -0.002
_ALPHA04_SPECIMEN = {
    "44b6": {"primary_metric": 0.9228460029238004, "adjusted_edge_jaccard": 0.9028460029238004},
    "6bba": {"primary_metric": 0.9442148231081169, "adjusted_edge_jaccard": 0.9242148231081169},
}
_VAL039_VIDEO_ADJUSTED_EDGE = {
    "44b6_1d530831": 0.7969198174184619,
    "44b6_2a2eff9f": 0.89235322899701,
    "44b6_551a5dba": 0.8293364900661753,
    "44b6_7a302da0": 0.9631748927747178,
    "44b6_7e557709": 0.9697278692084568,
    "44b6_aaf8b0ea": 1.0069255657234752,
    "44b6_c15fded2": 0.828546217819058,
    "44b6_c50204e0": 0.8120402474453199,
    "6bba_0c7fa718": 0.8003078098372215,
    "6bba_283bf9f1": 0.9341409661473707,
    "6bba_337b1b3a": 0.9401114627658469,
    "6bba_372c8cb8": 1.0032753214280064,
    "6bba_55c70843": 0.7122589938896665,
    "6bba_80d12824": 0.894819771976011,
    "6bba_ef7b4f7e": 0.9788588208381466,
    "6bba_fe670320": 0.9750245558283982,
}
if len(validator_summary_rows) != 1:
    raise RuntimeError("Expected exactly one train16 summary")
_summary = validator_summary_rows[0]
_specimens = {}
for _specimen in ("44b6", "6bba"):
    _rows = [row for row in validator_sample_rows if row["stem"].startswith(_specimen + "_")]
    _aggregate = aggregate_official(_rows)
    _baseline = _ALPHA04_SPECIMEN[_specimen]
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
_video_deltas_vs_val039 = {
    row["stem"]: float(row["adjusted_edge_jaccard"] - _VAL039_VIDEO_ADJUSTED_EDGE[row["stem"]])
    for row in validator_sample_rows
}
_worst_video = min(_video_deltas_vs_val039, key=_video_deltas_vs_val039.get)
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
    "experiment_id_injected": _EXPERIMENT_ID == "exp_042_public_0942_motion_ema_alpha06",
    "frozen_samples_and_order": all(_specimens[s]["samples"] == FROZEN_SAMPLES[s] for s in FROZEN_SAMPLES),
    "frozen_strata": all(set(_specimens[s]["division_positive_samples"]) == set(FROZEN_POSITIVES[s])
                         for s in FROZEN_SAMPLES),
    "video_baseline_complete": set(_video_deltas_vs_val039) == set(_VAL039_VIDEO_ADJUSTED_EDGE),
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
    "aggregate_at_least_alpha04": float(_summary["proxy_score"]) >= _ALPHA04_PRIMARY,
    "adjusted_edge_no_material_specimen_regression_vs_alpha04": all(
        metrics["adjusted_edge_delta"] >= -_SPECIMEN_ADJUSTED_EDGE_TOLERANCE
        for metrics in _specimens.values()),
    "worst_video_delta_vs_val039_at_least_minus_0_002": (
        _video_deltas_vs_val039[_worst_video] >= _WORST_VIDEO_DELTA_FLOOR),
    "division_tp_at_least_4": int(_overall["div_tp"]) >= 4,
    "division_fp_at_most_8": int(_overall["div_fp"]) <= 8,
    "division_fn_at_most_8": int(_overall["div_fn"]) <= 8,
}
_metrics = {
    "schema_version": 1,
    "experiment_id": _EXPERIMENT_ID,
    "primary_metric": float(_summary["proxy_score"]),
    "baseline_primary_metric": _ALPHA04_PRIMARY,
    "runtime_seconds": _run_time.perf_counter() - RUN_STARTED_AT,
    "reproducible": False,
    "validation": {
        "protocol": _PROTOCOL, "sample_count": 16,
        "adjusted_edge_jaccard": float(_summary["adjusted_edge_jaccard"]),
        "division_jaccard": float(_summary["division_jaccard"]),
        "selection_and_scorer_reference": "val_039_public_0941_train16",
        "warning": "Frozen models saw training videos; this is an optimistic paired sensitivity test.",
    },
    "specimen_metrics": _specimens,
    "metrics": {
        "validation_contract_passed": all(_contract_checks.values()),
        "alpha06_candidate_gate_passed": all(_contract_checks.values()) and all(_research_gates.values()),
        "checks": _contract_checks,
        "research_gates": _research_gates,
        "failed_checks": [key for key, value in _contract_checks.items() if not value],
        "failed_research_gates": [key for key, value in _research_gates.items() if not value],
        "video_response_vs_val039": {
            "deltas": _video_deltas_vs_val039,
            "positive": sum(value > 0 for value in _video_deltas_vs_val039.values()),
            "zero": sum(value == 0 for value in _video_deltas_vs_val039.values()),
            "negative": sum(value < 0 for value in _video_deltas_vs_val039.values()),
            "worst_video": _worst_video,
            "worst_delta": _video_deltas_vs_val039[_worst_video],
        },
        "motion_relink_ema_execution": _ema_execution,
        "motion_relink_velocity_estimator": "per_track_ema",
        "motion_relink_velocity_weight": MOTION_RELINK_VELOCITY_WEIGHT,
        "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,
        "inference_identity": _inference_receipt,
        "parent_experiment": "repro_041_public_0941_motion_ema",
        "parent_public_lb_displayed": 0.942,
        "parent_public_lb_source": "user_reported_kaggle_ui",
        "candidate_submission_sha256": _inference_receipt["submission_sha256"],
        "division_counts": {key: int(_overall[key]) for key in ("div_tp", "div_fp", "div_fn")},
    },
}
(WORKING_DIR / "validation_stage_stats.json").write_text(
    json.dumps(VALIDATION_STAGE_STATS, indent=2, sort_keys=True), encoding="utf-8")
(WORKING_DIR / "metrics.json").write_text(json.dumps(_metrics, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(_metrics, indent=2, sort_keys=True))
