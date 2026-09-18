"""exp_060 — DeepCenter safe-division threshold micro-sweep (v2, post-admission-BLOCK-1).

APPENDED (with a tiny strippable call-site injection) onto the frozen repro_059 (Public LB
0.947) notebook by scripts/build_exp060_threshold_sweep.py. The parent's own 0.947 prediction
path runs byte-unchanged; stripping every `# exp060` line reproduces the parent exactly
(parity by construction). When BIOHUB_EXP060_ENABLE=1 it additionally produces three test
submissions at DEEPCENTER_SAFE_DIV_THRESHOLD in {0.20, 0.18, 0.22} plus attribution telemetry.

Design (proposal v3 CONSENSUS + admission-v1 fixes):
  * PIN the parent's resolved config = base env + MOTION_RELINK_TIGHT_UM=5.5 (authoritative
    source: ppsweep_selected.json). The parent's adaptive PP-sweep still executes as part of the
    byte-frozen parent pipeline (that is what keeps this purely additive and gives an
    independent within-run parent confirmation); exp_060's arms do NOT use it for selection.
  * Heatmaps are threshold-invariant; the sweep computes each frame once and reuses it across
    arms via a persistent cache (monkeypatch of deepcenter_heatmap_for_frame). [Accepted, bounded
    duplication: heatmaps the PARENT computed for its own submission are not shared into the
    sweep; the sweep recomputes them once, then arms 2/3 reuse arm-1's.]
  * Each arm re-runs the UNCHANGED filter_output_graph from a freshly loaded graph per movie
    (stronger isolation than deep-copy: zero cross-arm mutable state).
  * The 0.20 arm is the byte-parity control; its SHA256 MUST equal the parent's
    (d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60). Parity is checked
    IMMEDIATELY after the 0.20 arm; on mismatch the sweep STOPS (0.18/0.22 not run) and writes
    fail-closed metrics.json (gate False) — no crash.
  * Telemetry (admission fix #2): captured AT the safe-div call site with full node identities
    (dataset, t, parent/existing-child/candidate-child IDs, DeepCenter score + status, per-arm
    accept). Final surviving forks are captured with full (parent, child, child) identities from
    each arm's edge list; cross-arm fork/edge/node deltas are reported.
  * Runtime + hard stop (fix #3/#4): runtime_seconds measured from process start; a 2.0-h
    deadline is ENFORCED between arms; missing/nonfinite/error scores are distinguished and never
    serialized as NaN.

References parent-notebook globals by name (present after the parent cell runs).
"""

# ---------------------------------------------------------------------------
# Static configuration (frozen; mirrored in the experiment config/proposal)
# ---------------------------------------------------------------------------
EXP060_PARENT_SUBMISSION_SHA256 = (
    "d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60"
)
EXP060_RESOLVED_OVERRIDES = {"MOTION_RELINK_TIGHT_UM": 5.5}  # from ppsweep_selected.json
EXP060_CONTROL_THRESHOLD = 0.20
EXP060_ARMS = (0.20, 0.18, 0.22)  # pre-registered; 0.20 first (parity control)
EXP060_VALIDATION_PROTOCOL = "public_0947_deepcenter_safe_div_threshold_sweep_v1"
EXP060_EXPERIMENT_ID = "exp_060_deepcenter_safe_div_threshold_sweep"
EXP060_HARD_STOP_SECONDS = 2.0 * 3600.0
# Effective-config knobs captured at RUNTIME per arm to prove only the threshold differs across
# arms on the ACTUAL pipeline (Codex formal review fix #3).
EXP060_CONFIG_KEYS = (
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
    "SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC", "SHORT_TRACK_RESCUE_MIN_LEN",
    "SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB", "SHORT_TRACK_RESCUE_MAX_MEAN_EDGE_DIST_UM",
    "SHORT_TRACK_RESCUE_MAX_NODES_FRAC", "SHORT_TRACK_RESCUE_MAX_NODES_ABS",
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
# Call-site candidate logger (fed by a strippable `# exp060` line injected into
# add_safe_divisions_postlink). A no-op stub with the same name is injected at the TOP of the
# parent cell so the parent's own run (before this module cell) never hits a NameError; this
# module rebinds the stub to the real logger only while an arm is active.
# ---------------------------------------------------------------------------
_EXP060_CANDIDATE_LOG = []          # list of per-candidate rows (full node identities)
_EXP060_ACTIVE_ARM = {"threshold": None}


def _exp060_real_candidate_logger(g):
    """Return a logger closure bound to notebook globals `g`."""
    import math

    def _log(dataset, t, source_id, existing_child_id, candidate_id, point,
             detector_bundle, frame_cache, heatmap_cache):
        if _EXP060_ACTIVE_ARM["threshold"] is None:
            return
        score = None
        status = "ok"
        try:
            score = g["deepcenter_score_point"](
                dataset, None if t is None else int(t), point,
                detector_bundle, frame_cache, heatmap_cache,
            )
        except Exception:
            status = "error"
            score = None
        if score is None:
            if status != "error":
                status = "missing"
        elif not math.isfinite(float(score)):
            status = "nonfinite"
            score = None  # never serialize NaN/inf
        else:
            score = float(score)
        threshold = _EXP060_ACTIVE_ARM["threshold"]
        # Replicate the real gate outcome (deepcenter_accept_repair_point): a missing/None score
        # is a BYPASS that the gate accepts; otherwise accept iff score >= threshold. `error`/
        # `nonfinite` are anomalies (score forced to None) -> flagged, not silently accepted.
        bypass = status in ("missing", "error", "nonfinite")
        if bypass:
            gate_accept = (status == "missing")  # only a genuine missing score bypass-accepts
        else:
            gate_accept = float(score) >= float(threshold)
        _EXP060_CANDIDATE_LOG.append({
            "arm_threshold": threshold,
            "dataset": dataset,
            "t": None if t is None else int(t),
            "parent_id": None if source_id is None else int(source_id),
            "existing_child_id": None if existing_child_id is None else int(existing_child_id),
            "candidate_child_id": None if candidate_id is None else int(candidate_id),
            "deepcenter_score": score,
            "score_status": status,
            "gate_bypass": bool(bypass),
            "gate_accept": bool(gate_accept),
            "survived_final": None,          # both daughters present in the final fork
            "survived_candidate_edge": None,  # just the candidate edge present in the final graph
        })
    return _log


def _exp060_process_start_seconds():
    """Return (process_start_epoch_seconds, reliable). `reliable` is False when we could not read
    a real process/kernel start time and fell back to now() — the caller must then FAIL the
    hard-stop check rather than silently restart the budget clock (admission fix #2)."""
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
                    btime = float(line.split()[1])
                    return btime + starttime_ticks / hz, True
    except Exception:
        pass
    return time.time(), False


def run_exp060_threshold_sweep(g: dict) -> dict:
    """Run the three-arm safe-division threshold sweep in the notebook namespace `g`."""
    import os
    import csv
    import json
    import time
    import math
    import hashlib
    from pathlib import Path
    from collections import Counter

    # Whole-run start is the top-of-notebook injected timestamp (arms/measures BEFORE the parent
    # run). Fall back to the process-start reader; if THAT is unreliable, the deadline check fails
    # closed. The top-injected SIGALRM watchdog (armed before the parent) is the actual enforcer;
    # it is disarmed only after metrics+telemetry are finalized (Codex v3 fix #1).
    if "_EXP060_RUN_START" in g:
        proc_start, timing_reliable = float(g["_EXP060_RUN_START"]), True
    else:
        proc_start, timing_reliable = _exp060_process_start_seconds()
    whole_run_watchdog_armed = bool(g.get("_EXP060_WATCHDOG_ARMED", False))

    def _elapsed():
        return time.time() - proc_start

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
        "test_stems", "CSV_COLUMNS", "REPO_DIR", "METHOD",
        "deepcenter_heatmap_for_frame", "deepcenter_accept_repair_point",
        "deepcenter_score_point", "DEEPCENTER_SAFE_DIV_THRESHOLD", "MOTION_RELINK_TIGHT_UM",
        "WORKING_DIR",
    ]
    missing = [name for name in required if name not in g]
    if missing:
        raise RuntimeError(f"exp060: missing parent globals: {missing}")

    out_dir = Path(g["WORKING_DIR"]) / "exp060"
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = Path(g["WORKING_DIR"]) / "metrics.json"
    experiment_id = str(g.get("EXPERIMENT_ID", EXP060_EXPERIMENT_ID) or EXP060_EXPERIMENT_ID)

    # -- pin resolved config (base env + tight55) ------------------------------
    for key, value in EXP060_RESOLVED_OVERRIDES.items():
        if key not in g:
            raise RuntimeError(f"exp060: cannot pin unknown global {key}")
        g[key] = value

    def _write_metrics(integrity_passed, checks, arm_summaries, note="", extra=None):
        runtime_seconds = max(0.0, _elapsed())
        # COMMIT-TIME deadline recheck (Codex v4 fix #1): if the 2.0-h budget was crossed by the
        # time we commit metrics, force the gate False -- a PASS computed earlier cannot survive a
        # commit that lands over budget. Sticky: this only ever flips PASS->FAIL, never FAIL->PASS.
        if runtime_seconds > EXP060_HARD_STOP_SECONDS:
            checks = dict(checks, within_hard_stop_and_timing_reliable=False)
            integrity_passed = False
            note = (note + " | commit-time over budget").strip(" |")
        metrics = {
            "schema_version": 1,
            "experiment_id": experiment_id,
            "validation": {"protocol": EXP060_VALIDATION_PROTOCOL},
            "runtime_seconds": runtime_seconds,
            "reproducible": False,
            "primary_metric": 1.0 if integrity_passed else 0.0,
            "primary_metric_meaning": (
                "integrity gate: 0.20-arm byte-parity with parent 0.947 submission + all three "
                "arms produced + resolved config pinned + no error/nonfinite scores + within the "
                "2.0h budget (reliable timing) + no exception. Decides NOTHING about quality; "
                "the Public LB scores the 0.18/0.22 arms."
            ),
            "exp060_threshold_sweep_integrity_passed": bool(integrity_passed),
            "checks": checks,
            "note": note,
            "arm_submission_sha256": {k: v["sha256"] for k, v in arm_summaries.items()},
            "arm_final_counts": {k: {"nodes": v["nodes"], "edges": v["edges"], "rows": v["rows"]}
                                 for k, v in arm_summaries.items()},
            "parent_submission_sha256": EXP060_PARENT_SUBMISSION_SHA256,
            "pinned_overrides": EXP060_RESOLVED_OVERRIDES,
            "runtime_seconds_source": "process_start_to_now",
        }
        if extra:
            metrics.update(extra)
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, allow_nan=False, indent=2)
        return metrics

    # -- persistent heatmap cache (compute once, reuse across arms) ------------
    persistent_heatmaps = {}
    _orig_heatmap_for_frame = g["deepcenter_heatmap_for_frame"]

    def _persistent_heatmap_for_frame(dataset, t, detector_bundle, frame_cache, heatmap_cache):
        key = (dataset, int(t))
        cached = persistent_heatmaps.get(key)
        if cached is not None:
            return cached
        hm = _orig_heatmap_for_frame(dataset, t, detector_bundle, frame_cache, heatmap_cache)
        if hm is not None:
            persistent_heatmaps[key] = hm
        return hm

    # -- gate wrapper: per-arm accept telemetry (point-level, complements the --
    #    call-site ID logger). Distinguishes missing/nonfinite/error. -----------
    _orig_accept = g["deepcenter_accept_repair_point"]

    # -- install patches + real call-site logger -------------------------------
    g["deepcenter_heatmap_for_frame"] = _persistent_heatmap_for_frame
    _stub_logger = g.get("_exp060_log_safe_div_candidate")
    g["_exp060_log_safe_div_candidate"] = _exp060_real_candidate_logger(g)

    def _forks_with_ids(edges, nodes_by_id):
        """Return {parent_id: sorted(child_ids)} for source nodes with >=2 children."""
        out = {}
        for e in edges:
            s = int(e["source_id"]); tt = int(e["target_id"])
            out.setdefault(s, []).append(tt)
        return {s: sorted(ch) for s, ch in out.items() if len(ch) >= 2}

    def _write_arm_submission(threshold, out_path):
        """Write one arm's submission via the UNCHANGED filter_output_graph per movie.

        Row-emission is a faithful copy of write_test_submission (parent ~3103-3142); Codex v1
        admission verified byte-parity of this logic.
        """
        g["DEEPCENTER_SAFE_DIV_THRESHOLD"] = float(threshold)
        _EXP060_ACTIVE_ARM["threshold"] = float(threshold)

        geffs = sorted((Path(g["REPO_DIR"]) / "predictions").glob(f"*/{g['METHOD']}/split_0/*.geff"))
        found = [p.stem for p in geffs]
        expected = set(g["test_stems"])
        if (len(geffs) != len(g["test_stems"]) or
                sorted(s for s, c in Counter(found).items() if c > 1) or
                sorted(expected - set(found)) or sorted(set(found) - expected)):
            raise RuntimeError(f"exp060 arm {threshold}: unexpected prediction graphs")

        csv_columns = g["CSV_COLUMNS"]
        row_id = 0
        total_nodes = 0
        total_edges = 0
        arm_final = {}
        final_edge_sets = {}  # dataset -> set[(source_id, target_id)] in the final graph
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_columns)
            writer.writeheader()
            for geff_path in geffs:
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
                for edge in edges:
                    s = int(edge["source_id"]); tt = int(edge["target_id"])
                    if s not in nodes_by_id or tt not in nodes_by_id:
                        raise AssertionError(f"{dataset}: dangling edge after filtering")
                    writer.writerow({"id": row_id, "dataset": dataset, "row_type": "edge",
                                     "node_id": -1, "t": -1, "z": -1, "y": -1, "x": -1,
                                     "source_id": s, "target_id": tt})
                    row_id += 1
                    edge_set.add((s, tt))
                total_nodes += len(nodes_by_id)
                total_edges += len(edges)
                final_edge_sets[dataset] = edge_set
                arm_final[dataset] = {"forks": _forks_with_ids(edges, nodes_by_id),
                                      "edge_set": edge_set,
                                      "n_edges": len(edges), "n_nodes": len(nodes_by_id)}
        # join final graph back to this arm's logged candidates. A safe-division SURVIVES only if
        # the parent is a fork in the final graph (BOTH daughters present), not merely the single
        # candidate edge (Codex formal review fix #4).
        this_arm = float(threshold)
        for row in _EXP060_CANDIDATE_LOG:
            if row["arm_threshold"] == this_arm and row["survived_final"] is None:
                es = final_edge_sets.get(row["dataset"], set())
                forks = arm_final.get(row["dataset"], {}).get("forks", {})
                pid, ecid, ccid = row["parent_id"], row["existing_child_id"], row["candidate_child_id"]
                cand_edge = pid is not None and ccid is not None and (int(pid), int(ccid)) in es
                exist_edge = pid is not None and ecid is not None and (int(pid), int(ecid)) in es
                row["survived_candidate_edge"] = bool(cand_edge)
                row["survived_final"] = bool(cand_edge and exist_edge and pid is not None
                                             and int(pid) in forks and int(ccid) in forks[int(pid)])
        _EXP060_ACTIVE_ARM["threshold"] = None
        # capture the ACTUAL, COMPLETE effective config this arm ran with (fix #3): every knob in
        # EXP060_CONFIG_KEYS must be a live global; a missing knob fails the completeness gate.
        effective_config = {k: g[k] for k in EXP060_CONFIG_KEYS if k in g}
        # include env-driven TTA / fusion settings (formal review round-3 #3)
        for _envk in ("BIOHUB_DEEPCENTER_TTA", "BIOHUB_SECONDARY_EDGE_FEATURE_TTA",
                      "BIOHUB_SECONDARY_EDGE_FEATURE_TTA_WEIGHT", "BIOHUB_EDGE_FEATURE_TTA",
                      "BIOHUB_BIDIRECTIONAL_FUSION_MODE", "BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT"):
            effective_config["env:" + _envk] = os.environ.get(_envk)
        config_complete = all(k in g for k in EXP060_CONFIG_KEYS)
        missing_config_keys = [k for k in EXP060_CONFIG_KEYS if k not in g]
        sha = hashlib.sha256(Path(out_path).read_bytes()).hexdigest()
        return {"sha256": sha, "rows": row_id, "nodes": total_nodes, "edges": total_edges,
                "effective_config": effective_config, "config_complete": config_complete,
                "missing_config_keys": missing_config_keys, "per_dataset": arm_final}

    # -- run arms with early-parity stop + ENFORCED deadline (watchdog + gates) --
    def _predictions_fingerprint():
        """Fingerprint the shared prediction geffs (path/size/mtime) to prove the arms leave the
        shared inputs immutable on the REAL pipeline (formal review round-3 #2)."""
        base = Path(g["REPO_DIR"]) / "predictions"
        items = []
        if base.exists():
            for p in sorted(base.rglob("*")):
                if p.is_file():
                    st = p.stat()
                    items.append((str(p.relative_to(base)), st.st_size, st.st_mtime_ns))
        return hashlib.sha256(repr(items).encode()).hexdigest()

    pred_fp_before = _predictions_fingerprint()
    arm_summaries = {}
    stop_note = ""
    run_exception = None
    # The whole-run SIGALRM watchdog is already armed (top-of-notebook injection); it stays armed
    # through metrics+telemetry finalization and is disarmed at the very end.
    try:
        for threshold in EXP060_ARMS:
            if _elapsed() > EXP060_HARD_STOP_SECONDS:
                stop_note = f"hard-stop {EXP060_HARD_STOP_SECONDS}s reached before arm {threshold}"
                print(f"[exp060] {stop_note}", flush=True)
                break
            label = f"thr{int(round(threshold * 100)):03d}"
            arm_summaries[label] = _write_arm_submission(threshold, out_dir / f"submission_{label}.csv")
            print(f"[exp060] arm {threshold}: sha={arm_summaries[label]['sha256'][:16]}... "
                  f"nodes={arm_summaries[label]['nodes']} edges={arm_summaries[label]['edges']} "
                  f"elapsed={_elapsed():.0f}s", flush=True)
            if label == "thr020" and arm_summaries["thr020"]["sha256"] != EXP060_PARENT_SUBMISSION_SHA256:
                stop_note = "0.20 control parity mismatch - stopping before 0.18/0.22"
                print(f"[exp060] {stop_note}", flush=True)
                break
    except BaseException as exc:  # incl. TimeoutError from the watchdog
        run_exception = f"{type(exc).__name__}: {exc}"
        stop_note = stop_note or f"exception during sweep: {run_exception}"
        print(f"[exp060] EXCEPTION: {run_exception}", flush=True)
    finally:
        # restore parent functions; do NOT disarm the whole-run watchdog yet (retain through
        # finalization so metrics/telemetry writing is still covered by the budget).
        g["deepcenter_heatmap_for_frame"] = _orig_heatmap_for_frame
        g["deepcenter_accept_repair_point"] = _orig_accept
        if _stub_logger is not None:
            g["_exp060_log_safe_div_candidate"] = _stub_logger
        g["DEEPCENTER_SAFE_DIV_THRESHOLD"] = float(EXP060_CONTROL_THRESHOLD)
        _EXP060_ACTIVE_ARM["threshold"] = None

    # -- integrity checks (fail-closed via the gate, never a silent PASS) -------
    control = arm_summaries.get("thr020", {})
    parity_ok = bool(control) and control.get("sha256") == EXP060_PARENT_SUBMISSION_SHA256
    all_arms_present = all(f"thr{int(round(t * 100)):03d}" in arm_summaries for t in EXP060_ARMS)
    pin_ok = float(g["MOTION_RELINK_TIGHT_UM"]) == 5.5
    n_nonfinite = sum(1 for r in _EXP060_CANDIDATE_LOG if r.get("score_status") == "nonfinite")
    n_error = sum(1 for r in _EXP060_CANDIDATE_LOG if r.get("score_status") == "error")
    n_missing = sum(1 for r in _EXP060_CANDIDATE_LOG if r.get("score_status") == "missing")
    n_survived = sum(1 for r in _EXP060_CANDIDATE_LOG if r.get("survived_final") is True)
    within_deadline = timing_reliable and (_elapsed() <= EXP060_HARD_STOP_SECONDS)
    # effective-config fingerprint: the FULL captured config (minus the threshold) must be
    # identical across arms, on the ACTUAL pipeline (fix #3).
    # Canonical parent config = the 0.20 control arm's effective config (which reproduces the
    # parent submission byte-for-byte). Every arm's full config MINUS the threshold must equal it,
    # be complete (no missing knob), and each arm's captured threshold must equal its assigned arm
    # (formal review round-3 #3).
    _arm_thr = {"thr020": 0.20, "thr018": 0.18, "thr022": 0.22}

    def _cfg_minus_thr(label):
        return {k: v for k, v in arm_summaries.get(label, {}).get("effective_config", {}).items()
                if k != "DEEPCENTER_SAFE_DIV_THRESHOLD"}

    _canon = _cfg_minus_thr("thr020")
    _all_complete = bool(arm_summaries) and all(s.get("config_complete") for s in arm_summaries.values())
    _match_canon = ("thr020" in arm_summaries
                    and all(_cfg_minus_thr(lbl) == _canon for lbl in arm_summaries))
    _thr_assigned = all(
        float(arm_summaries[lbl].get("effective_config", {}).get("DEEPCENTER_SAFE_DIV_THRESHOLD", -1))
        == _arm_thr.get(lbl, -1) for lbl in arm_summaries)
    effective_config_threshold_only = (_match_canon and _all_complete and _thr_assigned
                                       and len(_canon) >= 40)
    shared_prediction_inputs_unchanged = (pred_fp_before == _predictions_fingerprint())

    # -- attribution: cross-arm fork/edge/node deltas (full IDs) ---------------
    def _fork_edge_delta(base_label, arm_label):
        out = {}
        if base_label not in arm_summaries or arm_label not in arm_summaries:
            return out
        for ds in arm_summaries[base_label]["per_dataset"]:
            b = arm_summaries[base_label]["per_dataset"][ds]
            a = arm_summaries[arm_label]["per_dataset"][ds]
            b_forks = {(p, tuple(ch)) for p, ch in b["forks"].items()}
            a_forks = {(p, tuple(ch)) for p, ch in a["forks"].items()}
            b_edges, a_edges = b.get("edge_set", set()), a.get("edge_set", set())
            out[ds] = {
                "d_forks": len(a_forks) - len(b_forks),
                "forks_added": [{"parent": p, "children": list(ch)} for p, ch in sorted(a_forks - b_forks)],
                "forks_removed": [{"parent": p, "children": list(ch)} for p, ch in sorted(b_forks - a_forks)],
                "d_edges": a["n_edges"] - b["n_edges"],
                "d_nodes": a["n_nodes"] - b["n_nodes"],
                # EXACT edge differences (Codex formal review fix #4)
                "edges_added": [list(e) for e in sorted(a_edges - b_edges)],
                "edges_removed": [list(e) for e in sorted(b_edges - a_edges)],
            }
        return out

    candidate_counts = {"nonfinite": n_nonfinite, "error": n_error, "missing_bypass": n_missing,
                        "survived_final": n_survived, "total": len(_EXP060_CANDIDATE_LOG)}

    # -- telemetry is a REQUIRED contract output: persist + VALIDATE it FIRST, and make its
    #    successful persistence a gate condition (Codex formal review fix #2). Metrics.json is
    #    still written LAST and unconditionally, so telemetry can neither mask nor precede it.
    telemetry = {
        "experiment": experiment_id,
        "parent": "repro_059_public_0947_exact_copy",
        "pinned_overrides": EXP060_RESOLVED_OVERRIDES,
        "stop_note": stop_note,
        "run_exception": run_exception,
        "candidate_counts": candidate_counts,
        "arms": {k: {kk: vv for kk, vv in v.items() if kk != "per_dataset"}
                 for k, v in arm_summaries.items()},
        "parity": {"control_sha256": control.get("sha256"),
                   "parent_sha256": EXP060_PARENT_SUBMISSION_SHA256, "ok": parity_ok},
        "delta_vs_control": {"thr018": _fork_edge_delta("thr020", "thr018"),
                             "thr022": _fork_edge_delta("thr020", "thr022")},
        "candidate_telemetry_rows": _EXP060_CANDIDATE_LOG,
    }
    tel_path = out_dir / "exp060_telemetry.json"
    telemetry_persisted = False
    try:
        with open(tel_path, "w") as f:
            json.dump(telemetry, f, allow_nan=False, indent=2)
        json.loads(tel_path.read_text())  # validate it round-trips
        telemetry_persisted = True
    except Exception as exc:
        print(f"[exp060] telemetry persistence FAILED (gate will fail closed): {exc}", flush=True)

    checks = {
        "control_parity_sha256_matches_parent": parity_ok,
        "all_three_arms_produced": all_arms_present,
        "resolved_config_pinned_tight55": pin_ok,
        "effective_config_threshold_only": effective_config_threshold_only,
        "shared_prediction_inputs_unchanged": shared_prediction_inputs_unchanged,
        "no_candidate_score_errors": n_error == 0,
        "no_missing_or_nonfinite_bypass": (n_missing == 0 and n_nonfinite == 0),
        "telemetry_nonempty": len(_EXP060_CANDIDATE_LOG) > 0,
        "telemetry_persisted_and_valid": telemetry_persisted,
        "no_exception_during_sweep": run_exception is None,
        "within_hard_stop_and_timing_reliable": within_deadline,
        "whole_run_watchdog_armed": whole_run_watchdog_armed,
        "no_hard_stop_triggered": stop_note == "",
    }
    integrity_passed = all(checks.values())
    note = stop_note or ("integrity PASS" if integrity_passed else "integrity FAIL")

    # metrics.json LAST + unconditional (all floats sanitized; commit-time deadline recheck inside).
    _write_metrics(integrity_passed, checks, arm_summaries, note=note,
                   extra={"candidate_counts": candidate_counts, "run_exception": run_exception,
                          "telemetry_persisted": telemetry_persisted})
    print(f"[exp060] integrity {'PASS' if integrity_passed else 'FAIL'}; parity_ok={parity_ok}; "
          f"note={note!r}; runtime={_elapsed():.0f}s; counts={candidate_counts}; wrote {metrics_path}",
          flush=True)
    # finalization complete -> now it is safe to disarm the whole-run budget watchdog.
    _disarm_watchdog()
    return telemetry


# Injection contract (builder scripts/build_exp060_threshold_sweep.py):
#   1. Inject at the TOP of the parent code cell (strippable `# exp060`):
#        _exp060_log_safe_div_candidate = (lambda *a, **k: None)  # exp060 stub
#   2. Inject one line immediately BEFORE the safe-div DeepCenter gate call
#      (parent add_safe_divisions_postlink), passing the in-scope IDs (strippable `# exp060`):
#        _exp060_log_safe_div_candidate(dataset, int(candidate['t']), source_id, existing_child_id, candidate_id, node_point(candidate), deepcenter_bundle, frame_cache, deepcenter_cache)  # exp060
#   3. Append this module source as one cell, then a final cell with the guarded top-level call:
#        import os
#        os.environ.setdefault('BIOHUB_EXP060_ENABLE', '1')
#        if os.environ.get('BIOHUB_EXP060_ENABLE', '0') == '1':
#            _exp060_telemetry = run_exp060_threshold_sweep(globals())
#        else:
#            print('[exp060] BIOHUB_EXP060_ENABLE != 1 - threshold sweep skipped (parent path only).')
# Stripping every line containing the `# exp060` marker reproduces the parent notebook exactly.
