"""Build the exp_061 notebook from repro_059 (0.947): strippable telemetry injection + appended
DeepCenter-TTA probe cells.

Two kinds of additive change, every added line tagged `# exp061` (or, for appended cells, the
APPEND_MARKER). Stripping every `# exp061`-tagged line and every appended cell reproduces the
parent notebook's per-cell text byte-for-byte (parity guard below).

  1. injections into the single parent code cell (all `# exp061`):
       * whole-run 2.0h SIGALRM watchdog, immediately after `from __future__ ...`
       * a no-op stub `_exp061_log_veto_candidate`, at the top of the cell (after the watchdog)
       * a gap1 veto-candidate logger, immediately before the gap1 DeepCenter veto call
       * a safe-div veto-candidate logger, immediately before the safe-div DeepCenter veto call
  2. two appended code cells: the exp061_deepcenter_tta.py module source, then the guarded call.

Usage: python scripts/build_exp061_deepcenter_tta.py [--check-only]
Output: .private/current/exp061_deepcenter_tta.ipynb
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT_NB = (ROOT / "experiments/repro_059_public_0947_exact_copy/snapshot/source/"
             "biohub-repro059-public-0947-exact-copy.ipynb")
MODULE = ROOT / "scripts/exp061_deepcenter_tta.py"
OUT_NB = ROOT / ".private/current/exp061_deepcenter_tta.ipynb"

MARK = "# exp061"
APPEND_MARKER = "# === exp_061 DeepCenter-TTA appended cell (purely additive) ==="

GAP1_NEEDLE = ("if requires_center_confirmation and (not deepcenter_accept_repair_point("
               "dataset, mid_t, node_point(middle)")
SAFEDIV_NEEDLE = ("if DEEPCENTER_SAFE_DIV_VETO and (not deepcenter_accept_repair_point("
                  "dataset, int(candidate['t']), node_point(candidate)")

# Whole-run budget watchdog, injected right AFTER the `from __future__` line so it arms BEFORE
# the parent's long run. On firing it writes a minimal fail-closed metrics.json then raises.
WHOLE_RUN_GUARD_LINES = [
    "import time as _e61t, json as _e61j  # exp061",
    "_EXP061_RUN_START = _e61t.time()  # exp061",
    "def _exp061_whole_run_guard(signum, frame):  # exp061",
    "    try:  # exp061",
    "        _e61f = open('/kaggle/working/metrics.json', 'w')  # exp061",
    ("        _e61j.dump({'schema_version': 1, 'experiment_id': 'exp_061_deepcenter_tta', "
     "'validation': {'protocol': 'public_0947_deepcenter_tta_probe_v1'}, 'runtime_seconds': "
     "float(_e61t.time() - _EXP061_RUN_START), 'reproducible': False, 'primary_metric': 0.0, "
     "'exp061_deepcenter_tta_integrity_passed': False, 'note': "
     "'whole-run 2.0h budget exceeded (top watchdog)'}, _e61f)  # exp061"),
    "        _e61f.flush()  # exp061",
    "        _e61f.close()  # exp061",
    "    except Exception:  # exp061",
    "        pass  # exp061",
    "    try:  # exp061",
    "        import os as _e61os, psutil as _e61ps  # exp061",
    "        for _e61c in _e61ps.Process(_e61os.getpid()).children(recursive=True):  # exp061",
    "            try:  # exp061",
    "                _e61c.kill()  # exp061",
    "            except Exception:  # exp061",
    "                pass  # exp061",
    "    except Exception:  # exp061",
    "        pass  # exp061",
    "    raise KeyboardInterrupt('exp061 whole-run 2.0h budget exceeded')  # exp061",
    "_EXP061_WATCHDOG_ARMED = False  # exp061",
    "try:  # exp061",
    "    import signal as _e61sig  # exp061",
    "    if hasattr(_e61sig, 'SIGALRM'):  # exp061",
    "        _e61sig.signal(_e61sig.SIGALRM, _exp061_whole_run_guard)  # exp061",
    "        _e61sig.alarm(7200)  # exp061",
    "        _EXP061_WATCHDOG_ARMED = True  # exp061",
    "except Exception:  # exp061",
    "    _EXP061_WATCHDOG_ARMED = False  # exp061",
]

# Disable the parent's adaptive PP-sweep (validator) -- pure overhead for exp_061 (the xyonly
# replay pins tight55 itself), reconciling the feasibility accounting (admission #6). Injected at
# the top, BEFORE the parent reads BIOHUB_VALIDATOR_ENABLE (line ~3193). Imports os locally because
# this runs before the parent's own `import os`. GATED on the probe flag (admission v2 #6): with
# BIOHUB_EXP061_ENABLE=0 the validator is NOT disabled, so the parent runs unchanged (tight55) --
# a true rollback to the parent's 0.947 behaviour.
VALIDATOR_DISABLE_LINE = ("import os as _e61os_pre  # exp061\n"
                          "if _e61os_pre.environ.get('BIOHUB_EXP061_ENABLE', '1') != '0':  # exp061\n"
                          "    _e61os_pre.environ['BIOHUB_VALIDATOR_ENABLE'] = '0'  # exp061")
STUB_LINE = "_exp061_log_veto_candidate = (lambda *a, **k: None)  # exp061 stub"
GAP1_LOGGER = ("_exp061_log_veto_candidate('gap', dataset, mid_t, {'middle_id': middle_id, "
               "'left_id': source_id, 'right_id': target_id, 'reused': int(middle_reused)}, "
               "node_point(middle))  # exp061")
SAFEDIV_LOGGER = ("_exp061_log_veto_candidate('safe_div', dataset, int(candidate['t']), "
                  "{'parent_id': source_id, 'existing_child_id': existing_child_id, "
                  "'candidate_child_id': candidate_id}, node_point(candidate))  # exp061")

GUARDED_CALL = (
    APPEND_MARKER + "\n"
    "import os\n"
    "os.environ.setdefault('BIOHUB_EXP061_ENABLE', '1')\n"
    "if os.environ.get('BIOHUB_EXP061_ENABLE', '0') == '1':\n"
    "    _exp061_telemetry = run_exp061_deepcenter_tta(globals())\n"
    "else:\n"
    "    print('[exp061] BIOHUB_EXP061_ENABLE != 1 - TTA probe skipped (parent path only).')\n"
)


def _text(cell) -> str:
    return "".join(cell["source"])


def _code_cell(source: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": source.splitlines(keepends=True)}


def _inject_into_parent_cell(cell: dict) -> dict:
    lines = _text(cell).split("\n")
    gap_idx = [i for i, ln in enumerate(lines) if GAP1_NEEDLE in ln]
    sd_idx = [i for i, ln in enumerate(lines) if SAFEDIV_NEEDLE in ln]
    fut_idx = [i for i, ln in enumerate(lines) if ln.startswith("from __future__ import")]
    if len(gap_idx) != 1:
        raise SystemExit(f"expected exactly 1 gap1 veto call, found {len(gap_idx)}")
    if len(sd_idx) != 1:
        raise SystemExit(f"expected exactly 1 safe-div veto call, found {len(sd_idx)}")
    if len(fut_idx) != 1:
        raise SystemExit(f"expected exactly 1 `from __future__` line, found {len(fut_idx)}")
    g_i, s_i, f_i = gap_idx[0], sd_idx[0], fut_idx[0]
    if not (f_i < g_i < s_i):
        raise SystemExit("unexpected ordering of injection points (want future < gap1 < safediv)")
    gap_indent = " " * (len(lines[g_i]) - len(lines[g_i].lstrip()))
    sd_indent = " " * (len(lines[s_i]) - len(lines[s_i].lstrip()))

    # Insert at DECREASING indices so earlier indices stay valid.
    new_lines = list(lines)
    new_lines.insert(s_i, sd_indent + SAFEDIV_LOGGER)         # before safe-div veto call
    new_lines.insert(g_i, gap_indent + GAP1_LOGGER)           # before gap1 veto call
    # top block: watchdog (after `from __future__`), validator-disable, then the stub (all module
    # level, before both veto call sites)
    new_lines[f_i + 1:f_i + 1] = WHOLE_RUN_GUARD_LINES + [VALIDATOR_DISABLE_LINE, STUB_LINE]

    out = copy.deepcopy(cell)
    out["source"] = ("\n".join(new_lines)).splitlines(keepends=True)
    return out


def _strip_to_parent_text(cell: dict) -> str:
    return "\n".join(ln for ln in _text(cell).split("\n") if MARK not in ln)


def build(check_only: bool = False) -> int:
    parent = json.loads(PARENT_NB.read_text(encoding="utf-8"))
    parent_cells = parent["cells"]
    code_idx = [i for i, c in enumerate(parent_cells) if c["cell_type"] == "code"]
    if len(code_idx) != 1:
        raise SystemExit(f"expected exactly 1 parent code cell, found {len(code_idx)}")
    ci = code_idx[0]

    nb = copy.deepcopy(parent)
    nb["cells"][ci] = _inject_into_parent_cell(parent_cells[ci])
    module_src = APPEND_MARKER + "\n" + MODULE.read_text(encoding="utf-8")
    nb["cells"] = list(nb["cells"]) + [_code_cell(module_src), _code_cell(GUARDED_CALL)]

    # -- parity guard (text-level): strip appended cells + `# exp061` lines -> parent -------
    rebuilt = []
    for c in nb["cells"]:
        if c["cell_type"] == "code" and _text(c).startswith(APPEND_MARKER):
            continue
        rebuilt.append((c["cell_type"], _strip_to_parent_text(c)))
    parent_ref = [(c["cell_type"], _text(c)) for c in parent_cells]
    if rebuilt != parent_ref:
        for k, (a, b) in enumerate(zip(rebuilt, parent_ref)):
            if a != b:
                raise SystemExit(f"PARITY GUARD FAILED at cell {k}: stripped != parent")
        raise SystemExit(f"PARITY GUARD FAILED: cell count {len(rebuilt)} != {len(parent_ref)}")

    # sanity: injected `# exp061` lines = watchdog block + validator-disable (multi-line) + stub +
    # 2 loggers
    n_expected = len(WHOLE_RUN_GUARD_LINES) + VALIDATOR_DISABLE_LINE.count(MARK) + 1 + 2
    injected = [ln for ln in _text(nb["cells"][ci]).split("\n") if MARK in ln]
    appended = [c for c in nb["cells"] if c["cell_type"] == "code" and _text(c).startswith(APPEND_MARKER)]
    if len(injected) != n_expected:
        raise SystemExit(f"expected {n_expected} injected # exp061 lines, found {len(injected)}")
    if len(appended) != 2:
        raise SystemExit(f"expected 2 appended cells, found {len(appended)}")

    print(f"parity guard PASSED. parent cells: {len(parent_cells)}; injected lines: {n_expected}; "
          f"appended cells: 2; total cells: {len(nb['cells'])}")

    if check_only:
        return 0
    OUT_NB.parent.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT_NB}\n  sha256={hashlib.sha256(OUT_NB.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    raise SystemExit(build(check_only=ap.parse_args().check_only))
