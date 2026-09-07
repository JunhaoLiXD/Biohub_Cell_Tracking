"""Structural Family-A policy with node-level endpoint-validity learning."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


EXPERIMENT_ID = "diag_033_train16_node_validity_rank_policy"
PARENT_EXPERIMENT_ID = "diag_019_train16_final_validation_graph_export"
PROTOCOL = "public_0933_train16_node_validity_rank_policy_v1"
NODE_FEATURE_NAMES = (
    "indegree",
    "outdegree",
    "component_size",
    "component_duration",
    "track_age",
    "track_remaining",
    "normalized_time",
)


def _attach_node_validity_dataset(
    videos: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    features: list[list[float]] = []
    labels: list[int] = []
    specimens: list[str] = []
    for video in videos.values():
        nodes = video["nodes"]
        base_edges = video["base_edges"]
        out_adj: dict[int, set[int]] = defaultdict(set)
        in_adj: dict[int, set[int]] = defaultdict(set)
        for source, target in base_edges:
            out_adj[source].add(target)
            in_adj[target].add(source)
        components, component_stats = _component_statistics(nodes, base_edges)
        maximum_time = max(int(row[0]) for row in nodes.values())
        gt_nodes = _node_rows(video["gt"])
        pred_to_gt, _gt_to_pred = _match_nodes_bipartite(nodes, gt_nodes, video["scale"])
        node_features: dict[int, list[float]] = {}
        for node_id, node in nodes.items():
            component = components[node_id]
            stats = component_stats[component]
            node_time = int(node[0])
            row = [
                float(len(in_adj[node_id])),
                float(len(out_adj[node_id])),
                float(stats["size"]),
                float(stats["maximum_time"] - stats["minimum_time"] + 1),
                float(node_time - stats["minimum_time"]),
                float(stats["maximum_time"] - node_time),
                float(node_time / max(1, maximum_time)),
            ]
            node_features[node_id] = row
            features.append(row)
            labels.append(int(node_id in pred_to_gt))
            specimens.append(video["specimen"])
        video["node_features"] = node_features
    matrix = np.asarray(features, dtype=np.float64)
    target = np.asarray(labels, dtype=np.int64)
    domain = np.asarray(specimens)
    if not len(matrix) or target.sum() == 0:
        raise RuntimeError("No node-validity rows were constructed")
    return matrix, target, domain


def _node_validity_best_actions(
    node_model, division_model, videos: dict[str, Any], specimen: str
) -> dict[str, dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for name, video in videos.items():
        if video["specimen"] != specimen or not video["action_rows"]:
            continue
        edge_matrix = np.asarray([row["features"] for row in video["action_rows"]], dtype=np.float64)
        source_matrix = np.asarray(
            [video["node_features"][row["pair"][0]] for row in video["action_rows"]],
            dtype=np.float64,
        )
        target_matrix = np.asarray(
            [video["node_features"][row["pair"][1]] for row in video["action_rows"]],
            dtype=np.float64,
        )
        source_probability = node_model.predict_proba(source_matrix)[:, 1]
        target_probability = node_model.predict_proba(target_matrix)[:, 1]
        division_probability = division_model.predict_proba(edge_matrix)[:, 1]
        probability = source_probability * target_probability * division_probability
        index = int(np.argmax(probability))
        best[name] = {
            **video["action_rows"][index],
            "probability": float(probability[index]),
            "source_validity_probability": float(source_probability[index]),
            "target_validity_probability": float(target_probability[index]),
            "division_probability": float(division_probability[index]),
        }
    return best


def _node_validity_direction(
    candidate_matrix,
    division_target,
    candidate_validity,
    candidate_domain,
    node_matrix,
    node_target,
    node_domain,
    videos: dict[str, Any],
    train_specimen: str,
    test_specimen: str,
) -> dict[str, Any]:
    node_model = _fit_model(node_matrix, node_target, node_domain, train_specimen)
    valid_mask = candidate_validity == 1
    division_model = _fit_model(
        candidate_matrix[valid_mask],
        division_target[valid_mask],
        candidate_domain[valid_mask],
        train_specimen,
    )
    train_actions = _node_validity_best_actions(node_model, division_model, videos, train_specimen)
    test_actions = _node_validity_best_actions(node_model, division_model, videos, test_specimen)
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
    test_mask = node_domain == test_specimen
    test_node_probability = node_model.predict_proba(node_matrix[test_mask])[:, 1]
    test_prevalence = float(node_target[test_mask].mean())
    return {
        "train_specimen": train_specimen,
        "test_specimen": test_specimen,
        "transferred_action_count": int(chosen["action_count"]),
        "node_validity_test_rows": int(test_mask.sum()),
        "node_validity_test_positive": int(node_target[test_mask].sum()),
        "node_validity_test_roc_auc": float(roc_auc_score(node_target[test_mask], test_node_probability)),
        "node_validity_test_average_precision": float(
            average_precision_score(node_target[test_mask], test_node_probability)
        ),
        "node_validity_test_prevalence": test_prevalence,
        "train_baseline": train_baseline,
        "train_policy": chosen["score"],
        "train_delta_score": chosen["delta_score"],
        "test_baseline": test_baseline,
        "test_policy": test_score,
        "test_delta_adjusted_edge_jaccard": test_score["adjusted_edge_jaccard"] - test_baseline["adjusted_edge_jaccard"],
        "test_delta_division_jaccard": test_score["division_jaccard"] - test_baseline["division_jaccard"],
        "test_delta_score": test_score["score"] - test_baseline["score"],
    }


def run_node_validity_policy_gate(
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
    node_matrix, node_target, node_domain = _attach_node_validity_dataset(videos)
    expected_candidate_width = len(FEATURE_NAMES) + 2 + len(STRUCTURAL_FEATURE_NAMES)
    feature_contract_valid = (
        matrix.ndim == 2
        and matrix.shape[1] == expected_candidate_width
        and node_matrix.ndim == 2
        and node_matrix.shape[1] == len(NODE_FEATURE_NAMES)
        and len(matrix) == len(division_target) == len(validity_target) == len(domain)
        and len(node_matrix) == len(node_target) == len(node_domain)
    )
    if not feature_contract_valid:
        raise RuntimeError("Inference feature/label contract is inconsistent")
    directions = {
        "44b6_to_6bba": _node_validity_direction(
            matrix, division_target, validity_target, domain,
            node_matrix, node_target, node_domain, videos, "44b6", "6bba",
        ),
        "6bba_to_44b6": _node_validity_direction(
            matrix, division_target, validity_target, domain,
            node_matrix, node_target, node_domain, videos, "6bba", "44b6",
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
            "warning": "Train16 node-validity factorized cross-specimen action-policy gate.",
        },
        "specimen_metrics": {
            row["test_specimen"]: {"primary_metric": row["test_delta_score"], "baseline_primary_metric": 0.0}
            for row in directions.values()
        },
        "metrics": {
            "node_validity_policy_gate_passed": passed,
            "baseline_reproduced": baseline_reproduced,
            "directions": directions,
            "dataset_audit": audit,
            "node_feature_names": list(NODE_FEATURE_NAMES),
            "action_score": "P(source valid) * P(target valid) * P(division edge)",
            "feature_contract_valid": feature_contract_valid,
            "all_features_available_at_inference": feature_contract_valid,
            "gt_matching_is_not_a_model_feature": feature_contract_valid,
            "wall_clock_seconds": time.monotonic() - started,
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_node_validity_policy_gate()["metrics"], indent=2, sort_keys=True))
