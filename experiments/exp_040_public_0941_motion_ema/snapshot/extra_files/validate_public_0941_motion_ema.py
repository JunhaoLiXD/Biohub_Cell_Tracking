"""Validate the deterministic single-variable EMA adaptation without GPU inference."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

try:
    from scripts.build_public_0941_motion_ema import PARENT, build, source
except ModuleNotFoundError:  # Direct execution places scripts/ rather than the project root on sys.path.
    from build_public_0941_motion_ema import PARENT, build, source


def functions(text):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(text).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def find_code(cells, marker):
    matches = [cell for cell in cells if cell.get("cell_type") == "code" and marker in source(cell)]
    if len(matches) != 1:
        raise ValueError(f"Expected one code cell containing {marker!r}, found {len(matches)}")
    return matches[0]


def validate(path):
    actual = json.loads(Path(path).read_text(encoding="utf-8"))
    expected = build()
    if actual != expected:
        raise ValueError("Notebook differs from deterministic reviewed EMA adaptation")
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    parent_post = functions(source(find_code(parent["cells"], "def motion_relink_edges")))
    candidate_post = functions(source(find_code(actual["cells"], "def motion_relink_edges")))
    assert set(parent_post) == set(candidate_post), "Postprocessing function set changed"
    assert all(parent_post[name] == candidate_post[name] for name in parent_post if name != "motion_relink_edges"), \
        "A postprocessing function other than motion_relink_edges changed"
    parent_scorer = functions(source(find_code(parent["cells"], 'row["t_true_source"]')))
    candidate_scorer = functions(source(find_code(actual["cells"], 'row["t_true_source"]')))
    assert parent_scorer == candidate_scorer, "Frozen scoring functions changed"
    text = "\n".join(source(cell) for cell in actual["cells"])
    required = (
        'BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "0.5"',
        'BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"',
        "velocity_um: dict[int, np.ndarray] = {}",
        "velocity = velocity_um.get(source_id)",
        "MOTION_RELINK_EMA_ALPHA * step_velocity",
        '"motion_relink_velocity_estimator": "per_track_ema"',
        '"motion_ema_exercised_both_specimens"',
        '"ema_candidate_gate_passed"',
        '"aggregate_improvement_at_least_0_001"',
        '"candidate_submission_unchanged_after_validation"',
        'WORKING_DIR / "metrics.json"',
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise ValueError(f"EMA notebook contract is missing {missing}")
    assert text.count("__CONTROLLER_EXPERIMENT_ID__") == 1
    assert not any("\u4e00" <= ch <= "\u9fff" or "\u0400" <= ch <= "\u04ff" for ch in text)
    for cell in actual["cells"]:
        if cell.get("cell_type") == "code":
            ast.parse(source(cell))
            assert cell["outputs"] == [] and cell["execution_count"] is None
    return {"passed": True, "cells": len(actual["cells"]), "single_algorithm_change": "motion_velocity_estimator",
            "ema_alpha": 0.4, "velocity_weight": 0.5, "frozen_train16_protocol": True, "saved_errors": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    print(json.dumps(validate(parser.parse_args().notebook), indent=2))
