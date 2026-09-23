from __future__ import annotations

import csv
from pathlib import Path

from scripts.audit_biohub_submission_csv import COLUMNS, audit_submission


def _write(path: Path, rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        writer.writerows(rows)


def _valid_rows() -> list[list[object]]:
    return [
        [0, "movie", "node", 10, 0, 1, 2, 3, -1, -1],
        [1, "movie", "node", 11, 1, 1, 3, 4, -1, -1],
        [2, "movie", "edge", -1, -1, -1, -1, -1, 10, 11],
    ]


def test_valid_graph_passes(tmp_path: Path) -> None:
    path = tmp_path / "submission.csv"
    _write(path, _valid_rows())
    report = audit_submission(path, expected_datasets={"movie"}, image_bounds=(2, 4, 5))
    assert report["status"] == "PASS"


def test_rejects_id_gap_wrong_sentinel_and_missing_endpoint(tmp_path: Path) -> None:
    path = tmp_path / "submission.csv"
    rows = _valid_rows()
    rows[1][0] = 3
    rows[0][8] = 0
    rows[2][9] = 99
    _write(path, rows)
    report = audit_submission(path)
    assert report["status"] == "FAIL"
    joined = "\n".join(report["errors"])
    assert "id must be unique" in joined
    assert "node edge sentinels" in joined
    assert "edge endpoint missing" in joined


def test_rejects_duplicate_nonadjacent_edge_and_degree_overflow(tmp_path: Path) -> None:
    path = tmp_path / "submission.csv"
    rows = _valid_rows()
    rows.extend([
        [3, "movie", "node", 12, 1, 1, 2, 2, -1, -1],
        [4, "movie", "node", 13, 1, 1, 2, 3, -1, -1],
        [5, "movie", "node", 14, 2, 1, 2, 4, -1, -1],
        [6, "movie", "edge", -1, -1, -1, -1, -1, 10, 11],
        [7, "movie", "edge", -1, -1, -1, -1, -1, 10, 12],
        [8, "movie", "edge", -1, -1, -1, -1, -1, 10, 13],
        [9, "movie", "edge", -1, -1, -1, -1, -1, 10, 14],
    ])
    _write(path, rows)
    report = audit_submission(path)
    joined = "\n".join(report["errors"])
    assert "duplicate edge" in joined
    assert "non-adjacent edge" in joined
    assert "outdegree 5" in joined


def test_rejects_dataset_and_bounds_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "submission.csv"
    _write(path, _valid_rows())
    report = audit_submission(path, expected_datasets={"hidden"}, image_bounds=(1, 3, 4))
    joined = "\n".join(report["errors"])
    assert "dataset set mismatch" in joined
    assert "outside" in joined


def test_rejects_short_row_without_crashing(tmp_path: Path) -> None:
    path = tmp_path / "submission.csv"
    path.write_text(",".join(COLUMNS) + "\n0,movie,node\n", encoding="utf-8")
    report = audit_submission(path)
    assert report["status"] == "FAIL"
    assert any("empty value" in error for error in report["errors"])


def test_rejects_header_only_file(tmp_path: Path) -> None:
    path = tmp_path / "submission.csv"
    path.write_text(",".join(COLUMNS) + "\n", encoding="utf-8")
    report = audit_submission(path)
    assert report["status"] == "FAIL"
    assert "submission contains no data rows" in report["errors"]
    assert "submission contains no node rows" in report["errors"]
