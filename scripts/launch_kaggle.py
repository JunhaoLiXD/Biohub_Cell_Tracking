from __future__ import annotations

import argparse
import json

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError
from experiment_controller.kaggle import launch


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate, reserve budget, and launch a Kaggle experiment")
    parser.add_argument("--experiment", required=True)
    parser.add_argument(
        "--user-approved-budget",
        action="store_true",
        help="Use only after the user explicitly approves an above-threshold experiment",
    )
    args = parser.parse_args()
    try:
        record = launch(PROJECT_ROOT, args.experiment, user_approved_budget=args.user_approved_budget)
    except ControllerError as exc:
        parser.error(str(exc))
    print(json.dumps({"experiment": args.experiment, "state": record["state"], "remote": record["remote"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

