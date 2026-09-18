"""Local smoke/validator for the exp_058 A0 division diagnostic notebook.

Proves what CAN be proven without the GPU pipeline:
  1. Deterministic build: rebuilding from the pinned base reproduces the given
     notebook byte-for-byte (provenance + determinism).
  2. Purely-additive instrumentation: stripping every __EXP058_TELEMETRY__ line from
     each instrumented cell reproduces the corresponding base cell byte-for-byte
     (the build's parity guard, re-checked here independently).
  3. Every code cell parses (ast).
  4. native-int serialization regression: _exp058_native + json.dumps handle numpy
     integer/float/bool and nested tuples (the diag_044 failure mode).
  5. The controller experiment-id placeholder is present.

The decisive non-perturbation proof is the RUNTIME integrity gate on Kaggle (exact
reproduction of official score 0.9310696 / division 3/8/9 / test submission SHA
0319ba6d); local smoke cannot execute the pipeline.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_exp058_a0_division_diagnostic import (  # noqa: E402
    BASE_NOTEBOOK, TAG, build, _load_cell_source, _strip_tag_lines,
)
from exp058_instrumentation import cell5_replacements  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _fail(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    print(f"SMOKE FAIL: {msg}")
    raise SystemExit(1)


def main() -> int:
    given = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".private/current/exp058_a0_division_diagnostic.ipynb")
    given = given if given.is_absolute() else ROOT / given

    # 1) deterministic rebuild -> byte-identical to the given notebook
    tmp = ROOT / ".private/current/_exp058_smoke_rebuild.ipynb"
    build(ROOT / BASE_NOTEBOOK, tmp)
    if tmp.read_bytes() != given.read_bytes():
        _fail("deterministic rebuild does not match the provided notebook byte-for-byte")

    nb = json.loads(given.read_text(encoding="utf-8"))
    base_nb = json.loads((ROOT / BASE_NOTEBOOK).read_text(encoding="utf-8"))

    # 2) parity: functions cell + validator cell, minus tagged lines == base cells
    fidx, fbase = _load_cell_source(base_nb)
    if _strip_tag_lines("".join(nb["cells"][fidx]["source"])) != fbase:
        _fail("functions cell is not purely additive vs base")
    stash_anchor = cell5_replacements()[0][0]
    matched = [i for i, c in enumerate(base_nb["cells"])
               if c.get("cell_type") == "code" and stash_anchor in "".join(c.get("source", []))]
    if len(matched) != 1:
        _fail(f"validator-cell anchor not unique in base (n={len(matched)})")
    vidx = matched[0]
    if _strip_tag_lines("".join(nb["cells"][vidx]["source"])) != "".join(base_nb["cells"][vidx]["source"]):
        _fail("validator cell is not purely additive vs base")

    # 3) all code cells parse
    for i, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        try:
            ast.parse("".join(c["source"]))
        except SyntaxError as e:
            _fail(f"cell {i} syntax error line {e.lineno}: {e.msg}")

    # 4) native-int serialization regression (extract + exec the helper).
    # numpy-free: the controller venv may lack numpy (Kaggle always has it). We test
    # the python paths + a custom float-able scalar; if numpy IS present, also test it.
    ns: dict = {}
    fsrc = "".join(nb["cells"][fidx]["source"])
    lines = fsrc.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("def _exp058_native"))
    body = [lines[start]]
    for l in lines[start + 1:]:
        if l and not l[0].isspace():
            break
        body.append(l)
    exec("\n".join(l.replace(TAG, "") for l in body), ns)
    conv = ns["_exp058_native"]

    class _FakeScalar:
        def __init__(self, x): self._x = x
        def __float__(self): return float(self._x)

    sample = {
        "b": conv(True), "i": conv(7), "f": conv(1.5), "n": conv(None),
        "seq": conv((1, 2.0, (3, 4))), "scalar": conv(_FakeScalar(2.5)),
    }
    if not (sample["b"] is True and isinstance(sample["i"], int)
            and isinstance(sample["f"], float) and sample["n"] is None
            and sample["seq"] == [1, 2.0, [3, 4]] and sample["scalar"] == 2.5):
        _fail(f"_exp058_native did not normalize types: {sample}")
    try:
        json.dumps(sample)
    except (TypeError, ValueError) as e:
        _fail(f"native json regression failed: {e}")
    try:
        import numpy as np  # optional
        nps = {"i": conv(np.int64(5)), "f": conv(np.float64(1.5)), "b": conv(np.bool_(True))}
        json.dumps(nps)
        if not (isinstance(nps["i"], int) and isinstance(nps["f"], float) and nps["b"] is True):
            _fail(f"_exp058_native did not normalize numpy types: {nps}")
    except ImportError:
        pass

    # 5) controller experiment-id placeholder present
    allsrc = "".join("".join(c["source"]) for c in nb["cells"])
    if "__CONTROLLER_EXPERIMENT_ID__" not in allsrc:
        _fail("controller experiment-id placeholder missing")

    # 6) executable correctness checks on the analysis cell (targets the exact bug
    #    classes the admission review caught: p2g direction, cand_t join, metrics
    #    contract). These run at smoke time, unlike pure AST parsing.
    analysis = "".join(nb["cells"][-1]["source"])
    if "exp058_diagnostic_integrity_passed" not in analysis:
        _fail("last cell is not the analysis/integrity cell")
    # directionality must map the PRED source via p2g (pred->gt), NOT g2p
    if "_p2g.get(_c['source_id'])" not in analysis:
        _fail("directionality must use _p2g.get(source_id) (pred->gt); p2g direction bug")
    if "_g2p.get(_c['source_id'])" in analysis:
        _fail("directionality uses _g2p on a pred source id (the reviewed bug)")
    # DeepCenter join must key on candidate time (cand_t), since the score is at t+1
    if "_c['cand_t']" not in analysis or "cand_t=int(candidate['t'])" not in "".join(nb["cells"][fidx]["source"]):
        _fail("DeepCenter join must use candidate time cand_t (t+1), not source t")
    # whole-panel official delta (not per-sample only)
    if "_panel_delta" not in analysis or "d_panel_proxy_score" not in analysis:
        _fail("suppression/addition must report whole-panel official d_panel_proxy_score")
    # exactly-12 GT enforcement
    if "exactly_12_gt_divisions" not in analysis or "_GT_DIVISIONS_EXPECTED = 12" not in analysis:
        _fail("GT coverage must enforce exactly 12 GT divisions")
    # controller-valid metrics contract fields
    for _field in ("'schema_version': 1", "'runtime_seconds'", "'reproducible'", "'specimen_metrics'"):
        if _field not in analysis:
            _fail(f"metrics.json contract missing {_field}")
    if "'44b6': _spec_metric" not in analysis or "'6bba': _spec_metric" not in analysis:
        _fail("specimen_metrics must include 44b6 and 6bba")
    # downstream tracing + missing_bypass telemetry present
    if "survived_to_final_graph" not in analysis:
        _fail("downstream tracing of added safe_division edges missing")
    fcell = "".join(nb["cells"][fidx]["source"])
    for _stage in ("missing_bypass", "cap_global", "cap_frame", "conflict_target",
                   "conflict_source", "source_no_existing_child_at_t1", "frame_pools"):
        if _stage not in fcell:
            _fail(f"candidate-journey telemetry missing stage: {_stage}")

    tmp.unlink(missing_ok=True)
    print("SMOKE PASS: deterministic build, purely-additive parity (2 cells), all cells parse, "
          "native-int regression ok, experiment-id placeholder present.")
    print(f"  telemetry lines: functions cell + validator cell; markers={allsrc.count('__EXP058_TELEMETRY__')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
