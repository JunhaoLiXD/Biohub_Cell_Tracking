"""Independently audit the completed public-0.941 motion-EMA screening run."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import load_record, verify_snapshot
from experiment_controller.public_copy import aggregate, audit_submission

EXPERIMENT = "exp_040_public_0941_motion_ema"
PARENT = "val_039_public_0941_train16"
MINIMUM_IMPROVEMENT = 0.001
ADJUSTED_EDGE_TOLERANCE = 0.002


def close(left, right):
    if not math.isclose(float(left), float(right), rel_tol=0, abs_tol=1e-12):
        raise ValueError(f"Metric mismatch: {left} != {right}")


def load_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    numeric = (
        "weight", "adjusted_edge_jaccard", "div_tp", "div_fp", "div_fn",
        "motion_relink_ema_predictions", "motion_relink_one_frame_fallbacks",
        "motion_relink_skipped_large_frame",
    )
    for row in rows:
        for key in numeric:
            row[key] = float(row.get(key, 0) or 0)
    return rows


def analyze(root=PROJECT_ROOT):
    record = load_record(root, EXPERIMENT)
    verify_snapshot(root, record)
    if record["state"] != "KEEP":
        raise ValueError("EMA experiment must be terminal KEEP before completed-run analysis")
    experiment_dir = root / "experiments" / EXPERIMENT
    artifacts = experiment_dir / "artifacts"
    parent_dir = root / "experiments" / PARENT
    metrics = json.loads((artifacts / "metrics.json").read_text(encoding="utf-8"))
    identity = json.loads((artifacts / "inference_identity.json").read_text(encoding="utf-8"))
    stages = json.loads((artifacts / "validation_stage_stats.json").read_text(encoding="utf-8"))
    parent_metrics = json.loads((parent_dir / "metrics.json").read_text(encoding="utf-8"))
    rows = load_rows(artifacts / "validator_results.csv")
    parent_rows = {row["stem"]: row for row in load_rows(parent_dir / "artifacts" / "validator_results.csv")}

    assert len(rows) == len({row["stem"] for row in rows}) == 16
    assert [row["stem"] for row in rows] == [stem for specimen in ("44b6", "6bba")
                                                 for stem in metrics["specimen_metrics"][specimen]["samples"]]
    assert set(stages) == {row["stem"] for row in rows} == set(parent_rows)
    assert all(identity["checks"].values())
    assert all(metrics["metrics"]["checks"].values())
    assert all(metrics["metrics"]["research_gates"].values())
    assert metrics["metrics"]["validation_contract_passed"] is True
    assert metrics["metrics"]["ema_candidate_gate_passed"] is True

    candidate_submission = audit_submission(artifacts / "submission.csv")
    parent_submission = audit_submission(parent_dir / "artifacts" / "submission.csv")
    assert candidate_submission["sha256"] == identity["submission_sha256"] \
        == metrics["metrics"]["candidate_submission_sha256"]
    assert candidate_submission["datasets"] == parent_submission["datasets"]

    recomputed = aggregate(rows)
    close(recomputed["primary_metric"], metrics["primary_metric"])
    close(recomputed["adjusted_edge_jaccard"], metrics["validation"]["adjusted_edge_jaccard"])
    close(recomputed["division_jaccard"], metrics["validation"]["division_jaccard"])

    specimen_results = {}
    for specimen in ("44b6", "6bba"):
        selected = [row for row in rows if row["stem"].startswith(specimen + "_")]
        current = aggregate(selected)
        reported = metrics["specimen_metrics"][specimen]
        for key in ("primary_metric", "adjusted_edge_jaccard", "division_jaccard"):
            close(current[key], reported[key])
        specimen_results[specimen] = {
            "score": current["primary_metric"],
            "score_delta": current["primary_metric"] - parent_metrics["specimen_metrics"][specimen]["primary_metric"],
            "adjusted_edge_jaccard": current["adjusted_edge_jaccard"],
            "adjusted_edge_delta": current["adjusted_edge_jaccard"]
            - parent_metrics["specimen_metrics"][specimen]["adjusted_edge_jaccard"],
            "division_jaccard": current["division_jaccard"],
            "division_delta": current["division_jaccard"]
            - parent_metrics["specimen_metrics"][specimen]["division_jaccard"],
            "division_counts": {key: int(reported["error_summary"][key]) for key in ("div_tp", "div_fp", "div_fn")},
        }

    overall_delta = metrics["primary_metric"] - parent_metrics["primary_metric"]
    adjusted_delta = metrics["validation"]["adjusted_edge_jaccard"] \
        - parent_metrics["validation"]["adjusted_edge_jaccard"]
    division_delta = metrics["validation"]["division_jaccard"] \
        - parent_metrics["validation"]["division_jaccard"]
    counts = metrics["metrics"]["division_counts"]
    independent_gates = {
        "aggregate_improvement": overall_delta >= MINIMUM_IMPROVEMENT,
        "per_specimen_adjusted_edge": all(
            item["adjusted_edge_delta"] >= -ADJUSTED_EDGE_TOLERANCE
            for item in specimen_results.values()),
        "division_counts": counts["div_tp"] >= 4 and counts["div_fp"] <= 9 and counts["div_fn"] <= 8,
        "ema_executed": all(
            sum(row["motion_relink_ema_predictions"] for row in rows if row["stem"].startswith(specimen + "_")) > 0
            for specimen in ("44b6", "6bba")),
    }
    assert all(independent_gates.values())

    video_deltas = sorted(({
        "stem": row["stem"],
        "weight": int(row["weight"]),
        "adjusted_edge_delta": row["adjusted_edge_jaccard"] - parent_rows[row["stem"]]["adjusted_edge_jaccard"],
        "division_tp_delta": int(row["div_tp"] - parent_rows[row["stem"]]["div_tp"]),
        "division_fp_delta": int(row["div_fp"] - parent_rows[row["stem"]]["div_fp"]),
        "division_fn_delta": int(row["div_fn"] - parent_rows[row["stem"]]["div_fn"]),
    } for row in rows), key=lambda item: item["adjusted_edge_delta"], reverse=True)
    ema_execution = {
        specimen: {
            "ema_predictions": int(sum(row["motion_relink_ema_predictions"] for row in rows
                                       if row["stem"].startswith(specimen + "_"))),
            "one_frame_fallbacks": int(sum(row["motion_relink_one_frame_fallbacks"] for row in rows
                                           if row["stem"].startswith(specimen + "_"))),
        }
        for specimen in ("44b6", "6bba")
    }
    assert ema_execution == {
        specimen: {key: values[key] for key in ("ema_predictions", "one_frame_fallbacks")}
        for specimen, values in metrics["metrics"]["motion_relink_ema_execution"].items()
    }

    return {
        "experiment_id": EXPERIMENT,
        "decision": record["state"],
        "audit_passed": True,
        "independent_gates": independent_gates,
        "aggregate": {
            "score": metrics["primary_metric"], "score_delta": overall_delta,
            "adjusted_edge_jaccard": metrics["validation"]["adjusted_edge_jaccard"],
            "adjusted_edge_delta": adjusted_delta,
            "division_jaccard": metrics["validation"]["division_jaccard"],
            "division_delta": division_delta,
            "score_delta_from_adjusted_edge": adjusted_delta,
            "score_delta_from_weighted_division": 0.1 * division_delta,
        },
        "specimens": specimen_results,
        "division_counts": {
            "candidate": counts,
            "parent": {"div_tp": 4, "div_fp": 9, "div_fn": 8},
        },
        "ema_execution": ema_execution,
        "submission": {
            "candidate": candidate_submission,
            "parent": parent_submission,
            "node_delta": candidate_submission["nodes"] - parent_submission["nodes"],
            "edge_delta": candidate_submission["edges"] - parent_submission["edges"],
        },
        "runtime_seconds": metrics["runtime_seconds"],
        "best_video_deltas": video_deltas[:5],
        "worst_video_deltas": list(reversed(video_deltas[-5:])),
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2, ensure_ascii=False))
