# Embedded after the frozen reproduction checks, before metrics serialization.
_ev_required_stages = {'raw_post_ilp', 'distance_filtered', 'motion_relinked',
    'degree_repaired', 'gap1', 'gap2', 'safe_divisions', 'geometry_and_isolated',
    'short_track_filtered', 'final_scored', 'scorer_matching'}
_ev_worker_manifest = {}
for _ev_stem_name in val_stems:
    _ev_folder = WORKING_DIR / 'tracklet_evidence' / _ev_stem_name
    _ev_paths = sorted(_ev_folder.glob('*.npz'))
    _ev_worker_manifest[_ev_stem_name] = [dict(name=p.name, bytes=p.stat().st_size,
        sha256=_sha256_file(p)) for p in _ev_paths]
_ev_checks = {
    'parent_reproduction_passed': _reproduction_passed,
    'all_parent_contract_checks_passed': all(_contract_checks.values()),
    'validation_csv_bytes_exact': _sha256_file(WORKING_DIR / 'validator_results.csv') ==
        '2e6b0bf3a02f3a74b2115b23342ddd22bd8340d0faa9db8893b4733dadb9da85',
    'graph_stages_complete': set(EV_MANIFEST) == set(val_stems) and
        all(set(v) == _ev_required_stages for v in EV_MANIFEST.values()),
    'worker_exports_complete': all(
        {r['name'] for r in files} == {'pre_ilp_nodes.npz'} |
        {'pair_%03d_%03d.npz' % (t, t + 1) for t in range(99)}
        for files in _ev_worker_manifest.values()),
    'worker_size_bounded': all(sum(r['bytes'] for r in files) <= 128 * 1024**2
        for files in _ev_worker_manifest.values()),
}
_metrics['reproducible'] = all(_ev_checks.values())
_metrics['metrics'].update(evidence_diagnostic_passed=all(_ev_checks.values()),
    evidence_checks=_ev_checks, evidence_graph_manifest=EV_MANIFEST,
    evidence_worker_manifest=_ev_worker_manifest,
    evidence_pool='top8_per_source_and_target_union_all_accepted_pre_ilp',
    evidence_scope='offline_reachable_error_audit_only_no_quality_advancement')
(WORKING_DIR / 'tracklet_evidence_manifest.json').write_text(json.dumps(dict(
    schema_version=1, parent='repro_041_public_0941_motion_ema',
    graph_manifest=EV_MANIFEST, worker_manifest=_ev_worker_manifest,
    checks=_ev_checks), indent=2, allow_nan=False))
