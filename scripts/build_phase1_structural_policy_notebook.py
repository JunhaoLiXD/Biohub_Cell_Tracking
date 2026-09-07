"""Build the Phase-1 structural factorized policy notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".private" / "current" / "v9_division_aware.ipynb"
TARGET = ROOT / ".private" / "current" / "phase1_structural_policy.ipynb"
SOURCES = (
    ROOT / "scripts" / "run_phase0_candidate_oracle.py",
    ROOT / "scripts" / "run_phase1_feature_separability.py",
    ROOT / "scripts" / "run_phase1_family_a_policy.py",
    ROOT / "scripts" / "run_phase1_deployment_policy.py",
    ROOT / "scripts" / "run_phase1_factorized_policy.py",
    ROOT / "scripts" / "run_phase1_eligible_validity_policy.py",
    ROOT / "scripts" / "run_phase1_structural_policy.py",
)


def code_cell(source: str, cell_id: str) -> dict:
    return {
        "cell_type": "code",
        "id": cell_id,
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


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
        {
            "cell_type": "markdown",
            "id": "summary",
            "metadata": {},
            "source": (
                "# Phase 1 structural factorized policy gate\n\n"
                "This CPU-only diagnostic adds inference-available graph, track-duration, and "
                "sibling-geometry features to the diag_030 factorized Family-A policy. Labels, "
                "models, action constraints, frozen scorer, per-video cap, and training-specimen-only "
                "threshold calibration remain fixed.\n"
            ).splitlines(keepends=True),
        },
        code_cell(environment_source, "environment"),
        *[code_cell(without_main(path), f"embedded-{index}") for index, path in enumerate(SOURCES)],
        code_cell(
            "payload = run_structural_policy_gate()\n"
            "print(json.dumps(payload['metrics'], indent=2, sort_keys=True))\n",
            "execute",
        ),
        code_cell(
            "metrics_path = Path('/kaggle/working/metrics.json')\n"
            "assert metrics_path.is_file()\n"
            "saved_metrics = json.loads(metrics_path.read_text(encoding='utf-8'))\n"
            "assert saved_metrics['experiment_id'] == 'diag_031_train16_structural_factorized_policy'\n"
            "assert isinstance(saved_metrics['metrics']['structural_policy_gate_passed'], bool)\n"
            "assert saved_metrics['metrics']['all_structural_features_available_at_inference'] is True\n"
            "assert saved_metrics['metrics']['gt_matching_is_not_a_model_feature'] is True\n",
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
