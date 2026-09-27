from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .core import (
    ControllerError,
    command_prefix,
    configured_review_provider,
    experiment_dir,
    load_config,
    load_record,
    REVIEW_PROVIDERS,
    save_record,
    transition,
    utc_now,
)


VERDICT_RE = re.compile(r"(?im)^\s*VERDICT\s*:\s*(PASS|REVISE|BLOCK)\s*$")
MAX_TIER_B_REVIEW_PACKET_BYTES = 15 * 1024


def claude_command() -> list[str]:
    return command_prefix("claude", env_name="CLAUDE_COMMAND")


def codex_command() -> list[str]:
    """Build the explicitly read-only Codex CLI invocation."""
    return [
        *command_prefix("codex", env_name="CODEX_COMMAND"),
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "-",
    ]


def _review_provider(root: Path, record: dict[str, Any]) -> str:
    review = record.get("review") or {}
    recorded = str(review.get("provider") or "").strip().lower()
    if recorded in REVIEW_PROVIDERS:
        return recorded
    _, config = load_config(root / str(record["snapshot_config"]), root)
    return configured_review_provider(config)


def build_review_prompt(root: Path, record: dict[str, Any]) -> str:
    experiment_id = str(record["experiment_id"])
    parent_id = str(record.get("parent") or "")
    _, config = load_config(root / str(record["snapshot_config"]), root)
    workflow = config.get("workflow") or {}
    risk_tier = str(workflow.get("risk_tier") or "C").strip().upper()
    if risk_tier not in {"B", "C"}:
        risk_tier = "C"
    parent_context = []
    if parent_id:
        for relative in (
            f"experiments/{parent_id}/experiment.json",
            f"experiments/{parent_id}/metrics.json",
        ):
            if (root / relative).exists():
                parent_context.append(relative)
    packet = f"experiments/{experiment_id}/review_packet.md"
    packet_path = root / packet
    if risk_tier == "B":
        if not packet_path.exists():
            raise ControllerError(f"Tier B review requires compact packet: {packet}")
        packet_size = packet_path.stat().st_size
        if packet_size > MAX_TIER_B_REVIEW_PACKET_BYTES:
            raise ControllerError(
                f"Tier B review packet is {packet_size} bytes; limit is "
                f"{MAX_TIER_B_REVIEW_PACKET_BYTES} bytes"
            )
    context_paths = [*parent_context, *([packet] if packet_path.exists() else [])]
    context_list = "\n".join(f"- {path}" for path in context_paths)
    return f"""You are the independent research reviewer for a Kaggle cell-tracking project.

Work read-only. Do not edit or create files and do not run commands that change state.
Challenge the proposed strategy, methodology, and implementation independently; do not act as
the experiment author or assume the proposal is correct.

Review experiment: {experiment_id}

Risk tier: {risk_tier}

Read only these files first:
- docs/research/AGENT_WORKFLOW_V2.md
- {record['snapshot_config']}
{context_list}

Use targeted reads from the snapshot source only when the compact packet or diff
leaves a concrete implementation question unresolved. Do not inspect historical
plans, complete logs, prior prompts, or the full repository diff by default.

For Tier C, verify that the versioned Claude strategy, Codex objections, and
revision reached explicit ``CONSENSUS``. Tier B does not require a separate
strategy-consensus exchange; verify its compact experiment card instead.

Conserve the user's weekly model allowance: inspect only the cells relevant to configuration,
dependencies, graph audit, validation, and the final metrics contract. Do not load or restate the
entire notebook when targeted searches are sufficient.

Evaluate:
1. For a normal experiment, is the hypothesis testable and attributable to one major variable?
   An explicitly authorized high-risk or framework-changing experiment may bundle coupled
   changes only when the scope is precise, the rationale is justified, the change is reversible,
   validation is fail-fast, and an ablation or rollback plan is recorded.
2. Is the validation protocol trustworthy, including leakage and the 44b6/6bba domain split?
3. Are there likely implementation bugs or missing output-contract fields?
4. Does the implementation preserve the claimed upstream algorithm, and do its runtime guards
   verify the effective configuration rather than stale notebook prose?
5. Is the experiment duplicate or already contradicted by history?
6. Is expected information gain worth the GPU cost?
7. Does the parent result logically justify this next experiment, and are the stated reasons for
   the change supported by the recorded evidence?
8. What concrete changes are required before launch?
9. Does the declared risk tier match the actual scope, and are that tier's
   strategy or experiment-card requirements satisfied?
10. If this is a bold or framework-changing experiment, verify that it does not relax any
    leakage, provenance, hash-integrity, budget, leaderboard-submission, or promotion gate.

Return concise Markdown. Give every required change a stable finding ID such as
F1 or F2 so a single delta-only revision can address it. End with exactly one line:

VERDICT: PASS

or VERDICT: REVISE / VERDICT: BLOCK. PASS means safe to proceed to the next controller stage
(local smoke testing or remote launch, depending on current state); it is not a claim that the
hypothesis will win.
"""


def request_review(root: Path, experiment_id: str) -> dict[str, Any]:
    record = load_record(root, experiment_id)
    if record["state"] not in {"PROPOSED", "MANUAL_REVIEW_REQUIRED", "READY"}:
        raise ControllerError(
            f"Independent review must happen before remote submission; current state is {record['state']}"
        )
    provider = _review_provider(root, record)
    prompt = build_review_prompt(root, record)
    if provider == "codex":
        command = codex_command()
    else:
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
    prompt_path = exp_dir / f"{provider}-prompt.md"
    run_path = exp_dir / f"{provider}-review-run.json"
    prompt_path.write_text(prompt, encoding="utf-8")
    log = {
        "provider": provider,
        "command": command,
        "exit_code": result.returncode,
        "stderr": result.stderr,
        "completed_at": utc_now(),
    }
    run_path.write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if result.returncode != 0:
        record["review"] = {
            "required": record.get("review", {}).get("required", False),
            "provider": provider,
            "status": "FAILED",
            "completed_at": utc_now(),
            "exit_code": result.returncode,
        }
        save_record(root, record)
        raise ControllerError(
            f"{provider.title()} review command failed for {experiment_id}; see {run_path.name}"
        )

    review_text = result.stdout.strip() + "\n"
    (exp_dir / "review.md").write_text(review_text, encoding="utf-8")
    review_heading = "Codex" if provider == "codex" else "Claude"
    (root / f"{review_heading.upper()}_REVIEW.md").write_text(
        f"# Latest {review_heading} Review\n\nExperiment: `{experiment_id}`  \nCaptured: {utc_now()}\n\n{review_text}",
        encoding="utf-8",
    )
    match = VERDICT_RE.search(review_text)
    verdict = match.group(1) if match else "MISSING"
    record = load_record(root, experiment_id)
    record["review"] = {
        "required": record.get("review", {}).get("required", False),
        "provider": provider,
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
            transition(root, record, "MANUAL_REVIEW_REQUIRED", note=f"{review_heading} verdict: {verdict}")
        if verdict != "PASS":
            raise ControllerError(f"{review_heading} review did not pass: VERDICT={verdict}")
    return record
