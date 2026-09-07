from __future__ import annotations

import argparse
import json

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError
from experiment_controller.loop import run_once, watch


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the bounded, queue-driven experiment controller")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=300)
    parser.add_argument("--max-cycles", type=int)
    args = parser.parse_args()
    try:
        result = watch(PROJECT_ROOT, args.poll_seconds, args.max_cycles) if args.watch else run_once(PROJECT_ROOT)
    except ControllerError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
