"""Run the single allowed repro079 admission retry with evidence embedded in the prompt.

The normal read-only reviewer could not initialize its filesystem helper. This retry
keeps the reviewer tool-free and supplies the bounded Tier B evidence directly. It
does not weaken or waive the requirement for an independent PASS.
"""

from __future__ import annotations

import json
import re
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
    if record.get("review", {}).get("verdict") != "BLOCK":
        raise ControllerError("Expected preserved infrastructure-only BLOCK")

    workflow = (root / "docs/research/AGENT_WORKFLOW_V2.md").read_text(encoding="utf-8")
    config = (root / record["snapshot_config"]).read_text(encoding="utf-8")
    parent = (root / "experiments/exp_064_x138_verbatim_repro/experiment.json").read_text(encoding="utf-8")
    packet = (root / f"experiments/{EXPERIMENT_ID}/review_packet.md").read_text(encoding="utf-8")
    notebook_path = root / record["snapshot_source"]
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", "")) for cell in notebook["cells"])
    patterns = re.compile(
        r"BIOHUB_SCORE_AXIS|DEEPCENTER_SAFE_DIV_THRESHOLD|SUBMISSION_PATH|"
        r"write_test_submission|ppsweep_selected|dcsafediv020|leaderboard_submission",
        re.IGNORECASE,
    )
    excerpts = "\n".join(line for line in source.splitlines() if patterns.search(line))
    if len(excerpts) > 30000:
        excerpts = excerpts[:30000] + "\n[truncated after bounded relevant excerpts]"

    prompt = f"""You are the independent admission reviewer for a Tier B Kaggle reproduction.
The previous review returned BLOCK only because its read-only filesystem helper failed before
reading any file. This is the single delta-only retry. Do not call tools or inspect the filesystem;
all bounded evidence is embedded below. Review independently and do not assume PASS.

Evaluate source identity, attribution, leakage, output contract, non-duplication, GPU budget,
stop rule, and whether one private Kaggle run (no leaderboard submission) is safe and informative.
The notebook itself is an immutable third-party public source; requiring algorithm repairs would
defeat the byte-verbatim hypothesis, but concrete unsafe or non-informative defects may block it.
Return concise Markdown with stable finding IDs for required changes. End with exactly one line:
VERDICT: PASS
or VERDICT: REVISE
or VERDICT: BLOCK

--- WORKFLOW ---
{workflow}
--- SNAPSHOT CONFIG ---
{config}
--- PARENT RECORD ---
{parent}
--- COMPACT REVIEW PACKET ---
{packet}
--- TARGETED IMMUTABLE NOTEBOOK EXCERPTS ---
{excerpts}
--- END EVIDENCE ---
"""

    result = subprocess.run(
        codex_command(), cwd=root, text=True, encoding="utf-8", errors="replace",
        input=prompt, capture_output=True, check=False,
    )
    exp_dir = root / "experiments" / EXPERIMENT_ID
    (exp_dir / "codex-prompt-round2-selfcontained.md").write_text(prompt, encoding="utf-8")
    (exp_dir / "codex-review-run-round2-selfcontained.json").write_text(
        json.dumps({
            "provider": "codex",
            "command": codex_command(),
            "exit_code": result.returncode,
            "stderr": result.stderr,
            "completed_at": utc_now(),
            "mode": "tool_free_self_contained_delta_retry_after_read_helper_failure",
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if result.returncode:
        raise ControllerError("Self-contained Codex review command failed")
    review_text = result.stdout.strip() + "\n"
    review_path = exp_dir / "review_round2.md"
    review_path.write_text(review_text, encoding="utf-8")
    match = VERDICT_RE.search(review_text)
    verdict = match.group(1) if match else "MISSING"
    record = load_record(root, EXPERIMENT_ID)
    record["review"] = {
        "required": True,
        "provider": "codex",
        "status": "PASSED" if verdict == "PASS" else "CHANGES_REQUESTED",
        "verdict": verdict,
        "path": review_path.relative_to(root).as_posix(),
        "completed_at": utc_now(),
        "mode": "tool_free_self_contained_delta_retry_after_read_helper_failure",
        "prior_infrastructure_block": f"experiments/{EXPERIMENT_ID}/review.md",
    }
    save_record(root, record)
    if verdict == "PASS":
        transition(root, record, "REVIEWED", note="Independent self-contained Codex retry PASS")
    else:
        raise ControllerError(f"Self-contained Codex review did not pass: {verdict}")
    print(review_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
