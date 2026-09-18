"""Build the exp_060 notebook from repro_059 (0.947): strippable telemetry injection + appended
threshold-sweep cells.

Two kinds of additive change, every added line tagged `# exp060` (or, for appended cells, the
APPEND_MARKER). Stripping every `# exp060`-tagged line and every appended cell reproduces the
parent notebook's per-cell text byte-for-byte (parity guard below).

  1. call-site telemetry injection into the single parent code cell:
       * a no-op stub def, immediately before `def add_safe_divisions_postlink`
       * a logger call, immediately before the safe-div DeepCenter gate `if` line
  2. two appended code cells: the exp060_threshold_sweep.py module source, then the guarded call.

Usage: python scripts/build_exp060_threshold_sweep.py [--check-only]
Output: .private/current/exp060_deepcenter_safe_div_threshold_sweep.ipynb
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT_NB = (ROOT / "experiments/repro_059_public_0947_exact_copy/snapshot/source/"
             "biohub-repro059-public-0947-exact-copy.ipynb")
MODULE = ROOT / "scripts/exp060_threshold_sweep.py"
OUT_NB = ROOT / ".private/current/exp060_deepcenter_safe_div_threshold_sweep.ipynb"

MARK = "# exp060"
APPEND_MARKER = "# === exp_060 threshold-sweep appended cell (purely additive) ==="

GATE_NEEDLE = "if DEEPCENTER_SAFE_DIV_VETO and (not deepcenter_accept_repair_point(dataset, int(candidate['t'])"
DEF_NEEDLE = "def add_safe_divisions_postlink("

# Whole-run budget watchdog, injected right AFTER the `from __future__` line so it arms BEFORE
# the parent's long run. On firing it writes a minimal fail-closed metrics.json (reconciling the
# hard-interrupt vs always-write-metrics tension) then raises. The appended module disarms it only
# after metrics+telemetry are finalized.
WHOLE_RUN_GUARD_LINES = [
    "import time as _e6t, json as _e6j  # exp060",
    "_EXP060_RUN_START = _e6t.time()  # exp060",
    "def _exp060_whole_run_guard(signum, frame):  # exp060",
    "    try:  # exp060",
    "        _e6f = open('/kaggle/working/metrics.json', 'w')  # exp060",
    ("        _e6j.dump({'schema_version': 1, 'experiment_id': "
     "'exp_060_deepcenter_safe_div_threshold_sweep', 'validation': {'protocol': "
     "'public_0947_deepcenter_safe_div_threshold_sweep_v1'}, 'runtime_seconds': "
     "float(_e6t.time() - _EXP060_RUN_START), 'reproducible': False, 'primary_metric': 0.0, "
     "'exp060_threshold_sweep_integrity_passed': False, 'note': "
     "'whole-run 2.0h budget exceeded (top watchdog)'}, _e6f)  # exp060"),
    "        _e6f.flush()  # exp060",
    "        _e6f.close()  # exp060",
    "    except Exception:  # exp060",
    "        pass  # exp060",
    "    try:  # exp060",
    "        import os as _e6os, psutil as _e6ps  # exp060",
    "        for _e6c in _e6ps.Process(_e6os.getpid()).children(recursive=True):  # exp060",
    "            try:  # exp060",
    "                _e6c.kill()  # exp060",
    "            except Exception:  # exp060",
    "                pass  # exp060",
    "    except Exception:  # exp060",
    "        pass  # exp060",
    "    raise KeyboardInterrupt('exp060 whole-run 2.0h budget exceeded')  # exp060",
    "_EXP060_WATCHDOG_ARMED = False  # exp060",
    "try:  # exp060",
    "    import signal as _e6sig  # exp060",
    "    if hasattr(_e6sig, 'SIGALRM'):  # exp060",
    "        _e6sig.signal(_e6sig.SIGALRM, _exp060_whole_run_guard)  # exp060",
    "        _e6sig.alarm(7200)  # exp060",
    "        _EXP060_WATCHDOG_ARMED = True  # exp060",
    "except Exception:  # exp060",
    "    _EXP060_WATCHDOG_ARMED = False  # exp060",
]

STUB_LINE = "_exp060_log_safe_div_candidate = (lambda *a, **k: None)  # exp060 stub"
LOGGER_LINE = ("_exp060_log_safe_div_candidate(dataset, int(candidate['t']), source_id, "
               "existing_child_id, candidate_id, node_point(candidate), deepcenter_bundle, "
               "frame_cache, deepcenter_cache)  # exp060")

GUARDED_CALL = (
    APPEND_MARKER + "\n"
    "import os\n"
    "os.environ.setdefault('BIOHUB_EXP060_ENABLE', '1')\n"
    "if os.environ.get('BIOHUB_EXP060_ENABLE', '0') == '1':\n"
    "    _exp060_telemetry = run_exp060_threshold_sweep(globals())\n"
    "else:\n"
    "    print('[exp060] BIOHUB_EXP060_ENABLE != 1 - threshold sweep skipped (parent path only).')\n"
)


def _text(cell) -> str:
    return "".join(cell["source"])


def _code_cell(source: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": source.splitlines(keepends=True)}


def _inject_into_parent_cell(cell: dict) -> dict:
    lines = _text(cell).split("\n")
    gate_idx = [i for i, ln in enumerate(lines) if GATE_NEEDLE in ln]
    def_idx = [i for i, ln in enumerate(lines) if DEF_NEEDLE in ln and ln.startswith("def ")]
    fut_idx = [i for i, ln in enumerate(lines) if ln.startswith("from __future__ import")]
    if len(gate_idx) != 1:
        raise SystemExit(f"expected exactly 1 safe-div gate line, found {len(gate_idx)}")
    if len(def_idx) != 1:
        raise SystemExit(f"expected exactly 1 add_safe_divisions_postlink def, found {len(def_idx)}")
    if len(fut_idx) != 1:
        raise SystemExit(f"expected exactly 1 `from __future__` line, found {len(fut_idx)}")
    g_i, d_i, f_i = gate_idx[0], def_idx[0], fut_idx[0]
    if not (f_i < d_i < g_i):
        raise SystemExit("unexpected ordering of injection points")
    gate_indent = " " * (len(lines[g_i]) - len(lines[g_i].lstrip()))

    # Insert at DECREASING indices so earlier indices stay valid.
    new_lines = list(lines)
    new_lines.insert(g_i, gate_indent + LOGGER_LINE)          # before safe-div gate
    new_lines.insert(d_i, STUB_LINE)                          # before add_safe_divisions_postlink def
    new_lines[f_i + 1:f_i + 1] = WHOLE_RUN_GUARD_LINES        # after `from __future__` (arms before parent run)

    out = copy.deepcopy(cell)
    out["source"] = ("\n".join(new_lines)).splitlines(keepends=True)
    return out


def _strip_to_parent_text(cell: dict) -> str:
    """Text of a cell with every `# exp060`-tagged line removed."""
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

    # -- parity guard (text-level): strip appended cells + `# exp060` lines -> parent ------
    rebuilt = []
    for c in nb["cells"]:
        if c["cell_type"] == "code" and _text(c).startswith(APPEND_MARKER):
            continue  # drop appended cells
        rebuilt.append((c["cell_type"], _strip_to_parent_text(c)))
    parent_ref = [(c["cell_type"], _text(c)) for c in parent_cells]
    if rebuilt != parent_ref:
        for k, (a, b) in enumerate(zip(rebuilt, parent_ref)):
            if a != b:
                raise SystemExit(f"PARITY GUARD FAILED at cell {k}: stripped != parent")
        raise SystemExit(f"PARITY GUARD FAILED: cell count {len(rebuilt)} != {len(parent_ref)}")

    # sanity: injected `# exp060` lines (stub + logger + whole-run guard block), 2 appended cells
    n_expected = 2 + len(WHOLE_RUN_GUARD_LINES)
    injected = [ln for ln in _text(nb["cells"][ci]).split("\n") if MARK in ln]
    appended = [c for c in nb["cells"] if c["cell_type"] == "code" and _text(c).startswith(APPEND_MARKER)]
    if len(injected) != n_expected:
        raise SystemExit(f"expected {n_expected} injected # exp060 lines, found {len(injected)}")
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
