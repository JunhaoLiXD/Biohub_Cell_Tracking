"""Negative + positive test of the exp_057 integrity GATE logic (dependency-free).

Extracts the actual gate lines from the exp_057 notebook (the effective-alpha
check and the exp057_ema_integrity_passed conjunction) and execs them with
controlled inputs. Proves a run configured with a pre-existing non-0.4 alpha (or a
missing off-parity / no edge diff / no EMA) CANNOT emit
exp057_ema_integrity_passed=true, closing the round-5 formal-review defect.
Runs in the controller minimal .venv (no numpy).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _bootstrap import PROJECT_ROOT

EXP_NB = PROJECT_ROOT / ".private/current/exp057_0944_motion_ema.ipynb"

GATE_LINES = (
    "_EXP057_EXPECTED_ALPHA = 0.4",
    "_exp057_alpha_ok = (isinstance(_exp057_on_alpha, float) and _exp057_on_alpha == _EXP057_EXPECTED_ALPHA)",
    "_exp057_passed = bool(_exp057_alpha_ok and _exp057_off_parity and _exp057_diff_ok and _exp057_ema_ran)",
)


def _cell(nb_path: Path) -> str:
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    for c in nb["cells"]:
        if c["cell_type"] == "code" and "def motion_relink_edges" in "".join(c["source"]):
            return "".join(c["source"])
    raise RuntimeError("motion_relink cell not found")


def _gate(on_alpha, off_parity, diff_ok, ema_ran, source: str):
    # Verify each gate line is present verbatim in the notebook, then exec them.
    for line in GATE_LINES:
        if line not in source:
            raise AssertionError(f"gate line absent from notebook: {line!r}")
    ns = {
        "_exp057_on_alpha": on_alpha,
        "_exp057_off_parity": off_parity,
        "_exp057_diff_ok": diff_ok,
        "_exp057_ema_ran": ema_ran,
    }
    exec("\n".join(GATE_LINES), ns)
    return ns["_exp057_passed"]


def main() -> int:
    src = _cell(EXP_NB)
    cases = [
        # (on_alpha, off_parity, diff_ok, ema_ran) -> expected pass
        ((0.4, True, True, True), True),      # all good -> pass
        ((0.6, True, True, True), False),     # wrong pre-set alpha -> must FAIL
        ((0.0, True, True, True), False),     # alpha 0 -> fail
        (("0.4", True, True, True), False),   # string alpha (never a float 0.4) -> fail
        ((None, True, True, True), False),    # EMA disabled -> fail
        ((0.4, False, True, True), False),    # off parity broken -> fail
        ((0.4, True, False, True), False),    # no canonical edge diff -> fail
        ((0.4, True, True, False), False),    # EMA never ran -> fail
    ]
    ok = True
    for (args, expected) in cases:
        got = _gate(*args, source=src)
        status = "OK" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"[{status}] on_alpha={args[0]!r} off={args[1]} diff={args[2]} ema={args[3]} -> passed={got} (expected {expected})")
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
