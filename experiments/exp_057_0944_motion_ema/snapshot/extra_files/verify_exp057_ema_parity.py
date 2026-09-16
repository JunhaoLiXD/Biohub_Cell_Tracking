"""Unit-level parity/behaviour proof for the exp_057 EMA edit.

Extracts ``motion_relink_edges`` from the repro_048 base notebook and the exp_057
notebook and, on synthetic multi-frame inputs, asserts:

1.  EMA OFF (``MOTION_RELINK_EMA_ALPHA = None``): exp_057's function returns edges
    IDENTICAL to the repro_048 base function (byte-identical action set) -> the
    off-switch reduces exactly to repro_048.
2.  EMA ON (0.4): the EMA branch is exercised
    (``motion_relink_ema_predictions > 0``) and, under non-constant motion, the
    relinked edge set differs from the base -> the change is real, not a no-op.

This does not replace the on-Kaggle EMA-off submission byte-parity to
``0319ba6d...`` (that runs at admission); it proves the code-level contract here.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from _bootstrap import PROJECT_ROOT

BASE_NB = PROJECT_ROOT / "experiments/repro_048_public_0946_exact_copy/snapshot/source/public_0946_edge_feature_tta_copy.ipynb"
EXP_NB = PROJECT_ROOT / ".private/current/exp057_0944_motion_ema.ipynb"


def _extract_func(nb_path: Path, name: str) -> str:
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        if f"def {name}" in src:
            lines = src.splitlines()
            start = next(i for i, l in enumerate(lines) if l.lstrip().startswith(f"def {name}"))
            base_indent = len(lines[start]) - len(lines[start].lstrip())
            body = [lines[start]]
            in_sig = True
            for l in lines[start + 1:]:
                if in_sig:
                    body.append(l)
                    if l.rstrip().endswith(":") and ")" in l:
                        in_sig = False
                    continue
                if l.strip() == "":
                    body.append(l)
                    continue
                ind = len(l) - len(l.lstrip())
                if ind <= base_indent and l.strip():
                    break
                body.append(l)
            return "\n".join(body)
    raise RuntimeError(f"{name} not found in {nb_path}")


def _make_namespace(ema_alpha):
    ns = {
        "np": np,
        "math": math,
        "linear_sum_assignment": linear_sum_assignment,
        "OUTPUT_MOTION_RELINK": True,
        "MOTION_RELINK_MAX_FRAME_NODES": 2600,
        "MOTION_RELINK_TIGHT_UM": 6.0,
        "MOTION_RELINK_RELAXED_UM": 10.0,
        "MOTION_RELINK_VELOCITY_WEIGHT": 0.5,
        "MOTION_RELINK_LEARNED_BONUS": 1.0,
        "MOTION_RELINK_EMA_ALPHA": ema_alpha,
        "VOXEL_SCALE_UM": (1.0, 1.0, 1.0),
    }
    exec(
        "def _position_um(node):\n"
        "    return np.array([float(node['z'])*VOXEL_SCALE_UM[0], float(node['y'])*VOXEL_SCALE_UM[1], float(node['x'])*VOXEL_SCALE_UM[2]], dtype=np.float64)\n",
        ns,
    )
    return ns


def _load(nb_path, name, ema_alpha):
    ns = _make_namespace(ema_alpha)
    exec(_extract_func(nb_path, name), ns)
    return ns[name]


def _nodes(accelerating: bool):
    """A few cells moving across 4 frames; accelerating motion makes EMA != one-frame."""
    nodes = {}
    nid = 0
    # Two tracks; positions in (z,y,x). Frame step grows if accelerating.
    tracks = [
        {"z0": 0.0, "y0": 0.0, "x0": 0.0, "vy": 2.0, "vx": 0.0},
        {"z0": 0.0, "y0": 20.0, "x0": 0.0, "vy": 0.0, "vx": 2.0},
    ]
    for t in range(4):
        for tr in tracks:
            accel = (1.0 + 0.6 * t) if accelerating else 1.0
            y = tr["y0"] + tr["vy"] * t * accel
            x = tr["x0"] + tr["vx"] * t * accel
            nodes[nid] = {"t": t, "z": tr["z0"], "y": y, "x": x}
            nid += 1
    return nodes


def _flip_nodes():
    """Accelerating single track + two ambiguous frame-3 targets so the EMA
    (smoothed) velocity predicts a different target than the one-frame velocity."""
    # Track A: y = 0, 4, 12 over frames 0,1,2 (instant vel 4 then 8).
    nodes = {
        0: {"t": 0, "z": 0.0, "y": 0.0, "x": 0.0},
        1: {"t": 1, "z": 0.0, "y": 4.0, "x": 0.0},
        2: {"t": 2, "z": 0.0, "y": 12.0, "x": 0.0},
        # frame 3 candidates: one near the one-frame prediction (16.0),
        # one near the EMA prediction (~14.8).
        3: {"t": 3, "z": 0.0, "y": 16.0, "x": 0.0},
        4: {"t": 3, "z": 0.0, "y": 14.8, "x": 0.0},
    }
    return nodes


def _run(func, nodes):
    stats = {
        "motion_relink_tight_edges": 0,
        "motion_relink_relaxed_edges": 0,
        "motion_relink_frames": 0,
        "motion_relink_edges": 0,
    }
    edges = func(dict(nodes), stats, {})
    # Compare COMPLETE ordered edge records IN THE EMITTED ORDER (every field, no
    # outer sort), so off==base means byte-equal relink output including ordering,
    # not merely matching connectivity.
    key = [tuple(sorted(e.items(), key=lambda kv: kv[0])) for e in edges]
    return key, stats


def main() -> int:
    base = _load(BASE_NB, "motion_relink_edges", None)  # base has no EMA ref
    exp_off = _load(EXP_NB, "motion_relink_edges", None)
    exp_on = _load(EXP_NB, "motion_relink_edges", 0.4)

    ok = True
    flip_seen = False
    scenarios = [
        ("constant-motion", _nodes(False)),
        ("accelerating-motion", _nodes(True)),
        ("ambiguous-flip", _flip_nodes()),
    ]
    for label, nodes in scenarios:
        base_key, _ = _run(base, nodes)
        off_key, off_stats = _run(exp_off, nodes)
        on_key, on_stats = _run(exp_on, nodes)

        parity = off_key == base_key
        ema_used = on_stats.get("motion_relink_ema_predictions", 0) > 0
        changed = on_key != base_key
        flip_seen = flip_seen or changed
        print(f"[{label}] base_edges={len(base_key)} off==base:{parity} "
              f"ema_predictions_on={on_stats.get('motion_relink_ema_predictions', 0)} "
              f"on!=base:{changed}")
        # Contract: EMA-off must equal base on EVERY scenario.
        if not parity:
            ok = False
            print(f"  FAIL parity: base={base_key} off={off_key}")
        # Contract: whenever a track spans >=3 frames the EMA branch must fire.
        if not ema_used:
            ok = False
            print(f"  FAIL: EMA branch never exercised with alpha=0.4 in {label}")

    # Contract: the EMA path must be exercised somewhere, and it must be able to
    # change the relinked edge set (materiality), or the change is a no-op.
    if not flip_seen:
        ok = False
        print("  FAIL: EMA never changed the relinked edge set in any scenario")
    print(f"EMA materially changed edges in >=1 scenario: {flip_seen}")
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
