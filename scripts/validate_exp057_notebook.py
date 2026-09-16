"""Dependency-free static admission check for the exp_057 notebook.

Runs in the controller's minimal .venv (no numpy). Proves that the exp_057
notebook is EXACTLY repro_048 plus the four scoped EMA edits, by reverse-applying
each patch and asserting the result is byte-identical to the base cell. Also
asserts the off-switch, env var, EMA state/propagation, and telemetry counters are
present. It does NOT execute the pipeline (see scripts/verify_exp057_ema_parity.py
for the numpy behaviour proof).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from build_exp057_0944_motion_ema import (
    BASE,
    BASE_SHA256,
    PATCHES,
    TARGET,
)


def _relink_cell_source(nb_path: Path) -> str:
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    for c in nb["cells"]:
        if c["cell_type"] == "code" and "def motion_relink_edges" in "".join(c["source"]):
            return "".join(c["source"])
    raise RuntimeError(f"motion_relink_edges cell not found in {nb_path}")


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else TARGET
    problems: list[str] = []

    base_raw = BASE.read_bytes()
    if hashlib.sha256(base_raw).hexdigest() != BASE_SHA256:
        problems.append("base repro_048 notebook SHA256 changed")

    base_cell = _relink_cell_source(BASE)
    exp_cell = _relink_cell_source(target)

    # 1) Reverse each patch (REPLACE -> FIND). The result must equal the base cell,
    #    proving exp_057 == base + exactly these four scoped edits.
    reversed_cell = exp_cell
    for name, find, replace in PATCHES:
        if replace not in reversed_cell:
            problems.append(f"expected patched region absent: {name}")
            continue
        if reversed_cell.count(replace) != 1:
            problems.append(f"patched region not unique: {name}")
        reversed_cell = reversed_cell.replace(replace, find, 1)
    if reversed_cell != base_cell:
        problems.append("reverse-patched exp_057 cell does not equal repro_048 base cell "
                        "(the change is not restricted to the four EMA edits)")

    # 2) Off-switch + env var + gating present.
    for needle in (
        "os.environ.setdefault('BIOHUB_MOTION_RELINK_EMA_ALPHA', '0.4')",
        "if os.environ.get('BIOHUB_MOTION_RELINK_EMA_ALPHA', '') != ''",
        "velocity_um: dict[int, np.ndarray] = {}",
        "velocity = velocity_um.get(source_id)",
        "if velocity is not None:",
        "motion_relink_ema_predictions",
        "motion_relink_one_frame_fallbacks",
        "if MOTION_RELINK_EMA_ALPHA is not None:",
        "MOTION_RELINK_EMA_ALPHA * step_velocity",
    ):
        if needle not in exp_cell:
            problems.append(f"required EMA construct absent: {needle!r}")

    # 2b) Integrity block present (fail-closed off/on collector emitting metrics.json).
    for needle in (
        "exp_057 EMA integrity contract (fail-closed)",
        "_EXP057_REPRO048_SHA256 = '0319ba6d8e864335d3573f6b1a6227c546f17e9247a0c2858fa09b6c2422db3f'",
        "MOTION_RELINK_EMA_ALPHA = None",
        "MOTION_RELINK_EMA_ALPHA = _exp057_on_alpha",
        "'exp057_ema_integrity_passed': _exp057_passed",
        "_EXP057_EXPECTED_ALPHA = 0.4",
        "_exp057_alpha_ok = (isinstance(_exp057_on_alpha, float) and _exp057_on_alpha == _EXP057_EXPECTED_ALPHA)",
        "_exp057_passed = bool(_exp057_alpha_ok and _exp057_off_parity and _exp057_diff_ok and _exp057_ema_ran)",
        "'effective_on_pass_alpha_is_preregistered_0_4': _exp057_alpha_ok",
        "(WORKING_DIR / 'metrics.json').write_text",
        "raise AssertionError('exp_057 EMA integrity FAILED (fail-closed)",
    ):
        if needle not in exp_cell:
            problems.append(f"required integrity construct absent: {needle!r}")

    # 2c) The off-pass writer must mirror the on-pass writer row format exactly, so
    #     an off-pass divergence cannot silently change the compared bytes. Each
    #     format-defining token must appear on BOTH the on-pass and off-pass writers.
    for token, least in (
        ("'row_type': 'node'", 2),
        ("'row_type': 'edge'", 2),
        ("max(0, int(round(float(", 6),  # z,y,x on both writers
        ("'node_id': -1, 't': -1, 'z': -1, 'y': -1, 'x': -1", 2),
        ("'source_id': -1, 'target_id': -1", 2),
    ):
        if exp_cell.count(token) < least:
            problems.append(f"off-pass writer does not mirror on-pass writer for {token!r} "
                            f"(found {exp_cell.count(token)}, need >= {least})")

    # 2d) Markdown / non-code cells must be byte-identical to the base notebook.
    base_nb0 = json.loads(BASE.read_bytes().decode("utf-8"))
    exp_nb0 = json.loads(target.read_text(encoding="utf-8"))
    base_md = ["".join(c["source"]) for c in base_nb0["cells"] if c["cell_type"] != "code"]
    exp_md = ["".join(c["source"]) for c in exp_nb0["cells"] if c["cell_type"] != "code"]
    if base_md != exp_md:
        problems.append("non-code (markdown) cells differ from the base notebook")

    # 3) Every OTHER code cell must be byte-identical to base (single-cell change).
    base_nb = json.loads(BASE.read_bytes().decode("utf-8"))
    exp_nb = json.loads(target.read_text(encoding="utf-8"))
    # Full parsed-notebook identity: after replacing ONLY the motion_relink cell's
    # source field with the base cell's source, the entire parsed notebook (cells,
    # order, types, metadata, outputs, nbformat) must equal the base notebook. This
    # proves no other field anywhere changed, independent of the builder's patches.
    if len(base_nb["cells"]) != len(exp_nb["cells"]):
        problems.append(f"cell count changed: base={len(base_nb['cells'])} exp={len(exp_nb['cells'])}")
    else:
        exp_idx = [i for i, c in enumerate(exp_nb["cells"])
                   if c["cell_type"] == "code" and "def motion_relink_edges" in "".join(c["source"])]
        base_idx = [i for i, c in enumerate(base_nb["cells"])
                    if c["cell_type"] == "code" and "def motion_relink_edges" in "".join(c["source"])]
        if len(exp_idx) != 1 or exp_idx != base_idx:
            problems.append(f"motion_relink cell index mismatch: base={base_idx} exp={exp_idx}")
        else:
            restored = json.loads(json.dumps(exp_nb))
            restored["cells"][exp_idx[0]]["source"] = base_nb["cells"][base_idx[0]]["source"]
            if restored != base_nb:
                # Localise where it still differs for a useful message.
                extra = [i for i in range(len(base_nb["cells"]))
                         if restored["cells"][i] != base_nb["cells"][i]]
                meta_diff = restored.get("metadata") != base_nb.get("metadata") \
                    or restored.get("nbformat") != base_nb.get("nbformat") \
                    or restored.get("nbformat_minor") != base_nb.get("nbformat_minor")
                problems.append(
                    "notebook differs from base beyond the one authorized cell source "
                    f"(cells still differing after restore: {extra}; metadata/nbformat differ: {meta_diff})"
                )

    if problems:
        print("exp_057 static validation FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print("exp_057 static validation PASSED: notebook is repro_048 + only the scoped EMA edits "
          "(config/init/prediction/propagation) plus the appended fail-closed integrity block; "
          "off-switch, env var, velocity_um EMA, telemetry counters, mirrored off/on writer, "
          "metrics.json emission, and byte-identical markdown all present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
