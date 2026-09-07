from __future__ import annotations

import argparse
import json

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError
from experiment_controller.kaggle import collect


def main() -> int:
    parser = argparse.ArgumentParser(description="Download, parse, and evaluate a completed Kaggle run")
    parser.add_argument("experiment")
    parser.add_argument("--promote", action="store_true", help="Explicitly promote if all gates pass")
    args = parser.parse_args()
    try:
        result = collect(PROJECT_ROOT, args.experiment, promote=args.promote)
    except ControllerError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

