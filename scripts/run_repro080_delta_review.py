"""Run repro080's single delta-only Codex admission review without filesystem tools."""

from __future__ import annotations

import json
import subprocess

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError, load_record, save_record, transition, utc_now
from experiment_controller.review import VERDICT_RE, codex_command


EXPERIMENT_ID = "repro_080_kunal_public_verbatim_admission_repair"


def main() -> int:
    root = PROJECT_ROOT
    record = load_record(root, EXPERIMENT_ID)
    if record["state"] != "MANUAL_REVIEW_REQUIRED" or record.get("review", {}).get("verdict") != "REVISE":
        raise ControllerError("Expected the preserved initial REVISE state")
    exp_dir = root / "experiments" / EXPERIMENT_ID
    prior = (exp_dir / "review.md").read_text(encoding="utf-8")
    delta = (exp_dir / "admission_delta_round1.md").read_text(encoding="utf-8")
    exception = (exp_dir / "tier_b_exception.md").read_text(encoding="utf-8")
    checker = (root / "scripts/audit_repro080_sweep_receipts.py").read_text(encoding="utf-8")
    prompt = f"""Perform the one allowed delta-only independent Codex review for repro080.
Do not call tools or inspect files. Decide only whether F1 and F2 are closed by the supplied
delta; do not reopen unrelated history unless the delta introduces a concrete safety defect.
Return concise Markdown and end with exactly VERDICT: PASS, VERDICT: REVISE, or VERDICT: BLOCK.

--- PRIOR FINDINGS ---
{prior}
--- DELTA ---
{delta}
--- USER EXCEPTION RECORD ---
{exception}
--- SWEEP RECEIPT CHECKER ---
{checker}
--- END ---
"""
    result = subprocess.run(codex_command(), cwd=root, text=True, encoding="utf-8",
                            errors="replace", input=prompt, capture_output=True, check=False)
    (exp_dir / "codex-prompt-delta-round1.md").write_text(prompt, encoding="utf-8")
    (exp_dir / "codex-review-run-delta-round1.json").write_text(json.dumps({
        "provider": "codex", "command": codex_command(), "exit_code": result.returncode,
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
        "prior_review": f"experiments/{EXPERIMENT_ID}/review.md",
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
