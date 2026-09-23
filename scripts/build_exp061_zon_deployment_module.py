from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "exp061_deepcenter_tta.py"
OUTPUT = ROOT / "scripts" / "exp061_zon_deployment.py"
s = SOURCE.read_text(encoding="utf-8")
EXPECTED_SOURCE_SHA256 = "45d756b7585f171e4f590eec04be54277ef525c3b63790f04f025f7d0c548178"
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED_SOURCE_SHA256:
    raise SystemExit("frozen v2 harness SHA256 mismatch")

def rep(old, new, n=1):
    global s
    count = s.count(old)
    if count != n:
        raise SystemExit(f"expected {n} matches for {old[:80]!r}, got {count}")
    s = s.replace(old, new, n)

rep('"""exp_061', '"""exp061 zon-only deployment runner copied from the frozen v2 research harness.')
rep('When BIOHUB_EXP061_ENABLE=1 it additionally produces three test submissions under\nthree DeepCenter-TTA arms, plus attribution telemetry.',
    'The deployment entry point runs only the frozen zon arm and writes its current-input\nreceipt. It intentionally does not run XY parity or xyd4 replays.')
rep('EXP061_VALIDATION_PROTOCOL = "public_0947_deepcenter_tta_probe_v1"',
    'EXP061_VALIDATION_PROTOCOL = "exp061_zon_only_deployment_v3"')
rep('EXP061_EXPERIMENT_ID = "exp_061_deepcenter_tta"',
    'EXP061_EXPERIMENT_ID = "exp_061_zon_lb_submission_repair_v3"')
rep('def run_exp061_deepcenter_tta(g: dict) -> dict:', 'def run_exp061_zon_deployment(g: dict) -> dict:')
rep('"""Run the three-arm DeepCenter-TTA probe', '"""Run only the frozen zon arm')
rep('    arm_views_seen = {}       # arm -> set(view_id) actually computed  [execution validity]', '    arm_views_seen = {"zon": set()}\n    arm_frame_views_seen = {}\n    arm_frame_square = {}')
rep('            views = EXP061_ARM_VIEWS[arm]\n            acc = None',
    '            views = EXP061_ARM_VIEWS[arm]\n            frame_key = (arm, dataset, int(t))\n            arm_frame_views_seen[frame_key] = []\n            arm_frame_square[frame_key] = bool(square)\n            acc = None')
rep('                arm_views_seen.setdefault(arm, set()).add(view_id)   # execution evidence (#3)',
    '                arm_views_seen.setdefault(arm, set()).add(view_id)   # execution evidence (#3)\n                arm_frame_views_seen[frame_key].append(view_id)')
rep('arm_status = {a: "not_reached" for a in EXP061_ARMS}   # started/completed/skipped/failed (#4)',
    'arm_status = {"zon": "not_reached"}   # started/completed/skipped/failed (#4)')
rep('for arm in EXP061_ARMS:', 'for arm in ("zon",):')
start = s.index('    # -- mechanism-active check (admission #2):')
end = s.index('    pin_ok = float(g["MOTION_RELINK_TIGHT_UM"]) == 5.5', start)
s = s[:start] + '''    # Deployment validates the zon intervention itself; cross-arm parity/mechanism
    # comparisons are development-only and deliberately absent from this scoring path.
    control = {}
    parity_ok = None
    mechanism = {}
    zon_summary = arm_summaries.get("zon", {})
    zon_views_expected_by_frame = {}
    frame_view_contract_ok = True
    for frame_key, actual_views in arm_frame_views_seen.items():
        _arm, _dataset, _t = frame_key
        _square = arm_frame_square[frame_key]
        _expected = [view_id for view_id, square_only in EXP061_ARM_VIEWS["zon"]
                     if not square_only or _square]
        zon_views_expected_by_frame[f"{_dataset}:{_t}"] = _expected
        if actual_views != _expected:
            frame_view_contract_ok = False
    zero_candidate_case = len(veto_log) == 0
    zon_view_execution_valid = bool(zon_summary) and (
        frame_view_contract_ok and
        (bool(arm_frame_views_seen) or zero_candidate_case)
    )
    started_experimental = ["zon"] if "zon" in arm_summaries else []
    all_started_execution_valid = (len(started_experimental) == 1
                                   and zon_view_execution_valid)

''' + s[end:]
rep('n_missing = sum(1 for r in veto_log if r.get("score_status") == "missing")',
    'n_missing = sum(1 for r in veto_log if r.get("score_status") == "missing")\n    veto_calls_accounted_for = all(\n        r.get("score_status") == "ok" and isinstance(r.get("ids"), dict) and bool(r.get("ids"))\n        for r in veto_log\n    )')
rep('    _canon = _cfg(EXP061_CONTROL_ARM)\n    all_config_complete = bool(arm_summaries) and all(s.get("config_complete") for s in arm_summaries.values())\n    config_matches_control = bool(_canon) and all(_cfg(a) == _canon for a in arm_summaries)\n    all_arm_configs_equal_frozen_parent = (bool(arm_summaries)\n                                           and live_config_equals_frozen_parent\n                                           and all(_knob_config(_cfg(a)) == expected_parent_config\n                                                   for a in arm_summaries))',
    '    all_config_complete = bool(arm_summaries) and all(s.get("config_complete") for s in arm_summaries.values())\n    all_arm_configs_equal_frozen_parent = (bool(arm_summaries)\n                                           and live_config_equals_frozen_parent\n                                           and all(_knob_config(_cfg(a)) == expected_parent_config\n                                                   for a in arm_summaries))')
rep('all_arm_configs_equal_parent = bool(all_arm_configs_equal_frozen_parent)  # DIRECT (admission v2 #2)',
    'all_arm_configs_equal_parent = bool(all_arm_configs_equal_frozen_parent)  # direct frozen-parent compare')
rep('"control_parity_sha256_matches_parent": parity_ok,',
    '"deployment_runs_only_zon": arms_started == ["zon"] and arm_status.get("zon") == "completed",')
rep('"control_arm_started_first": bool(arms_started) and arms_started[0] == EXP061_CONTROL_ARM,',
    '"zon_started": bool(arms_started) and arms_started[0] == "zon",')
rep('"no_veto_score_errors": n_error == 0,',
    '"all_veto_scores_finite_and_accounted": n_error == 0 and n_nonfinite == 0 and n_missing == 0 and veto_calls_accounted_for,')
rep('"arm_status": arm_status,',
    '"arm_status": arm_status,\n                          "zero_candidate_case": zero_candidate_case,\n                          "zon_view_expected_by_frame": zon_views_expected_by_frame,\n                          "veto_calls_accounted_for": veto_calls_accounted_for,', 2)
rep('"parity": {"control_sha256": control.get("sha256"),\n                   "parent_sha256": EXP061_PARENT_SUBMISSION_SHA256, "ok": parity_ok},',
    '"parity": {"applicable": False, "reason": "deployment-only run omits development replay"},')
rep('"delta_vs_xyonly": {"zon": _delta("xyonly", "zon"), "xyd4": _delta("xyonly", "xyd4")},',
    '"delta_vs_xyonly": None,')
rep('"mechanism_active": mechanism,',
    '"mechanism_active": mechanism,\n        "deployment_only": True,\n        "zero_candidate_case": zero_candidate_case,\n        "zon_view_expected_by_frame": zon_views_expected_by_frame,\n        "veto_calls_accounted_for": veto_calls_accounted_for,', 2)
rep('"exp061_deepcenter_tta_integrity_passed": bool(integrity_passed),', '"exp061_zon_deployment_integrity_passed": bool(integrity_passed),')
start = s.index('            "primary_metric_meaning": (')
end = s.index('            ),', start) + len('            ),')
s = s[:start] + '            "primary_metric_meaning": "zon-only deployment integrity; no quality inference",\n' + s[end:]
rep('print(f"[exp061] integrity {\'PASS\' if integrity_passed else \'FAIL\'}; parity_ok={parity_ok}; ',
    'print(f"[exp061-zon] integrity {\'PASS\' if integrity_passed else \'FAIL\'}; deployment_only=True; ')
rep('"n_veto_records": len(arm_veto_rows), "veto_rows": arm_veto_rows}', '"n_veto_records": len(arm_veto_rows), "per_dataset": sorted(per_dataset), "veto_rows": arm_veto_rows}')
rep('"deployment_runs_only_zon": arms_started == ["zon"] and arm_status.get("zon") == "completed",', '"deployment_runs_only_zon": arms_started == ["zon"] and arm_status.get("zon") == "completed",\n        "all_discovered_test_datasets_completed": (arm_status.get("zon") == "completed" and set(zon_summary.get("per_dataset", {})) == set(g["test_stems"])),')
rep('    feasibility_worksheet = {', '    try:\n        import resource\n        process_peak_rss_bytes = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024\n    except Exception:\n        process_peak_rss_bytes = None\n    feasibility_worksheet = {\n        "process_peak_rss_bytes": process_peak_rss_bytes,')
compile(s, str(OUTPUT), "exec")
OUTPUT.write_text(s, encoding="utf-8", newline="\n")
receipt = {"source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
           "output_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
           "transform": "deterministic textual patch set in scripts/build_exp061_zon_deployment_module.py",
           "run_entrypoint": "run_exp061_zon_deployment",
           "expected_arms": ["zon"]}
(OUTPUT.with_suffix(".build.json")).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt, indent=2))

