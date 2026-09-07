"""Cross-specimen factorized validity-times-division Family-A policy gate."""

from __future__ import annotations

import gzip
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_ID = "diag_029_train16_factorized_family_a_policy"
PARENT_EXPERIMENT_ID = "diag_019_train16_final_validation_graph_export"
PROTOCOL = "public_0933_train16_factorized_family_a_policy_v1"


def _load_factorized_dataset(
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
                feature_row = [_finite_feature(row, feature) for feature in FEATURE_NAMES]
                feature_row.extend([min(feature_row[5], feature_row[6]), max(feature_row[3], feature_row[4])])
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
        raise RuntimeError("No factorized candidate training rows were constructed")
    return matrix, division_target, validity_target, domain, videos, audit


def _fit_factorized_models(
    matrix: np.ndarray,
    division_target: np.ndarray,
    validity_target: np.ndarray,
    domain: np.ndarray,
    specimen: str,
):
    validity_model = _fit_model(matrix, validity_target, domain, specimen)
    valid_mask = validity_target == 1
    division_model = _fit_model(
        matrix[valid_mask], division_target[valid_mask], domain[valid_mask], specimen
    )
    return validity_model, division_model


def _factorized_best_actions(
    validity_model, division_model, videos: dict[str, Any], specimen: str
) -> dict[str, dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for name, video in videos.items():
        if video["specimen"] != specimen or not video["action_rows"]:
            continue
        matrix = np.asarray([row["features"] for row in video["action_rows"]], dtype=np.float64)
        validity_probability = validity_model.predict_proba(matrix)[:, 1]
        division_probability = division_model.predict_proba(matrix)[:, 1]
        probability = validity_probability * division_probability
        index = int(np.argmax(probability))
        best[name] = {
            **video["action_rows"][index],
            "probability": float(probability[index]),
            "validity_probability": float(validity_probability[index]),
            "division_probability": float(division_probability[index]),
        }
    return best


def _factorized_direction(
    matrix: np.ndarray,
    division_target: np.ndarray,
    validity_target: np.ndarray,
    domain: np.ndarray,
    videos: dict[str, Any],
    train_specimen: str,
    test_specimen: str,
) -> dict[str, Any]:
    validity_model, division_model = _fit_factorized_models(
        matrix, division_target, validity_target, domain, train_specimen
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


def run_factorized_policy_gate(
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
    directions = {
        "44b6_to_6bba": _factorized_direction(
            matrix, division_target, validity_target, domain, videos, "44b6", "6bba"
        ),
        "6bba_to_44b6": _factorized_direction(
            matrix, division_target, validity_target, domain, videos, "6bba", "44b6"
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
            "warning": "Train16 factorized cross-specimen action-policy gate.",
        },
        "specimen_metrics": {
            row["test_specimen"]: {"primary_metric": row["test_delta_score"], "baseline_primary_metric": 0.0}
            for row in directions.values()
        },
        "metrics": {
            "factorized_policy_gate_passed": passed,
            "baseline_reproduced": baseline_reproduced,
            "directions": directions,
            "dataset_audit": audit,
            "action_score": "P(both endpoints matched) * P(division edge | both endpoints matched)",
            "gt_matching_is_not_a_model_feature": True,
            "wall_clock_seconds": time.monotonic() - started,
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_factorized_policy_gate()["metrics"], indent=2, sort_keys=True))
