"""Structural factorized Family-A policy with rank-count transfer."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


EXPERIMENT_ID = "diag_032_train16_structural_rank_transfer_policy"
PARENT_EXPERIMENT_ID = "diag_019_train16_final_validation_graph_export"
PROTOCOL = "public_0933_train16_structural_rank_transfer_policy_v1"


def _score_rank_policy(
    videos: dict[str, Any],
    specimen: str,
    best_actions: dict[str, dict[str, Any]],
    action_count: int,
) -> dict[str, Any]:
    ranked = sorted(
        best_actions.items(),
        key=lambda item: (-item[1]["probability"], item[0]),
    )
    selected_names = {name for name, _row in ranked[:action_count]}
    rows = []
    visible = 0
    true_division = 0
    selected_probabilities = []
    for name, video in videos.items():
        if video["specimen"] != specimen:
            continue
        edges = set(video["base_edges"])
        action = best_actions.get(name)
        if name in selected_names and action is not None:
            edges.add(action["pair"])
            visible += int(action["both_endpoints_matched"])
            true_division += int(action["true_division_edge"])
            selected_probabilities.append(float(action["probability"]))
        rows.append(_score(video["nodes"], edges, video["gt"], video["scale"], video["n_total"]))
    aggregate = _aggregate(rows)
    aggregate.update(
        {
            "selected_actions": len(selected_names),
            "selected_both_endpoints_matched": visible,
            "selected_true_division_edges": true_division,
            "selected_probability_minimum": min(selected_probabilities) if selected_probabilities else None,
            "selected_probability_maximum": max(selected_probabilities) if selected_probabilities else None,
        }
    )
    return aggregate


def _rank_transfer_direction(
    matrix,
    division_target,
    validity_target,
    domain,
    validity_matrix,
    eligible_validity_target,
    validity_domain,
    videos: dict[str, Any],
    train_specimen: str,
    test_specimen: str,
) -> dict[str, Any]:
    validity_model = _fit_model(validity_matrix, eligible_validity_target, validity_domain, train_specimen)
    valid_mask = validity_target == 1
    division_model = _fit_model(
        matrix[valid_mask], division_target[valid_mask], domain[valid_mask], train_specimen
    )
    train_actions = _factorized_best_actions(validity_model, division_model, videos, train_specimen)
    test_actions = _factorized_best_actions(validity_model, division_model, videos, test_specimen)
    train_baseline = _aggregate(
        [video["baseline"] for video in videos.values() if video["specimen"] == train_specimen]
    )
    candidates = []
    for action_count in range(len(train_actions) + 1):
        score = _score_rank_policy(videos, train_specimen, train_actions, action_count)
        candidates.append(
            {
                "action_count": action_count,
                "score": score,
                "delta_score": score["score"] - train_baseline["score"],
            }
        )
    chosen = max(candidates, key=lambda row: (row["delta_score"], -row["action_count"]))
    test_baseline = _aggregate(
        [video["baseline"] for video in videos.values() if video["specimen"] == test_specimen]
    )
    test_score = _score_rank_policy(
        videos, test_specimen, test_actions, int(chosen["action_count"])
    )
    return {
        "train_specimen": train_specimen,
        "test_specimen": test_specimen,
        "transferred_action_count": int(chosen["action_count"]),
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


def run_rank_transfer_policy_gate(
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
    matrix, division_target, validity_target, domain, videos, audit = _load_structural_dataset(
        parent_root, train_dir, names
    )
    validity_matrix, eligible_validity_target, validity_domain = _eligible_validity_dataset(videos)
    directions = {
        "44b6_to_6bba": _rank_transfer_direction(
            matrix, division_target, validity_target, domain,
            validity_matrix, eligible_validity_target, validity_domain,
            videos, "44b6", "6bba",
        ),
        "6bba_to_44b6": _rank_transfer_direction(
            matrix, division_target, validity_target, domain,
            validity_matrix, eligible_validity_target, validity_domain,
            videos, "6bba", "44b6",
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
            "warning": "Train16 structural factorized policy with train-only action-count calibration.",
        },
        "specimen_metrics": {
            row["test_specimen"]: {"primary_metric": row["test_delta_score"], "baseline_primary_metric": 0.0}
            for row in directions.values()
        },
        "metrics": {
            "rank_transfer_policy_gate_passed": passed,
            "baseline_reproduced": baseline_reproduced,
            "directions": directions,
            "dataset_audit": audit,
            "calibration": "training-optimal global action count transferred to the held-out specimen",
            "all_features_available_at_inference": True,
            "gt_matching_is_not_a_model_feature": True,
            "wall_clock_seconds": time.monotonic() - started,
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_rank_transfer_policy_gate()["metrics"], indent=2, sort_keys=True))
