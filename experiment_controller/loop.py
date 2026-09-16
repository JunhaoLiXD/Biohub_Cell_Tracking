from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .core import (
    ControllerError,
    create_experiment,
    experiment_dir,
    load_config,
    load_record,
    read_json,
    review_provider_label,
    write_json,
)
from .kaggle import check_status, collect, launch


def run_once(root: Path) -> list[dict[str, Any]]:
    queue_path = root / "research" / "experiment_queue.json"
    queue = read_json(queue_path)
    limits = queue.get("limits", {})
    entries = queue.get("experiments", [])
    approved = [item for item in entries if item.get("approved") is True]
    max_experiments = int(limits.get("max_autonomous_experiments", 3))
    if len(approved) > max_experiments:
        raise ControllerError(f"Queue has {len(approved)} approved experiments, above limit {max_experiments}")
    expected_total = 0.0
    for item in approved:
        _, config = load_config(root / str(item["config"]), root)
        expected_total += float(config["budget"]["expected_gpu_hours"])
    if expected_total > float(limits.get("max_gpu_hours", 6.0)):
        raise ControllerError(
            f"Approved queue requests {expected_total:.2f} GPU h, above autonomous limit {limits.get('max_gpu_hours')}"
        )
    if int(limits.get("max_leaderboard_submissions", 0)) != 0:
        raise ControllerError("V1 controlled loop requires max_leaderboard_submissions=0")

    report: list[dict[str, Any]] = []
    for item in entries:
        if item.get("approved") is not True:
            report.append({"config": item.get("config"), "action": "WAITING_FOR_USER_APPROVAL"})
            continue
        _, config = load_config(root / str(item["config"]), root)
        experiment_id = str(config["experiment_id"])
        if not experiment_dir(root, experiment_id).exists():
            create_experiment(root / str(item["config"]), root=root)
        record = load_record(root, experiment_id)
        state = record["state"]
        if state in {"PROPOSED", "MANUAL_REVIEW_REQUIRED"} and record.get("review", {}).get("required"):
            action = f"NEEDS_{review_provider_label(record).upper()}_REVIEW"
        elif state in {"PROPOSED", "REVIEWED"}:
            action = "READY_FOR_SMOKE_AND_LAUNCH"
            launch(root, experiment_id)
        elif state == "READY":
            action = "LAUNCHED"
            launch(root, experiment_id)
        elif state in {"SUBMITTED", "RUNNING"}:
            checked = check_status(root, experiment_id)
            if checked.get("remote", {}).get("status") == "COMPLETE":
                collect(root, experiment_id)
                action = "COLLECTED_AND_EVALUATED"
            else:
                action = f"REMOTE_{checked.get('remote', {}).get('status', 'UNKNOWN')}"
        else:
            action = f"NO_ACTION_{state}"
        item["status"] = load_record(root, experiment_id)["state"]
        report.append({"experiment_id": experiment_id, "action": action, "state": item["status"]})
    write_json(queue_path, queue)
    return report


def watch(root: Path, poll_seconds: int, max_cycles: int | None = None) -> list[list[dict[str, Any]]]:
    if poll_seconds < 30:
        raise ControllerError("poll_seconds must be at least 30")
    history: list[list[dict[str, Any]]] = []
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        report = run_once(root)
        history.append(report)
        cycles += 1
        if all(
            item.get("action", "").startswith(("NO_ACTION_", "WAITING_", "NEEDS_"))
            for item in report
        ):
            break
        if max_cycles is None or cycles < max_cycles:
            time.sleep(poll_seconds)
    return history
