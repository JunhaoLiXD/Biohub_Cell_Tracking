"""Build the controlled alpha-0.6 sensitivity test from the reproduced alpha-0.4 candidate."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / ".private/current/public_0941_motion_ema.ipynb"
TARGET = ROOT / ".private/current/public_0942_motion_ema_alpha06.ipynb"
PARENT_SHA = "914104fffa12f92de10521cd1a106a415a7b353eac5b5c460b04daf83ec96453"
PARENT_SUBMISSION_SHA = "fd1162bfc09b6d06413701aa898eb14bc5df9cc5bfd999fe598bf81fbf125515"


def source(cell):
    return "".join(cell["source"])


def set_source(cell, text):
    cell["source"] = text.splitlines(keepends=True)
    cell["outputs"] = []
    cell["execution_count"] = None


def find_code(cells, marker):
    matches = [cell for cell in cells if cell.get("cell_type") == "code" and marker in source(cell)]
    if len(matches) != 1:
        raise ValueError(f"Expected one code cell containing {marker!r}, found {len(matches)}")
    return matches[0]


def replace_once(text, old, new, label):
    if text.count(old) != 1:
        raise ValueError(f"Expected exactly one {label} replacement, found {text.count(old)}")
    return text.replace(old, new, 1)


def build():
    if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA:
        raise ValueError("Frozen alpha-0.4 parent changed")
    notebook = json.loads(PARENT.read_text(encoding="utf-8"))
    parent_cells = copy.deepcopy(notebook["cells"])
    notebook["cells"][0] = {
        "cell_type": "markdown", "metadata": {},
        "source": (
            "# Public 0.942 motion-EMA alpha-0.6 sensitivity test\n\n"
            "Parent: `repro_041_public_0941_motion_ema`, the exactly reproduced alpha-0.4 "
            "candidate with user-reported Public LB 0.942. This experiment changes only the "
            "EMA alpha from 0.4 to 0.6. The velocity multiplier remains 0.5. Models, checkpoints, "
            "detector, association, ILP, gap closing, division logic, frozen train16 samples, and "
            "scorer remain fixed. The hypothesis is that less historical inertia preserves the "
            "aggregate gain while reducing the worst video-level regression. No leaderboard "
            "submission is performed by this notebook.\n"
        ).splitlines(keepends=True),
    }

    config = find_code(notebook["cells"], "BIOHUB_SCORE_AXIS")
    text = source(config)
    text = replace_once(text,
                        "BIOHUB_SCORE_AXIS = 'public 0.941 train16 + single-variable motion EMA alpha 0.4'",
                        "BIOHUB_SCORE_AXIS = 'public 0.942 motion EMA alpha sensitivity 0.6'",
                        "score axis")
    text = replace_once(text, 'os.environ["BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"',
                        'os.environ["BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.6"', "EMA environment")
    set_source(config, text)

    guard = find_code(notebook["cells"], "Configuration drift detected")
    text = source(guard)
    text = replace_once(text, '    "BIOHUB_MOTION_RELINK_EMA_ALPHA": 0.4,',
                        '    "BIOHUB_MOTION_RELINK_EMA_ALPHA": 0.6,', "guard alpha")
    text = replace_once(text, 'print("EMA alpha: 0.4; unchanged velocity multiplier: 0.5")',
                        'print("EMA alpha: 0.6; unchanged velocity multiplier: 0.5")', "guard report")
    set_source(guard, text)

    imports = find_code(notebook["cells"], "MOTION_RELINK_EMA_ALPHA =")
    text = source(imports)
    text = replace_once(text,
                        'MOTION_RELINK_EMA_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_ALPHA", "0.4"))',
                        'MOTION_RELINK_EMA_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_ALPHA", "0.6"))',
                        "EMA default")
    set_source(imports, text)

    preflight = find_code(notebook["cells"], "# Embedded after candidate test inference")
    prefix = source(preflight).split("# Embedded after candidate test inference", 1)[0]
    prefix = replace_once(prefix,
                          "PARENT_SUBMISSION_SHA = 'bf66c879298e71c5cce0326fbac5956ca567a344ae28f0d402dfc5003fba52bd'",
                          f"PARENT_SUBMISSION_SHA = '{PARENT_SUBMISSION_SHA}'",
                          "parent submission SHA")
    set_source(preflight, prefix + (ROOT / "scripts/public_0942_motion_ema_alpha06_preflight.py").read_text(encoding="utf-8"))

    contract = find_code(notebook["cells"], "# Embedded final contract")
    set_source(contract, (ROOT / "scripts/public_0942_motion_ema_alpha06_contract.py").read_text(encoding="utf-8"))

    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            cell["outputs"], cell["execution_count"] = [], None
            ast.parse(source(cell))
    if len(notebook["cells"]) != len(parent_cells):
        raise ValueError("Notebook cell count changed unexpectedly")
    return notebook


if __name__ == "__main__":
    TARGET.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(TARGET)
