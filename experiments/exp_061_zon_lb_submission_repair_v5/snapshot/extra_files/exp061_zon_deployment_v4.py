"""exp061 zon-only deployment runner copied from the frozen v2 research harness. — DeepCenter repair-heatmap TTA probe (xyonly / zon / xyd4).

APPENDED (with a tiny strippable call-site injection) onto the frozen repro_059 (Public LB 0.947)
notebook by scripts/build_exp061_deepcenter_tta.py. The parent's own 0.947 prediction path runs
byte-unchanged; stripping every `# exp061` line reproduces the parent exactly (parity by
construction). The deployment entry point runs only the frozen zon arm and writes its current-input
receipt. It intentionally does not run XY parity or xyd4 replays.

Strategy record: docs/research/exp061_z_reflection_deepcenter_tta_proposal.md (v5, CONSENSUS) +
exp061_codex_challenge_v1..v5.md. Parent submission SHA (0.947 = the xyonly byte-parity target):
  d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60

Design (CONSENSUS):
  * THREE arms differing ONLY in the DeepCenter TTA set, all else frozen at the parent's resolved
    config (MOTION_RELINK_TIGHT_UM=5.5, from ppsweep_selected.json; adaptive PP-sweep is the
    parent's own byte-frozen path and is not used for arm selection):
      - xyonly : parent TTA exactly (V0,Vx,Vy,Vxy,R1,R3,Td,Ta) -> BYTE-PARITY control.
      - zon    : the 8 above + a Z-reflection (dim -3) of each -> primary probe.
      - xyd4   : uniform 8-view D4 = replace the duplicated anti-transpose Ta with the missing
                 anti-diagonal reflection Aad -> in-group geometrically-motivated companion.
  * Two DIRECT DeepCenter veto consumers read the heatmap: gap1 (close_single_frame_gaps) and
    safe-division. recover_strict_gap2 reads NO heatmap (downstream stage). The per-arm replay
    re-runs the UNCHANGED filter_output_graph from a freshly loaded graph per movie, which starts
    BEFORE gap1 -> the treatment reaches BOTH consumers (proposal replay-boundary requirement).
  * View-level cache: each unique input transform's raw model output model(T(x)) is computed ONCE
    per (dataset,t,view), stored LOSSLESSLY on disk (float32 .npy) + a bounded RAM LRU, retained
    until ALL arms finish (arms run sequentially). Each arm accumulates its own ordered view list
    IN TORCH on-device, in the parent's exact left-to-right order (byte-parity requires this;
    numpy re-summation would not bit-match). ~17 distinct forwards/frame union across arms.
  * xyonly's submission SHA MUST equal the parent's. It is computed FRESH through the SAME cached
    accumulation path the experimental arms use (proving that path). On mismatch the run STOPS
    before trusting zon/xyd4 and writes fail-closed metrics.json (gate False) -- no crash.
  * Mechanism-active check (NOT the old delta==0 raise): zon/xyd4 heatmaps must differ from
    xyonly on >=1 scored frame; a verified ZERO response is a recorded mechanism NULL (blocks a
    duplicate submission), not an implementation failure.
  * Budget: whole-run 2.0h SIGALRM watchdog (top-injected). Arms run xyonly -> zon -> xyd4; each
    arm's outputs are written as an atomic completed-arm artifact; an arm is NOT started unless
    remaining budget >= measured_running_rate * est_cost + a 20-min finalization reserve. A
    partial run (e.g. xyd4 not started) is a VALID recorded result, unlike a mid-arm kill.

References parent-notebook globals by name (present after the parent cell runs).
"""

# ---------------------------------------------------------------------------
# Static configuration (frozen; mirrored in the experiment config/proposal v5)
# ---------------------------------------------------------------------------
EXP061_PARENT_SUBMISSION_SHA256 = (
    "d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60"
)
EXP061_RESOLVED_OVERRIDES = {"MOTION_RELINK_TIGHT_UM": 5.5}  # ppsweep_selected.json
EXP061_CONTROL_ARM = "xyonly"
EXP061_ARMS = ("xyonly", "zon", "xyd4")   # pre-registered; xyonly first (parity control)
EXP061_VALIDATION_PROTOCOL = "exp061_zon_only_deployment_v4"
EXP061_EXPERIMENT_ID = "exp_061_zon_lb_submission_repair_v4"
EXP061_HARD_STOP_SECONDS = 2.0 * 3600.0
EXP061_FINALIZATION_RESERVE_SECONDS = 20.0 * 60.0   # numeric reserve (proposal §7)
EXP061_RAM_LRU_MAX_VIEWS = 64                        # bounded RAM cache of decoded view logits
EXP061_TRANSFORM_IMPL_VERSION = "v1"                 # bound into the view-cache key (admission #1)
# The parent writes its verified checkpoint hashes here; we REQUIRE the deepcenter hash for the
# view-cache provenance instead of falling back to a placeholder (admission #1).
EXP061_RUNTIME_INTEGRITY_FILE = "bidirectional_production_runtime_integrity.json"
EXP061_HEATMAP_SAMPLE_FRAMES = 8                     # keep a few full heatmaps per arm for |delta| stats
# The parent's adaptive PP-sweep (validator) is DISABLED for this run via a strippable
# `BIOHUB_VALIDATOR_ENABLE=0` injection (admission #6): the xyonly replay pins tight55 itself, so
# the sweep is pure overhead here. We REQUIRE it to be off so the feasibility accounting holds.
EXP061_REQUIRE_VALIDATOR_DISABLED = ("BIOHUB_VALIDATOR_ENABLE", "0")

# The parent's DeepCenter TTA env flag MUST be ON for all arms (the parent 0.947 pipeline uses it;
# xyonly reproduces the parent exactly). The arms differ only via _EXP061_ACTIVE_ARM below.
EXP061_REQUIRE_PARENT_TTA_ENV = ("BIOHUB_DEEPCENTER_TTA", "1")

# Effective-config completeness (same knob set as exp_060; every knob must be a live global so we
# prove nothing but the TTA set differs across arms on the ACTUAL pipeline).
EXP061_CONFIG_KEYS = (
    "ILP_EDGE_WEIGHT", "ILP_APPEARANCE_WEIGHT", "ILP_DISAPPEARANCE_WEIGHT", "ILP_DIVISION_WEIGHT",
    "OUTPUT_EDGE_MAX_UM", "OUTPUT_ENFORCE_NEXT_FRAME", "OUTPUT_SINGLE_PARENT_REPAIR",
    "OUTPUT_SINGLE_CHILD_REPAIR", "OUTPUT_PRUNE_ISOLATED", "OUTPUT_MOTION_RELINK",
    "MOTION_RELINK_TIGHT_UM", "MOTION_RELINK_RELAXED_UM", "MOTION_RELINK_VELOCITY_WEIGHT",
    "MOTION_RELINK_LEARNED_BONUS", "MOTION_RELINK_MAX_FRAME_NODES",
    "OUTPUT_DIVISION_GEOMETRY_FILTER", "DIV_PARENT_MAX_UM", "DIV_SISTER_MAX_UM",
    "DIV_DROP_TO_SINGLE_IF_BAD", "OUTPUT_GAP_CLOSE", "GAP_CLOSE_MAX_GAP", "GAP_CLOSE_UM",
    "GAP_DENSITY_ADAPTIVE", "GAP_DENSITY_REFERENCE_UM", "GAP_DENSITY_GAIN",
    "GAP_DENSITY_MAX_STEP_DELTA_UM", "GAP_DENSITY_NEIGHBORS", "GAP_CLOSE_REUSE_EXISTING",
    "GAP_CLOSE_REUSE_UM", "GAP_CLOSE_MAX_ADDED_FRAC", "GAP_CLOSE_MAX_ADDED_ABS",
    "GAP_REFINE_SYNTHETIC", "GAP_REFINE_WIN_Z", "GAP_REFINE_WIN_YX", "GAP_REFINE_MAX_SHIFT_UM",
    "OUTPUT_FILTER_SHORT_TRACKS", "OUTPUT_MIN_TRACK_LEN", "OUTPUT_KEEP_DIVISION_COMPONENTS",
    "OUTPUT_LINEFIT_SMOOTH", "OUTPUT_LINEFIT_WEIGHT", "OUTPUT_LINEFIT_WINDOW",
    "OUTPUT_GAP2_RECOVERY", "GAP2_MAX_TOTAL_UM", "GAP2_MAX_STEP_UM", "GAP2_MAX_LINKS_FRAC",
    "GAP2_MAX_LINKS_ABS", "GAP2_REQUIRE_CONTEXT", "GAP2_FRAME_FRAC_CAP", "OUTPUT_SAFE_DIVISIONS",
    "SAFE_DIV_MAX_UM", "SAFE_DIV_SISTER_MAX_UM", "SAFE_DIV_SISTER_SYMMETRY_TAU",
    "SAFE_DIV_EXISTING_CHILD_MAX_UM", "SAFE_DIV_FRAME_FRAC_CAP", "SAFE_DIV_GLOBAL_FRAC_CAP",
    "SAFE_DIV_DIVERGE_UM", "SAFE_DIV_REQUIRE_DIVERGENCE", "SAFE_DIV_REQUIRE_MUTUAL_NN",
    "USE_DEEPCENTER_VETO", "REQUIRE_DEEPCENTER_VETO", "DEEPCENTER_GAP_VETO",
    "DEEPCENTER_SAFE_DIV_VETO", "DEEPCENTER_GAP_THRESHOLD", "DEEPCENTER_EXPECTED_EPOCH",
    "DEEPCENTER_GAP_CONFIRM_MIN_SPAN_UM", "DEEPCENTER_SAFE_DIV_THRESHOLD",
    "DEEPCENTER_SCORE_WIN_Z", "DEEPCENTER_SCORE_WIN_YX",
)

# ---------------------------------------------------------------------------
# INDEPENDENTLY-DERIVED frozen parent config (admission v3 #1; CORRECTED admission v4 #1).
#
# These are the repro_059 (0.947) post-processing knob values as the 0.947 pipeline EFFECTIVELY
# resolves them. CRITICAL (v4 #1 bug fix): the parent notebook SETS `os.environ['BIOHUB_KEY']='V'`
# overrides in its env-setup block BEFORE the `KEY = float/int(os.environ.get('BIOHUB_KEY',
# 'DEFAULT'))` / `... != '0'` declarations, so the EFFECTIVE value is the env override when present,
# and only the declaration fallback for knobs the env never sets. The earlier table used the bare
# declaration fallbacks -> it disagreed with the real pipeline on 18 knobs, which would have
# fail-closed the real GPU run. This table now stores, per key, `env_override if set else
# declaration_fallback` (see scripts/test_exp061_behavioral.py::test_N, which re-parses BOTH the
# env-setup block AND the declarations and recomputes the effective value, so this table cannot
# silently drift from the parent). At runtime every started arm's live config is asserted EQUAL to
# EXP061_FROZEN_PARENT_CONFIG key-by-key (fail-closed), which is this table with the documented
# tight55 ppsweep override applied -- so the gate verifies the STARTING values equal an
# independently frozen reference, not merely that they stay constant across arms.
# ("# env" = set in the parent env-setup block; "# default" = never set in env, declaration fallback.)
EXP061_PARENT_BASE_DEFAULTS = {
    "ILP_EDGE_WEIGHT": -1.0, "ILP_APPEARANCE_WEIGHT": 0.0, "ILP_DISAPPEARANCE_WEIGHT": 2.0,  # env
    "ILP_DIVISION_WEIGHT": 1.2, "OUTPUT_EDGE_MAX_UM": 14.0, "OUTPUT_ENFORCE_NEXT_FRAME": True,  # env
    "OUTPUT_SINGLE_PARENT_REPAIR": True, "OUTPUT_SINGLE_CHILD_REPAIR": False,
    "OUTPUT_PRUNE_ISOLATED": True, "OUTPUT_MOTION_RELINK": True, "MOTION_RELINK_TIGHT_UM": 6.0,
    "MOTION_RELINK_RELAXED_UM": 10.0, "MOTION_RELINK_VELOCITY_WEIGHT": 0.5,
    "MOTION_RELINK_LEARNED_BONUS": 1.0, "MOTION_RELINK_MAX_FRAME_NODES": 2600,  # env: bonus 1.0
    "OUTPUT_DIVISION_GEOMETRY_FILTER": False, "DIV_PARENT_MAX_UM": 10.5, "DIV_SISTER_MAX_UM": 8.0,
    "DIV_DROP_TO_SINGLE_IF_BAD": True, "OUTPUT_GAP_CLOSE": True, "GAP_CLOSE_MAX_GAP": 2,  # env: gap 2
    "GAP_CLOSE_UM": 5.0, "GAP_DENSITY_ADAPTIVE": True, "GAP_DENSITY_REFERENCE_UM": 6.5,  # env
    "GAP_DENSITY_GAIN": 0.04, "GAP_DENSITY_MAX_STEP_DELTA_UM": 0.125, "GAP_DENSITY_NEIGHBORS": 3,
    "GAP_CLOSE_REUSE_EXISTING": True, "GAP_CLOSE_REUSE_UM": 3.2, "GAP_CLOSE_MAX_ADDED_FRAC": 0.05,
    "GAP_CLOSE_MAX_ADDED_ABS": 2000, "GAP_REFINE_SYNTHETIC": True, "GAP_REFINE_WIN_Z": 1,
    "GAP_REFINE_WIN_YX": 3, "GAP_REFINE_MAX_SHIFT_UM": 3.2, "OUTPUT_FILTER_SHORT_TRACKS": True,
    "OUTPUT_MIN_TRACK_LEN": 6, "OUTPUT_KEEP_DIVISION_COMPONENTS": True, "OUTPUT_LINEFIT_SMOOTH": True,
    "OUTPUT_LINEFIT_WEIGHT": 0.8, "OUTPUT_LINEFIT_WINDOW": 2, "OUTPUT_GAP2_RECOVERY": True,  # env: True
    "GAP2_MAX_TOTAL_UM": 10.2, "GAP2_MAX_STEP_UM": 4.4, "GAP2_MAX_LINKS_FRAC": 0.0045,
    "GAP2_MAX_LINKS_ABS": 180, "GAP2_REQUIRE_CONTEXT": True, "GAP2_FRAME_FRAC_CAP": 0.006,
    "OUTPUT_SAFE_DIVISIONS": True, "SAFE_DIV_MAX_UM": 9.0, "SAFE_DIV_SISTER_MAX_UM": 14.0,  # env
    "SAFE_DIV_SISTER_SYMMETRY_TAU": 0.6, "SAFE_DIV_EXISTING_CHILD_MAX_UM": 10.0,  # env
    "SAFE_DIV_FRAME_FRAC_CAP": 0.0076, "SAFE_DIV_GLOBAL_FRAC_CAP": 0.00375, "SAFE_DIV_DIVERGE_UM": 2.25,  # env
    "SAFE_DIV_REQUIRE_DIVERGENCE": True, "SAFE_DIV_REQUIRE_MUTUAL_NN": True,
    "USE_DEEPCENTER_VETO": True, "REQUIRE_DEEPCENTER_VETO": True, "DEEPCENTER_GAP_VETO": True,
    "DEEPCENTER_SAFE_DIV_VETO": True, "DEEPCENTER_GAP_THRESHOLD": 0.25, "DEEPCENTER_EXPECTED_EPOCH": 2,  # env
    "DEEPCENTER_GAP_CONFIRM_MIN_SPAN_UM": 8.5, "DEEPCENTER_SAFE_DIV_THRESHOLD": 0.20,  # env
    "DEEPCENTER_SCORE_WIN_Z": 1, "DEEPCENTER_SCORE_WIN_YX": 2,
}
# The resolved 0.947 config = the parent defaults with ONLY the documented tight55 override. Built
# from the two independent tables so the override lives in exactly one place.
EXP061_FROZEN_PARENT_CONFIG = {**EXP061_PARENT_BASE_DEFAULTS, **EXP061_RESOLVED_OVERRIDES}

# ---------------------------------------------------------------------------
# Per-STAGE filter_output_graph counters captured per dataset (admission v3 #2): the parent's own
# `stats` dict already attributes node/edge additions and DeepCenter bypasses to the gap1, gap2 and
# safe-division stages. Capturing them per arm lets us report gap1/gap2-SPECIFIC final edge deltas
# and the count of DeepCenter-BYPASSED gap candidates (the ones the veto never scored), which a
# single global edge delta cannot. Missing keys default to 0 (the parent only emits a counter the
# first time it increments).
EXP061_STAGE_STAT_KEYS = {
    "gap1": ("gap_candidates", "gap_pairs_selected", "gap_added_edges", "gap_added_nodes",
             "gap_inserted_synthetic", "gap_reused_existing",
             "deepcenter_gap_bypassed_strong_motion", "deepcenter_gap_bypassed_observed_node"),
    "gap2": ("gap2_candidates", "gap2_pairs_selected", "gap2_added_edges", "gap2_added_nodes"),
    "safe_div": ("safe_division_candidates", "safe_division_geometric_candidates",
                 "safe_divisions_added"),
}

# ---------------------------------------------------------------------------
# Per-arm TTA view specification.
#
# A "view" is an ordered forward transform T applied to the input tensor; the raw model output
# model(T(x)) is cached; at accumulation the inverse T^-1 is applied (in torch) and summed. All
# XY transforms act on dims (-2,-1); Z acts on dim -3. `square_only` views run only when XY is
# square (matching the parent). Weight is 1 for every executed view (mean over executed views).
#
# View ids and their (forward, inverse) torch expressions are applied by _apply_forward/_apply_inv
# below; the executable spec + coordinate-mapping assertions live in scripts/test_exp061_behavioral.
# Order is the parent's exact order so xyonly reproduces the parent byte-for-byte.
# ---------------------------------------------------------------------------
# ("view_id", square_only)
_XY_BASE = (("V0", False), ("Vx", False), ("Vy", False), ("Vxy", False),
            ("R1", True), ("R3", True), ("Td", True))
EXP061_ARM_VIEWS = {
    # parent order: V0,Vx,Vy,Vxy,R1,R3,Td,Ta  (Ta = anti-transpose, distinct forward, keeps the
    # parent's duplicate slot at weight 1)
    "xyonly": _XY_BASE + (("Ta", True),),
    # xyonly's 8 views + the Z-reflection of each (square_only inherited from the XY part; Z of a
    # flip is always valid, Z of a rot/transpose needs square)
    "zon": _XY_BASE + (("Ta", True),)
            + (("ZV0", False), ("ZVx", False), ("ZVy", False), ("ZVxy", False),
               ("ZR1", True), ("ZR3", True), ("ZTd", True), ("ZTa", True)),
    # uniform D4: replace Ta with the anti-diagonal reflection Aad
    "xyd4": _XY_BASE + (("Aad", True),),
}

# Active-arm selector consumed by the installed heatmap function.
_EXP061_ACTIVE_ARM = {"name": None}


def _apply_forward(view_id, tensor, torch_mod):
    """Forward transform T(view_id) applied to the input tensor (torch), matching proposal §3."""
    Z = lambda x: x.flip((-3,))
    if view_id == "V0":  return tensor
    if view_id == "Vx":  return tensor.flip((-1,))
    if view_id == "Vy":  return tensor.flip((-2,))
    if view_id == "Vxy": return tensor.flip((-2, -1))
    if view_id == "R1":  return torch_mod.rot90(tensor, 1, dims=(-2, -1))
    if view_id == "R3":  return torch_mod.rot90(tensor, 3, dims=(-2, -1))
    if view_id == "Td":  return tensor.transpose(-1, -2)
    if view_id == "Ta":  return torch_mod.rot90(tensor, 1, dims=(-2, -1)).transpose(-1, -2)
    if view_id == "Aad": return tensor.transpose(-1, -2).flip((-2, -1))
    if view_id.startswith("Z"):
        return _apply_forward(view_id[1:], Z(tensor), torch_mod)
    raise KeyError(f"exp061: unknown view forward {view_id}")


def _apply_inverse(view_id, y, torch_mod):
    """Inverse transform T^-1(view_id) applied to a model output y (torch), matching proposal §3."""
    Zi = lambda x: x.flip((-3,))
    if view_id == "V0":  return y
    if view_id == "Vx":  return y.flip((-1,))
    if view_id == "Vy":  return y.flip((-2,))
    if view_id == "Vxy": return y.flip((-2, -1))
    if view_id == "R1":  return torch_mod.rot90(y, -1, dims=(-2, -1))
    if view_id == "R3":  return torch_mod.rot90(y, -3, dims=(-2, -1))
    if view_id == "Td":  return y.transpose(-1, -2)
    if view_id == "Ta":  return torch_mod.rot90(y.transpose(-1, -2), -1, dims=(-2, -1))
    if view_id == "Aad": return y.transpose(-1, -2).flip((-2, -1))  # self-inverse (F∘T)
    if view_id.startswith("Z"):
        return Zi(_apply_inverse(view_id[1:], y, torch_mod))
    raise KeyError(f"exp061: unknown view inverse {view_id}")


def exp061_arm_signature(arm):
    """Canonical, order-sensitive signature of an arm's TTA set (proposal §4.1)."""
    import hashlib
    views = EXP061_ARM_VIEWS[arm]
    payload = "exp061-v1|" + arm + "|" + ",".join(f"{v}:{int(sq)}" for v, sq in views)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def exp061_view_key(run_provenance, dataset, t, view_id, image_hash):
    """Module-level view-cache key (admission #1): provenance = impl-version + verified checkpoint
    hash (carried in run_provenance); input provenance = image content hash. The key is NOT a
    function of the arm -- shared views are reused across arms, but a different provenance,
    dataset/frame, view, or input image content yields a different key (negative-test-covered)."""
    import hashlib
    payload = f"{run_provenance}|{dataset}|{int(t)}|{view_id}|img={image_hash}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _exp061_process_start_seconds():
    """(process_start_epoch_seconds, reliable); mirrors exp_060 -- unreliable timing fails closed."""
    import os
    import time
    try:
        import psutil  # noqa
        return float(psutil.Process(os.getpid()).create_time()), True
    except Exception:
        pass
    try:
        with open("/proc/self/stat") as fh:
            starttime_ticks = float(fh.read().split()[21])
        hz = os.sysconf("SC_CLK_TCK")
        with open("/proc/stat") as fh:
            for line in fh:
                if line.startswith("btime"):
                    return float(line.split()[1]) + starttime_ticks / hz, True
    except Exception:
        pass
    return time.time(), False


def run_exp061_zon_deployment(g: dict) -> dict:
    """Run only the frozen zon arm in the notebook namespace `g`."""
    import os
    import csv
    import json
    import time
    import math
    import hashlib
    from pathlib import Path
    from collections import Counter, OrderedDict

    import numpy as np

    if "_EXP061_RUN_START" in g:
        proc_start, timing_reliable = float(g["_EXP061_RUN_START"]), True
    else:
        proc_start, timing_reliable = _exp061_process_start_seconds()
    whole_run_watchdog_armed = bool(g.get("_EXP061_WATCHDOG_ARMED", False))

    def _elapsed():
        return time.time() - proc_start

    def _remaining():
        return EXP061_HARD_STOP_SECONDS - _elapsed()

    def _disarm_watchdog():
        try:
            import signal
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)
        except Exception:
            pass

    # -- prerequisites (fail closed if absent) ---------------------------------
    required = [
        "filter_output_graph", "graph_from_geff", "DEEPCENTER_VETO_DETECTOR",
        "test_stems", "CSV_COLUMNS", "REPO_DIR", "METHOD", "WORKING_DIR",
        "deepcenter_heatmap_for_frame", "deepcenter_accept_repair_point", "deepcenter_score_point",
        "read_test_frame", "_dc_pool_frame_xy", "_dc_normalize_dynamic_range", "_dc_cache_trim",
        "DEEPCENTER_SAFE_DIV_THRESHOLD", "MOTION_RELINK_TIGHT_UM",
    ]
    missing = [name for name in required if name not in g]
    if missing:
        raise RuntimeError(f"exp061: missing parent globals: {missing}")

    out_dir = Path(g["WORKING_DIR"]) / "exp061"
    out_dir.mkdir(parents=True, exist_ok=True)
    view_dir = Path(g["WORKING_DIR"]) / "exp061_viewcache"
    view_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = Path(g["WORKING_DIR"]) / "metrics.json"
    experiment_id = str(g.get("EXPERIMENT_ID", EXP061_EXPERIMENT_ID) or EXP061_EXPERIMENT_ID)

    # Parent DeepCenter TTA env must be ON (xyonly == parent path); the adaptive PP-sweep
    # (validator) must be OFF (admission #6 -- feasibility accounting requires it).
    _tta_env, _tta_val = EXP061_REQUIRE_PARENT_TTA_ENV
    parent_tta_on = os.environ.get(_tta_env, "0") == _tta_val
    _val_env, _val_val = EXP061_REQUIRE_VALIDATOR_DISABLED
    validator_disabled = os.environ.get(_val_env, "1") == _val_val

    _CONFIG_ENV_KEYS = ("BIOHUB_DEEPCENTER_TTA", "BIOHUB_SECONDARY_EDGE_FEATURE_TTA",
                        "BIOHUB_SECONDARY_EDGE_FEATURE_TTA_WEIGHT", "BIOHUB_EDGE_FEATURE_TTA",
                        "BIOHUB_VALIDATOR_ENABLE")

    def _capture_effective_config():
        cfg = {k: g[k] for k in EXP061_CONFIG_KEYS if k in g}
        for _envk in _CONFIG_ENV_KEYS:
            cfg["env:" + _envk] = os.environ.get(_envk)
        return cfg

    # -- pin resolved config (base env + tight55) ------------------------------
    for key, value in EXP061_RESOLVED_OVERRIDES.items():
        if key not in g:
            raise RuntimeError(f"exp061: cannot pin unknown global {key}")
        g[key] = value

    # INDEPENDENT frozen-parent reference (admission v3 #1): the parent's resolved 0.947 config is
    # NOT captured from this run. It is EXP061_FROZEN_PARENT_CONFIG -- the parent notebook's own knob
    # defaults (transcribed once, guarded by scripts/test_exp061_behavioral.py against the parent
    # notebook) with the documented tight55 override. Every started arm's LIVE knob config is
    # asserted EQUAL to this independent reference, key-by-key, fail-closed -- so the gate verifies
    # the STARTING values equal an independently frozen config, not merely that they stay constant
    # across arms. `live_parent_config_snapshot` (with env keys) is recorded for telemetry only.
    def _knob_config(cfg):
        # the knob subset (drop the informational `env:` entries) for the frozen-reference compare
        return {k: v for k, v in cfg.items() if not str(k).startswith("env:")}

    expected_parent_config = dict(EXP061_FROZEN_PARENT_CONFIG)   # independent reference (v3 #1)
    live_parent_config_snapshot = _capture_effective_config()   # telemetry-only (incl env keys)
    # up-front fail-closed check: the live pinned config must already equal the frozen reference
    # before ANY arm runs (missing/extra/diff knob -> gate fails, no wasted GPU on a mis-pinned run)
    live_knobs = _knob_config(live_parent_config_snapshot)
    live_config_equals_frozen_parent = (live_knobs == expected_parent_config)
    if not live_config_equals_frozen_parent:
        _diff = {k: (expected_parent_config.get(k), live_knobs.get(k))
                 for k in set(expected_parent_config) | set(live_knobs)
                 if expected_parent_config.get(k) != live_knobs.get(k)}
        print(f"[exp061] LIVE CONFIG != FROZEN PARENT (gate fails closed): {_diff}", flush=True)

    # checkpoint provenance (admission #1): REQUIRE the parent's verified deepcenter checkpoint
    # hash from its runtime-integrity report -- no silent placeholder fallback. If it cannot be
    # established, checkpoint_provenance_verified is False and the gate fails closed.
    verified_ckpt_sha = None
    integ_path = Path(g["WORKING_DIR"]) / EXP061_RUNTIME_INTEGRITY_FILE
    if integ_path.exists():
        try:
            verified_ckpt_sha = (json.loads(integ_path.read_text())
                                 .get("checkpoint_sha256", {}).get("deepcenter"))
        except Exception:
            verified_ckpt_sha = None
    checkpoint_provenance_verified = bool(verified_ckpt_sha)
    run_provenance = (f"exp061|impl={EXP061_TRANSFORM_IMPL_VERSION}|"
                      f"dcckpt={verified_ckpt_sha or 'MISSING'}")

    # ---------------------------------------------------------------------
    # View-level cache: raw model(T(x)) logits, lossless float32 on disk + bounded RAM LRU,
    # keyed (dataset,t,view,provenance). Retained for the whole run (arms are sequential).
    # ---------------------------------------------------------------------
    _ram_lru = OrderedDict()
    _view_sha = {}   # view-key -> sha256 of the stored logits (integrity validation, admission #1)
    view_stats = {"forward_calls": 0, "disk_hits": 0, "ram_hits": 0, "distinct_frames": set(),
                  "integrity_failures": 0, "nonfinite_view_logits": 0}
    # per-arm heatmap identity for the observed-response check + nonfinite detection at the tensor
    # level. EXECUTION validity (admission v2 #3) is tracked SEPARATELY from the observed response:
    # a correct arm can legitimately produce an identical heatmap (reflection-equivariant model) --
    # that is a valid NULL, not a failure. Execution evidence = the intended views actually ran.
    arm_heatmap_sha = {}      # (arm, dataset, t) -> sha256(heatmap bytes)  [observed response]
    arm_heatmap_sample = {}   # arm -> {(dataset,t): np.ndarray} for a few frames (|delta| stats)
    arm_views_seen = {"zon": set()}
    arm_frame_views_seen = {}
    arm_frame_square = {}
    nonfinite_heatmap_events = []   # (arm, dataset, t) with a non-finite heatmap/logits

    def _view_key(dataset, t, view_id, image_hash):
        return exp061_view_key(run_provenance, dataset, t, view_id, image_hash)

    def _digest(arr):
        return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()

    def _compute_and_store(key, view_id, tensor, model, torch_mod):
        """Freshly compute model(T_view(tensor)); persist the array + a sidecar digest."""
        transformed = _apply_forward(view_id, tensor, torch_mod)
        out = model(transformed)
        arr = out.detach().to("cpu").numpy().astype(np.float32, copy=False)
        dig = _digest(arr)
        _view_sha[key] = dig
        if not np.isfinite(arr).all():
            view_stats["nonfinite_view_logits"] += 1
        np.save(view_dir / f"{key}.npy", arr)             # lossless persist; retained until run end
        (view_dir / f"{key}.sha256").write_text(dig)      # persisted expected digest (admission v2 #5)
        view_stats["forward_calls"] += 1
        return arr

    def _get_view_logits(dataset, t, view_id, image_hash, tensor, model, torch_mod, device):
        """Return model(T_view(tensor)) as a torch tensor on `device`, cached at view level.

        Raw model output stored losslessly (float32 .npy + a .sha256 sidecar) keyed by
        (impl_version, verified_ckpt_sha, dataset, t, view, image_hash). A cached entry is
        ACCEPTED only if its content digest matches the persisted/expected digest AND it is finite;
        otherwise it is REJECTED and recomputed BEFORE use (admission v2 #5)."""
        key = _view_key(dataset, t, view_id, image_hash)

        def _valid(arr, expected):
            return (arr is not None and expected is not None
                    and _digest(arr) == expected and bool(np.isfinite(arr).all()))

        arr = _ram_lru.get(key)
        if arr is not None:
            view_stats["ram_hits"] += 1
            if _valid(arr, _view_sha.get(key)):
                _ram_lru.move_to_end(key)
            else:                                          # reject-before-use -> recompute
                view_stats["integrity_failures"] += 1
                _ram_lru.pop(key, None)
                arr = _compute_and_store(key, view_id, tensor, model, torch_mod)
        else:
            fpath = view_dir / f"{key}.npy"
            spath = view_dir / f"{key}.sha256"
            if fpath.exists():
                view_stats["disk_hits"] += 1
                disk_arr = None
                try:
                    disk_arr = np.load(fpath)
                except Exception:
                    disk_arr = None
                expected = _view_sha.get(key)
                if expected is None and spath.exists():
                    try:
                        expected = spath.read_text().strip()
                    except Exception:
                        expected = None
                if _valid(disk_arr, expected):
                    arr = disk_arr
                    _view_sha[key] = expected
                else:                                      # missing/mismatched digest -> recompute
                    view_stats["integrity_failures"] += 1
                    arr = _compute_and_store(key, view_id, tensor, model, torch_mod)
            else:
                arr = _compute_and_store(key, view_id, tensor, model, torch_mod)
        _ram_lru[key] = arr
        _ram_lru.move_to_end(key)
        while len(_ram_lru) > EXP061_RAM_LRU_MAX_VIEWS:
            _ram_lru.popitem(last=False)
        view_stats["distinct_frames"].add((dataset, int(t)))
        return torch_mod.from_numpy(np.array(arr, copy=False)).to(device=device)

    _orig_heatmap_for_frame = g["deepcenter_heatmap_for_frame"]

    def _exp061_heatmap_for_frame(dataset, t, detector_bundle, frame_cache, heatmap_cache):
        """Per-arm heatmap via the view cache. For xyonly the accumulation is the parent's exact
        left-to-right order/ops -> byte-identical heatmap (given a deterministic model). The
        per-arm heatmap_cache (installed fresh per arm) is keyed (dataset,t)."""
        if detector_bundle is None:
            return None
        key = (dataset, int(t))
        cached = heatmap_cache.get(key)
        if cached is not None:
            return cached
        arm = _EXP061_ACTIVE_ARM["name"]
        model = detector_bundle["model"]
        cfg = detector_bundle["cfg"]
        device = detector_bundle["device"]
        torch_mod = detector_bundle["torch"]
        pool_factor = int(getattr(cfg, "pool_factor", 4))
        volume = g["read_test_frame"](dataset, int(t), frame_cache)
        pooled = g["_dc_pool_frame_xy"](volume, pool_factor)
        image = g["_dc_normalize_dynamic_range"](pooled, cfg)
        # input provenance: content hash of the (pooled, normalized) model input (admission #1)
        image_hash = hashlib.sha256(
            np.ascontiguousarray(np.asarray(image, dtype=np.float32)).tobytes()).hexdigest()
        with torch_mod.no_grad():
            tensor = torch_mod.from_numpy(image[None, None, ...]).to(device=device, dtype=torch_mod.float32)
            square = tensor.shape[-1] == tensor.shape[-2]
            views = EXP061_ARM_VIEWS[arm]
            frame_key = (arm, dataset, int(t))
            arm_frame_views_seen[frame_key] = []
            arm_frame_square[frame_key] = bool(square)
            acc = None
            nv = 0
            for view_id, square_only in views:
                if square_only and not square:
                    continue
                raw = _get_view_logits(dataset, t, view_id, image_hash, tensor, model, torch_mod, device)
                contrib = _apply_inverse(view_id, raw, torch_mod)
                acc = contrib.clone() if acc is None else acc + contrib
                nv += 1
                arm_views_seen.setdefault(arm, set()).add(view_id)   # execution evidence (#3)
                arm_frame_views_seen[frame_key].append(view_id)
            logits = acc / nv
            logits_finite = bool(torch_mod.isfinite(logits).all().item())
            heatmap = torch_mod.sigmoid(logits)[0, 0].detach().cpu().numpy().astype(np.float32, copy=False)
        # tensor-level nonfinite detection (admission #3): catch invalid heatmaps BEFORE any scorer
        # nulls the score into a "missing" bypass.
        if (not logits_finite) or (not np.isfinite(heatmap).all()):
            nonfinite_heatmap_events.append({"arm": arm, "dataset": dataset, "t": int(t)})
        # record heatmap identity for the REAL mechanism-active check (admission #2)
        arm_heatmap_sha[(arm, dataset, int(t))] = hashlib.sha256(
            np.ascontiguousarray(heatmap).tobytes()).hexdigest()
        samp = arm_heatmap_sample.setdefault(arm, {})
        if len(samp) < EXP061_HEATMAP_SAMPLE_FRAMES:
            samp[(dataset, int(t))] = heatmap
        heatmap_cache[key] = heatmap
        # preserve the parent's bounded per-movie heatmap retention (admission v2 #4 memory): the
        # parent calls _dc_cache_trim(heatmap_cache) here, else complete heatmaps accumulate.
        if "_dc_cache_trim" in g:
            g["_dc_cache_trim"](heatmap_cache)
        return heatmap

    # ---------------------------------------------------------------------
    # Central veto telemetry: wrap deepcenter_accept_repair_point (called at BOTH gap1 and
    # safe-div). Records (arm, dataset, t, kind, score, accept). Node IDs come from the strippable
    # call-site loggers injected at gap1 + safe-div. Heatmap diagnostics come from the arm store.
    # ---------------------------------------------------------------------
    _orig_accept = g["deepcenter_accept_repair_point"]
    veto_log = []          # one combined record per REAL veto call (ids + score + accept)
    _pending_ids = {"kind": None, "ids": None}   # stashed by the injected call-site logger (#4)

    def _accept_wrapper(dataset, t, point, detector_bundle, frame_cache, heatmap_cache,
                        stats, kind, threshold):
        arm = _EXP061_ACTIVE_ARM["name"]
        # score with the REAL caches the pipeline already populated (no fresh {} re-scoring, #4)
        score = None
        status = "ok"
        try:
            score = g["deepcenter_score_point"](dataset, None if t is None else int(t), point,
                                                detector_bundle, frame_cache, heatmap_cache)
        except Exception:
            status = "error"
        if score is None:
            if status != "error":
                status = "missing"
        elif not math.isfinite(float(score)):
            status = "nonfinite"
            score = None
        else:
            score = float(score)
        accept = _orig_accept(dataset, t, point, detector_bundle, frame_cache, heatmap_cache,
                              stats, kind, threshold)
        if arm is not None:
            # consume the IDs the injected logger stashed immediately before this call (#4): one
            # combined record links identity -> score -> acceptance for the ACTUAL veto.
            ids = _pending_ids["ids"] if _pending_ids["kind"] == str(kind) else None
            _pending_ids["kind"], _pending_ids["ids"] = None, None
            veto_log.append({
                "arm": arm, "dataset": dataset, "t": None if t is None else int(t),
                "kind": str(kind),
                "ids": None if ids is None else {k: (None if v is None else int(v)) for k, v in ids.items()},
                "deepcenter_score": score, "score_status": status, "accept": bool(accept),
                "survived_final": None,   # filled by a post-hoc join for safe_div candidates
            })
        return accept

    def _make_candidate_logger():
        # cheap: just stash the in-scope IDs for the veto call that immediately follows (#4).
        def _log(kind, dataset, t, ids, point):
            if _EXP061_ACTIVE_ARM["name"] is None:
                return
            _pending_ids["kind"], _pending_ids["ids"] = str(kind), dict(ids)
        return _log

    # -- helpers: forks + submission writer (faithful copy of write_test_submission) -----------
    def _forks_with_ids(edges):
        out = {}
        for e in edges:
            out.setdefault(int(e["source_id"]), []).append(int(e["target_id"]))
        return {s: sorted(ch) for s, ch in out.items() if len(ch) >= 2}

    # MEASURED per-dataset wall costs (admission v3 #4): the arm writer times every dataset and
    # gates on the measured running rate, so even the CONTROL arm's continuation is governed by
    # real measurements (not a zero-cost assumption). Keyed (arm, dataset).
    dataset_costs = {}

    def _view_cache_capacity():
        # measured on-disk view-cache capacity + I/O (admission v3 #4 "cache capacity/I/O")
        files = 0
        nbytes = 0
        try:
            for p in view_dir.glob("*.npy"):
                files += 1
                nbytes += p.stat().st_size
        except Exception:
            pass
        return {"disk_view_files": files, "disk_view_bytes": nbytes,
                "ram_lru_entries": len(_ram_lru), "ram_lru_max": EXP061_RAM_LRU_MAX_VIEWS,
                "forward_calls": view_stats["forward_calls"], "disk_hits": view_stats["disk_hits"],
                "ram_hits": view_stats["ram_hits"]}

    def _write_arm_submission(arm, out_path):
        _EXP061_ACTIVE_ARM["name"] = arm
        geffs = sorted((Path(g["REPO_DIR"]) / "predictions").glob(f"*/{g['METHOD']}/split_0/*.geff"))
        found = [p.stem for p in geffs]
        expected = set(g["test_stems"])
        if (len(geffs) != len(g["test_stems"]) or
                sorted(s for s, c in Counter(found).items() if c > 1) or
                sorted(expected - set(found)) or sorted(set(found) - expected)):
            raise RuntimeError(f"exp061 arm {arm}: unexpected prediction graphs")

        csv_columns = g["CSV_COLUMNS"]
        row_id = 0
        total_nodes = total_edges = 0
        per_dataset = {}
        n_ds = len(geffs)
        budget_aborted = False
        abort_note = ""
        # write to a temp path then os.replace -> the final arm CSV is created atomically
        # (admission #4); an interrupted arm never leaves a half-written final file.
        tmp_path = Path(str(out_path) + ".tmp")
        with open(tmp_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_columns)
            writer.writeheader()
            for ds_i, geff_path in enumerate(geffs):
                ds_t0 = time.time()
                dataset = geff_path.stem
                graph = g["graph_from_geff"](geff_path)
                nodes_by_id = {}
                for row in graph.node_attrs().iter_rows(named=True):
                    nid = int(row["node_id"])
                    nodes_by_id[nid] = {"node_id": nid, "t": int(row["t"]),
                                        "z": float(row["z"]), "y": float(row["y"]), "x": float(row["x"])}
                raw_edges = []
                for row in graph.edge_attrs().iter_rows(named=True):
                    ep = row.get("edge_prob") if hasattr(row, "get") else None
                    raw_edges.append({"source_id": int(row["source_id"]),
                                      "target_id": int(row["target_id"]),
                                      "edge_prob": None if ep is None else float(ep)})
                nodes_by_id, edges, _stats = g["filter_output_graph"](
                    nodes_by_id, raw_edges, dataset=dataset,
                    deepcenter_bundle=g["DEEPCENTER_VETO_DETECTOR"],
                )
                if not nodes_by_id:
                    raise AssertionError(f"{dataset}: post-processing removed every node")
                for nid in sorted(nodes_by_id):
                    node = nodes_by_id[nid]
                    writer.writerow({"id": row_id, "dataset": dataset, "row_type": "node",
                                     "node_id": int(node["node_id"]), "t": int(node["t"]),
                                     "z": max(0, int(round(float(node["z"])))),
                                     "y": max(0, int(round(float(node["y"])))),
                                     "x": max(0, int(round(float(node["x"])))),
                                     "source_id": -1, "target_id": -1})
                    row_id += 1
                edge_set = set()
                indeg = {}
                outdeg = {}
                for edge in edges:
                    s = int(edge["source_id"]); tt = int(edge["target_id"])
                    if s not in nodes_by_id or tt not in nodes_by_id:
                        raise AssertionError(f"{dataset}: dangling edge after filtering")
                    # parent submission audits applied to EVERY arm (admission v2 #1): consecutive
                    # frame + lineage-degree (parent asserts max_indegree<=1, max_outdegree<=2).
                    if int(nodes_by_id[tt]["t"]) != int(nodes_by_id[s]["t"]) + 1:
                        raise AssertionError(f"{dataset}: non-consecutive-frame edge {s}->{tt}")
                    indeg[tt] = indeg.get(tt, 0) + 1
                    outdeg[s] = outdeg.get(s, 0) + 1
                    writer.writerow({"id": row_id, "dataset": dataset, "row_type": "edge",
                                     "node_id": -1, "t": -1, "z": -1, "y": -1, "x": -1,
                                     "source_id": s, "target_id": tt})
                    row_id += 1
                    edge_set.add((s, tt))
                if indeg and max(indeg.values()) > 1:
                    raise AssertionError(f"{dataset}: multi-parent (max in-degree > 1)")
                if outdeg and max(outdeg.values()) > 2:
                    raise AssertionError(f"{dataset}: invalid lineage degree (out-degree > 2)")
                total_nodes += len(nodes_by_id)
                total_edges += len(edges)
                # per-stage counters (admission v3 #2): gap1/gap2/safe-div node+edge additions and
                # DeepCenter bypass counts, straight from the parent's own stats dict.
                def _stat(k):
                    try:
                        return int(_stats.get(k, 0)) if hasattr(_stats, "get") else int(_stats[k])
                    except Exception:
                        return 0
                stage_stats = {stage: {k: _stat(k) for k in keys}
                               for stage, keys in EXP061_STAGE_STAT_KEYS.items()}
                per_dataset[dataset] = {"forks": _forks_with_ids(edges), "edge_set": edge_set,
                                        "n_edges": len(edges), "n_nodes": len(nodes_by_id),
                                        "stage_stats": stage_stats}
                # MEASURED per-dataset budget gate (admission v3 #4): time this dataset, then use the
                # measured mean per-dataset cost to project the remaining datasets. If finishing the
                # arm would breach the 20-min finalization reserve, abort CLEANLY between datasets
                # (discard the tmp CSV, publish nothing) -- a valid partial result governed by the
                # measured running rate, NOT a mid-dataset kill. This governs the CONTROL arm too, so
                # no arm's continuation assumes zero cost.
                dataset_costs[(arm, dataset)] = time.time() - ds_t0
                done = ds_i + 1
                datasets_left = n_ds - done
                _arm_ds_costs = [c for (a_, _d), c in dataset_costs.items() if a_ == arm]
                mean_ds = (sum(_arm_ds_costs) / len(_arm_ds_costs)) if _arm_ds_costs else 0.0
                projected_remaining = mean_ds * datasets_left
                if datasets_left > 0 and _remaining() < projected_remaining + EXP061_FINALIZATION_RESERVE_SECONDS:
                    budget_aborted = True
                    abort_note = (f"arm {arm}: measured budget abort after {done}/{n_ds} datasets "
                                  f"(remaining {_remaining():.0f}s < projected {projected_remaining:.0f}s "
                                  f"+ reserve {EXP061_FINALIZATION_RESERVE_SECONDS:.0f}s)")
                    print(f"[exp061] {abort_note}", flush=True)
                    break
        if budget_aborted:
            # publish nothing for this arm; discard the partial tmp CSV. The caller records the arm
            # as aborted_budget (a valid partial run), leaving prior completed arms intact.
            try:
                tmp_path.unlink()
            except Exception:
                pass
            _EXP061_ACTIVE_ARM["name"] = None
            return {"budget_aborted": True, "abort_note": abort_note,
                    "datasets_done": done, "datasets_total": n_ds}
        os.replace(tmp_path, out_path)   # atomic publish of the completed arm CSV (admission #4)
        _EXP061_ACTIVE_ARM["name"] = None
        # per-arm survival annotation BEFORE the receipt (admission v2 #2/#4 + v3 #2), for BOTH
        # DeepCenter veto consumers, so a partial run preserves identity-linked survival evidence:
        #   * safe_div SURVIVES iff the parent is a final fork AND BOTH the candidate daughter AND
        #     the recorded existing daughter are its children in this arm's final graph.
        #   * gap SURVIVES iff BOTH bridge edges (left->middle, middle->right) are in the final graph
        #     (a rejected gap drops its synthetic middle, so its edges are naturally absent).
        for r in veto_log:
            if r.get("arm") != arm or not r.get("ids"):
                continue
            ds_info = per_dataset.get(r["dataset"], {})
            if r.get("kind") == "safe_div":
                forks = ds_info.get("forks", {})
                pid = r["ids"].get("parent_id")
                ccid = r["ids"].get("candidate_child_id")
                ecid = r["ids"].get("existing_child_id")
                children = forks.get(int(pid), []) if pid is not None else []
                r["survived_final"] = bool(pid is not None and ccid is not None and ecid is not None
                                           and int(pid) in forks and int(ccid) in children
                                           and int(ecid) in children)
            elif r.get("kind") == "gap":
                edge_set = ds_info.get("edge_set", set())
                lid = r["ids"].get("left_id")
                mid = r["ids"].get("middle_id")
                rid = r["ids"].get("right_id")
                r["survived_final"] = bool(lid is not None and mid is not None and rid is not None
                                           and (int(lid), int(mid)) in edge_set
                                           and (int(mid), int(rid)) in edge_set)
        effective_config = _capture_effective_config()
        sha = hashlib.sha256(Path(out_path).read_bytes()).hexdigest()
        summary = {"sha256": sha, "rows": row_id, "nodes": total_nodes, "edges": total_edges,
                   "arm_signature": exp061_arm_signature(arm),
                   "effective_config": effective_config,
                   "config_complete": all(k in g for k in EXP061_CONFIG_KEYS),
                   "missing_config_keys": [k for k in EXP061_CONFIG_KEYS if k not in g],
                   "per_dataset": per_dataset}
        # atomic per-arm completion receipt (admission #4): status + sha/counts + this arm's veto
        # rows + view set, so a partial run preserves the agreed per-arm evidence on its own.
        arm_veto_rows = [r for r in veto_log if r.get("arm") == arm]
        receipt = {"arm": arm, "status": "completed", "sha256": sha, "rows": row_id,
                   "nodes": total_nodes, "edges": total_edges,
                   "arm_signature": summary["arm_signature"],
                   "views_run": sorted(arm_views_seen.get(arm, set())),
                   "n_veto_records": len(arm_veto_rows), "per_dataset": sorted(per_dataset), "veto_rows": arm_veto_rows}
        rc_tmp = out_dir / f"receipt_{arm}.json.tmp"
        with open(rc_tmp, "w") as rf:
            json.dump(receipt, rf, allow_nan=False, indent=2)
        os.replace(rc_tmp, out_dir / f"receipt_{arm}.json")
        return summary

    def _predictions_fingerprint():
        # CONTENT sha256 of the shared prediction inputs (admission #5): size/mtime cannot detect a
        # same-size in-place edit; the geffs are read-only inputs so a content hash is the honest
        # immutability check.
        base = Path(g["REPO_DIR"]) / "predictions"
        items = []
        if base.exists():
            for p in sorted(base.rglob("*")):
                if p.is_file():
                    items.append((str(p.relative_to(base)),
                                  hashlib.sha256(p.read_bytes()).hexdigest()))
        return hashlib.sha256(repr(items).encode()).hexdigest()

    def _write_metrics(integrity_passed, checks, arm_summaries, note="", extra=None):
        runtime_seconds = max(0.0, _elapsed())
        if runtime_seconds > EXP061_HARD_STOP_SECONDS:
            checks = dict(checks, within_hard_stop_and_timing_reliable=False)
            integrity_passed = False
            note = (note + " | commit-time over budget").strip(" |")
        metrics = {
            "schema_version": 1,
            "experiment_id": experiment_id,
            "validation": {"protocol": EXP061_VALIDATION_PROTOCOL},
            "runtime_seconds": runtime_seconds,
            "reproducible": False,
            "primary_metric": 1.0 if integrity_passed else 0.0,
            "primary_metric_meaning": "zon-only deployment integrity; no quality inference",

            "exp061_zon_deployment_integrity_passed": bool(integrity_passed),
            "checks": checks,
            "note": note,
            "arm_submission_sha256": {k: v["sha256"] for k, v in arm_summaries.items()},
            "arm_final_counts": {k: {"nodes": v["nodes"], "edges": v["edges"], "rows": v["rows"]}
                                 for k, v in arm_summaries.items()},
            "arm_signatures": {k: v["arm_signature"] for k, v in arm_summaries.items()},
            "parent_submission_sha256": EXP061_PARENT_SUBMISSION_SHA256,
            "pinned_overrides": EXP061_RESOLVED_OVERRIDES,
            "runtime_seconds_source": "process_start_to_now",
        }
        if extra:
            metrics.update(extra)
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, allow_nan=False, indent=2)
        return metrics

    # -- install patches -------------------------------------------------------
    g["deepcenter_heatmap_for_frame"] = _exp061_heatmap_for_frame
    g["deepcenter_accept_repair_point"] = _accept_wrapper
    _stub_logger = g.get("_exp061_log_veto_candidate")
    g["_exp061_log_veto_candidate"] = _make_candidate_logger()

    pred_fp_before = _predictions_fingerprint()
    arm_summaries = {}
    arm_costs = {}
    arm_status = {"zon": "not_reached"}   # started/completed/skipped/failed (#4)
    stop_note = ""
    run_exception = None
    arms_started = []
    try:
        for arm in ("zon",):
            # budget-gated admission (admission v3 #4): don't START an arm unless the remaining
            # budget clears the measured prior-arm cost + the 20-min reserve. For arms 2+ `est` is
            # the largest MEASURED prior-arm cost (proposal §7 "measured running rate"). The CONTROL
            # arm (no prior arm cost) is not admitted on a zero-cost assumption: once started it is
            # governed by the MEASURED per-dataset budget gate inside _write_arm_submission, which
            # aborts cleanly between datasets if finishing would breach the reserve.
            est = max(arm_costs.values()) if arm_costs else 0.0
            need = est + EXP061_FINALIZATION_RESERVE_SECONDS
            if _remaining() < need:
                arm_status[arm] = "skipped"
                stop_note = (f"skip arm {arm}: remaining {_remaining():.0f}s < "
                             f"est {est:.0f}s + reserve {EXP061_FINALIZATION_RESERVE_SECONDS:.0f}s")
                print(f"[exp061] {stop_note}", flush=True)
                break
            arm_status[arm] = "started"
            arms_started.append(arm)   # recorded BEFORE running so an interrupted arm is visible
            t0 = time.time()
            try:
                _result = _write_arm_submission(arm, out_dir / f"submission_{arm}.csv")
            except BaseException:
                arm_status[arm] = "failed"
                raise
            arm_costs[arm] = time.time() - t0
            # measured per-dataset budget abort (admission v3 #4): a valid partial run, not a failure.
            if isinstance(_result, dict) and _result.get("budget_aborted"):
                arm_status[arm] = "aborted_budget"
                stop_note = _result.get("abort_note", f"arm {arm}: measured budget abort")
                print(f"[exp061] {stop_note}", flush=True)
                break
            arm_summaries[arm] = _result
            arm_status[arm] = "completed"
            s = arm_summaries[arm]
            print(f"[exp061] arm {arm}: sha={s['sha256'][:16]}... nodes={s['nodes']} "
                  f"edges={s['edges']} cost={arm_costs[arm]:.0f}s elapsed={_elapsed():.0f}s", flush=True)
            if arm == EXP061_CONTROL_ARM and s["sha256"] != EXP061_PARENT_SUBMISSION_SHA256:
                stop_note = "xyonly control parity mismatch - stopping before zon/xyd4"
                print(f"[exp061] {stop_note}", flush=True)
                break
    except BaseException as exc:
        run_exception = f"{type(exc).__name__}: {exc}"
        stop_note = stop_note or f"exception during probe: {run_exception}"
        print(f"[exp061] EXCEPTION: {run_exception}", flush=True)
    finally:
        g["deepcenter_heatmap_for_frame"] = _orig_heatmap_for_frame
        g["deepcenter_accept_repair_point"] = _orig_accept
        if _stub_logger is not None:
            g["_exp061_log_veto_candidate"] = _stub_logger
        _EXP061_ACTIVE_ARM["name"] = None

    # Deployment validates the zon intervention itself; cross-arm parity/mechanism
    # comparisons are development-only and deliberately absent from this scoring path.
    control = {}
    parity_ok = None
    mechanism = {}
    zon_summary = arm_summaries.get("zon", {})
    zon_views_expected_by_frame = {}
    frame_view_contract_ok = True
    for frame_key, actual_views in arm_frame_views_seen.items():
        _arm, _dataset, _t = frame_key
        _square = arm_frame_square[frame_key]
        _expected = [view_id for view_id, square_only in EXP061_ARM_VIEWS["zon"]
                     if not square_only or _square]
        zon_views_expected_by_frame[f"{_dataset}:{_t}"] = _expected
        if actual_views != _expected:
            frame_view_contract_ok = False
    zero_candidate_case = len(veto_log) == 0
    zon_view_execution_valid = bool(zon_summary) and (
        frame_view_contract_ok and
        (bool(arm_frame_views_seen) or zero_candidate_case)
    )
    started_experimental = ["zon"] if "zon" in arm_summaries else []
    all_started_execution_valid = (len(started_experimental) == 1
                                   and zon_view_execution_valid)

    pin_ok = float(g["MOTION_RELINK_TIGHT_UM"]) == 5.5
    within_deadline = timing_reliable and (_elapsed() <= EXP061_HARD_STOP_SECONDS)
    n_error = sum(1 for r in veto_log if r.get("score_status") == "error")
    n_nonfinite = sum(1 for r in veto_log if r.get("score_status") == "nonfinite")
    n_missing = sum(1 for r in veto_log if r.get("score_status") == "missing")
    veto_calls_accounted_for = all(
        r.get("score_status") == "ok" and isinstance(r.get("ids"), dict) and bool(r.get("ids"))
        for r in veto_log
    )
    shared_prediction_inputs_unchanged = (pred_fp_before == _predictions_fingerprint())

    # effective-config: every started arm's live KNOB config must equal the INDEPENDENT frozen-parent
    # reference EXP061_FROZEN_PARENT_CONFIG (admission v3 #1) -- a DIRECT comparison to a checked-in,
    # test-guarded table, not to a value captured from this run. (config_matches_control kept as an
    # extra cross-arm consistency signal; the up-front live_config_equals_frozen_parent guards the
    # pinned values BEFORE any arm runs.)
    def _cfg(label):
        return arm_summaries.get(label, {}).get("effective_config", {})
    all_config_complete = bool(arm_summaries) and all(s.get("config_complete") for s in arm_summaries.values())
    all_arm_configs_equal_frozen_parent = (bool(arm_summaries)
                                           and live_config_equals_frozen_parent
                                           and all(_knob_config(_cfg(a)) == expected_parent_config
                                                   for a in arm_summaries))

    # cross-arm deltas (full IDs) for attribution
    def _delta(base, arm):
        out = {}
        if base not in arm_summaries or arm not in arm_summaries:
            return out
        for ds in arm_summaries[base]["per_dataset"]:
            b = arm_summaries[base]["per_dataset"][ds]
            a = arm_summaries[arm]["per_dataset"][ds]
            b_forks = {(p, tuple(ch)) for p, ch in b["forks"].items()}
            a_forks = {(p, tuple(ch)) for p, ch in a["forks"].items()}
            # gap1/gap2/safe-div-SPECIFIC stage-counter deltas (admission v3 #2): attribute the edge
            # movement to the stage that produced it, which a single global edge delta cannot.
            b_stage = b.get("stage_stats", {})
            a_stage = a.get("stage_stats", {})
            stage_delta = {stage: {k: a_stage.get(stage, {}).get(k, 0) - b_stage.get(stage, {}).get(k, 0)
                                   for k in keys}
                           for stage, keys in EXP061_STAGE_STAT_KEYS.items()}
            out[ds] = {
                "d_forks": len(a_forks) - len(b_forks),
                "forks_added": [{"parent": p, "children": list(ch)} for p, ch in sorted(a_forks - b_forks)],
                "forks_removed": [{"parent": p, "children": list(ch)} for p, ch in sorted(b_forks - a_forks)],
                "d_edges": a["n_edges"] - b["n_edges"], "d_nodes": a["n_nodes"] - b["n_nodes"],
                "edges_added": [list(e) for e in sorted(a["edge_set"] - b["edge_set"])],
                "edges_removed": [list(e) for e in sorted(b["edge_set"] - a["edge_set"])],
                "stage_stat_delta": stage_delta,
            }
        return out

    view_forward_summary = {"forward_calls": view_stats["forward_calls"],
                            "disk_hits": view_stats["disk_hits"], "ram_hits": view_stats["ram_hits"],
                            "distinct_frames": len(view_stats["distinct_frames"]),
                            "integrity_failures": view_stats["integrity_failures"],
                            "nonfinite_view_logits": view_stats["nonfinite_view_logits"]}
    view_cache_integrity_ok = (view_stats["integrity_failures"] == 0
                               and view_stats["nonfinite_view_logits"] == 0)
    no_nonfinite_heatmaps = (len(nonfinite_heatmap_events) == 0)
    all_arm_configs_equal_parent = bool(all_arm_configs_equal_frozen_parent)  # direct frozen-parent compare

    # (safe_div fork-survival is annotated per-arm inside _write_arm_submission, BEFORE each
    # receipt, so a partial run preserves survival evidence -- admission v2 #2/#4.)

    # MEASURED feasibility worksheet (admission v3 #4): real per-arm AND per-dataset wall costs, the
    # per-forward rate, and measured view-cache capacity/I/O from THIS run -- so admission is gated
    # by measurement, not a pre-guessed estimate. Per-dataset costs are what the in-arm budget gate
    # uses to protect the 20-min reserve (governing the control arm from its first dataset onward).
    _ds_cost_by_arm = {}
    for (a_, d_), c_ in dataset_costs.items():
        _ds_cost_by_arm.setdefault(a_, {})[d_] = round(c_, 2)
    _all_ds_costs = list(dataset_costs.values())
    try:
        import resource
        process_peak_rss_bytes = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
    except Exception:
        process_peak_rss_bytes = None
    feasibility_worksheet = {
        "process_peak_rss_bytes": process_peak_rss_bytes,
        "measured": True,
        "arm_costs_seconds": arm_costs,
        "dataset_costs_seconds_by_arm": _ds_cost_by_arm,
        "mean_seconds_per_dataset": (round(sum(_all_ds_costs) / len(_all_ds_costs), 2)
                                     if _all_ds_costs else None),
        "max_seconds_per_dataset": (round(max(_all_ds_costs), 2) if _all_ds_costs else None),
        "distinct_deepcenter_frames": len(view_stats["distinct_frames"]),
        "view_forward_calls": view_stats["forward_calls"],
        "seconds_per_view_forward": (sum(arm_costs.values()) / max(1, view_stats["forward_calls"]))
                                    if view_stats["forward_calls"] else None,
        "view_cache_capacity_io": _view_cache_capacity(),
        "elapsed_seconds": round(_elapsed(), 1),
        "remaining_seconds": round(_remaining(), 1),
        "finalization_reserve_seconds": EXP061_FINALIZATION_RESERVE_SECONDS,
        "hard_stop_seconds": EXP061_HARD_STOP_SECONDS,
        "admission_policy": ("arms 2+ START-gated on max measured prior-arm cost + 20-min reserve; "
                             "every arm (incl. control) governed by the measured per-dataset in-arm "
                             "budget gate that aborts cleanly between datasets to protect the reserve"),
    }

    # per-arm ABSOLUTE stage counters summed over datasets (admission v3 #2) + identity-linked veto
    # survival counts for BOTH consumers, so gap and safe-div survival is legible without re-joining.
    stage_stats_by_arm = {}
    for a, s in arm_summaries.items():
        agg = {stage: {k: 0 for k in keys} for stage, keys in EXP061_STAGE_STAT_KEYS.items()}
        for ds in s.get("per_dataset", {}).values():
            for stage, keys in EXP061_STAGE_STAT_KEYS.items():
                for k in keys:
                    agg[stage][k] += int(ds.get("stage_stats", {}).get(stage, {}).get(k, 0))
        stage_stats_by_arm[a] = agg
    veto_survival_summary = {}
    for a in arm_summaries:
        rows_a = [r for r in veto_log if r.get("arm") == a]
        for kind in ("gap", "safe_div"):
            kr = [r for r in rows_a if r.get("kind") == kind]
            veto_survival_summary.setdefault(a, {})[kind] = {
                "records": len(kr),
                "accepted": sum(1 for r in kr if r.get("accept")),
                "survived_final": sum(1 for r in kr if r.get("survived_final")),
                "id_linked": sum(1 for r in kr if r.get("ids")),
            }

    telemetry = {
        "experiment": experiment_id,
        "parent": "repro_059_public_0947_exact_copy",
        "pinned_overrides": EXP061_RESOLVED_OVERRIDES,
        "arms_started": arms_started,
        "arm_status": arm_status,
                          "zero_candidate_case": zero_candidate_case,
                          "zon_view_expected_by_frame": zon_views_expected_by_frame,
                          "veto_calls_accounted_for": veto_calls_accounted_for,
        "arm_costs_seconds": arm_costs,
        "stop_note": stop_note,
        "run_exception": run_exception,
        "parent_tta_env_on": parent_tta_on,
        "validator_sweep_disabled": validator_disabled,
        "checkpoint_provenance": {"verified": checkpoint_provenance_verified,
                                  "deepcenter_sha256": verified_ckpt_sha,
                                  "transform_impl_version": EXP061_TRANSFORM_IMPL_VERSION},
        "parity": {"applicable": False, "reason": "deployment-only run omits development replay"},
        "mechanism_active": mechanism,
        "deployment_only": True,
        "zero_candidate_case": zero_candidate_case,
        "zon_view_expected_by_frame": zon_views_expected_by_frame,
        "veto_calls_accounted_for": veto_calls_accounted_for,
        "nonfinite_heatmap_events": nonfinite_heatmap_events,
        "view_cache": view_forward_summary,
        "feasibility_worksheet": feasibility_worksheet,
        "config_equal_frozen_parent": all_arm_configs_equal_parent,
        "frozen_parent_config_reference": {
            "source": "EXP061_FROZEN_PARENT_CONFIG (independent, parent-notebook-derived, test-guarded)",
            "live_pinned_equals_frozen": bool(live_config_equals_frozen_parent),
            "live_config_snapshot": live_parent_config_snapshot,
        },
        "veto_counts": {"error": n_error, "nonfinite": n_nonfinite, "missing_bypass": n_missing,
                        "total": len(veto_log)},
        "stage_stats_by_arm": stage_stats_by_arm,             # gap1/gap2/safe-div absolute counters (#2)
        "veto_survival_summary": veto_survival_summary,       # gap + safe-div identity-linked survival (#2)
        "arms": {k: {kk: vv for kk, vv in v.items() if kk != "per_dataset"}
                 for k, v in arm_summaries.items()},
        "delta_vs_xyonly": None,
        # combined per-veto records (identity + score + acceptance + safe_div final survival, #4)
        "veto_telemetry_rows": veto_log,
    }
    tel_path = out_dir / "exp061_telemetry.json"
    telemetry_persisted = False
    try:
        with open(tel_path, "w") as f:
            json.dump(telemetry, f, allow_nan=False, indent=2)
        json.loads(tel_path.read_text())
        telemetry_persisted = True
    except Exception as exc:
        print(f"[exp061] telemetry persistence FAILED (gate fails closed): {exc}", flush=True)

    checks = {
        "deployment_runs_only_zon": arms_started == ["zon"] and arm_status.get("zon") == "completed",
        "all_discovered_test_datasets_completed": (arm_status.get("zon") == "completed" and set(zon_summary.get("per_dataset", {})) == set(g["test_stems"])),
        "parent_deepcenter_tta_env_on": parent_tta_on,
        "validator_sweep_disabled": validator_disabled,                         # admission #6
        "checkpoint_provenance_verified": checkpoint_provenance_verified,       # admission #1
        "view_cache_integrity_ok": view_cache_integrity_ok,                     # admission #1
        "zon_started": bool(arms_started) and arms_started[0] == "zon",
        "resolved_config_pinned_tight55": pin_ok,
        "config_complete_all_arms": all_config_complete,
        "live_pinned_config_equals_frozen_parent": bool(live_config_equals_frozen_parent),  # v3 #1
        "all_arm_configs_equal_parent": all_arm_configs_equal_parent,          # admission #5 (v3 #1)
        "experimental_arms_execution_valid": all_started_execution_valid,       # admission v2 #3
        "shared_prediction_inputs_unchanged": shared_prediction_inputs_unchanged,  # content-hash (#5)
        "all_veto_scores_finite_and_accounted": n_error == 0 and n_nonfinite == 0 and n_missing == 0 and veto_calls_accounted_for,
        "no_nonfinite_heatmaps": no_nonfinite_heatmaps,                         # admission #3
        "telemetry_persisted_and_valid": telemetry_persisted,
        "no_exception_during_probe": run_exception is None,
        "within_hard_stop_and_timing_reliable": within_deadline,
        "whole_run_watchdog_armed": whole_run_watchdog_armed,
    }
    integrity_passed = all(checks.values())
    note = stop_note or ("integrity PASS" if integrity_passed else "integrity FAIL")

    _write_metrics(integrity_passed, checks, arm_summaries, note=note,
                   extra={"mechanism_active": mechanism,
        "deployment_only": True,
        "zero_candidate_case": zero_candidate_case,
        "zon_view_expected_by_frame": zon_views_expected_by_frame,
        "veto_calls_accounted_for": veto_calls_accounted_for, "view_cache": view_forward_summary,
                          "arms_started": arms_started, "arm_status": arm_status,
                          "zero_candidate_case": zero_candidate_case,
                          "zon_view_expected_by_frame": zon_views_expected_by_frame,
                          "veto_calls_accounted_for": veto_calls_accounted_for,
                          "checkpoint_provenance_verified": checkpoint_provenance_verified,
                          "validator_sweep_disabled": validator_disabled,
                          "nonfinite_heatmap_events": len(nonfinite_heatmap_events),
                          "run_exception": run_exception, "telemetry_persisted": telemetry_persisted})
    print(f"[exp061-zon] integrity {'PASS' if integrity_passed else 'FAIL'}; deployment_only=True; "
          f"arms={arms_started}; mechanism={mechanism}; note={note!r}; runtime={_elapsed():.0f}s; "
          f"wrote {metrics_path}", flush=True)
    # Keep the whole-run watchdog armed through final CSV audit and publication.
    return telemetry


# Injection contract (builder scripts/build_exp061_deepcenter_tta.py):
#   0. Inject at the TOP of the parent code cell, BEFORE the parent reads BIOHUB_VALIDATOR_ENABLE
#      (strippable `# exp061`) -- disables the adaptive PP-sweep (validator) which is pure overhead
#      here (the xyonly replay pins tight55 itself), reconciling the feasibility accounting:
#        os.environ['BIOHUB_VALIDATOR_ENABLE'] = '0'  # exp061
#   1. Inject at the TOP of the parent code cell (strippable `# exp061`):
#        _exp061_log_veto_candidate = (lambda *a, **k: None)  # exp061 stub
#   2. Inject one line immediately BEFORE the gap1 DeepCenter veto call (close_single_frame_gaps),
#      passing the in-scope IDs (strippable `# exp061`):
#        _exp061_log_veto_candidate('gap', dataset, mid_t, {'middle_id': middle_id, 'left_id': source_id, 'right_id': target_id, 'reused': int(middle_reused)}, node_point(middle))  # exp061
#   3. Inject one line immediately BEFORE the safe-div DeepCenter veto call
#      (add_safe_divisions_postlink), passing the in-scope IDs (strippable `# exp061`):
#        _exp061_log_veto_candidate('safe_div', dataset, int(candidate['t']), {'parent_id': source_id, 'existing_child_id': existing_child_id, 'candidate_child_id': candidate_id}, node_point(candidate))  # exp061
#   4. Append this module source as one cell, then a final cell with the guarded top-level call:
#        import os
#        os.environ.setdefault('BIOHUB_EXP061_ENABLE', '1')
#        if os.environ.get('BIOHUB_EXP061_ENABLE', '0') == '1':
#            _exp061_telemetry = run_exp061_deepcenter_tta(globals())
#        else:
#            print('[exp061] BIOHUB_EXP061_ENABLE != 1 - TTA probe skipped (parent path only).')
# Stripping every line containing the `# exp061` marker reproduces the parent notebook exactly.
