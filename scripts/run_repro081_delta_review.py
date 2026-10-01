"""Single delta-only Codex review for repro081."""

from __future__ import annotations

import json
import subprocess

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError, load_record, save_record, transition, utc_now
from experiment_controller.review import VERDICT_RE, codex_command


EXPERIMENT_ID = "repro_081_kunal_runtime_receipt"


def main() -> int:
    root = PROJECT_ROOT
    record = load_record(root, EXPERIMENT_ID)
    if record["state"] != "MANUAL_REVIEW_REQUIRED" or record.get("review", {}).get("verdict") != "REVISE":
        raise ControllerError("Expected initial substantive REVISE")
    exp_dir = root / "experiments" / EXPERIMENT_ID
    parts = {
        "prior_findings": (exp_dir / "review_selfcontained.md").read_text(encoding="utf-8"),
        "delta": (exp_dir / "admission_delta_round1.md").read_text(encoding="utf-8"),
        "test_receipts": (exp_dir / "admission_test_receipts.json").read_text(encoding="utf-8"),
        "experiment_record": (exp_dir / "experiment.json").read_text(encoding="utf-8"),
        "budget": (root / "GPU_BUDGET.json").read_text(encoding="utf-8"),
    }
    prompt = """Perform repro081's one allowed delta-only independent Codex review.
Do not call tools or inspect files. Decide only whether R081-TEST-001, R081-BUDGET-001,
and R081-PARENT-001 are closed by the supplied evidence. Do not reopen unrelated history
unless this delta introduces a concrete correctness or safety defect. Return concise Markdown
and end with exactly VERDICT: PASS, VERDICT: REVISE, or VERDICT: BLOCK.

""" + "\n".join(f"--- {name.upper()} ---\n{text}" for name, text in parts.items())
    command = codex_command()
    result = subprocess.run(command, cwd=root, text=True, encoding="utf-8", errors="replace",
                            input=prompt, capture_output=True, check=False)
    (exp_dir / "codex-prompt-delta-round1.md").write_text(prompt, encoding="utf-8")
    (exp_dir / "codex-review-run-delta-round1.json").write_text(json.dumps({
        "provider": "codex", "command": command, "exit_code": result.returncode,
        "stderr": result.stderr, "completed_at": utc_now(), "mode": "tool_free_delta_only",
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if result.returncode:
        raise ControllerError("Delta-only Codex review command failed")
    review_text = result.stdout.strip() + "\n"
    review_path = exp_dir / "review_delta_round1.md"
    review_path.write_text(review_text, encoding="utf-8")
    match = VERDICT_RE.search(review_text)
    verdict = match.group(1) if match else "MISSING"
    record = load_record(root, EXPERIMENT_ID)
    record["review"] = {
        "required": True, "provider": "codex",
        "status": "PASSED" if verdict == "PASS" else "CHANGES_REQUESTED",
        "verdict": verdict, "path": review_path.relative_to(root).as_posix(),
        "completed_at": utc_now(), "mode": "tool_free_delta_only",
        "prior_review": f"experiments/{EXPERIMENT_ID}/review_selfcontained.md",
        "delta": f"experiments/{EXPERIMENT_ID}/admission_delta_round1.md",
    }
    save_record(root, record)
    if verdict == "PASS":
        transition(root, record, "REVIEWED", note="Independent delta-only Codex PASS")
    else:
        raise ControllerError(f"Delta-only Codex review did not pass: {verdict}")
    print(review_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
