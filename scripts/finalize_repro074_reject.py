"""Finalize authenticated repro074 Public LB 0.901 as terminal REJECT."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "repro_074_amanatar_claimed_0965_verbatim"
SUBMISSION_ID = 56650147
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


ledger_path = ROOT / "SUBMISSION_BUDGET.json"
ledger = load(ledger_path)
row = next(item for item in ledger["submissions"] if item.get("submission_id") == SUBMISSION_ID)
row.update({
    "status": "COMPLETE",
    "public_score": 0.901,
    "score_source": "authenticated kaggle competitions submissions",
    "score_verified_at_utc": NOW,
    "delta_vs_retained_0953": -0.052,
    "delta_vs_claimed_0965": -0.064,
    "verdict": "REJECT_CLOSE_PUBLIC_0965_CLAIM: retain exp064 at 0.953; no repair, rerun, resubmission, promotion, or derivative from this notebook.",
})
save(ledger_path, ledger)

experiment_path = ROOT / "experiments" / EXPERIMENT_ID / "experiment.json"
experiment = load(experiment_path)
previous = experiment["state"]
experiment["state"] = "REJECT"
experiment["updated_at"] = NOW
experiment["leaderboard_submission"].update({
    "status": "COMPLETE", "public_score": 0.901,
    "score_verified_at": NOW, "verdict": "REJECT",
})
experiment.setdefault("state_history", []).append({
    "from": previous, "to": "REJECT", "at": NOW,
    "note": "Authenticated Public LB 0.901; user instructed to discard this branch",
})
save(experiment_path, experiment)

state_path = ROOT / "STATE.json"
state = load(state_path)
state["repro074_submission"].update({
    "status": "COMPLETE", "public_score": 0.901,
    "score_verified_at_utc": NOW, "verdict": "REJECT",
    "note": "Authenticated Public LB 0.901, -0.052 versus retained exp064 0.953. User closed and discarded this public-notebook branch. Preserve artifacts as negative evidence; no repair, rerun, resubmission, promotion, or derivative.",
})
state["updated_at"] = NOW
save(state_path, state)
