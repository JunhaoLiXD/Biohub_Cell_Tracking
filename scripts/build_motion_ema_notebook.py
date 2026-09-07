"""Build the controlled train16 motion-EMA experiment notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".private" / "current" / "repro_public_0933.ipynb"
TARGET = ROOT / ".private" / "current" / "motion_ema_train16_v2.ipynb"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one {label} replacement target, found {count}")
    return source.replace(old, new, 1)


notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
notebook["cells"].insert(
    0,
    {
        "cell_type": "markdown",
        "id": "motion-ema-summary",
        "metadata": {},
        "source": (
            "# Controlled motion-EMA validation\n\n"
            "This experiment starts from the frozen public-0.933 train16 validator and changes "
            "only the motion-relink velocity estimator. The parent uses the latest one-frame "
            "displacement; this candidate carries a per-track exponential moving average with "
            "alpha 0.4. The velocity multiplier remains 0.5 and every detector, fusion, ILP, "
            "gap-closing, division, validation, and scoring setting remains fixed. The EMA rule "
            "is adapted from `grafael/biohub-ct-0940-ema`; no public outputs are used.\n"
        ).splitlines(keepends=True),
    },
)

code_cells = [cell for cell in notebook["cells"] if cell.get("cell_type") == "code"]

config = code_cells[0]
source = "".join(config["source"])
source = replace_once(
    source,
    "BIOHUB_SCORE_AXIS = 'train16 baseline + DeepCenter safe-division score audit'",
    "BIOHUB_SCORE_AXIS = 'train16 paired motion-relink EMA ablation'",
    "score-axis",
)
source = replace_once(
    source,
    'os.environ["BIOHUB_DET_THRESHOLD"] = "0.965"\n',
    'os.environ["BIOHUB_DET_THRESHOLD"] = "0.965"\n'
    'os.environ["BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "0.5"\n'
    'os.environ["BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"\n',
    "EMA environment",
)
config["source"] = source.splitlines(keepends=True)

guard = code_cells[1]
source = "".join(guard["source"])
source = replace_once(
    source,
    '    "BIOHUB_DET_THRESHOLD": 0.965,\n',
    '    "BIOHUB_DET_THRESHOLD": 0.965,\n'
    '    "BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT": 0.5,\n'
    '    "BIOHUB_MOTION_RELINK_EMA_ALPHA": 0.4,\n',
    "configuration guard",
)
source = replace_once(
    source,
    '    "BIOHUB_ILP_APPEARANCE_WEIGHT": 0.0,\n',
    '    "BIOHUB_ILP_APPEARANCE_WEIGHT": 0.0,\n'
    '    "BIOHUB_MOTION_RELINK_LEARNED_BONUS": 1.0,\n',
    "learned-bonus guard",
)
source = replace_once(
    source,
    'print("Diagnostic-only change: DeepCenter safe-division score audit enabled")\n'
    'print("Safe-division output remains ungated; reference threshold: 0.12")',
    'print("Single algorithm change: one-frame velocity replaced by per-track EMA")\n'
    'print("EMA alpha: 0.4; unchanged velocity multiplier: 0.5")',
    "guard summary",
)
guard["source"] = source.splitlines(keepends=True)

imports = code_cells[2]
source = "".join(imports["source"])
source = replace_once(
    source,
    'MOTION_RELINK_VELOCITY_WEIGHT = float(os.environ.get("BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT", "0.5"))\n',
    'MOTION_RELINK_VELOCITY_WEIGHT = float(os.environ.get("BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT", "0.5"))\n'
    'MOTION_RELINK_EMA_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_ALPHA", "0.4"))\n',
    "EMA configuration parse",
)
source = replace_once(
    source,
    '    "motion_relink_velocity_weight": MOTION_RELINK_VELOCITY_WEIGHT,\n',
    '    "motion_relink_velocity_weight": MOTION_RELINK_VELOCITY_WEIGHT,\n'
    '    "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,\n',
    "configuration display",
)
imports["source"] = source.splitlines(keepends=True)

postprocess = code_cells[5]
source = "".join(postprocess["source"])
source = replace_once(
    source,
    '    predecessor_position_um: dict[int, np.ndarray] = {}\n'
    '    selected_edges: list[dict[str, object]] = []\n',
    '    predecessor_position_um: dict[int, np.ndarray] = {}\n'
    '    velocity_um: dict[int, np.ndarray] = {}\n'
    '    selected_edges: list[dict[str, object]] = []\n',
    "velocity state",
)
source = replace_once(
    source,
    '            prev_pos = predecessor_position_um.get(source_id)\n'
    '            if prev_pos is None:\n'
    '                predicted = source_pos\n'
    '            else:\n'
    '                predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * (source_pos - prev_pos)\n',
    '            prev_pos = predecessor_position_um.get(source_id)\n'
    '            velocity = velocity_um.get(source_id)\n'
    '            if velocity is not None:\n'
    '                predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * velocity\n'
    '                stats["motion_relink_ema_predictions"] = stats.get("motion_relink_ema_predictions", 0) + 1\n'
    '            elif prev_pos is None:\n'
    '                predicted = source_pos\n'
    '            else:\n'
    '                predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * (source_pos - prev_pos)\n'
    '                stats["motion_relink_one_frame_fallbacks"] = stats.get("motion_relink_one_frame_fallbacks", 0) + 1\n',
    "EMA prediction",
)
source = replace_once(
    source,
    '            predecessor_position_um[target_id] = position_um[source_id]\n'
    '        stats["motion_relink_frames"] += 1\n',
    '            predecessor_position_um[target_id] = position_um[source_id]\n'
    '            step_velocity = position_um[target_id] - position_um[source_id]\n'
    '            previous_velocity = velocity_um.get(source_id)\n'
    '            velocity_um[target_id] = (\n'
    '                step_velocity\n'
    '                if previous_velocity is None\n'
    '                else MOTION_RELINK_EMA_ALPHA * step_velocity\n'
    '                + (1.0 - MOTION_RELINK_EMA_ALPHA) * previous_velocity\n'
    '            )\n'
    '        stats["motion_relink_frames"] += 1\n',
    "EMA update",
)
postprocess["source"] = source.splitlines(keepends=True)

scoring = code_cells[8]
source = "".join(scoring["source"])
source = replace_once(
    source,
    '        row["stem"] = stem\n'
    '        row["t_true_source"] = "estimated_number_of_nodes" if t_true is not None else "MISSING"\n'
    '        rows_this_config.append(row)\n',
    '        row["stem"] = stem\n'
    '        row["t_true_source"] = "estimated_number_of_nodes" if t_true is not None else "MISSING"\n'
    '        row["motion_relink_ema_predictions"] = int(_stage_stats.get("motion_relink_ema_predictions", 0))\n'
    '        row["motion_relink_one_frame_fallbacks"] = int(_stage_stats.get("motion_relink_one_frame_fallbacks", 0))\n'
    '        row["motion_relink_skipped_large_frame"] = int(_stage_stats.get("motion_relink_skipped_large_frame", 0))\n'
    '        rows_this_config.append(row)\n',
    "per-sample EMA telemetry",
)
scoring["source"] = source.splitlines(keepends=True)

contract = code_cells[-1]
source = "".join(contract["source"])
source = replace_once(
    source,
    '_controller_checks = {\n',
    '_controller_ema_execution_by_specimen = {\n'
    '    specimen: {\n'
    '        "ema_predictions": int(sum(\n'
    '            row.get("motion_relink_ema_predictions", 0)\n'
    '            for row in validator_sample_rows\n'
    '            if str(row["stem"]).split("_")[0] == specimen\n'
    '        )),\n'
    '        "one_frame_fallbacks": int(sum(\n'
    '            row.get("motion_relink_one_frame_fallbacks", 0)\n'
    '            for row in validator_sample_rows\n'
    '            if str(row["stem"]).split("_")[0] == specimen\n'
    '        )),\n'
    '        "skipped_large_frames": int(sum(\n'
    '            row.get("motion_relink_skipped_large_frame", 0)\n'
    '            for row in validator_sample_rows\n'
    '            if str(row["stem"]).split("_")[0] == specimen\n'
    '        )),\n'
    '    }\n'
    '    for specimen in _CONTROLLER_SPECIMENS\n'
    '}\n\n'
    '_controller_checks = {\n'
    '    "motion_ema_exercised_both_specimens": all(\n'
    '        values["ema_predictions"] > 0\n'
    '        for values in _controller_ema_execution_by_specimen.values()\n'
    '    ),\n',
    "EMA runtime contract",
)
source = replace_once(
    source,
    '    "baseline_output_preserved": _controller_math.isclose(\n'
    '        _controller_primary, _CONTROLLER_BASELINE_PRIMARY, abs_tol=1e-12\n'
    '    ),\n'
    '    "baseline_specimen_outputs_preserved": all(\n'
    '        _controller_math.isclose(\n'
    '            metrics.get("primary_metric", float("nan")),\n'
    '            _CONTROLLER_BASELINE_SPECIMEN[specimen],\n'
    '            abs_tol=1e-12,\n'
    '        )\n'
    '        for specimen, metrics in _controller_specimen_metrics.items()\n'
    '    ),\n',
    '',
    "diagnostic-only baseline-preservation gates",
)
source = replace_once(
    source,
    '        "validation_contract_passed": _controller_validation_contract_passed,\n',
    '        "validation_contract_passed": _controller_validation_contract_passed,\n'
    '        "motion_relink_ema_execution": _controller_ema_execution_by_specimen,\n',
    "EMA execution metrics",
)
source = replace_once(
    source,
    '            "gap_close_um": GAP_CLOSE_UM,\n',
    '            "gap_close_um": GAP_CLOSE_UM,\n'
    '            "motion_relink_velocity_estimator": "per_track_ema",\n'
    '            "motion_relink_velocity_weight": MOTION_RELINK_VELOCITY_WEIGHT,\n'
    '            "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,\n'
    '            "ema_reference_kernel": "grafael/biohub-ct-0940-ema",\n',
    "metrics provenance",
)
contract["source"] = source.splitlines(keepends=True)

TARGET.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
print(TARGET)
