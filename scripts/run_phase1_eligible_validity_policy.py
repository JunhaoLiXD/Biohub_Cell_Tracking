"""Factorized Family-A policy with validity trained only on eligible actions."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_ID = "diag_030_train16_eligible_validity_factorized_policy"
PARENT_EXPERIMENT_ID = "diag_019_train16_final_validation_graph_export"
PROTOCOL = "public_0933_train16_eligible_validity_factorized_policy_v1"


def _eligible_validity_dataset(
    videos: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    features: list[list[float]] = []
    labels: list[int] = []
    specimens: list[str] = []
    for video in videos.values():
        for row in video["action_rows"]:
            features.append(row["features"])
            labels.append(int(row["both_endpoints_matched"]))
            specimens.append(video["specimen"])
    matrix = np.asarray(features, dtype=np.float64)
    target = np.asarray(labels, dtype=np.int64)
    domain = np.asarray(specimens)
    if not len(matrix) or target.sum() == 0:
        raise RuntimeError("No eligible validity training rows were constructed")
    return matrix, target, domain


def _eligible_factorized_direction(
    division_matrix: np.ndarray,
    division_target: np.ndarray,
    division_validity: np.ndarray,
    division_domain: np.ndarray,
    validity_matrix: np.ndarray,
    validity_target: np.ndarray,
    validity_domain: np.ndarray,
    videos: dict[str, Any],
    train_specimen: str,
    test_specimen: str,
) -> dict[str, Any]:
    validity_model = _fit_model(validity_matrix, validity_target, validity_domain, train_specimen)
    valid_mask = division_validity == 1
    division_model = _fit_model(
        division_matrix[valid_mask],
        division_target[valid_mask],
        division_domain[valid_mask],
        train_specimen,
    )
    train_actions = _factorized_best_actions(validity_model, division_model, videos, train_specimen)
    test_actions = _factorized_best_actions(validity_model, division_model, videos, test_specimen)
    thresholds = [math.inf, *sorted({row["probability"] for row in train_actions.values()}, reverse=True)]
    train_baseline = _aggregate(
        [video["baseline"] for video in videos.values() if video["specimen"] == train_specimen]
    )
    candidates = []
    for threshold in thresholds:
        score = _score_deployment_policy(videos, train_specimen, train_actions, threshold)
        candidates.append(
            {
                "threshold": None if math.isinf(threshold) else threshold,
                "score": score,
                "delta_score": score["score"] - train_baseline["score"],
            }
        )
    chosen = max(candidates, key=lambda row: (row["delta_score"], -row["score"]["selected_actions"]))
    threshold = math.inf if chosen["threshold"] is None else float(chosen["threshold"])
    test_baseline = _aggregate(
        [video["baseline"] for video in videos.values() if video["specimen"] == test_specimen]
    )
    test_score = _score_deployment_policy(videos, test_specimen, test_actions, threshold)
    return {
        "train_specimen": train_specimen,
        "test_specimen": test_specimen,
        "threshold": chosen["threshold"],
        "train_baseline": train_baseline,
        "train_policy": chosen["score"],
        "train_delta_score": chosen["delta_score"],
        "test_baseline": test_baseline,
        "test_policy": test_score,
        "test_delta_adjusted_edge_jaccard": test_score["adjusted_edge_jaccard"] - test_baseline["adjusted_edge_jaccard"],
        "test_delta_division_jaccard": test_score["division_jaccard"] - test_baseline["division_jaccard"],
        "test_delta_score": test_score["score"] - test_baseline["score"],
        "train_candidate_videos": len(train_actions),
        "test_candidate_videos": len(test_actions),
    }


def run_eligible_validity_policy_gate(
    search_root: Path = Path("/kaggle/input"),
    output_path: Path = Path("/kaggle/working/metrics.json"),
) -> dict[str, Any]:
    started = time.monotonic()
    parent_root = _find_experiment_output(search_root, PARENT_EXPERIMENT_ID)
    parent_metrics = json.loads((parent_root / "metrics.json").read_text(encoding="utf-8"))
    names = [
        name
        for specimen in ("44b6", "6bba")
        for name in parent_metrics["specimen_metrics"][specimen]["samples"]
    ]
    train_dir = _find_train_dir(search_root, names)
    matrix, division_target, validity_target, domain, videos, audit = _load_factorized_dataset(
        parent_root, train_dir, names
    )
    validity_matrix, eligible_validity_target, validity_domain = _eligible_validity_dataset(videos)
    directions = {
        "44b6_to_6bba": _eligible_factorized_direction(
            matrix,
            division_target,
            validity_target,
            domain,
            validity_matrix,
            eligible_validity_target,
            validity_domain,
            videos,
            "44b6",
            "6bba",
        ),
        "6bba_to_44b6": _eligible_factorized_direction(
            matrix,
            division_target,
            validity_target,
            domain,
            validity_matrix,
            eligible_validity_target,
            validity_domain,
            videos,
            "6bba",
            "44b6",
        ),
    }
    baseline_reproduced = all(
        _baseline_matches(
            parent_metrics,
            specimen,
            _aggregate([video["baseline"] for video in videos.values() if video["specimen"] == specimen]),
        )
        for specimen in ("44b6", "6bba")
    )
    passed = baseline_reproduced and all(
        row["test_delta_score"] > 0.0 and row["test_delta_adjusted_edge_jaccard"] >= 0.0
        for row in directions.values()
    )
    primary = min(row["test_delta_score"] for row in directions.values())
    payload = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "primary_metric": primary,
        "baseline_primary_metric": 0.0,
        "runtime_seconds": 0.0,
        "reproducible": False,
        "methodology_valid": True,
        "validation": {
            "protocol": PROTOCOL,
            "seed": 314159,
            "warning": "Train16 factorized policy with eligible-conditioned validity training.",
        },
        "specimen_metrics": {
            row["test_specimen"]: {"primary_metric": row["test_delta_score"], "baseline_primary_metric": 0.0}
            for row in directions.values()
        },
        "metrics": {
            "eligible_validity_policy_gate_passed": passed,
            "baseline_reproduced": baseline_reproduced,
            "directions": directions,
            "dataset_audit": audit,
            "validity_training_distribution": "deployable Family-A candidates only",
            "division_training_distribution": "matched candidates only",
            "gt_matching_is_not_a_model_feature": True,
            "wall_clock_seconds": time.monotonic() - started,
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_eligible_validity_policy_gate()["metrics"], indent=2, sort_keys=True))
