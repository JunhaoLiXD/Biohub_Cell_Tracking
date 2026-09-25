"""Validate exp061 zon-only v4 with the watchdog armed through publication."""
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
from build_exp061_zon_submission_repair_v4 import PARENT_NB as BASE, OUT_MODULE as MODULE, OUT_NB as OUT
FINAL = "".join(json.loads(OUT.read_text(encoding="utf-8"))["cells"][4]["source"])


def load_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_source_contract(path):
    base = json.loads(BASE.read_text(encoding="utf-8"))
    nb = json.loads(Path(path).read_text(encoding="utf-8"))
    assert len(base["cells"]) == len(nb["cells"]) == 5
    assert nb["cells"][:3] == base["cells"][:3], "parent inference and setup changed"
    module = "".join(nb["cells"][3]["source"])
    assert module == MODULE.read_text(encoding="utf-8")
    assert "".join(nb["cells"][4]["source"]) == FINAL
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"v4_cell_{i}", "exec")
    tree = ast.parse(module)
    runner = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_exp061_zon_deployment")
    runner_calls = [n for n in ast.walk(runner) if isinstance(n, ast.Call)]
    assert not any(isinstance(n.func, ast.Name) and n.func.id == "_disarm_watchdog" for n in runner_calls)
    arm_loops = [n for n in ast.walk(runner) if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == "arm"]
    assert len(arm_loops) == 1
    assert isinstance(arm_loops[0].iter, ast.Tuple) and [x.value for x in arm_loops[0].iter.elts] == ["zon"]
    assert FINAL.index("whole-notebook deadline reached") < FINAL.index("_zon_os.replace(_zon_tmp, _zon_target)")
    assert FINAL.index("_zon_os.replace(_zon_tmp, _zon_target)") < FINAL.index("_zon_signal.alarm(0)")
    receipt = json.loads((OUT.parent / "build-receipt.json").read_text(encoding="utf-8"))
    assert receipt["parent_notebook_sha256"] == hashlib.sha256(BASE.read_bytes()).hexdigest()
    assert receipt["parent_module_sha256"] == hashlib.sha256((ROOT / "experiments/exp_061_zon_lb_submission_repair_v3/snapshot/extra_files/exp061_zon_deployment.py").read_bytes()).hexdigest()
    assert receipt["module_sha256"] == hashlib.sha256(MODULE.read_bytes()).hexdigest()
    assert receipt["notebook_sha256"] == hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert receipt["watchdog_disarm_after_publication"] is True
    return nb


def load_fixture():
    t = load_path("test_exp061_behavioral_v3_fixture", ROOT / "scripts/test_exp061_behavioral.py")
    return t


def load_deployment_module():
    return load_path("exp061_zon_deployment_v4", MODULE)


def run_mock(work, *, fourfold=False, no_veto=False, missing_score=False, omit_dataset=False):
    import numpy as np
    fixture = load_fixture()
    m, g = fixture._build_mock_g(np, str(work), model_bias=0.7)
    deploy = load_deployment_module()
    g["EXPERIMENT_ID"] = "exp_061_zon_lb_submission_repair_v4"
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
    start = time.perf_counter()
    telemetry = deploy.run_exp061_zon_deployment(g)
    elapsed = time.perf_counter() - start
    metrics = json.loads((Path(g["WORKING_DIR"]) / "metrics.json").read_text())
    return deploy, g, telemetry, metrics, elapsed


def _csv_payload(header=None, edge_target_t=1):
    columns = header or ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
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
        # Mimics the parent notebook's already-created 0.947 artifact before final adapter starts.
        target.write_bytes(b"parent-output-must-never-survive-a-v3-failure")
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
        g = {"SUBMISSION_PATH": target, "WORKING_DIR": str(root), "CSV_COLUMNS": receipt and
             ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"],
             "test_stems": ["d0"], "run_exp061_zon_deployment": runner,
             "_EXP061_RUN_START": time.time() - (7201 if mode == "deadline_expired" else 0),
             "EXP061_HARD_STOP_SECONDS": 7200.0}
        try:
            exec(FINAL, g)
        except Exception:
            assert mode != "ok"
            assert not target.exists(), f"fallback submission survived {mode}"
        else:
            assert mode == "ok"
            assert target.read_bytes() == payload


def validate(path):
    assert_source_contract(path)
    print("PASS: immutable parent cells, zon-only AST, watchdog active through publication")
    modes = ("ok", "runner_exception", "integrity_failure", "dataset_incomplete",
             "receipt_dataset_missing", "digest_mismatch", "bad_schema", "bad_graph", "deadline_expired")
    for mode in modes:
        publication_case(mode)
    print("PASS: final publication positives/negatives incl. deadline; parent fallback deleted")

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
        assert telemetry["feasibility_worksheet"]["process_peak_rss_bytes"] is None or telemetry["feasibility_worksheet"]["process_peak_rss_bytes"] > 0
    print("PASS: mocked end-to-end zon-only, all score receipts finite, exact per-frame 16-view list")

    with tempfile.TemporaryDirectory() as td:
        _, _, tel, metrics, elapsed4x = run_mock(Path(td) / "fourfold", fourfold=True)
        assert metrics["exp061_zon_deployment_integrity_passed"] is True
        assert metrics["checks"]["all_discovered_test_datasets_completed"] is True
        assert len(json.loads((Path(_["WORKING_DIR"]) / "exp061" / "receipt_zon.json").read_text())["per_dataset"]) == 8
        print(f"PASS: deterministic fourfold dataset-count fixture, elapsed={elapsed4x:.3f}s "
              f"disk_cache_bytes={tel['feasibility_worksheet']['view_cache_capacity_io']['disk_view_bytes']}")

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

