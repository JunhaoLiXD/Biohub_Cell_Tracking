"""Run the one-time, read-only post-run review authorized for repro_041."""
from __future__ import annotations

import json
import re
import subprocess

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import command_prefix, utc_now, write_json


EXPERIMENT = "repro_041_public_0941_motion_ema"
VERDICT_RE = re.compile(r"(?im)^\s*VERDICT\s*:\s*(PASS|REVISE|BLOCK)\s*$")


def main() -> int:
    root = PROJECT_ROOT
    exp_dir = root / "experiments" / EXPERIMENT
    receipt_path = exp_dir / "post-run-review.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not receipt.get("required") or not str(receipt.get("status", "")).startswith("PENDING"):
        raise RuntimeError(f"Post-run review is not pending: {receipt.get('status')}")

    prompt = f"""You are the independent final reviewer for one completed Kaggle cell-tracking reproduction.

Work read-only. Do not edit or create files and do not run commands that change state.
Review only `{EXPERIMENT}` under the one-time scope described in
`experiments/{EXPERIMENT}/post-run-review-instructions.md`.

Read the required evidence listed in that instruction file, including GOAL.md,
.private/current/CONTINUATION.md, both experiment records/manifests and raw artifacts,
and `.private/research/repro041_completed_analysis_2026-09-06.md`. Independently verify:

1. aggregate and specimen metrics match exp_040 within absolute tolerance 1e-12 and zero relative tolerance;
2. division counts and EMA telemetry match exactly;
3. submission bytes and graph audit match exactly;
4. inference, validation samples/order, checkpoint identity, and runtime health are frozen and valid;
5. the interpretation is honest: repeatability is established, not generalization or leaderboard gain.

Return concise Markdown with sections Summary, Evidence, Limitations, and Recommendation.
End with exactly one line: VERDICT: PASS, VERDICT: REVISE, or VERDICT: BLOCK.
PASS supports discussing a leaderboard submission; it is not submission authorization.
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
    (exp_dir / "post-run-claude-prompt.md").write_text(prompt, encoding="utf-8")
    write_json(
        exp_dir / "post-run-claude-review-run.json",
        {
            "command": command,
            "exit_code": result.returncode,
            "stderr": result.stderr,
            "completed_at": completed_at,
        },
    )
    if result.returncode != 0:
        receipt.update({"status": "FAILED", "verdict": None, "completed_at": completed_at})
        write_json(receipt_path, receipt)
        return result.returncode or 1

    review_text = result.stdout.strip() + "\n"
    (exp_dir / "post-run-review.md").write_text(review_text, encoding="utf-8")
    match = VERDICT_RE.search(review_text)
    verdict = match.group(1) if match else "MISSING"
    receipt.update(
        {
            "status": "PASSED" if verdict == "PASS" else "CHANGES_REQUESTED",
            "verdict": verdict,
            "completed_at": completed_at,
            "exit_code": result.returncode,
        }
    )
    write_json(receipt_path, receipt)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
