from __future__ import annotations

import argparse
import json

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError, create_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an immutable experiment snapshot")
    parser.add_argument("config")
    parser.add_argument("--allow-duplicate", action="store_true")
    args = parser.parse_args()
    try:
        record = create_experiment(args.config, root=PROJECT_ROOT, allow_duplicate=args.allow_duplicate)
    except ControllerError as exc:
        parser.error(str(exc))
    print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

