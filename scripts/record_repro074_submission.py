"""Record the user-authorized repro074 code submission after remote acceptance."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_ID = 56650147
EXPERIMENT_ID = "repro_074_amanatar_claimed_0965_verbatim"
SHA256 = "cfd8690d9f9c33582976f9fbae25b63114d3db93e55c8e9751766c8831d727c2"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


ledger_path = ROOT / "SUBMISSION_BUDGET.json"
ledger = load(ledger_path)
if not any(row.get("submission_id") == SUBMISSION_ID for row in ledger["submissions"]):
    ledger["submissions"].append({
        "local_date": "2026-09-28",
        "gate_checked_at_utc": "2026-09-28T19:04:27+00:00",
        "submitted_at_utc": "2026-09-28T19:05:25.007000Z",
        "competition": "biohub-cell-tracking-during-development",
        "submission_id": SUBMISSION_ID,
        "experiment_id": EXPERIMENT_ID,
        "kernel": "lingxd/biohub-repro074-amanatar-0965-verbatim",
        "kernel_version": 1,
        "file_name": "submission.csv",
        "submission_sha256": SHA256,
        "status": "PENDING",
        "public_score": None,
        "submit_method": "competition_submit_code (kernel v1, output submission.csv)",
        "gate_verdict": {
            "allowed": True,
            "cap_conservative": 3,
            "cap_platform": 5,
            "remote_today_before_submit": 0,
            "local_today_before_submit": 0,
            "remaining_platform_after_submit": 4,
            "duplicate_output": False,
        },
        "remote_history_checked_before_submit": True,
        "user_authorized": True,
        "review_status": "NO_CODEX_PASS. The byte-verbatim reproduction kernel ran under a one-time user waiver; the user separately authorized this LB submission after collection.",
        "integrity": "Kernel COMPLETE. Structural CSV audit PASS: 240311 rows, 123684 nodes, 116627 edges, four expected datasets, no structural errors.",
        "runtime_caveat": "All four advanced repair calls raised NameError for SAFE_DIV_HORIZON_FRAMES and fell back to basic-filtered ILP graphs. This submission tests the notebook's actual fallback output, not the advertised complete 0.965 mechanism.",
        "rationale": "User explicitly requested one LB submission of the completed public 0.965-claim notebook reproduction; output is non-duplicate and structurally valid.",
    })
save(ledger_path, ledger)

experiment_path = ROOT / "experiments" / EXPERIMENT_ID / "experiment.json"
experiment = load(experiment_path)
experiment["leaderboard_submission"] = {
    "authorized_by_user": True,
    "submission_id": SUBMISSION_ID,
    "submitted_at": "2026-09-28T19:05:25.007000Z",
    "status": "PENDING",
    "submission_sha256": SHA256,
    "kernel_version": 1,
    "runtime_caveat": "Advanced repair failed with SAFE_DIV_HORIZON_FRAMES NameError on all four datasets; fallback output submitted.",
}
save(experiment_path, experiment)

state_path = ROOT / "STATE.json"
state = load(state_path)
state["repro074_submission"] = {
    "submission_id": SUBMISSION_ID,
    "status": "PENDING",
    "submitted_at_utc": "2026-09-28T19:05:25.007000Z",
    "submission_sha256": SHA256,
    "note": "User-authorized LB submission of actual byte-verbatim notebook output. Structural audit PASS; advanced repair fell back on all four datasets due undefined SAFE_DIV_HORIZON_FRAMES, so the 0.965 claim is not reproduced by mechanism integrity alone.",
}
state["updated_at"] = "2026-09-28T19:05:25+00:00"
save(state_path, state)
