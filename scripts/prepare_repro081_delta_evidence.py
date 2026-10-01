from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import (
    ControllerError,
    load_record,
    reserve_budget,
    save_record,
    utc_now,
    write_json,
)


EXPERIMENT_ID = "repro_081_kunal_runtime_receipt"
PUBLIC_OUTPUT = Path(os.environ.get("REPRO081_PUBLIC_OUTPUT", Path(tempfile.gettempdir()) / "kunal_biohub_output_20260929"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout[-8000:],
        "stderr": result.stderr[-8000:],
    }


def main() -> int:
    root = PROJECT_ROOT
    record = load_record(root, EXPERIMENT_ID)
    if record["state"] != "MANUAL_REVIEW_REQUIRED" or record.get("review", {}).get("verdict") != "REVISE":
        raise ControllerError("Expected initial substantive REVISE")
    if not PUBLIC_OUTPUT.exists():
        raise ControllerError(f"Public fixture directory missing: {PUBLIC_OUTPUT}")
    exp_dir = root / "experiments" / EXPERIMENT_ID
    extras = exp_dir / "snapshot" / "extra_files"
    source = root / record["snapshot_source"]
    upstream = root / "experiments/repro_080_kunal_public_verbatim_admission_repair/snapshot/source/biohub-cell-tracking.ipynb"
    commands = [
        [sys.executable, str(extras / "smoke_repro081.py"), str(upstream), str(source)],
        [sys.executable, str(extras / "test_repro081_runtime_receipt.py"), str(PUBLIC_OUTPUT), str(source)],
    ]
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        commands.extend([
            [sys.executable, str(extras / "audit_repro080_sweep_receipts.py"), str(PUBLIC_OUTPUT), str(upstream), "--output", str(temp_root / "sweep.json")],
            [sys.executable, str(extras / "audit_repro079_output.py"), str(PUBLIC_OUTPUT / "submission.csv"), "--output", str(temp_root / "output.json")],
        ])
        checks = [run(command) for command in commands]
    receipt = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "at_utc": utc_now(),
        "snapshot_source_sha256": digest(source),
        "upstream_source_sha256": digest(upstream),
        "public_fixture_hashes": {
            name: digest(PUBLIC_OUTPUT / name)
            for name in ("ppsweep_selected.json", "ppsweep_results.csv", "run_stats.csv", "submission.csv")
        },
        "checks": checks,
        "all_passed": all(check["returncode"] == 0 for check in checks),
    }
    receipt_path = exp_dir / "admission_test_receipts.json"
    write_json(receipt_path, receipt)
    if not receipt["all_passed"]:
        raise ControllerError("A repro081 deterministic admission test failed")

    if not record.get("budget", {}).get("reserved"):
        reserve_budget(root, EXPERIMENT_ID, 3.0)
        record = load_record(root, EXPERIMENT_ID)
        record["budget"]["reserved"] = True
    budget = json.loads((root / "GPU_BUDGET.json").read_text(encoding="utf-8"))
    reservations = budget.get("reserved_hours", {})
    if reservations.get(EXPERIMENT_ID) != 3.0:
        raise ControllerError("repro081 3.0-hour reservation missing")
    if reservations.get("diag_078_fork_protected_namespaced_cache") != 1.0:
        raise ControllerError("diag078 concurrent 1.0-hour reservation missing")
    record["authorization"] = {
        "tier_b_exception": True,
        "user_approved_at_context": "2026-09-29",
        "scope": "One prediction-neutral receipt-instrumented private repro081 run; no retry or leaderboard submission.",
        "parent_exception": "User directed repro081 continuation after repro080 remained unlaunched solely for missing effective-runtime receipts. Repro081 preserves all repro080 findings already closed and supersedes that unlaunched parent.",
    }
    record["admission_evidence"] = {
        "test_receipt": receipt_path.relative_to(root).as_posix(),
        "tests_passed": True,
        "budget_receipt": {
            "remaining_hours": budget["remaining_hours"],
            "reservations": {
                "diag_078_fork_protected_namespaced_cache": reservations["diag_078_fork_protected_namespaced_cache"],
                EXPERIMENT_ID: reservations[EXPERIMENT_ID],
            },
            "remaining_after_reservations": budget["remaining_hours"] - sum(float(value) for value in reservations.values()),
        },
    }
    save_record(root, record)
    print(json.dumps({"tests": receipt["all_passed"], "budget": record["admission_evidence"]["budget_receipt"], "authorization": record["authorization"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
