"""Build the prediction-neutral hidden-rerun repair for exp068 ep015.

The exp068 snapshot is immutable evidence.  This successor changes only the
locally-added execution governor: the 5,400 second hard process kill becomes a
passive monotonic timer, and the matching final assertion uses the vehicle's
declared 32,400 second Kaggle wall budget.  Inference and CSV code are untouched.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/exp_068_ep015_single_probe/snapshot/source/biohub-exp068-ep015.ipynb"
OUTPUT = ROOT / ".private/current/biohub-exp069-ep015-hidden-rerun-repair.ipynb"

OLD_WATCHDOG_MARKER = "EXP068 HARD WALLTIME: 5400 seconds"
OLD_RUNTIME_ASSERT = "assert 0 < runtime < 5400"
NEW_RUNTIME_ASSERT = "assert 0 < runtime < float(os.environ['BIOHUB_WALL_BUDGET_S'])"
OLD_EXPERIMENT_ID = "'experiment_id': 'exp_068_ep015_single_probe'"
NEW_EXPERIMENT_ID = "'experiment_id': 'exp_069_ep015_hidden_rerun_repair'"

PASSIVE_TIMER = """# exp069: passive timer only. Kaggle's native 9 h limit owns termination.
import time
_exp068_started = time.monotonic()
print("EXP069 hidden-rerun repair: 5400 s process killer disabled; native 32400 s budget retained.", flush=True)
"""


def build() -> dict:
    original = json.loads(SOURCE.read_text(encoding="utf-8"))
    notebook = copy.deepcopy(original)

    watchdog_cells = [
        index
        for index, cell in enumerate(notebook["cells"])
        if OLD_WATCHDOG_MARKER in "".join(cell.get("source", []))
    ]
    assert watchdog_cells == [0], watchdog_cells
    notebook["cells"][0]["source"] = PASSIVE_TIMER.splitlines(keepends=True)

    runtime_replacements = 0
    id_replacements = 0
    for cell in notebook["cells"]:
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        runtime_replacements += source.count(OLD_RUNTIME_ASSERT)
        id_replacements += source.count(OLD_EXPERIMENT_ID)
        source = source.replace(OLD_RUNTIME_ASSERT, NEW_RUNTIME_ASSERT)
        source = source.replace(OLD_EXPERIMENT_ID, NEW_EXPERIMENT_ID)
        cell["source"] = source.splitlines(keepends=True)
        cell["outputs"] = []
        cell["execution_count"] = None

    assert runtime_replacements == 1, runtime_replacements
    assert id_replacements == 1, id_replacements

    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") == "code":
            compile("".join(cell.get("source", [])), f"<exp069_cell_{index}>", "exec")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    return notebook


if __name__ == "__main__":
    built = build()
    print(f"Wrote {OUTPUT} ({len(built['cells'])} cells)")
