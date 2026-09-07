from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError, sha256_file
from experiment_controller.kaggle import gate_submission


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Enforce the Kaggle daily leaderboard-submission cap and duplicate-probe guard "
            "before submitting. Queries the live remote history and the local "
            "SUBMISSION_BUDGET.json; exits non-zero (blocking) when a submission must not proceed."
        )
    )
    parser.add_argument(
        "--competition",
        default="biohub-cell-tracking-during-development",
        help="Kaggle competition slug.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Submission file to hash for the duplicate check.")
    group.add_argument("--sha256", help="Precomputed submission SHA256 for the duplicate check.")
    parser.add_argument("--experiment", help="Experiment id this submission belongs to (for the record).")
    parser.add_argument(
        "--user-override",
        action="store_true",
        help="Explicitly override the cap / duplicate guard (requires user justification).",
    )
    args = parser.parse_args()

    candidate_sha256 = args.sha256 or sha256_file(args.file)
    try:
        verdict = gate_submission(
            PROJECT_ROOT,
            competition=args.competition,
            candidate_sha256=candidate_sha256,
            experiment_id=args.experiment,
            user_override=args.user_override,
        )
    except ControllerError as exc:
        print(json.dumps({"allowed": False, "reason": str(exc), "sha256": candidate_sha256}, indent=2))
        return 1
    verdict["allowed"] = True
    verdict["sha256"] = candidate_sha256
    print(json.dumps(verdict, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
