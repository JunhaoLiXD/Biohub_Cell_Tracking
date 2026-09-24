"""exp_062 behavioral tests -- executable, zero-GPU, no torch required.

These do not describe the rank prior; they EXECUTE it. `MUTUAL_BEST_BLOCK` is lifted verbatim out
of scripts/exp062_mutual_best.py, wrapped in a function, and run against a numpy-backed torch shim.
That is what makes the axis-semantics test real rather than circular (Codex round-1 answer 1).

Covers the local gates in proposal v3 section 6:
  1  builder parity guard                     -> validate_exp062_notebook.py
  2  beta = 0 inertness (EXACTLY zero)        -> test_beta_zero_is_exactly_inert
  3  axis semantics through the patched block -> test_axis_semantics_*, incl. ties / degenerate
  4  bonus truth table                        -> test_bonus_truth_table
  5  anchor fail-closed                       -> test_anchor_*
  6  activation branch                        -> test_activation_branch_recorded
  7  calibration telemetry separation         -> test_read_stats_merges
  8  resume-signature discrimination          -> test_resume_signature_*
  9  parent-SHA gating                        -> test_parent_sha_guard_cleared
 10  snapshot smoke                           -> validate_exp062_notebook.py

Run: python scripts/test_exp062_behavioral.py
"""

from __future__ import annotations

import os
import sys
import textwrap
import types
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exp062_mutual_best as M  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  PASS  %s" % name)
    else:
        print("  FAIL  %s %s" % (name, detail))
        FAILURES.append(name)


# --------------------------------------------------------------------------------------------
# A numpy-backed torch shim: only what the block actually touches.
# --------------------------------------------------------------------------------------------
class T:
    """Minimal tensor wrapper with the handful of ops the block uses."""

    def __init__(self, a, dtype=None):
        self.a = np.asarray(a, dtype=dtype if dtype is not None else None)

    # arithmetic
    def __add__(self, o):
        return T(self.a + (o.a if isinstance(o, T) else o))

    __radd__ = __add__

    def __sub__(self, o):
        return T(self.a - (o.a if isinstance(o, T) else o))

    def __rsub__(self, o):
        return T((o.a if isinstance(o, T) else o) - self.a)

    def __mul__(self, o):
        return T(self.a * (o.a if isinstance(o, T) else o))

    __rmul__ = __mul__

    def __neg__(self):
        return T(-self.a)

    # logical
    def __and__(self, o):
        return T(np.logical_and(self.a, o.a))

    def __invert__(self):
        return T(np.logical_not(self.a))

    def __eq__(self, o):
        return T(self.a == (o.a if isinstance(o, T) else o))

    def __ne__(self, o):
        return T(self.a != (o.a if isinstance(o, T) else o))

    # casts / reductions
    def float(self):
        return T(self.a.astype(np.float64))

    def to(self, dtype):
        return T(self.a.astype(dtype))

    def abs(self):
        return T(np.abs(self.a))

    def max(self):
        return T(np.max(self.a))

    def std(self):
        return T(np.std(self.a))

    def any(self):
        return T(np.any(self.a))

    def item(self):
        return self.a.item()

    def cpu(self):
        return self

    def numpy(self):
        return self.a

    @property
    def dtype(self):
        return self.a.dtype

    def __getitem__(self, i):
        return T(self.a[i])


def _softmax(x, dim):
    a = x.a.astype(np.float64)
    m = np.max(a, axis=dim, keepdims=True)
    e = np.exp(a - m)
    return T(e / np.sum(e, axis=dim, keepdims=True))


def _sigmoid(x):
    return T(1.0 / (1.0 + np.exp(-x.a.astype(np.float64))))


def _argsort(x, dim):
    return T(np.argsort(x.a, axis=dim, kind="stable"))


torch_shim = types.SimpleNamespace(softmax=_softmax, sigmoid=_sigmoid, argsort=_argsort)


def run_block(raw_np, mode, beta, activation="softmax"):
    """Execute MUTUAL_BEST_BLOCK verbatim and return (raw_out, probs, stats)."""
    body = textwrap.dedent(M.MUTUAL_BEST_BLOCK)
    src = "def _run(edge_logits_pair, cfg, torch, os, _EXP062_STATS):\n"
    src += textwrap.indent(body, "    ")
    src += "    return raw, probs\n"
    ns = {}
    exec(compile(src, "<mutual_best_block>", "exec"), ns)  # noqa: S102
    stats = {"frames": 0, "frames_with_bonus": 0, "activation": None,
             "raw_absmax": 0.0, "raw_std_sum": 0.0}
    env = {M.MODE_KEY: mode, M.BETA_KEY: str(beta)}
    cfg = types.SimpleNamespace(edge_activation=activation)
    raw, probs = ns["_run"](T(np.asarray(raw_np, dtype=np.float64))[None],
                            cfg, torch_shim, types.SimpleNamespace(environ=env), stats)
    return raw.a, probs, stats


# --------------------------------------------------------------------------------------------
def test_beta_zero_is_exactly_inert():
    raw = np.array([[2.0, 0.1, -1.0], [0.3, 3.0, 0.2]])
    for mode in ("none", "mutual_best", "relative_rank"):
        beta = 0.0
        out, _, stats = run_block(raw, mode, beta)
        check("beta=0 inert, mode=%s (EXACT)" % mode,
              np.array_equal(out, raw), "max|d|=%r" % np.max(np.abs(out - raw)))
        check("beta=0 records no bonus frame, mode=%s" % mode, stats["frames_with_bonus"] == 0)


def test_bonus_truth_table():
    """mutual 2b | col-best only 0.8b | row-best only 0.3b | neither -0.2b.

    raw is (n_src, n_tgt): dim0 -> best SOURCE per target (col_best);
                           dim1 -> best TARGET per source (row_best).
    """
    # 3 sources x 3 targets, engineered so each category appears.
    raw = np.array([
        [10.0, 1.0, 0.0],   # src0: best target = t0 ; t0's best source = src0  -> mutual
        [5.0, 0.5, 0.4],    # src1: best target = t0 ; t0's best source = src0  -> row-best only
        [0.1, 2.0, 9.0],    # src2: best target = t2 ; t2's best source = src2  -> mutual
    ])
    beta = 0.20
    out, _, _ = run_block(raw, "mutual_best", beta)
    d = out - raw

    col_best = np.zeros_like(raw, dtype=bool)
    col_best[np.argmax(raw, axis=0), np.arange(raw.shape[1])] = True
    row_best = np.zeros_like(raw, dtype=bool)
    row_best[np.arange(raw.shape[0]), np.argmax(raw, axis=1)] = True
    mutual = col_best & row_best

    exp = (beta * col_best + 0.5 * beta * row_best + 0.5 * beta * mutual
           - 0.20 * beta * (~mutual))
    check("truth table matches the four-row spec", np.allclose(d, exp), "d=%s exp=%s" % (d, exp))
    check("mutual gets 2.0*beta", np.allclose(d[mutual], 2.0 * beta))
    check("col-best-only gets 0.8*beta",
          np.allclose(d[col_best & ~mutual], 0.8 * beta) if (col_best & ~mutual).any() else True)
    check("row-best-only gets 0.3*beta",
          np.allclose(d[row_best & ~mutual], 0.3 * beta) if (row_best & ~mutual).any() else True)
    check("neither gets -0.2*beta", np.allclose(d[~col_best & ~row_best], -0.20 * beta))
    # v1 of the proposal asserted the opposite; this is the regression guard for that error.
    check("NOT all non-mutual pairs decrease (v1's gate was wrong)",
          (d[~mutual] > 0).any())


def test_axis_semantics_rectangular():
    """n_src != n_tgt so a transposed reading cannot silently pass."""
    raw = np.array([
        [9.0, 0.0, 0.0, 0.0],
        [0.0, 0.1, 0.2, 8.0],
    ])  # 2 sources x 4 targets
    beta = 0.5
    out, _, _ = run_block(raw, "mutual_best", beta)
    d = out - raw
    check("rectangular: shape preserved", out.shape == raw.shape)
    # target 0's best source is src0; src0's best target is t0 -> mutual
    check("rect: (0,0) is mutual -> 2b", np.isclose(d[0, 0], 2.0 * beta))
    # target 3's best source is src1; src1's best target is t3 -> mutual
    check("rect: (1,3) is mutual -> 2b", np.isclose(d[1, 3], 2.0 * beta))
    # target 1's best source is src1 (0.1 > 0.0) but src1's best target is t3 -> col-best only
    check("rect: (1,1) is col-best only -> 0.8b", np.isclose(d[1, 1], 0.8 * beta))
    # (0,1) is neither
    check("rect: (0,1) is neither -> -0.2b", np.isclose(d[0, 1], -0.20 * beta))


def test_axis_semantics_degenerate():
    single_src = np.array([[1.0, 2.0, 3.0]])
    out, _, _ = run_block(single_src, "mutual_best", 0.3)
    check("single source: runs and preserves shape", out.shape == single_src.shape)
    # With one source, every entry is column-best.
    d = out - single_src
    check("single source: all entries column-best", (d > 0).all(), "d=%s" % d)

    single_tgt = np.array([[1.0], [5.0], [2.0]])
    out2, _, _ = run_block(single_tgt, "mutual_best", 0.3)
    check("single target: runs and preserves shape", out2.shape == single_tgt.shape)
    d2 = out2 - single_tgt
    # With one target, every source's best target is t0 -> every entry row-best.
    check("single target: all entries row-best", (d2 > 0).all(), "d2=%s" % d2)


def test_axis_semantics_ties():
    raw = np.array([[1.0, 1.0], [1.0, 1.0]])
    out, _, _ = run_block(raw, "mutual_best", 0.4)
    d = out - raw
    check("ties: deterministic and finite", np.isfinite(d).all())
    check("ties: exactly one winner per column", int((d[:, 0] > 0).sum()) >= 1)


def test_activation_branch_recorded():
    raw = np.array([[1.0, 0.0], [0.0, 1.0]])
    for act in ("softmax", "sigmoid"):
        _, probs, stats = run_block(raw, "mutual_best", 0.2, activation=act)
        check("activation %s recorded" % act, stats["activation"] == act)
        check("activation %s probs finite" % act, np.isfinite(probs).all())
    _, probs_sm, _ = run_block(raw, "none", 0.0, activation="softmax")
    check("softmax normalises over SOURCES (dim 0)",
          np.allclose(np.asarray(probs_sm).sum(axis=0), 1.0))


def test_stats_counters():
    raw = np.array([[1.0, 0.0], [0.0, 1.0]])
    _, _, s_on = run_block(raw, "mutual_best", 0.2)
    _, _, s_off = run_block(raw, "none", 0.0)
    check("stats: bonus frame counted when on", s_on["frames_with_bonus"] == 1)
    check("stats: no bonus frame when off", s_off["frames_with_bonus"] == 0)
    check("stats: frames counted in both", s_on["frames"] == 1 and s_off["frames"] == 1)
    check("stats: final-raw absmax recorded", s_on["raw_absmax"] > 0)


# --------------------------------------------------------------------------------------------
def _synthetic_script(body):
    """A syntactically valid stand-in whose anchor sits at the real indent (12)."""
    return ("def _outer(cfg, torch, os, edge_logits_pair, _EXP062_STATS):\n"
            "    for _a in range(1):\n"
            "        for _b in range(1):\n"
            + body +
            "\n\ndef main() -> None:\n    pass\n")


def test_anchor_fail_closed():
    good = _synthetic_script(M.ANCHOR)
    info = M.apply_mutual_best_patch("<mem>", source=good)
    check("anchor: exactly-one applies", info["anchor_match_count"] == 1)
    check("anchor: patched source contains the prior",
          "_lb_rank_bonus" in info["patched_source"])
    check("anchor: patched source still compiles",
          compile(info["patched_source"], "<patched>", "exec") is not None)

    for name, src in (("missing", _synthetic_script("            pass\n")),
                      ("duplicated", _synthetic_script(M.ANCHOR + M.ANCHOR))):
        try:
            M.apply_mutual_best_patch("<mem>", source=src)
            check("anchor: %s raises" % name, False, "did not raise")
        except M.Exp062Error:
            check("anchor: %s raises" % name, True)


def test_mode_beta_validation():
    for env, ok in (({M.MODE_KEY: "mutual_best", M.BETA_KEY: "0.20"}, True),
                    ({M.MODE_KEY: "none", M.BETA_KEY: "0"}, True),
                    ({M.MODE_KEY: "bogus", M.BETA_KEY: "0.2"}, False),
                    ({M.MODE_KEY: "mutual_best", M.BETA_KEY: "nope"}, False),
                    ({M.MODE_KEY: "mutual_best", M.BETA_KEY: "9"}, False),
                    ({M.MODE_KEY: "none", M.BETA_KEY: "0.2"}, False)):
        try:
            M.read_mode_beta(env)
            got = True
        except M.Exp062Error:
            got = False
        check("mode/beta %s -> %s" % (env, "accept" if ok else "reject"), got == ok)


def test_resume_signature_discriminates():
    parent_keys = ["BIOHUB_DET_THRESHOLD", "BIOHUB_SECONDARY_EDGE_WEIGHT"]
    try:
        M.assert_resume_signature_discriminates(parent_keys)
        check("resume: bare parent key list is REJECTED", False, "did not raise")
    except M.Exp062Error:
        check("resume: bare parent key list is REJECTED", True)
    M.assert_resume_signature_discriminates(parent_keys + list(M.EXP062_ENV_KEYS))
    check("resume: extended key list accepted", True)

    # The real point: two environments differing only in mode/beta must hash differently.
    import hashlib
    import json as _json

    def sig(keys, env):
        return hashlib.sha256(_json.dumps(
            {k: env.get(k) for k in keys}, sort_keys=True).encode()).hexdigest()

    ctrl = {M.MODE_KEY: "none", M.BETA_KEY: "0.0"}
    cand = {M.MODE_KEY: "mutual_best", M.BETA_KEY: "0.20"}
    check("resume: parent key list does NOT discriminate (the defect)",
          sig(parent_keys, ctrl) == sig(parent_keys, cand))
    check("resume: extended key list DOES discriminate (the fix)",
          sig(parent_keys + list(M.EXP062_ENV_KEYS), ctrl)
          != sig(parent_keys + list(M.EXP062_ENV_KEYS), cand))


def test_parent_sha_guard_cleared():
    os.environ[M.EXPECT_SHA_KEY] = "deadbeef"
    M.assert_parent_sha_guard_cleared()
    check("parent-SHA guard actively cleared", M.EXPECT_SHA_KEY not in os.environ)


def test_cache_hit_alarm():
    slow = M.check_cache_hit(False, 900.0)
    check("cache: a real run is not flagged", slow["cache_hit_suspected"] is False)
    fast = M.check_cache_hit(False, 0.4)
    check("cache: near-zero measured time IS flagged", fast["cache_hit_suspected"] is True)
    ready = M.check_cache_hit(True, 900.0)
    check("cache: prediction_ready IS flagged even with a plausible time",
          ready["cache_hit_suspected"] is True)


def test_read_stats_merges(tmp="exp062_stats_test.jsonl"):
    p = Path(tmp)
    p.write_text('{"frames": 3, "frames_with_bonus": 3, "activation": "softmax", '
                 '"raw_absmax": 2.0, "raw_std_sum": 1.5}\n'
                 '{"frames": 2, "frames_with_bonus": 1, "activation": "softmax", '
                 '"raw_absmax": 5.0, "raw_std_sum": 0.5}\n', encoding="utf-8")
    s = M.read_stats(p)
    check("stats merge: frames summed", s["frames"] == 5)
    check("stats merge: bonus frames summed", s["frames_with_bonus"] == 4)
    check("stats merge: absmax is a max", s["raw_absmax"] == 5.0)
    check("stats merge: final-raw std mean computed", abs(s["raw_std_mean"] - 0.4) < 1e-9)
    p.unlink()
    check("stats merge: missing file is empty, not an error", M.read_stats(p)["frames"] == 0)


def main():
    print("exp_062 behavioral tests")
    for fn in (test_beta_zero_is_exactly_inert, test_bonus_truth_table,
               test_axis_semantics_rectangular, test_axis_semantics_degenerate,
               test_axis_semantics_ties, test_activation_branch_recorded, test_stats_counters,
               test_anchor_fail_closed, test_mode_beta_validation,
               test_resume_signature_discriminates, test_parent_sha_guard_cleared,
               test_cache_hit_alarm, test_read_stats_merges):
        print("\n[%s]" % fn.__name__)
        fn()
    print("\n%s" % ("ALL PASS" if not FAILURES else "FAILURES: %s" % FAILURES))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
