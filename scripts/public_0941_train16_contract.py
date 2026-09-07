# Embedded final contract. No pass condition depends on beating the historical baseline.
_EXPERIMENT_ID = "__CONTROLLER_EXPERIMENT_ID__"
_PROTOCOL = "public_0941_frozen_train16_stratified_proxy_v1"
if len(validator_summary_rows) != 1:
    raise RuntimeError("Expected exactly one train16 summary")
_summary = validator_summary_rows[0]
_specimens = {}
for _specimen in ("44b6", "6bba"):
    _rows = [r for r in validator_sample_rows if r["stem"].startswith(_specimen + "_")]
    _aggregate = aggregate_official(_rows)
    _specimens[_specimen] = {
        "primary_metric": float(_aggregate["proxy_score"]),
        "adjusted_edge_jaccard": float(_aggregate["adjusted_edge_jaccard"]),
        "division_jaccard": float(_aggregate["division_jaccard"]),
        "samples": [r["stem"] for r in _rows],
        "division_positive_samples": [r["stem"] for r in _rows if division_flags[r["stem"]]],
        "division_negative_samples": [r["stem"] for r in _rows if not division_flags[r["stem"]]],
        "error_summary": _aggregate,
    }
_checks = {
    **_inference_checks,
    "experiment_id_injected": _EXPERIMENT_ID == "val_039_public_0941_train16",
    "frozen_samples_and_order": all(_specimens[s]["samples"] == FROZEN_SAMPLES[s] for s in FROZEN_SAMPLES),
    "frozen_strata": all(set(_specimens[s]["division_positive_samples"]) == set(FROZEN_POSITIVES[s])
                         for s in FROZEN_SAMPLES),
    "sample_count": len(validator_sample_rows) == int(_summary["n_samples"]) == 16,
    "finite_scores": all(_contract_math.isfinite(float(r[k])) for r in validator_sample_rows
                         for k in ("weight", "adjusted_edge_jaccard", "div_tp", "div_fp", "div_fn")),
    "density_penalty_available": all(r["t_true"] is not None and float(r["t_true"]) > 0
                                     for r in validator_sample_rows),
    "test_submission_unchanged_after_validation": _sha256_file(SUBMISSION_PATH) == EXPECTED_SUBMISSION_SHA,
    "stage_stats_complete": set(VALIDATION_STAGE_STATS) == set(val_stems),
}
_metrics = {
    "schema_version": 1,
    "experiment_id": _EXPERIMENT_ID,
    "primary_metric": float(_summary["proxy_score"]),
    "runtime_seconds": _run_time.perf_counter() - RUN_STARTED_AT,
    "reproducible": False,
    "validation": {
        "protocol": _PROTOCOL, "sample_count": 16,
        "adjusted_edge_jaccard": float(_summary["adjusted_edge_jaccard"]),
        "division_jaccard": float(_summary["division_jaccard"]),
        "selection_and_scorer_reference": "val_008_public_0933_train16_launchable",
        "warning": "Frozen models saw training videos; optimistic train-derived proxy, not held-out model generalization.",
    },
    "specimen_metrics": _specimens,
    "metrics": {
        "validation_contract_passed": all(_checks.values()),
        "checks": _checks, "failed_checks": [k for k, v in _checks.items() if not v],
        "inference_identity": _inference_receipt,
        "parent_public_lb": 0.941, "parent_submission_id": 56044403,
        "baseline_establishment_only": True,
    },
}
(WORKING_DIR / "validation_stage_stats.json").write_text(
    json.dumps(VALIDATION_STAGE_STATS, indent=2, sort_keys=True), encoding="utf-8")
(WORKING_DIR / "metrics.json").write_text(json.dumps(_metrics, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(_metrics, indent=2, sort_keys=True))
