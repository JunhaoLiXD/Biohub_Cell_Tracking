from __future__ import annotations

import argparse
import json

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError
from experiment_controller.review import request_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Request a read-only Claude Code experiment review")
    parser.add_argument("experiment")
    args = parser.parse_args()
    try:
        record = request_review(PROJECT_ROOT, args.experiment)
    except ControllerError as exc:
        parser.error(str(exc))
    print(json.dumps(record["review"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

