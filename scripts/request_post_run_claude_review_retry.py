"""Run the explicitly user-authorized format-correction review for repro_041."""
from __future__ import annotations

import json
import re
import subprocess

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import command_prefix, utc_now, write_json


EXPERIMENT = "repro_041_public_0941_motion_ema"
RETRY = "retry-01"
VERDICT_RE = re.compile(r"(?im)^\s*VERDICT\s*:\s*(PASS|REVISE|BLOCK)\s*$")


def main() -> int:
    root = PROJECT_ROOT
    exp_dir = root / "experiments" / EXPERIMENT
    receipt_path = exp_dir / "post-run-review.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("verdict") != "MISSING" or receipt.get("status") != "CHANGES_REQUESTED":
        raise RuntimeError("The format-correction review is only valid after the recorded MISSING verdict")
    retry_receipt = exp_dir / f"post-run-review-{RETRY}.json"
    if retry_receipt.exists():
        raise RuntimeError(f"Refusing to repeat an existing review retry: {retry_receipt}")

    prompt = f"""Perform a narrowly scoped, read-only final review of `{EXPERIMENT}`.

The user explicitly authorized this single retry because the prior review substantively said PASS
but omitted the mandatory machine-readable final verdict line. Do not edit files. Do not ask for
permission to persist anything. Do not enter or exit plan mode. Inspect the evidence directly and
return the complete review in this response.

Read:
- experiments/{EXPERIMENT}/post-run-review-instructions.md
- experiments/{EXPERIMENT}/post-run-review.md (the prior format-failed review)
- GOAL.md and .private/current/CONTINUATION.md
- both repro_041 and exp_040 experiment records, manifests, metrics, raw validator CSV,
  inference identity, validation stage statistics, submission hashes/graph audits, and runtime logs
- .private/research/repro041_completed_analysis_2026-09-06.md

Verify exact aggregate/specimen metrics at absolute tolerance 1e-12 and zero relative tolerance,
exact division counts and EMA telemetry, byte-identical submission and result-bearing artifacts,
frozen inference/validation/checkpoint identity, runtime health, and the honest repeatability-only
interpretation. PASS does not authorize a leaderboard submission by itself.

Return concise Markdown with sections Summary, Evidence, Limitations, and Recommendation.
Your response MUST end with exactly one unformatted line and no text after it, choosing one of:
VERDICT: PASS
VERDICT: REVISE
VERDICT: BLOCK
"""
    command = [
        *command_prefix("claude", env_name="CLAUDE_COMMAND"),
        "--print",
        "--permission-mode",
        "plan",
        "--output-format",
        "text",
    ]
    result = subprocess.run(
        command,
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        input=prompt,
        capture_output=True,
        check=False,
    )
    completed_at = utc_now()
    (exp_dir / f"post-run-claude-prompt-{RETRY}.md").write_text(prompt, encoding="utf-8")
    write_json(
        retry_receipt,
        {
            "schema_version": 1,
            "experiment_id": EXPERIMENT,
            "retry": RETRY,
            "reason": "Explicit user-authorized retry after a substantive PASS omitted the required verdict line",
            "command": command,
            "exit_code": result.returncode,
            "stderr": result.stderr,
            "completed_at": completed_at,
        },
    )
    if result.returncode != 0:
        return result.returncode or 1

    review_text = result.stdout.strip() + "\n"
    review_path = exp_dir / f"post-run-review-{RETRY}.md"
    review_path.write_text(review_text, encoding="utf-8")
    match = VERDICT_RE.search(review_text)
    verdict = match.group(1) if match else "MISSING"
    retry_data = json.loads(retry_receipt.read_text(encoding="utf-8"))
    retry_data.update({"verdict": verdict, "review_path": review_path.relative_to(root).as_posix()})
    write_json(retry_receipt, retry_data)

    history = list(receipt.get("retry_history") or [])
    history.append(
        {
            "retry": RETRY,
            "authorized_by": "user",
            "completed_at": completed_at,
            "verdict": verdict,
            "review_path": review_path.relative_to(root).as_posix(),
            "receipt_path": retry_receipt.relative_to(root).as_posix(),
        }
    )
    receipt.update(
        {
            "status": "PASSED" if verdict == "PASS" else "CHANGES_REQUESTED",
            "verdict": verdict,
            "review_path": review_path.relative_to(root).as_posix(),
            "completed_at": completed_at,
            "retry_history": history,
        }
    )
    write_json(receipt_path, receipt)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
