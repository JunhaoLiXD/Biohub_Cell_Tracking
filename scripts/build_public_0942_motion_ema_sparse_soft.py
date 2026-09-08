"""Build the reviewed sparse soft-EMA candidate from telemetry-v2 evidence."""
from __future__ import annotations

import ast
import copy
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DONOR = ROOT / ".private/current/public_0942_motion_ema_telemetry_v2.ipynb"
BEHAVIOR_PARENT = ROOT / ".private/current/public_0941_motion_ema.ipynb"
PARENT_METRICS = ROOT / "experiments/repro_041_public_0941_motion_ema/metrics.json"
PARENT_ROWS = ROOT / "experiments/repro_041_public_0941_motion_ema/artifacts/validator_results.csv"
TARGET = ROOT / ".private/current/public_0942_motion_ema_sparse_soft.ipynb"
DONOR_SHA = "ee0ec68cf97d9ce5928dbae2090c4e98973133c01714387fdd842c4a3b4c1420"
BEHAVIOR_PARENT_SHA = "914104fffa12f92de10521cd1a106a415a7b353eac5b5c460b04daf83ec96453"
PARENT_METRICS_SHA = "63e8dd963b0358a2231155826a83eed32ff4a68c0635c5b40a19f365350fc4dc"
PARENT_ROWS_SHA = "2e6b0bf3a02f3a74b2115b23342ddd22bd8340d0faa9db8893b4733dadb9da85"
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


def _reference():
    metrics = json.loads(PARENT_METRICS.read_text(encoding="utf-8"))
    with PARENT_ROWS.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return {
        "aggregate": {
            "primary_metric": metrics["primary_metric"],
            "adjusted_edge_jaccard": metrics["validation"]["adjusted_edge_jaccard"],
            "division_jaccard": metrics["validation"]["division_jaccard"],
        },
        "specimens": {
            specimen: {
                key: metrics["specimen_metrics"][specimen][key]
                for key in ("primary_metric", "adjusted_edge_jaccard", "division_jaccard")
            }
            for specimen in ("44b6", "6bba")
        },
        "videos": {
            row["stem"]: {
                "adjusted_edge_jaccard": float(row["adjusted_edge_jaccard"]),
                "div_tp": int(row["div_tp"]),
                "div_fp": int(row["div_fp"]),
                "div_fn": int(row["div_fn"]),
            }
            for row in rows
        },
        "division_counts": metrics["metrics"]["division_counts"],
        "submission_sha256": PARENT_SUBMISSION_SHA,
    }


def build():
    for path, expected in (
        (DONOR, DONOR_SHA),
        (BEHAVIOR_PARENT, BEHAVIOR_PARENT_SHA),
        (PARENT_METRICS, PARENT_METRICS_SHA),
        (PARENT_ROWS, PARENT_ROWS_SHA),
    ):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Frozen input changed: {path}")

    notebook = json.loads(DONOR.read_text(encoding="utf-8"))
    donor_cells = copy.deepcopy(notebook["cells"])
    notebook["cells"][0] = {
        "cell_type": "markdown",
        "metadata": {},
        "source": (
            "# Public 0.942 sparse soft motion EMA\n\n"
            "Behavior parent: `repro_041_public_0941_motion_ema`. Evidence donor: "
            "`diag_045_public_0942_motion_ema_telemetry_v2`. Base EMA alpha remains 0.4. "
            "The only algorithmic change is a label-free one-update alpha 0.6 when normalized "
            "velocity innovation is greater than 1.25, source track age is at least 3, a finite "
            "second assignment candidate exists, and the selected assignment margin is at least "
            "0.5. All other updates retain alpha 0.4. Velocity weight, models, checkpoints, "
            "validation samples, and scorer remain frozen. No leaderboard submission is performed.\n"
        ).splitlines(keepends=True),
    }

    config = find_code(notebook["cells"], "BIOHUB_SCORE_AXIS")
    text = source(config)
    text = replace_once(
        text,
        "BIOHUB_SCORE_AXIS = 'public 0.942 fixed-alpha online motion telemetry v2'",
        "BIOHUB_SCORE_AXIS = 'public 0.942 sparse soft motion EMA'",
        "score axis",
    )
    text = replace_once(
        text,
        'os.environ["BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"\n',
        'os.environ["BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"\n'
        'os.environ["BIOHUB_MOTION_RELINK_EMA_SOFT_ALPHA"] = "0.6"\n'
        'os.environ["BIOHUB_MOTION_RELINK_EMA_INNOVATION_THRESHOLD"] = "1.25"\n'
        'os.environ["BIOHUB_MOTION_RELINK_EMA_MIN_TRACK_AGE"] = "3"\n'
        'os.environ["BIOHUB_MOTION_RELINK_EMA_MIN_ASSIGNMENT_MARGIN"] = "0.5"\n',
        "sparse soft environment",
    )
    set_source(config, text)

    guard = find_code(notebook["cells"], "Configuration drift detected")
    text = source(guard)
    text = replace_once(
        text,
        '    "BIOHUB_MOTION_RELINK_EMA_ALPHA": 0.4,\n',
        '    "BIOHUB_MOTION_RELINK_EMA_ALPHA": 0.4,\n'
        '    "BIOHUB_MOTION_RELINK_EMA_SOFT_ALPHA": 0.6,\n'
        '    "BIOHUB_MOTION_RELINK_EMA_INNOVATION_THRESHOLD": 1.25,\n'
        '    "BIOHUB_MOTION_RELINK_EMA_MIN_TRACK_AGE": 3,\n'
        '    "BIOHUB_MOTION_RELINK_EMA_MIN_ASSIGNMENT_MARGIN": 0.5,\n',
        "sparse soft guard values",
    )
    text = replace_once(
        text,
        'print("EMA alpha: 0.4; unchanged velocity multiplier: 0.5")',
        'print("Sparse soft EMA: alpha 0.6 only at innovation > 1.25, age >= 3, finite margin >= 0.5")\n'
        'print("Base alpha: 0.4; unchanged velocity multiplier: 0.5")',
        "guard report",
    )
    set_source(guard, text)

    imports = find_code(notebook["cells"], "MOTION_RELINK_EMA_ALPHA =")
    text = source(imports)
    text = replace_once(
        text,
        'MOTION_RELINK_EMA_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_ALPHA", "0.4"))\n',
        'MOTION_RELINK_EMA_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_ALPHA", "0.4"))\n'
        'MOTION_RELINK_EMA_SOFT_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_SOFT_ALPHA", "0.6"))\n'
        'MOTION_RELINK_EMA_INNOVATION_THRESHOLD = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_INNOVATION_THRESHOLD", "1.25"))\n'
        'MOTION_RELINK_EMA_MIN_TRACK_AGE = int(os.environ.get("BIOHUB_MOTION_RELINK_EMA_MIN_TRACK_AGE", "3"))\n'
        'MOTION_RELINK_EMA_MIN_ASSIGNMENT_MARGIN = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_MIN_ASSIGNMENT_MARGIN", "0.5"))\n',
        "sparse soft constants",
    )
    text = replace_once(
        text,
        '    "motion_relink_velocity_estimator": "per_track_ema",\n'
        '    "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,\n',
        '    "motion_relink_velocity_estimator": "sparse_soft_ema",\n'
        '    "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,\n'
        '    "motion_relink_ema_soft_alpha": MOTION_RELINK_EMA_SOFT_ALPHA,\n'
        '    "motion_relink_ema_innovation_threshold": MOTION_RELINK_EMA_INNOVATION_THRESHOLD,\n'
        '    "motion_relink_ema_min_track_age": MOTION_RELINK_EMA_MIN_TRACK_AGE,\n'
        '    "motion_relink_ema_min_assignment_margin": MOTION_RELINK_EMA_MIN_ASSIGNMENT_MARGIN,\n',
        "sparse soft display",
    )
    set_source(imports, text)

    postprocess = find_code(notebook["cells"], "def motion_relink_edges")
    text = source(postprocess)
    text = replace_once(
        text,
        "def motion_relink_edges(\n",
        "def _use_sparse_soft_alpha(innovation_ratio, source_track_age, assignment_margin):\n"
        "    return bool(\n"
        "        innovation_ratio > MOTION_RELINK_EMA_INNOVATION_THRESHOLD\n"
        "        and source_track_age >= MOTION_RELINK_EMA_MIN_TRACK_AGE\n"
        "        and bool(np.isfinite(assignment_margin))\n"
        "        and assignment_margin >= MOTION_RELINK_EMA_MIN_ASSIGNMENT_MARGIN\n"
        "    )\n\n\n"
        "def motion_relink_edges(\n",
        "sparse soft predicate",
    )
    old_update = (
        "            if MOTION_RELINK_TELEMETRY and previous_velocity is not None:\n"
        "                innovation_scale = max(float(np.linalg.norm(step_velocity)),\n"
        "                                       float(np.linalg.norm(previous_velocity)), 1e-6)\n"
        "                innovation_ratio = float(np.linalg.norm(step_velocity - previous_velocity)) / innovation_scale\n"
        "                telemetry_innovation.append(innovation_ratio)\n"
        "                telemetry_track_age.append(source_track_age)\n"
        "                telemetry_assignment_margin.append(assignment_margin)\n"
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
        "                stats[\"motion_relink_sparse_initial_updates\"] = stats.get(\"motion_relink_sparse_initial_updates\", 0) + 1\n"
        "            else:\n"
        "                innovation_scale = max(float(np.linalg.norm(step_velocity)),\n"
        "                                       float(np.linalg.norm(previous_velocity)), 1e-6)\n"
        "                innovation_ratio = float(np.linalg.norm(step_velocity - previous_velocity)) / innovation_scale\n"
        "                use_soft_alpha = _use_sparse_soft_alpha(\n"
        "                    innovation_ratio, source_track_age, assignment_margin)\n"
        "                effective_alpha = MOTION_RELINK_EMA_SOFT_ALPHA if use_soft_alpha else MOTION_RELINK_EMA_ALPHA\n"
        "                counter = \"motion_relink_sparse_soft_updates\" if use_soft_alpha else \"motion_relink_sparse_base_updates\"\n"
        "                stats[counter] = stats.get(counter, 0) + 1\n"
        "                if MOTION_RELINK_TELEMETRY:\n"
        "                    telemetry_innovation.append(innovation_ratio)\n"
        "                    telemetry_track_age.append(source_track_age)\n"
        "                    telemetry_assignment_margin.append(assignment_margin)\n"
        "                velocity_um[target_id] = (\n"
        "                    effective_alpha * step_velocity\n"
        "                    + (1.0 - effective_alpha) * previous_velocity\n"
        "                )\n"
    )
    text = replace_once(text, old_update, new_update, "sparse soft velocity update")
    set_source(postprocess, text)

    scorer = find_code(notebook["cells"], 'row["motion_relink_ema_predictions"]')
    text = source(scorer)
    text = replace_once(
        text,
        '        row["motion_relink_skipped_large_frame"] = int(_stage_stats.get("motion_relink_skipped_large_frame", 0))\n',
        '        row["motion_relink_skipped_large_frame"] = int(_stage_stats.get("motion_relink_skipped_large_frame", 0))\n'
        '        row["motion_relink_sparse_soft_updates"] = int(_stage_stats.get("motion_relink_sparse_soft_updates", 0))\n'
        '        row["motion_relink_sparse_base_updates"] = int(_stage_stats.get("motion_relink_sparse_base_updates", 0))\n'
        '        row["motion_relink_sparse_initial_updates"] = int(_stage_stats.get("motion_relink_sparse_initial_updates", 0))\n',
        "sparse execution rows",
    )
    set_source(scorer, text)

    preflight = find_code(notebook["cells"], "# Embedded after candidate test inference")
    prefix = source(preflight).split("# Embedded after candidate test inference", 1)[0]
    prefix = replace_once(
        prefix,
        "PARENT_SUBMISSION_SHA = 'bf66c879298e71c5cce0326fbac5956ca567a344ae28f0d402dfc5003fba52bd'",
        f"PARENT_SUBMISSION_SHA = '{PARENT_SUBMISSION_SHA}'",
        "parent submission SHA",
    )
    set_source(
        preflight,
        prefix + (ROOT / "scripts/public_0942_motion_ema_sparse_soft_preflight.py").read_text(encoding="utf-8"),
    )

    contract = find_code(notebook["cells"], "# Embedded final contract")
    set_source(
        contract,
        f"SPARSE_SOFT_EXPECTED = {_reference()!r}\n"
        + (ROOT / "scripts/public_0942_motion_ema_sparse_soft_contract.py").read_text(encoding="utf-8"),
    )

    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            cell["outputs"], cell["execution_count"] = [], None
            ast.parse(source(cell))
    if len(notebook["cells"]) != len(donor_cells):
        raise ValueError("Notebook cell count changed unexpectedly")
    return notebook


if __name__ == "__main__":
    TARGET.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(TARGET)
