from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .core import (
    ControllerError,
    command_prefix,
    experiment_dir,
    load_record,
    save_record,
    transition,
    utc_now,
)


VERDICT_RE = re.compile(r"(?im)^\s*VERDICT\s*:\s*(PASS|REVISE|BLOCK)\s*$")


def claude_command() -> list[str]:
    return command_prefix("claude", env_name="CLAUDE_COMMAND")


def build_review_prompt(root: Path, record: dict[str, Any]) -> str:
    experiment_id = str(record["experiment_id"])
    parent_id = str(record.get("parent") or "")
    parent_context = []
    if parent_id:
        for relative in (
            f"experiments/{parent_id}/experiment.json",
            f"experiments/{parent_id}/metrics.json",
        ):
            if (root / relative).exists():
                parent_context.append(relative)
    optional_context = [
        "research/PUBLIC_SOLUTIONS.md",
        "research/BASELINE_CANDIDATES.md",
        ".private/automation/agent_quota_policy.json",
        ".private/research/public_solution_review_2026-08-31.md",
        ".private/archive/docs/v9_division_aware_tracking_plan.md",
        ".private/archive/docs/optimization_audit.md",
    ]
    context_paths = [*parent_context, *[path for path in optional_context if (root / path).exists()]]
    context_list = "\n".join(f"- {path}" for path in context_paths)
    return f"""You are the independent research reviewer for a Kaggle cell-tracking project.

Work read-only. Do not edit or create files and do not run commands that change state.

Review experiment: {experiment_id}

Read these project files:
- GOAL.md
- AGENTS.md
- CURRENT_BEST.json
- GPU_BUDGET.json
- results.json
- EXPERIMENTS.md
- {record['snapshot_config']}
- {record['snapshot_source']}
{context_list}

Also inspect the current git diff read-only if available.

Conserve the user's weekly Claude allowance: inspect only the cells relevant to configuration,
dependencies, graph audit, validation, and the final metrics contract. Do not load or restate the
entire notebook when targeted searches are sufficient.

Evaluate:
1. Is the hypothesis testable and attributable to one major variable?
2. Is the validation protocol trustworthy, including leakage and the 44b6/6bba domain split?
3. Are there likely implementation bugs or missing output-contract fields?
4. Does the implementation preserve the claimed upstream algorithm, and do its runtime guards
   verify the effective configuration rather than stale notebook prose?
5. Is the experiment duplicate or already contradicted by history?
6. Is expected information gain worth the GPU cost?
7. Does the parent result logically justify this next experiment, and are the stated reasons for
   the change supported by the recorded evidence?
8. What concrete changes are required before launch?

Return concise Markdown with sections: Summary, Methodology, Implementation risks, Budget,
Required changes, and Recommendation. End with exactly one line:

VERDICT: PASS

or VERDICT: REVISE / VERDICT: BLOCK. PASS means safe to proceed to the next controller stage
(local smoke testing or remote launch, depending on current state); it is not a claim that the
hypothesis will win.
"""


def request_review(root: Path, experiment_id: str) -> dict[str, Any]:
    record = load_record(root, experiment_id)
    if record["state"] not in {"PROPOSED", "MANUAL_REVIEW_REQUIRED", "READY"}:
        raise ControllerError(
            f"Claude review must happen before remote submission; current state is {record['state']}"
        )
    prompt = build_review_prompt(root, record)
    command = [*claude_command(), "--print", "--permission-mode", "plan", "--output-format", "text"]
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
    exp_dir = experiment_dir(root, experiment_id)
    (exp_dir / "claude-prompt.md").write_text(prompt, encoding="utf-8")
    log = {
        "command": command,
        "exit_code": result.returncode,
        "stderr": result.stderr,
        "completed_at": utc_now(),
    }
    (exp_dir / "claude-review-run.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if result.returncode != 0:
        record["review"] = {
            "required": record.get("review", {}).get("required", False),
            "status": "FAILED",
            "completed_at": utc_now(),
            "exit_code": result.returncode,
        }
        save_record(root, record)
        raise ControllerError(
            f"Claude review command failed for {experiment_id}; see claude-review-run.json"
        )

    review_text = result.stdout.strip() + "\n"
    (exp_dir / "review.md").write_text(review_text, encoding="utf-8")
    (root / "CLAUDE_REVIEW.md").write_text(
        f"# Latest Claude Review\n\nExperiment: `{experiment_id}`  \nCaptured: {utc_now()}\n\n{review_text}",
        encoding="utf-8",
    )
    match = VERDICT_RE.search(review_text)
    verdict = match.group(1) if match else "MISSING"
    record = load_record(root, experiment_id)
    record["review"] = {
        "required": record.get("review", {}).get("required", False),
        "status": "PASSED" if verdict == "PASS" else "CHANGES_REQUESTED",
        "verdict": verdict,
        "path": (exp_dir / "review.md").relative_to(root).as_posix(),
        "completed_at": utc_now(),
    }
    save_record(root, record)
    if verdict == "PASS" and record["state"] != "READY":
        transition(root, record, "REVIEWED")
    else:
        if verdict != "PASS" and record["state"] in {"PROPOSED", "READY"}:
            transition(root, record, "MANUAL_REVIEW_REQUIRED", note=f"Claude verdict: {verdict}")
        if verdict != "PASS":
            raise ControllerError(f"Claude review did not pass: VERDICT={verdict}")
    return record
