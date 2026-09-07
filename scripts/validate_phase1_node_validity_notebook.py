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
        "def run_node_validity_policy_gate(",
        "def _attach_node_validity_dataset(",
        "P(source valid) * P(target valid) * P(division edge)",
        '"node_validity_test_roc_auc"',
        '"44b6_to_6bba"',
        '"6bba_to_44b6"',
        '"feature_contract_valid"',
        '"node_validity_policy_gate_passed"',
        "/kaggle/working/metrics.json",
    )
    missing = [item for item in required if item not in source]
    if missing:
        raise ControllerError(f"Node-validity notebook is missing required code: {missing}")
    summary["cross_specimen_directions"] = 2
    summary["node_level_validity"] = True
    summary["runtime_feature_contract"] = True
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
