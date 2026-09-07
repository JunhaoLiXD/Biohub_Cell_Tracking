from __future__ import annotations

import argparse
import json

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError, run_smoke_test


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an experiment's configured local smoke test")
    parser.add_argument("experiment")
    args = parser.parse_args()
    try:
        record = run_smoke_test(PROJECT_ROOT, args.experiment)
    except ControllerError as exc:
        parser.error(str(exc))
    print(json.dumps(record["smoke_test"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

