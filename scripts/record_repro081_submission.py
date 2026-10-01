"""Record the user-authorized repro081 code submission after the three frozen audits passed."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_ID = 56676153
EXPERIMENT_ID = "repro_081_kunal_runtime_receipt"
SHA256 = "e424b8c4feadc8d5520d71985ed8f20722e49bab17cd469f543e04681fc8a978"
SUBMITTED_AT = "2026-09-29T12:59:45.367000Z"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


ledger_path = ROOT / "SUBMISSION_BUDGET.json"
ledger = load(ledger_path)
if not any(row.get("submission_id") == SUBMISSION_ID for row in ledger["submissions"]):
    ledger["submissions"].append({
        "local_date": "2026-09-29",
        "gate_checked_at_utc": "2026-09-29T12:58:51+00:00",
        "submitted_at_utc": SUBMITTED_AT,
        "competition": "biohub-cell-tracking-during-development",
        "submission_id": SUBMISSION_ID,
        "experiment_id": EXPERIMENT_ID,
        "kernel": "lingxd/biohub-repro081-kunal-receipt",
        "kernel_version": 1,
        "file_name": "submission.csv",
        "submission_sha256": SHA256,
        "status": "PENDING",
        "public_score": None,
        "submit_method": "competition_submit_code (kernel v1, output submission.csv)",
        "gate_verdict": {
            "allowed": True,
            "cap_platform": 5,
            "remote_today_before_submit": 0,
            "local_today_before_submit": 0,
            "remaining_platform_after_submit": 4,
            "duplicate_output": False,
        },
        "remote_history_checked_before_submit": True,
        "user_authorized": True,
        "review_status": "Independent Codex admission PASS (delta round 1) and snapshot smoke PASS were recorded before launch.",
        "integrity": (
            "Kernel COMPLETE. All three frozen gates PASS: sweep-receipt audit "
            "(8 held-out TRAIN stems, 4+4 prefixes, 15 candidates, selection rule recomputed, "
            "no TEST overlap, no fallback degradation, selected dcsafediv020), runtime-receipt audit "
            "(validator effective, selected overrides equal effective globals during the final TEST "
            "write, artifact hashes bind selected write to final output), and structural output audit "
            "(238308 rows, 121232 nodes, 117076 edges, four expected TEST datasets, no errors)."
        ),
        "rationale": (
            "User explicitly requested this leaderboard submission after the repro081 run completed. "
            "Kunal's pipeline is the only plausible updated public candidate; its selected "
            "DEEPCENTER_SAFE_DIV_THRESHOLD=0.2 arm is a genuine LB probe against the retained "
            "exp064 0.953."
        ),
    })
save(ledger_path, ledger)

experiment_path = ROOT / "experiments" / EXPERIMENT_ID / "experiment.json"
experiment = load(experiment_path)
experiment["remote"]["status"] = "COMPLETE"
experiment["remote"]["last_checked_at"] = "2026-09-29T12:54:11+00:00"
experiment["manual_collection"] = {
    "collected_at": "2026-09-29T12:56:00+00:00",
    "note": (
        "scripts/collect_results.py downloaded the full remote output but exited non-zero because a "
        "public-source reproduction writes no controller metrics.json. Artifacts are complete under "
        "experiments/repro_081_kunal_runtime_receipt/artifacts. Collected exactly once."
    ),
    "submission_sha256": SHA256,
}
experiment["audits"] = {
    "sweep_receipts": {"script": "scripts/audit_repro080_sweep_receipts.py", "status": "PASS",
                       "output": "experiments/repro_081_kunal_runtime_receipt/audits/sweep_receipts.json",
                       "source_notebook": ".private/current/repro079_kunal_public/biohub-cell-tracking.ipynb",
                       "selected": "dcsafediv020"},
    "runtime_receipt": {"script": "scripts/audit_repro081_runtime_receipt.py", "status": "PASS",
                        "output": "experiments/repro_081_kunal_runtime_receipt/audits/runtime_receipt.json"},
    "structural_output": {"script": "scripts/audit_repro079_output.py", "status": "PASS",
                          "output": "experiments/repro_081_kunal_runtime_receipt/audits/structural_output.json"},
}
experiment["leaderboard_submission"] = {
    "authorized_by_user": True,
    "submission_id": SUBMISSION_ID,
    "submitted_at": SUBMITTED_AT,
    "status": "PENDING",
    "submission_sha256": SHA256,
    "kernel_version": 1,
    "note": "All three frozen audits PASS before submission; score pending.",
}
save(experiment_path, experiment)

state_path = ROOT / "STATE.json"
state = load(state_path)
state["phase"] = "REPRO081_COMPLETE_AUDITS_PASS_LB_SUBMITTED_PENDING_DIAG_BRANCH_PAUSED"
state["repro081_submission"] = {
    "submission_id": SUBMISSION_ID,
    "status": "PENDING",
    "submitted_at_utc": SUBMITTED_AT,
    "submission_sha256": SHA256,
    "kernel": "lingxd/biohub-repro081-kunal-receipt",
    "kernel_version": 1,
    "note": (
        "User-authorized LB probe of the completed Kunal reproduction. Kernel COMPLETE, output "
        "collected once, and the sweep-receipt, runtime-receipt and structural-output audits all "
        "PASS. Selected candidate dcsafediv020. Retained best remains exp064 56535761 at 0.953 "
        "unless this scores higher."
    ),
}
state["updated_at"] = "2026-09-29T13:00:00+00:00"
save(state_path, state)
print("recorded", SUBMISSION_ID)
