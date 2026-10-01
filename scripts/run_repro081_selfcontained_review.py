"""Tool-free evidence review after repro081's read-helper infrastructure BLOCK."""

from __future__ import annotations

import json
import subprocess

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError, load_record, save_record, transition, utc_now
from experiment_controller.review import VERDICT_RE, codex_command


EXPERIMENT_ID = "repro_081_kunal_runtime_receipt"


def read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    root = PROJECT_ROOT
    record = load_record(root, EXPERIMENT_ID)
    if record["state"] != "MANUAL_REVIEW_REQUIRED" or record.get("review", {}).get("verdict") != "BLOCK":
        raise ControllerError("Expected infrastructure-only BLOCK")
    evidence = {
        "workflow": read("docs/research/AGENT_WORKFLOW_V2.md"),
        "snapshot_config": read(record["snapshot_config"]),
        "parent_record": read("experiments/repro_080_kunal_public_verbatim_admission_repair/experiment.json"),
        "review_packet": read(f"experiments/{EXPERIMENT_ID}/review_packet.md"),
        "manifest": read(record["snapshot_manifest"]),
        "builder": read("experiments/repro_081_kunal_runtime_receipt/snapshot/extra_files/build_repro081_runtime_receipt.py"),
        "smoke": read("experiments/repro_081_kunal_runtime_receipt/snapshot/extra_files/smoke_repro081.py"),
        "sweep_audit": read("experiments/repro_081_kunal_runtime_receipt/snapshot/extra_files/audit_repro080_sweep_receipts.py"),
        "runtime_audit": read("experiments/repro_081_kunal_runtime_receipt/snapshot/extra_files/audit_repro081_runtime_receipt.py"),
        "runtime_tests": read("experiments/repro_081_kunal_runtime_receipt/snapshot/extra_files/test_repro081_runtime_receipt.py"),
        "output_audit": read("experiments/repro_081_kunal_runtime_receipt/snapshot/extra_files/audit_repro079_output.py"),
        "base_output_audit": read("experiments/repro_081_kunal_runtime_receipt/snapshot/extra_files/audit_biohub_submission_csv.py"),
    }
    prompt = """You are the independent Codex admission reviewer for repro081. The prior
review was an infrastructure-only BLOCK because its file helper failed before reading anything.
Do not call tools or inspect files. All bounded evidence is embedded below. Review independently,
including tier authorization, source preservation, receipt truthfulness, negative tests, leakage,
output contracts, budget, and stop rules. Do not assume PASS. Return concise Markdown with stable
finding IDs for required changes. End with exactly VERDICT: PASS, VERDICT: REVISE, or VERDICT: BLOCK.

""" + "\n".join(f"--- {name.upper()} ---\n{text}" for name, text in evidence.items())
    command = codex_command()
    result = subprocess.run(command, cwd=root, text=True, encoding="utf-8", errors="replace",
                            input=prompt, capture_output=True, check=False)
    exp_dir = root / "experiments" / EXPERIMENT_ID
    (exp_dir / "codex-prompt-selfcontained.md").write_text(prompt, encoding="utf-8")
    (exp_dir / "codex-review-run-selfcontained.json").write_text(json.dumps({
        "provider": "codex", "command": command, "exit_code": result.returncode,
        "stderr": result.stderr, "completed_at": utc_now(),
        "mode": "tool_free_self_contained_after_read_helper_block",
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if result.returncode:
        raise ControllerError("Self-contained Codex review command failed")
    review_text = result.stdout.strip() + "\n"
    review_path = exp_dir / "review_selfcontained.md"
    review_path.write_text(review_text, encoding="utf-8")
    match = VERDICT_RE.search(review_text)
    verdict = match.group(1) if match else "MISSING"
    record = load_record(root, EXPERIMENT_ID)
    record["review"] = {
        "required": True, "provider": "codex",
        "status": "PASSED" if verdict == "PASS" else "CHANGES_REQUESTED",
        "verdict": verdict, "path": review_path.relative_to(root).as_posix(),
        "completed_at": utc_now(), "mode": "tool_free_self_contained_after_read_helper_block",
        "prior_infrastructure_block": f"experiments/{EXPERIMENT_ID}/review.md",
    }
    save_record(root, record)
    if verdict == "PASS":
        transition(root, record, "REVIEWED", note="Independent self-contained Codex PASS")
    else:
        raise ControllerError(f"Self-contained Codex review did not pass: {verdict}")
    print(review_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
