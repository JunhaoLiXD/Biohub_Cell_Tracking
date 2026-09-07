"""Candidate-constrained Phase-0 division oracle for the fixed train16 validator.

This module is intended to run in a Kaggle notebook with the competition data,
the tracking support pack and the same-run candidate, pre-ILP graph, and final
validation graph outputs of diag_019. It never trains a model and never uses
test labels. All decisions are made on the frozen 16-video train-derived
validation set recorded by diag_019.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import polars as pl
import tracksdata as td
from geff import GeffMetadata
from scipy.optimize import linear_sum_assignment

from biohub_tracking.io import open_dataset
from biohub_tracking.metrics import evaluate as compute_metric
from biohub_tracking.metrics import node_recall, per_sample_metrics


EXPERIMENT_ID = "diag_025_train16_frozen_scorer_candidate_oracle"
FINAL_GRAPH_EXPERIMENT_ID = "diag_019_train16_final_validation_graph_export"
PROTOCOL = "public_0933_train16_candidate_oracle_v1"
DIVISION_WEIGHT = 0.1
MAX_MATCH_DISTANCE_UM = 7.0
BASELINE_ABS_TOL = 1e-10
EXPECTED_RETAINED_TIME_MISMATCH_ROWS = 17
K = td.DEFAULT_ATTR_KEYS


@dataclass(frozen=True)
class Action:
    mother_gt_id: int
    adds: frozenset[tuple[int, int]]
    removes: frozenset[tuple[int, int]]


def _find_experiment_output(search_root: Path, experiment_id: str) -> Path:
    candidates: list[Path] = []
    for path in search_root.rglob("metrics.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if payload.get("experiment_id") == experiment_id:
            candidates.append(path.parent)
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected exactly one attached {experiment_id} output, found {candidates}"
        )
    return candidates[0]


def _find_train_dir(search_root: Path, required_names: Iterable[str]) -> Path:
    names = tuple(required_names)
    candidates: set[Path] = set()
    for first in search_root.rglob(f"{names[0]}.geff"):
        candidates.add(first.parent)
    valid = [
        path
        for path in candidates
        if all((path / f"{name}.geff").exists() and (path / f"{name}.zarr").exists() for name in names)
    ]
    if len(valid) != 1:
        raise RuntimeError(f"Expected one competition train directory for all validator names, found {valid}")
    return valid[0]


def _load_graph(path: Path) -> td.graph.BaseGraph:
    loaded = td.graph.IndexedRXGraph.from_geff(path)
    return loaded[0] if isinstance(loaded, tuple) else loaded


def _node_rows(graph: td.graph.BaseGraph) -> dict[int, tuple[int, float, float, float]]:
    attrs = graph.node_attrs(attr_keys=[K.NODE_ID, K.T, K.Z, K.Y, K.X])
    return {
        int(row[K.NODE_ID]): (
            int(row[K.T]),
            float(row[K.Z]),
            float(row[K.Y]),
            float(row[K.X]),
        )
        for row in attrs.iter_rows(named=True)
    }


def _edge_pairs(graph: td.graph.BaseGraph) -> set[tuple[int, int]]:
    if graph.num_edges() == 0:
        return set()
    attrs = graph.edge_attrs(attr_keys=[K.EDGE_SOURCE, K.EDGE_TARGET])
    return {
        (int(row[K.EDGE_SOURCE]), int(row[K.EDGE_TARGET]))
        for row in attrs.iter_rows(named=True)
    }


def _load_final_graph(root: Path, name: str) -> tuple[
    dict[int, tuple[int, float, float, float]], set[tuple[int, int]]
]:
    graph_path = root / "final_validation_graphs" / f"{name}.json.gz"
    summary_path = root / "final_validation_graph_summary.jsonl"
    if not graph_path.is_file() or not summary_path.is_file():
        raise RuntimeError(f"Missing diag_019 final graph artifact for {name}")
    summaries = [json.loads(line) for line in summary_path.read_text(encoding="utf-8").splitlines() if line]
    matches = [row for row in summaries if row.get("dataset") == name]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one diag_019 final graph summary for {name}, found {len(matches)}")
    summary = matches[0]
    digest = hashlib.sha256(graph_path.read_bytes()).hexdigest()
    if digest != summary.get("sha256"):
        raise RuntimeError(f"Final graph hash mismatch for {name}")
    with gzip.open(graph_path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    expected_stage = "post_filter_output_graph_pre_validator_scoring"
    if payload.get("dataset") != name or payload.get("stage") != expected_stage:
        raise RuntimeError(f"Final graph identity or stage mismatch for {name}")
    nodes = {
        int(node_id): (int(t), float(z), float(y), float(x))
        for node_id, t, z, y, x in payload.get("nodes", [])
    }
    edges = {(int(source), int(target)) for source, target in payload.get("edges", [])}
    if not nodes or not edges:
        raise RuntimeError(f"Final graph is empty for {name}")
    if len(nodes) != int(summary.get("nodes", -1)) or len(edges) != int(summary.get("edges", -1)):
        raise RuntimeError(f"Final graph count mismatch for {name}")
    if any(source not in nodes or target not in nodes for source, target in edges):
        raise RuntimeError(f"Final graph contains an unknown endpoint for {name}")
    return nodes, edges


def _gt_children(graph: td.graph.BaseGraph) -> dict[int, list[int]]:
    children: dict[int, list[int]] = defaultdict(list)
    for source, target in _edge_pairs(graph):
        children[source].append(target)
    for values in children.values():
        values.sort()
    return children


def _make_graph(
    nodes: dict[int, tuple[int, float, float, float]],
    edges: set[tuple[int, int]],
    scale: tuple[float, float, float],
) -> tuple[td.graph.BaseGraph, dict[int, int]]:
    graph = td.graph.InMemoryGraph()
    for key in ("z", "y", "x"):
        graph.add_node_attr_key(key, pl.Float64, -999999.0)
    original_ids = sorted(nodes)
    new_ids = graph.bulk_add_nodes(
        [
            {"t": nodes[node_id][0], "z": nodes[node_id][1], "y": nodes[node_id][2], "x": nodes[node_id][3]}
            for node_id in original_ids
        ]
    )
    id_map = {old: int(new) for old, new in zip(original_ids, new_ids)}
    if edges:
        graph.add_edge_attr_key("edge_prob", pl.Float64, 0.0)
        graph.add_edge_attr_key("edge_dist", pl.Float64, 0.0)
        scale_arr = np.asarray(scale, dtype=np.float64)
        payload = []
        for source, target in sorted(edges):
            source_pos = np.asarray(nodes[source][1:], dtype=np.float64)
            target_pos = np.asarray(nodes[target][1:], dtype=np.float64)
            payload.append(
                {
                    "source_id": id_map[source],
                    "target_id": id_map[target],
                    "edge_prob": 1.0,
                    "edge_dist": float(np.linalg.norm((source_pos - target_pos) * scale_arr)),
                }
            )
        graph.bulk_add_edges(payload)
    return graph, id_map


def _n_total(gt_path: Path) -> float:
    metadata = GeffMetadata.read(gt_path)
    value = (metadata.extra or {}).get("estimated_number_of_nodes")
    if value is None:
        raise RuntimeError(f"Missing estimated_number_of_nodes in {gt_path}")
    return float(value)


def _match_nodes_bipartite(
    pred_nodes: dict[int, tuple[int, float, float, float]],
    gt_nodes: dict[int, tuple[int, float, float, float]],
    scale: tuple[float, float, float],
) -> tuple[dict[int, int], dict[int, int]]:
    pred_by_t: dict[int, list[int]] = defaultdict(list)
    gt_by_t: dict[int, list[int]] = defaultdict(list)
    for node_id, (t, *_position) in pred_nodes.items():
        pred_by_t[int(t)].append(node_id)
    for node_id, (t, *_position) in gt_nodes.items():
        gt_by_t[int(t)].append(node_id)
    pred_to_gt: dict[int, int] = {}
    gt_to_pred: dict[int, int] = {}
    voxel_scale = np.asarray(scale, dtype=np.float64)
    for t, pred_ids in pred_by_t.items():
        gt_ids = gt_by_t.get(t, [])
        if not gt_ids:
            continue
        pred_positions = np.asarray([pred_nodes[node_id][1:] for node_id in pred_ids]) * voxel_scale
        gt_positions = np.asarray([gt_nodes[node_id][1:] for node_id in gt_ids]) * voxel_scale
        distance = np.sqrt(((pred_positions[:, None, :] - gt_positions[None, :, :]) ** 2).sum(axis=-1))
        gated = np.where(distance <= MAX_MATCH_DISTANCE_UM, distance, 1e6)
        row_indices, column_indices = linear_sum_assignment(gated)
        for row, column in zip(row_indices, column_indices):
            if gated[row, column] >= 1e6:
                continue
            pred_to_gt[pred_ids[row]] = gt_ids[column]
            gt_to_pred[gt_ids[column]] = pred_ids[row]
    return pred_to_gt, gt_to_pred


def _edge_confusion(
    pred_edges: set[tuple[int, int]],
    gt_edges: set[tuple[int, int]],
    pred_to_gt: dict[int, int],
) -> tuple[int, int, int]:
    gt_outgoing: dict[int, set[int]] = defaultdict(set)
    gt_incoming_source: dict[int, int] = {}
    for source, target in gt_edges:
        gt_outgoing[source].add(target)
        gt_incoming_source[target] = source
    tp = 0
    fp = 0
    matched_gt_edges: set[tuple[int, int]] = set()
    for source, target in pred_edges:
        matched_source = pred_to_gt.get(source)
        matched_target = pred_to_gt.get(target)
        if (
            matched_source is not None
            and matched_target is not None
            and matched_target in gt_outgoing.get(matched_source, ())
        ):
            tp += 1
            matched_gt_edges.add((matched_source, matched_target))
        elif (
            matched_target is not None and matched_target in gt_incoming_source
        ) or (matched_source is not None and bool(gt_outgoing.get(matched_source))):
            fp += 1
    return tp, fp, len(gt_edges - matched_gt_edges)


def _weakly_connected_components(
    node_ids: Iterable[int], edges: set[tuple[int, int]]
) -> dict[int, int]:
    parent = {node_id: node_id for node_id in node_ids}

    def find(node_id: int) -> int:
        while parent[node_id] != node_id:
            parent[node_id] = parent[parent[node_id]]
            node_id = parent[node_id]
        return node_id

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[left_root] = right_root

    for source, target in edges:
        if source in parent and target in parent:
            union(source, target)
    return {node_id: find(node_id) for node_id in parent}


def _division_confusion(
    pred_nodes: dict[int, tuple[int, float, float, float]],
    pred_edges: set[tuple[int, int]],
    gt_edges: set[tuple[int, int]],
    pred_to_gt: dict[int, int],
    gt_to_pred: dict[int, int],
) -> tuple[int, int, int]:
    gt_out: dict[int, set[int]] = defaultdict(set)
    gt_in: dict[int, int] = {}
    pred_out: dict[int, set[int]] = defaultdict(set)
    for source, target in gt_edges:
        gt_out[source].add(target)
        gt_in[target] = source
    for source, target in pred_edges:
        pred_out[source].add(target)
    components = _weakly_connected_components(pred_nodes, pred_edges)
    fork_components = {
        components[node_id]
        for node_id, targets in pred_out.items()
        if len(targets) >= 2 and node_id in components
    }
    gt_division_sources = [source for source, targets in gt_out.items() if len(targets) >= 2]

    def lineage_descendants(root_child: int) -> set[int]:
        seen = {root_child}
        stack = [root_child]
        while stack:
            current = stack.pop()
            for target in gt_out.get(current, ()):
                if target not in seen:
                    seen.add(target)
                    stack.append(target)
        return seen

    tp = 0
    fn = 0
    tp_gt_sources: set[int] = set()
    for gt_source in gt_division_sources:
        children = sorted(gt_out[gt_source])
        if len(children) < 2:
            continue
        anchors = [gt_source]
        if gt_source in gt_in:
            anchors.append(gt_in[gt_source])
        anchor_pred_nodes = [gt_to_pred[anchor] for anchor in anchors if anchor in gt_to_pred]
        lineage_hit_components: list[set[int]] = []
        valid = True
        for child in children[:2]:
            lineage = lineage_descendants(child)
            hit_components = {
                components[pred_id]
                for gt_id in lineage
                if (pred_id := gt_to_pred.get(gt_id)) is not None and pred_id in components
            }
            if not hit_components:
                valid = False
                break
            lineage_hit_components.append(hit_components)
        if not valid or not anchor_pred_nodes:
            fn += 1
            continue
        anchor_components = {components[pred_id] for pred_id in anchor_pred_nodes if pred_id in components}
        if not anchor_components:
            fn += 1
            continue
        found = any(
            component in lineage_hit_components[0]
            and component in lineage_hit_components[1]
            and component in fork_components
            for component in anchor_components
        )
        if found:
            tp += 1
            tp_gt_sources.add(gt_source)
        else:
            fn += 1
    fp = 0
    for node_id, targets in pred_out.items():
        if len(targets) < 2:
            continue
        matched_gt = pred_to_gt.get(node_id)
        if matched_gt is None or matched_gt not in gt_out or matched_gt in tp_gt_sources:
            continue
        fp += 1
    return tp, fp, fn


def _score(
    nodes: dict[int, tuple[int, float, float, float]],
    edges: set[tuple[int, int]],
    gt_graph: td.graph.BaseGraph,
    scale: tuple[float, float, float],
    n_total: float,
    *,
    return_matching: bool = False,
) -> dict[str, Any]:
    gt_nodes = _node_rows(gt_graph)
    gt_edges = _edge_pairs(gt_graph)
    pred_to_gt, gt_to_pred = _match_nodes_bipartite(nodes, gt_nodes, scale)
    edge_tp, edge_fp, edge_fn = _edge_confusion(edges, gt_edges, pred_to_gt)
    edge_denom = edge_tp + edge_fp + edge_fn
    edge_jaccard = edge_tp / edge_denom if edge_denom else 0.0
    adjusted = max(0.0, edge_jaccard * (1.0 - 0.1 * (len(nodes) - n_total) / n_total))
    division_tp, division_fp, division_fn = _division_confusion(
        nodes, edges, gt_edges, pred_to_gt, gt_to_pred
    )
    division_denom = division_tp + division_fp + division_fn
    division_jaccard = division_tp / division_denom if division_denom else 0.0
    output: dict[str, Any] = {
        "adjusted_edge_jaccard": float(adjusted),
        "division_jaccard": float(division_jaccard),
        "score": float(adjusted + DIVISION_WEIGHT * division_jaccard),
        "edge_tp": edge_tp,
        "edge_fp": edge_fp,
        "edge_fn": edge_fn,
        "division_tp": division_tp,
        "division_fp": division_fp,
        "division_fn": division_fn,
        "edge_weight": edge_denom,
    }
    if return_matching:
        output["gt_to_pred"] = gt_to_pred
    return output


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    total_weight = sum(int(row["edge_weight"]) for row in rows) or 1
    adjusted = sum(float(row["adjusted_edge_jaccard"]) * int(row["edge_weight"]) for row in rows) / total_weight
    division_tp = sum(int(row["division_tp"]) for row in rows)
    division_fp = sum(int(row["division_fp"]) for row in rows)
    division_fn = sum(int(row["division_fn"]) for row in rows)
    division_denom = division_tp + division_fp + division_fn
    division = division_tp / division_denom if division_denom else 0.0
    return {
        "adjusted_edge_jaccard": adjusted,
        "division_jaccard": division,
        "score": adjusted + DIVISION_WEIGHT * division,
        "division_tp": division_tp,
        "division_fp": division_fp,
        "division_fn": division_fn,
        "edge_weight": total_weight,
    }


def _load_relevant_candidates(
    path: Path,
    wanted: set[tuple[int, int]],
    final_nodes: dict[int, tuple[int, float, float, float]],
) -> tuple[dict[tuple[int, int], dict[str, Any]], dict[str, int]]:
    found: dict[tuple[int, int], dict[str, Any]] = {}
    audit = {
        "total_rows": 0,
        "retained_endpoint_rows": 0,
        "pruned_endpoint_rows": 0,
        "time_mismatch_rows": 0,
        "invalid_distance_rows": 0,
    }
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            pair = (int(row["source_id"]), int(row["target_id"]))
            audit["total_rows"] += 1
            if pair[0] not in final_nodes or pair[1] not in final_nodes:
                audit["pruned_endpoint_rows"] += 1
                continue
            audit["retained_endpoint_rows"] += 1
            time_mismatch = (
                int(row["t_src"]) != final_nodes[pair[0]][0]
                or int(row["t_tgt"]) != final_nodes[pair[1]][0]
                or int(row["t_tgt"]) != int(row["t_src"]) + 1
            )
            audit["time_mismatch_rows"] += int(time_mismatch)
            distance_um = float(row["distance_um"])
            if not math.isfinite(distance_um) or distance_um < 0.0 or distance_um > 12.0 + 1e-6:
                audit["invalid_distance_rows"] += 1
            if time_mismatch:
                continue
            if pair in wanted:
                found[pair] = row
    return found, audit


def _select_nonconflicting(actions: list[Action]) -> tuple[list[Action], int]:
    selected: list[Action] = []
    claimed_mothers: set[int] = set()
    claimed_targets: dict[int, int] = {}
    selected_adds: set[tuple[int, int]] = set()
    selected_removes: set[tuple[int, int]] = set()
    conflicts = 0
    for action in sorted(actions, key=lambda item: item.mother_gt_id):
        conflict = action.mother_gt_id in claimed_mothers
        for source, target in action.adds:
            conflict |= target in claimed_targets and claimed_targets[target] != source
        conflict |= bool(action.adds & selected_removes)
        conflict |= bool(action.removes & selected_adds)
        if conflict:
            conflicts += 1
            continue
        selected.append(action)
        claimed_mothers.add(action.mother_gt_id)
        for source, target in action.adds:
            claimed_targets[target] = source
        selected_adds.update(action.adds)
        selected_removes.update(action.removes)
    return selected, conflicts


def _family_actions(
    family: str,
    gt_divisions: list[int],
    children: dict[int, list[int]],
    gt_to_pred: dict[int, int],
    base_edges: set[tuple[int, int]],
    candidate_rows: dict[tuple[int, int], dict[str, Any]],
) -> tuple[list[Action], dict[str, int]]:
    out_adj: dict[int, set[int]] = defaultdict(set)
    in_adj: dict[int, set[int]] = defaultdict(set)
    for source, target in base_edges:
        out_adj[source].add(target)
        in_adj[target].add(source)
    actions: list[Action] = []
    stats = {"gt_divisions": len(gt_divisions), "detectable": 0, "applicable": 0, "candidate_covered": 0}
    for mother_gt in gt_divisions:
        daughters_gt = children[mother_gt]
        if len(daughters_gt) != 2:
            continue
        required_gt = [mother_gt, *daughters_gt]
        if any(node_id not in gt_to_pred for node_id in required_gt):
            continue
        stats["detectable"] += 1
        mother = gt_to_pred[mother_gt]
        daughters = {gt_to_pred[node_id] for node_id in daughters_gt}
        linked_true = daughters & out_adj[mother]
        adds: set[tuple[int, int]] = set()
        removes: set[tuple[int, int]] = set()
        if family in {"A", "AB"}:
            if len(out_adj[mother]) != 1 or len(linked_true) != 1:
                continue
            missing = next(iter(daughters - linked_true))
            if family == "A" and in_adj[missing]:
                continue
            adds.add((mother, missing))
            if family == "AB":
                removes.update((source, missing) for source in in_adj[missing] if source != mother)
        elif family == "ABC":
            missing_daughters = daughters - linked_true
            wrong_children = out_adj[mother] - daughters
            if not missing_daughters and not wrong_children:
                continue
            adds.update((mother, daughter) for daughter in missing_daughters)
            removes.update((mother, child) for child in wrong_children)
            for daughter in daughters:
                removes.update((source, daughter) for source in in_adj[daughter] if source != mother)
        else:
            raise ValueError(f"Unknown family: {family}")
        stats["applicable"] += 1
        if any(pair not in candidate_rows for pair in adds):
            continue
        stats["candidate_covered"] += 1
        actions.append(Action(mother_gt, frozenset(adds), frozenset(removes)))
    return actions, stats


def _apply_actions(base_edges: set[tuple[int, int]], actions: list[Action]) -> set[tuple[int, int]]:
    removes = set().union(*(action.removes for action in actions)) if actions else set()
    adds = set().union(*(action.adds for action in actions)) if actions else set()
    return (base_edges - removes) | adds


def _baseline_matches(parent_metrics: dict[str, Any], specimen: str, aggregate: dict[str, Any]) -> bool:
    expected = parent_metrics["specimen_metrics"][specimen]
    return math.isclose(
        float(aggregate["adjusted_edge_jaccard"]),
        float(expected["adjusted_edge_jaccard"]),
        rel_tol=0.0,
        abs_tol=BASELINE_ABS_TOL,
    ) and math.isclose(
        float(aggregate["division_jaccard"]),
        float(expected["division_jaccard"]),
        rel_tol=0.0,
        abs_tol=BASELINE_ABS_TOL,
    )


def run(search_root: Path = Path("/kaggle/input"), output_path: Path = Path("/kaggle/working/metrics.json")) -> dict[str, Any]:
    started = time.monotonic()
    parent_root = _find_experiment_output(search_root, FINAL_GRAPH_EXPERIMENT_ID)
    final_graph_root = parent_root
    parent_metrics = json.loads((parent_root / "metrics.json").read_text(encoding="utf-8"))
    required_parent_keys = {"primary_metric", "specimen_metrics"}
    if not required_parent_keys.issubset(parent_metrics):
        raise RuntimeError(f"Parent metrics schema is missing {sorted(required_parent_keys - set(parent_metrics))}")
    for specimen in ("44b6", "6bba"):
        required_specimen_keys = {"adjusted_edge_jaccard", "division_jaccard", "samples"}
        available = set(parent_metrics.get("specimen_metrics", {}).get(specimen, {}))
        if not required_specimen_keys.issubset(available):
            raise RuntimeError(
                f"Parent metrics schema for {specimen} is missing "
                f"{sorted(required_specimen_keys - available)}"
            )
    validation_names = [
        name
        for specimen in ("44b6", "6bba")
        for name in parent_metrics["specimen_metrics"][specimen]["samples"]
    ]
    train_dir = _find_train_dir(search_root, validation_names)
    candidate_dir = parent_root / "preilp_edge_audit"
    if not candidate_dir.is_dir():
        raise RuntimeError("diag_019 same-run candidate export directory is missing")

    per_video: dict[str, dict[str, Any]] = {}
    for name in validation_names:
        dataset = open_dataset(train_dir / name, normalize=False, require_tracks=True, load_image=False)
        gt = dataset.tracks
        if gt is None:
            raise RuntimeError(f"Ground truth was not loaded for {name}")
        nodes, base_edges = _load_final_graph(final_graph_root, name)
        baseline = _score(nodes, base_edges, gt, dataset.scale, _n_total(train_dir / f"{name}.geff"), return_matching=True)
        children = _gt_children(gt)
        gt_divisions = sorted(node_id for node_id, values in children.items() if len(values) == 2)
        wanted = {
            (baseline["gt_to_pred"][mother], baseline["gt_to_pred"][daughter])
            for mother in gt_divisions
            for daughter in children[mother]
            if mother in baseline["gt_to_pred"] and daughter in baseline["gt_to_pred"]
        }
        candidate_path = candidate_dir / f"{name}.jsonl.gz"
        if not candidate_path.is_file():
            raise RuntimeError(f"Missing candidate export for {name}: {candidate_path}")
        candidates, candidate_audit = _load_relevant_candidates(
            candidate_path,
            wanted,
            nodes,
        )
        if candidate_audit["total_rows"] == 0:
            raise RuntimeError(f"Candidate export is empty for {name}")
        if candidate_audit["retained_endpoint_rows"] == 0:
            raise RuntimeError(
                f"Candidate/prediction node-id spaces have no retained overlap for {name}"
            )
        if candidate_audit["invalid_distance_rows"]:
            raise RuntimeError(
                f"Candidate/final-graph retained node-id mapping failed metadata checks for {name}: "
                f"time_mismatches={candidate_audit['time_mismatch_rows']}, "
                f"invalid_distances={candidate_audit['invalid_distance_rows']}"
            )
        per_video[name] = {
            "specimen": name.split("_")[0],
            "nodes": nodes,
            "base_edges": base_edges,
            "gt": gt,
            "scale": tuple(float(value) for value in dataset.scale),
            "n_total": _n_total(train_dir / f"{name}.geff"),
            "baseline": baseline,
            "children": children,
            "gt_divisions": gt_divisions,
            "candidates": candidates,
            "candidate_audit": candidate_audit,
            "relevant_candidate_count": len(candidates),
        }

    total_time_mismatch_rows = sum(
        video["candidate_audit"]["time_mismatch_rows"] for video in per_video.values()
    )
    if total_time_mismatch_rows != EXPECTED_RETAINED_TIME_MISMATCH_ROWS:
        raise RuntimeError(
            "Frozen diag_019 retained candidate identity-collision count changed: "
            f"expected={EXPECTED_RETAINED_TIME_MISMATCH_ROWS}, actual={total_time_mismatch_rows}"
        )

    total_relevant_candidates = sum(video["relevant_candidate_count"] for video in per_video.values())
    if total_relevant_candidates == 0:
        raise RuntimeError(
            "No GT-relevant candidate pair was found despite valid candidate endpoint ids; "
            "refusing to interpret this as zero oracle headroom"
        )

    baseline_by_specimen = {
        specimen: _aggregate([v["baseline"] for v in per_video.values() if v["specimen"] == specimen])
        for specimen in ("44b6", "6bba")
    }
    baseline_reproduced = all(
        _baseline_matches(parent_metrics, specimen, baseline_by_specimen[specimen])
        for specimen in baseline_by_specimen
    )

    family_results: dict[str, Any] = {}
    for family in ("A", "AB", "ABC"):
        scored_rows: dict[str, dict[str, Any]] = {}
        video_stats: dict[str, dict[str, int]] = {}
        for name, video in per_video.items():
            actions, stats = _family_actions(
                family,
                video["gt_divisions"],
                video["children"],
                video["baseline"]["gt_to_pred"],
                video["base_edges"],
                video["candidates"],
            )
            selected, conflicts = _select_nonconflicting(actions)
            edited_edges = _apply_actions(video["base_edges"], selected)
            score = _score(video["nodes"], edited_edges, video["gt"], video["scale"], video["n_total"])
            stats.update(
                {
                    "selected_actions": len(selected),
                    "conflicts_rejected": conflicts,
                    "adds": sum(len(action.adds) for action in selected),
                    "removes": sum(len(action.removes) for action in selected),
                }
            )
            scored_rows[name] = score
            video_stats[name] = stats
        specimen_payload: dict[str, Any] = {}
        for specimen in ("44b6", "6bba"):
            names = [name for name, video in per_video.items() if video["specimen"] == specimen]
            oracle = _aggregate([scored_rows[name] for name in names])
            baseline = baseline_by_specimen[specimen]
            counts = {
                key: sum(video_stats[name][key] for name in names)
                for key in (
                    "gt_divisions",
                    "detectable",
                    "applicable",
                    "candidate_covered",
                    "selected_actions",
                    "conflicts_rejected",
                    "adds",
                    "removes",
                )
            }
            specimen_payload[specimen] = {
                "baseline": baseline,
                "oracle": oracle,
                "delta_adjusted_edge_jaccard": oracle["adjusted_edge_jaccard"] - baseline["adjusted_edge_jaccard"],
                "delta_division_jaccard": oracle["division_jaccard"] - baseline["division_jaccard"],
                "delta_score": oracle["score"] - baseline["score"],
                **counts,
            }
        family_results[family] = {"specimens": specimen_payload, "videos": video_stats}

    abc_positive_both = all(
        family_results["ABC"]["specimens"][specimen]["delta_score"] > 0.0
        for specimen in ("44b6", "6bba")
    )
    a_positive_both = all(
        family_results["A"]["specimens"][specimen]["delta_score"] > 0.0
        for specimen in ("44b6", "6bba")
    )
    gate_passed = baseline_reproduced and abc_positive_both
    primary = min(
        family_results["ABC"]["specimens"][specimen]["delta_score"]
        for specimen in ("44b6", "6bba")
    )
    payload = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "primary_metric": primary,
        "baseline_primary_metric": float(parent_metrics["primary_metric"]),
        "runtime_seconds": 0.0,
        "reproducible": False,
        "methodology_valid": True,
        "validation": {
            "protocol": PROTOCOL,
            "seed": "public_0933_train16_v1",
            "warning": "Train-derived proxy with frozen feature extractors; use paired deltas and cross-specimen consistency only.",
        },
        "specimen_metrics": {
            specimen: {
                "primary_metric": family_results["ABC"]["specimens"][specimen]["delta_score"],
                "baseline_primary_metric": 0.0,
            }
            for specimen in ("44b6", "6bba")
        },
        "metrics": {
            "oracle_gate_passed": gate_passed,
            "baseline_reproduced": baseline_reproduced,
            "family_a_positive_both_specimens": a_positive_both,
            "family_abc_positive_both_specimens": abc_positive_both,
            "baseline_by_specimen": baseline_by_specimen,
            "families": family_results,
            "candidate_constraint": "diag_019 same-run top-4-per-source-or-target union within 12 um",
            "graph_source": "diag_019 post_filter_output_graph_pre_validator_scoring",
            "candidate_metadata_source": "diag_019 hash-verified pre-ILP export with retained final-node time checks",
            "candidate_id_space_valid": True,
            "candidate_rows_by_video": {
                name: {
                    **video["candidate_audit"],
                    "gt_relevant": video["relevant_candidate_count"],
                }
                for name, video in per_video.items()
            },
            "total_gt_relevant_candidates": total_relevant_candidates,
            "excluded_identity_collision_rows": total_time_mismatch_rows,
            "conflict_policy": "deterministic GT-action selection with unique mother and target claims",
            "wall_clock_seconds": time.monotonic() - started,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = run()
    print(json.dumps(result["metrics"], indent=2, sort_keys=True))
