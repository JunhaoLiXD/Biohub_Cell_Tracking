from __future__ import annotations

import argparse
import json

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError
from experiment_controller.metrics import evaluate
from experiment_controller.core import experiment_dir, read_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate parsed metrics and update the experiment registry")
    parser.add_argument("experiment")
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    try:
        metrics = read_json(experiment_dir(PROJECT_ROOT, args.experiment) / "metrics.json")
        result = evaluate(PROJECT_ROOT, args.experiment, metrics, promote=args.promote)
    except ControllerError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

