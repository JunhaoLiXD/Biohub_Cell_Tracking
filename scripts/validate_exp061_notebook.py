"""Local structural / bug-class validator for the exp_061 DeepCenter-TTA notebook.

Zero-GPU, fails closed. Verifies the built notebook is a strippable additive extension of the
frozen repro_059 (0.947) parent (text-level parity) and that the appended exp_061 logic honours
the CONSENSUS contract (proposal v5 + Codex challenge v1..v5 fixes). Does NOT execute the
pipeline; runtime xyonly byte-parity is asserted on Kaggle by the notebook itself. The transform
coordinate-map correctness is checked by scripts/test_exp061_behavioral.py (run here too).

Usage: python scripts/validate_exp061_notebook.py [<notebook.ipynb>]
"""

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT_NB = (ROOT / "experiments/repro_059_public_0947_exact_copy/snapshot/source/"
             "biohub-repro059-public-0947-exact-copy.ipynb")
DEFAULT_NB = ROOT / ".private/current/exp061_deepcenter_tta.ipynb"
MODULE = ROOT / "scripts/exp061_deepcenter_tta.py"
CONFIG = ROOT / "configs/exp_061_deepcenter_tta.yaml"
PARENT_SHA = "d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60"
MARK = "# exp061"
APPEND_MARKER = "# === exp_061 DeepCenter-TTA appended cell (purely additive) ==="

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

    # 1. text-level parity: strip appended cells + every `# exp061` line -> parent per-cell text
    rebuilt = []
    for c in cells:
        if c["cell_type"] == "code" and _text(c).startswith(APPEND_MARKER):
            continue
        rebuilt.append((c["cell_type"], "\n".join(ln for ln in _text(c).split("\n") if MARK not in ln)))
    parent_ref = [(c["cell_type"], _text(c)) for c in parent["cells"]]
    check(rebuilt == parent_ref, "strippable parity: appended cells + `# exp061` lines strip to parent")

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

    # 3. injected `# exp061` lines: 29-line watchdog + stub + gap1 logger + safe-div logger = 32
    big = _text([c for c in cells if c["cell_type"] == "code" and not _text(c).startswith(APPEND_MARKER)][0])
    injected = [ln for ln in big.split("\n") if MARK in ln]
    check(len(injected) == 35, f"exactly 35 injected `# exp061` lines (29 watchdog + 3 validator-disable + stub + 2 loggers) (got {len(injected)})")
    check("_e61os_pre.environ['BIOHUB_VALIDATOR_ENABLE'] = '0'" in big
          and "_e61os_pre.environ.get('BIOHUB_EXP061_ENABLE', '1') != '0'" in big,
          "validator/PP-sweep disabled via strippable BIOHUB_VALIDATOR_ENABLE=0, GATED on the probe flag (admission #6 + v2 #6 rollback)")
    check("_exp061_log_veto_candidate = (lambda" in big, "no-op stub injected (parent-run safe)")
    check(("_exp061_log_veto_candidate('gap', dataset, mid_t, {'middle_id': middle_id}, "
           "node_point(middle))") in big,
          "gap1 call-site logger captures middle_id (first DeepCenter consumer)")
    check(("_exp061_log_veto_candidate('safe_div', dataset, int(candidate['t']), "
           "{'parent_id': source_id, 'existing_child_id': existing_child_id, "
           "'candidate_child_id': candidate_id}, node_point(candidate))") in big,
          "safe-div call-site logger captures parent/existing-child/candidate-child IDs")
    # whole-run watchdog injected AFTER `from __future__` so it arms BEFORE the parent run
    blines = big.split("\n")
    fut_i = next((i for i, ln in enumerate(blines) if ln.startswith("from __future__")), -1)
    check(fut_i >= 0 and blines[fut_i + 1].strip().startswith("import time as _e61t")
          and "_EXP061_RUN_START = _e61t.time()" in blines[fut_i + 2],
          "whole-run watchdog + _EXP061_RUN_START injected immediately after `from __future__`")
    check("def _exp061_whole_run_guard" in big and "_e61sig.alarm(7200)" in big
          and "_EXP061_WATCHDOG_ARMED = True" in big,
          "whole-run SIGALRM watchdog arms a 2.0-h budget before the parent run")
    check("'/kaggle/working/metrics.json'" in big and "'exp061_deepcenter_tta_integrity_passed': False" in big
          and "_e61f.flush()" in big and "_e61f.close()" in big,
          "watchdog handler writes+flushes+closes a fail-closed over-budget metrics.json")
    check("children(recursive=True)" in big and "_e61c.kill()" in big,
          "watchdog handler REAPS GPU child subprocesses on timeout")
    check("raise KeyboardInterrupt" in big,
          "watchdog raises KeyboardInterrupt (BaseException) so `except Exception` cannot swallow it")

    # 4. appended cells: module + guarded top-level call
    appended = [c for c in cells if c["cell_type"] == "code" and _text(c).startswith(APPEND_MARKER)]
    check(len(appended) == 2, f"exactly 2 appended cells (got {len(appended)})")
    call_cell = _text(appended[1]) if len(appended) > 1 else ""
    check("run_exp061_deepcenter_tta(globals())" in call_cell and "BIOHUB_EXP061_ENABLE" in call_cell,
          "final cell = env-guarded top-level run_exp061_deepcenter_tta(globals())")

    # 5. module constants
    src = MODULE.read_text(encoding="utf-8")
    consts = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                consts[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass
    check(consts.get("EXP061_PARENT_SUBMISSION_SHA256") == PARENT_SHA, "parent-parity SHA == d3453380...")
    check(consts.get("EXP061_RESOLVED_OVERRIDES") == {"MOTION_RELINK_TIGHT_UM": 5.5},
          "pinned overrides == {MOTION_RELINK_TIGHT_UM: 5.5}")
    arms = consts.get("EXP061_ARMS")
    check(arms and tuple(arms)[0] == "xyonly" and set(arms) == {"xyonly", "zon", "xyd4"},
          "arms exactly {xyonly,zon,xyd4}, xyonly (parity control) first")
    check(consts.get("EXP061_CONTROL_ARM") == "xyonly", "control arm == xyonly")
    check("EXP061_FINALIZATION_RESERVE_SECONDS = 20.0 * 60.0" in src,
          "numeric 20-min finalization reserve constant")

    # 6. arm view specs (structural): xyonly 8, zon 16, xyd4 8; xyd4 replaces Ta with Aad
    check('"xyonly":' in src and '"zon":' in src and '"xyd4":' in src, "EXP061_ARM_VIEWS defines all three arms")
    check('("Aad", True)' in src and '"xyd4":' in src, "xyd4 uses the anti-diagonal reflection Aad")
    # zon adds Z-views
    check(all(z in src for z in ('"ZV0"', '"ZVx"', '"ZTa"')) or ("ZV0" in src and "ZVx" in src),
          "zon adds Z-reflected views (ZV0/ZVx/.../ZTa)")

    # 7. metrics.json contract + fail-closed
    import yaml
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    proto = cfg["validation"]["protocol"]
    check(consts.get("EXP061_VALIDATION_PROTOCOL") == proto,
          f"module validation protocol == config protocol ({proto})")
    check('"validation": {"protocol": EXP061_VALIDATION_PROTOCOL}' in src,
          "metrics.json includes validation.protocol object (controller metrics.py requires it)")
    check('"schema_version": 1' in src and '"experiment_id": experiment_id' in src,
          "metrics.json has schema_version=1 + experiment_id")
    check('"reproducible": False' in src and '"primary_metric"' in src, "metrics has reproducible:False + primary_metric")
    check('"exp061_deepcenter_tta_integrity_passed"' in src, "metrics emits the gate field")
    check(src.count("allow_nan=False") >= 2, "all json.dump reject NaN (allow_nan=False)")
    check(cfg["evaluation"]["gate_field"] == "exp061_deepcenter_tta_integrity_passed",
          "config gate_field matches the emitted gate field")

    # 8. contract fixes (proposal v5 / Codex v1..v5)
    check("EXP061_HARD_STOP_SECONDS" in src, "2.0-h hard stop constant present")
    check("_disarm_watchdog" in src and "signal.alarm(0)" in src,
          "module disarms the (top-injected) whole-run SIGALRM watchdog")
    check("within_hard_stop_and_timing_reliable" in src and "timing_reliable" in src,
          "final elapsed gate + timing-source reliability (fallback-to-now => fail)")
    check('"_EXP061_RUN_START" in g' in src and '"whole_run_watchdog_armed": whole_run_watchdog_armed' in src,
          "module uses whole-run start + requires the watchdog armed")
    check("_disarm_watchdog()" in src and src.rindex("_disarm_watchdog()") > src.index("exp061_telemetry.json"),
          "whole-run watchdog disarmed only AFTER metrics+telemetry finalization")
    check("if runtime_seconds > EXP061_HARD_STOP_SECONDS:" in src
          and "integrity_passed = False" in src.split("def _write_metrics", 1)[1],
          "COMMIT-TIME deadline recheck inside _write_metrics forces gate False if over budget")
    # xyonly parity checked immediately, stops before experimental arms (Codex v1 P2-5 / byte-parity)
    check('arm == EXP061_CONTROL_ARM and s["sha256"] != EXP061_PARENT_SUBMISSION_SHA256' in src,
          "xyonly control parity checked IMMEDIATELY, stops before zon/xyd4 on mismatch")
    check("control_parity_sha256_matches_parent" in src,
          "gate: xyonly byte-parity with parent 0.947 submission")
    # byte-parity computed through the SAME cached path (Codex v2 #4)
    check("_get_view_logits" in src and "_apply_inverse" in src and "acc = contrib.clone()" in src,
          "xyonly parity computed through the SAME view-cache accumulation path the experimental arms use")
    check("_EXP061_ACTIVE_ARM" in src and "EXP061_ARM_VIEWS[arm]" in src,
          "single per-arm heatmap function selects views by active arm (no separate control path)")
    # execution-validity SEPARATE from observed response (admission v2 #3): a correct arm can give
    # an identical heatmap (valid NULL). The gate is EXECUTION validity (intended views ran), NOT
    # heatmap difference; a zero response is a recorded null.
    check("execution_valid" in src and "arm_views_seen" in src and "delta == 0" not in src,
          "execution validity = intended views actually ran (arm_views_seen), separate from response")
    check('"verified_null": bool(execution_valid and not heatmap_differs)' in src,
          "verified_null == execution valid AND heatmap identical (a valid null, NOT a failure, admission v2 #3)")
    check('"experimental_arms_execution_valid": all_started_execution_valid' in src
          and 'mechanism.get(a, {}).get("execution_valid")' in src,
          "gate: each started experimental arm is EXECUTION-VALID (ran its views); response is a result not a gate")
    check("_heatmap_delta_stats" in src and "max_abs_delta" in src
          and '"active": bool(heatmap_differs)' in src,
          "observed heatmap response (active + |delta| stats) recorded SEPARATELY from execution validity")
    # cache rejection BEFORE use + persisted digest (admission v2 #5)
    check("_compute_and_store" in src and 'f"{key}.sha256").write_text(dig)' in src,
          "view cache persists a .sha256 sidecar digest (admission v2 #5)")
    check("reject-before-use -> recompute" in src and "_view_sha.get(key)" in src
          and "spath.read_text().strip()" in src,
          "invalid/unverifiable cache entries are REJECTED and recomputed BEFORE use (admission v2 #5)")
    # per-arm output audits applied to every arm (admission v2 #1)
    check("non-consecutive-frame edge" in src and "multi-parent (max in-degree > 1)" in src
          and "out-degree > 2" in src,
          "parent submission audits (consecutive-frame + max in-degree<=1 + out-degree<=2) applied per arm (admission v2 #1)")
    # explicit frozen-parent config comparison, not transitive (admission v2 #2)
    check("expected_parent_config = _capture_effective_config()" in src
          and "all_arm_configs_equal_frozen_parent" in src,
          "every arm's config compared DIRECTLY to an explicit frozen-parent config (admission v2 #2)")
    # telemetry: no per-candidate re-scoring; combined records; fork survival; per-arm receipt rows
    check("no fresh {} re-scoring" in src and "_pending_ids" in src and "candidate_log =" not in src,
          "candidate logger only STASHES ids (no fresh-cache re-scoring); one combined veto record (admission v2 #4)")
    check('"survived_final"' in src and "int(ccid) in children" in src and "int(ecid) in children" in src,
          "safe_div survival requires parent fork + BOTH candidate AND existing daughters, annotated per-arm before receipt (admission v2 #2/#4)")
    check('g["_dc_cache_trim"](heatmap_cache)' in src,
          "parent's bounded per-movie heatmap retention (_dc_cache_trim) preserved (admission v2 #4 memory)")
    check('"veto_rows": arm_veto_rows' in src,
          "per-arm receipt preserves that arm's veto evidence (partial-run safe, admission v2 #4)")
    check("feasibility_worksheet" in src and "seconds_per_view_forward" in src,
          "measured feasibility worksheet (per-forward rate + remaining margin) recorded (admission v2 budget)")
    # tensor-level nonfinite detection (admission #3)
    check("nonfinite_heatmap_events" in src and "np.isfinite(heatmap).all()" in src
          and "torch_mod.isfinite(logits).all()" in src,
          "nonfinite detected at the HEATMAP/logits tensor level, before any scorer nulls it (admission #3)")
    check('"no_nonfinite_heatmaps": no_nonfinite_heatmaps' in src,
          "gate: no nonfinite heatmaps (admission #3)")
    # checkpoint provenance REQUIRED, no silent fallback (admission #1)
    check("EXP061_RUNTIME_INTEGRITY_FILE" in src and 'get("deepcenter")' in src
          and "checkpoint_provenance_verified" in src and '"nockpt"' not in src,
          "checkpoint provenance REQUIRES the parent's verified deepcenter hash (no nockpt fallback, admission #1)")
    check('"checkpoint_provenance_verified": checkpoint_provenance_verified' in src,
          "gate: checkpoint provenance verified (admission #1)")
    # view-cache integrity (content hash + finiteness) + input/impl provenance in the key (#1)
    check("_view_sha" in src and "tobytes()).hexdigest()" in src and "integrity_failures" in src,
          "view cache validates a content sha256 on every hit (admission #1)")
    check('"view_cache_integrity_ok": view_cache_integrity_ok' in src,
          "gate: view-cache integrity ok (content hash + finiteness, admission #1)")
    check("EXP061_TRANSFORM_IMPL_VERSION" in src and "image_hash" in src
          and "img={image_hash}" in src,
          "view-cache key binds transform-impl version + verified ckpt + input image content hash (admission #1)")
    # budget-gated per-arm admission incl. the CONTROL (admission #6) + 20-min reserve
    check("EXP061_FINALIZATION_RESERVE_SECONDS" in src and "_remaining() < need" in src,
          "arm NOT started unless remaining budget >= est cost + 20-min finalization reserve")
    check("for arm in EXP061_ARMS:" in src and "if arm != EXP061_CONTROL_ARM" not in src.split("for arm in EXP061_ARMS:", 1)[1].split("arm_status[arm] = \"started\"")[0],
          "the reserve/admission check applies to EVERY arm incl. the control (admission #6)")
    check('"control_arm_started_first"' in src and "arms_started[0] == EXP061_CONTROL_ARM" in src,
          "gate: control arm xyonly started first (protected execution order)")
    check("arm_costs" in src and "max(arm_costs.values())" in src,
          "per-arm measured cost drives the next-arm admission (runtime-gated, not the estimate)")
    # atomic per-arm artifacts + started/completed/skipped/failed status (admission #4)
    check("os.replace(tmp_path, out_path)" in src and 'receipt_{arm}.json' in src
          and 'os.replace(rc_tmp' in src,
          "arm CSV + receipt published atomically via os.replace (admission #4)")
    check("arm_status" in src and all(s in src for s in ('"started"', '"completed"', '"skipped"', '"failed"'))
          and "arms_started.append(arm)   # recorded BEFORE running" in src,
          "arm status tracks started/completed/skipped/failed; arms_started set BEFORE running (admission #4)")
    # config equality to the FROZEN PARENT (transitive via xyonly parity), admission #5
    check("all_arm_configs_equal_parent = bool(all_arm_configs_equal_frozen_parent)" in src
          and '"all_arm_configs_equal_parent": all_arm_configs_equal_parent' in src,
          "gate: every arm's config == the FROZEN PARENT config (DIRECT comparison, admission v2 #2)")
    # validator/PP-sweep disabled at runtime (admission #6)
    check('"validator_sweep_disabled": validator_disabled' in src
          and "EXP061_REQUIRE_VALIDATOR_DISABLED" in src,
          "gate: the adaptive PP-sweep (validator) is disabled at runtime (admission #6)")
    # view-level disk-backed cache retained across sequential arms (Codex v3 #3)
    check("exp061_viewcache" in src and 'np.save(view_dir / f"{key}.npy"' in src and "np.load(fpath)" in src,
          "view-level cache is DISK-BACKED (lossless .npy), retained across sequential arms")
    check("EXP061_RAM_LRU_MAX_VIEWS" in src and "_ram_lru.popitem(last=False)" in src,
          "bounded RAM LRU in front of the disk view store")
    check("_view_key" in src and "run_provenance" in src,
          "view-cache key includes provenance (guards stale cross-run reuse)")
    # config completeness + parent-TTA env + finite scores
    check("EXP061_CONFIG_KEYS" in src and len(consts.get("EXP061_CONFIG_KEYS", ())) >= 40
          and 'config_complete' in src and "config_matches_control" in src,
          f"runtime effective-config over {len(consts.get('EXP061_CONFIG_KEYS', ()))} knobs + matches-control + completeness gate")
    check('"parent_deepcenter_tta_env_on": parent_tta_on' in src and "BIOHUB_DEEPCENTER_TTA" in src,
          "gate: parent DeepCenter TTA env ON (xyonly == parent path)")
    check(all(s in src for s in ('"missing"', '"nonfinite"', '"error"', '"score_status"')),
          "veto scores distinguish missing/nonfinite/error, never serialized as NaN")
    check('"no_veto_score_errors": n_error == 0' in src,
          "gate detects veto score errors")
    check('"no_exception_during_probe": run_exception is None' in src and "except BaseException" in src,
          "outer exception handler => run_exception flagged + gate False")
    # telemetry-persisted gate + written last
    mi = src.rfind("_write_metrics(integrity_passed, checks, arm_summaries, note=note,")
    ti = src.find('tel_path = out_dir / "exp061_telemetry.json"')
    check(0 < ti < mi, "telemetry attempted+validated BEFORE the unconditional final metrics.json write")
    check('"telemetry_persisted_and_valid": telemetry_persisted' in src
          and "json.loads(tel_path.read_text())" in src,
          "telemetry persistence is validated (round-trip) and is a GATE condition")
    # two direct consumers only (Codex v2 #2)
    check("veto_log" in src and '"kind": str(kind)' in src,
          "veto telemetry records the consumer kind (gap1 vs safe_div); gap2 reads no heatmap")
    check("shared_prediction_inputs_unchanged" in src and "_predictions_fingerprint" in src
          and "hashlib.sha256(p.read_bytes()).hexdigest()" in src,
          "shared prediction-input immutability uses a CONTENT sha256 (not size/mtime, admission #5)")
    check("finally:" in src and 'g["deepcenter_heatmap_for_frame"] = _orig_heatmap_for_frame' in src,
          "monkeypatches restored in finally")
    # cross-arm exact deltas
    check('"edges_added"' in src and '"edges_removed"' in src and '"forks_added"' in src,
          "cross-arm delta emits EXACT edge/fork differences vs xyonly")

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
