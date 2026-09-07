"""Independently audit the exact reproduction of the public-0.941 motion-EMA run."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import load_record, sha256_file, verify_snapshot
from experiment_controller.public_copy import aggregate, audit_submission


EXPERIMENT = "repro_041_public_0941_motion_ema"
REFERENCE = "exp_040_public_0941_motion_ema"
SPECIMENS = ("44b6", "6bba")
ABS_TOLERANCE = 1e-12


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    numeric = (
        "weight",
        "adjusted_edge_jaccard",
        "div_tp",
        "div_fp",
        "div_fn",
    )
    for row in rows:
        for key in numeric:
            row[key] = float(row.get(key, 0) or 0)
    return rows


def _close(left: object, right: object) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=ABS_TOLERANCE)


def analyze(root: Path = PROJECT_ROOT) -> dict[str, object]:
    record = load_record(root, EXPERIMENT)
    reference_record = load_record(root, REFERENCE)
    verify_snapshot(root, record)
    verify_snapshot(root, reference_record)
    if record["state"] != "KEEP" or reference_record["state"] != "KEEP":
        raise ValueError("Both the reproduction and reference must be terminal KEEP runs")

    candidate_dir = root / "experiments" / EXPERIMENT / "artifacts"
    reference_dir = root / "experiments" / REFERENCE / "artifacts"
    candidate_metrics = _load_json(candidate_dir / "metrics.json")
    reference_metrics = _load_json(reference_dir / "metrics.json")
    candidate_rows = _load_rows(candidate_dir / "validator_results.csv")
    reference_rows = _load_rows(reference_dir / "validator_results.csv")

    recomputed = aggregate(candidate_rows)
    aggregate_checks = {
        "primary_metric": _close(recomputed["primary_metric"], reference_metrics["primary_metric"]),
        "adjusted_edge_jaccard": _close(
            recomputed["adjusted_edge_jaccard"],
            reference_metrics["validation"]["adjusted_edge_jaccard"],
        ),
        "division_jaccard": _close(
            recomputed["division_jaccard"], reference_metrics["validation"]["division_jaccard"]
        ),
    }
    specimen_checks: dict[str, dict[str, bool]] = {}
    for specimen in SPECIMENS:
        selected = [row for row in candidate_rows if row["stem"].startswith(specimen + "_")]
        current = aggregate(selected)
        reference = reference_metrics["specimen_metrics"][specimen]
        specimen_checks[specimen] = {
            key: _close(current[key], reference[key])
            for key in ("primary_metric", "adjusted_edge_jaccard", "division_jaccard")
        }

    exact_file_checks = {
        name: sha256_file(candidate_dir / name) == sha256_file(reference_dir / name)
        for name in (
            "validator_results.csv",
            "inference_identity.json",
            "validation_stage_stats.json",
            "submission.csv",
        )
    }
    candidate_submission = audit_submission(candidate_dir / "submission.csv")
    reference_submission = audit_submission(reference_dir / "submission.csv")
    reproduction = candidate_metrics["metrics"]["reproduction_checks"]
    contract_checks = {
        "reported_reproduction_passed": candidate_metrics["metrics"]["reproduction_passed"] is True,
        "reported_reproducible": candidate_metrics["reproducible"] is True,
        "reported_checks_all_true": all(reproduction.values()),
        "division_counts_exact": (
            candidate_metrics["metrics"]["division_counts"]
            == reference_metrics["metrics"]["division_counts"]
        ),
        "ema_telemetry_exact": (
            candidate_metrics["metrics"]["motion_relink_ema_execution"]
            == reference_metrics["metrics"]["motion_relink_ema_execution"]
        ),
        "submission_graph_exact": candidate_submission == reference_submission,
        "sample_order_exact": [row["stem"] for row in candidate_rows]
        == [row["stem"] for row in reference_rows],
    }
    all_checks = [
        *aggregate_checks.values(),
        *(passed for checks in specimen_checks.values() for passed in checks.values()),
        *exact_file_checks.values(),
        *contract_checks.values(),
    ]
    if not all(all_checks):
        raise AssertionError("Independent reproduction audit failed; inspect the emitted check groups")

    return {
        "experiment_id": EXPERIMENT,
        "reference_experiment": REFERENCE,
        "decision": record["state"],
        "audit_passed": True,
        "absolute_tolerance": ABS_TOLERANCE,
        "aggregate": {
            "primary_metric": recomputed["primary_metric"],
            "adjusted_edge_jaccard": recomputed["adjusted_edge_jaccard"],
            "division_jaccard": recomputed["division_jaccard"],
            "checks": aggregate_checks,
        },
        "specimen_checks": specimen_checks,
        "exact_file_checks": exact_file_checks,
        "contract_checks": contract_checks,
        "division_counts": candidate_metrics["metrics"]["division_counts"],
        "ema_execution": candidate_metrics["metrics"]["motion_relink_ema_execution"],
        "submission": candidate_submission,
        "runtime_seconds": candidate_metrics["runtime_seconds"],
        "reference_runtime_seconds": reference_metrics["runtime_seconds"],
        "interpretation": (
            "Exact repeatability passed under the frozen proxy protocol; this does not establish "
            "generalization or leaderboard improvement."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2, ensure_ascii=False))
