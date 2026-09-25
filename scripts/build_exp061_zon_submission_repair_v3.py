"""Build exp061 zon-only deployment notebook v3 from the immutable upstream snapshot."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import yaml

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / ".private/exp061_lb_repair/upstream/biohub-exp061-deepcenter-tta.ipynb"
MODULE = ROOT / "scripts/exp061_zon_deployment.py"
OUT = ROOT / ".private/exp061_lb_repair_v3/build/exp061_zon_submission_repair_v3.ipynb"
EXPERIMENT = "exp_061_zon_lb_submission_repair_v3"
IDENTITY_ANCHOR = "from __future__ import annotations\n"
IDENTITY_LINE = "EXPERIMENT_ID = '__CONTROLLER_EXPERIMENT_ID__'  # submission adapter metadata\n"
WATCHDOG_OLD = "'experiment_id': 'exp_061_deepcenter_tta'"
WATCHDOG_NEW = "'experiment_id': EXPERIMENT_ID"
EXPECTED_BASE_SHA256 = "bb60ffe996a81bfaad7a3f8c53b1282d5772a68fb12536c58bfa24c483f16aae"
EXPECTED_MODULE_SHA256 = "35aa6d61c543a891da5649ed48722938e10b4ca240a31d3c3e4360c3ccd39123"

FINAL = r'''# Publish only the zon result produced by this execution.
import csv as _zon_csv
import hashlib as _zon_hashlib
import json as _zon_json
import os as _zon_os
import shutil as _zon_shutil
from pathlib import Path as _zon_Path

_zon_target = _zon_Path(SUBMISSION_PATH)
if _zon_target.exists():
    _zon_target.unlink()
_zon_telemetry = run_exp061_zon_deployment(globals())
_zon_work = _zon_Path(WORKING_DIR)
_zon_metrics = _zon_json.loads((_zon_work / "metrics.json").read_text())
if not _zon_metrics.get("exp061_zon_deployment_integrity_passed"):
    raise RuntimeError("Refusing publication: zon deployment integrity failed")
if not _zon_metrics.get("checks", {}).get("all_discovered_test_datasets_completed"):
    raise RuntimeError("Refusing publication: not every discovered test dataset completed")
if _zon_metrics.get("arm_status", {}).get("zon") != "completed":
    raise RuntimeError("Refusing publication: zon arm did not complete")
if _zon_metrics.get("run_exception") is not None:
    raise RuntimeError("Refusing publication: zon runner recorded an exception")
if not _zon_metrics.get("veto_calls_accounted_for"):
    raise RuntimeError("Refusing publication: veto score receipts are incomplete")

_zon_csv_path = _zon_work / "exp061" / "submission_zon.csv"
_zon_receipt_path = _zon_work / "exp061" / "receipt_zon.json"
_zon_receipt = _zon_json.loads(_zon_receipt_path.read_text())
_zon_expected_datasets = sorted(str(s) for s in test_stems)
if _zon_receipt.get("status") != "completed":
    raise RuntimeError("Refusing publication: zon receipt is incomplete")
if sorted(_zon_receipt.get("per_dataset", [])) != _zon_expected_datasets:
    raise RuntimeError("Refusing publication: zon receipt dataset set differs from test discovery")
_zon_digest = _zon_hashlib.sha256(_zon_csv_path.read_bytes()).hexdigest()
if _zon_digest != _zon_receipt.get("sha256"):
    raise RuntimeError("Refusing publication: zon CSV digest differs from receipt")
if _zon_digest != _zon_metrics.get("arm_submission_sha256", {}).get("zon"):
    raise RuntimeError("Refusing publication: zon CSV digest differs from metrics")

with _zon_csv_path.open("r", newline="", encoding="utf-8") as _zon_fh:
    _zon_reader = _zon_csv.DictReader(_zon_fh)
    if _zon_reader.fieldnames != list(CSV_COLUMNS):
        raise RuntimeError("Refusing publication: CSV schema differs from competition header")
    _zon_rows = list(_zon_reader)
if not _zon_rows or len(_zon_rows) != int(_zon_receipt.get("rows", -1)):
    raise RuntimeError("Refusing publication: zon CSV row count is empty or inconsistent")
_zon_integer_columns = ("id", "node_id", "t", "z", "y", "x", "source_id", "target_id")
_zon_ids = []
_zon_nodes = {}
_zon_edges = {}
for _zon_line, _zon_row in enumerate(_zon_rows, start=2):
    if None in _zon_row or set(_zon_row) != set(CSV_COLUMNS):
        raise RuntimeError(f"Refusing publication: malformed CSV columns on row {_zon_line}")
    if any(_zon_row.get(name) is None or _zon_row.get(name) == "" for name in CSV_COLUMNS):
        raise RuntimeError(f"Refusing publication: empty CSV field on row {_zon_line}")
    try:
        _zon_values = {name: int(_zon_row[name]) for name in _zon_integer_columns}
    except (TypeError, ValueError) as _zon_exc:
        raise RuntimeError(f"Refusing publication: non-integer CSV field on row {_zon_line}") from _zon_exc
    _zon_ids.append(_zon_values["id"])
    _zon_ds = _zon_row["dataset"]
    if not _zon_ds:
        raise RuntimeError(f"Refusing publication: empty dataset on row {_zon_line}")
    if _zon_row["row_type"] == "node":
        if _zon_values["source_id"] != -1 or _zon_values["target_id"] != -1:
            raise RuntimeError(f"Refusing publication: invalid node sentinels on row {_zon_line}")
        if min(_zon_values[name] for name in ("node_id", "t", "z", "y", "x")) < 0:
            raise RuntimeError(f"Refusing publication: negative node field on row {_zon_line}")
        _zon_ds_nodes = _zon_nodes.setdefault(_zon_ds, {})
        if _zon_values["node_id"] in _zon_ds_nodes:
            raise RuntimeError(f"Refusing publication: duplicate node on row {_zon_line}")
        _zon_ds_nodes[_zon_values["node_id"]] = _zon_values["t"]
    elif _zon_row["row_type"] == "edge":
        if any(_zon_values[name] != -1 for name in ("node_id", "t", "z", "y", "x")):
            raise RuntimeError(f"Refusing publication: invalid edge sentinels on row {_zon_line}")
        if min(_zon_values["source_id"], _zon_values["target_id"]) < 0:
            raise RuntimeError(f"Refusing publication: negative edge endpoint on row {_zon_line}")
        _zon_edges.setdefault(_zon_ds, []).append((_zon_values["source_id"], _zon_values["target_id"]))
    else:
        raise RuntimeError(f"Refusing publication: invalid row type on row {_zon_line}")
if _zon_ids != list(range(len(_zon_ids))) or not _zon_ids or not _zon_nodes:
    raise RuntimeError("Refusing publication: CSV IDs are invalid or CSV has no node data")
if set(_zon_nodes) != set(_zon_expected_datasets):
    raise RuntimeError("Refusing publication: CSV dataset set differs from test discovery")
for _zon_ds, _zon_ds_edges in _zon_edges.items():
    _zon_seen_edges = set()
    _zon_indegree = {}
    _zon_outdegree = {}
    for _zon_source, _zon_target_id in _zon_ds_edges:
        _zon_edge = (_zon_source, _zon_target_id)
        if _zon_edge in _zon_seen_edges:
            raise RuntimeError("Refusing publication: duplicate graph edge")
        _zon_seen_edges.add(_zon_edge)
        _zon_ds_nodes = _zon_nodes.get(_zon_ds, {})
        if _zon_source not in _zon_ds_nodes or _zon_target_id not in _zon_ds_nodes:
            raise RuntimeError("Refusing publication: graph edge endpoint is missing")
        if _zon_ds_nodes[_zon_target_id] != _zon_ds_nodes[_zon_source] + 1:
            raise RuntimeError("Refusing publication: graph edge is not between adjacent frames")
        _zon_outdegree[_zon_source] = _zon_outdegree.get(_zon_source, 0) + 1
        _zon_indegree[_zon_target_id] = _zon_indegree.get(_zon_target_id, 0) + 1
    if max(_zon_indegree.values(), default=0) > 1 or max(_zon_outdegree.values(), default=0) > 2:
        raise RuntimeError("Refusing publication: lineage degree constraint failed")
_zon_tmp = _zon_target.with_name(_zon_target.name + ".zon.tmp")
_zon_shutil.copyfile(_zon_csv_path, _zon_tmp)
if _zon_hashlib.sha256(_zon_tmp.read_bytes()).hexdigest() != _zon_digest:
    _zon_tmp.unlink(missing_ok=True)
    raise RuntimeError("Refusing publication: staged submission digest mismatch")
_zon_os.replace(_zon_tmp, _zon_target)
print("Published current-run zon submission:", _zon_digest)
'''

def build():
    base_bytes = BASE.read_bytes()
    module_bytes = MODULE.read_bytes()
    if hashlib.sha256(base_bytes).hexdigest() != EXPECTED_BASE_SHA256:
        raise SystemExit("frozen upstream notebook SHA256 mismatch")
    if hashlib.sha256(module_bytes).hexdigest() != EXPECTED_MODULE_SHA256:
        raise SystemExit("generated zon deployment module SHA256 mismatch")
    source = json.loads(base_bytes.decode("utf-8"))
    result = copy.deepcopy(source)
    if len(source.get("cells", [])) != 5:
        raise SystemExit("unexpected upstream notebook cell count")
    parent_code = "".join(source["cells"][2]["source"])
    if parent_code.count(IDENTITY_ANCHOR) != 1 or parent_code.count(WATCHDOG_OLD) != 1:
        raise SystemExit("parent inference identity/watchdog anchors drifted")
    result["cells"][2]["source"] = parent_code.replace(
        IDENTITY_ANCHOR, IDENTITY_ANCHOR + IDENTITY_LINE
    ).replace(WATCHDOG_OLD, WATCHDOG_NEW).splitlines(True)
    result["cells"][3]["source"] = module_bytes.decode("utf-8").splitlines(True)
    result["cells"][4]["source"] = FINAL.splitlines(True)

    restored_parent = "".join(result["cells"][2]["source"]).replace(IDENTITY_LINE, "").replace(WATCHDOG_NEW, WATCHDOG_OLD)
    if restored_parent != parent_code:
        raise SystemExit("parent inference cell differs beyond experiment identity/watchdog metadata")
    if result["cells"][:2] != source["cells"][:2]:
        raise SystemExit("pre-inference cells changed")
    module_code = "".join(result["cells"][3]["source"])
    module_tree = ast.parse(module_code)
    runner = next((node for node in module_tree.body
                   if isinstance(node, ast.FunctionDef) and node.name == "run_exp061_zon_deployment"), None)
    if runner is None:
        raise SystemExit("deployment module entrypoint mismatch")
    calls = [node for node in ast.walk(module_tree) if isinstance(node, ast.Call)]
    if any(isinstance(node.func, ast.Name) and node.func.id == "run_exp061_deepcenter_tta"
           for node in calls):
        raise SystemExit("old research runner is called by the deployment module")
    zon_loops = [node for node in ast.walk(runner) if isinstance(node, ast.For)
                 and isinstance(node.target, ast.Name) and node.target.id == "arm"]
    if len(zon_loops) != 1 or not (isinstance(zon_loops[0].iter, ast.Tuple)
                                   and [elt.value for elt in zon_loops[0].iter.elts] == ["zon"]):
        raise SystemExit("runner arm loop is not exactly zon-only")
    for index, cell in enumerate(result["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"v3_cell_{index}", "exec")
            cell["outputs"] = []
            cell["execution_count"] = None
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")

    config = yaml.safe_load((ROOT / "configs/exp_061_zon_lb_submission_repair_v2.yaml").read_text(encoding="utf-8"))
    config.update(
        experiment_id=EXPERIMENT,
        parent="exp_061_zon_lb_submission_repair_v2",
        source_notebook=OUT.relative_to(ROOT).as_posix(),
        hypothesis=("Removing the current-input XY reference and xyonly/xyd4 development replays from the scoring path "
                    "will reduce deployment work while preserving the exact zon output for a fixed input; the hidden "
                    "failure cause remains unknown."),
        change={
            "component": "zon_only_code_competition_deployment",
            "from": "v2 full parent pipeline plus current-input XY reference and xyonly/zon/xyd4 replay",
            "to": "same parent pipeline plus exactly one zon replay and fail-closed current-run publication",
            "variables_changed": "deployment execution and validation contract only; no model or prediction-policy changes",
        },
        authorization={
            "scope": "User explicitly requested rebuilding and running the submission notebook based on current project state. "
                     "This authorizes one bounded Kaggle kernel run after consensus, fresh Codex PASS, snapshot smoke and budget reservation. "
                     "It does not authorize leaderboard submission.",
        },
    )
    config["substrate_note"] = (
        "The executed exp061 parent inference is unchanged except for experiment identity "
        "metadata. Deployment runs one zon replay with the frozen transforms, graph "
        "writer, and prediction policy. The independent XY reference and xyonly/xyd4 "
        "research replays are omitted."
    )
    config["validation"]["protocol"] = "exp061_zon_only_deployment_v3"
    config["validation"]["warning"] = (
        "Deployment integrity only. XY parity, xyd4 and the independent XY reference are development-only and intentionally omitted. "
        "The exact hidden traceback and hidden workload size are unavailable; the 4x-public estimate is risk screening only, not a guarantee. "
        "The 2h watchdog and 20m finalization reserve remain unchanged. This run does not authorize or perform an LB submission."
    )
    config["evaluation"]["gate_field"] = "exp061_zon_deployment_integrity_passed"
    config["submission"]["user_authorized_count"] = 0
    config["authorization"]["no_leaderboard_submission"] = True
    config["budget"]["expected_gpu_hours"] = 2.0
    config["provenance"].update(
        builder="scripts/build_exp061_zon_submission_repair_v3.py",
        module_builder="scripts/build_exp061_zon_deployment_module.py",
        appended_module="scripts/exp061_zon_deployment.py",
        source_parent="exp_061_zon_lb_submission_repair_v2",
        strategy_amendment="experiments/exp_061_zon_lb_submission_repair_v3/strategy_amendment_v2.md",
        arms=["zon"],
        historical_development_zon_sha256="2593a5438a17e5649736fcd6ad2f7af4c2fa8f822a759e9f51d877cdf6c840a1",
        generated_zon_deployment_sha256=EXPECTED_MODULE_SHA256,
    )
    config["provenance"].pop("historical_development_xyonly_submission_sha256", None)
    config["provenance"].pop("repair_dependency_sha256", None)
    config["kaggle"].update(slug="biohub-exp061-zon-deploy-v3", title="biohub-exp061-zon-deploy-v3",
                            extra_files=[
                                "scripts/build_exp061_zon_submission_repair_v3.py",
                                "scripts/build_exp061_zon_deployment_module.py",
                                "scripts/exp061_zon_deployment.py",
                                "scripts/validate_exp061_zon_deployment_v3.py",
                                BASE.relative_to(ROOT).as_posix(),
                            ])
    config["local"]["smoke_test"] = ["{python}", "scripts/validate_exp061_zon_deployment_v3.py", "{source_notebook}"]
    config["admission"]["require_codex_review"] = True
    config["admission"]["reviewer_provider"] = "codex"
    config["admission"]["require_claude_review"] = False
    (ROOT / "configs" / f"{EXPERIMENT}.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    receipt = {
        "base_sha256": hashlib.sha256(base_bytes).hexdigest(),
        "module_sha256": hashlib.sha256(module_bytes).hexdigest(),
        "notebook_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
        "parent_inference_cell_unchanged_after_metadata_restore": True,
        "pre_inference_cells_unchanged": True,
        "deployment_arms": ["zon"],
        "development_replays_omitted": ["current_input_xy_reference", "xyonly", "xyd4"],
    }
    (OUT.parent / "build-receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))

if __name__ == "__main__":
    build()


