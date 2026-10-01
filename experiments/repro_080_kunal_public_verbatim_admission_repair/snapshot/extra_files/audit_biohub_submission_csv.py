from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


COLUMNS = [
    "id", "dataset", "row_type", "node_id", "t", "z", "y", "x",
    "source_id", "target_id",
]
INTEGER_COLUMNS = ["id", "node_id", "t", "z", "y", "x", "source_id", "target_id"]


def _integer(text: str, column: str, row_number: int) -> int:
    if text == "":
        raise ValueError(f"row {row_number}: empty {column}")
    try:
        value = int(text)
    except ValueError as exc:
        raise ValueError(f"row {row_number}: {column} is not an integer: {text!r}") from exc
    return value


def audit_submission(
    path: Path,
    *,
    expected_datasets: set[str] | None = None,
    image_bounds: tuple[int, int, int] | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    nodes: dict[str, dict[int, tuple[int, int, int, int]]] = defaultdict(dict)
    edges: dict[str, list[tuple[int, int]]] = defaultdict(list)
    ids: list[int] = []
    dataset_rows: Counter[str] = Counter()

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COLUMNS:
            errors.append(f"header mismatch: expected {COLUMNS!r}, got {reader.fieldnames!r}")
        for row_number, row in enumerate(reader, start=2):
            if None in row or set(row) != set(COLUMNS):
                errors.append(f"row {row_number}: malformed column count")
                continue
            if any(row[name] is None or row[name] == "" for name in COLUMNS):
                errors.append(f"row {row_number}: empty value")
                continue
            dataset = row["dataset"]
            if not dataset:
                errors.append(f"row {row_number}: empty dataset")
                continue
            try:
                values = {name: _integer(row[name], name, row_number) for name in INTEGER_COLUMNS}
            except ValueError as exc:
                errors.append(str(exc))
                continue
            ids.append(values["id"])
            dataset_rows[dataset] += 1
            row_type = row["row_type"]
            if row_type == "node":
                if values["source_id"] != -1 or values["target_id"] != -1:
                    errors.append(f"row {row_number}: node edge sentinels must both be -1")
                if min(values[name] for name in ("node_id", "t", "z", "y", "x")) < 0:
                    errors.append(f"row {row_number}: node fields must be non-negative")
                if values["node_id"] in nodes[dataset]:
                    errors.append(f"row {row_number}: duplicate node ({dataset}, {values['node_id']})")
                nodes[dataset][values["node_id"]] = (
                    values["t"], values["z"], values["y"], values["x"]
                )
                if image_bounds is not None:
                    for axis, value, bound in zip(("z", "y", "x"), nodes[dataset][values["node_id"]][1:], image_bounds):
                        if value >= bound:
                            errors.append(f"row {row_number}: {axis}={value} outside [0,{bound})")
            elif row_type == "edge":
                if any(values[name] != -1 for name in ("node_id", "t", "z", "y", "x")):
                    errors.append(f"row {row_number}: edge node/coordinate sentinels must all be -1")
                if values["source_id"] < 0 or values["target_id"] < 0:
                    errors.append(f"row {row_number}: edge endpoints must be non-negative")
                edges[dataset].append((values["source_id"], values["target_id"]))
            else:
                errors.append(f"row {row_number}: invalid row_type {row_type!r}")

    if ids != list(range(len(ids))):
        errors.append("id must be unique, contiguous, zero-based, and in file order")
    if not ids:
        errors.append("submission contains no data rows")
    if not any(nodes.values()):
        errors.append("submission contains no node rows")
    found_datasets = set(dataset_rows)
    if expected_datasets is not None and found_datasets != expected_datasets:
        errors.append(
            f"dataset set mismatch: missing={sorted(expected_datasets - found_datasets)!r}, "
            f"unexpected={sorted(found_datasets - expected_datasets)!r}"
        )

    for dataset, dataset_edges in edges.items():
        seen_edges: set[tuple[int, int]] = set()
        indegree: Counter[int] = Counter()
        outdegree: Counter[int] = Counter()
        for source, target in dataset_edges:
            edge = (source, target)
            if edge in seen_edges:
                errors.append(f"duplicate edge ({dataset}, {source}, {target})")
            seen_edges.add(edge)
            if source not in nodes[dataset] or target not in nodes[dataset]:
                errors.append(f"edge endpoint missing ({dataset}, {source}, {target})")
                continue
            source_t = nodes[dataset][source][0]
            target_t = nodes[dataset][target][0]
            if target_t != source_t + 1:
                errors.append(f"non-adjacent edge ({dataset}, {source}, {target}): {source_t}->{target_t}")
            outdegree[source] += 1
            indegree[target] += 1
        for node_id, degree in indegree.items():
            if degree > 1:
                errors.append(f"node has indegree {degree} ({dataset}, {node_id})")
        for node_id, degree in outdegree.items():
            if degree > 2:
                errors.append(f"node has outdegree {degree} ({dataset}, {node_id})")

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "status": "PASS" if not errors else "FAIL",
        "path": str(path),
        "sha256": digest,
        "rows": len(ids),
        "datasets": dict(sorted(dataset_rows.items())),
        "node_rows": sum(len(value) for value in nodes.values()),
        "edge_rows": sum(len(value) for value in edges.values()),
        "errors": errors,
        "scope": "Project-side structural audit; not an official Kaggle scorer replica.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a Biohub submission CSV structurally.")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--expected-dataset", action="append", default=[])
    parser.add_argument("--image-bounds", nargs=3, type=int, metavar=("Z", "Y", "X"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_submission(
        args.csv,
        expected_datasets=set(args.expected_dataset) if args.expected_dataset else None,
        image_bounds=tuple(args.image_bounds) if args.image_bounds else None,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())


