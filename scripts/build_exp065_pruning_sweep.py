"""Build exp_065 Run 1 from the archived vehicle notebook.

Vehicle: docs/research/public_notebook_archive/optimized-biohub-max-score.ipynb
         sha256 371fc1f9f4f20f692e0586616ff7d3eab4621d167f6c78516d3243c5a4fddfab
Parent:  exp_064_x138_verbatim_repro, Public LB 0.953, output sha d52a5da2...

Applies exactly the six authored changes specified in
docs/research/exp065_metric_aligned_pruning_proposal_v3.md section 4.1, then verifies the diff is
exactly that and nothing else. Fails loudly on any anchor mismatch -- this project has four recorded
instances of a patch whose anchor count silently went to zero.

    python scripts/build_exp065_pruning_sweep.py

Run 1 delivers, in one run:
  * submission_base.csv  -- the base pass snapshotted BEFORE the sweep rewrites submission.csv,
                            for the Gate 1 byte check against the parent
  * ppsweep_results.csv / validator_results.csv -- the 15 eligible pruning candidates scored on
                            8 held-out TRAIN stems
  * submission.csv       -- rewritten by the notebook's own prefix-guarded selection
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
VEHICLE = ROOT / "docs/research/public_notebook_archive/optimized-biohub-max-score.ipynb"
VEHICLE_SHA = "371fc1f9f4f20f692e0586616ff7d3eab4621d167f6c78516d3243c5a4fddfab"
OUT_DIR = ROOT / "experiments/exp_065_metric_aligned_pruning/kaggle_kernel"
OUT_NB = OUT_DIR / "biohub-exp065-pruning-sweep.ipynb"

KERNEL_ID = "lingxd/biohub-exp065-pruning-sweep"

# The 15 eligible pruning candidates, ordered so a deadline truncation still leaves the most
# valuable rows measured: the two candidates amanatar already scored come first as a cross-check of
# our table against theirs, then the untested cx* mechanism, then the rest.
ELIGIBLE = [
    "ep015", "leaf040",                       # cross-check against the harvested table
    "cx03", "cx06", "cx10",                   # the untested core-relative budget
    "ep010", "ep020",                         # the rest of the ep family
    "seg035L4", "seg030L3", "seg040L6",       # weak pendant segments
    "leaf030",                                # the other leaf threshold
    "ep_cx", "prune_pack", "seg_cx", "leaf_seg",   # the stacks
]

ASSERTIONS = [
    '',
    '# exp_065 change (d): the empty-string settings above ENABLE the /kaggle/input/*/ppsweep_selected.json',
    '# and */cache_key.txt auto-attach (cell 0 line 178, 202) rather than disabling it. Fail closed here,',
    '# after loading and before any application to inference, so the base pass is provably the parent.',
    'assert not _V9_AUTO_SET_ENV, f"exp_065: preset/cache auto-attach fired: {_V9_AUTO_SET_ENV}"',
    'assert FROZEN_PRESET_OVERRIDES is None, "exp_065: a frozen preset was loaded; the base pass is not the parent"',
]

SNAPSHOT = [
    '',
    '# exp_065 change (e): write_test_submission always opens the same SUBMISSION_PATH with "w" and the',
    '# sweep rewrites it after selection, so without this snapshot the base control artifact does not',
    '# survive a successful sweep and Gate 1 cannot be evaluated.',
    'import shutil as _x65_shutil',
    '_X65_BASE_SNAPSHOT = WORKING_DIR / "submission_base.csv"',
    '_x65_shutil.copy2(SUBMISSION_PATH, _X65_BASE_SNAPSHOT)',
    'print(f"exp_065: base submission snapshotted to {_X65_BASE_SNAPSHOT}", flush=True)',
]


def die(msg: str) -> None:
    sys.exit(f"BUILD FAILED: {msg}")


def cell_lines(nb: dict, index: int) -> list[str]:
    return "".join(nb["cells"][index]["source"]).split("\n")


def set_cell(nb: dict, index: int, lines: list[str]) -> None:
    nb["cells"][index]["source"] = "\n".join(lines)


def main() -> None:
    raw = VEHICLE.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != VEHICLE_SHA:
        die(f"vehicle sha256 mismatch\n  expected {VEHICLE_SHA}\n  got      {got}")
    print(f"vehicle sha256 OK: {got[:16]}...")

    nb = json.loads(raw.decode("utf-8"))
    applied: list[str] = []

    # ---- (a) cell 11 line 44: the AttributeError that killed the author's own run ----
    L = cell_lines(nb, 11)
    i = [k for k, l in enumerate(L) if l.strip() == "_v6env = os.environ.get"]
    if len(i) != 1:
        die(f"(a) expected exactly 1 anchor '_v6env = os.environ.get' in cell 11, found {len(i)}")
    L[i[0]] = L[i[0]].replace("os.environ.get", "os.environ")
    set_cell(nb, 11, L)
    applied.append(f"(a) cell 11 line {i[0] + 1}: _v6env = os.environ.get -> os.environ")

    # ---- (b) cell 0: an enforced sweep bound, 26100 s -> 12600 s ----
    L = cell_lines(nb, 0)
    i = [k for k, l in enumerate(L) if 'os.environ["BIOHUB_SWEEP_DEADLINE_S"] = "26100"' in l]
    if len(i) != 1:
        die(f"(b) expected exactly 1 SWEEP_DEADLINE_S=26100 anchor in cell 0, found {len(i)}")
    L[i[0]] = L[i[0]].replace('"26100"', '"12600"').replace(
        "# sweep inner-loop abort, keeps best-so-far (7.25 h)",
        "# exp_065: enforced 3.5 h sweep bound (was 26100 = 7.25 h); aborts keeping best-so-far")
    b_line = i[0] + 1
    set_cell(nb, 0, L)

    # ---- (b2) cell 1: the vehicle's OWN config-drift guard pins SWEEP_DEADLINE_S at 26100.0, so
    # changing only cell 0 makes the notebook raise "Configuration drift detected" in cell 1. Run 1
    # v1 died here. The guard is doing its job; the expected value has to move with the setting. ----
    L1 = cell_lines(nb, 1)
    j = [k for k, l in enumerate(L1) if l.strip() == '"BIOHUB_SWEEP_DEADLINE_S": 26100.0,']
    if len(j) != 1:
        die(f"(b2) expected exactly 1 drift-guard anchor for SWEEP_DEADLINE_S in cell 1, found {len(j)}")
    L1[j[0]] = L1[j[0]].replace("26100.0", "12600.0")
    set_cell(nb, 1, L1)

    L = cell_lines(nb, 0)

    # ---- (d) cell 0: fail-closed auto-attach assertions ----
    i = [k for k, l in enumerate(L) if l.startswith('print("BIOHUB_PRESET:"')]
    if len(i) != 1:
        die(f"(d) expected exactly 1 'print(\"BIOHUB_PRESET:\"' anchor in cell 0, found {len(i)}")
    L[i[0]:i[0]] = ASSERTIONS
    set_cell(nb, 0, L)
    applied.append(f"(b) cell 0 line {b_line}: SWEEP_DEADLINE_S 26100 -> 12600")
    applied.append(f"(b2) cell 1 line {j[0] + 1}: drift-guard expected 26100.0 -> 12600.0")
    applied.append(f"(d) cell 0 before line {i[0] + 1}: +{len(ASSERTIONS)} lines, auto-attach assertions")

    # ---- (e) cell 5: snapshot the base submission before the sweep can overwrite it ----
    L = cell_lines(nb, 5)
    i = [k for k, l in enumerate(L) if l.strip() == "globals()[_v7_k] = _v7_v"]
    if len(i) != 1:
        die(f"(e) expected exactly 1 'globals()[_v7_k] = _v7_v' anchor in cell 5, found {len(i)}")
    at = i[0] + 1
    L[at:at] = SNAPSHOT
    set_cell(nb, 5, L)
    applied.append(f"(e) cell 5 after line {at}: +{len(SNAPSHOT)} lines, base snapshot")

    # ---- (c) cell 10: sweep exactly the 15 eligible pruning candidates ----
    L = cell_lines(nb, 10)
    i = [k for k, l in enumerate(L) if l.strip() == "_V7_FAST_TIER = ("]
    if len(i) != 1:
        die(f"(c) expected exactly 1 '_V7_FAST_TIER = (' anchor in cell 10, found {len(i)}")
    start = i[0] + 1
    end = next((k for k in range(start, len(L)) if L[k].strip() == ")"), None)
    if end is None:
        die("(c) could not find the closing paren of the _V7_FAST_TIER tuple")
    old = [l for l in L[start:end]]
    if len(old) != 2:
        die(f"(c) expected the original tier to be 2 lines, found {len(old)}")
    new = ['        # exp_065: exactly the 15 pruning candidates Gate 2 can select from, highest-value first']
    for k in range(0, len(ELIGIBLE), 4):
        new.append("        " + ", ".join(f'"{n}"' for n in ELIGIBLE[k:k + 4]) + ",")
    L[start:end] = new
    set_cell(nb, 10, L)
    applied.append(f"(c) cell 10 lines {start + 1}-{end}: tier tuple -> the {len(ELIGIBLE)} eligible candidates")

    # ---------------- verification ----------------
    print("\napplied:")
    for a in applied:
        print("  " + a)

    before = "\n".join("".join(c["source"]) for c in json.loads(raw.decode("utf-8"))["cells"]).split("\n")
    after = "\n".join("".join(c["source"]) for c in nb["cells"]).split("\n")
    import difflib
    changed = added = removed = 0
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
    changed = min(removed, added)
    print(f"\nlines removed {removed}, lines added {added}")

    # v3 section 4.1 budget, stated as exact removed/added totals INCLUDING the explanatory
    # comments, because a budget gate that does not match the document is the same drift the
    # review rounds kept catching. Breakdown of the 21 added:
    #   (a) 1  the _v6env fix
    #   (b) 1  the sweep deadline
    #   (b2) 1 the vehicle's own drift guard, which pins that same deadline
    #   (c) 5  a comment + four name lines, replacing the 2-line tier tuple
    #   (d) 6  a blank + 3 comments + 2 assertions
    #   (e) 8  a blank + 3 comments + 4 code lines
    # and of the 5 removed: (a) 1, (b) 1, (b2) 1, (c) 2.
    expected_removed, expected_added = 5, 22
    if (removed, added) != (expected_removed, expected_added):
        die(f"authored-change budget violated: expected {expected_removed} removed / "
            f"{expected_added} added, got {removed} / {added}. Review the diff above.")
    print(f"authored-change budget OK: {removed} removed / {added} added, exactly as designed")

    # sanity: the three settings that must NOT have been touched
    c0 = "".join(nb["cells"][0]["source"])
    for key, want in (("BIOHUB_VALIDATOR_ENABLE", '"1"'),
                      ("BIOHUB_PPSWEEP_FAST_TIER", '"1"'),
                      ("BIOHUB_PPSWEEP_EXTENDED", '"1"'),
                      ("BIOHUB_PPSWEEP_PREFIX_GUARD", '"1"'),
                      ("BIOHUB_REPAIR_DEADLINE_S", '"27000"'),
                      ("BIOHUB_OUTPUT_MIN_EDGE_PROB", '"0.0"'),
                      ("BIOHUB_COUNT_EXCESS_FRAC", '"0.0"'),
                      ("BIOHUB_LEAF_PRUNE_MIN_EDGE_PROB", '"0.0"'),
                      ("BIOHUB_SEG_PRUNE_MIN_PROB", '"0.0"')):
        if f'os.environ["{key}"] = {want}' not in c0:
            die(f"expected cell 0 to still contain os.environ[\"{key}\"] = {want}")
    print("config gate OK: validator on, fast tier on, extended on, prefix guard on, "
          "repair deadline 27000, all v5 levers at 0")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    meta = {
        "id": KERNEL_ID,
        "title": KERNEL_ID.split("/")[1],
        "code_file": OUT_NB.name,
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
    }
    (OUT_DIR / "kernel-metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"\nwrote {OUT_NB.relative_to(ROOT)}")
    print(f"      sha256 {hashlib.sha256(OUT_NB.read_bytes()).hexdigest()[:16]}...")
    print(f"wrote {(OUT_DIR / 'kernel-metadata.json').relative_to(ROOT)}")
    print("\nNOT pushed. Launch is a separate, explicitly authorized step.")


if __name__ == "__main__":
    main()
