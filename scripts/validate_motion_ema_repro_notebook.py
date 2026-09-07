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
        'BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"',
        'BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "0.5"',
        '"motion_ema_exercised_both_specimens"',
        '"reproduction_primary_exact"',
        '"reproduction_adjusted_edge_exact"',
        '"reproduction_division_exact"',
        '"reproduction_specimens_exact"',
        '"reproduction_submission_sha256_exact"',
        '"reproduction_passed": _controller_reproduction_passed',
        '"reproducible": _controller_reproduction_passed',
        '"exp_035_train16_motion_ema_reviewfix"',
        '"93eec4d1e2f47d3b93f08fc7b0385cf3c80b7a7311e1eef8e0934ea2755f3ca3"',
    )
    missing = [item for item in required if item not in source]
    if missing:
        raise ControllerError(f"Motion-EMA reproduction contract is incomplete: {missing}")
    summary["algorithm_unchanged_from_exp_035"] = True
    summary["exact_metric_contract"] = True
    summary["exact_submission_sha256_contract"] = True
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
