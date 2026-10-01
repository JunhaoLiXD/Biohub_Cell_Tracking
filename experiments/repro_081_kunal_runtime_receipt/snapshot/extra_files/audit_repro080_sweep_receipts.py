from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


EXPECTED_SOURCE_SHA256 = "5c370da1bf31d28215e023c4e4208c0bb658943c6ea4840d0af996aac5305b30"
EXPECTED_HELD_OUT = {
    "44b6_12dfb391", "44b6_267148e4", "44b6_2a2eff9f", "44b6_341df25f",
    "6bba_062c8d37", "6bba_07e24132", "6bba_085bf656", "6bba_09961292",
}
EXPECTED_TEST = {
    "44b6_0113de3b", "44b6_0b24845f", "6bba_05b6850b", "6bba_05db0fb1",
}
EXPECTED_CANDIDATES = {
    "base": {},
    "tight55": {"MOTION_RELINK_TIGHT_UM": 5.5},
    "gap45": {"GAP_CLOSE_UM": 4.5},
    "dcgap035": {"DEEPCENTER_GAP_THRESHOLD": 0.35},
    "bonus125": {"MOTION_RELINK_LEARNED_BONUS": 1.25},
    "relaxed9": {"MOTION_RELINK_RELAXED_UM": 9.0},
    "gap2step40": {"GAP2_MAX_STEP_UM": 4.0},
    "reuse28": {"GAP_CLOSE_REUSE_UM": 2.8},
    "sym_tau04": {"SAFE_DIV_SISTER_SYMMETRY_TAU": 0.4},
    "gap2tot92": {"GAP2_MAX_TOTAL_UM": 9.2},
    "dcsafediv020": {"DEEPCENTER_SAFE_DIV_THRESHOLD": 0.2},
    "edgemax12": {"OUTPUT_EDGE_MAX_UM": 12.0},
    "sym_dcsd": {"SAFE_DIV_SISTER_SYMMETRY_TAU": 0.4, "DEEPCENTER_SAFE_DIV_THRESHOLD": 0.2},
    "vel04": {"MOTION_RELINK_VELOCITY_WEIGHT": 0.4},
    "relaxed11": {"MOTION_RELINK_RELAXED_UM": 11.0},
}
SELECT_MARGIN = 0.0005
MAX_ADJ_LOSS = 0.0010


def finite_float(value: str, field: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise AssertionError(f"non-finite {field}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("source_notebook", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    assert hashlib.sha256(args.source_notebook.read_bytes()).hexdigest() == EXPECTED_SOURCE_SHA256
    selected = json.loads((args.artifacts / "ppsweep_selected.json").read_text(encoding="utf-8"))
    stems = selected["held_out_stems"]
    assert len(stems) == 8 and len(set(stems)) == 8
    assert set(stems) == EXPECTED_HELD_OUT
    assert Counter(stem.split("_", 1)[0] for stem in stems) == {"44b6": 4, "6bba": 4}
    assert not (set(stems) & EXPECTED_TEST)

    with (args.artifacts / "ppsweep_results.csv").open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(EXPECTED_CANDIDATES)
    by_label = {row["config"]: row for row in rows}
    assert len(by_label) == len(rows)
    assert set(by_label) == set(EXPECTED_CANDIDATES)
    for label, expected_overrides in EXPECTED_CANDIDATES.items():
        row = by_label[label]
        assert int(row["n_samples"]) == 8
        assert json.loads(row["overrides"]) == expected_overrides
        finite_float(row["proxy_score"], f"{label}.proxy_score")
        finite_float(row["adjusted_edge_jaccard"], f"{label}.adjusted_edge_jaccard")

    base = by_label["base"]
    base_proxy = finite_float(base["proxy_score"], "base.proxy_score")
    base_adj = finite_float(base["adjusted_edge_jaccard"], "base.adjusted_edge_jaccard")
    ranked = sorted(rows, key=lambda row: finite_float(row["proxy_score"], row["config"]), reverse=True)
    best = ranked[0]
    expected_selected = "base"
    if (
        best["config"] != "base"
        and finite_float(best["proxy_score"], "best.proxy_score") >= base_proxy + SELECT_MARGIN
        and finite_float(best["adjusted_edge_jaccard"], "best.adjusted_edge_jaccard") >= base_adj - MAX_ADJ_LOSS
    ):
        expected_selected = best["config"]
    assert selected["selected"] == expected_selected
    assert selected["overrides"] == EXPECTED_CANDIDATES[expected_selected]
    assert math.isclose(float(selected["base_proxy"]), base_proxy, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(
        float(selected["selected_proxy"]),
        finite_float(by_label[expected_selected]["proxy_score"], "selected.proxy_score"),
        rel_tol=0.0,
        abs_tol=1e-12,
    )

    with (args.artifacts / "run_stats.csv").open(newline="", encoding="utf-8-sig") as handle:
        run_rows = list(csv.DictReader(handle))
    assert {row["dataset"] for row in run_rows} == EXPECTED_TEST
    assert len(run_rows) == 4
    expected_suffix = ":" + expected_selected
    assert all(row["experiment_tag"].endswith(expected_suffix) for row in run_rows)
    assert all(int(row["repair_fallback"]) == 0 for row in run_rows)
    assert all(int(row["deadline_degraded"]) == 0 for row in run_rows)

    report = {
        "status": "PASS",
        "validator_enabled_effective": True,
        "held_out_stems": stems,
        "prefix_counts": dict(Counter(stem.split("_", 1)[0] for stem in stems)),
        "candidate_count": len(rows),
        "candidate_set_complete": True,
        "selection_rule_recomputed": True,
        "selected": expected_selected,
        "overrides": EXPECTED_CANDIDATES[expected_selected],
        "final_run_stats_use_selected_label": True,
        "test_datasets": sorted(EXPECTED_TEST),
        "no_train_test_stem_overlap": True,
        "fallback_or_deadline_degradation": False,
        "source_sha256": EXPECTED_SOURCE_SHA256,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
