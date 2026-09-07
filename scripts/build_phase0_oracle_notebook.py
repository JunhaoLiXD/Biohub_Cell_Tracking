"""Build the lightweight Kaggle notebook for the candidate-constrained oracle."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".private" / "current" / "v9_division_aware.ipynb"
TARGET = ROOT / ".private" / "current" / "phase0_candidate_oracle.ipynb"
RUNNER = ROOT / "scripts" / "run_phase0_candidate_oracle.py"


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


source_notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
environment_source = "".join(source_notebook["cells"][1]["source"])
environment_source = environment_source.replace(
    "# as a matched pair. Prefer the attached offline wheels, then use PyPI (this audit\n"
    "# runs with internet ON). No-op when polars already works.\n",
    "# as a matched pair. This experiment requires the attached offline wheels and runs\n"
    "# with internet disabled. No-op when polars already works.\n",
)
runner_source = RUNNER.read_text(encoding="utf-8").split('\n\nif __name__ == "__main__":', maxsplit=1)[0]

notebook = {
    "cells": [
        markdown_cell(
            "# Phase 0 candidate-constrained division oracle\n\n"
            "Parent: `diag_019_train16_final_validation_graph_export`. This CPU-only diagnostic uses "
            "same-run candidate, pre-ILP graph, and final graph artifacts from that parent, plus the "
            "fixed 16-video validation set, the exact final graphs passed to validation scoring, "
            "and the bounded pre-ILP candidate export. It evaluates cumulative families A, A+B, "
            "and A+B+C with atomic, "
            "conflict-aware edits. Absolute train-derived scores are optimistic; decisions use paired "
            "deltas and require positive headroom on both specimens.\n",
            "oracle-summary",
        ),
        code_cell(environment_source, "runtime-environment"),
        code_cell(runner_source, "embedded-oracle-runner"),
        code_cell(
            "# Execute the embedded frozen analysis.\n"
            "import json\n"
            "from pathlib import Path\n\n"
            "payload = run()\n"
            "print(json.dumps({\n"
            "    'gate': payload['metrics']['oracle_gate_passed'],\n"
            "    'baseline_reproduced': payload['metrics']['baseline_reproduced'],\n"
            "    'candidate_rows_by_video': payload['metrics']['candidate_rows_by_video'],\n"
            "    'families': payload['metrics']['families'],\n"
            "}, indent=2, sort_keys=True))\n",
            "execute-oracle",
        ),
        code_cell(
            "# Controller output contract: the preceding analysis must write this final artifact.\n"
            "metrics_path = Path('/kaggle/working/metrics.json')\n"
            "assert metrics_path.is_file(), 'Oracle did not write metrics.json'\n"
            "saved_metrics = json.loads(metrics_path.read_text(encoding='utf-8'))\n"
            "assert saved_metrics['experiment_id'] == 'diag_025_train16_frozen_scorer_candidate_oracle'\n"
            "assert isinstance(saved_metrics['metrics']['oracle_gate_passed'], bool)\n"
            "print('validated', metrics_path)\n",
            "metrics-contract",
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
