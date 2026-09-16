"""Final independent parity gate, evaluated after all prediction and scoring."""
_jr_checks = dict(_contract_checks)
_jr_checks['solver_pinned'] = _jr_solver_version == '1.18.1'
_jr_checks['test_and_validation_coverage'] = set(JR_RECEIPTS) == set(val_stems) | set(_guard_datasets)
_jr_checks['exact_validation_graphs'] = all(
    JR_RECEIPTS[s]['input_graph_sha256'] == v['input'] and
    JR_RECEIPTS[s]['output_graph_sha256'] == v['output'] for s, v in JR_EXPECTED.items())
_jr_rows = {r['stem']: r for r in validator_sample_rows}
_jr_checks['exact_score_rows'] = all(
    all(_contract_math.isclose(float(_jr_rows[s][k]), float(value), rel_tol=0, abs_tol=1e-12)
        for k, value in v['score'].items()) for s, v in JR_EXPECTED.items())
_jr_checks['aggregate_expected'] = _contract_math.isclose(
    float(_summary['proxy_score']), 0.9535869213120838, rel_tol=0, abs_tol=1e-12)
_jr_checks['aggregate_gain'] = float(_summary['proxy_score']) - 0.9387332376874039 >= 0.005
_jr_checks['division_preserved'] = all(int(_overall[k]) == v
    for k, v in dict(div_tp=4, div_fp=8, div_fn=8).items())
# Exact full graph and per-video score reproduction also fixes all predeclared
# panel/specimen deltas, worst-video loss and division protection to local results.
_metrics['baseline_primary_metric'] = 0.9387332376874039
_metrics['reproducible'] = False
_metrics['metrics'] = dict(joint_repair_passed=all(_jr_checks.values()), checks=_jr_checks,
    failed_checks=[k for k, v in _jr_checks.items() if not v],
    parent_experiment='repro_041_public_0941_motion_ema',
    candidate_submission_sha256=_sha256_file(SUBMISSION_PATH),
    division_counts={k: int(_overall[k]) for k in ('div_tp', 'div_fp', 'div_fn')},
    joint_repair_receipts=JR_RECEIPTS, solver_version=_jr_solver_version)
(WORKING_DIR / 'validation_stage_stats.json').write_text(json.dumps(VALIDATION_STAGE_STATS, allow_nan=False))
(WORKING_DIR / 'metrics.json').write_text(json.dumps(_metrics, indent=2, allow_nan=False))
print(json.dumps(_metrics, indent=2, allow_nan=False))
