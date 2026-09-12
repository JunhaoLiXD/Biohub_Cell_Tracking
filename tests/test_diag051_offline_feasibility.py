import numpy as np

from scripts.diag051_offline_feasibility import extract_candidate_records, rank_stats


def _pair():
    return {
        "pair_indices": np.array([[0, 0], [1, 1], [2, 2]], dtype=np.int64),
        "source_ids": np.array([1, 0, 2], dtype=np.int64),
        "target_ids": np.array([2, 3, 0], dtype=np.int64),
        "primary_source_features": np.array([[1.0], [1.0], [1.0]]),
        "primary_target_features": np.array([[1.0], [1.0], [1.0]]),
        "secondary_source_features": np.array([[1.0], [1.0], [1.0]]),
        "secondary_target_features": np.array([[1.0], [1.0], [1.0]]),
        "probabilities": np.array([0.11, 0.77, 0.99]),
        "blended_logits": np.array([-1.1, 7.7, 9.9]),
        "status": np.array([2, 1, 2], dtype=np.int64),
    }


def test_filtered_pair_rows_keep_original_probability_logit_and_status():
    rows = extract_candidate_records(
        _pair(), np.array([10, 20, 30, 40]), {20}, {(20, 30)}, {(20, 30)},
        {20, 30}, {20, 30}
    )

    assert len(rows) == 1
    assert rows[0]["probability"] == 0.11
    assert rows[0]["blended"] == -1.1
    assert rows[0]["status"] == 2


def test_rank_stats_uses_conservative_worst_rank_for_ties():
    items = [
        {"source": 1, "positive": True, "probability": 1.0},
        {"source": 1, "positive": False, "probability": 1.0},
        {"source": 1, "positive": False, "probability": 0.0},
    ]

    stats = rank_stats(items, "probability")
    assert stats["n"] == 1
    assert stats["top1"] == 0
    assert stats["top3"] == 1
    assert stats["median_rank"] == 2.0


def test_noncontiguous_mask_preserves_distinct_original_rows():
    rows = extract_candidate_records(
        _pair(), np.array([10, 20, 30, 40]), {20, 30}, set(), set(),
        {10, 20, 30, 40}, {10, 20, 30, 40}
    )
    assert [(r["source"], r["target"]) for r in rows] == [(20, 30), (30, 10)]
    assert [r["probability"] for r in rows] == [0.11, 0.99]
    assert [r["blended"] for r in rows] == [-1.1, 9.9]
    assert [r["status"] for r in rows] == [2, 2]
    rows = extract_candidate_records(
        _pair(), np.array([10, 20, 30, 40]), {10}, set(), set(),
        {10, 20, 30, 40}, {10, 20, 30, 40}
    )
    assert (rows[0]["probability"], rows[0]["blended"], rows[0]["status"]) == (0.77, 7.7, 1)


def test_unmapped_endpoint_is_unlabeled_and_remains_in_candidate_pool():
    rows = extract_candidate_records(
        _pair(), np.array([10, 20, 30, 40]), {20}, {(20, 30)}, {(20, 30)},
        {20, 30, 40}, {20, 30}
    )

    assert [row["label"] for row in rows] == ["positive"]

    pair = _pair()
    pair["target_ids"] = np.array([3, 3, 0], dtype=np.int64)
    rows = extract_candidate_records(
        pair, np.array([10, 20, 30, 40]), {20}, {(20, 30)}, {(20, 30)},
        {20, 30, 40}, {20, 30}
    )
    assert rows[0]["label"] == "unlabeled"
    assert rows[0]["positive"] is False
