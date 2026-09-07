"""Cross-specimen Phase-1 separability audit on frozen candidate features."""

from __future__ import annotations

import gzip
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score


EXPERIMENT_ID = "diag_026_train16_cross_specimen_feature_separability"
PARENT_EXPERIMENT_ID = "diag_019_train16_final_validation_graph_export"
PROTOCOL = "public_0933_train16_candidate_feature_separability_v1"
FEATURE_NAMES = (
    "distance_um",
    "fused_logit",
    "fused_probability",
    "parent_margin",
    "child_margin",
    "parent_rank_for_target",
    "child_rank_for_source",
)


def _finite_feature(row: dict[str, Any], name: str) -> float:
    value = float(row.get(name, 0.0) or 0.0)
    return value if math.isfinite(value) else 0.0


def _candidate_dataset(
    parent_root: Path,
    train_dir: Path,
    names: list[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    features: list[list[float]] = []
    labels: list[int] = []
    specimens: list[str] = []
    per_video: dict[str, Any] = {}
    for name in names:
        nodes, _base_edges = _load_final_graph(parent_root, name)
        dataset = open_dataset(train_dir / name, normalize=False, require_tracks=True, load_image=False)
        if dataset.tracks is None:
            raise RuntimeError(f"Ground truth was not loaded for {name}")
        gt_nodes = _node_rows(dataset.tracks)
        gt_edges = _edge_pairs(dataset.tracks)
        pred_to_gt, _gt_to_pred = _match_nodes_bipartite(
            nodes, gt_nodes, tuple(float(value) for value in dataset.scale)
        )
        gt_out: dict[int, set[int]] = {}
        for source, target in gt_edges:
            gt_out.setdefault(source, set()).add(target)
        seen_pairs: set[tuple[int, int]] = set()
        counts = {"rows": 0, "eligible": 0, "positive": 0, "time_collision": 0}
        path = parent_root / "preilp_edge_audit" / f"{name}.jsonl.gz"
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                counts["rows"] += 1
                source = int(row["source_id"])
                target = int(row["target_id"])
                pair = (source, target)
                if pair in seen_pairs or source not in nodes or target not in nodes:
                    continue
                seen_pairs.add(pair)
                t_src = int(row["t_src"])
                t_tgt = int(row["t_tgt"])
                if (
                    nodes[source][0] != t_src
                    or nodes[target][0] != t_tgt
                    or t_tgt != t_src + 1
                ):
                    counts["time_collision"] += 1
                    continue
                matched_source = pred_to_gt.get(source)
                matched_target = pred_to_gt.get(target)
                if matched_source is None or matched_target is None:
                    continue
                label = int(
                    len(gt_out.get(matched_source, ())) >= 2
                    and (matched_source, matched_target) in gt_edges
                )
                feature_row = [_finite_feature(row, feature) for feature in FEATURE_NAMES]
                feature_row.extend(
                    [
                        min(feature_row[5], feature_row[6]),
                        max(feature_row[3], feature_row[4]),
                    ]
                )
                features.append(feature_row)
                labels.append(label)
                specimens.append(name.split("_")[0])
                counts["eligible"] += 1
                counts["positive"] += label
        per_video[name] = counts
    matrix = np.asarray(features, dtype=np.float64)
    target = np.asarray(labels, dtype=np.int64)
    domain = np.asarray(specimens)
    if not len(matrix) or target.sum() == 0:
        raise RuntimeError("No labeled candidate feature rows were constructed")
    return matrix, target, domain, per_video


def _fit_direction(
    matrix: np.ndarray,
    target: np.ndarray,
    domain: np.ndarray,
    train_specimen: str,
    test_specimen: str,
) -> dict[str, Any]:
    train_mask = domain == train_specimen
    test_mask = domain == test_specimen
    y_train = target[train_mask]
    y_test = target[test_mask]
    if len(np.unique(y_train)) != 2 or len(np.unique(y_test)) != 2:
        raise RuntimeError(
            f"Both classes are required for {train_specimen}->{test_specimen}: "
            f"train_positive={int(y_train.sum())}, test_positive={int(y_test.sum())}"
        )
    positive_weight = len(y_train) / (2.0 * int(y_train.sum()))
    negative_weight = len(y_train) / (2.0 * int((1 - y_train).sum()))
    sample_weight = np.where(y_train == 1, positive_weight, negative_weight)
    model = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_depth=3,
        max_iter=120,
        l2_regularization=1.0,
        random_state=314159,
    )
    model.fit(matrix[train_mask], y_train, sample_weight=sample_weight)
    probability = model.predict_proba(matrix[test_mask])[:, 1]
    prevalence = float(y_test.mean())
    auc = float(roc_auc_score(y_test, probability))
    average_precision = float(average_precision_score(y_test, probability))
    return {
        "train_specimen": train_specimen,
        "test_specimen": test_specimen,
        "train_rows": int(train_mask.sum()),
        "train_positive": int(y_train.sum()),
        "test_rows": int(test_mask.sum()),
        "test_positive": int(y_test.sum()),
        "test_prevalence": prevalence,
        "roc_auc": auc,
        "average_precision": average_precision,
        "average_precision_lift": average_precision / prevalence,
    }


def run_feature_audit(
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
    matrix, target, domain, per_video = _candidate_dataset(parent_root, train_dir, names)
    directions = {
        "44b6_to_6bba": _fit_direction(matrix, target, domain, "44b6", "6bba"),
        "6bba_to_44b6": _fit_direction(matrix, target, domain, "6bba", "44b6"),
    }
    min_auc = min(row["roc_auc"] for row in directions.values())
    min_ap_lift = min(row["average_precision_lift"] for row in directions.values())
    gate = min_auc > 0.5 and min_ap_lift > 1.0
    payload = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "primary_metric": min_auc,
        "baseline_primary_metric": 0.5,
        "runtime_seconds": 0.0,
        "reproducible": False,
        "methodology_valid": True,
        "validation": {
            "protocol": PROTOCOL,
            "seed": 314159,
            "warning": "Train-derived representation audit; this is not a deployable action scorer.",
        },
        "specimen_metrics": {
            row["test_specimen"]: {
                "primary_metric": row["roc_auc"],
                "baseline_primary_metric": 0.5,
            }
            for row in directions.values()
        },
        "metrics": {
            "feature_separability_passed": gate,
            "minimum_cross_specimen_roc_auc": min_auc,
            "minimum_cross_specimen_average_precision_lift": min_ap_lift,
            "feature_names": [*FEATURE_NAMES, "minimum_rank", "maximum_margin"],
            "directions": directions,
            "total_rows": int(len(target)),
            "total_positive": int(target.sum()),
            "per_video": per_video,
            "wall_clock_seconds": time.monotonic() - started,
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_feature_audit()["metrics"], indent=2, sort_keys=True))
