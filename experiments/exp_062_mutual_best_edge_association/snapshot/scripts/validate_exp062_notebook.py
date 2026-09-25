"""exp_062 structural validator + real-patched-source gate.

The load-bearing check here is GROUP 4: it REPLAYS the parent notebook's own five-stage patch
chain onto a temp copy of the reference `predict_unet_transformer.py`, then asserts the exp_062
anchor is unique in that ACTUALLY-PATCHED source and that our patch applies and compiles on it.
A constructed unit test cannot establish that (Codex round-1 answer 1); this can, with no GPU.

Run: python scripts/validate_exp062_notebook.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import exp062_mutual_best as M  # noqa: E402

PARENT_NB = (ROOT / "experiments/repro_059_public_0947_exact_copy/snapshot/source/"
             "biohub-repro059-public-0947-exact-copy.ipynb")
REF_PREDICT = ROOT / "references/biohub-tracking-support-pack/repo/scripts/predict_unet_transformer.py"
NOTEBOOKS = {
    "control": ROOT / ".private/current/exp062_mutual_best_control.ipynb",
    "candidate": ROOT / ".private/current/exp062_mutual_best_candidate.ipynb",
}
MARK = "# exp062"
CELL_MARKER = "# === exp_062 appended cell (purely additive) ==="
PARENT_SHA = "d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60"

# Parent cell-2 line spans (0-based, end-exclusive), verified against the snapshot.
ENV_SCAN_END = 100
HELPERS = (9, 28)
PATCH_CHAIN = (1020, 1518)

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  PASS  %s" % name)
    else:
        print("  FAIL  %s %s" % (name, detail))
        FAILURES.append(name)


def cell_text(c):
    return "".join(c["source"])


def parent_code_lines():
    nb = json.loads(PARENT_NB.read_text(encoding="utf-8"))
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert len(code) == 1
    return cell_text(code[0]).split("\n")


# ---------------------------------------------------------------------------- GROUP 1: parity
def group1_parity():
    print("\n[1] builder parity guard (both variants)")
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_exp062_mutual_best as B
    for variant in ("control", "candidate"):
        try:
            rc = B.build(variant, check_only=True)
            check("parity guard passes [%s]" % variant, rc == 0)
        except SystemExit as exc:
            check("parity guard passes [%s]" % variant, False, str(exc))


# ------------------------------------------------------------------- GROUP 2: notebook structure
def group2_structure():
    print("\n[2] built notebook structure")
    parent = json.loads(PARENT_NB.read_text(encoding="utf-8"))
    for variant, path in NOTEBOOKS.items():
        if not path.is_file():
            check("%s notebook exists" % variant, False, str(path))
            continue
        nb = json.loads(path.read_text(encoding="utf-8"))
        cells = nb["cells"]
        check("%s: 2 added cells" % variant, len(cells) == len(parent["cells"]) + 2,
              "%d vs %d" % (len(cells), len(parent["cells"])))
        marked = [i for i, c in enumerate(cells)
                  if c["cell_type"] == "code" and cell_text(c).startswith(CELL_MARKER)]
        check("%s: exactly 2 marked cells" % variant, len(marked) == 2, str(marked))
        body = cell_text(cells[marked[0] + 1]) if marked else ""
        check("%s: module cell precedes the parent cell" % variant,
              bool(marked) and marked[0] < marked[1] and "from __future__" in body)
        check("%s: every injected line carries the marker" % variant,
              all(MARK in ln for ln in body.split("\n")
                  if "BIOHUB_LB_SCORING" in ln or "_EXP062_" in ln
                  or "apply_mutual_best_patch" in ln or "assert_resume_signature" in ln))
        check("%s: patch applied before predict_cmd" % variant,
              body.index("apply_mutual_best_patch(") < body.index("predict_cmd = [sys.executable"))
        check("%s: resume keys extended before the signature is computed" % variant,
              body.index("_inference_resume_env_keys = list(")
              < body.index("_test_prediction_signature = _resume_signature("))
        check("%s: cache check uses a measured timer" % variant,
              "_EXP062_T0 = time.time()" in body
              and "check_cache_hit(_test_prediction_ready, time.time() - _EXP062_T0)" in body)
        # Variant-specific env contract
        if variant == "control":
            check("control: mode=none, beta=0", "'BIOHUB_LB_SCORING_MODE'] = 'none'" in body
                  and "'BIOHUB_LB_SCORING_BETA'] = '0.0'" in body)
            check("control: parent-SHA guard armed",
                  ("os.environ['BIOHUB_EXP062_EXPECT_PARENT_SHA'] = %r" % PARENT_SHA) in body)
        else:
            check("candidate: mode=mutual_best, beta=0.20",
                  "'BIOHUB_LB_SCORING_MODE'] = 'mutual_best'" in body
                  and "'BIOHUB_LB_SCORING_BETA'] = '0.20'" in body)
            check("candidate: NO parent-SHA assignment (source level)",
                  "os.environ['BIOHUB_EXP062_EXPECT_PARENT_SHA'] =" not in body)
            check("candidate: parent-SHA actively popped + asserted (runtime level)",
                  "os.environ.pop('BIOHUB_EXP062_EXPECT_PARENT_SHA', None)" in body
                  and "not in os.environ" in body)


# ------------------------------------------------------------- GROUP 3: variants differ only in env
def group3_variant_diff():
    print("\n[3] the two variants differ ONLY in the environment block")
    import difflib
    a = json.loads(NOTEBOOKS["control"].read_text(encoding="utf-8"))
    b = json.loads(NOTEBOOKS["candidate"].read_text(encoding="utf-8"))
    ta = cell_text(a["cells"][3]).split("\n")
    tb = cell_text(b["cells"][3]).split("\n")
    diff = [l for l in difflib.unified_diff(ta, tb, lineterm="", n=0)
            if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
    allowed = ("BIOHUB_LB_SCORING", "BIOHUB_EXP062_EXPECT_PARENT_SHA", "_EXP062_RUN_ID")
    check("only env/identity lines differ",
          all(any(a in l for a in allowed) for l in diff), "\n".join(diff[:10]))
    check("diff is small and env-only", 0 < len(diff) <= 10, "%d lines" % len(diff))
    # Everything outside the parent cell must be byte-identical.
    for i in (0, 1, 2, 4):
        check("cell %d identical across variants" % i,
              cell_text(a["cells"][i]) == cell_text(b["cells"][i]))


# ------------------------------------------- GROUP 4: the real patched source (the decisive gate)
def group4_real_patched_source():
    print("\n[4] REPLAY the parent patch chain, then verify our anchor on the result")
    L = parent_code_lines()
    tmp = Path(tempfile.mkdtemp(prefix="exp062_validate_"))
    try:
        repo = tmp / "repo"
        (repo / "scripts").mkdir(parents=True)
        shutil.copy(REF_PREDICT, repo / "scripts")

        env_lines = [l for l in L[:ENV_SCAN_END] if re.match(r"^os\.environ\[", l)]
        check("parent env assignments found", len(env_lines) > 40, str(len(env_lines)))

        ns = {"REPO_DIR": repo, "os": os, "Path": Path, "json": json, "sys": sys}
        saved = dict(os.environ)
        try:
            exec(compile("\n".join(env_lines), "<env>", "exec"), ns)              # noqa: S102
            exec(compile("\n".join(L[HELPERS[0]:HELPERS[1]]), "<helpers>", "exec"), ns)  # noqa: S102
            exec(compile("\n".join(L[PATCH_CHAIN[0]:PATCH_CHAIN[1]]), "<chain>", "exec"), ns)  # noqa: S102
            replayed = True
            err = ""
        except Exception as exc:  # noqa: BLE001
            replayed, err = False, "%s: %s" % (type(exc).__name__, exc)
        finally:
            os.environ.clear()
            os.environ.update(saved)
        check("parent patch chain replays cleanly", replayed, err)
        if not replayed:
            return

        patched = (repo / "scripts" / "predict_unet_transformer.py").read_text(encoding="utf-8")
        check("exp_062 anchor is UNIQUE in the real patched source",
              patched.count(M.ANCHOR) == 1, "count=%d" % patched.count(M.ANCHOR))
        check("stats anchor is unique in the real patched source",
              patched.count(M.STATS_ANCHOR) == 1)
        check("patched source is materially larger than pristine (parent patches applied)",
              len(patched) > len(REF_PREDICT.read_text(encoding="utf-8")))
        check("harmonic fusion present after replay", "harmonic_prob" in patched)
        check("secondary blend present after replay", "secondary_for_mix" in patched)

        info = M.apply_mutual_best_patch(repo / "scripts" / "predict_unet_transformer.py")
        check("exp_062 patch applies to the real patched source", info["anchor_match_count"] == 1)
        final = (repo / "scripts" / "predict_unet_transformer.py").read_text(encoding="utf-8")
        check("final source compiles", compile(final, "<final>", "exec") is not None)
        check("prior present in final source", "_lb_rank_bonus" in final)
        check("stats preamble present in final source", "_EXP062_STATS" in final)
        # Idempotence guard: a second application must FAIL, not silently double-patch.
        try:
            M.apply_mutual_best_patch(repo / "scripts" / "predict_unet_transformer.py")
            check("double-patching is refused", False, "did not raise")
        except M.Exp062Error:
            check("double-patching is refused", True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------- GROUP 5: parent resume-signature assumptions
def group5_resume_assumptions():
    print("\n[5] the parent's resume-signature assumptions still hold")
    L = parent_code_lines()
    keys_line = [l for l in L if l.startswith("_inference_resume_env_keys = [")]
    sig_line = [l for l in L if l.startswith("_test_prediction_signature = _resume_signature(")]
    check("exactly one resume key-list line", len(keys_line) == 1)
    check("exactly one test-prediction signature line", len(sig_line) == 1)
    if keys_line:
        check("parent key list does NOT contain the exp_062 keys (the defect exists)",
              all(k not in keys_line[0] for k in M.EXP062_ENV_KEYS))
    if sig_line:
        check("signature consumes exactly the key list",
              "for key in _inference_resume_env_keys" in sig_line[0])
    check("parent restores predict_seconds on a cache hit (why we measure ourselves)",
          any("predict_seconds = float(_test_prediction_state.get('predict_seconds'" in l for l in L))


def main():
    print("exp_062 notebook validator")
    group1_parity()
    group2_structure()
    group3_variant_diff()
    group4_real_patched_source()
    group5_resume_assumptions()
    print("\n%s" % ("ALL PASS" if not FAILURES else "FAILURES: %s" % FAILURES))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
