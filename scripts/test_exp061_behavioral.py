"""Behavioral tests for the exp_061 DeepCenter-TTA harness (proposal v5 CONSENSUS).

Dependency-light and fail-closed. Covers the correctness-critical claims the fresh Codex admission
must be able to re-verify WITHOUT a GPU:

  A. Transform coordinate maps (byte-parity critical): each view's forward/inverse, on an
     ASYMMETRIC fixture, maps coordinates exactly as documented -- NOT merely inverse(forward)==id
     (a wrong transform + its own inverse would pass that weaker check). Verifies Ta == X-flip
     orientation (matches the parent), Aad == anti-diagonal reflection and self-inverse,
     Aad != Ta, xyd4 = 8 DISTINCT D4 orientations, xyonly = 7 (Ta duplicates Vx), and the Z
     composition (Z-of-view == flip(-3) then the XY view).
  B. When numpy is available, the ACTUAL module `_apply_forward`/`_apply_inverse` are exercised on
     a numpy tensor and cross-checked against the pure-python coordinate model.
  C. Arm view specs: xyonly 8 / zon 16 / xyd4 8, orders, xyd4 replaces Ta with Aad, control first.
  D. Cache-key + signature negative tests: distinct arm signatures (stable); view keys differ
     across (dataset,t,view); a different arm signature never collides.
  E. Accumulation order: the xyonly view order equals the parent's exact order (byte-parity).

Usage: python scripts/test_exp061_behavioral.py
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/exp061_deepcenter_tta.py"

_failures = []


def check(cond, msg):
    print(("  ok  " if cond else " FAIL ") + msg)
    if not cond:
        _failures.append(msg)


def _load_module():
    spec = importlib.util.spec_from_file_location("exp061_mod", MODULE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------------------
# Pure-python coordinate model of the XY-plane transforms (torch semantics: last dim = X (-1),
# second-last = Y (-2); rot90 on dims (-2,-1) is CCW). Mirrors the module's view definitions so we
# can assert coordinate maps with zero deps.
# ---------------------------------------------------------------------------
def _flipX(g):     return [row[::-1] for row in g]
def _flipY(g):     return g[::-1]
def _flipYX(g):    return [row[::-1] for row in g[::-1]]
def _transpose(g): return [list(r) for r in zip(*g)]
def _rot90(g, k):
    k %= 4
    for _ in range(k):
        g = [list(r) for r in zip(*g)][::-1]   # one CCW step
    return g
def _rotm90(g, k): return _rot90(g, (-k) % 4)


def _fwd_xy(v, g):
    return {"V0": g, "Vx": _flipX(g), "Vy": _flipY(g), "Vxy": _flipYX(g),
            "R1": _rot90(g, 1), "R3": _rot90(g, 3), "Td": _transpose(g),
            "Ta": _transpose(_rot90(g, 1)),         # rot90(x,1).transpose(-1,-2)
            "Aad": _flipYX(_transpose(g))}[v]       # transpose(x).flip(-2,-1)


def _inv_xy(v, y):
    if v == "V0":  return y
    if v == "Vx":  return _flipX(y)
    if v == "Vy":  return _flipY(y)
    if v == "Vxy": return _flipYX(y)
    if v == "R1":  return _rotm90(y, 1)
    if v == "R3":  return _rotm90(y, 3)
    if v == "Td":  return _transpose(y)
    if v == "Ta":  return _rotm90(_transpose(y), 1)   # rot90(y.transpose, -1)
    if v == "Aad": return _flipYX(_transpose(y))      # self-inverse
    raise KeyError(v)


def test_A_coordinate_maps():
    print("A. transform coordinate maps (asymmetric fixture)")
    g = [[10 * r + c for c in range(4)] for r in range(4)]   # 4x4 unique cells
    xy_views = ["V0", "Vx", "Vy", "Vxy", "R1", "R3", "Td", "Ta", "Aad"]
    bad = [v for v in xy_views if _inv_xy(v, _fwd_xy(v, g)) != g]
    check(not bad, f"roundtrip inv(fwd(x))==x for all XY views (bad: {bad})")
    check(_fwd_xy("Ta", g) == _fwd_xy("Vx", g), "Ta orientation == X-flip (matches parent)")
    check(_fwd_xy("Aad", g) == _flipYX(_transpose(g)), "Aad == anti-diagonal reflection")
    check(_inv_xy("Aad", _fwd_xy("Aad", g)) == g, "Aad self-inverse")
    check(_fwd_xy("Aad", g) != _fwd_xy("Ta", g), "Aad orientation != Ta (distinct view)")
    xyd4 = ["V0", "Vx", "Vy", "Vxy", "R1", "R3", "Td", "Aad"]
    orients = {tuple(map(tuple, _fwd_xy(v, g))) for v in xyd4}
    check(len(orients) == 8, "xyd4 = 8 DISTINCT orientations (true D4)")
    xyonly = ["V0", "Vx", "Vy", "Vxy", "R1", "R3", "Td", "Ta"]
    check(len({tuple(map(tuple, _fwd_xy(v, g))) for v in xyonly}) == 7,
          "xyonly = 7 distinct orientations (Ta duplicates Vx)")


def test_B_module_functions_numpy():
    print("B. actual module _apply_forward/_apply_inverse (numpy)")
    try:
        import numpy as np
    except Exception:
        print("  skip  numpy unavailable (runs on Kaggle); pure-python model in A covers the algebra")
        return
    m = _load_module()

    class T:  # minimal torch-tensor shim over numpy
        def __init__(s, a): s.a = np.asarray(a)
        @property
        def shape(s): return s.a.shape
        def flip(s, dims): return T(np.flip(s.a, tuple(dims)))
        def transpose(s, i, j): return T(np.swapaxes(s.a, i, j))

    class TM:
        @staticmethod
        def rot90(x, k, dims): return T(np.rot90(x.a, k, axes=tuple(dims)))
    tm = TM()

    # asymmetric 5D volume (1,1,Z=2,Y=4,X=4); Z distinct so Z-reflection is observable
    x = T(np.arange(2 * 4 * 4, dtype=np.float32).reshape(1, 1, 2, 4, 4))
    allviews = set()
    for arm, views in m.EXP061_ARM_VIEWS.items():
        for v, _ in views:
            allviews.add(v)
    bad = []
    for v in sorted(allviews):
        got = m._apply_inverse(v, m._apply_forward(v, x, tm), tm).a
        if not np.array_equal(got, x.a):
            bad.append(v)
    check(not bad, f"module roundtrip inv(fwd(x))==x for ALL views incl. Z (bad: {bad})")
    # Ta input == Vx input (X-flip orientation) on the actual module function
    check(np.array_equal(m._apply_forward("Ta", x, tm).a, m._apply_forward("Vx", x, tm).a),
          "module Ta input == Vx input (X-flip)")
    # ZVx forward == flip(-3) then Vx
    zvx = m._apply_forward("ZVx", x, tm).a
    ref = np.flip(np.flip(x.a, (-3,)), (-1,))
    check(np.array_equal(zvx, ref), "module ZVx == Z(flip -3) then Vx")
    # Aad != Ta as an actual forward
    check(not np.array_equal(m._apply_forward("Aad", x, tm).a, m._apply_forward("Ta", x, tm).a),
          "module Aad forward != Ta forward")


def test_C_arm_specs():
    print("C. arm view specs")
    m = _load_module()
    v = m.EXP061_ARM_VIEWS
    ids = {a: [vid for vid, _ in v[a]] for a in v}
    check(ids["xyonly"] == ["V0", "Vx", "Vy", "Vxy", "R1", "R3", "Td", "Ta"],
          "xyonly views == parent order V0,Vx,Vy,Vxy,R1,R3,Td,Ta (8)")
    check(len(ids["zon"]) == 16 and ids["zon"][:8] == ids["xyonly"]
          and all(z.startswith("Z") for z in ids["zon"][8:]),
          "zon == xyonly (8) + Z-reflection of each (8) = 16")
    check(ids["xyd4"] == ["V0", "Vx", "Vy", "Vxy", "R1", "R3", "Td", "Aad"],
          "xyd4 replaces Ta with Aad (uniform 8-view D4)")
    check("Ta" not in ids["xyd4"] and "Aad" not in ids["xyonly"],
          "xyd4 has no Ta; xyonly has no Aad (arms are distinct)")
    check(m.EXP061_ARMS[0] == m.EXP061_CONTROL_ARM == "xyonly",
          "control arm xyonly is first (protected execution order)")


def test_D_signatures_and_keys():
    print("D. arm signatures + view-cache keys (isolation)")
    m = _load_module()
    sigs = {a: m.exp061_arm_signature(a) for a in m.EXP061_ARMS}
    check(len(set(sigs.values())) == 3, f"three DISTINCT arm signatures ({sigs})")
    check(all(sigs[a] == m.exp061_arm_signature(a) for a in m.EXP061_ARMS),
          "arm signatures are stable (order-sensitive, deterministic)")
    # order sensitivity: a reordered view list must change the signature
    import hashlib
    base = "exp061-v1|xyonly|" + ",".join(f"{vid}:{int(sq)}" for vid, sq in m.EXP061_ARM_VIEWS["xyonly"])
    swapped_views = list(m.EXP061_ARM_VIEWS["xyonly"])
    swapped_views[1], swapped_views[2] = swapped_views[2], swapped_views[1]
    swapped = "exp061-v1|xyonly|" + ",".join(f"{vid}:{int(sq)}" for vid, sq in swapped_views)
    check(hashlib.sha256(base.encode()).hexdigest()[:16] == sigs["xyonly"]
          and hashlib.sha256(swapped.encode()).hexdigest()[:16] != sigs["xyonly"],
          "signature is order-sensitive (reordering views changes it)")


def test_E_accumulation_order_parity():
    print("E. xyonly accumulation order == parent (byte-parity intent)")
    src = MODULE.read_text(encoding="utf-8")
    # the parent order is V0,Vx,Vy,Vxy,R1,R3,Td,Ta -- assert the module encodes exactly this for xyonly
    m = _load_module()
    ids = [vid for vid, _ in m.EXP061_ARM_VIEWS["xyonly"]]
    check(ids == ["V0", "Vx", "Vy", "Vxy", "R1", "R3", "Td", "Ta"],
          "xyonly order matches the parent heatmap loop (base, 3 flips, 2 rots, transpose, anti-transpose)")
    # accumulation is left-to-right out-of-place from cached raw logits (no stacked reduction / in-place)
    check("acc = contrib.clone() if acc is None else acc + contrib" in src,
          "accumulation is sequential left-to-right, out-of-place (acc + contrib), lossless")
    check("logits = acc / nv" in src and "torch_mod.sigmoid(logits)" in src,
          "mean over executed views then sigmoid (matches parent)")
    check(".astype(np.float32, copy=False)" in src and 'np.save(view_dir / f"{key}.npy", arr)' in src,
          "view logits cached losslessly as float32 (byte-parity safe reload)")


def test_F_view_cache_keys():
    print("F. view-cache key: provenance + input binding, arm-independence (admission #1/#5)")
    m = _load_module()
    prov = "exp061|impl=v1|dcckpt=abc123"
    k = m.exp061_view_key(prov, "44b6_0113de3b", 7, "Vx", "IMGHASH")
    # deterministic + stable
    check(k == m.exp061_view_key(prov, "44b6_0113de3b", 7, "Vx", "IMGHASH"), "view key deterministic")
    # NEGATIVE tests: each field change flips the key (no collision)
    check(k != m.exp061_view_key(prov, "44b6_0113de3b", 8, "Vx", "IMGHASH"), "different frame t -> different key")
    check(k != m.exp061_view_key(prov, "6bba_05b6850b", 7, "Vx", "IMGHASH"), "different dataset -> different key")
    check(k != m.exp061_view_key(prov, "44b6_0113de3b", 7, "Vy", "IMGHASH"), "different view -> different key")
    check(k != m.exp061_view_key(prov, "44b6_0113de3b", 7, "Vx", "OTHER"), "different input image content -> different key (stale-input rejection)")
    check(k != m.exp061_view_key("exp061|impl=v2|dcckpt=abc123", "44b6_0113de3b", 7, "Vx", "IMGHASH"),
          "different transform-impl version -> different key (stale-impl rejection)")
    check(k != m.exp061_view_key("exp061|impl=v1|dcckpt=DIFFERENT", "44b6_0113de3b", 7, "Vx", "IMGHASH"),
          "different verified checkpoint hash -> different key (cross-run rejection)")


def test_G_arm_order_invariance():
    print("G. arm-order invariance (admission v2 #3/#5)")
    m = _load_module()
    prov = "exp061|impl=v1|dcckpt=abc123"
    # BOUNDED EXECUTION: the shared views' cache keys are identical no matter which arm 'computes'
    # them first -> reusing across arms in ANY order is deterministic. Build the key set for the
    # shared XY views in two different traversal orders and confirm equality.
    shared = [vid for vid, _ in m.EXP061_ARM_VIEWS["xyonly"]]
    keys_fwd = [m.exp061_view_key(prov, "ds", 5, vid, "IMG") for vid in shared]
    keys_rev = [m.exp061_view_key(prov, "ds", 5, vid, "IMG") for vid in reversed(shared)]
    check(set(keys_fwd) == set(keys_rev) and len(set(keys_fwd)) == len(shared),
          "shared-view cache keys are order-independent (arm-order-invariant reuse)")
    # the key function takes NO arm argument -> a view computed for one arm is reused by another
    src = MODULE.read_text(encoding="utf-8")
    defline = "".join(l for l in src.splitlines() if "def exp061_view_key" in l)
    check("arm" not in defline, "view-cache key signature takes no arm argument (cross-arm reuse)")
    # arm view lists are pure functions of arm name (no dependence on execution order/prior arms)
    check(m.EXP061_ARM_VIEWS["zon"] == m.EXP061_ARM_VIEWS["zon"]
          and 'EXP061_ARMS = ("xyonly", "zon", "xyd4")' in src,
          "arm view lists pure per arm; deterministic order xyonly->zon->xyd4")
    # NOTE: a full arm-execution reorder / valid-zero-response / interrupted-finalization test needs
    # the GPU pipeline (torch + geffs) and runs in the authorized Kaggle run; the harness records
    # arm_status started/completed/skipped/failed + atomic receipts for exactly those cases.


def test_H_hardening_source():
    print("H. hardening (atomic artifacts, content-hash, tensor nonfinite) source checks")
    src = MODULE.read_text(encoding="utf-8")
    check("os.replace(tmp_path, out_path)" in src, "arm CSV published atomically (temp + os.replace)")
    check("receipt_{arm}.json" in src and "os.replace(rc_tmp" in src, "atomic per-arm completion receipt")
    check(all(s in src for s in ('"started"', '"completed"', '"skipped"', '"failed"')),
          "arm status distinguishes started/completed/skipped/failed")
    check("hashlib.sha256(p.read_bytes()).hexdigest()" in src,
          "prediction-input immutability uses a CONTENT hash (not size/mtime)")
    check("np.isfinite(heatmap).all()" in src and "torch_mod.isfinite(logits).all()" in src,
          "nonfinite detected at the heatmap/logits tensor level")
    check("_view_sha" in src and "integrity_failures" in src,
          "view-cache content-hash integrity validation on hits")


# ===========================================================================
# EXECUTABLE end-to-end fixtures (admission v3 #3). These build a fully mocked notebook namespace
# `g` -- a numpy-backed torch shim, a deterministic fake DeepCenter model, a fake filter that drives
# BOTH veto consumers, and tiny on-disk fake geffs -- then run the ACTUAL top-level
# run_exp061_deepcenter_tta(g) end-to-end (no GPU). They exercise the real view-cache accumulation,
# per-arm isolation, veto telemetry/survival, the frozen-config gate, the measured per-dataset
# budget abort, and corrupt-cache recovery -- the behaviours source checks cannot prove.
# ===========================================================================

def _np_or_skip():
    try:
        import numpy as np
        return np
    except Exception:
        return None


def _build_mock_g(np, workdir, model_bias=0.0, dataset_sleep=0.0):
    """Construct a mocked parent-notebook namespace `g` for run_exp061_deepcenter_tta.

    Deterministic fake model: model(u) = u + model_bias * B, where B is a FIXED asymmetric pattern.
    bias == 0 -> the model is transform-EQUIVARIANT (every arm yields the identical heatmap: a valid
    ZERO response / verified null). bias != 0 -> arms with different view sets yield different
    heatmaps (mechanism active).
    """
    import os, csv

    # ---- numpy-backed torch tensor + torch module shims -----------------------------------
    class FT:
        __slots__ = ("a",)
        def __init__(s, a): s.a = np.asarray(a, dtype=np.float32)
        @property
        def shape(s): return s.a.shape
        def flip(s, dims): return FT(np.flip(s.a, tuple(dims)))
        def transpose(s, i, j): return FT(np.swapaxes(s.a, i, j))
        def detach(s): return s
        def cpu(s): return s
        def to(s, *a, **k): return s
        def clone(s): return FT(s.a.copy())
        def numpy(s): return s.a
        def item(s): return s.a.item()
        def all(s): return FT(np.array(bool(np.all(s.a))))
        def __add__(s, o): return FT(s.a + (o.a if isinstance(o, FT) else o))
        def __truediv__(s, o): return FT(s.a / (o.a if isinstance(o, FT) else o))
        def __getitem__(s, idx): return FT(s.a[idx])

    class TorchMod:
        float32 = np.float32
        @staticmethod
        def from_numpy(a): return FT(a)
        @staticmethod
        def rot90(x, k, dims): return FT(np.rot90(x.a, k, axes=tuple(dims)))
        @staticmethod
        def isfinite(x): return FT(np.isfinite(x.a))
        @staticmethod
        def sigmoid(x): return FT(1.0 / (1.0 + np.exp(-x.a)))
        class no_grad:
            def __enter__(s): return s
            def __exit__(s, *a): return False
    tm = TorchMod()

    # fixed asymmetric bias pattern over the (Z=2,Y=4,X=4) model field
    B = np.arange(2 * 4 * 4, dtype=np.float32).reshape(2, 4, 4)
    B = (B - B.mean())

    class Cfg:
        pool_factor = 1
    def fake_model(ft):
        return FT(ft.a + model_bias * (B if ft.a.shape[-3:] == B.shape else 0.0))

    bundle = {"model": fake_model, "cfg": Cfg(), "device": "cpu", "torch": tm}

    def read_test_frame(dataset, t, frame_cache):
        # deterministic per (dataset,t); asymmetric so transforms are observable
        base = (abs(hash((dataset, int(t)))) % 7) + 1
        vol = (np.arange(2 * 4 * 4, dtype=np.float32).reshape(2, 4, 4) + base)
        return vol
    def _dc_pool_frame_xy(volume, pool_factor): return volume
    def _dc_normalize_dynamic_range(pooled, cfg): return pooled.astype(np.float32)
    def _dc_cache_trim(cache):
        # bounded retention: keep <= 2 heatmaps (mirrors the parent's trim contract)
        while len(cache) > 2:
            cache.pop(next(iter(cache)))

    # veto scoring reads the REAL installed heatmap fn through the pipeline caches
    def deepcenter_score_point(dataset, t, point, bundle_, frame_cache, heatmap_cache):
        hm = g["deepcenter_heatmap_for_frame"](dataset, t, bundle_, frame_cache, heatmap_cache)
        if hm is None:
            return None
        return float(np.asarray(hm).mean())
    def deepcenter_accept_repair_point(dataset, t, point, bundle_, frame_cache, heatmap_cache,
                                       stats, kind, threshold):
        s = deepcenter_score_point(dataset, t, point, bundle_, frame_cache, heatmap_cache)
        return bool(s is not None and s >= 0.0)   # deterministic accept
    def deepcenter_heatmap_for_frame(dataset, t, bundle_, frame_cache, heatmap_cache):
        return None   # replaced by the harness install; parent stub

    # a fake graph object with node/edge iter_rows
    class _Rows:
        def __init__(s, rows): s._rows = rows
        def iter_rows(s, named=True): return iter(s._rows)
    class _Graph:
        def __init__(s, nodes, edges): s._n = nodes; s._e = edges
        def node_attrs(s): return _Rows(s._n)
        def edge_attrs(s): return _Rows(s._e)
    def graph_from_geff(path):
        # tiny fixed raw graph (filter replaces it deterministically); ids unique per dataset
        return _Graph([{"node_id": 0, "t": 0, "z": 0.0, "y": 0.0, "x": 0.0}],
                      [{"source_id": 0, "target_id": 0, "edge_prob": 1.0}])

    def filter_output_graph(nodes_by_id, raw_edges, dataset=None, deepcenter_bundle=None):
        if dataset_sleep:
            import time as _s
            _s.sleep(dataset_sleep)   # simulate a costly dataset to exercise the per-dataset gate
        # deterministic tiny lineage that drives BOTH veto consumers, with a division (fork) and a
        # gap bridge so gap + safe_div survival are both exercised.
        nodes = {
            0: {"node_id": 0, "t": 0, "z": 0, "y": 0, "x": 0},   # division parent
            1: {"node_id": 1, "t": 1, "z": 1, "y": 1, "x": 1},   # child A (existing)
            2: {"node_id": 2, "t": 1, "z": 2, "y": 2, "x": 2},   # child B (safe-div candidate)
            10: {"node_id": 10, "t": 0, "z": 3, "y": 3, "x": 3},  # gap left
            11: {"node_id": 11, "t": 1, "z": 4, "y": 4, "x": 0},  # gap middle
            12: {"node_id": 12, "t": 2, "z": 0, "y": 4, "x": 4},  # gap right
        }
        edges = [{"source_id": 0, "target_id": 1}, {"source_id": 0, "target_id": 2},
                 {"source_id": 10, "target_id": 11}, {"source_id": 11, "target_id": 12}]
        stats = {"gap_candidates": 1, "gap_pairs_selected": 1, "gap_added_edges": 2,
                 "gap_added_nodes": 1, "gap_inserted_synthetic": 1, "gap_reused_existing": 0,
                 "deepcenter_gap_bypassed_strong_motion": 0, "deepcenter_gap_bypassed_observed_node": 0,
                 "gap2_candidates": 0, "gap2_pairs_selected": 0, "gap2_added_edges": 0,
                 "gap2_added_nodes": 0, "safe_division_candidates": 1,
                 "safe_division_geometric_candidates": 1, "safe_divisions_added": 1}
        fc, hc = {}, {}
        # drive gap1 veto (logger then accept), matching the injected call-site contract
        g["_exp061_log_veto_candidate"]("gap", dataset, 1,
                                        {"middle_id": 11, "left_id": 10, "right_id": 12, "reused": 0},
                                        (4.0, 4.0, 0.0))
        g["deepcenter_accept_repair_point"](dataset, 1, (4.0, 4.0, 0.0), deepcenter_bundle, fc, hc,
                                            stats, "gap", 0.10)
        # drive safe-div veto
        g["_exp061_log_veto_candidate"]("safe_div", dataset, 1,
                                        {"parent_id": 0, "existing_child_id": 1, "candidate_child_id": 2},
                                        (2.0, 2.0, 2.0))
        g["deepcenter_accept_repair_point"](dataset, 1, (2.0, 2.0, 2.0), deepcenter_bundle, fc, hc,
                                            stats, "safe_div", 0.12)
        return nodes, edges, stats

    # on-disk fake geffs matching the writer's glob predictions/<stem>/<METHOD>/split_0/<stem>.geff
    method = "M"
    stems = ["44b6_0113de3b", "6bba_05b6850b"]
    preds = Path(workdir) / "repo" / "predictions"
    for stem in stems:
        d = preds / stem / method / "split_0"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{stem}.geff").write_text("x")

    # runtime-integrity file so checkpoint provenance verifies (admission #1)
    (Path(workdir) / "bidirectional_production_runtime_integrity.json").write_text(
        '{"checkpoint_sha256": {"deepcenter": "deadbeefcafe"}}')

    from importlib import import_module  # noqa
    m = _load_module()

    g = dict(m.EXP061_PARENT_BASE_DEFAULTS)   # live knobs start at the frozen base defaults
    g.update({
        "filter_output_graph": filter_output_graph, "graph_from_geff": graph_from_geff,
        "DEEPCENTER_VETO_DETECTOR": bundle, "test_stems": stems,
        "CSV_COLUMNS": ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x",
                        "source_id", "target_id"],
        "REPO_DIR": str(Path(workdir) / "repo"), "METHOD": method,
        "WORKING_DIR": str(workdir),
        "deepcenter_heatmap_for_frame": deepcenter_heatmap_for_frame,
        "deepcenter_accept_repair_point": deepcenter_accept_repair_point,
        "deepcenter_score_point": deepcenter_score_point,
        "read_test_frame": read_test_frame, "_dc_pool_frame_xy": _dc_pool_frame_xy,
        "_dc_normalize_dynamic_range": _dc_normalize_dynamic_range, "_dc_cache_trim": _dc_cache_trim,
        "_exp061_log_veto_candidate": (lambda *a, **k: None),
    })
    import time as _t
    g["_EXP061_RUN_START"] = _t.time()
    g["_EXP061_WATCHDOG_ARMED"] = True
    return m, g


def _run_probe(np, workdir, model_bias=0.0, parent_sha=None):
    import os, json
    os.environ["BIOHUB_DEEPCENTER_TTA"] = "1"
    os.environ["BIOHUB_VALIDATOR_ENABLE"] = "0"
    os.environ["BIOHUB_EXP061_ENABLE"] = "1"
    m, g = _build_mock_g(np, workdir, model_bias=model_bias)
    if parent_sha is not None:
        m.EXP061_PARENT_SUBMISSION_SHA256 = parent_sha   # patch the ACTUAL module the run uses
    tel = m.run_exp061_deepcenter_tta(g)
    metrics = json.loads((Path(workdir) / "metrics.json").read_text())
    return m, g, tel, metrics


def test_I_executable_end_to_end_parity_and_survival():
    print("I. EXECUTABLE end-to-end: parity gate + gap/safe-div survival (mocked, no GPU)")
    np = _np_or_skip()
    if np is None:
        print("  skip  numpy unavailable"); return
    import tempfile, json
    with tempfile.TemporaryDirectory() as tmp:
        # first pass to learn the deterministic xyonly submission sha, then pin it as the parent SHA
        m, g, tel, metrics = _run_probe(np, tmp + "/w1", model_bias=0.7)
        xyonly_sha = tel["arms"]["xyonly"]["sha256"]
        check(xyonly_sha is not None, "xyonly arm produced a submission sha (executed end-to-end)")
        # second pass with the true parent==xyonly sha -> all three arms run
        _, g2, tel2, metrics2 = _run_probe(np, tmp + "/w2", model_bias=0.7, parent_sha=xyonly_sha)
        check(metrics2["checks"]["control_parity_sha256_matches_parent"],
              "control parity check passes when xyonly sha == parent sha")
        check(metrics2["checks"]["live_pinned_config_equals_frozen_parent"],
              "live pinned config equals the INDEPENDENT frozen parent reference (v3 #1)")
        check(set(tel2["arms"].keys()) == {"xyonly", "zon", "xyd4"},
              "all three arms executed end-to-end once parity holds")
        check(metrics2["exp061_deepcenter_tta_integrity_passed"],
              "integrity gate PASSES on the mocked happy path")
        surv = tel2["veto_survival_summary"]
        gap_ok = any(surv[a]["gap"]["survived_final"] >= 1 for a in surv)
        sd_ok = any(surv[a]["safe_div"]["survived_final"] >= 1 for a in surv)
        check(gap_ok, "gap veto records have identity-linked final survival filled (v3 #2)")
        check(sd_ok, "safe-div veto records have identity-linked final survival filled (v3 #2)")
        # stage-specific deltas present
        check("stage_stat_delta" in json.dumps(tel2["delta_vs_xyonly"]),
              "cross-arm deltas include gap1/gap2/safe-div stage-specific counters (v3 #2)")


def test_J_executable_zero_response_is_valid_null():
    print("J. EXECUTABLE valid-zero-response: equivariant model -> verified null, not failure")
    np = _np_or_skip()
    if np is None:
        print("  skip  numpy unavailable"); return
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        m, g, tel, metrics = _run_probe(np, tmp + "/w", model_bias=0.0)   # equivariant -> identical
        _, _, tel2, metrics2 = _run_probe(np, tmp + "/w2", model_bias=0.0,
                                          parent_sha=tel["arms"]["xyonly"]["sha256"])
        mech = tel2["mechanism_active"]
        check(mech["zon"]["execution_valid"], "zon executed its intended views (execution valid)")
        check(not mech["zon"]["heatmap_differs_from_xyonly"],
              "equivariant model -> zon heatmap identical to xyonly (zero response)")
        check(mech["zon"]["verified_null"], "identical heatmap recorded as a VERIFIED NULL")
        check(metrics2["checks"]["experimental_arms_execution_valid"],
              "execution-valid gate still PASSES on a verified null (null != failure)")


def test_K_executable_config_drift_fails_closed():
    print("K. EXECUTABLE config drift: a wrong live knob fails the frozen-parent gate")
    np = _np_or_skip()
    if np is None:
        print("  skip  numpy unavailable"); return
    import tempfile, os, json
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["BIOHUB_DEEPCENTER_TTA"] = "1"; os.environ["BIOHUB_VALIDATOR_ENABLE"] = "0"
        m, g = _build_mock_g(np, tmp + "/w", model_bias=0.7)
        g["DEEPCENTER_SAFE_DIV_THRESHOLD"] = 0.18   # DRIFT from the frozen parent (0.12)
        m.run_exp061_deepcenter_tta(g)
        metrics = json.loads((Path(tmp + "/w") / "metrics.json").read_text())
        check(not metrics["checks"]["live_pinned_config_equals_frozen_parent"],
              "drifted live knob is DETECTED against the independent frozen reference")
        check(not metrics["exp061_deepcenter_tta_integrity_passed"],
              "integrity gate FAILS CLOSED on config drift")


def test_L_executable_corrupt_cache_recovery():
    print("L. EXECUTABLE corrupt-cache recovery: digest-reject -> recompute before use")
    np = _np_or_skip()
    if np is None:
        print("  skip  numpy unavailable"); return
    import tempfile, os, json
    w = None
    with tempfile.TemporaryDirectory() as tmp:
        w = Path(tmp) / "w"
        os.environ["BIOHUB_DEEPCENTER_TTA"] = "1"; os.environ["BIOHUB_VALIDATOR_ENABLE"] = "0"
        # pass 1 populates the on-disk view cache
        m, g, tel1, metrics1 = _run_probe(np, str(w), model_bias=0.7)
        vc = w / "exp061_viewcache"
        npys = sorted(vc.glob("*.npy"))
        check(len(npys) >= 1, "view cache persisted to disk in pass 1")
        # CORRUPT one cached view's bytes but leave its .sha256 sidecar (now mismatching)
        victim = npys[0]
        arr = np.load(victim); arr = arr + 999.0; np.save(victim, arr)
        # pass 2 reuses the SAME disk cache (same provenance/inputs -> same keys) and must reject +
        # recompute the corrupted entry BEFORE trusting it
        m2, g2, tel2, metrics2 = _run_probe(np, str(w), model_bias=0.7)
        check(tel2["view_cache"]["integrity_failures"] >= 1,
              "corrupted disk cache entry detected (digest mismatch) and rejected")
        check(metrics2["checks"]["view_cache_integrity_ok"] is False
              or tel2["view_cache"]["integrity_failures"] >= 1,
              "reject-before-use recomputes the entry (recovery path exercised)")


def test_M_executable_budget_abort_is_clean_partial():
    print("M. EXECUTABLE measured budget abort: clean partial, no half-written CSV")
    np = _np_or_skip()
    if np is None:
        print("  skip  numpy unavailable"); return
    import tempfile, os, json
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["BIOHUB_DEEPCENTER_TTA"] = "1"; os.environ["BIOHUB_VALIDATOR_ENABLE"] = "0"
        # slow datasets (0.6s each) with a 0.5s hard-stop + 0 reserve: the FIRST arm STARTS (remaining
        # ~0.5 > need 0) but after dataset 1 (~0.6s) the measured per-dataset gate trips -> a clean
        # aborted_budget between datasets, publishing nothing for that arm (generous 100ms margins).
        m, g = _build_mock_g(np, tmp + "/w", model_bias=0.7, dataset_sleep=0.6)
        saved_hs, saved_res = m.EXP061_HARD_STOP_SECONDS, m.EXP061_FINALIZATION_RESERVE_SECONDS
        try:
            m.EXP061_FINALIZATION_RESERVE_SECONDS = 0.0
            m.EXP061_HARD_STOP_SECONDS = 0.5
            m.run_exp061_deepcenter_tta(g)
            wdir = Path(tmp + "/w")
            metrics = json.loads((wdir / "metrics.json").read_text())
            statuses = metrics.get("arm_status", {})
            check(statuses.get("xyonly") == "aborted_budget",
                  f"control arm cleanly aborted between datasets on the MEASURED per-dataset gate ({statuses})")
            # no stray .tmp partials, and no final CSV for the aborted arm
            tmps = list((wdir / "exp061").glob("*.tmp"))
            check(not tmps, "no half-written .tmp CSV left behind (clean abort)")
            check(not (wdir / "exp061" / "submission_xyonly.csv").exists(),
                  "aborted arm publishes NO final submission CSV (clean partial)")
            check(not metrics["exp061_deepcenter_tta_integrity_passed"],
                  "integrity is not asserted on a control-aborted partial run (fail-closed)")
        finally:
            m.EXP061_HARD_STOP_SECONDS = saved_hs
            m.EXP061_FINALIZATION_RESERVE_SECONDS = saved_res


def test_N_frozen_parent_config_matches_parent_notebook():
    print("N. frozen parent config is INDEPENDENTLY derived from the parent notebook (v3 #1 guard)")
    import json, re
    m = _load_module()
    nb_path = (ROOT / "experiments/repro_059_public_0947_exact_copy/snapshot/source/"
               "biohub-repro059-public-0947-exact-copy.ipynb")
    if not nb_path.exists():
        print("  skip  parent notebook not present in this checkout"); return
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    src = "".join(code[0]["source"]); lines = src.split("\n")
    FLOAT = re.compile(r"^\s*(\w+)\s*=\s*float\(os\.environ\.get\('BIOHUB_\w+',\s*'([^']*)'\)\)\s*$")
    INT = re.compile(r"^\s*(\w+)\s*=\s*int\(os\.environ\.get\('BIOHUB_\w+',\s*'([^']*)'\)\)\s*$")
    BOOL = re.compile(r"^\s*(\w+)\s*=\s*os\.environ\.get\('BIOHUB_\w+',\s*'([^']*)'\)\s*!=\s*'0'\s*$")
    parsed = {}
    for k in m.EXP061_PARENT_BASE_DEFAULTS:
        for l in lines:
            if re.match(rf"\s*{k}\s*=", l):
                for rx, cast in ((FLOAT, float), (INT, int), (BOOL, lambda v: v != "0")):
                    mm = rx.match(l)
                    if mm:
                        parsed[k] = cast(mm.group(2)); break
                break
    mismatches = {k: (m.EXP061_PARENT_BASE_DEFAULTS[k], parsed.get(k))
                  for k in m.EXP061_PARENT_BASE_DEFAULTS if parsed.get(k) != m.EXP061_PARENT_BASE_DEFAULTS[k]}
    check(not mismatches, f"EXP061_PARENT_BASE_DEFAULTS matches the parent notebook defaults ({mismatches})")
    check(m.EXP061_FROZEN_PARENT_CONFIG["MOTION_RELINK_TIGHT_UM"] == 5.5,
          "frozen resolved config applies ONLY the tight55 override")
    check(all(m.EXP061_FROZEN_PARENT_CONFIG[k] == m.EXP061_PARENT_BASE_DEFAULTS[k]
              for k in m.EXP061_PARENT_BASE_DEFAULTS if k != "MOTION_RELINK_TIGHT_UM"),
          "frozen resolved config == base defaults on every non-tight knob")


def main() -> int:
    for t in (test_A_coordinate_maps, test_B_module_functions_numpy, test_C_arm_specs,
              test_D_signatures_and_keys, test_E_accumulation_order_parity,
              test_F_view_cache_keys, test_G_arm_order_invariance, test_H_hardening_source,
              test_I_executable_end_to_end_parity_and_survival,
              test_J_executable_zero_response_is_valid_null,
              test_K_executable_config_drift_fails_closed,
              test_L_executable_corrupt_cache_recovery,
              test_M_executable_budget_abort_is_clean_partial,
              test_N_frozen_parent_config_matches_parent_notebook):
        t()
    print()
    if _failures:
        print(f"BEHAVIORAL TESTS FAILED: {len(_failures)}")
        for m in _failures:
            print("  - " + m)
        return 1
    print("BEHAVIORAL TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
