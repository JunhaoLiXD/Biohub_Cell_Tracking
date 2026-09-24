"""Build the exp_062 notebook from repro_059 (0.947): mutual-best edge-association rank prior.

Strategy: docs/research/exp062_mutual_best_edge_association_proposal_v3.md (v3, CONSENSUS).

Purely additive. Every injected line carries `# exp062`; the module and finalize cells carry
CELL_MARKER. Stripping all of them reproduces the parent notebook's per-cell text byte-for-byte
(parity guard below).

Two variants of ONE notebook, differing only in the environment block:

  control   -- BIOHUB_LB_SCORING_MODE=none,        beta 0.00, EXPECT_PARENT_SHA armed. Never submitted.
  candidate -- BIOHUB_LB_SCORING_MODE=mutual_best, beta 0.20, EXPECT_PARENT_SHA actively cleared.

Usage:
    python scripts/build_exp062_mutual_best.py --variant control   [--check-only]
    python scripts/build_exp062_mutual_best.py --variant candidate [--check-only]
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT_NB = (ROOT / "experiments/repro_059_public_0947_exact_copy/snapshot/source/"
             "biohub-repro059-public-0947-exact-copy.ipynb")
MODULE = ROOT / "scripts/exp062_mutual_best.py"
OUT = {
    "control": ROOT / ".private/current/exp062_mutual_best_control.ipynb",
    "candidate": ROOT / ".private/current/exp062_mutual_best_candidate.ipynb",
}

MARK = "# exp062"
CELL_MARKER = "# === exp_062 appended cell (purely additive) ==="

PARENT_SHA = "d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60"
STATS_PATH = "/kaggle/working/exp062_stats.jsonl"

# --- injection anchors, each asserted to occur exactly once -------------------------------------
A_ENV = "os.environ['BIOHUB_SECONDARY_ARTIFACT_MANIFEST']"      # after  (line 8)
A_PATCH = "predict_cmd = [sys.executable"                        # before (line 1541)
A_RESUME = "_inference_resume_env_keys = ["                      # after  (line 1669)
A_TIMER = "if _test_prediction_ready:"                           # before (line 1674)
A_AFTER = "import tracksdata as td"                              # before (line 1735)


def _env_lines(variant):
    common_head = [
        "import time as _exp062_time  # exp062",
        "_EXP062_RUN_START = _exp062_time.time()  # exp062",
        "os.environ['BIOHUB_EXP062_STATS_PATH'] = %r  # exp062" % STATS_PATH,
    ]
    if variant == "control":
        return common_head + [
            "os.environ['BIOHUB_LB_SCORING_MODE'] = 'none'  # exp062",
            "os.environ['BIOHUB_LB_SCORING_BETA'] = '0.0'  # exp062",
            # Control only: historical public-output equality. A hidden rerun sees different input
            # data, so this must never be armed in the submitted variant.
            "os.environ['BIOHUB_EXP062_EXPECT_PARENT_SHA'] = %r  # exp062" % PARENT_SHA,
        ]
    return common_head + [
        "os.environ['BIOHUB_LB_SCORING_MODE'] = 'mutual_best'  # exp062",
        "os.environ['BIOHUB_LB_SCORING_BETA'] = '0.20'  # exp062",
        # Source-level absence does not establish process-environment absence (Codex round 2).
        "os.environ.pop('BIOHUB_EXP062_EXPECT_PARENT_SHA', None)  # exp062",
        "assert 'BIOHUB_EXP062_EXPECT_PARENT_SHA' not in os.environ, 'exp062 guard not cleared'  # exp062",
    ]


PATCH_LINES = [
    "# insert the rank prior into the ALREADY-PARENT-PATCHED predict script  # exp062",
    "# fail-closed on any anchor count != 1; an unpatched run would masquerade as a null  # exp062",
    "_EXP062_PATCH_INFO = apply_mutual_best_patch(REPO_DIR / 'scripts' / 'predict_unet_transformer.py')  # exp062",
    "print('exp062 rank-prior patch applied:', _EXP062_PATCH_INFO['patched_region_sha256'][:16], flush = True)  # exp062",
]

RESUME_LINES = [
    # The defect Codex found in round 2: without these two keys the candidate computes the SAME
    # resume signature as the control, skips inference and replays the control's predictions.
    "_inference_resume_env_keys = list(_inference_resume_env_keys) + ['BIOHUB_LB_SCORING_MODE', 'BIOHUB_LB_SCORING_BETA']  # exp062",
    "assert_resume_signature_discriminates(_inference_resume_env_keys)  # exp062",
]

TIMER_LINES = [
    "_EXP062_T0 = time.time()  # exp062",
]

# Parent line 1675 restores the historical predict_seconds on a cache hit, so only an
# independently MEASURED elapsed time can detect one.
AFTER_LINES = [
    "_EXP062_CACHE = check_cache_hit(_test_prediction_ready, time.time() - _EXP062_T0)  # exp062",
    "print('exp062 cache check:', _EXP062_CACHE, flush = True)  # exp062",
]

FINALIZE_CELL = CELL_MARKER + """
# Gated finalization. Every check is fail-closed; finalize() raises if any fails.
_exp062_tel = dict(_EXP062_PATCH_INFO)
_exp062_tel.pop('patched_source', None)
_exp062_tel.update(_EXP062_CACHE)
_exp062_tel['resume_signature_inputs_include_exp062_keys'] = all(
    _k in _inference_resume_env_keys for _k in EXP062_ENV_KEYS)
_exp062_tel.update(read_stats(os.environ['BIOHUB_EXP062_STATS_PATH']))
_exp062_tel['runtime_seconds'] = time.time() - _EXP062_RUN_START
_exp062_metrics = finalize(WORKING_DIR, _exp062_tel, SUBMISSION_PATH)
print(json.dumps(_exp062_metrics, indent = 2, sort_keys = True))
"""


def _text(cell):
    return "".join(cell["source"])


def _code_cell(source):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": source.splitlines(keepends=True)}


def _one(lines, needle, *, strip=False):
    hits = [i for i, ln in enumerate(lines)
            if (ln.strip().startswith(needle) if strip else ln.startswith(needle))]
    if len(hits) != 1:
        raise SystemExit("expected exactly 1 %r anchor, found %d" % (needle, len(hits)))
    return hits[0]


def _inject(cell, variant):
    lines = _text(cell).split("\n")
    i_env = _one(lines, A_ENV)
    i_patch = _one(lines, A_PATCH)
    i_resume = _one(lines, A_RESUME)
    i_timer = _one(lines, A_TIMER)
    i_after = _one(lines, A_AFTER)
    if not (i_env < i_patch < i_resume < i_timer < i_after):
        raise SystemExit("unexpected anchor ordering: %s" % [i_env, i_patch, i_resume, i_timer, i_after])

    out = list(lines)
    # Insert at DECREASING indices so earlier indices stay valid.
    out[i_after:i_after] = AFTER_LINES
    out[i_timer:i_timer] = TIMER_LINES
    out[i_resume + 1:i_resume + 1] = RESUME_LINES
    out[i_patch:i_patch] = PATCH_LINES
    out[i_env + 1:i_env + 1] = _env_lines(variant)

    cell = copy.deepcopy(cell)
    cell["source"] = ("\n".join(out)).splitlines(keepends=True)
    return cell


def _strip(cell):
    return "\n".join(ln for ln in _text(cell).split("\n") if MARK not in ln)


def build(variant, check_only=False):
    parent = json.loads(PARENT_NB.read_text(encoding="utf-8"))
    pcells = parent["cells"]
    code_idx = [i for i, c in enumerate(pcells) if c["cell_type"] == "code"]
    if len(code_idx) != 1:
        raise SystemExit("expected exactly 1 parent code cell, found %d" % len(code_idx))
    ci = code_idx[0]

    nb = copy.deepcopy(parent)
    nb["cells"][ci] = _inject(pcells[ci], variant)
    # The module cell must run BEFORE the parent cell: the patch is applied mid-parent-cell.
    module_cell = _code_cell(CELL_MARKER + "\n" + MODULE.read_text(encoding="utf-8"))
    nb["cells"] = list(nb["cells"][:ci]) + [module_cell] + list(nb["cells"][ci:]) + [_code_cell(FINALIZE_CELL)]

    # -- parity guard: drop marked cells + `# exp062` lines -> parent, byte-for-byte -------------
    rebuilt = []
    for c in nb["cells"]:
        if c["cell_type"] == "code" and _text(c).startswith(CELL_MARKER):
            continue
        rebuilt.append((c["cell_type"], _strip(c)))
    ref = [(c["cell_type"], _text(c)) for c in pcells]
    if rebuilt != ref:
        for k, (a, b) in enumerate(zip(rebuilt, ref)):
            if a != b:
                raise SystemExit("PARITY GUARD FAILED at cell %d" % k)
        raise SystemExit("PARITY GUARD FAILED: cell count %d != %d" % (len(rebuilt), len(ref)))

    all_injected = _env_lines(variant) + PATCH_LINES + RESUME_LINES + TIMER_LINES + AFTER_LINES
    unmarked = [l for l in all_injected if MARK not in l]
    if unmarked:
        raise SystemExit("injected lines missing the %r marker: %r" % (MARK, unmarked))
    n_expected = len(all_injected)
    injected = [l for l in _text(nb["cells"][ci + 1]) .split("\n") if MARK in l]
    if len(injected) != n_expected:
        raise SystemExit("expected %d injected lines, found %d" % (n_expected, len(injected)))

    # The submitted variant must not even mention the historical-hash guard as an assignment.
    if variant == "candidate":
        body = _text(nb["cells"][ci + 1])
        if "os.environ['BIOHUB_EXP062_EXPECT_PARENT_SHA'] =" in body:
            raise SystemExit("candidate variant assigns EXPECT_PARENT_SHA")

    print("parity guard PASSED [%s]: injected %d lines, cells %d -> %d"
          % (variant, n_expected, len(pcells), len(nb["cells"])))
    if check_only:
        return 0
    out = OUT[variant]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s\n  sha256=%s" % (out, hashlib.sha256(out.read_bytes()).hexdigest()))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=sorted(OUT), required=True)
    ap.add_argument("--check-only", action="store_true")
    a = ap.parse_args()
    raise SystemExit(build(a.variant, a.check_only))
