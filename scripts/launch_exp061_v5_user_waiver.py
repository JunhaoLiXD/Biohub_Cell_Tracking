"""One-time tracked Kaggle launch for the user's explicit v5 review waiver.

The user asked for the corrected v5 notebook to be built and pushed immediately, as a fallback in
case the v4 leaderboard submission (56481730) fails the way v2 did. This does not claim a Codex
PASS and does not change the generic controller gates.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import (
    ControllerError,
    load_config,
    load_record,
    release_budget,
    reserve_budget,
    save_record,
    sha256_file,
    transition,
    utc_now,
    verify_snapshot,
    write_json,
)
from experiment_controller.kaggle import _run_kaggle, prepare_kernel_directory, resolve_kernel_settings


ROOT = PROJECT_ROOT
EXPERIMENT_ID = "exp_061_zon_lb_submission_repair_v5"
EXPECTED_SHA256 = "da4d933b9ab1735cd2cb5150137445925fb19602916dd0143f76b5c8afe815ac"
VALIDATOR = ROOT / "scripts" / "validate_exp061_zon_deployment_v5.py"


def main() -> int:
    record = load_record(ROOT, EXPERIMENT_ID)
    if record["state"] != "PROPOSED" or record.get("remote"):
        raise ControllerError("One-time v5 launch requires an untouched PROPOSED record and no remote run")
    verify_snapshot(ROOT, record)
    source = ROOT / record["snapshot_source"]
    if sha256_file(source) != EXPECTED_SHA256:
        raise ControllerError("v5 notebook hash changed")
    _, config = load_config(ROOT / record["snapshot_config"], ROOT)
    settings = resolve_kernel_settings(config)
    if settings["kernel_id"] != "lingxd/biohub-exp061-zon-deploy-v5":
        raise ControllerError("Unexpected Kaggle target")
    command = [sys.executable, str(VALIDATOR), str(source)]
    check = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    write_json(ROOT / "experiments" / EXPERIMENT_ID / "user-waiver-smoke.json", {
        "at_utc": utc_now(),
        "source_sha256": EXPECTED_SHA256,
        "command": command,
        "returncode": check.returncode,
        "stdout": check.stdout,
        "stderr": check.stderr,
    })
    if check.returncode:
        raise ControllerError("v5 immutable snapshot validation failed; see user-waiver-smoke.json")

    record["review"] = {
        "required": True,
        "provider": "codex",
        "status": "WAIVED_BY_USER_FOR_ONE_V5_KERNEL_RUN",
        "verdict": "NO_PASS",
        "reason": "User asked for the corrected v5 build to be pushed immediately as a fallback for the pending v4 LB submission 56481730.",
        "at_utc": utc_now(),
    }
    record["smoke_test"] = {
        "status": "PASSED",
        "type": "direct_immutable_snapshot_validation_with_review_waiver",
        "receipt": f"experiments/{EXPERIMENT_ID}/user-waiver-smoke.json",
        "at_utc": utc_now(),
    }
    transition(ROOT, record, "REVIEWED", note="One-time user waiver; formal Codex PASS absent")
    transition(ROOT, record, "LOCAL_TESTING", note="Direct immutable snapshot smoke passed")
    transition(ROOT, record, "READY", note="Ready for one manually tracked Kaggle push")
    reserve_budget(ROOT, EXPERIMENT_ID, float(config["budget"]["expected_gpu_hours"]))
    record = load_record(ROOT, EXPERIMENT_ID)
    record["budget"]["reserved"] = True
    save_record(ROOT, record)

    try:
        kernel_dir, kernel_id = prepare_kernel_directory(ROOT, record, config)
        args = ["kernels", "push", "-p", str(kernel_dir)]
        if config["kaggle"].get("accelerator"):
            args += ["--accelerator", str(config["kaggle"]["accelerator"])]
        result = _run_kaggle(ROOT, EXPERIMENT_ID, args, "kaggle-launch.log")
    except Exception:
        release_budget(ROOT, EXPERIMENT_ID)
        record = load_record(ROOT, EXPERIMENT_ID)
        record["budget"]["reserved"] = False
        transition(ROOT, record, "REMOTE_FAILED", note="Pre-push failure in one-time user-waiver launch")
        raise
    if result.returncode:
        release_budget(ROOT, EXPERIMENT_ID)
        record = load_record(ROOT, EXPERIMENT_ID)
        record["budget"]["reserved"] = False
        transition(ROOT, record, "REMOTE_FAILED", note="Kaggle push failed in one-time user-waiver launch")
        raise ControllerError("Kaggle push failed; see experiment kaggle-launch.log")
    record = load_record(ROOT, EXPERIMENT_ID)
    record["remote"] = {
        "kernel_id": kernel_id,
        "submitted_at": utc_now(),
        "status": "SUBMITTED",
        "last_checked_at": None,
        "launch_mode": "one_time_user_waiver_no_codex_pass",
    }
    transition(ROOT, record, "SUBMITTED", note="One-time user-authorized kernel run; no LB submission")
    print(json.dumps({"experiment": EXPERIMENT_ID, "remote": record["remote"], "stdout": result.stdout}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
