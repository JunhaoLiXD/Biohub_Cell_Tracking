from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .core import (
    ControllerError,
    experiment_dir,
    load_config,
    load_record,
    read_json,
    save_record,
    state_lock,
    transition,
    utc_now,
    write_json,
)


def _finite_number(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ControllerError(f"Metric field {field} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ControllerError(f"Metric field {field} must be finite")
    return number


def find_remote_metrics(artifacts_dir: Path) -> Path:
    matches = sorted(path for path in artifacts_dir.rglob("metrics.json") if path.is_file())
    if not matches:
        raise ControllerError(f"Remote output did not contain metrics.json under {artifacts_dir}")
    if len(matches) > 1:
        relative = ", ".join(str(path.relative_to(artifacts_dir)) for path in matches)
        raise ControllerError(f"Remote output contained multiple metrics.json files: {relative}")
    return matches[0]


def parse_metrics(root: Path, experiment_id: str, source: Path | None = None) -> dict[str, Any]:
    record = load_record(root, experiment_id)
    _, config = load_config(root / str(record["snapshot_config"]), root)
    metrics_path = source or find_remote_metrics(experiment_dir(root, experiment_id) / "artifacts")
    payload = read_json(metrics_path)
    if not isinstance(payload, dict):
        raise ControllerError("metrics.json must contain a JSON object")
    if payload.get("schema_version") != 1:
        raise ControllerError("metrics.json must declare schema_version=1")
    if payload.get("experiment_id") != experiment_id:
        raise ControllerError(
            f"Metric experiment_id mismatch: expected {experiment_id}, got {payload.get('experiment_id')!r}"
        )
    expected_protocol = str(config["validation"]["protocol"])
    validation = payload.get("validation")
    if not isinstance(validation, dict):
        raise ControllerError("metrics.json validation must be an object")
    if validation.get("protocol") != expected_protocol:
        raise ControllerError(
            f"Validation protocol mismatch: expected {expected_protocol}, got {validation.get('protocol')!r}"
        )
    primary = _finite_number(payload.get("primary_metric"), "primary_metric")
    payload["primary_metric"] = primary
    if "baseline_primary_metric" in payload and payload["baseline_primary_metric"] is not None:
        payload["baseline_primary_metric"] = _finite_number(
            payload["baseline_primary_metric"], "baseline_primary_metric"
        )
    runtime_seconds = _finite_number(payload.get("runtime_seconds", 0.0), "runtime_seconds")
    if runtime_seconds < 0:
        raise ControllerError("runtime_seconds must be non-negative")
    payload["runtime_seconds"] = runtime_seconds

    required_specimens = [str(item) for item in config["validation"].get("required_specimens", [])]
    specimen_metrics = payload.get("specimen_metrics", {})
    if required_specimens:
        if not isinstance(specimen_metrics, dict):
            raise ControllerError("specimen_metrics must be an object")
        missing = [name for name in required_specimens if name not in specimen_metrics]
        if missing:
            raise ControllerError(f"metrics.json is missing required specimens: {', '.join(missing)}")
        for specimen in required_specimens:
            value = specimen_metrics[specimen]
            if not isinstance(value, dict):
                raise ControllerError(f"specimen_metrics.{specimen} must be an object")
            value["primary_metric"] = _finite_number(
                value.get("primary_metric"), f"specimen_metrics.{specimen}.primary_metric"
            )
            if value.get("baseline_primary_metric") is not None:
                value["baseline_primary_metric"] = _finite_number(
                    value["baseline_primary_metric"],
                    f"specimen_metrics.{specimen}.baseline_primary_metric",
                )

    payload["parsed_at"] = utc_now()
    payload["source"] = str(metrics_path.resolve())
    write_json(experiment_dir(root, experiment_id) / "metrics.json", payload)
    return payload


def _specimen_deltas(metrics: dict[str, Any], required: list[str]) -> dict[str, float]:
    deltas: dict[str, float] = {}
    specimen_metrics = metrics.get("specimen_metrics", {})
    for specimen in required:
        item = specimen_metrics[specimen]
        if item.get("delta") is not None:
            deltas[specimen] = _finite_number(item["delta"], f"specimen_metrics.{specimen}.delta")
        elif item.get("baseline_primary_metric") is not None:
            deltas[specimen] = float(item["primary_metric"]) - float(item["baseline_primary_metric"])
        else:
            raise ControllerError(
                f"specimen_metrics.{specimen} needs delta or baseline_primary_metric for comparison"
            )
    return deltas


def decide(root: Path, experiment_id: str, metrics: dict[str, Any]) -> tuple[str, float | None, float | None]:
    record = load_record(root, experiment_id)
    _, config = load_config(root / str(record["snapshot_config"]), root)
    evaluation = config.get("evaluation", {})
    mode = evaluation.get("mode", "compare")
    if mode == "gate":
        gate_field = str(evaluation.get("gate_field", "gate_passed"))
        gate_value = metrics.get("metrics", {}).get(gate_field, metrics.get(gate_field))
        if gate_value is True:
            return "KEEP", None, None
        if gate_value is False:
            return "REJECT", None, None
        return "INCONCLUSIVE", None, None
    if mode != "compare":
        raise ControllerError(f"Unsupported evaluation.mode: {mode}")

    current = read_json(root / "CURRENT_BEST.json")
    current_protocol = current.get("validation_protocol")
    candidate_protocol = config["validation"]["protocol"]
    baseline = metrics.get("baseline_primary_metric")
    if current_protocol != candidate_protocol and baseline is None:
        raise ControllerError(
            "Candidate validation protocol differs from CURRENT_BEST; metrics.json must include a paired baseline_primary_metric"
        )
    if baseline is None:
        baseline = current.get("validation_score")
    if baseline is None:
        raise ControllerError("No comparable baseline metric is available")
    baseline_score = _finite_number(baseline, "comparison baseline")
    primary = float(metrics["primary_metric"])
    delta = primary - baseline_score

    success = config["success"]
    min_improvement = float(success["minimum_improvement"])
    regression_threshold = float(success["regression_threshold"])
    tolerance = float(success.get("per_specimen_max_regression", 0.0))
    required = [str(item) for item in config["validation"].get("required_specimens", [])]
    specimen_deltas = _specimen_deltas(metrics, required) if required else {}
    specimen_regression = any(value < -tolerance for value in specimen_deltas.values())

    if delta >= min_improvement and not specimen_regression:
        return "KEEP", baseline_score, delta
    if delta <= regression_threshold or specimen_regression:
        return "REJECT", baseline_score, delta
    return "INCONCLUSIVE", baseline_score, delta


def _update_registry_markdown(root: Path, results: dict[str, Any]) -> None:
    lines = [
        "# Automated Experiment Registry",
        "",
        "This file is maintained by `scripts/update_results.py`. Detailed historical notebook notes remain",
        "in `docs/experiments.md`.",
        "",
        "| Experiment | State | Decision | Primary metric | Delta | Protocol |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in results.get("experiments", []):
        primary = item.get("validation_score")
        delta = item.get("delta")
        primary_text = f"{float(primary):.6f}" if isinstance(primary, (int, float)) else "-"
        delta_text = f"{float(delta):+.6f}" if isinstance(delta, (int, float)) else "-"
        lines.append(
            f"| `{item.get('experiment_id', '-')}` | {item.get('status', '-')} | "
            f"{item.get('decision', '-')} | {primary_text} | {delta_text} | "
            f"`{item.get('validation_protocol', '-')}` |"
        )
    (root / "EXPERIMENTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def evaluate(
    root: Path,
    experiment_id: str,
    metrics: dict[str, Any],
    *,
    promote: bool = False,
) -> dict[str, Any]:
    record = load_record(root, experiment_id)
    if record["state"] != "COLLECTING":
        raise ControllerError(f"Evaluation requires COLLECTING state, got {record['state']}")
    decision, baseline_score, delta = decide(root, experiment_id, metrics)
    transition(root, record, "EVALUATED")
    record = load_record(root, experiment_id)
    record["evaluation"] = {
        "decision": decision,
        "primary_metric": metrics["primary_metric"],
        "baseline_primary_metric": baseline_score,
        "delta": delta,
        "evaluated_at": utc_now(),
    }
    save_record(root, record)
    transition(root, record, decision)

    results_path = root / "results.json"
    entry = {
        "experiment_id": experiment_id,
        "status": decision,
        "parent": record.get("parent"),
        "hypothesis": record.get("hypothesis"),
        "validation_score": metrics["primary_metric"],
        "validation_protocol": record.get("validation_protocol"),
        "previous_best": baseline_score,
        "delta": delta,
        "runtime_hours": float(metrics.get("runtime_seconds", 0.0)) / 3600.0,
        "decision": decision,
        "git_commit": record.get("git_commit"),
        "metrics_path": (experiment_dir(root, experiment_id) / "metrics.json").relative_to(root).as_posix(),
        "evaluated_at": utc_now(),
    }
    # results.json and CURRENT_BEST.json are shared ledgers; guard the read-modify-write.
    with state_lock(root):
        results = read_json(results_path)
        experiments = results.setdefault("experiments", [])
        experiments[:] = [item for item in experiments if item.get("experiment_id") != experiment_id]
        experiments.append(entry)
        write_json(results_path, results)
        _update_registry_markdown(root, results)

        if promote:
            promote_current_best(root, experiment_id, metrics, decision)
    return entry


def promote_current_best(root: Path, experiment_id: str, metrics: dict[str, Any], decision: str) -> None:
    if decision != "KEEP":
        raise ControllerError("Only a KEEP experiment can be promoted")
    record = load_record(root, experiment_id)
    _, config = load_config(root / str(record["snapshot_config"]), root)
    if config.get("evaluation", {}).get("mode", "compare") != "compare":
        raise ControllerError("Research-gate experiments cannot become CURRENT_BEST")
    admission = config.get("admission", {})
    if not admission.get("methodology_valid", False):
        raise ControllerError("Promotion blocked: admission.methodology_valid is not true")
    if record.get("review", {}).get("required") and record["review"].get("status") != "PASSED":
        raise ControllerError("Promotion blocked: required Claude review is not complete")
    if admission.get("require_reproducible_for_promotion", True) and not metrics.get("reproducible", False):
        raise ControllerError("Promotion blocked: metrics.json does not mark the result reproducible")
    current = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "validation_score": metrics["primary_metric"],
        "validation_protocol": config["validation"]["protocol"],
        "public_lb": metrics.get("public_lb"),
        "config": record["config"],
        "source_notebook": config["source_notebook"],
        "checkpoint": metrics.get("checkpoint"),
        "git_commit": record.get("git_commit"),
        "status": "verified",
        "promoted_at": utc_now(),
    }
    write_json(root / "CURRENT_BEST.json", current)
