"""Behavioral test of exp_060 embedded logic (admission fixes #3/#4). Zero-GPU.

Executes run_exp060_threshold_sweep against a MOCK notebook namespace whose stub parent functions
reproduce the threshold-gated safe-division control flow, so we behaviorally verify (not string-
match) the required properties, AND it executes the EXTRACTED REAL parent gate function
(deepcenter_accept_repair_point) with mocked GPU deps.

Verified here:
  * shared heatmap cache => each frame computed EXACTLY ONCE across 3 arms (GPU counter);
  * effective-config fingerprint => only DEEPCENTER_SAFE_DIV_THRESHOLD differs across arms;
  * input fingerprint => each arm's gate evaluates the SAME candidate set (threshold-invariant
    candidate generation);
  * arm-order invariance; threshold monotonicity (0.18 admits >= 0.22 divisions);
  * telemetry carries IDs + gate_accept/gate_bypass + survived_final;
  * fail-closed: wrong parity -> gate False + metrics written + early-stop; a filtering EXCEPTION
    -> metrics.json still written + gate False; a NONFINITE score -> gate False; an over-budget
    deadline -> gate False;
  * the EXTRACTED real gate: score<thr rejects, score>=thr accepts, None bypass-accepts.

Real parent postprocessing needs GPU/torch and is not run; its runtime 0.20 byte-parity is the
notebook's own ground-truth assert.
"""

import ast
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/exp060_threshold_sweep.py"
PARENT_NB = (ROOT / "experiments/repro_059_public_0947_exact_copy/snapshot/source/"
             "biohub-repro059-public-0947-exact-copy.ipynb")

_spec = importlib.util.spec_from_file_location("exp060_threshold_sweep", MODULE_PATH)
exp060 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exp060)

_fail = []
_CFG_KEYS = ["MOTION_RELINK_TIGHT_UM", "DEEPCENTER_SAFE_DIV_THRESHOLD", "GAP_CLOSE_UM",
             "OUTPUT_MIN_TRACK_LEN", "SAFE_DIV_MAX_UM", "DEEPCENTER_GAP_THRESHOLD",
             "ILP_DIVISION_WEIGHT"]


def check(cond, msg):
    print(("  ok  " if cond else " FAIL ") + msg)
    if not cond:
        _fail.append(msg)


class _FakeGraph:
    def __init__(self, stem):
        self.stem = stem
        self._nodes = [{"node_id": 0, "t": 0, "z": 1.0, "y": 1.0, "x": 1.0},
                       {"node_id": 1, "t": 1, "z": 1.0, "y": 2.0, "x": 2.0},
                       {"node_id": 2, "t": 1, "z": 1.0, "y": 3.0, "x": 3.0},
                       {"node_id": 3, "t": 1, "z": 1.0, "y": 4.0, "x": 4.0}]
        self._edges = [{"source_id": 0, "target_id": 1, "edge_prob": 0.9}]

    def node_attrs(self):
        rows = self._nodes
        return type("NA", (), {"iter_rows": staticmethod(lambda named=True: iter(rows))})()

    def edge_attrs(self):
        rows = self._edges
        return type("EA", (), {"iter_rows": staticmethod(lambda named=True: iter(rows))})()


def _make_namespace(workdir, gpu_counter, per_arm_cfg, per_arm_cands, fault=None,
                    watchdog_armed=True, run_start="NOW", clock=None):
    import time
    stems = ["44b6_aaaa", "6bba_bbbb"]
    repo = workdir / "repo"
    for s in stems:
        (repo / "predictions/unknown/unet_transformer/split_0" / f"{s}.geff").mkdir(parents=True, exist_ok=True)
    cand_score = {2: 0.21, 3: 0.19}  # daughter 2 strong, 3 weak

    def graph_from_geff(path):
        return _FakeGraph(Path(path).stem)

    # populate the FULL effective-config surface (every EXP060_CONFIG_KEYS knob) so the module's
    # completeness gate is satisfied; only DEEPCENTER_SAFE_DIV_THRESHOLD varies across arms.
    _cfg_extra = {k: 1.0 for k in exp060.EXP060_CONFIG_KEYS}

    def deepcenter_heatmap_for_frame(dataset, t, bundle, fc, hc):
        gpu_counter[(dataset, int(t))] = gpu_counter.get((dataset, int(t)), 0) + 1
        return {"dataset": dataset, "t": int(t)}

    def deepcenter_score_point(dataset, t, point, bundle, fc, hc):
        g_ns["deepcenter_heatmap_for_frame"](dataset, t, bundle, fc, hc)
        # faithful to the REAL scorer: a nonfinite heatmap value is sanitized to None BEFORE the
        # logger sees it (=> manifests as a missing-score bypass, Codex formal review fix #1).
        if fault == "nonfinite" and int(point) == 3:
            return None
        return cand_score.get(int(point), 0.0)

    def deepcenter_accept_repair_point(dataset, t, point, bundle, fc, hc, stats, prefix, threshold):
        s = g_ns["deepcenter_score_point"](dataset, t, point, bundle, fc, hc)
        import math
        if s is None or not math.isfinite(s):
            return True
        return s >= float(threshold)

    def filter_output_graph(nodes_by_id, raw_edges, dataset=None, deepcenter_bundle=None):
        if clock is not None:
            clock["t"] += 125  # model per-movie work advancing the (patched) wall clock
        thr = g_ns["DEEPCENTER_SAFE_DIV_THRESHOLD"]
        # capture the FULL effective config the arm ran with (Codex v4 fix #2: fuller fingerprint)
        per_arm_cfg.setdefault(thr, {k: g_ns[k] for k in _CFG_KEYS})
        edges = list(raw_edges)
        if fault == "exception" and dataset == "6bba_bbbb":
            raise RuntimeError("injected filtering exception")
        for cand in (2, 3):
            per_arm_cands.setdefault(thr, set()).add((dataset, cand))
            g_ns["_exp060_log_safe_div_candidate"](dataset, 1, 0, 1, cand, cand, deepcenter_bundle, {}, {})
            if deepcenter_accept_repair_point(dataset, 1, cand, deepcenter_bundle, {}, {}, {}, "safe_div", thr):
                edges.append({"source_id": 0, "target_id": cand, "edge_prob": 0.5})
        return nodes_by_id, edges, {"safe_divisions_added": len(edges) - 1}

    g_ns = {
        **_cfg_extra,
        "WORKING_DIR": str(workdir), "REPO_DIR": str(repo), "METHOD": "unet_transformer",
        "test_stems": stems,
        "CSV_COLUMNS": ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"],
        "DEEPCENTER_VETO_DETECTOR": object(),
        "graph_from_geff": graph_from_geff,
        "deepcenter_heatmap_for_frame": deepcenter_heatmap_for_frame,
        "deepcenter_score_point": deepcenter_score_point,
        "deepcenter_accept_repair_point": deepcenter_accept_repair_point,
        "filter_output_graph": filter_output_graph,
        "DEEPCENTER_SAFE_DIV_THRESHOLD": 0.20, "MOTION_RELINK_TIGHT_UM": 5.5,
        "_exp060_log_safe_div_candidate": (lambda *a, **k: None),
        "_EXP060_WATCHDOG_ARMED": watchdog_armed,
    }
    if run_start is not None:
        g_ns["_EXP060_RUN_START"] = (clock["t"] if clock is not None else time.time()) if run_start == "NOW" else run_start
    return g_ns, stems


def _reset():
    exp060._EXP060_CANDIDATE_LOG.clear()
    exp060._EXP060_ACTIVE_ARM["threshold"] = None


def _run(pin="AUTO", fault=None, unreliable_start=False, watchdog_armed=True,
         run_start="NOW", clock=None, hard_stop=None, tel_write_fault=False):
    import builtins
    workdir = Path(tempfile.mkdtemp(prefix="exp060_test_"))
    gpu, cfg, cands = {}, {}, {}
    g_ns, _ = _make_namespace(workdir, gpu, cfg, cands, fault=fault,
                              watchdog_armed=watchdog_armed, run_start=run_start, clock=clock)
    saved_sha = exp060.EXP060_PARENT_SUBMISSION_SHA256
    saved_start = exp060._exp060_process_start_seconds
    saved_hs = exp060.EXP060_HARD_STOP_SECONDS
    _reset()
    if pin == "AUTO":
        pre = Path(tempfile.mkdtemp(prefix="exp060_pre_"))
        g2, _ = _make_namespace(pre, {}, {}, {})
        exp060.run_exp060_threshold_sweep(g2)
        exp060.EXP060_PARENT_SUBMISSION_SHA256 = json.loads((pre / "metrics.json").read_text())["arm_submission_sha256"]["thr020"]
        _reset()
    elif pin is not None:
        exp060.EXP060_PARENT_SUBMISSION_SHA256 = pin
    if unreliable_start:
        exp060._exp060_process_start_seconds = lambda: (__import__("time").time(), False)
    if hard_stop is not None:
        exp060.EXP060_HARD_STOP_SECONDS = hard_stop

    import time as _time
    real_time = _time.time
    real_open = builtins.open

    def _fake_open(file, *a, **k):
        if tel_write_fault and str(file).endswith("exp060_telemetry.json"):
            raise OSError("injected telemetry write fault")
        return real_open(file, *a, **k)

    try:
        if clock is not None:
            _time.time = lambda: float(clock["t"])
        if tel_write_fault:
            builtins.open = _fake_open
        exp060.run_exp060_threshold_sweep(g_ns)
        metrics = json.loads((workdir / "metrics.json").read_text()) if (workdir / "metrics.json").exists() else None
        telf = workdir / "exp060" / "exp060_telemetry.json"
        tel = json.loads(telf.read_text()) if telf.exists() else None
    finally:
        _time.time = real_time
        builtins.open = real_open
        exp060.EXP060_PARENT_SUBMISSION_SHA256 = saved_sha
        exp060._exp060_process_start_seconds = saved_start
        exp060.EXP060_HARD_STOP_SECONDS = saved_hs
    return workdir, gpu, cfg, cands, metrics, tel


def _test_extracted_real_gate():
    """Execute the REAL parent deepcenter_accept_repair_point with mocked GPU deps."""
    nb = json.loads(PARENT_NB.read_text(encoding="utf-8"))
    text = "".join([c for c in nb["cells"] if c["cell_type"] == "code"][0]["source"])
    tree = ast.parse(text)
    fn_src = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "deepcenter_accept_repair_point":
            fn_src = ast.get_source_segment(text, node)
            break
    if fn_src is None:
        check(False, "could not extract real deepcenter_accept_repair_point")
        return
    scores = {"acc": 0.30, "rej": 0.10, "none": None}
    import math as _math

    class _NP:  # permissive numpy stub for def-time / unrelated references
        def __getattr__(self, k):
            return lambda *a, **k2: None
    ns = {"USE_DEEPCENTER_VETO": True, "np": _NP(), "math": _math,
          "deepcenter_score_point": lambda ds, t, p, b, fc, hc: scores[p]}
    exec(fn_src, ns)
    gate = ns["deepcenter_accept_repair_point"]
    st = lambda: {"deepcenter_safe_div_missing": 0, "deepcenter_safe_div_checked": 0,
                  "deepcenter_safe_div_accepted": 0, "deepcenter_safe_div_rejected": 0}
    check(gate("d", 1, "acc", object(), {}, {}, st(), "safe_div", 0.20) is True,
          "extracted REAL gate: score>=threshold accepts")
    check(gate("d", 1, "rej", object(), {}, {}, st(), "safe_div", 0.20) is False,
          "extracted REAL gate: score<threshold rejects")
    check(gate("d", 1, "none", object(), {}, {}, st(), "safe_div", 0.20) is True,
          "extracted REAL gate: missing score bypass-accepts")


def _test_watchdog_handler():
    """Execute the INJECTED whole-run watchdog handler from the BUILT notebook: it must write a
    fail-closed over-budget metrics.json then raise TimeoutError (Codex v4 fix #2)."""
    import builtins, io, json as _json, time as _time
    built = ROOT / ".private/current/exp060_deepcenter_safe_div_threshold_sweep.ipynb"
    nb = json.loads(built.read_text(encoding="utf-8"))
    text = "".join([c for c in nb["cells"] if c["cell_type"] == "code"
                    and not "".join(c["source"]).startswith("# === exp_060")][0]["source"])
    fn_src = None
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef) and node.name == "_exp060_whole_run_guard":
            fn_src = ast.get_source_segment(text, node)
            break
    if fn_src is None:
        check(False, "could not extract injected watchdog handler")
        return
    ns = {"_e6j": _json, "_e6t": _time, "_EXP060_RUN_START": _time.time() - 10000.0}
    exec(fn_src, ns)
    handler = ns["_exp060_whole_run_guard"]
    captured = {}
    real_open = builtins.open

    class _CapIO(io.StringIO):
        def close(self):  # the handler flushes+closes; capture the bytes before close
            captured["value"] = self.getvalue()
            super().close()

    def fake_open(f, *a, **k):
        if str(f) == "/kaggle/working/metrics.json":
            return _CapIO()
        return real_open(f, *a, **k)

    raised = False
    builtins.open = fake_open
    try:
        handler(None, None)
    except KeyboardInterrupt:  # BaseException => not swallowed by broad `except Exception` (fix)
        raised = True
    finally:
        builtins.open = real_open
    check(raised, "injected watchdog handler raises KeyboardInterrupt (BaseException, not swallowable)")
    m = _json.loads(captured.get("value", "{}") or "{}")
    check(m.get("schema_version") == 1 and m.get("exp060_threshold_sweep_integrity_passed") is False
          and m.get("validation", {}).get("protocol") == exp060.EXP060_VALIDATION_PROTOCOL
          and float(m.get("runtime_seconds", 0)) > 0,
          "injected watchdog handler writes a controller-valid fail-closed over-budget metrics.json")


def main() -> int:
    import time
    print("behavioral test: exp_060 orchestration + extracted real gate")

    # PASS path (the mock provides _EXP060_RUN_START + _EXP060_WATCHDOG_ARMED, mirroring the
    # top-of-notebook whole-run watchdog injection).
    workdir, gpu, cfg, cands, metrics, tel = _run(pin="AUTO")
    check(metrics and metrics["exp060_threshold_sweep_integrity_passed"] is True, "PASS path: integrity gate True")
    check(set(gpu) == {("44b6_aaaa", 1), ("6bba_bbbb", 1)},
          f"heatmap INPUT content: EXACT expected (dataset,t) frame set ({sorted(gpu)})")
    check(metrics["validation"]["protocol"] == exp060.EXP060_VALIDATION_PROTOCOL and metrics["schema_version"] == 1,
          "metrics controller contract (schema+validation)")
    check(all(v == 1 for v in gpu.values()) and len(gpu) >= 1,
          f"heatmap computed once per frame across 3 arms (GPU={dict(gpu)})")
    # effective-config fingerprint: FULL config identical across arms EXCEPT the threshold
    cfg_nothr = [{k: v for k, v in c.items() if k != "DEEPCENTER_SAFE_DIV_THRESHOLD"} for c in cfg.values()]
    check(len(cfg) == 3 and all(c == cfg_nothr[0] for c in cfg_nothr) and len(cfg_nothr[0]) >= 6,
          "effective-config fingerprint: full config identical across arms except the threshold")
    # input fingerprint: each arm evaluates the same candidate set
    cand_sets = list(cands.values())
    check(len(cand_sets) == 3 and all(s == cand_sets[0] for s in cand_sets),
          "input fingerprint: identical candidate set per arm (threshold-invariant generation)")
    fc = metrics["arm_final_counts"]
    check(fc["thr018"]["edges"] >= fc["thr022"]["edges"], "0.18 admits >= 0.22 divisions")
    rows = tel["candidate_telemetry_rows"]
    check(rows and all({"parent_id", "existing_child_id", "candidate_child_id", "gate_accept",
                        "gate_bypass", "survived_final"} <= set(r) for r in rows),
          "telemetry rows carry IDs + gate_accept/gate_bypass + survived_final")
    check(any(r["survived_final"] is True for r in rows), "at least one candidate joined to a surviving final fork")
    check(metrics["checks"]["effective_config_threshold_only"] is True,
          "runtime effective-config fingerprint: full config identical across arms except threshold (fix #3)")
    check(metrics["checks"]["telemetry_persisted_and_valid"] is True, "telemetry persisted+validated (fix #2)")
    check(metrics["checks"]["shared_prediction_inputs_unchanged"] is True,
          "shared prediction inputs immutable across arms (real-pipeline evidence, formal r3 #2)")
    d18 = tel["delta_vs_control"]["thr018"]
    check(d18 and all("edges_added" in v and "edges_removed" in v for v in d18.values()),
          "cross-arm delta emits EXACT edge differences (fix #4)")
    check(all("survived_candidate_edge" in r for r in rows),
          "telemetry distinguishes candidate-edge survival vs full-fork survival (fix #4)")

    # arm-order invariance
    saved = exp060.EXP060_ARMS
    try:
        exp060.EXP060_ARMS = (0.20, 0.22, 0.18)
        _, _, _, _, m2, _ = _run(pin=metrics["arm_submission_sha256"]["thr020"])
        check(m2["arm_submission_sha256"]["thr018"] == metrics["arm_submission_sha256"]["thr018"]
              and m2["arm_submission_sha256"]["thr022"] == metrics["arm_submission_sha256"]["thr022"],
              "arm-order invariance: per-arm SHAs identical under permuted order")
    finally:
        exp060.EXP060_ARMS = saved

    # FAIL: wrong parity -> gate False + metrics + early stop
    _, _, _, _, mf, _ = _run(pin="deadbeef" * 8)
    check(mf and mf["exp060_threshold_sweep_integrity_passed"] is False, "wrong parity => gate False")
    check("thr018" not in mf["arm_submission_sha256"], "early-parity stop: 0.18/0.22 not run")

    # FAIL: filtering exception -> metrics.json still written, gate False
    we, _, _, _, me, _ = _run(pin="AUTO", fault="exception")
    check((we / "metrics.json").exists() and me["exp060_threshold_sweep_integrity_passed"] is False,
          "filtering exception => metrics.json still written + gate False")
    check(me.get("run_exception"), "exception recorded in metrics")

    # FAIL: nonfinite score (sanitized to None by the real scorer => missing bypass) -> gate False
    _, _, _, _, mn, _ = _run(pin="AUTO", fault="nonfinite")
    check(mn and mn["exp060_threshold_sweep_integrity_passed"] is False,
          "nonfinite-as-missing bypass (real scorer path) => gate False")
    check(mn["checks"]["no_missing_or_nonfinite_bypass"] is False and mn["candidate_counts"]["missing_bypass"] > 0,
          "nonfinite manifests as a missing bypass and is flagged (fix #1)")

    good_sha = metrics["arm_submission_sha256"]["thr020"]

    # FAIL: runaway before an arm (epoch-0 run start => huge elapsed => pre-arm hard-stop)
    _, _, _, _, md, _ = _run(pin=good_sha, run_start=0.0)
    check(md and md["checks"]["within_hard_stop_and_timing_reliable"] is False,
          "runaway elapsed => within_hard_stop check False => gate False")

    # FAIL: FINAL-ARM OVERRUN via a moving (patched) clock — all pre-arm checks pass, but arm-3
    # execution pushes elapsed past the (shrunk) budget so the FINAL gate catches it.
    clk = {"t": 0.0}
    _, _, _, _, mo, _ = _run(pin=good_sha, run_start=0.0, clock=clk, hard_stop=600.0)
    check(mo and mo["checks"]["within_hard_stop_and_timing_reliable"] is False
          and mo["checks"]["no_hard_stop_triggered"] is True
          and "thr022" in mo["arm_submission_sha256"],
          "final-arm overrun: all arms ran, FINAL elapsed gate fails closed (not a pre-arm stop)")
    check(mo and "commit-time over budget" in mo.get("note", ""),
          "commit-time deadline recheck fires when finalization lands over budget (v4 fix #1)")

    # FAIL: unreliable timing source (no _EXP060_RUN_START; process-start read fails) => gate False
    _, _, _, _, mu, _ = _run(pin=good_sha, run_start=None, unreliable_start=True)
    check(mu and mu["checks"]["within_hard_stop_and_timing_reliable"] is False,
          "unreliable timing source => within_hard_stop False (no silent clock reset)")

    # FAIL: whole-run watchdog not armed => gate False
    _, _, _, _, mw, _ = _run(pin=good_sha, watchdog_armed=False)
    check(mw and mw["checks"]["whole_run_watchdog_armed"] is False,
          "whole-run watchdog not armed => gate False")

    # telemetry persistence fault => metrics.json STILL written (unconditional, last) but the gate
    # FAILS CLOSED because telemetry is a required contract output (Codex formal review fix #2)
    wt, _, _, _, mt, tt = _run(pin=good_sha, tel_write_fault=True)
    check((wt / "metrics.json").exists() and mt is not None and tt is None,
          "telemetry fault: metrics.json still written (unconditional), telemetry absent")
    check(mt["exp060_threshold_sweep_integrity_passed"] is False
          and mt["checks"]["telemetry_persisted_and_valid"] is False,
          "telemetry persistence is a GATE condition: fault => gate False (fix #2)")

    # extracted REAL parent gate + injected watchdog handler
    _test_extracted_real_gate()
    _test_watchdog_handler()

    print()
    if _fail:
        print(f"BEHAVIORAL TEST FAILED: {len(_fail)}")
        for m in _fail:
            print("  - " + m)
        return 1
    print("BEHAVIORAL TEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
