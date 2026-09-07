"""Align DeepCenter audit scores with final safe-division edges in a submission.

The diagnostic notebook records scores before the final divergence and cap checks.
The source GEFF files contain the unmodified model graph, so this script reads the
post-processed submission CSV and keeps only records whose candidate edge was
actually retained.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

QUANTILES = (0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0)


def linear_quantile(sorted_values: list[float], q: float) -> float:
    position = (len(sorted_values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] * (1.0 - fraction) + sorted_values[upper] * fraction


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, **{f"q{int(q * 100):02d}": None for q in QUANTILES}}
    ordered = sorted(values)
    result: dict[str, float | int | None] = {"count": len(ordered)}
    result.update(
        {f"q{int(q * 100):02d}": linear_quantile(ordered, q) for q in QUANTILES}
    )
    return result


def analyze(experiment_dir: Path) -> dict[str, object]:
    artifact_dir = experiment_dir / "artifacts"
    audit_paths = sorted(artifact_dir.glob("deepcenter_safe_div_scores_*.jsonl"))
    if len(audit_paths) != 1:
        raise ValueError(f"Expected one score audit JSONL, found {len(audit_paths)}")
    submission_path = artifact_dir / "submission.csv"
    final_edges: dict[str, set[tuple[int, int]]] = defaultdict(set)
    with submission_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["row_type"] == "edge":
                final_edges[row["dataset"]].add(
                    (int(row["source_id"]), int(row["target_id"]))
                )
    final_out_degree = {
        dataset: Counter(source for source, _ in edges)
        for dataset, edges in final_edges.items()
    }

    all_validator_scores: dict[str, list[float]] = defaultdict(list)
    retained_scores: dict[str, list[float]] = defaultdict(list)
    retained_records: list[dict[str, object]] = []
    with audit_paths[0].open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            dataset = str(record["dataset"])
            if dataset not in final_edges:
                continue
            score = float(record["score"])
            all_validator_scores[dataset].append(score)
            source = int(record["source_id"])
            candidate = int(record["candidate_id"])
            existing_child = int(record["existing_child_id"])
            edges = final_edges[dataset]
            retained = (
                (source, candidate) in edges
                and (source, existing_child) in edges
                and final_out_degree[dataset][source] >= 2
            )
            if retained:
                retained_scores[dataset].append(score)
                retained_records.append(record)

    datasets: dict[str, object] = {}
    for dataset in sorted(final_edges):
        datasets[dataset] = {
            "audited_pre_divergence": summarize(all_validator_scores[dataset]),
            "retained_final_divisions": summarize(retained_scores[dataset]),
            "final_division_sources": int(
                sum(degree >= 2 for degree in final_out_degree[dataset].values())
            ),
        }

    retained_unique = {
        (str(record["dataset"]), int(record["source_id"]), int(record["candidate_id"]))
        for record in retained_records
    }
    if len(retained_unique) != len(retained_records):
        raise ValueError("Duplicate retained audit records were found")

    return {
        "experiment": experiment_dir.name,
        "method": "Audit candidate edge matched to both daughter edges in the final submission CSV.",
        "datasets": datasets,
        "validator_all_pre_divergence": summarize(
            [score for values in all_validator_scores.values() for score in values]
        ),
        "validator_retained_final_divisions": summarize(
            [score for values in retained_scores.values() for score in values]
        ),
        "retained_records": retained_records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.experiment_dir.resolve())
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.resolve().write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
