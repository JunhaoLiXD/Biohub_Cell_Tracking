"""Validate exp061 zon-only v5: rerun-aware deadline + view cache off the collected output dir.

Everything the v4 validator proved still has to hold (immutable parent inference cells, a single
zon arm, the watchdog armed through publication, fail-closed publication). On top of that this
EXECUTES the two v5 changes rather than pattern-matching them:

  * the cell-2 arming block and the module's deadline helper are run under KAGGLE_IS_COMPETITION_RERUN
    on/off/garbage plus an explicit override, and must agree with each other every time;
  * the scratch-root selector is run for real, and a mocked end-to-end run must leave no view cache
    under WORKING_DIR.
"""
from pathlib import Path
import ast
import csv
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_exp061_zon_submission_repair_v5 import (
    CELL2_ALARM_NEW,
    OUT_MODULE as MODULE,
    OUT_NB as OUT,
    PARENT_NB as BASE,
    RERUN_ALARM_SECONDS,
    VISIBLE_ALARM_SECONDS,
    assert_only_exp061_lines_changed,
)

FINAL = "".join(json.loads(OUT.read_text(encoding="utf-8"))["cells"][4]["source"])
CSV_COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]


def load_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_source_contract(path):
    base = json.loads(BASE.read_text(encoding="utf-8"))
    nb = json.loads(Path(path).read_text(encoding="utf-8"))
    assert len(base["cells"]) == len(nb["cells"]) == 5
    assert nb["cells"][:2] == base["cells"][:2], "parent markdown/setup changed"

    cell2_before = "".join(base["cells"][2]["source"])
    cell2_after = "".join(nb["cells"][2]["source"])
    assert cell2_before != cell2_after, "v5 cell-2 watchdog edit is missing"
    assert_only_exp061_lines_changed(cell2_before, cell2_after)
    assert "alarm(7200)" not in cell2_after, "hardcoded 7200s alarm survived"
    assert "_e61sig.alarm(_EXP061_ALARM_SECONDS)" in cell2_after
    assert "KAGGLE_IS_COMPETITION_RERUN" in cell2_after

    module = "".join(nb["cells"][3]["source"])
    assert module == MODULE.read_text(encoding="utf-8")
    assert "".join(nb["cells"][4]["source"]) == FINAL
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"v5_cell_{i}", "exec")

    tree = ast.parse(module)
    runner = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_exp061_zon_deployment")
    runner_calls = [n for n in ast.walk(runner) if isinstance(n, ast.Call)]
    assert not any(isinstance(n.func, ast.Name) and n.func.id == "_disarm_watchdog" for n in runner_calls)
    arm_loops = [n for n in ast.walk(runner) if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == "arm"]
    assert len(arm_loops) == 1
    assert isinstance(arm_loops[0].iter, ast.Tuple) and [x.value for x in arm_loops[0].iter.elts] == ["zon"]
    assert 'Path(g["WORKING_DIR"]) / "exp061_viewcache"' not in module, "view cache still under WORKING_DIR"
    assert '_exp061_scratch_root(g["WORKING_DIR"]) / "exp061_viewcache"' in module

    # The deadline guard must fail fast, but only after the parent artifact is gone, so a raise can
    # never leave the parent's own 0.947 submission.csv behind to be scored.
    assert FINAL.index("_zon_target.unlink()") < FINAL.index("module deadline disagrees")
    assert FINAL.index("module deadline disagrees") < FINAL.index("run_exp061_zon_deployment(globals())")
    assert FINAL.index("whole-notebook deadline reached") < FINAL.index("_zon_os.replace(_zon_tmp, _zon_target)")
    assert FINAL.index("_zon_os.replace(_zon_tmp, _zon_target)") < FINAL.index("_zon_signal.alarm(0)")

    receipt = json.loads((OUT.parent / "build-receipt.json").read_text(encoding="utf-8"))
    assert receipt["parent_notebook_sha256"] == hashlib.sha256(BASE.read_bytes()).hexdigest()
    assert receipt["module_sha256"] == hashlib.sha256(MODULE.read_bytes()).hexdigest()
    assert receipt["notebook_sha256"] == hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert receipt["visible_alarm_seconds"] == VISIBLE_ALARM_SECONDS
    assert receipt["rerun_alarm_seconds"] == RERUN_ALARM_SECONDS
    return nb


def load_deployment_module():
    return load_path("exp061_zon_deployment_v5", MODULE)


def _eval_cell2_alarm():
    """Execute the injected cell-2 arming block in isolation and return the armed seconds."""
    scope = {"_exp061_whole_run_guard": lambda *a, **k: None}
    exec(CELL2_ALARM_NEW, scope)
    return int(scope["_EXP061_ALARM_SECONDS"]), bool(scope["_EXP061_IS_COMPETITION_RERUN"])


def check_deadline_policy():
    saved = {k: os.environ.get(k) for k in ("KAGGLE_IS_COMPETITION_RERUN", "BIOHUB_EXP061_HARD_STOP_SECONDS")}

    def apply(rerun, override):
        for key, value in (("KAGGLE_IS_COMPETITION_RERUN", rerun), ("BIOHUB_EXP061_HARD_STOP_SECONDS", override)):
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    cases = [
        (None, None, VISIBLE_ALARM_SECONDS, False),
        ("", None, VISIBLE_ALARM_SECONDS, False),
        ("0", None, VISIBLE_ALARM_SECONDS, False),
        ("false", None, VISIBLE_ALARM_SECONDS, False),
        ("True", None, RERUN_ALARM_SECONDS, True),
        ("1", None, RERUN_ALARM_SECONDS, True),
        ("1", "not-a-number", RERUN_ALARM_SECONDS, True),
        ("1", "0", RERUN_ALARM_SECONDS, True),
        ("1", "-5", RERUN_ALARM_SECONDS, True),
        ("1", "600", 600, True),
        (None, "900", 900, False),
    ]
    try:
        for rerun, override, expected, expect_flag in cases:
            apply(rerun, override)
            armed, flag = _eval_cell2_alarm()
            module = load_deployment_module()
            module_stop = int(module.EXP061_HARD_STOP_SECONDS)
            assert flag is expect_flag, (rerun, flag, expect_flag)
            assert armed == expected, (rerun, override, armed, expected)
            assert module_stop == armed, f"module {module_stop} disagrees with armed alarm {armed} for {rerun!r}/{override!r}"
    finally:
        apply(saved["KAGGLE_IS_COMPETITION_RERUN"], saved["BIOHUB_EXP061_HARD_STOP_SECONDS"])
    print(f"PASS: deadline is {VISIBLE_ALARM_SECONDS}s on a visible run, {RERUN_ALARM_SECONDS}s under "
          f"KAGGLE_IS_COMPETITION_RERUN, override-respected, and cell 2 always agrees with the module")


def check_scratch_root():
    module = load_deployment_module()
    saved = os.environ.get("BIOHUB_EXP061_SCRATCH_DIR")
    try:
        with tempfile.TemporaryDirectory() as td:
            working = Path(td) / "working"
            working.mkdir()
            explicit = Path(td) / "scratch"
            os.environ["BIOHUB_EXP061_SCRATCH_DIR"] = str(explicit)
            root = module._exp061_scratch_root(str(working))
            assert root == explicit and root.is_dir(), root
            assert module._exp061_outside_working_dir(root, str(working)) is True

            os.environ.pop("BIOHUB_EXP061_SCRATCH_DIR", None)
            fallback = module._exp061_scratch_root(str(working))
            assert module._exp061_outside_working_dir(fallback, str(working)) is True, fallback

            inside = working / "exp061_viewcache"
            inside.mkdir()
            assert module._exp061_outside_working_dir(inside, str(working)) is False

            # An override that cannot be a directory (it is a regular file) must not abort the run.
            blocker = Path(td) / "blocker"
            blocker.write_bytes(b"not-a-directory")
            os.environ["BIOHUB_EXP061_SCRATCH_DIR"] = str(blocker / "cache")
            recovered = module._exp061_scratch_root(str(working))
            assert recovered != blocker / "cache", recovered
            assert module._exp061_outside_working_dir(recovered, str(working)) is True, recovered
    finally:
        if saved is None:
            os.environ.pop("BIOHUB_EXP061_SCRATCH_DIR", None)
        else:
            os.environ["BIOHUB_EXP061_SCRATCH_DIR"] = saved
    print("PASS: scratch root honours the override, falls back outside WORKING_DIR, and survives a bad override")


def load_fixture():
    return load_path("test_exp061_behavioral_v5_fixture", ROOT / "scripts/test_exp061_behavioral.py")


def run_mock(work, *, fourfold=False, no_veto=False, missing_score=False, omit_dataset=False):
    import numpy as np
    fixture = load_fixture()
    m, g = fixture._build_mock_g(np, str(work), model_bias=0.7)
    deploy = load_deployment_module()
    g["EXPERIMENT_ID"] = "exp_061_zon_lb_submission_repair_v5"
    if fourfold:
        stems = list(g["test_stems"])
        pred_root = Path(g["REPO_DIR"]) / "predictions"
        for index in range(6):
            stem = f"fixture_extra_{index:02d}"
            parent = pred_root / stem / g["METHOD"] / "split_0"
            parent.mkdir(parents=True, exist_ok=True)
            (parent / f"{stem}.geff").write_text("fixture")
            stems.append(stem)
        g["test_stems"] = stems
    if omit_dataset:
        (Path(g["REPO_DIR"]) / "predictions" / g["test_stems"][-1] / g["METHOD"] / "split_0" /
         f"{g['test_stems'][-1]}.geff").unlink()
    if no_veto:
        def filter_without_candidates(nodes, edges, dataset=None, deepcenter_bundle=None):
            return (
                {10: {"node_id": 10, "t": 0, "z": 0, "y": 0, "x": 0},
                 11: {"node_id": 11, "t": 1, "z": 1, "y": 1, "x": 1}},
                [{"source_id": 10, "target_id": 11}],
                {},
            )
        g["filter_output_graph"] = filter_without_candidates
    if missing_score:
        g["deepcenter_score_point"] = lambda *a, **k: None
    os.environ["BIOHUB_DEEPCENTER_TTA"] = "1"
    os.environ["BIOHUB_VALIDATOR_ENABLE"] = "0"
    # Keep each fixture's cache isolated now that it no longer lives under WORKING_DIR.
    os.environ["BIOHUB_EXP061_SCRATCH_DIR"] = str(Path(work).parent / f"scratch_{Path(work).name}")
    start = time.perf_counter()
    telemetry = deploy.run_exp061_zon_deployment(g)
    elapsed = time.perf_counter() - start
    metrics = json.loads((Path(g["WORKING_DIR"]) / "metrics.json").read_text())
    return deploy, g, telemetry, metrics, elapsed


def _csv_payload(header=None, edge_target_t=1):
    columns = header or CSV_COLUMNS
    rows = [
        ["0", "d0", "node", "1", "0", "0", "0", "0", "-1", "-1"],
        ["1", "d0", "node", "2", str(edge_target_t), "0", "0", "0", "-1", "-1"],
        ["2", "d0", "edge", "-1", "-1", "-1", "-1", "-1", "1", "2"],
    ]
    import io
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(columns)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def publication_case(mode):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "exp061").mkdir()
        target = root / "submission.csv"
        # Mimics the parent notebook's already-created 0.947 artifact before the final adapter runs.
        target.write_bytes(b"parent-output-must-never-survive-a-v5-failure")
        good = _csv_payload()
        bad = _csv_payload(header=["wrong"])
        payload = bad if mode == "bad_schema" else (_csv_payload(edge_target_t=2) if mode == "bad_graph" else good)
        zon_csv = root / "exp061" / "submission_zon.csv"
        zon_csv.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        receipt = {"status": "completed", "sha256": digest, "rows": 3, "per_dataset": ["d0"]}
        if mode == "receipt_dataset_missing":
            receipt["per_dataset"] = []
        (root / "exp061" / "receipt_zon.json").write_text(json.dumps(receipt))
        metrics = {
            "exp061_zon_deployment_integrity_passed": mode != "integrity_failure",
            "checks": {"all_discovered_test_datasets_completed": mode != "dataset_incomplete"},
            "arm_status": {"zon": "completed"},
            "run_exception": None,
            "veto_calls_accounted_for": True,
            "arm_submission_sha256": {"zon": "wrong" if mode == "digest_mismatch" else digest},
        }
        (root / "metrics.json").write_text(json.dumps(metrics))

        def runner(_g):
            if mode == "runner_exception":
                raise RuntimeError("injected zon failure")
            return {"arm_status": {"zon": "completed"}}

        hard_stop = RERUN_ALARM_SECONDS if mode == "rerun_deadline" else VISIBLE_ALARM_SECONDS
        armed = 999 if mode == "deadline_mismatch" else hard_stop
        started = time.time() - (hard_stop + 1 if mode == "deadline_expired" else 0)
        g = {"SUBMISSION_PATH": target, "WORKING_DIR": str(root), "CSV_COLUMNS": CSV_COLUMNS,
             "test_stems": ["d0"], "run_exp061_zon_deployment": runner,
             "_EXP061_RUN_START": started,
             "_EXP061_ALARM_SECONDS": armed,
             "_EXP061_IS_COMPETITION_RERUN": mode == "rerun_deadline",
             "EXP061_HARD_STOP_SECONDS": float(hard_stop)}
        try:
            exec(FINAL, g)
        except Exception:
            assert mode not in ("ok", "rerun_deadline"), mode
            assert not target.exists(), f"fallback submission survived {mode}"
        else:
            assert mode in ("ok", "rerun_deadline"), mode
            assert target.read_bytes() == payload


def validate(path):
    assert_source_contract(path)
    print("PASS: parent cells intact, only exp061-marked lines changed, zon-only AST, cache off WORKING_DIR")

    check_deadline_policy()
    check_scratch_root()

    modes = ("ok", "rerun_deadline", "runner_exception", "integrity_failure", "dataset_incomplete",
             "receipt_dataset_missing", "digest_mismatch", "bad_schema", "bad_graph",
             "deadline_expired", "deadline_mismatch")
    for mode in modes:
        publication_case(mode)
    print("PASS: publication positives/negatives incl. 8.5h rerun deadline, expiry and watchdog mismatch")

    with tempfile.TemporaryDirectory() as td:
        deploy, g, telemetry, metrics, elapsed = run_mock(Path(td) / "normal")
        assert telemetry["arms_started"] == ["zon"]
        assert telemetry["arm_status"] == {"zon": "completed"}
        assert metrics["exp061_zon_deployment_integrity_passed"] is True, metrics.get("checks")
        assert metrics["checks"]["all_discovered_test_datasets_completed"] is True
        assert telemetry["veto_counts"]["total"] == 4
        assert telemetry["veto_calls_accounted_for"] is True
        for _key, _expected in telemetry["zon_view_expected_by_frame"].items():
            assert _expected == ["V0", "Vx", "Vy", "Vxy", "R1", "R3", "Td", "Ta",
                                 "ZV0", "ZVx", "ZVy", "ZVxy", "ZR1", "ZR3", "ZTd", "ZTa"]
        assert "xyonly" not in telemetry["arm_status"] and "xyd4" not in telemetry["arm_status"]
        worksheet = telemetry["feasibility_worksheet"]
        assert worksheet["view_cache_outside_working_dir"] is True, worksheet["view_cache_root"]
        assert worksheet["is_competition_rerun"] is False
        assert int(worksheet["hard_stop_seconds"]) == VISIBLE_ALARM_SECONDS
        stale = list(Path(g["WORKING_DIR"]).rglob("exp061_viewcache"))
        assert not stale, f"view cache leaked into the collected output dir: {stale}"
        assert worksheet["view_cache_capacity_io"]["disk_view_files"] > 0, "cache is not actually being written"
    print("PASS: mocked end-to-end zon-only, 16-view list exact, cache written OUTSIDE WORKING_DIR")

    with tempfile.TemporaryDirectory() as td:
        _, _, tel, metrics, elapsed4x = run_mock(Path(td) / "fourfold", fourfold=True)
        assert metrics["exp061_zon_deployment_integrity_passed"] is True
        assert metrics["checks"]["all_discovered_test_datasets_completed"] is True
        assert len(json.loads((Path(_["WORKING_DIR"]) / "exp061" / "receipt_zon.json").read_text())["per_dataset"]) == 8
        assert not list(Path(_["WORKING_DIR"]).rglob("exp061_viewcache"))
        print(f"PASS: deterministic fourfold dataset-count fixture, elapsed={elapsed4x:.3f}s "
              f"disk_cache_bytes={tel['feasibility_worksheet']['view_cache_capacity_io']['disk_view_bytes']} "
              f"cache_root_outside_output={tel['feasibility_worksheet']['view_cache_outside_working_dir']}")

    with tempfile.TemporaryDirectory() as td:
        _, _, tel0, metrics0, _ = run_mock(Path(td) / "zero", no_veto=True)
        assert metrics0["exp061_zon_deployment_integrity_passed"] is True
        assert tel0["zero_candidate_case"] is True and tel0["veto_counts"]["total"] == 0
    print("PASS: zero-candidate no-veto case with every discovered dataset completed")

    with tempfile.TemporaryDirectory() as td:
        _, _, _, metrics_bad, _ = run_mock(Path(td) / "missing_score", missing_score=True)
        assert metrics_bad["exp061_zon_deployment_integrity_passed"] is False
        assert not metrics_bad["checks"]["all_veto_scores_finite_and_accounted"]
    with tempfile.TemporaryDirectory() as td:
        _, _, _, metrics_incomplete, _ = run_mock(Path(td) / "missing_dataset", omit_dataset=True)
        assert metrics_incomplete["exp061_zon_deployment_integrity_passed"] is False
        assert not metrics_incomplete["checks"]["all_discovered_test_datasets_completed"]
    print("PASS: missing score and missing discovered dataset fail closed")


if __name__ == "__main__":
    validate(sys.argv[1] if len(sys.argv) > 1 else str(OUT))
