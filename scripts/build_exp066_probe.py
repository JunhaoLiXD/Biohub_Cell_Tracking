"""Build a deterministic single-lever probe from the archived vehicle notebook.

    python scripts/build_exp066_probe.py cx03
    python scripts/build_exp066_probe.py ep015

PLAN.md Step 1 (`cx03`) and Step 3 (`ep015`). One arm per run, no validator, no sweep, no runtime
re-selection: the base pass IS the arm, so the notebook's own output is what gets submitted.

Parent: exp_064_x138_verbatim_repro, Public LB 0.953, output sha d52a5da2…
Vehicle: docs/research/public_notebook_archive/optimized-biohub-max-score.ipynb, whose base pass is
BYTE-VERIFIED to reproduce that parent when its levers are off (exp_065 Gate 1).

Verified before writing this script:
  * `COUNT_EXCESS_FRAC` and `VALIDATOR_ENABLE` are NOT in the cell-1 `_EXPECTED_NUMERIC` drift guard,
    so unlike exp_065's sweep-deadline change these need no matching guard edit.
  * `prune_to_node_count_target` is called at cell 5 line 2702 inside `filter_output_graph`, which
    `write_test_submission` calls at line 2770 — so the lever fires on the TEST submission path, not
    only inside the validator.

The build asserts an exact authored-line budget and fails on any other delta. After the run, the
output sha MUST differ from the parent's: if it is identical the lever did not fire and the probe is
void, not null.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
VEHICLE = ROOT / "docs/research/public_notebook_archive/optimized-biohub-max-score.ipynb"
VEHICLE_SHA = "371fc1f9f4f20f692e0586616ff7d3eab4621d167f6c78516d3243c5a4fddfab"
PARENT_SHA = "d52a5da2ae5cb0d1b22499f6ca51a00838a6c32ae9a1986ec756ea72e7909e03"

# arm -> {env key: (from, to)}. Values are the notebook's own candidate definitions.
ARMS: dict[str, dict[str, tuple[str, str]]] = {
    "cx03": {"BIOHUB_COUNT_EXCESS_FRAC": ("0.0", "0.03")},
    "cx06": {"BIOHUB_COUNT_EXCESS_FRAC": ("0.0", "0.06")},
    "ep015": {"BIOHUB_OUTPUT_MIN_EDGE_PROB": ("0.0", "0.15")},
}

ASSERTIONS = [
    '',
    '# exp_066 probe: the empty-string preset/cache settings above ENABLE the',
    '# /kaggle/input/*/ppsweep_selected.json and */cache_key.txt auto-attach rather than disabling it.',
    '# Fail closed here, after loading and before any application to inference.',
    'assert not _V9_AUTO_SET_ENV, f"exp_066: preset/cache auto-attach fired: {_V9_AUTO_SET_ENV}"',
    'assert FROZEN_PRESET_OVERRIDES is None, "exp_066: a frozen preset was loaded; this is not a clean arm"',
]

SNAPSHOT = [
    '',
    '# exp_066 probe: snapshot the written submission. With the validator off nothing rewrites',
    '# submission.csv, so this is a belt-and-braces copy that also makes the arm artefact explicit',
    '# in the kernel output.',
    'import shutil as _x66_shutil',
    '_X66_SNAPSHOT = WORKING_DIR / "submission_arm.csv"',
    '_x66_shutil.copy2(SUBMISSION_PATH, _X66_SNAPSHOT)',
    'print(f"exp_066: arm submission snapshotted to {_X66_SNAPSHOT}", flush=True)',
]


def die(msg: str) -> None:
    sys.exit(f"BUILD FAILED: {msg}")


def lines_of(nb: dict, i: int) -> list[str]:
    return "".join(nb["cells"][i]["source"]).split("\n")


def set_cell(nb: dict, i: int, lines: list[str]) -> None:
    nb["cells"][i]["source"] = "\n".join(lines)


def replace_env(lines: list[str], key: str, old: str, new: str, label: str,
                comment: str | None = None) -> int:
    """Swap one os.environ value, and REWRITE its trailing comment rather than leaving one that
    now contradicts the line. A source comment saying "validator ON" above a line setting it to 0
    is precisely the class of misleading declaration that has cost this project seven times."""
    needle = f'os.environ["{key}"] = "{old}"'
    hits = [k for k, l in enumerate(lines) if l.startswith(needle)]
    if len(hits) != 1:
        die(f"{label}: expected exactly 1 line starting `{needle}`, found {len(hits)}")
    new_line = f'os.environ["{key}"] = "{new}"'
    if comment:
        new_line += f"  # {comment}"
    lines[hits[0]] = new_line
    return hits[0] + 1


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ARMS:
        die(f"usage: build_exp066_probe.py <{'|'.join(ARMS)}>")
    arm = sys.argv[1]
    overrides = ARMS[arm]

    raw = VEHICLE.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != VEHICLE_SHA:
        die(f"vehicle sha256 mismatch\n  expected {VEHICLE_SHA}\n  got      {got}")
    print(f"vehicle sha256 OK: {got[:16]}…")

    nb = json.loads(raw.decode("utf-8"))
    applied: list[str] = []

    # (a) the AttributeError that killed the notebook author's own run, in a cell-12 summary print
    L = lines_of(nb, 11)
    hits = [k for k, l in enumerate(L) if l.strip() == "_v6env = os.environ.get"]
    if len(hits) != 1:
        die(f"(a) expected exactly 1 `_v6env = os.environ.get` in cell 11, found {len(hits)}")
    L[hits[0]] = L[hits[0]].replace("os.environ.get", "os.environ")
    set_cell(nb, 11, L)
    applied.append(f"(a) cell 11 line {hits[0] + 1}: _v6env = os.environ.get -> os.environ")

    L = lines_of(nb, 0)

    # (v) validator and sweep OFF -- this arm is deterministic, the base pass IS the arm
    n = replace_env(L, "BIOHUB_VALIDATOR_ENABLE", "1", "0", "(v)",
                    comment="exp_066: validator and sweep OFF -- this arm is deterministic, "
                            "the base pass IS the arm")
    applied.append(f"(v) cell 0 line {n}: VALIDATOR_ENABLE 1 -> 0")

    # (arm) the single lever
    for key, (old, new) in overrides.items():
        n = replace_env(L, key, old, new, f"(arm {arm})",
                        comment=f"exp_066 arm {arm}: THE single active v5 lever (was {old} = off)")
        applied.append(f"(arm) cell 0 line {n}: {key} {old} -> {new}")

    # (d) fail-closed auto-attach assertions, before anything can be applied to inference
    hits = [k for k, l in enumerate(L) if l.startswith('print("BIOHUB_PRESET:"')]
    if len(hits) != 1:
        die(f"(d) expected exactly 1 `print(\"BIOHUB_PRESET:\"` anchor in cell 0, found {len(hits)}")
    L[hits[0]:hits[0]] = ASSERTIONS
    set_cell(nb, 0, L)
    applied.append(f"(d) cell 0 before line {hits[0] + 1}: +{len(ASSERTIONS)} lines, auto-attach assertions")

    # (e) snapshot the arm artefact
    L = lines_of(nb, 5)
    hits = [k for k, l in enumerate(L) if l.strip() == "globals()[_v7_k] = _v7_v"]
    if len(hits) != 1:
        die(f"(e) expected exactly 1 `globals()[_v7_k] = _v7_v` anchor in cell 5, found {len(hits)}")
    at = hits[0] + 1
    L[at:at] = SNAPSHOT
    set_cell(nb, 5, L)
    applied.append(f"(e) cell 5 after line {at}: +{len(SNAPSHOT)} lines, arm snapshot")

    print("\napplied:")
    for a in applied:
        print("  " + a)

    # ---------- verification ----------
    before = "\n".join("".join(c["source"]) for c in json.loads(raw.decode("utf-8"))["cells"]).split("\n")
    after = "\n".join("".join(c["source"]) for c in nb["cells"]).split("\n")
    import difflib
    removed = added = 0
    print("\ndiff against the archived vehicle:")
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        for l in before[i1:i2]:
            print(f"  - {l}")
            removed += 1
        for l in after[j1:j2]:
            print(f"  + {l}")
            added += 1

    # budget: 1 (a) + 1 (v) + one per override, all changed; plus 6 (d) + 8 (e) added
    want_removed = 2 + len(overrides)
    want_added = want_removed + len(ASSERTIONS) + len(SNAPSHOT)
    print(f"\nlines removed {removed}, lines added {added}  (expected {want_removed} / {want_added})")
    if (removed, added) != (want_removed, want_added):
        die("authored-change budget violated; review the diff above")
    print("authored-change budget OK")

    # nothing else may have moved, and the drift guard must still agree with cell 0
    c0 = "".join(nb["cells"][0]["source"])
    must_hold = {
        "BIOHUB_PPSWEEP_FAST_TIER": '"1"',        # irrelevant with the validator off, must be untouched
        "BIOHUB_REPAIR_DEADLINE_S": '"27000"',
        "BIOHUB_SWEEP_DEADLINE_S": '"26100"',     # untouched: no sweep runs in this arm
        "BIOHUB_DET_THRESHOLD": '"0.965"',
        "BIOHUB_MOTION_RELINK_TIGHT_UM": '"5.5"',
    }
    for key, want in must_hold.items():
        if f'os.environ["{key}"] = {want}' not in c0:
            die(f"expected cell 0 to still contain os.environ[\"{key}\"] = {want}")
    for key in ("BIOHUB_OUTPUT_MIN_EDGE_PROB", "BIOHUB_SEG_PRUNE_MIN_PROB",
                "BIOHUB_LEAF_PRUNE_MIN_EDGE_PROB", "BIOHUB_COUNT_EXCESS_FRAC",
                "BIOHUB_GAP_CLOSE_DIV_UM", "BIOHUB_REPAIR_PARENT_MAX_UM",
                "BIOHUB_LINEFIT_MAX_SHIFT_UM"):
        if key in overrides:
            continue
        if f'os.environ["{key}"] = "0.0"' not in c0:
            die(f"every v5 lever except the arm must still be 0.0; {key} is not")
    print(f"config gate OK: validator off, {arm} is the ONLY active v5 lever, "
          "sweep deadline and all other settings untouched")

    for i, c in enumerate(nb["cells"]):
        try:
            compile("".join(c["source"]), f"<cell{i}>", "exec")
        except SyntaxError as e:
            die(f"cell {i} does not compile: {e}")
    print(f"syntax OK: all {len(nb['cells'])} cells compile")

    out_dir = ROOT / f"experiments/exp_066_probe_{arm}/kaggle_kernel"
    out_dir.mkdir(parents=True, exist_ok=True)
    nb_path = out_dir / f"biohub-exp066-{arm}.ipynb"
    nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    kid = f"lingxd/biohub-exp066-{arm}"
    (out_dir / "kernel-metadata.json").write_text(json.dumps({
        "id": kid,
        "title": kid.split("/")[1],
        "code_file": nb_path.name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": False,
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": [
            "pilkwang/biohub-deepcenter-unet3d-center-prior-v1",
            "pilkwang/biohub-temporal-unet3d-seed314159-v1",
            "pilkwang/biohub-tracking-support-pack-50ep-v1",
            "anvithpothula/biohub-v1284-head-s075",
        ],
        "competition_sources": ["biohub-cell-tracking-during-development"],
        "kernel_sources": [],
        "docker_image": "gcr.io/kaggle-private-byod/python@sha256:"
                        "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        "docker_image_pinning_type": "original",
    }, indent=2) + "\n", encoding="utf-8")

    print(f"\nwrote {nb_path.relative_to(ROOT)}")
    print(f"      sha256 {hashlib.sha256(nb_path.read_bytes()).hexdigest()[:16]}…")
    print(f"\nAFTER THE RUN: the output sha MUST differ from the parent {PARENT_SHA[:8]}…")
    print("If it is identical the lever did not fire and the probe is VOID, not null.")
    print("NOT pushed. Launch is a separate step.")


if __name__ == "__main__":
    main()
