from __future__ import annotations

import argparse

from _bootstrap import PROJECT_ROOT
from experiment_controller.baselines import pull
from experiment_controller.core import ControllerError


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull a public Kaggle kernel while preserving provenance")
    parser.add_argument("--kernel", required=True)
    args = parser.parse_args()
    try:
        destination = pull(PROJECT_ROOT, args.kernel)
    except ControllerError as exc:
        parser.error(str(exc))
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

