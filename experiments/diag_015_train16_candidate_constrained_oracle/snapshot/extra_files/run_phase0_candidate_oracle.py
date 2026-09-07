"""Candidate-constrained Phase-0 division oracle for the fixed train16 validator.

This module is intended to run in a Kaggle notebook with the competition data,
the tracking support pack, and the output of diag_014 attached. It never trains
a model and never uses test labels. All decisions are made on the frozen 16-video
train-derived validation set recorded by diag_014.
"""

from __future__ import annotations

import gzip
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

from biohub_tracking.io import open_dataset
from biohub_tracking.metrics import evaluate as compute_metric
from biohub_tracking.metrics import node_recall, per_sample_metrics


EXPERIMENT_ID = "diag_015_train16_candidate_constrained_oracle"
PARENT_EXPERIMENT_ID = "diag_014_train16_preilp_edge_export"
PROTOCOL = "public_0933_train16_candidate_oracle_v1"
DIVISION_WEIGHT = 0.1
MAX_MATCH_DISTANCE_UM = 7.0
BASELINE_ABS_TOL = 1e-10
K = td.DEFAULT_ATTR_KEYS


@dataclass(frozen=True)
class Action:
    mother_gt_id: int
    adds: frozenset[tuple[int, int]]
    removes: frozenset[tuple[int, int]]


def _find_parent_output(search_root: Path) -> Path:
    candidates: list[Path] = []
    for path in search_root.rglob("metrics.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if payload.get("experiment_id") == PARENT_EXPERIMENT_ID:
            candidates.append(path.parent)
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected exactly one attached {PARENT_EXPERIMENT_ID} output, found {candidates}"
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


def _score(
    nodes: dict[int, tuple[int, float, float, float]],
    edges: set[tuple[int, int]],
    gt_graph: td.graph.BaseGraph,
    scale: tuple[float, float, float],
    n_total: float,
    *,
    return_matching: bool = False,
) -> dict[str, Any]:
    graph, original_to_new = _make_graph(nodes, edges, scale)
    new_to_original = {new: old for old, new in original_to_new.items()}
    result = compute_metric(graph, gt_graph, scale=scale, max_distance=MAX_MATCH_DISTANCE_UM)
    recall = node_recall(graph, gt_graph)
    derived = per_sample_metrics(result, n_total, recall)
    division_denom = result.division_tp + result.division_fp + result.division_fn
    division_jaccard = result.division_tp / division_denom if division_denom else 0.0
    output: dict[str, Any] = {
        "adjusted_edge_jaccard": float(derived["adj_edge_jaccard"]),
        "division_jaccard": float(division_jaccard),
        "score": float(derived["adj_edge_jaccard"] + DIVISION_WEIGHT * division_jaccard),
        "edge_tp": int(result.edge_tp),
        "edge_fp": int(result.edge_fp),
        "edge_fn": int(result.edge_fn),
        "division_tp": int(result.division_tp),
        "division_fp": int(result.division_fp),
        "division_fn": int(result.division_fn),
        "edge_weight": int(result.edge_tp + result.edge_fp + result.edge_fn),
    }
    if return_matching:
        attrs = graph.node_attrs(attr_keys=[K.NODE_ID, K.MATCHED_NODE_ID])
        gt_to_pred: dict[int, int] = {}
        for row in attrs.iter_rows(named=True):
            matched = row[K.MATCHED_NODE_ID]
            if matched is not None and int(matched) != -1:
                gt_to_pred[int(matched)] = new_to_original[int(row[K.NODE_ID])]
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


def _load_relevant_candidates(path: Path, wanted: set[tuple[int, int]]) -> dict[tuple[int, int], dict[str, Any]]:
    found: dict[tuple[int, int], dict[str, Any]] = {}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            pair = (int(row["source_id"]), int(row["target_id"]))
            if pair in wanted:
                found[pair] = row
    return found


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
    parent_root = _find_parent_output(search_root)
    parent_metrics = json.loads((parent_root / "metrics.json").read_text(encoding="utf-8"))
    validation_names = [
        name
        for specimen in ("44b6", "6bba")
        for name in parent_metrics["specimen_metrics"][specimen]["samples"]
    ]
    train_dir = _find_train_dir(search_root, validation_names)
    prediction_dir = parent_root / "tracking_repo" / "predictions" / "unknown" / "unet_transformer_val" / "split_0"
    candidate_dir = parent_root / "preilp_edge_audit"
    if not prediction_dir.is_dir() or not candidate_dir.is_dir():
        raise RuntimeError("diag_014 prediction or candidate export directory is missing")

    per_video: dict[str, dict[str, Any]] = {}
    for name in validation_names:
        prediction = _load_graph(prediction_dir / f"{name}.geff")
        dataset = open_dataset(train_dir / name, normalize=False, require_tracks=True, load_image=False)
        gt = dataset.tracks
        if gt is None:
            raise RuntimeError(f"Ground truth was not loaded for {name}")
        nodes = _node_rows(prediction)
        base_edges = _edge_pairs(prediction)
        baseline = _score(nodes, base_edges, gt, dataset.scale, _n_total(train_dir / f"{name}.geff"), return_matching=True)
        children = _gt_children(gt)
        gt_divisions = sorted(node_id for node_id, values in children.items() if len(values) == 2)
        wanted = {
            (baseline["gt_to_pred"][mother], baseline["gt_to_pred"][daughter])
            for mother in gt_divisions
            for daughter in children[mother]
            if mother in baseline["gt_to_pred"] and daughter in baseline["gt_to_pred"]
        }
        candidates = _load_relevant_candidates(candidate_dir / f"{name}.jsonl.gz", wanted)
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
        }

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
            "candidate_constraint": "diag_014 top-4-per-source-or-target union within 12 um",
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
