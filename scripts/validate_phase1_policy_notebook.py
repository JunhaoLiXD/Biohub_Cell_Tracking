from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import PROJECT_ROOT  # noqa: F401
from experiment_controller.core import ControllerError, validate_notebook


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    args = parser.parse_args()
    summary = validate_notebook(args.notebook, require_metrics_contract=True)
    notebook = json.loads(args.notebook.read_text(encoding="utf-8"))
    source = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    required = (
        "def run_policy_gate(",
        "HistGradientBoostingClassifier",
        '"44b6_to_6bba"',
        '"6bba_to_44b6"',
        '"test_delta_adjusted_edge_jaccard"',
        '"family_a_policy_gate_passed"',
        "one highest-scoring orphan-only action per video",
        "/kaggle/working/metrics.json",
    )
    missing = [item for item in required if item not in source]
    if missing:
        raise ControllerError(f"Policy notebook is missing required code: {missing}")
    summary["cross_specimen_directions"] = 2
    summary["metric_scored_policy"] = True
    summary["maximum_actions_per_video"] = 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
