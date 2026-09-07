from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError
from experiment_controller.metrics import parse_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a structured experiment metrics.json")
    parser.add_argument("experiment")
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    try:
        result = parse_metrics(PROJECT_ROOT, args.experiment, args.source.resolve() if args.source else None)
    except ControllerError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

