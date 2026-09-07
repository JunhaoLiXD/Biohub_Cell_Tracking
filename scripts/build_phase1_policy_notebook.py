"""Build the CPU-only Phase-1 cross-specimen Family-A policy notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".private" / "current" / "v9_division_aware.ipynb"
TARGET = ROOT / ".private" / "current" / "phase1_family_a_policy.ipynb"
ORACLE_HELPERS = ROOT / "scripts" / "run_phase0_candidate_oracle.py"
FEATURE_HELPERS = ROOT / "scripts" / "run_phase1_feature_separability.py"
RUNNER = ROOT / "scripts" / "run_phase1_family_a_policy.py"


def code_cell(source: str, cell_id: str) -> dict:
    return {
        "cell_type": "code",
        "id": cell_id,
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def markdown_cell(source: str, cell_id: str) -> dict:
    return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": source.splitlines(keepends=True)}


def without_main(path: Path) -> str:
    return path.read_text(encoding="utf-8").split('\n\nif __name__ == "__main__":', 1)[0]


source_notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
environment_source = "".join(source_notebook["cells"][1]["source"]).replace(
    "# as a matched pair. Prefer the attached offline wheels, then use PyPI (this audit\n"
    "# runs with internet ON). No-op when polars already works.\n",
    "# as a matched pair. This experiment requires the attached offline wheels and runs\n"
    "# with internet disabled. No-op when polars already works.\n",
)

notebook = {
    "cells": [
        markdown_cell(
            "# Phase 1 cross-specimen Family-A policy gate\n\n"
            "This CPU-only diagnostic converts the transferable candidate signal from diag_026 "
            "into a conservative metric-scored action policy. A model is trained on one specimen, "
            "its threshold is calibrated only on that specimen, and the unchanged policy is scored "
            "on the held-out specimen in both directions. Each video may receive at most one "
            "orphan-only Family-A division edge.\n",
            "summary",
        ),
        code_cell(environment_source, "environment"),
        code_cell(without_main(ORACLE_HELPERS), "frozen-scorer"),
        code_cell(without_main(FEATURE_HELPERS), "feature-helpers"),
        code_cell(without_main(RUNNER), "policy-gate"),
        code_cell(
            "payload = run_policy_gate()\n"
            "print(json.dumps(payload['metrics'], indent=2, sort_keys=True))\n",
            "execute",
        ),
        code_cell(
            "metrics_path = Path('/kaggle/working/metrics.json')\n"
            "assert metrics_path.is_file()\n"
            "saved_metrics = json.loads(metrics_path.read_text(encoding='utf-8'))\n"
            "assert saved_metrics['experiment_id'] == 'diag_027_train16_cross_specimen_family_a_policy'\n"
            "assert isinstance(saved_metrics['metrics']['family_a_policy_gate_passed'], bool)\n",
            "contract",
        ),
    ],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
TARGET.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
print(TARGET)
