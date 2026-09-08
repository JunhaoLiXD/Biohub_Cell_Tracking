"""Build the corrected and decomposed telemetry-only diagnostic."""
from __future__ import annotations

import ast
import copy
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / ".private/current/public_0942_motion_ema_online_telemetry.ipynb"
BEHAVIOR_PARENT = ROOT / ".private/current/public_0941_motion_ema.ipynb"
PARENT_METRICS = ROOT / "experiments/repro_041_public_0941_motion_ema/metrics.json"
PARENT_ROWS = ROOT / "experiments/repro_041_public_0941_motion_ema/artifacts/validator_results.csv"
TARGET = ROOT / ".private/current/public_0942_motion_ema_telemetry_v2.ipynb"
PARENT_SHA = "c418bce2805486d16533cfd296bd1da5dd0dbcd283cf922f9186f23238fc0c3a"
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
                "div_tp": int(row["div_tp"]), "div_fp": int(row["div_fp"]),
                "div_fn": int(row["div_fn"]),
            }
            for row in rows
        },
        "division_counts": metrics["metrics"]["division_counts"],
        "ema_execution": metrics["metrics"]["motion_relink_ema_execution"],
        "submission_sha256": PARENT_SUBMISSION_SHA,
    }


def build():
    for path, expected in (
        (PARENT, PARENT_SHA), (PARENT_METRICS, PARENT_METRICS_SHA),
        (PARENT_ROWS, PARENT_ROWS_SHA),
    ):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Frozen parent input changed: {path}")

    notebook = json.loads(PARENT.read_text(encoding="utf-8"))
    parent_cells = copy.deepcopy(notebook["cells"])
    notebook["cells"][0] = {
        "cell_type": "markdown", "metadata": {},
        "source": (
            "# Public 0.942 fixed-alpha motion telemetry diagnostic v2\n\n"
            "Behavior parent: `repro_041_public_0941_motion_ema`. Failed diagnostic predecessor: "
            "`diag_044_public_0942_motion_ema_online_telemetry`. Fixed alpha 0.4 and all prediction "
            "decisions remain unchanged. This version converts telemetry counts to native Python "
            "integers, strictly tests JSON serialization, decomposes the age and assignment-margin "
            "guards, records finite-margin coverage, and measures informative innovation thresholds "
            "1.0, 1.25, 1.5, and 1.75. Telemetry remains label-free and read-only. No leaderboard "
            "submission is performed.\n"
        ).splitlines(keepends=True),
    }

    config = find_code(notebook["cells"], "BIOHUB_SCORE_AXIS")
    text = source(config)
    text = replace_once(
        text,
        "BIOHUB_SCORE_AXIS = 'public 0.942 fixed-alpha online motion telemetry'",
        "BIOHUB_SCORE_AXIS = 'public 0.942 fixed-alpha online motion telemetry v2'",
        "score axis",
    )
    set_source(config, text)

    postprocess = find_code(notebook["cells"], "def motion_relink_edges")
    text = source(postprocess)
    text = replace_once(
        text,
        "def motion_relink_edges(\n",
        "def _native_true_count(values):\n"
        "    return int(sum(bool(value) for value in values))\n\n\n"
        "def motion_relink_edges(\n",
        "native telemetry counter",
    )
    old_summary = (
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
    )
    new_summary = (
        '    if MOTION_RELINK_TELEMETRY:\n'
        '        stats["motion_relink_telemetry_eligible_updates"] = int(len(telemetry_innovation))\n'
        '        finite_margin_flags = [bool(np.isfinite(value)) for value in telemetry_assignment_margin]\n'
        '        finite_margins = [value for value, finite in zip(telemetry_assignment_margin,\n'
        '                                                          finite_margin_flags) if finite]\n'
        '        stats["motion_relink_telemetry_finite_margin_updates"] = _native_true_count(\n'
        '            finite_margin_flags)\n'
        '        stats["motion_relink_telemetry_nonfinite_margin_updates"] = int(\n'
        '            len(telemetry_assignment_margin) - len(finite_margins))\n'
        '        for prefix, values in (("innovation", telemetry_innovation),\n'
        '                               ("track_age", telemetry_track_age),\n'
        '                               ("assignment_margin", finite_margins)):\n'
        '            if not values:\n'
        '                raise RuntimeError(f"Missing online telemetry values for {prefix}")\n'
        '            for quantile in (10, 50, 90, 95, 99):\n'
        '                stats[f"motion_relink_telemetry_{prefix}_q{quantile}"] = float(\n'
        '                    np.quantile(values, quantile / 100.0))\n'
        '        for threshold in (1.0, 1.25, 1.5, 1.75):\n'
        '            code = int(round(threshold * 1000))\n'
        '            observations = tuple(zip(telemetry_innovation, telemetry_track_age,\n'
        '                                     telemetry_assignment_margin))\n'
        '            stats[f"motion_relink_telemetry_proposed_gt_{code}"] = _native_true_count(\n'
        '                innovation > threshold for innovation, _, _ in observations)\n'
        '            stats[f"motion_relink_telemetry_age_ge3_gt_{code}"] = _native_true_count(\n'
        '                innovation > threshold and age >= 3\n'
        '                for innovation, age, _ in observations)\n'
        '            stats[f"motion_relink_telemetry_finite_margin_gt_{code}"] = _native_true_count(\n'
        '                innovation > threshold and bool(np.isfinite(margin))\n'
        '                for innovation, _, margin in observations)\n'
        '            stats[f"motion_relink_telemetry_margin_ge0500_gt_{code}"] = _native_true_count(\n'
        '                innovation > threshold and bool(np.isfinite(margin)) and margin >= 0.5\n'
        '                for innovation, _, margin in observations)\n'
        '            stats[f"motion_relink_telemetry_guarded_gt_{code}"] = _native_true_count(\n'
        '                innovation > threshold and age >= 3 and bool(np.isfinite(margin)) and margin >= 0.5\n'
        '                for innovation, age, margin in observations)\n'
    )
    text = replace_once(text, old_summary, new_summary, "corrected telemetry summary")
    set_source(postprocess, text)

    preflight = find_code(notebook["cells"], "# Embedded after candidate test inference")
    prefix = source(preflight).split("# Embedded after candidate test inference", 1)[0]
    set_source(
        preflight,
        prefix + (ROOT / "scripts/public_0942_motion_ema_telemetry_v2_preflight.py").read_text(encoding="utf-8"),
    )

    contract = find_code(notebook["cells"], "# Embedded final contract")
    set_source(
        contract,
        f"TELEMETRY_V2_EXPECTED = {_reference()!r}\n"
        + (ROOT / "scripts/public_0942_motion_ema_telemetry_v2_contract.py").read_text(encoding="utf-8"),
    )

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
