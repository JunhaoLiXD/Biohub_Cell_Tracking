"""Factorized Family-A policy with graph and sibling-geometry features."""

from __future__ import annotations

import gzip
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_ID = "diag_031_train16_structural_factorized_policy"
PARENT_EXPERIMENT_ID = "diag_019_train16_final_validation_graph_export"
PROTOCOL = "public_0933_train16_structural_factorized_policy_v1"
STRUCTURAL_FEATURE_NAMES = (
    "source_indegree",
    "source_outdegree",
    "target_indegree",
    "target_outdegree",
    "source_component_size",
    "target_component_size",
    "source_component_duration",
    "target_component_duration",
    "source_track_age",
    "target_track_remaining",
    "same_component",
    "normalized_time",
    "has_single_existing_child",
    "existing_child_distance_um",
    "sibling_distance_um",
    "daughter_vector_cosine",
    "daughter_radius_difference_um",
    "daughter_midpoint_offset_um",
)


def _component_statistics(
    nodes: dict[int, tuple[int, float, float, float]],
    edges: set[tuple[int, int]],
) -> tuple[dict[int, int], dict[int, dict[str, int]]]:
    components = _weakly_connected_components(nodes, edges)
    grouped: dict[int, list[int]] = defaultdict(list)
    for node_id, component in components.items():
        grouped[component].append(node_id)
    statistics = {}
    for component, node_ids in grouped.items():
        times = [int(nodes[node_id][0]) for node_id in node_ids]
        statistics[component] = {
            "size": len(node_ids),
            "minimum_time": min(times),
            "maximum_time": max(times),
        }
    return components, statistics


def _structural_features(
    nodes: dict[int, tuple[int, float, float, float]],
    out_adj: dict[int, set[int]],
    in_adj: dict[int, set[int]],
    components: dict[int, int],
    component_stats: dict[int, dict[str, int]],
    source: int,
    target: int,
    scale: tuple[float, float, float],
    maximum_time: int,
) -> list[float]:
    source_component = components[source]
    target_component = components[target]
    source_stats = component_stats[source_component]
    target_stats = component_stats[target_component]
    source_time = int(nodes[source][0])
    target_time = int(nodes[target][0])
    output = [
        float(len(in_adj[source])),
        float(len(out_adj[source])),
        float(len(in_adj[target])),
        float(len(out_adj[target])),
        float(source_stats["size"]),
        float(target_stats["size"]),
        float(source_stats["maximum_time"] - source_stats["minimum_time"] + 1),
        float(target_stats["maximum_time"] - target_stats["minimum_time"] + 1),
        float(source_time - source_stats["minimum_time"]),
        float(target_stats["maximum_time"] - target_time),
        float(source_component == target_component),
        float(source_time / max(1, maximum_time)),
    ]
    children = sorted(out_adj[source])
    if len(children) != 1:
        return [*output, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    child = children[0]
    voxel_scale = np.asarray(scale, dtype=np.float64)
    source_position = np.asarray(nodes[source][1:], dtype=np.float64) * voxel_scale
    child_position = np.asarray(nodes[child][1:], dtype=np.float64) * voxel_scale
    target_position = np.asarray(nodes[target][1:], dtype=np.float64) * voxel_scale
    existing_vector = child_position - source_position
    candidate_vector = target_position - source_position
    existing_distance = float(np.linalg.norm(existing_vector))
    candidate_distance = float(np.linalg.norm(candidate_vector))
    sibling_distance = float(np.linalg.norm(target_position - child_position))
    denominator = existing_distance * candidate_distance
    cosine = float(np.dot(existing_vector, candidate_vector) / denominator) if denominator > 0 else 0.0
    midpoint_offset = float(np.linalg.norm((child_position + target_position) * 0.5 - source_position))
    return [
        *output,
        1.0,
        existing_distance,
        sibling_distance,
        cosine,
        abs(existing_distance - candidate_distance),
        midpoint_offset,
    ]


def _load_structural_dataset(
    parent_root: Path, train_dir: Path, names: list[str]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any], dict[str, Any]]:
    features: list[list[float]] = []
    division_labels: list[int] = []
    validity_labels: list[int] = []
    specimens: list[str] = []
    videos: dict[str, Any] = {}
    audit: dict[str, Any] = {}
    for name in names:
        nodes, base_edges = _load_final_graph(parent_root, name)
        dataset = open_dataset(train_dir / name, normalize=False, require_tracks=True, load_image=False)
        if dataset.tracks is None:
            raise RuntimeError(f"Ground truth was not loaded for {name}")
        gt_nodes = _node_rows(dataset.tracks)
        gt_edges = _edge_pairs(dataset.tracks)
        scale = tuple(float(value) for value in dataset.scale)
        pred_to_gt, _gt_to_pred = _match_nodes_bipartite(nodes, gt_nodes, scale)
        gt_out: dict[int, set[int]] = defaultdict(set)
        for source, target in gt_edges:
            gt_out[source].add(target)
        out_adj: dict[int, set[int]] = defaultdict(set)
        in_adj: dict[int, set[int]] = defaultdict(set)
        for source, target in base_edges:
            out_adj[source].add(target)
            in_adj[target].add(source)
        components, component_stats = _component_statistics(nodes, base_edges)
        maximum_time = max(int(row[0]) for row in nodes.values())

        action_rows: list[dict[str, Any]] = []
        seen_pairs: set[tuple[int, int]] = set()
        counts = {
            "training_union_rows": 0,
            "validity_positive": 0,
            "division_positive": 0,
            "action_eligible": 0,
            "action_validity_positive": 0,
            "action_division_positive": 0,
        }
        path = parent_root / "preilp_edge_audit" / f"{name}.jsonl.gz"
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                source = int(row["source_id"])
                target = int(row["target_id"])
                pair = (source, target)
                if pair in seen_pairs or source not in nodes or target not in nodes:
                    continue
                seen_pairs.add(pair)
                t_src = int(row["t_src"])
                t_tgt = int(row["t_tgt"])
                distance = float(row["distance_um"])
                if (
                    nodes[source][0] != t_src
                    or nodes[target][0] != t_tgt
                    or t_tgt != t_src + 1
                    or not math.isfinite(distance)
                    or distance < 0.0
                    or distance > 12.0 + 1e-6
                ):
                    continue
                matched_source = pred_to_gt.get(source)
                matched_target = pred_to_gt.get(target)
                valid = int(matched_source is not None and matched_target is not None)
                division = int(
                    valid
                    and len(gt_out.get(matched_source, ())) >= 2
                    and (matched_source, matched_target) in gt_edges
                )
                eligible = pair not in base_edges and len(out_adj[source]) == 1 and not in_adj[target]
                edge_features = [_finite_feature(row, feature) for feature in FEATURE_NAMES]
                edge_features.extend(
                    [min(edge_features[5], edge_features[6]), max(edge_features[3], edge_features[4])]
                )
                structural = _structural_features(
                    nodes,
                    out_adj,
                    in_adj,
                    components,
                    component_stats,
                    source,
                    target,
                    scale,
                    maximum_time,
                )
                feature_row = [*edge_features, *structural]
                if valid or eligible:
                    features.append(feature_row)
                    division_labels.append(division)
                    validity_labels.append(valid)
                    specimens.append(name.split("_")[0])
                    counts["training_union_rows"] += 1
                    counts["validity_positive"] += valid
                    counts["division_positive"] += division
                if eligible:
                    action_rows.append(
                        {
                            "pair": pair,
                            "features": feature_row,
                            "both_endpoints_matched": bool(valid),
                            "true_division_edge": bool(division),
                        }
                    )
                    counts["action_eligible"] += 1
                    counts["action_validity_positive"] += valid
                    counts["action_division_positive"] += division

        n_total = _n_total(train_dir / f"{name}.geff")
        baseline = _score(nodes, base_edges, dataset.tracks, scale, n_total)
        videos[name] = {
            "specimen": name.split("_")[0],
            "nodes": nodes,
            "base_edges": base_edges,
            "gt": dataset.tracks,
            "scale": scale,
            "n_total": n_total,
            "baseline": baseline,
            "action_rows": action_rows,
        }
        audit[name] = counts
    matrix = np.asarray(features, dtype=np.float64)
    division_target = np.asarray(division_labels, dtype=np.int64)
    validity_target = np.asarray(validity_labels, dtype=np.int64)
    domain = np.asarray(specimens)
    if not len(matrix) or division_target.sum() == 0 or validity_target.sum() == 0:
        raise RuntimeError("No structural factorized training rows were constructed")
    return matrix, division_target, validity_target, domain, videos, audit


def run_structural_policy_gate(
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
            "warning": "Train16 structural factorized cross-specimen action-policy gate.",
        },
        "specimen_metrics": {
            row["test_specimen"]: {"primary_metric": row["test_delta_score"], "baseline_primary_metric": 0.0}
            for row in directions.values()
        },
        "metrics": {
            "structural_policy_gate_passed": passed,
            "baseline_reproduced": baseline_reproduced,
            "directions": directions,
            "dataset_audit": audit,
            "structural_feature_names": list(STRUCTURAL_FEATURE_NAMES),
            "all_structural_features_available_at_inference": True,
            "gt_matching_is_not_a_model_feature": True,
            "wall_clock_seconds": time.monotonic() - started,
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_structural_policy_gate()["metrics"], indent=2, sort_keys=True))
