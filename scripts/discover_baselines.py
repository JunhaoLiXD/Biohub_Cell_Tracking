from __future__ import annotations

import argparse
import json

from _bootstrap import PROJECT_ROOT
from experiment_controller.baselines import discover
from experiment_controller.core import ControllerError


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover public Kaggle kernel candidates")
    parser.add_argument("--competition", required=True)
    parser.add_argument("--top-k", type=int, default=20)
    args = parser.parse_args()
    try:
        rows = discover(PROJECT_ROOT, args.competition, args.top_k)
    except ControllerError as exc:
        parser.error(str(exc))
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

