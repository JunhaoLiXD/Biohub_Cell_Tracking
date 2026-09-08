"""Validate the deterministic telemetry-only diagnostic without GPU inference."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

try:
    from scripts.build_public_0942_motion_ema_online_telemetry import PARENT, build, source
except ModuleNotFoundError:
    from build_public_0942_motion_ema_online_telemetry import PARENT, build, source


def functions(text):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(text).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def find_code(cells, marker):
    matches = [cell for cell in cells if cell.get("cell_type") == "code" and marker in source(cell)]
    if len(matches) != 1:
        raise ValueError(f"Expected one code cell containing {marker!r}, found {len(matches)}")
    return matches[0]


def function_source(text, name):
    tree = ast.parse(text)
    matches = [node for node in tree.body
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(matches) != 1:
        raise ValueError(f"Expected one function named {name!r}, found {len(matches)}")
    return ast.get_source_segment(text, matches[0]) or ""


def validate(path):
    actual = json.loads(Path(path).read_text(encoding="utf-8"))
    expected = build()
    if actual != expected:
        raise ValueError("Notebook differs from deterministic reviewed telemetry adaptation")
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    parent_post = functions(source(find_code(parent["cells"], "def motion_relink_edges")))
    candidate_post = functions(source(find_code(actual["cells"], "def motion_relink_edges")))
    assert set(parent_post) == set(candidate_post), "Postprocessing function set changed"
    assert all(parent_post[name] == candidate_post[name]
               for name in parent_post if name != "motion_relink_edges"), \
        "A postprocessing function other than motion_relink_edges changed"
    parent_scorer = functions(source(find_code(parent["cells"], 'row["t_true_source"]')))
    candidate_scorer = functions(source(find_code(actual["cells"], 'row["t_true_source"]')))
    assert parent_scorer == candidate_scorer, "Frozen scoring functions changed"
    text = "\n".join(source(cell) for cell in actual["cells"])
    required = (
        'BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"',
        'BIOHUB_MOTION_RELINK_TELEMETRY"] = "1"',
        'else MOTION_RELINK_EMA_ALPHA * step_velocity',
        '"motion_relink_telemetry_innovation_q50"',
        '"motion_relink_telemetry_assignment_margin_q50"',
        '"motion_relink_telemetry_guarded_gt_1000"',
        '"submission_bytes_exact_parent"',
        '"aggregate_primary_exact"',
        '"videos_exact"',
        '"telemetry_diagnostic_passed"',
        'WORKING_DIR / "metrics.json"',
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise ValueError(f"Telemetry notebook contract is missing {missing}")
    motion_cell = source(find_code(actual["cells"], "def motion_relink_edges"))
    motion_text = function_source(motion_cell, "motion_relink_edges")
    assert all(token not in motion_text.lower() for token in ("specimen", "ground_truth", "validator", "stem"))
    assert text.count("__CONTROLLER_EXPERIMENT_ID__") == 1
    assert not any("\u4e00" <= ch <= "\u9fff" or "\u0400" <= ch <= "\u04ff" for ch in text)
    for cell in actual["cells"]:
        if cell.get("cell_type") == "code":
            ast.parse(source(cell))
            assert cell["outputs"] == [] and cell["execution_count"] is None
    return {"passed": True, "cells": len(actual["cells"]),
            "single_change": "online_motion_telemetry_only", "base_alpha": 0.4,
            "velocity_weight": 0.5, "exact_parent_behavior_gates": True, "saved_errors": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    print(json.dumps(validate(parser.parse_args().notebook), indent=2))
