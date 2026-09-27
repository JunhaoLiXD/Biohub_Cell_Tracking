"""One-time tracked Kaggle launch for the user's explicit exp067c review waiver.

The user instructed on 2026-09-26, after the Codex CLI hit a usage limit part-way through the
admission review and produced no verdict: "don't wait for the codex review, if you think it's fine
push to kaggle directly."

This does NOT claim a Codex PASS. The record keeps `verdict: NO_PASS` and a review status that says
the gate was waived by the user, so no later reader can mistake this run for an admitted one. The
generic controller gates are untouched: `scripts/launch_kaggle.py` still refuses without a PASS, and
every other gate this run does pass -- snapshot integrity, the pinned notebook hash, the configured
smoke command, the behavioral test suite, the Kaggle target, and the budget reservation -- is
executed here rather than skipped.

Export only: no TEST inference, no sweep, no submission, no promotion.
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
EXPERIMENT_ID = "exp_067c_temporal_feature_export_v3"
EXPECTED_SHA256 = "ce2bcf4068890523296e81fe39cbe83f2a2fe545c77375bab011f1d2fca855fe"
EXPECTED_KERNEL = "lingxd/biohub-exp067c-temporal-export"
WAIVER_REASON = (
    "User instruction 2026-09-26: skip the Codex admission review and push directly to Kaggle. "
    "The review was requested and failed on a Codex CLI usage limit without producing a verdict "
    "(experiments/exp_067c_temporal_feature_export_v3/codex-review-quota-stop-v1.json). "
    "No PASS exists and none is claimed."
)
# The isolated CPU interpreter the exp067 suite is pinned to; falls back to this one if absent.
TEST_PYTHON = ROOT / ".private/runtime/exp067_cpu/Scripts/python.exe"
TEST_TARGETS = ("tests/test_exp067.py", "tests/test_exp067c_admission.py")


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def main() -> int:
    record = load_record(ROOT, EXPERIMENT_ID)
    # READY is accepted so a push that aborted before reaching Kaggle can be retried; a record
    # that already has a remote run never can.
    if record["state"] not in {"PROPOSED", "READY"} or record.get("remote"):
        raise ControllerError(
            "This one-time waiver launch requires a PROPOSED or READY record and no remote run")
    if record.get("review", {}).get("status") == "PASSED":
        raise ControllerError("A real review PASS exists; use scripts/launch_kaggle.py instead")

    verify_snapshot(ROOT, record)
    source = ROOT / record["snapshot_source"]
    actual = sha256_file(source)
    if actual != EXPECTED_SHA256:
        raise ControllerError(f"exp067c notebook hash changed: {actual}")

    _, config = load_config(ROOT / record["snapshot_config"], ROOT)
    settings = resolve_kernel_settings(config)
    if settings["kernel_id"] != EXPECTED_KERNEL:
        raise ControllerError(f"Unexpected Kaggle target: {settings['kernel_id']}")
    if (config.get("leaderboard") or {}).get("authorized"):
        raise ControllerError("This waiver covers an export run only; no leaderboard submission")

    # Everything the waived review would not have replaced anyway: run it, do not assume it.
    checks = []
    smoke = [sys.executable, str(ROOT / "scripts/validate_notebook.py"), str(source),
             "--require-metrics-contract"]
    checks.append(("notebook_contract", smoke, run(smoke)))
    python = str(TEST_PYTHON) if TEST_PYTHON.exists() else sys.executable
    tests = [python, "-m", "pytest", *TEST_TARGETS, "-q", "--tb=short",
             "--basetemp", ".private/runtime/exp067_waiver_launch"]
    checks.append(("behavioral_tests", tests, run(tests)))

    receipt = {
        "at_utc": utc_now(),
        "source_sha256": EXPECTED_SHA256,
        "review_waived": True,
        "waiver_reason": WAIVER_REASON,
        "checks": [{"name": name, "command": command, "returncode": result.returncode,
                    "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:]}
                   for name, command, result in checks],
    }
    write_json(ROOT / "experiments" / EXPERIMENT_ID / "user-waiver-smoke.json", receipt)
    failed = [name for name, _command, result in checks if result.returncode]
    if failed:
        raise ControllerError(f"Pre-launch checks failed {failed}; see user-waiver-smoke.json")

    record["review"] = {
        "required": True,
        "provider": "codex",
        "status": "WAIVED_BY_USER_FOR_ONE_EXPORT_KERNEL_RUN",
        "verdict": "NO_PASS",
        "reason": WAIVER_REASON,
        "failed_attempt": "experiments/exp_067c_temporal_feature_export_v3/codex-review-quota-stop-v1.json",
        "at_utc": utc_now(),
    }
    record["smoke_test"] = {
        "status": "PASSED",
        "type": "direct_immutable_snapshot_validation_and_test_suite_with_review_waiver",
        "receipt": f"experiments/{EXPERIMENT_ID}/user-waiver-smoke.json",
        "at_utc": utc_now(),
    }
    if record["state"] == "PROPOSED":
        transition(ROOT, record, "REVIEWED", note="One-time user waiver; formal Codex PASS absent")
        transition(ROOT, record, "LOCAL_TESTING", note="Direct snapshot smoke and exp067 suite passed")
        transition(ROOT, record, "READY", note="Ready for one manually tracked Kaggle push")
    else:
        # Already walked to READY by an attempt that aborted before reaching Kaggle; the checks
        # above have just been re-run against the same pinned snapshot.
        save_record(ROOT, record)
    reserve_budget(ROOT, EXPERIMENT_ID, float(config["budget"]["expected_gpu_hours"]))
    record = load_record(ROOT, EXPERIMENT_ID)
    record["budget"]["reserved"] = True
    save_record(ROOT, record)

    def unwind(note: str) -> None:
        release_budget(ROOT, EXPERIMENT_ID)
        failed_record = load_record(ROOT, EXPERIMENT_ID)
        failed_record["budget"]["reserved"] = False
        save_record(ROOT, failed_record)
        transition(ROOT, failed_record, "REMOTE_FAILED", note=note)

    try:
        kernel_dir, kernel_id = prepare_kernel_directory(ROOT, record, config)
        args = ["kernels", "push", "-p", str(kernel_dir)]
        if config["kaggle"].get("accelerator"):
            args += ["--accelerator", str(config["kaggle"]["accelerator"])]
        result = _run_kaggle(ROOT, EXPERIMENT_ID, args, "kaggle-launch.log")
    except Exception:
        unwind("Pre-push failure in the one-time user-waiver launch")
        raise
    if result.returncode:
        unwind("Kaggle push failed in the one-time user-waiver launch")
        raise ControllerError("Kaggle push failed; see experiment kaggle-launch.log")

    record = load_record(ROOT, EXPERIMENT_ID)
    record["remote"] = {
        "kernel_id": kernel_id,
        "submitted_at": utc_now(),
        "status": "SUBMITTED",
        "last_checked_at": None,
        "launch_mode": "one_time_user_waiver_no_codex_pass",
    }
    transition(ROOT, record, "SUBMITTED",
               note="One-time user-authorized export kernel run; no LB submission")
    print(json.dumps({"experiment": EXPERIMENT_ID, "remote": record["remote"],
                      "stdout": result.stdout}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
