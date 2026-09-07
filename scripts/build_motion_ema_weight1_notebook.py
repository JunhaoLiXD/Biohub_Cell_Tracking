"""Build the controlled EMA velocity-weight 1.0 experiment notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".private" / "current" / "motion_ema_train16_v2.ipynb"
TARGET = ROOT / ".private" / "current" / "motion_ema_weight1_train16.ipynb"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one {label} replacement target, found {count}")
    return source.replace(old, new, 1)


notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
summary_cell = next(cell for cell in notebook["cells"] if cell.get("id") == "motion-ema-summary")
summary_cell["source"] = (
    "# Controlled EMA velocity-weight validation\n\n"
    "This experiment starts from the independently reproduced motion-EMA candidate and changes "
    "only the velocity multiplier from 0.5 to 1.0, as used by the public 0.940 reference fork. "
    "EMA alpha remains 0.4 and every detector, fusion, ILP, gap-closing, division, validation, and "
    "scoring setting remains fixed. No public outputs are used.\n"
).splitlines(keepends=True)

code_cells = [cell for cell in notebook["cells"] if cell.get("cell_type") == "code"]
config = code_cells[0]
source = "".join(config["source"])
source = replace_once(
    source,
    "BIOHUB_SCORE_AXIS = 'train16 paired motion-relink EMA ablation'",
    "BIOHUB_SCORE_AXIS = 'train16 paired EMA velocity-weight ablation'",
    "score axis",
)
source = replace_once(
    source,
    'os.environ["BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "0.5"',
    'os.environ["BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "1.0"',
    "velocity-weight environment",
)
config["source"] = source.splitlines(keepends=True)

guard = code_cells[1]
source = "".join(guard["source"])
source = replace_once(
    source,
    '    "BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT": 0.5,',
    '    "BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT": 1.0,',
    "velocity-weight guard",
)
source = replace_once(
    source,
    'print("Single algorithm change: one-frame velocity replaced by per-track EMA")\n'
    'print("EMA alpha: 0.4; unchanged velocity multiplier: 0.5")',
    'print("Single parameter change: EMA velocity multiplier 0.5 to 1.0")\n'
    'print("EMA alpha remains 0.4")',
    "guard summary",
)
guard["source"] = source.splitlines(keepends=True)

contract = code_cells[-1]
source = "".join(contract["source"])
source = replace_once(
    source,
    '_CONTROLLER_BASELINE_PRIMARY = 0.9252519785518039\n'
    '_CONTROLLER_BASELINE_SPECIMEN = {\n'
    '    "44b6": 0.9036583711598225,\n'
    '    "6bba": 0.9329497722613302,\n'
    '}\n',
    '_CONTROLLER_BASELINE_PRIMARY = 0.9273163492758533\n'
    '_CONTROLLER_BASELINE_SPECIMEN = {\n'
    '    "44b6": 0.9050173749768016,\n'
    '    "6bba": 0.9355045025356437,\n'
    '}\n',
    "accepted EMA baseline",
)
source = replace_once(
    source,
    '        "validation_contract_passed": _controller_validation_contract_passed,\n',
    '        "validation_contract_passed": _controller_validation_contract_passed,\n'
    '        "comparison_parent": "repro_036_train16_motion_ema",\n'
    '        "velocity_weight_change": {"from": 0.5, "to": 1.0},\n',
    "comparison provenance",
)
contract["source"] = source.splitlines(keepends=True)

TARGET.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
print(TARGET)
