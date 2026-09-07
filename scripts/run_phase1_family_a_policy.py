"""Cross-specimen learned Family-A action-policy gate."""

from __future__ import annotations

import gzip
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier


EXPERIMENT_ID = "diag_027_train16_cross_specimen_family_a_policy"
PARENT_EXPERIMENT_ID = "diag_019_train16_final_validation_graph_export"
PROTOCOL = "public_0933_train16_cross_specimen_family_a_policy_v1"


def _fit_model(matrix: np.ndarray, target: np.ndarray, domain: np.ndarray, specimen: str):
    mask = domain == specimen
    labels = target[mask]
    if len(np.unique(labels)) != 2:
        raise RuntimeError(f"Training specimen {specimen} does not contain both classes")
    positive_weight = len(labels) / (2.0 * int(labels.sum()))
    negative_weight = len(labels) / (2.0 * int((1 - labels).sum()))
    weights = np.where(labels == 1, positive_weight, negative_weight)
    model = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_depth=3,
        max_iter=120,
        l2_regularization=1.0,
        random_state=314159,
    )
    model.fit(matrix[mask], labels, sample_weight=weights)
    return model


def _load_policy_videos(parent_root: Path, train_dir: Path, names: list[str]) -> dict[str, Any]:
    videos: dict[str, Any] = {}
    for name in names:
        nodes, base_edges = _load_final_graph(parent_root, name)
        dataset = open_dataset(train_dir / name, normalize=False, require_tracks=True, load_image=False)
        if dataset.tracks is None:
            raise RuntimeError(f"Ground truth was not loaded for {name}")
        out_adj: dict[int, set[int]] = defaultdict(set)
        in_adj: dict[int, set[int]] = defaultdict(set)
        for source, target in base_edges:
            out_adj[source].add(target)
            in_adj[target].add(source)
        action_rows: list[dict[str, Any]] = []
        seen_pairs: set[tuple[int, int]] = set()
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
                if pair in base_edges or len(out_adj[source]) != 1 or in_adj[target]:
                    continue
                feature_row = [_finite_feature(row, feature) for feature in FEATURE_NAMES]
                feature_row.extend([min(feature_row[5], feature_row[6]), max(feature_row[3], feature_row[4])])
                action_rows.append({"pair": pair, "features": feature_row})
        scale = tuple(float(value) for value in dataset.scale)
        baseline = _score(
            nodes,
            base_edges,
            dataset.tracks,
            scale,
            _n_total(train_dir / f"{name}.geff"),
            return_matching=False,
        )
        videos[name] = {
            "specimen": name.split("_")[0],
            "nodes": nodes,
            "base_edges": base_edges,
            "gt": dataset.tracks,
            "scale": scale,
            "n_total": _n_total(train_dir / f"{name}.geff"),
            "baseline": baseline,
            "action_rows": action_rows,
        }
    return videos


def _best_actions(model, videos: dict[str, Any], specimen: str) -> dict[str, dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for name, video in videos.items():
        if video["specimen"] != specimen or not video["action_rows"]:
            continue
        matrix = np.asarray([row["features"] for row in video["action_rows"]], dtype=np.float64)
        probabilities = model.predict_proba(matrix)[:, 1]
        index = int(np.argmax(probabilities))
        best[name] = {**video["action_rows"][index], "probability": float(probabilities[index])}
    return best


def _score_policy(
    videos: dict[str, Any], specimen: str, best_actions: dict[str, dict[str, Any]], threshold: float
) -> dict[str, Any]:
    rows = []
    selected = 0
    for name, video in videos.items():
        if video["specimen"] != specimen:
            continue
        action = best_actions.get(name)
        edges = set(video["base_edges"])
        if action is not None and action["probability"] >= threshold:
            edges.add(action["pair"])
            selected += 1
        rows.append(
            _score(video["nodes"], edges, video["gt"], video["scale"], video["n_total"])
        )
    aggregate = _aggregate(rows)
    aggregate["selected_actions"] = selected
    return aggregate


def _direction(
    matrix: np.ndarray,
    target: np.ndarray,
    domain: np.ndarray,
    videos: dict[str, Any],
    train_specimen: str,
    test_specimen: str,
) -> dict[str, Any]:
    model = _fit_model(matrix, target, domain, train_specimen)
    train_actions = _best_actions(model, videos, train_specimen)
    test_actions = _best_actions(model, videos, test_specimen)
    candidate_thresholds = [math.inf]
    candidate_thresholds.extend(
        sorted({row["probability"] for row in train_actions.values()}, reverse=True)
    )
    train_baseline = _aggregate(
        [video["baseline"] for video in videos.values() if video["specimen"] == train_specimen]
    )
    scored_thresholds = []
    for threshold in candidate_thresholds:
        score = _score_policy(videos, train_specimen, train_actions, threshold)
        scored_thresholds.append(
            {
                "threshold": None if math.isinf(threshold) else threshold,
                "score": score,
                "delta_score": score["score"] - train_baseline["score"],
            }
        )
    chosen = max(
        scored_thresholds,
        key=lambda row: (row["delta_score"], -row["score"]["selected_actions"]),
    )
    threshold = math.inf if chosen["threshold"] is None else float(chosen["threshold"])
    test_baseline = _aggregate(
        [video["baseline"] for video in videos.values() if video["specimen"] == test_specimen]
    )
    test_score = _score_policy(videos, test_specimen, test_actions, threshold)
    return {
        "train_specimen": train_specimen,
        "test_specimen": test_specimen,
        "threshold": chosen["threshold"],
        "train_baseline": train_baseline,
        "train_policy": chosen["score"],
        "train_delta_score": chosen["delta_score"],
        "test_baseline": test_baseline,
        "test_policy": test_score,
        "test_delta_adjusted_edge_jaccard": (
            test_score["adjusted_edge_jaccard"] - test_baseline["adjusted_edge_jaccard"]
        ),
        "test_delta_division_jaccard": test_score["division_jaccard"] - test_baseline["division_jaccard"],
        "test_delta_score": test_score["score"] - test_baseline["score"],
        "train_candidate_videos": len(train_actions),
        "test_candidate_videos": len(test_actions),
    }


def run_policy_gate(
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
    matrix, target, domain, _per_video = _candidate_dataset(parent_root, train_dir, names)
    videos = _load_policy_videos(parent_root, train_dir, names)
    directions = {
        "44b6_to_6bba": _direction(matrix, target, domain, videos, "44b6", "6bba"),
        "6bba_to_44b6": _direction(matrix, target, domain, videos, "6bba", "44b6"),
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
            "warning": "Train16 cross-specimen policy gate; thresholds are selected only on the training specimen.",
        },
        "specimen_metrics": {
            row["test_specimen"]: {
                "primary_metric": row["test_delta_score"],
                "baseline_primary_metric": 0.0,
            }
            for row in directions.values()
        },
        "metrics": {
            "family_a_policy_gate_passed": passed,
            "baseline_reproduced": baseline_reproduced,
            "directions": directions,
            "policy": "one highest-scoring orphan-only action per video above a train-specimen threshold",
            "wall_clock_seconds": time.monotonic() - started,
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_policy_gate()["metrics"], indent=2, sort_keys=True))
