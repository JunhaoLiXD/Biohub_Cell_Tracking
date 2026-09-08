"""Validate the deterministic sparse soft-EMA candidate without GPU inference."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

try:
    from scripts.build_public_0942_motion_ema_sparse_soft import (
        BEHAVIOR_PARENT,
        DONOR,
        build,
        source,
    )
except ModuleNotFoundError:
    from build_public_0942_motion_ema_sparse_soft import (
        BEHAVIOR_PARENT,
        DONOR,
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
        raise ValueError("Notebook differs from deterministic sparse-soft adaptation")

    donor = json.loads(DONOR.read_text(encoding="utf-8"))
    behavior_parent = json.loads(BEHAVIOR_PARENT.read_text(encoding="utf-8"))
    donor_post = functions(source(find_code(donor["cells"], "def motion_relink_edges")))
    candidate_post = functions(source(find_code(actual["cells"], "def motion_relink_edges")))
    assert set(candidate_post) == set(donor_post) | {"_use_sparse_soft_alpha"}
    assert all(
        donor_post[name] == candidate_post[name]
        for name in donor_post
        if name != "motion_relink_edges"
    ), "A postprocessing function outside the sparse policy changed"

    parent_scorer = functions(source(find_code(behavior_parent["cells"], 'row["t_true_source"]')))
    candidate_scorer = functions(source(find_code(actual["cells"], 'row["t_true_source"]')))
    assert parent_scorer == candidate_scorer, "Frozen scoring functions changed"

    motion_cell = source(find_code(actual["cells"], "def motion_relink_edges"))
    motion_text = function_source(motion_cell, "motion_relink_edges")
    predicate_text = function_source(motion_cell, "_use_sparse_soft_alpha")
    assert all(
        token not in (motion_text + predicate_text).lower()
        for token in ("specimen", "ground_truth", "validator", "stem", "video_id")
    )

    text = "\n".join(source(cell) for cell in actual["cells"])
    required = (
        'BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"',
        'BIOHUB_MOTION_RELINK_EMA_SOFT_ALPHA"] = "0.6"',
        'BIOHUB_MOTION_RELINK_EMA_INNOVATION_THRESHOLD"] = "1.25"',
        'BIOHUB_MOTION_RELINK_EMA_MIN_TRACK_AGE"] = "3"',
        'BIOHUB_MOTION_RELINK_EMA_MIN_ASSIGNMENT_MARGIN"] = "0.5"',
        "innovation_ratio > MOTION_RELINK_EMA_INNOVATION_THRESHOLD",
        "source_track_age >= MOTION_RELINK_EMA_MIN_TRACK_AGE",
        "bool(np.isfinite(assignment_margin))",
        "assignment_margin >= MOTION_RELINK_EMA_MIN_ASSIGNMENT_MARGIN",
        '"motion_relink_sparse_soft_updates"',
        '"motion_relink_sparse_base_updates"',
        '"motion_relink_sparse_initial_updates"',
        'soft == int(row["motion_relink_telemetry_guarded_gt_1250"])',
        'soft + base == eligible',
        '"aggregate_improvement_at_least_0_0001"',
        '"worst_video_delta_vs_parent_at_least_minus_0_002"',
        '"sparse_soft_ema_candidate_gate_passed"',
        'allow_nan=False',
        'WORKING_DIR / "metrics.json"',
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise ValueError(f"Sparse soft notebook contract is missing {missing}")

    assert text.count("__CONTROLLER_EXPERIMENT_ID__") == 1
    assert not any("\u4e00" <= ch <= "\u9fff" or "\u0400" <= ch <= "\u04ff" for ch in text)
    for cell in actual["cells"]:
        if cell.get("cell_type") == "code":
            ast.parse(source(cell))
            assert cell["outputs"] == [] and cell["execution_count"] is None
    return {
        "passed": True,
        "cells": len(actual["cells"]),
        "single_algorithm_change": "label_free_sparse_soft_ema",
        "base_alpha": 0.4,
        "soft_alpha": 0.6,
        "innovation_threshold": 1.25,
        "minimum_track_age": 3,
        "minimum_assignment_margin": 0.5,
        "velocity_weight": 0.5,
        "strict_policy_count_contract": True,
        "frozen_train16_protocol": True,
        "saved_errors": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    print(json.dumps(validate(parser.parse_args().notebook), indent=2))
