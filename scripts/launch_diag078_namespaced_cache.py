"""One tracked namespaced-cache transport repair under explicit user authorization."""

from __future__ import annotations

import json
import subprocess
import sys

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import (
    ControllerError, load_config, load_record, release_budget, reserve_budget,
    save_record, sha256_file, transition, utc_now, verify_snapshot, write_json,
)
from experiment_controller.kaggle import _run_kaggle, prepare_kernel_directory, resolve_kernel_settings


ROOT = PROJECT_ROOT
EXPERIMENT_ID = "diag_078_fork_protected_namespaced_cache"
EXPECTED_SHA256 = "7991ff30a975bd3d9f77498e692f299fe33fe70c23c30d71385cdb47cce8b03b"
EXPECTED_KERNEL = "lingxd/biohub-diag078-fork-protected-cache-path"
EXPECTED_DATASETS = [
    "pilkwang/biohub-deepcenter-unet3d-center-prior-v1",
    "pilkwang/biohub-temporal-unet3d-seed314159-v1",
    "pilkwang/biohub-tracking-support-pack-50ep-v1",
    "anvithpothula/biohub-v1284-head-s075",
]
EXPECTED_COMPETITIONS = ["biohub-cell-tracking-during-development"]
EXPECTED_KERNELS = ["lingxd/biohub-exp065-pruning-sweep"]
EXPECTED_DOCKER = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
AUTHORIZATION = (
    "User instruction 2026-09-28: fix the namespaced cache mount and rerun. The fresh "
    "reviewer failed before reading any file and explicitly reported an infrastructure-only "
    "BLOCK. No PASS is claimed. Authorization covers one diag078 kernel push only, with no "
    "automatic retry, confirmatory work, leaderboard submission, or promotion."
)


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def main() -> int:
    record = load_record(ROOT, EXPERIMENT_ID)
    if record["state"] != "MANUAL_REVIEW_REQUIRED" or record.get("remote"):
        raise ControllerError("diag078 launch requires MANUAL_REVIEW_REQUIRED and no remote run")
    verify_snapshot(ROOT, record)
    source = ROOT / record["snapshot_source"]
    if sha256_file(source) != EXPECTED_SHA256:
        raise ControllerError("diag078 notebook hash mismatch")
    _, config = load_config(ROOT / record["snapshot_config"], ROOT)
    settings = resolve_kernel_settings(config)
    if settings["kernel_id"] != EXPECTED_KERNEL:
        raise ControllerError(f"Unexpected Kaggle target: {settings['kernel_id']}")
    if (config.get("leaderboard") or {}).get("authorized"):
        raise ControllerError("Leaderboard submission is not authorized")

    smoke = [sys.executable, str(ROOT / "scripts/smoke_diag077.py"), str(source)]
    smoke_result = run(smoke)
    receipt = {
        "at_utc": utc_now(), "source_sha256": EXPECTED_SHA256,
        "review_waived": True, "authorization": AUTHORIZATION,
        "checks": [{"name": "namespaced_cache_snapshot_smoke", "command": smoke,
                    "returncode": smoke_result.returncode,
                    "stdout": smoke_result.stdout[-8000:], "stderr": smoke_result.stderr[-8000:]}],
    }
    receipt_path = ROOT / "experiments" / EXPERIMENT_ID / "authorized-repair-smoke.json"
    write_json(receipt_path, receipt)
    if smoke_result.returncode:
        raise ControllerError("diag078 smoke failed")

    prior_review = dict(record["review"])
    record["review"] = {
        "required": True, "provider": "codex",
        "status": "WAIVED_BY_USER_FOR_ONE_NAMESPACED_CACHE_REPAIR_RUN",
        "verdict": "NO_PASS", "reason": AUTHORIZATION,
        "failed_review": prior_review, "at_utc": utc_now(),
    }
    record["smoke_test"] = {
        "status": "PASSED", "type": "namespaced_cache_preflight_and_unchanged_science",
        "receipt": f"experiments/{EXPERIMENT_ID}/authorized-repair-smoke.json",
        "at_utc": utc_now(),
    }
    record["state"] = "READY"
    record.setdefault("state_history", []).append({
        "from": "MANUAL_REVIEW_REQUIRED", "to": "READY", "at": utc_now(),
        "note": "User-authorized namespaced-cache repair; formal Codex PASS absent",
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
        metadata = json.loads((kernel_dir / "kernel-metadata.json").read_text(encoding="utf-8"))
        generated_checks = {
            "dataset_sources": metadata.get("dataset_sources") == EXPECTED_DATASETS,
            "competition_sources": metadata.get("competition_sources") == EXPECTED_COMPETITIONS,
            "kernel_sources": metadata.get("kernel_sources") == EXPECTED_KERNELS,
            "docker_image": metadata.get("docker_image") == EXPECTED_DOCKER,
        }
        receipt["generated_kernel_dir"] = str(kernel_dir.relative_to(ROOT))
        receipt["generated_metadata"] = metadata
        receipt["generated_metadata_checks"] = generated_checks
        write_json(receipt_path, receipt)
        if not all(generated_checks.values()):
            raise ControllerError(f"Generated metadata mismatch: {generated_checks}")
        args = ["kernels", "push", "-p", str(kernel_dir)]
        if config["kaggle"].get("accelerator"):
            args += ["--accelerator", str(config["kaggle"]["accelerator"])]
        push = _run_kaggle(ROOT, EXPERIMENT_ID, args, "kaggle-launch.log")
    except Exception:
        unwind("Pre-push failure in diag078 namespaced-cache repair")
        raise
    if push.returncode:
        unwind("Kaggle push failed in diag078 namespaced-cache repair")
        raise ControllerError("Kaggle push failed; see kaggle-launch.log")

    record = load_record(ROOT, EXPERIMENT_ID)
    record["remote"] = {
        "kernel_id": kernel_id, "submitted_at": utc_now(), "status": "SUBMITTED",
        "last_checked_at": None, "launch_mode": "user_authorized_namespaced_cache_repair_no_pass",
    }
    transition(ROOT, record, "SUBMITTED", note="One user-authorized cache-path repair; no LB submission")
    print(json.dumps({"experiment": EXPERIMENT_ID, "remote": record["remote"],
                      "metadata_checks": generated_checks, "stdout": push.stdout}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
