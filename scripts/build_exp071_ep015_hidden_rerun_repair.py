"""Build the reviewed exp071 hidden-rerun repair from immutable exp068."""
from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/exp_068_ep015_single_probe/snapshot/source/biohub-exp068-ep015.ipynb"
OUTPUT = ROOT / ".private/current/biohub-exp071-ep015-hidden-rerun-repair.ipynb"

REPLACEMENTS = {
    "assert 0 < runtime < 5400": "assert 0 < runtime < float(os.environ['BIOHUB_WALL_BUDGET_S'])",
    "'experiment_id': 'exp_068_ep015_single_probe'": "'experiment_id': 'exp_071_ep015_hidden_rerun_repair'",
    "'validation': {'protocol': 'ep015_single_probe_v1'}": (
        "'validation': {'protocol': 'ep015_single_probe_v1', "
        "'admission_protocol': 'exp071_prediction_neutral_source_delta_v2'}"
    ),
    'os.environ["BIOHUB_REPAIR_DEADLINE_S"] = "27000"': (
        'os.environ["BIOHUB_REPAIR_DEADLINE_S"] = "32400"'
    ),
    '"BIOHUB_REPAIR_DEADLINE_S": 27000.0': '"BIOHUB_REPAIR_DEADLINE_S": 32400.0',
}

PASSIVE_TIMER = """# exp071: passive timer; Kaggle's native 9 h limit owns termination.
import time
_exp068_started = time.monotonic()
print("EXP071 hidden-rerun repair: 5400 s killer disabled; full repair retained through 32400 s.", flush=True)
"""


def build() -> dict:
    notebook = copy.deepcopy(json.loads(SOURCE.read_text(encoding="utf-8")))
    assert "EXP068 HARD WALLTIME: 5400 seconds" in "".join(notebook["cells"][0]["source"])
    notebook["cells"][0]["source"] = PASSIVE_TIMER.splitlines(keepends=True)

    counts = {old: 0 for old in REPLACEMENTS}
    for cell in notebook["cells"]:
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        for old, new in REPLACEMENTS.items():
            counts[old] += source.count(old)
            source = source.replace(old, new)
        cell["source"] = source.splitlines(keepends=True)
        cell["outputs"] = []
        cell["execution_count"] = None
    assert all(count == 1 for count in counts.values()), counts

    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") == "code":
            compile("".join(cell.get("source", [])), f"<exp071_cell_{index}>", "exec")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    return notebook


if __name__ == "__main__":
    result = build()
    print(f"Wrote {OUTPUT} ({len(result['cells'])} cells)")
