"""Build the controlled motion-EMA screen from the frozen 0.941 train16 baseline."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "experiments/val_039_public_0941_train16/snapshot/source/public_0941_train16.ipynb"
TARGET = ROOT / ".private/current/public_0941_motion_ema.ipynb"
PARENT_SHA = "190d07726229f3834055a226bfc5a77dda2608565c8967d61a7ef10c22cc0512"


def source(cell):
    return "".join(cell["source"])


def set_source(cell, text):
    cell["source"] = text.splitlines(keepends=True)
    cell["outputs"] = []
    cell["execution_count"] = None


def replace_once(text, old, new, label):
    if text.count(old) != 1:
        raise ValueError(f"Expected exactly one {label} replacement, found {text.count(old)}")
    return text.replace(old, new, 1)


def find_code(cells, marker):
    matches = [cell for cell in cells if cell.get("cell_type") == "code" and marker in source(cell)]
    if len(matches) != 1:
        raise ValueError(f"Expected one code cell containing {marker!r}, found {len(matches)}")
    return matches[0]


def build():
    if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA:
        raise ValueError("Frozen val_039 parent changed")
    notebook = json.loads(PARENT.read_text(encoding="utf-8"))
    baseline_cells = copy.deepcopy(notebook["cells"])
    notebook["cells"][0] = {
        "cell_type": "markdown", "metadata": {},
        "source": (
            "# Public 0.941 single-variable motion-EMA screen\n\n"
            "Parent: `val_039_public_0941_train16`, the frozen train16 baseline for the "
            "reproduced Public LB 0.941 pipeline. This experiment changes only the motion-relink "
            "velocity estimator from the latest one-frame displacement to a per-track exponential "
            "moving average with alpha 0.4. The velocity multiplier remains 0.5. Models, checkpoints, "
            "detector, association, ILP, gap closing, division logic, frozen sample selection, and "
            "scorer remain fixed. The EMA implementation was previously reproduced under the older "
            "0.933 parent; this run tests transfer, not guaranteed additivity. No leaderboard "
            "submission is performed by this notebook.\n"
        ).splitlines(keepends=True),
    }

    config = find_code(notebook["cells"], "BIOHUB_PRESET")
    text = source(config)
    text = replace_once(text, "BIOHUB_SCORE_AXIS = 'public 0.940 base + {\"BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD\": \"0.25\", \"BIOHUB_GAP_CLOSE_UM\": \"5.0\"}'",
                        "BIOHUB_SCORE_AXIS = 'public 0.941 train16 + single-variable motion EMA alpha 0.4'", "score axis")
    text = replace_once(text, 'os.environ["BIOHUB_DET_THRESHOLD"] = "0.965"\n',
                        'os.environ["BIOHUB_DET_THRESHOLD"] = "0.965"\n'
                        'os.environ["BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "0.5"\n'
                        'os.environ["BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"\n', "EMA environment")
    set_source(config, text)

    guard = find_code(notebook["cells"], "Configuration drift detected")
    text = source(guard)
    text = replace_once(text, '    "BIOHUB_DET_THRESHOLD": 0.965,\n',
                        '    "BIOHUB_DET_THRESHOLD": 0.965,\n'
                        '    "BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT": 0.5,\n'
                        '    "BIOHUB_MOTION_RELINK_EMA_ALPHA": 0.4,\n', "guard values")
    old_report = ('print("Baseline: fixed-90 dual-seed clean pipeline (public LB 0.913)")\n'
                  'print("Single model-level change: harmonic mutual-support association fusion")\n'
                  'print("Reverse-time association weight: 0.200")')
    new_report = ('print("Parent: val_039 frozen Public LB 0.941 train16 baseline")\n'
                  'print("Single algorithm change: one-frame velocity replaced by per-track EMA")\n'
                  'print("EMA alpha: 0.4; unchanged velocity multiplier: 0.5")')
    text = replace_once(text, old_report, new_report, "guard report")
    set_source(guard, text)

    imports = find_code(notebook["cells"], "MOTION_RELINK_VELOCITY_WEIGHT =")
    text = source(imports)
    text = replace_once(text,
                        'MOTION_RELINK_VELOCITY_WEIGHT = float(os.environ.get("BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT", "0.5"))\n',
                        'MOTION_RELINK_VELOCITY_WEIGHT = float(os.environ.get("BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT", "0.5"))\n'
                        'MOTION_RELINK_EMA_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_ALPHA", "0.4"))\n',
                        "EMA parse")
    text = replace_once(text, '    "motion_relink_velocity_weight": MOTION_RELINK_VELOCITY_WEIGHT,\n',
                        '    "motion_relink_velocity_weight": MOTION_RELINK_VELOCITY_WEIGHT,\n'
                        '    "motion_relink_velocity_estimator": "per_track_ema",\n'
                        '    "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,\n', "EMA display")
    set_source(imports, text)

    postprocess = find_code(notebook["cells"], "def motion_relink_edges")
    text = source(postprocess)
    text = replace_once(text,
                        "    predecessor_position_um: dict[int, np.ndarray] = {}\n    selected_edges: list[dict[str, object]] = []\n",
                        "    predecessor_position_um: dict[int, np.ndarray] = {}\n    velocity_um: dict[int, np.ndarray] = {}\n    selected_edges: list[dict[str, object]] = []\n",
                        "velocity state")
    text = replace_once(text,
                        "            prev_pos = predecessor_position_um.get(source_id)\n            if prev_pos is None:\n                predicted = source_pos\n            else:\n                predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * (source_pos - prev_pos)\n",
                        "            prev_pos = predecessor_position_um.get(source_id)\n            velocity = velocity_um.get(source_id)\n            if velocity is not None:\n                predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * velocity\n                stats[\"motion_relink_ema_predictions\"] = stats.get(\"motion_relink_ema_predictions\", 0) + 1\n            elif prev_pos is None:\n                predicted = source_pos\n            else:\n                predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * (source_pos - prev_pos)\n                stats[\"motion_relink_one_frame_fallbacks\"] = stats.get(\"motion_relink_one_frame_fallbacks\", 0) + 1\n",
                        "EMA prediction")
    text = replace_once(text,
                        "            predecessor_position_um[target_id] = position_um[source_id]\n        stats[\"motion_relink_frames\"] += 1\n",
                        "            predecessor_position_um[target_id] = position_um[source_id]\n            step_velocity = position_um[target_id] - position_um[source_id]\n            previous_velocity = velocity_um.get(source_id)\n            velocity_um[target_id] = (\n                step_velocity\n                if previous_velocity is None\n                else MOTION_RELINK_EMA_ALPHA * step_velocity\n                + (1.0 - MOTION_RELINK_EMA_ALPHA) * previous_velocity\n            )\n        stats[\"motion_relink_frames\"] += 1\n",
                        "EMA update")
    set_source(postprocess, text)

    scorer = find_code(notebook["cells"], 'row["t_true_source"]')
    text = source(scorer)
    text = replace_once(text,
                        '        row["t_true_source"] = "estimated_number_of_nodes" if t_true is not None else "MISSING"\n        rows_this_config.append(row)\n',
                        '        row["t_true_source"] = "estimated_number_of_nodes" if t_true is not None else "MISSING"\n'
                        '        row["motion_relink_ema_predictions"] = int(_stage_stats.get("motion_relink_ema_predictions", 0))\n'
                        '        row["motion_relink_one_frame_fallbacks"] = int(_stage_stats.get("motion_relink_one_frame_fallbacks", 0))\n'
                        '        row["motion_relink_skipped_large_frame"] = int(_stage_stats.get("motion_relink_skipped_large_frame", 0))\n'
                        '        rows_this_config.append(row)\n', "EMA telemetry")
    set_source(scorer, text)

    preflight = find_code(notebook["cells"], "# Embedded after test inference and audit")
    prefix = source(preflight).split("# Embedded after test inference and audit", 1)[0]
    prefix = prefix.replace("EXPECTED_SUBMISSION_SHA =", "PARENT_SUBMISSION_SHA =", 1)
    set_source(preflight, prefix + (ROOT / "scripts/public_0941_motion_ema_preflight.py").read_text(encoding="utf-8"))

    contract = find_code(notebook["cells"], "# Embedded final contract")
    set_source(contract, (ROOT / "scripts/public_0941_motion_ema_contract.py").read_text(encoding="utf-8"))

    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            cell["outputs"], cell["execution_count"] = [], None
            ast.parse(source(cell))

    if len(notebook["cells"]) != len(baseline_cells):
        raise ValueError("Notebook cell count changed unexpectedly")
    return notebook


if __name__ == "__main__":
    TARGET.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(TARGET)
