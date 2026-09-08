"""Validate the corrected telemetry-only diagnostic without GPU inference."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

try:
    from scripts.build_public_0942_motion_ema_telemetry_v2 import (
        BEHAVIOR_PARENT,
        PARENT,
        build,
        source,
    )
except ModuleNotFoundError:
    from build_public_0942_motion_ema_telemetry_v2 import (
        BEHAVIOR_PARENT,
        PARENT,
        build,
        source,
    )


def functions(text):
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in ast.parse(text).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def find_code(cells, marker):
    matches = [cell for cell in cells if cell.get("cell_type") == "code" and marker in source(cell)]
    if len(matches) != 1:
        raise ValueError(f"Expected one code cell containing {marker!r}, found {len(matches)}")
    return matches[0]


def function_source(text, name):
    tree = ast.parse(text)
    matches = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one function named {name!r}, found {len(matches)}")
    return ast.get_source_segment(text, matches[0]) or ""


def validate(path):
    actual = json.loads(Path(path).read_text(encoding="utf-8"))
    expected = build()
    if actual != expected:
        raise ValueError("Notebook differs from deterministic reviewed telemetry-v2 adaptation")

    predecessor = json.loads(PARENT.read_text(encoding="utf-8"))
    behavior_parent = json.loads(BEHAVIOR_PARENT.read_text(encoding="utf-8"))
    predecessor_post = functions(source(find_code(predecessor["cells"], "def motion_relink_edges")))
    candidate_post = functions(source(find_code(actual["cells"], "def motion_relink_edges")))
    assert set(candidate_post) == set(predecessor_post) | {"_native_true_count"}
    assert all(
        predecessor_post[name] == candidate_post[name]
        for name in predecessor_post
        if name != "motion_relink_edges"
    ), "A non-telemetry postprocessing function changed"

    helper_text = function_source(
        source(find_code(actual["cells"], "def _native_true_count")), "_native_true_count")
    expected_helper = "def _native_true_count(values):\n    return int(sum(bool(value) for value in values))"
    assert ast.dump(ast.parse(helper_text), include_attributes=False) == ast.dump(
        ast.parse(expected_helper), include_attributes=False)
    namespace = {}
    exec(helper_text, namespace)
    assert namespace["_native_true_count"]([True, False, True]) == 2
    assert type(namespace["_native_true_count"]([True])) is int

    parent_scorer = functions(source(find_code(behavior_parent["cells"], 'row["t_true_source"]')))
    candidate_scorer = functions(source(find_code(actual["cells"], 'row["t_true_source"]')))
    assert parent_scorer == candidate_scorer, "Frozen scoring functions changed"

    text = "\n".join(source(cell) for cell in actual["cells"])
    required = (
        'BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"',
        'BIOHUB_MOTION_RELINK_TELEMETRY"] = "1"',
        'else MOTION_RELINK_EMA_ALPHA * step_velocity',
        'for threshold in (1.0, 1.25, 1.5, 1.75)',
        '"motion_relink_telemetry_finite_margin_updates"',
        '"motion_relink_telemetry_nonfinite_margin_updates"',
        'motion_relink_telemetry_age_ge3_gt_',
        'motion_relink_telemetry_finite_margin_gt_',
        'motion_relink_telemetry_margin_ge0500_gt_',
        'motion_relink_telemetry_guarded_gt_',
        'bool(np.isfinite(margin))',
        'allow_nan=False',
        '"telemetry_count_types_native_int"',
        '"validation_stage_stats_json_serializable"',
        '"submission_bytes_exact_parent"',
        '"aggregate_primary_exact"',
        '"videos_exact"',
        '"telemetry_diagnostic_passed"',
        'WORKING_DIR / "metrics.json"',
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise ValueError(f"Telemetry-v2 notebook contract is missing {missing}")
    forbidden = (
        'motion_relink_telemetry_proposed_gt_2000',
        'motion_relink_telemetry_proposed_gt_3000',
        'for threshold in (1.0, 1.25, 1.5, 2.0, 3.0)',
    )
    present = [item for item in forbidden if item in text]
    if present:
        raise ValueError(f"Telemetry-v2 notebook retained uninformative threshold code {present}")

    motion_text = function_source(
        source(find_code(actual["cells"], "def motion_relink_edges")), "motion_relink_edges")
    assert all(
        token not in motion_text.lower()
        for token in ("specimen", "ground_truth", "validator", "stem")
    )
    assert text.count("__CONTROLLER_EXPERIMENT_ID__") == 1
    assert not any("\u4e00" <= ch <= "\u9fff" or "\u0400" <= ch <= "\u04ff" for ch in text)
    for cell in actual["cells"]:
        if cell.get("cell_type") == "code":
            ast.parse(source(cell))
            assert cell["outputs"] == [] and cell["execution_count"] is None
    return {
        "passed": True,
        "cells": len(actual["cells"]),
        "single_change": "corrected_decomposed_online_motion_telemetry_only",
        "base_alpha": 0.4,
        "velocity_weight": 0.5,
        "thresholds": [1.0, 1.25, 1.5, 1.75],
        "native_count_regression": True,
        "strict_json_contract": True,
        "exact_parent_behavior_gates": True,
        "saved_errors": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    print(json.dumps(validate(parser.parse_args().notebook), indent=2))
