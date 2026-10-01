"""One delta-only Codex admission review for repro079 findings."""

from __future__ import annotations

import json
import subprocess

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError, load_record, save_record, transition, utc_now
from experiment_controller.review import VERDICT_RE, codex_command


EXPERIMENT_ID = "repro_079_kunal_public_verbatim"


def main() -> int:
    root = PROJECT_ROOT
    record = load_record(root, EXPERIMENT_ID)
    if record["state"] != "MANUAL_REVIEW_REQUIRED":
        raise ControllerError(f"Expected MANUAL_REVIEW_REQUIRED, got {record['state']}")
    if record.get("review", {}).get("verdict") != "REVISE":
        raise ControllerError("Delta review requires the preserved REVISE verdict")
    prior = (root / f"experiments/{EXPERIMENT_ID}/review_round2.md").read_text(encoding="utf-8")
    delta = (root / f"experiments/{EXPERIMENT_ID}/admission_delta_round1.md").read_text(encoding="utf-8")
    source_audit = (root / "scripts/audit_repro079_source_delta.py").read_text(encoding="utf-8")
    output_audit = (root / "scripts/audit_repro079_output.py").read_text(encoding="utf-8")
    base_audit = (root / "scripts/audit_biohub_submission_csv.py").read_text(encoding="utf-8")
    prompt = f"""You are performing the one allowed delta-only independent Codex review.
Do not call tools or inspect files. Review only whether the two prior findings are fully closed
by the supplied delta. Do not reopen unrelated historical issues unless the delta introduces a
new concrete correctness, leakage, provenance, output-contract, or budget defect. End with exactly
VERDICT: PASS, VERDICT: REVISE, or VERDICT: BLOCK on its own line.

--- PRIOR FINDINGS ONLY ---
{prior}
--- DELTA EVIDENCE ---
{delta}
--- SOURCE DELTA CHECKER ---
{source_audit}
--- OUTPUT CONTRACT WRAPPER ---
{output_audit}
--- BASE STRUCTURAL AUDITOR USED BY WRAPPER ---
{base_audit}
--- END DELTA ---
"""
    result = subprocess.run(
        codex_command(), cwd=root, text=True, encoding="utf-8", errors="replace",
        input=prompt, capture_output=True, check=False,
    )
    exp_dir = root / "experiments" / EXPERIMENT_ID
    (exp_dir / "codex-prompt-delta-round1.md").write_text(prompt, encoding="utf-8")
    (exp_dir / "codex-review-run-delta-round1.json").write_text(
        json.dumps({"provider": "codex", "command": codex_command(),
                    "exit_code": result.returncode, "stderr": result.stderr,
                    "completed_at": utc_now(), "mode": "tool_free_delta_only"},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
        "prior_review": f"experiments/{EXPERIMENT_ID}/review_round2.md",
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
