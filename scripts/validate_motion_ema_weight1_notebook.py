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
        'BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "1.0"',
        '"BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT": 1.0',
        'BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"',
        '"BIOHUB_MOTION_RELINK_LEARNED_BONUS": 1.0',
        '_CONTROLLER_BASELINE_PRIMARY = 0.9273163492758533',
        '"44b6": 0.9050173749768016',
        '"6bba": 0.9355045025356437',
        '"comparison_parent": "repro_036_train16_motion_ema"',
        '"velocity_weight_change": {"from": 0.5, "to": 1.0}',
        '"motion_ema_exercised_both_specimens"',
    )
    missing = [item for item in required if item not in source]
    if missing:
        raise ControllerError(f"EMA weight-1 notebook contract is incomplete: {missing}")
    summary["single_parameter_change"] = "motion_relink_velocity_weight"
    summary["parent_velocity_weight"] = 0.5
    summary["candidate_velocity_weight"] = 1.0
    summary["ema_alpha_unchanged"] = 0.4
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
