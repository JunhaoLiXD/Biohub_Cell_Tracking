# Appended within the final metrics cell, before its only metrics.json write.
def _repro_equal(actual, expected):
    if isinstance(expected, dict):
        return (isinstance(actual, dict) and set(actual) == set(expected)
                and all(_repro_equal(actual[key], value) for key, value in expected.items()))
    if isinstance(expected, list):
        return (isinstance(actual, list) and len(actual) == len(expected)
                and all(_repro_equal(a, b) for a, b in zip(actual, expected)))
    if isinstance(expected, float):
        return (isinstance(actual, (int, float)) and not isinstance(actual, bool)
                and _contract_math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12))
    return type(actual) is type(expected) and actual == expected

_reproduction_checks = {
    "aggregate_exact": _repro_equal({
        "primary_metric": _metrics["primary_metric"],
        "adjusted_edge_jaccard": _metrics["validation"]["adjusted_edge_jaccard"],
        "division_jaccard": _metrics["validation"]["division_jaccard"],
    }, REPRO_EXPECTED["aggregate"]),
    "specimens_exact": _repro_equal(_specimens, REPRO_EXPECTED["specimens"]),
    "ema_telemetry_exact": _repro_equal(_ema_execution, REPRO_EXPECTED["ema_execution"]),
    "division_counts_exact": _repro_equal(_metrics["metrics"]["division_counts"], REPRO_EXPECTED["division_counts"]),
    "submission_bytes_exact": _sha256_file(SUBMISSION_PATH) == REPRO_EXPECTED["submission_sha256"],
    "parent_screen_gates_passed": _metrics["metrics"]["ema_candidate_gate_passed"] is True,
}
_reproduction_passed = all(_reproduction_checks.values())
_metrics["reproducible"] = _reproduction_passed
_metrics["metrics"].update({
    "reproduction_passed": _reproduction_passed,
    "reproduction_checks": _reproduction_checks,
    "failed_reproduction_checks": [key for key, passed in _reproduction_checks.items() if not passed],
    "reproduction_reference": "exp_040_public_0941_motion_ema",
    "one_time_post_run_claude_review_required": True,
    "post_run_claude_review_status": "PENDING",
})
