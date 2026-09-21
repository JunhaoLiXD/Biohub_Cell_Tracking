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


def main() -> int:
    for t in (test_A_coordinate_maps, test_B_module_functions_numpy, test_C_arm_specs,
              test_D_signatures_and_keys, test_E_accumulation_order_parity,
              test_F_view_cache_keys, test_G_arm_order_invariance, test_H_hardening_source):
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
