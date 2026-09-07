from __future__ import annotations

import argparse
import json

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError
from experiment_controller.kaggle import check_status


def main() -> int:
    parser = argparse.ArgumentParser(description="Check and persist a Kaggle experiment status")
    parser.add_argument("experiment")
    args = parser.parse_args()
    try:
        record = check_status(PROJECT_ROOT, args.experiment)
    except ControllerError as exc:
        parser.error(str(exc))
    print(json.dumps({"experiment": args.experiment, "state": record["state"], "remote": record["remote"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

