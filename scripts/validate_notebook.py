from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import PROJECT_ROOT  # noqa: F401
from experiment_controller.core import ControllerError, validate_notebook


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Kaggle notebook without executing GPU code")
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--require-metrics-contract", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_notebook(args.notebook.resolve(), require_metrics_contract=args.require_metrics_contract)
    except ControllerError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

