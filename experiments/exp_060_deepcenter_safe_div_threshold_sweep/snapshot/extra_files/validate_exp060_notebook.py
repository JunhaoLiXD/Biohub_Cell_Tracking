"""Local structural / bug-class validator for the exp_060 threshold-sweep notebook (v2).

Zero-GPU, fails closed. Verifies the built notebook is a strippable additive extension of the
frozen repro_059 (0.947) parent (text-level parity) and that the appended exp_060 logic honours
the CONSENSUS contract + the admission-v1 fixes. Does NOT execute the pipeline; runtime 0.20
byte-parity is asserted on Kaggle by the notebook itself.

Usage: python scripts/validate_exp060_notebook.py [<notebook.ipynb>]
"""

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT_NB = (ROOT / "experiments/repro_059_public_0947_exact_copy/snapshot/source/"
             "biohub-repro059-public-0947-exact-copy.ipynb")
DEFAULT_NB = ROOT / ".private/current/exp060_deepcenter_safe_div_threshold_sweep.ipynb"
MODULE = ROOT / "scripts/exp060_threshold_sweep.py"
CONFIG = ROOT / "configs/exp_060_deepcenter_safe_div_threshold_sweep.yaml"
PARENT_SHA = "d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60"
MARK = "# exp060"
APPEND_MARKER = "# === exp_060 threshold-sweep appended cell (purely additive) ==="

_failures = []


def check(cond, msg):
    print(("  ok  " if cond else " FAIL ") + msg)
    if not cond:
        _failures.append(msg)


def _text(cell):
    return "".join(cell["source"])


def main() -> int:
    nb_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_NB
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    parent = json.loads(PARENT_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    print(f"validating {nb_path}")

    # 1. text-level parity: strip appended cells + every `# exp060` line -> parent per-cell text
    rebuilt = []
    for c in cells:
        if c["cell_type"] == "code" and _text(c).startswith(APPEND_MARKER):
            continue
        rebuilt.append((c["cell_type"], "\n".join(ln for ln in _text(c).split("\n") if MARK not in ln)))
    parent_ref = [(c["cell_type"], _text(c)) for c in parent["cells"]]
    check(rebuilt == parent_ref, "strippable parity: appended cells + `# exp060` lines strip to parent")

    # 2. all code cells parse
    ok = True
    for c in cells:
        if c["cell_type"] == "code":
            try:
                ast.parse(_text(c))
            except SyntaxError as e:
                ok = False
                print(f"    SyntaxError: {e}")
    check(ok, "all code cells parse (AST)")

    # 3. exactly two injected `# exp060` lines: stub + call-site logger with full IDs
    big = _text([c for c in cells if c["cell_type"] == "code" and not _text(c).startswith(APPEND_MARKER)][0])
    injected = [ln for ln in big.split("\n") if MARK in ln]
    check(len(injected) == 31, f"exactly 31 injected `# exp060` lines (stub+logger+29-line guard) (got {len(injected)})")
    check("_exp060_log_safe_div_candidate = (lambda" in big, "no-op stub injected before the def (parent-run safe)")
    check(("_exp060_log_safe_div_candidate(dataset, int(candidate['t']), source_id, "
           "existing_child_id, candidate_id, node_point(candidate)") in big,
          "call-site logger captures parent/existing-child/candidate-child IDs (admission fix #2)")
    # whole-run watchdog injected AFTER `from __future__` so it arms BEFORE the parent run (v3 fix #1)
    blines = big.split("\n")
    fut_i = next((i for i, ln in enumerate(blines) if ln.startswith("from __future__")), -1)
    check(fut_i >= 0 and blines[fut_i + 1].strip().startswith("import time as _e6t")
          and "_EXP060_RUN_START = _e6t.time()" in blines[fut_i + 2],
          "whole-run watchdog + _EXP060_RUN_START injected immediately after `from __future__`")
    check("def _exp060_whole_run_guard" in big and "_e6sig.alarm(7200)" in big
          and "_EXP060_WATCHDOG_ARMED = True" in big,
          "whole-run SIGALRM watchdog arms a 2.0-h budget before the parent run")
    check("'/kaggle/working/metrics.json'" in big and "'exp060_threshold_sweep_integrity_passed': False" in big
          and "_e6f.flush()" in big and "_e6f.close()" in big,
          "watchdog handler writes+flushes+closes a fail-closed over-budget metrics.json")
    check("children(recursive=True)" in big and "_e6c.kill()" in big,
          "watchdog handler REAPS GPU child subprocesses on timeout (formal review fix #1)")

    # 4. appended cells: module + guarded top-level call
    appended = [c for c in cells if c["cell_type"] == "code" and _text(c).startswith(APPEND_MARKER)]
    check(len(appended) == 2, f"exactly 2 appended cells (got {len(appended)})")
    call_cell = _text(appended[1]) if len(appended) > 1 else ""
    check("run_exp060_threshold_sweep(globals())" in call_cell and "BIOHUB_EXP060_ENABLE" in call_cell,
          "final cell = env-guarded top-level run_exp060_threshold_sweep(globals())")

    # 5. module constants
    src = MODULE.read_text(encoding="utf-8")
    consts = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                consts[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass
    check(consts.get("EXP060_PARENT_SUBMISSION_SHA256") == PARENT_SHA, "parent-parity SHA == d3453380...")
    check(consts.get("EXP060_RESOLVED_OVERRIDES") == {"MOTION_RELINK_TIGHT_UM": 5.5},
          "pinned overrides == {MOTION_RELINK_TIGHT_UM: 5.5}")
    arms = consts.get("EXP060_ARMS")
    check(arms and tuple(arms)[0] == 0.20 and set(arms) == {0.20, 0.18, 0.22},
          "arms exactly {0.20,0.18,0.22}, 0.20 first")

    # 6. metrics.json contract (admission fix #1) + fail-closed
    import yaml
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    proto = cfg["validation"]["protocol"]
    check(consts.get("EXP060_VALIDATION_PROTOCOL") == proto,
          f"module validation protocol == config protocol ({proto})")
    check('"validation": {"protocol": EXP060_VALIDATION_PROTOCOL}' in src,
          "metrics.json includes validation.protocol object (controller metrics.py requires it)")
    check('"schema_version": 1' in src and '"experiment_id": experiment_id' in src,
          "metrics.json has schema_version=1 + experiment_id")
    check('"reproducible": False' in src and '"primary_metric"' in src, "metrics has reproducible:False + primary_metric")
    check('"exp060_threshold_sweep_integrity_passed"' in src, "metrics emits the gate field")
    check(src.count("allow_nan=False") >= 2, "all json.dump reject NaN (allow_nan=False)")
    check(cfg["evaluation"]["gate_field"] == "exp060_threshold_sweep_integrity_passed",
          "config gate_field matches the emitted gate field")

    # 7. admission v1/v2 fixes: deadline enforcement, early stop, status, watchdog, fail-closed
    check("EXP060_HARD_STOP_SECONDS" in src and "if _elapsed() > EXP060_HARD_STOP_SECONDS" in src,
          "2.0-h hard stop checked between arms")
    check("_disarm_watchdog" in src and "signal.alarm(0)" in src,
          "module disarms the (top-injected) whole-run SIGALRM watchdog (v3 fix #1)")
    check("within_hard_stop_and_timing_reliable" in src and "timing_reliable" in src,
          "final elapsed gate + timing-source reliability (fallback-to-now => fail, v2 fix #2)")
    check('"_EXP060_RUN_START" in g' in src and '"whole_run_watchdog_armed": whole_run_watchdog_armed' in src,
          "module uses whole-run start + requires the watchdog armed (v3 fix #1)")
    check("_disarm_watchdog()" in src and src.rindex("_disarm_watchdog()") > src.index("exp060_telemetry.json"),
          "whole-run watchdog disarmed only AFTER metrics+telemetry finalization (v3 fix #1)")
    check("if runtime_seconds > EXP060_HARD_STOP_SECONDS:" in src
          and "integrity_passed = False" in src.split("def _write_metrics", 1)[1],
          "COMMIT-TIME deadline recheck inside _write_metrics forces gate False if over budget (v4 fix #1)")
    check('label == "thr020" and arm_summaries["thr020"]["sha256"] != EXP060_PARENT_SUBMISSION_SHA256' in src,
          "0.20 control parity checked IMMEDIATELY, stops before 0.18/0.22 (v1 fix #4)")
    check(all(s in src for s in ('"missing"', '"nonfinite"', '"error"', '"score_status"')),
          "candidate scores distinguish missing/nonfinite/error, never serialized as NaN")
    check('"no_missing_or_nonfinite_bypass": (n_missing == 0 and n_nonfinite == 0)' in src
          and '"no_candidate_score_errors": n_error == 0' in src,
          "gate detects nonfinite (real scorer => None => missing) via zero-missing-bypass (formal fix #1)")
    check('"no_exception_during_sweep": run_exception is None' in src
          and "except BaseException" in src,
          "outer exception handler => run_exception flagged + gate False (v2 fix #1)")
    # metrics.json is written LAST + unconditionally, AFTER telemetry is attempted+validated; and
    # telemetry persistence is a GATE condition (formal review fix #2).
    mi = src.rfind("_write_metrics(integrity_passed, checks, arm_summaries, note=note,")
    ti = src.find('tel_path = out_dir / "exp060_telemetry.json"')
    check(0 < ti < mi, "telemetry attempted+validated BEFORE the unconditional final metrics.json write (formal fix #2)")
    check('"telemetry_persisted_and_valid": telemetry_persisted' in src
          and "json.loads(tel_path.read_text())" in src,
          "telemetry persistence is validated (round-trip) and is a GATE condition (formal fix #2)")
    check('"effective_config_threshold_only": effective_config_threshold_only' in src
          and "EXP060_CONFIG_KEYS" in src and len(consts.get("EXP060_CONFIG_KEYS", ())) >= 40
          and "config_complete = all(k in g for k in EXP060_CONFIG_KEYS)" in src
          and "_all_complete" in src,
          f"runtime effective-config fingerprint over {len(consts.get('EXP060_CONFIG_KEYS', ()))} knobs + no-missing-key completeness gate (formal fix #3)")
    check('_canon = _cfg_minus_thr("thr020")' in src and "_thr_assigned" in src
          and '"env:" + _envk' in src,
          "config gate: canonical=parent(0.20) config + per-arm threshold assertion + env TTA settings (formal r3 #3)")
    check('"shared_prediction_inputs_unchanged": shared_prediction_inputs_unchanged' in src
          and "_predictions_fingerprint" in src,
          "shared prediction-input immutability is a gate condition on the real pipeline (formal r3 #2)")
    check("raise KeyboardInterrupt" in _text([c for c in cells if c["cell_type"]=="code"
          and not _text(c).startswith(APPEND_MARKER)][0]),
          "watchdog raises KeyboardInterrupt (BaseException) so broad `except Exception` cannot swallow it (formal r3 #1)")
    check("survived_candidate_edge" in src and "int(ccid) in forks[int(pid)]" in src,
          "fork survival requires BOTH daughters (parent is a final fork), not just the candidate edge (formal fix #4)")
    check('"edges_added"' in src and '"edges_removed"' in src,
          "cross-arm delta emits EXACT edge differences (formal fix #4)")
    check(all(s in src for s in ("gate_accept", "gate_bypass", "survived_final")),
          "telemetry records gate accept/bypass + final survival")
    check("finally:" in src and 'g["deepcenter_heatmap_for_frame"] = _orig_heatmap_for_frame' in src,
          "monkeypatches restored in finally")

    # 8. isolation contract
    check("persistent_heatmaps" in src, "shared persistent heatmap cache (compute once)")
    check('g["DEEPCENTER_SAFE_DIV_THRESHOLD"] = float(threshold)' in src,
          "arm selected ONLY by overriding the global safe-div threshold")

    print()
    if _failures:
        print(f"VALIDATION FAILED: {len(_failures)} check(s)")
        for m in _failures:
            print("  - " + m)
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
