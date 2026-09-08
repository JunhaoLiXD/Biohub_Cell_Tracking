"""Replay a frozen submission graph to estimate label-free adaptive EMA trigger rates."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

VOXEL_SCALE_UM = (1.625, 0.40625, 0.40625)


def subtract(left, right):
    return tuple(a - b for a, b in zip(left, right))


def norm(vector):
    return math.sqrt(sum(value * value for value in vector))


def quantile(values, probability):
    ordered = sorted(values)
    if not ordered:
        return None
    position = probability * (len(ordered) - 1)
    low = int(math.floor(position))
    high = int(math.ceil(position))
    if low == high:
        return ordered[low]
    weight = position - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def diagnose(path: Path, threshold: float = 1.0):
    nodes = defaultdict(dict)
    edges = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            dataset = row["dataset"]
            if row["row_type"] == "node":
                nodes[dataset][int(row["node_id"])] = {
                    "t": int(row["t"]),
                    "position": tuple(float(row[key]) * scale
                                      for key, scale in zip(("z", "y", "x"), VOXEL_SCALE_UM)),
                }
            elif row["row_type"] == "edge":
                edges[dataset].append((int(row["source_id"]), int(row["target_id"])))

    results = {}
    all_ratios = []
    for dataset in sorted(nodes):
        node_map = nodes[dataset]
        consecutive = [edge for edge in edges[dataset]
                       if edge[0] in node_map and edge[1] in node_map
                       and node_map[edge[1]]["t"] == node_map[edge[0]]["t"] + 1]
        consecutive.sort(key=lambda edge: (node_map[edge[1]]["t"], edge[0], edge[1]))
        velocity = {}
        ratios = []
        initial = 0
        reset = 0
        base = 0
        for source_id, target_id in consecutive:
            step = subtract(node_map[target_id]["position"], node_map[source_id]["position"])
            previous = velocity.get(source_id)
            if previous is None:
                velocity[target_id] = step
                initial += 1
                continue
            scale = max(norm(step), norm(previous), 1e-6)
            ratio = norm(subtract(step, previous)) / scale
            ratios.append(ratio)
            all_ratios.append(ratio)
            alpha = 1.0 if ratio > threshold else 0.4
            if alpha == 1.0:
                reset += 1
            else:
                base += 1
            velocity[target_id] = tuple(alpha * current + (1.0 - alpha) * prior
                                        for current, prior in zip(step, previous))
        results[dataset] = {
            "consecutive_edges": len(consecutive),
            "initial_updates": initial,
            "eligible_updates": len(ratios),
            "reset_updates": reset,
            "base_updates": base,
            "reset_fraction": reset / len(ratios) if ratios else 0.0,
            "innovation_ratio_quantiles": {
                "p50": quantile(ratios, 0.5), "p90": quantile(ratios, 0.9),
                "p95": quantile(ratios, 0.95), "p99": quantile(ratios, 0.99),
            },
        }
    return {
        "source": str(path),
        "scope": "Approximate label-free replay on the frozen alpha-0.4 final submission graph",
        "limitations": "Final graph includes downstream postprocessing edges and is not an exact replay of motion_relink_edges.",
        "threshold": threshold,
        "datasets": results,
        "overall": {
            "eligible_updates": len(all_ratios),
            "reset_updates": sum(item["reset_updates"] for item in results.values()),
            "base_updates": sum(item["base_updates"] for item in results.values()),
            "reset_fraction": (sum(item["reset_updates"] for item in results.values()) / len(all_ratios)
                               if all_ratios else 0.0),
            "innovation_ratio_quantiles": {
                "p50": quantile(all_ratios, 0.5), "p90": quantile(all_ratios, 0.9),
                "p95": quantile(all_ratios, 0.95), "p99": quantile(all_ratios, 0.99),
            },
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("submission", type=Path)
    parser.add_argument("--threshold", type=float, default=1.0)
    args = parser.parse_args()
    print(json.dumps(diagnose(args.submission, args.threshold), indent=2))
