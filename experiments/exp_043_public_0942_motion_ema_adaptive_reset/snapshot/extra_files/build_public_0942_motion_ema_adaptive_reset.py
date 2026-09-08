"""Build a label-free adaptive EMA reset test from the reproduced alpha-0.4 candidate."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / ".private/current/public_0941_motion_ema.ipynb"
TARGET = ROOT / ".private/current/public_0942_motion_ema_adaptive_reset.ipynb"
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
            "# Public 0.942 label-free adaptive motion-EMA reset\n\n"
            "Parent: `repro_041_public_0941_motion_ema`, the exactly reproduced fixed-alpha "
            "candidate with user-reported Public LB 0.942. Base EMA alpha remains 0.4. The only "
            "algorithmic change is a runtime-only reset: compute the normalized velocity innovation "
            "from the current selected step and prior EMA velocity; when it exceeds 1.0, use alpha "
            "1.0 for that update, otherwise use 0.4. The rule uses no specimen, video ID, or ground "
            "truth. Velocity multiplier remains 0.5 and every other inference and validation setting "
            "is frozen. No leaderboard submission is performed by this notebook.\n"
        ).splitlines(keepends=True),
    }

    config = find_code(notebook["cells"], "BIOHUB_SCORE_AXIS")
    text = source(config)
    text = replace_once(text,
                        "BIOHUB_SCORE_AXIS = 'public 0.941 train16 + single-variable motion EMA alpha 0.4'",
                        "BIOHUB_SCORE_AXIS = 'public 0.942 label-free adaptive EMA reset'",
                        "score axis")
    text = replace_once(text, 'os.environ["BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"\n',
                        'os.environ["BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"\n'
                        'os.environ["BIOHUB_MOTION_RELINK_EMA_RESET_ALPHA"] = "1.0"\n'
                        'os.environ["BIOHUB_MOTION_RELINK_EMA_INNOVATION_THRESHOLD"] = "1.0"\n',
                        "adaptive EMA environment")
    set_source(config, text)

    guard = find_code(notebook["cells"], "Configuration drift detected")
    text = source(guard)
    text = replace_once(text, '    "BIOHUB_MOTION_RELINK_EMA_ALPHA": 0.4,\n',
                        '    "BIOHUB_MOTION_RELINK_EMA_ALPHA": 0.4,\n'
                        '    "BIOHUB_MOTION_RELINK_EMA_RESET_ALPHA": 1.0,\n'
                        '    "BIOHUB_MOTION_RELINK_EMA_INNOVATION_THRESHOLD": 1.0,\n',
                        "adaptive guard values")
    text = replace_once(text, 'print("EMA alpha: 0.4; unchanged velocity multiplier: 0.5")',
                        'print("Adaptive EMA: base alpha 0.4, innovation reset alpha 1.0 at ratio > 1.0")\n'
                        'print("Unchanged velocity multiplier: 0.5")', "guard report")
    set_source(guard, text)

    imports = find_code(notebook["cells"], "MOTION_RELINK_EMA_ALPHA =")
    text = source(imports)
    text = replace_once(text,
                        'MOTION_RELINK_EMA_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_ALPHA", "0.4"))\n',
                        'MOTION_RELINK_EMA_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_ALPHA", "0.4"))\n'
                        'MOTION_RELINK_EMA_RESET_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_RESET_ALPHA", "1.0"))\n'
                        'MOTION_RELINK_EMA_INNOVATION_THRESHOLD = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_INNOVATION_THRESHOLD", "1.0"))\n',
                        "adaptive constant parse")
    text = replace_once(text, '    "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,\n',
                        '    "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,\n'
                        '    "motion_relink_ema_reset_alpha": MOTION_RELINK_EMA_RESET_ALPHA,\n'
                        '    "motion_relink_ema_innovation_threshold": MOTION_RELINK_EMA_INNOVATION_THRESHOLD,\n',
                        "adaptive display")
    text = replace_once(text, '    "motion_relink_velocity_estimator": "per_track_ema",',
                        '    "motion_relink_velocity_estimator": "adaptive_ema_reset",',
                        "velocity estimator display")
    set_source(imports, text)

    postprocess = find_code(notebook["cells"], "def motion_relink_edges")
    text = source(postprocess)
    old_update = (
        "            velocity_um[target_id] = (\n"
        "                step_velocity\n"
        "                if previous_velocity is None\n"
        "                else MOTION_RELINK_EMA_ALPHA * step_velocity\n"
        "                + (1.0 - MOTION_RELINK_EMA_ALPHA) * previous_velocity\n"
        "            )\n"
    )
    new_update = (
        "            if previous_velocity is None:\n"
        "                velocity_um[target_id] = step_velocity\n"
        "                stats[\"motion_relink_adaptive_initial_updates\"] = stats.get(\"motion_relink_adaptive_initial_updates\", 0) + 1\n"
        "            else:\n"
        "                innovation_scale = max(float(np.linalg.norm(step_velocity)), float(np.linalg.norm(previous_velocity)), 1e-6)\n"
        "                innovation_ratio = float(np.linalg.norm(step_velocity - previous_velocity)) / innovation_scale\n"
        "                if innovation_ratio > MOTION_RELINK_EMA_INNOVATION_THRESHOLD:\n"
        "                    effective_alpha = MOTION_RELINK_EMA_RESET_ALPHA\n"
        "                    stats[\"motion_relink_adaptive_reset_updates\"] = stats.get(\"motion_relink_adaptive_reset_updates\", 0) + 1\n"
        "                else:\n"
        "                    effective_alpha = MOTION_RELINK_EMA_ALPHA\n"
        "                    stats[\"motion_relink_adaptive_base_updates\"] = stats.get(\"motion_relink_adaptive_base_updates\", 0) + 1\n"
        "                velocity_um[target_id] = (\n"
        "                    effective_alpha * step_velocity\n"
        "                    + (1.0 - effective_alpha) * previous_velocity\n"
        "                )\n"
    )
    text = replace_once(text, old_update, new_update, "adaptive velocity update")
    set_source(postprocess, text)

    scorer = find_code(notebook["cells"], 'row["motion_relink_ema_predictions"]')
    text = source(scorer)
    text = replace_once(text,
                        '        row["motion_relink_skipped_large_frame"] = int(_stage_stats.get("motion_relink_skipped_large_frame", 0))\n',
                        '        row["motion_relink_skipped_large_frame"] = int(_stage_stats.get("motion_relink_skipped_large_frame", 0))\n'
                        '        row["motion_relink_adaptive_reset_updates"] = int(_stage_stats.get("motion_relink_adaptive_reset_updates", 0))\n'
                        '        row["motion_relink_adaptive_base_updates"] = int(_stage_stats.get("motion_relink_adaptive_base_updates", 0))\n'
                        '        row["motion_relink_adaptive_initial_updates"] = int(_stage_stats.get("motion_relink_adaptive_initial_updates", 0))\n',
                        "adaptive telemetry")
    set_source(scorer, text)

    preflight = find_code(notebook["cells"], "# Embedded after candidate test inference")
    prefix = source(preflight).split("# Embedded after candidate test inference", 1)[0]
    prefix = replace_once(prefix,
                          "PARENT_SUBMISSION_SHA = 'bf66c879298e71c5cce0326fbac5956ca567a344ae28f0d402dfc5003fba52bd'",
                          f"PARENT_SUBMISSION_SHA = '{PARENT_SUBMISSION_SHA}'",
                          "parent submission SHA")
    set_source(preflight, prefix + (ROOT / "scripts/public_0942_motion_ema_adaptive_reset_preflight.py").read_text(encoding="utf-8"))

    contract = find_code(notebook["cells"], "# Embedded final contract")
    set_source(contract, (ROOT / "scripts/public_0942_motion_ema_adaptive_reset_contract.py").read_text(encoding="utf-8"))

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
