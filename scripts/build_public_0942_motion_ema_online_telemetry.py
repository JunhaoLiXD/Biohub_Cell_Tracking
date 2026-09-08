"""Build a telemetry-only diagnostic from the reproduced fixed-alpha-0.4 parent."""
from __future__ import annotations

import ast
import copy
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / ".private/current/public_0941_motion_ema.ipynb"
PARENT_METRICS = ROOT / "experiments/repro_041_public_0941_motion_ema/metrics.json"
PARENT_ROWS = ROOT / "experiments/repro_041_public_0941_motion_ema/artifacts/validator_results.csv"
TARGET = ROOT / ".private/current/public_0942_motion_ema_online_telemetry.ipynb"
PARENT_SHA = "914104fffa12f92de10521cd1a106a415a7b353eac5b5c460b04daf83ec96453"
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
            specimen: {key: metrics["specimen_metrics"][specimen][key]
                       for key in ("primary_metric", "adjusted_edge_jaccard", "division_jaccard")}
            for specimen in ("44b6", "6bba")
        },
        "videos": {
            row["stem"]: {
                "adjusted_edge_jaccard": float(row["adjusted_edge_jaccard"]),
                "div_tp": int(row["div_tp"]), "div_fp": int(row["div_fp"]), "div_fn": int(row["div_fn"]),
            }
            for row in rows
        },
        "division_counts": metrics["metrics"]["division_counts"],
        "ema_execution": metrics["metrics"]["motion_relink_ema_execution"],
        "submission_sha256": PARENT_SUBMISSION_SHA,
    }


def build():
    for path, expected in (
        (PARENT, PARENT_SHA), (PARENT_METRICS, PARENT_METRICS_SHA), (PARENT_ROWS, PARENT_ROWS_SHA),
    ):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Frozen parent input changed: {path}")
    notebook = json.loads(PARENT.read_text(encoding="utf-8"))
    parent_cells = copy.deepcopy(notebook["cells"])
    notebook["cells"][0] = {
        "cell_type": "markdown", "metadata": {},
        "source": (
            "# Public 0.942 fixed-alpha motion telemetry diagnostic\n\n"
            "Parent: `repro_041_public_0941_motion_ema`, the exactly reproduced fixed-alpha-0.4 "
            "candidate with user-reported Public LB 0.942. Prediction behavior remains unchanged. "
            "The only change is read-only online telemetry for normalized velocity innovation, "
            "track age, local assignment-cost margin, and prospective threshold rates. Telemetry "
            "uses runtime selected positions and assignment costs only, with no specimen, video "
            "identity, or ground truth. Exact parent submission bytes and train16 metrics are hard "
            "gates. No leaderboard submission is performed.\n"
        ).splitlines(keepends=True),
    }

    config = find_code(notebook["cells"], "BIOHUB_SCORE_AXIS")
    text = source(config)
    text = replace_once(text,
                        "BIOHUB_SCORE_AXIS = 'public 0.941 train16 + single-variable motion EMA alpha 0.4'",
                        "BIOHUB_SCORE_AXIS = 'public 0.942 fixed-alpha online motion telemetry'",
                        "score axis")
    text = replace_once(text, 'os.environ["BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"\n',
                        'os.environ["BIOHUB_MOTION_RELINK_EMA_ALPHA"] = "0.4"\n'
                        'os.environ["BIOHUB_MOTION_RELINK_TELEMETRY"] = "1"\n',
                        "telemetry environment")
    set_source(config, text)

    guard = find_code(notebook["cells"], "Configuration drift detected")
    text = source(guard)
    text = replace_once(text, '    "BIOHUB_MOTION_RELINK_EMA_ALPHA": 0.4,\n',
                        '    "BIOHUB_MOTION_RELINK_EMA_ALPHA": 0.4,\n'
                        '    "BIOHUB_MOTION_RELINK_TELEMETRY": 1,\n',
                        "telemetry guard")
    text = replace_once(text, 'print("EMA alpha: 0.4; unchanged velocity multiplier: 0.5")',
                        'print("EMA alpha: 0.4; unchanged velocity multiplier: 0.5")\n'
                        'print("Read-only online motion telemetry: enabled")',
                        "telemetry report")
    set_source(guard, text)

    imports = find_code(notebook["cells"], "MOTION_RELINK_EMA_ALPHA =")
    text = source(imports)
    text = replace_once(text,
                        'MOTION_RELINK_EMA_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_ALPHA", "0.4"))\n',
                        'MOTION_RELINK_EMA_ALPHA = float(os.environ.get("BIOHUB_MOTION_RELINK_EMA_ALPHA", "0.4"))\n'
                        'MOTION_RELINK_TELEMETRY = os.environ.get("BIOHUB_MOTION_RELINK_TELEMETRY", "0") != "0"\n',
                        "telemetry constant")
    text = replace_once(text, '    "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,\n',
                        '    "motion_relink_ema_alpha": MOTION_RELINK_EMA_ALPHA,\n'
                        '    "motion_relink_telemetry": MOTION_RELINK_TELEMETRY,\n',
                        "telemetry display")
    set_source(imports, text)

    postprocess = find_code(notebook["cells"], "def motion_relink_edges")
    text = source(postprocess)
    text = replace_once(text,
                        '    selected_edges: list[dict[str, object]] = []\n',
                        '    selected_edges: list[dict[str, object]] = []\n'
                        '    telemetry_innovation: list[float] = []\n'
                        '    telemetry_track_age: list[int] = []\n'
                        '    telemetry_assignment_margin: list[float] = []\n'
                        '    track_age: dict[int, int] = {}\n',
                        "telemetry accumulators")
    text = replace_once(text,
                        '    ) -> list[tuple[int, int, float, float, float]]:\n',
                        '    ) -> list[tuple[int, int, float, float, float, float]]:\n',
                        "assignment return annotation")
    text = replace_once(text,
                        '        matches: list[tuple[int, int, float, float, float]] = []\n',
                        '        matches: list[tuple[int, int, float, float, float, float]] = []\n',
                        "assignment list annotation")
    old_append = (
        '            matches.append((\n'
        '                source_ids[int(r)],\n'
        '                target_ids[int(c)],\n'
        '                float(raw_dist[r, c]),\n'
        '                float(motion_dist[r, c]),\n'
        '                float(prob_matrix[r, c]),\n'
        '            ))\n'
    )
    new_append = (
        '            alternatives = [float(cost[r, k]) for k in range(len(target_ids))\n'
        '                            if k != int(c) and cost[r, k] < big]\n'
        '            assignment_margin = (\n'
        '                min(alternatives) - float(cost[r, c]) if alternatives else float("nan")\n'
        '            )\n'
        '            matches.append((\n'
        '                source_ids[int(r)],\n'
        '                target_ids[int(c)],\n'
        '                float(raw_dist[r, c]),\n'
        '                float(motion_dist[r, c]),\n'
        '                float(prob_matrix[r, c]),\n'
        '                assignment_margin,\n'
        '            ))\n'
    )
    text = replace_once(text, old_append, new_append, "assignment margin")
    text = replace_once(text,
                        '        frame_matches: list[tuple[int, int, float, float, str, float]] = []\n',
                        '        frame_matches: list[tuple[int, int, float, float, str, float, float]] = []\n',
                        "frame match annotation")
    text = replace_once(text,
                        '            for source_id, target_id, raw, motion, prob in matches:\n',
                        '            for source_id, target_id, raw, motion, prob, assignment_margin in matches:\n',
                        "assignment unpack")
    text = replace_once(text,
                        '                frame_matches.append((source_id, target_id, raw, motion, pass_name, prob))\n',
                        '                frame_matches.append((source_id, target_id, raw, motion, pass_name, prob, assignment_margin))\n',
                        "frame match telemetry")
    text = replace_once(text,
                        '        for source_id, target_id, raw, motion, pass_name, prob in frame_matches:\n',
                        '        for source_id, target_id, raw, motion, pass_name, prob, assignment_margin in frame_matches:\n',
                        "frame unpack")
    old_update = (
        '            previous_velocity = velocity_um.get(source_id)\n'
        '            velocity_um[target_id] = (\n'
        '                step_velocity\n'
        '                if previous_velocity is None\n'
        '                else MOTION_RELINK_EMA_ALPHA * step_velocity\n'
        '                + (1.0 - MOTION_RELINK_EMA_ALPHA) * previous_velocity\n'
        '            )\n'
    )
    new_update = (
        '            previous_velocity = velocity_um.get(source_id)\n'
        '            source_track_age = track_age.get(source_id, 1)\n'
        '            track_age[target_id] = source_track_age + 1\n'
        '            if MOTION_RELINK_TELEMETRY and previous_velocity is not None:\n'
        '                innovation_scale = max(float(np.linalg.norm(step_velocity)),\n'
        '                                       float(np.linalg.norm(previous_velocity)), 1e-6)\n'
        '                innovation_ratio = float(np.linalg.norm(step_velocity - previous_velocity)) / innovation_scale\n'
        '                telemetry_innovation.append(innovation_ratio)\n'
        '                telemetry_track_age.append(source_track_age)\n'
        '                telemetry_assignment_margin.append(assignment_margin)\n'
        '            velocity_um[target_id] = (\n'
        '                step_velocity\n'
        '                if previous_velocity is None\n'
        '                else MOTION_RELINK_EMA_ALPHA * step_velocity\n'
        '                + (1.0 - MOTION_RELINK_EMA_ALPHA) * previous_velocity\n'
        '            )\n'
    )
    text = replace_once(text, old_update, new_update, "observational velocity telemetry")
    telemetry_summary = (
        '    if MOTION_RELINK_TELEMETRY:\n'
        '        stats["motion_relink_telemetry_eligible_updates"] = len(telemetry_innovation)\n'
        '        finite_margins = [value for value in telemetry_assignment_margin if np.isfinite(value)]\n'
        '        for prefix, values in (("innovation", telemetry_innovation),\n'
        '                               ("track_age", telemetry_track_age),\n'
        '                               ("assignment_margin", finite_margins)):\n'
        '            if not values:\n'
        '                raise RuntimeError(f"Missing online telemetry values for {prefix}")\n'
        '            for quantile in (10, 50, 90, 95, 99):\n'
        '                stats[f"motion_relink_telemetry_{prefix}_q{quantile}"] = float(\n'
        '                    np.quantile(values, quantile / 100.0))\n'
        '        for threshold in (1.0, 1.25, 1.5, 2.0, 3.0):\n'
        '            code = int(round(threshold * 1000))\n'
        '            stats[f"motion_relink_telemetry_proposed_gt_{code}"] = sum(\n'
        '                innovation > threshold for innovation in telemetry_innovation)\n'
        '            stats[f"motion_relink_telemetry_guarded_gt_{code}"] = sum(\n'
        '                innovation > threshold and age >= 3 and np.isfinite(margin) and margin >= 0.5\n'
        '                for innovation, age, margin in zip(telemetry_innovation, telemetry_track_age,\n'
        '                                                   telemetry_assignment_margin))\n'
        '\n'
        '    stats["motion_relink_edges"] = len(selected_edges)\n'
    )
    text = replace_once(text,
                        '    stats["motion_relink_edges"] = len(selected_edges)\n',
                        telemetry_summary,
                        "telemetry summary")
    set_source(postprocess, text)

    preflight = find_code(notebook["cells"], "# Embedded after candidate test inference")
    prefix = source(preflight).split("# Embedded after candidate test inference", 1)[0]
    set_source(preflight, prefix + (ROOT / "scripts/public_0942_motion_ema_online_telemetry_preflight.py").read_text(encoding="utf-8"))

    contract = find_code(notebook["cells"], "# Embedded final contract")
    expected = _reference()
    set_source(contract, f"TELEMETRY_EXPECTED = {expected!r}\n" +
               (ROOT / "scripts/public_0942_motion_ema_online_telemetry_contract.py").read_text(encoding="utf-8"))

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
