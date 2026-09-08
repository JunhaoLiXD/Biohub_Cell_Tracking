"""Independently audit the completed public-0.942 motion-EMA alpha-0.6 experiment."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import load_record, verify_snapshot
from experiment_controller.public_copy import aggregate, audit_submission

EXPERIMENT = "exp_042_public_0942_motion_ema_alpha06"
PARENT = "repro_041_public_0941_motion_ema"
VAL039 = "val_039_public_0941_train16"


def close(left, right):
    if not math.isclose(float(left), float(right), rel_tol=0, abs_tol=1e-12):
        raise ValueError(f"Metric mismatch: {left} != {right}")


def load_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    numeric = (
        "weight", "adjusted_edge_jaccard", "div_tp", "div_fp", "div_fn",
        "motion_relink_ema_predictions", "motion_relink_one_frame_fallbacks",
        "motion_relink_skipped_large_frame", "edges_fragmented",
        "edges_lost_to_detection", "edges_recovered", "spurious_pred_nodes",
    )
    for row in rows:
        for key in numeric:
            row[key] = float(row.get(key, 0) or 0)
    return rows


def analyze(root=PROJECT_ROOT):
    record = load_record(root, EXPERIMENT)
    verify_snapshot(root, record)
    if record["state"] != "REJECT":
        raise ValueError("Alpha-0.6 experiment must be terminal REJECT before completed-run analysis")
    experiment_dir = root / "experiments" / EXPERIMENT
    artifacts = experiment_dir / "artifacts"
    parent_dir = root / "experiments" / PARENT
    val039_dir = root / "experiments" / VAL039
    metrics = json.loads((artifacts / "metrics.json").read_text(encoding="utf-8"))
    identity = json.loads((artifacts / "inference_identity.json").read_text(encoding="utf-8"))
    stages = json.loads((artifacts / "validation_stage_stats.json").read_text(encoding="utf-8"))
    parent_metrics = json.loads((parent_dir / "metrics.json").read_text(encoding="utf-8"))
    rows = load_rows(artifacts / "validator_results.csv")
    parent_rows = {row["stem"]: row for row in load_rows(parent_dir / "artifacts" / "validator_results.csv")}
    val039_rows = {row["stem"]: row for row in load_rows(val039_dir / "artifacts" / "validator_results.csv")}

    assert len(rows) == len({row["stem"] for row in rows}) == 16
    assert set(stages) == {row["stem"] for row in rows} == set(parent_rows) == set(val039_rows)
    assert all(identity["checks"].values())
    assert all(metrics["metrics"]["checks"].values())
    assert metrics["metrics"]["validation_contract_passed"] is True
    assert metrics["metrics"]["alpha06_candidate_gate_passed"] is False
    expected_failed = {
        "aggregate_at_least_alpha04",
        "worst_video_delta_vs_val039_at_least_minus_0_002",
        "division_fp_at_most_8",
    }
    assert set(metrics["metrics"]["failed_research_gates"]) == expected_failed

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
        parent_reported = parent_metrics["specimen_metrics"][specimen]
        specimen_results[specimen] = {
            "score": current["primary_metric"],
            "score_delta_vs_alpha04": current["primary_metric"] - parent_reported["primary_metric"],
            "adjusted_edge_jaccard": current["adjusted_edge_jaccard"],
            "adjusted_edge_delta_vs_alpha04": current["adjusted_edge_jaccard"]
            - parent_reported["adjusted_edge_jaccard"],
            "division_jaccard": current["division_jaccard"],
            "division_delta_vs_alpha04": current["division_jaccard"]
            - parent_reported["division_jaccard"],
            "division_counts": {key: int(reported["error_summary"][key]) for key in ("div_tp", "div_fp", "div_fn")},
        }

    overall_delta = metrics["primary_metric"] - parent_metrics["primary_metric"]
    adjusted_delta = metrics["validation"]["adjusted_edge_jaccard"] \
        - parent_metrics["validation"]["adjusted_edge_jaccard"]
    division_delta = metrics["validation"]["division_jaccard"] \
        - parent_metrics["validation"]["division_jaccard"]
    video_deltas = []
    for row in rows:
        parent_row = parent_rows[row["stem"]]
        val039_row = val039_rows[row["stem"]]
        video_deltas.append({
            "stem": row["stem"],
            "adjusted_edge_delta_vs_alpha04": row["adjusted_edge_jaccard"]
            - parent_row["adjusted_edge_jaccard"],
            "adjusted_edge_delta_vs_val039": row["adjusted_edge_jaccard"]
            - val039_row["adjusted_edge_jaccard"],
            "division_tp_delta_vs_alpha04": int(row["div_tp"] - parent_row["div_tp"]),
            "division_fp_delta_vs_alpha04": int(row["div_fp"] - parent_row["div_fp"]),
            "division_fn_delta_vs_alpha04": int(row["div_fn"] - parent_row["div_fn"]),
        })
    video_deltas.sort(key=lambda item: item["adjusted_edge_delta_vs_alpha04"], reverse=True)

    val039_response = {
        "positive": sum(item["adjusted_edge_delta_vs_val039"] > 0 for item in video_deltas),
        "zero": sum(item["adjusted_edge_delta_vs_val039"] == 0 for item in video_deltas),
        "negative": sum(item["adjusted_edge_delta_vs_val039"] < 0 for item in video_deltas),
    }
    worst_vs_val039 = min(video_deltas, key=lambda item: item["adjusted_edge_delta_vs_val039"])
    counts = metrics["metrics"]["division_counts"]
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
        "failed_research_gates": sorted(expected_failed),
        "aggregate": {
            "score": metrics["primary_metric"],
            "score_delta_vs_alpha04": overall_delta,
            "adjusted_edge_jaccard": metrics["validation"]["adjusted_edge_jaccard"],
            "adjusted_edge_delta_vs_alpha04": adjusted_delta,
            "division_jaccard": metrics["validation"]["division_jaccard"],
            "division_delta_vs_alpha04": division_delta,
            "score_delta_from_adjusted_edge": adjusted_delta,
            "score_delta_from_weighted_division": 0.1 * division_delta,
        },
        "specimens": specimen_results,
        "division_counts": {
            "candidate": counts,
            "alpha04_parent": parent_metrics["metrics"]["division_counts"],
        },
        "video_response_vs_val039": {**val039_response, "worst": worst_vs_val039},
        "ema_execution": ema_execution,
        "submission": {
            "candidate": candidate_submission,
            "alpha04_parent": parent_submission,
            "node_delta": candidate_submission["nodes"] - parent_submission["nodes"],
            "edge_delta": candidate_submission["edges"] - parent_submission["edges"],
        },
        "runtime_seconds": metrics["runtime_seconds"],
        "best_video_changes_vs_alpha04": video_deltas[:5],
        "worst_video_changes_vs_alpha04": list(reversed(video_deltas[-5:])),
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2, ensure_ascii=False))
