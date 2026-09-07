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
        'BIOHUB_DET_THRESHOLD"] = "0.965"',
        'BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT"] = "0.15"',
        'BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "0.5"',
        'BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"',
        '"BIOHUB_MOTION_RELINK_LEARNED_BONUS": 1.0',
        "velocity_um: dict[int, np.ndarray] = {}",
        "velocity = velocity_um.get(source_id)",
        "MOTION_RELINK_EMA_ALPHA * step_velocity",
        '"motion_relink_velocity_estimator": "per_track_ema"',
        '"ema_reference_kernel": "grafael/biohub-ct-0940-ema"',
        '"motion_ema_exercised_both_specimens"',
        '"motion_relink_ema_execution"',
        'WORKING_DIR / "metrics.json"',
    )
    forbidden = (
        'BIOHUB_DET_THRESHOLD"] = "0.96875"',
        'BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT"] = "0.30"',
        'BIOHUB_SECONDARY_DETECTION_WEIGHT"] = "0.475"',
        'BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "1.0"',
        '"baseline_output_preserved"',
        '"baseline_specimen_outputs_preserved"',
    )
    missing = [item for item in required if item not in source]
    unexpected = [item for item in forbidden if item in source]
    if missing or unexpected:
        raise ControllerError(
            f"Motion-EMA notebook contract failed: missing={missing}, forbidden={unexpected}"
        )
    summary["single_algorithm_change"] = "motion_velocity_estimator"
    summary["ema_alpha"] = 0.4
    summary["velocity_weight"] = 0.5
    summary["frozen_train16_protocol"] = True
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
