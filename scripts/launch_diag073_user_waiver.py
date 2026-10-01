"""One-time tracked Kaggle launch for the user's explicit diag073 review waiver.

The failed review remains NO_PASS. All deterministic gates are re-run against the
immutable snapshot. This authorizes one diagnostic kernel push only: no retry,
confirmatory experiment, leaderboard submission, or promotion.
"""

from __future__ import annotations

import json
import subprocess
import sys

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
EXPERIMENT_ID = "diag_073_fork_protected_cache_repair"
EXPECTED_SHA256 = "77ad3756b4e6e600bf45a36bc12c9f20329058ad20d12478fa5df2cfd39c4b3f"
EXPECTED_KERNEL = "lingxd/biohub-diag073-fork-protected-cache-repair"
WAIVER_REASON = (
    "User instruction 2026-09-28: accept Codex's judgment that the admission gate may be "
    "waived and run diag073 once. Round 1's sole substantive destination-reuse finding was "
    "fixed and its positive and negative controls pass. The delta review then failed during "
    "environment setup three times before reading any file, so no substantive second finding "
    "exists. No PASS is claimed. This waiver covers one diagnostic kernel push only."
)


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def main() -> int:
    record = load_record(ROOT, EXPERIMENT_ID)
    if record["state"] != "MANUAL_REVIEW_REQUIRED" or record.get("remote"):
        raise ControllerError("Waiver launch requires MANUAL_REVIEW_REQUIRED and no prior remote run")
    if record.get("admission_conclusion", {}).get("status") != "NO_CONSENSUS":
        raise ControllerError("Expected preserved Tier B NO_CONSENSUS conclusion")

    verify_snapshot(ROOT, record)
    source = ROOT / record["snapshot_source"]
    actual = sha256_file(source)
    if actual != EXPECTED_SHA256:
        raise ControllerError(f"diag073 notebook hash changed: {actual}")

    _, config = load_config(ROOT / record["snapshot_config"], ROOT)
    settings = resolve_kernel_settings(config)
    if settings["kernel_id"] != EXPECTED_KERNEL:
        raise ControllerError(f"Unexpected Kaggle target: {settings['kernel_id']}")
    if (config.get("leaderboard") or {}).get("authorized"):
        raise ControllerError("This waiver does not authorize a leaderboard submission")

    smoke = [sys.executable, str(ROOT / "scripts/smoke_diag072.py"), str(source)]
    result = run(smoke)
    receipt = {
        "at_utc": utc_now(),
        "source_sha256": actual,
        "review_waived": True,
        "waiver_reason": WAIVER_REASON,
        "checks": [{
            "name": "diag073_immutable_snapshot_smoke",
            "command": smoke,
            "returncode": result.returncode,
            "stdout": result.stdout[-8000:],
            "stderr": result.stderr[-8000:],
        }],
    }
    write_json(ROOT / "experiments" / EXPERIMENT_ID / "user-waiver-smoke.json", receipt)
    if result.returncode:
        raise ControllerError("Pre-launch smoke failed; see user-waiver-smoke.json")

    prior_review = dict(record["review"])
    record["review"] = {
        "required": True,
        "provider": "codex",
        "status": "WAIVED_BY_USER_FOR_ONE_DIAGNOSTIC_KERNEL_RUN",
        "verdict": "NO_PASS",
        "reason": WAIVER_REASON,
        "failed_review": prior_review,
        "at_utc": utc_now(),
    }
    record["admission_conclusion"]["launch_allowed"] = True
    record["admission_conclusion"]["waiver"] = WAIVER_REASON
    record["smoke_test"] = {
        "status": "PASSED",
        "type": "direct_immutable_snapshot_validation_with_review_waiver",
        "receipt": f"experiments/{EXPERIMENT_ID}/user-waiver-smoke.json",
        "at_utc": utc_now(),
    }
    record["state"] = "READY"
    record.setdefault("state_history", []).append({
        "from": "MANUAL_REVIEW_REQUIRED",
        "to": "READY",
        "at": utc_now(),
        "note": "One-time user waiver; formal Codex PASS absent; immutable smoke passed",
    })
    save_record(ROOT, record)

    reserve_budget(ROOT, EXPERIMENT_ID, float(config["budget"]["expected_gpu_hours"]))
    record = load_record(ROOT, EXPERIMENT_ID)
    record["budget"]["reserved"] = True
    save_record(ROOT, record)

    def unwind(note: str) -> None:
        release_budget(ROOT, EXPERIMENT_ID)
        failed = load_record(ROOT, EXPERIMENT_ID)
        failed["budget"]["reserved"] = False
        save_record(ROOT, failed)
        transition(ROOT, failed, "REMOTE_FAILED", note=note)

    try:
        kernel_dir, kernel_id = prepare_kernel_directory(ROOT, record, config)
        args = ["kernels", "push", "-p", str(kernel_dir)]
        if config["kaggle"].get("accelerator"):
            args += ["--accelerator", str(config["kaggle"]["accelerator"])]
        push = _run_kaggle(ROOT, EXPERIMENT_ID, args, "kaggle-launch.log")
    except Exception:
        unwind("Pre-push failure in one-time diag073 user-waiver launch")
        raise
    if push.returncode:
        unwind("Kaggle push failed in one-time diag073 user-waiver launch")
        raise ControllerError("Kaggle push failed; see kaggle-launch.log")

    record = load_record(ROOT, EXPERIMENT_ID)
    record["remote"] = {
        "kernel_id": kernel_id,
        "submitted_at": utc_now(),
        "status": "SUBMITTED",
        "last_checked_at": None,
        "launch_mode": "one_time_user_waiver_no_codex_pass",
    }
    transition(ROOT, record, "SUBMITTED", note="One-time user-authorized diagnostic; no LB submission")
    print(json.dumps({"experiment": EXPERIMENT_ID, "remote": record["remote"], "stdout": push.stdout}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
