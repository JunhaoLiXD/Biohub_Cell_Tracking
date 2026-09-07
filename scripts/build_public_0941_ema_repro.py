"""Deterministically reproduce exp_040; only final evidence contract changes."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = "repro_041_public_0941_motion_ema"
PARENT = ROOT / "experiments/exp_040_public_0941_motion_ema/snapshot/source/public_0941_motion_ema.ipynb"
REFERENCE = ROOT / "experiments/exp_040_public_0941_motion_ema/artifacts/metrics.json"
TARGET = ROOT / ".private/current/public_0941_ema_repro.ipynb"
PARENT_SHA = "914104fffa12f92de10521cd1a106a415a7b353eac5b5c460b04daf83ec96453"
REFERENCE_SHA = "e90931af3e701ada413d672b0e7d629a8f5e2e36c78468b25fc1672b9909382b"


def build():
    for path, expected in ((PARENT, PARENT_SHA), (REFERENCE, REFERENCE_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Frozen input changed: {path}")
    notebook = json.loads(PARENT.read_text(encoding="utf-8"))
    metrics = json.loads(REFERENCE.read_text(encoding="utf-8"))
    expected = {
        "aggregate": {"primary_metric": metrics["primary_metric"],
                      **{key: metrics["validation"][key] for key in ("adjusted_edge_jaccard", "division_jaccard")}},
        "specimens": metrics["specimen_metrics"],
        "ema_execution": metrics["metrics"]["motion_relink_ema_execution"],
        "division_counts": metrics["metrics"]["division_counts"],
        "submission_sha256": metrics["metrics"]["candidate_submission_sha256"],
    }
    notebook["cells"].insert(0, {
        "cell_type": "markdown", "metadata": {}, "source": [
            "# Independent reproduction of public 0.941 motion EMA\n\n",
            "Parent: exp_040_public_0941_motion_ema. All inference and validation code is retained. "
            "Only the final evidence contract adds exact submission SHA256, aggregate/specimen "
            "metrics (absolute tolerance 1e-12, relative tolerance zero), division counts and "
            "EMA telemetry comparison against the frozen parent artifacts. An additional "
            "post-run Claude review is required for this reproduction only, before a leaderboard "
            "decision. Existing prelaunch review rules continue to apply.\n",
        ]})
    contract = notebook["cells"][-1]
    text = "".join(contract["source"])
    old = '_EXPERIMENT_ID == "exp_040_public_0941_motion_ema"'
    assert text.count(old) == 1
    text = text.replace(old, f'_EXPERIMENT_ID == "{EXPERIMENT}"')
    marker = '(WORKING_DIR / "validation_stage_stats.json").write_text('
    assert text.count(marker) == 1
    extra = (ROOT / "scripts/public_0941_ema_repro_contract.py").read_text(encoding="utf-8")
    text = text.replace(marker, f"REPRO_EXPECTED = {expected!r}\n" + extra + "\n" + marker)
    ast.parse(text)
    contract["source"] = text.splitlines(keepends=True)
    return notebook


if __name__ == "__main__":
    TARGET.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(TARGET)
