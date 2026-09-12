"""Local collection adapter for an unmodified public notebook; never executes it."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from .core import ControllerError, load_record, transition, verify_snapshot, write_json
from .kaggle import _mark_record_budget_consumed, _next_page_token, _run_kaggle, check_status
from .metrics import evaluate, parse_metrics

EXPERIMENT = "repro_047_public_0946_edge_feature_tta_exact_copy"
PROTOCOL = "public_0946_path_only_edited_upstream_train4_lb_probe_v1"
NOTEBOOK_SHA256 = "4eda3c3dae83f5ad21fee35513aad5f325e09b6de8f77fa55d9b7d6d4b50ca16"
DEEPCENTER_SHA256 = "8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0"


def finite(value: object) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ControllerError("Non-finite native metric or coordinate")
    return number


def read_validator(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        raw = list(csv.DictReader(stream))
    if len(raw) != 4 or len({row["stem"] for row in raw}) != 4:
        raise ControllerError("Expected four unique upstream validation samples")
    counts = Counter(row["stem"].split("_", 1)[0] for row in raw)
    if counts != {"44b6": 2, "6bba": 2}:
        raise ControllerError("Expected two validation samples per specimen")
    rows = []
    for row in raw:
        item = {"stem": row["stem"]}
        for key in ("weight", "adjusted_edge_jaccard", "div_tp", "div_fp", "div_fn"):
            item[key] = finite(row[key])
            if item[key] < 0:
                raise ControllerError("Negative native metric component")
        if item["adjusted_edge_jaccard"] > 1 or item["weight"] <= 0:
            raise ControllerError("Invalid native edge metric")
        rows.append(item)
    return rows


def aggregate(rows: list[dict]) -> dict:
    # Same weighted-edge and pooled-division aggregation as upstream
    # aggregate_official(), applied only to structured validator_results.csv.
    weight = sum(row["weight"] for row in rows)
    adjusted = sum(row["weight"] * row["adjusted_edge_jaccard"] for row in rows) / weight
    tp, fp, fn = (sum(row[key] for row in rows) for key in ("div_tp", "div_fp", "div_fn"))
    division = tp / (tp + fp + fn) if tp + fp + fn else 0.0
    return {"primary_metric": adjusted + 0.1 * division,
            "adjusted_edge_jaccard": adjusted, "division_jaccard": division,
            "samples": [row["stem"] for row in rows]}


def audit_submission(path: Path) -> dict:
    nodes, edges = {}, []
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"}
        if set(reader.fieldnames or []) != required:
            raise ControllerError("Submission column contract differs from upstream")
        seen_ids = set()
        for row in reader:
            if row["id"] in seen_ids:
                raise ControllerError("Duplicate submission row id")
            seen_ids.add(row["id"])
            dataset = row["dataset"]
            if row["row_type"] == "node":
                key = (dataset, int(row["node_id"]))
                if key in nodes:
                    raise ControllerError("Duplicate node id within dataset")
                nodes[key] = int(row["t"])
                for axis in ("z", "y", "x"):
                    if finite(row[axis]) < 0:
                        raise ControllerError("Negative node coordinate")
            elif row["row_type"] == "edge":
                edges.append((dataset, int(row["source_id"]), int(row["target_id"])))
            else:
                raise ControllerError("Unknown submission row type")
    datasets = sorted({key[0] for key in nodes})
    if Counter(s.split("_", 1)[0] for s in datasets) != {"44b6": 2, "6bba": 2}:
        raise ControllerError("Submission must contain the four test movies")
    if not edges or len(set(edges)) != len(edges):
        raise ControllerError("Empty or duplicate edge list")
    incoming, outgoing = Counter(), Counter()
    for dataset, source, target in edges:
        a, b = (dataset, source), (dataset, target)
        if a not in nodes or b not in nodes or nodes[b] != nodes[a] + 1:
            raise ControllerError("Dangling, self, backward, or nonconsecutive edge")
        incoming[b] += 1
        outgoing[a] += 1
    if max(incoming.values()) > 1 or max(outgoing.values()) > 2:
        raise ControllerError("Invalid parent or daughter degree")
    return {"datasets": datasets, "nodes": len(nodes), "edges": len(edges),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def collect(root: Path) -> dict:
    record = load_record(root, EXPERIMENT)
    verify_snapshot(root, record)
    if hashlib.sha256((root / record["snapshot_source"]).read_bytes()).hexdigest() != NOTEBOOK_SHA256:
        raise ControllerError("Public source does not match the audited path-only edited copy")
    record = check_status(root, EXPERIMENT)
    if record["remote"]["status"] != "COMPLETE":
        raise ControllerError("Public copy is not complete")
    if record["state"] not in {"RUNNING", "SUBMITTED", "COLLECTING"}:
        raise ControllerError("Collection is already evaluated or is not admissible")
    exp_dir = root / "experiments" / EXPERIMENT
    artifacts = exp_dir / "artifacts"
    artifacts.mkdir(exist_ok=True)
    transition(root, record, "COLLECTING")
    token, seen_tokens = None, set()
    while True:
        args = ["kernels", "output", record["remote"]["kernel_id"], "-p", str(artifacts),
                "--page-size", "200", "--file-pattern", r"(^|/)[^/]+\.(csv|json|log)$"]
        if token:
            args += ["--page-token", token]
        result = _run_kaggle(root, EXPERIMENT, args, "kaggle-collect.log")
        if result.returncode:
            raise ControllerError("Public output download failed; preserve state for explicit recovery")
        token = _next_page_token(result)
        if token is None:
            break
        if token in seen_tokens:
            raise ControllerError("Repeated output page token")
        seen_tokens.add(token)
    try:
        log_path = artifacts / (record["remote"]["kernel_id"].split("/")[1] + ".log")
        events = json.loads(log_path.read_text(encoding="utf-8"))
        runtime = max(finite(event["time"]) for event in events)
        if runtime <= 0:
            raise ControllerError("Missing positive runtime")
        # Runtime comes from structured event timestamps, never a metric in prose.
        text = "".join(str(event.get("data", "")) for event in events)
        receipt = json.loads((artifacts / "bidirectional_production_runtime_integrity.json").read_text())
        dc_path = receipt["materialized_paths"]["deepcenter"]
        if (not dc_path.endswith("/best.pt") or receipt["checkpoint_sha256"]["deepcenter"] != DEEPCENTER_SHA256
                or f"Loaded DeepCenter add-only gate checkpoint: {dc_path}\n" not in text
                or "Loaded DeepCenter add-only gate checkpoint:" not in text
                or any("checkpoint_last.pt" in line for line in text.splitlines()
                       if "Loaded DeepCenter add-only gate checkpoint:" in line)):
            raise ControllerError("Actual DeepCenter loading does not match verified best.pt")
        rows = read_validator(artifacts / "validator_results.csv")
        summary = aggregate(rows)
        submission = audit_submission(artifacts / "submission.csv")
        payload = {"schema_version": 1, "experiment_id": EXPERIMENT,
                   "primary_metric": summary["primary_metric"], "runtime_seconds": runtime,
                   "reproducible": False,
                   "validation": {"protocol": PROTOCOL, "sample_count": 4,
                                  "adjusted_edge_jaccard": summary["adjusted_edge_jaccard"],
                                  "division_jaccard": summary["division_jaccard"],
                                  "warning": "Original train4 proxy; not comparable with train16 or Public LB."},
                   "specimen_metrics": {s: aggregate([r for r in rows if r["stem"].startswith(s + "_")])
                                        for s in ("44b6", "6bba")},
                   "metrics": {"copy_execution_passed": True, "submission_audit": submission,
                               "actual_deepcenter_path": dc_path,
                               "public_lb_reproduction_passed": None}}
        write_json(exp_dir / "native-metrics-adapter.json", payload)
        metrics = parse_metrics(root, EXPERIMENT, exp_dir / "native-metrics-adapter.json")
        _mark_record_budget_consumed(root, EXPERIMENT, runtime / 3600.0)
        return evaluate(root, EXPERIMENT, metrics, promote=False)
    except (ControllerError, ValueError, KeyError, OSError) as exc:
        record = load_record(root, EXPERIMENT)
        _mark_record_budget_consumed(root, EXPERIMENT, record["budget"]["expected_gpu_hours"])
        transition(root, load_record(root, EXPERIMENT), "INVALID_METRIC", note=str(exc))
        raise ControllerError(f"Public copy audit failed: {exc}") from exc
