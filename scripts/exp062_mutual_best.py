"""exp_062 runtime: mutual-best edge-association rank prior on the frozen 0.947 pipeline.

Strategy record: docs/research/exp062_mutual_best_edge_association_proposal_v3.md (v3, CONSENSUS;
Codex PASS 2026-09-24, docs/research/exp062_codex_challenge_v3.md).

This module is appended verbatim into the built notebook as a cell. It does four things and
nothing else:

  1. `apply_mutual_best_patch` -- inserts the rank-prior block into the ALREADY-PARENT-PATCHED
     `predict_unet_transformer.py`, FAIL-CLOSED on any anchor count != 1.
  2. `assert_resume_signature_discriminates` -- proves the parent's resume signature now includes
     the exp_062 environment keys, so a candidate run cannot replay control predictions.
  3. `check_cache_hit` -- cache-hit alarm on MEASURED wall-clock, never the reported value.
  4. `finalize` -- writes gated metrics.json + exp062_telemetry.json.

The prior itself (bonus truth table, beta) is byte-identical to the published form; see
`MUTUAL_BEST_BLOCK`.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

EXPERIMENT_ID = "exp_062_mutual_best_edge_association"
PARENT_SUBMISSION_SHA256 = "d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60"

# Environment contract -------------------------------------------------------------------------
MODE_KEY = "BIOHUB_LB_SCORING_MODE"
BETA_KEY = "BIOHUB_LB_SCORING_BETA"
EXPECT_SHA_KEY = "BIOHUB_EXP062_EXPECT_PARENT_SHA"
STATS_PATH_KEY = "BIOHUB_EXP062_STATS_PATH"
EXP062_ENV_KEYS = (MODE_KEY, BETA_KEY)
VALID_MODES = ("none", "relative_rank", "mutual_best")

# The anchor, as it stands in the parent-patched predict script: the final `raw` assignment
# followed by the activation branch. Verified unique both pristine and after the parent's own
# patch chain (validate_exp062_notebook.py replays that chain and re-asserts uniqueness).
ANCHOR = (
    '            raw = edge_logits_pair[0]\n'
    '            if cfg.edge_activation == "softmax":\n'
    '                probs = torch.softmax(raw, dim=0).cpu().numpy()\n'
    '            else:\n'
    '                probs = torch.sigmoid(raw).cpu().numpy()\n'
)

# Published form, unaltered. Bonus truth table:
#   mutual 2.0*beta | column-best only 0.8*beta | row-best only 0.3*beta | neither -0.2*beta
# `raw` is (n_src, n_tgt): dim 0 reduces SOURCES (best source per target = _lb_col_best);
# dim 1 reduces TARGETS (best target per source = _lb_row_best).
MUTUAL_BEST_BLOCK = (
    '            raw = edge_logits_pair[0]\n'
    '            _lb_mode = os.environ.get("BIOHUB_LB_SCORING_MODE", "none")\n'
    '            _lb_beta = float(os.environ.get("BIOHUB_LB_SCORING_BETA", "0"))\n'
    '            _lb_applied = 0\n'
    '            if _lb_mode in {"relative_rank", "mutual_best"}:\n'
    '                _lb_col_prob = torch.softmax(raw.float(), dim=0)\n'
    '                _lb_row_prob = torch.softmax(raw.float(), dim=1)\n'
    '                _lb_col_best = torch.argsort(torch.argsort(-_lb_col_prob, dim=0), dim=0) == 0\n'
    '                _lb_row_best = torch.argsort(torch.argsort(-_lb_row_prob, dim=1), dim=1) == 0\n'
    '                _lb_mutual = _lb_col_best & _lb_row_best\n'
    '                _lb_rank_bonus = (\n'
    '                    _lb_beta * _lb_col_best.float()\n'
    '                    + 0.50 * _lb_beta * _lb_row_best.float()\n'
    '                    + 0.50 * _lb_beta * _lb_mutual.float()\n'
    '                )\n'
    '                if _lb_mode == "mutual_best":\n'
    '                    _lb_rank_bonus = _lb_rank_bonus - 0.20 * _lb_beta * (~_lb_mutual).float()\n'
    '                raw = raw + _lb_rank_bonus.to(raw.dtype)\n'
    '                _lb_applied = int((_lb_rank_bonus != 0).any().item())\n'
    '            _EXP062_STATS["frames"] += 1\n'
    '            _EXP062_STATS["frames_with_bonus"] += _lb_applied\n'
    '            _EXP062_STATS["activation"] = cfg.edge_activation\n'
    '            _EXP062_STATS["raw_absmax"] = max(_EXP062_STATS["raw_absmax"], float(raw.abs().max().item()))\n'
    '            _EXP062_STATS["raw_std_sum"] += float(raw.float().std().item())\n'
    '            if cfg.edge_activation == "softmax":\n'
    '                probs = torch.softmax(raw, dim=0).cpu().numpy()\n'
    '            else:\n'
    '                probs = torch.sigmoid(raw).cpu().numpy()\n'
)

# Module-level counters the injected block writes into, plus their dump hook. Final-`raw`
# statistics are kept DISTINCT from the parent's intermediate forward_scale/blend_weight, because
# beta acts on final `raw` and conflating the two was the defect Codex found in proposal v2.
STATS_PREAMBLE = (
    '_EXP062_STATS = {"frames": 0, "frames_with_bonus": 0, "activation": None,\n'
    '                 "raw_absmax": 0.0, "raw_std_sum": 0.0}\n'
    'import atexit as _exp062_atexit, json as _exp062_json, os as _exp062_os\n'
    'def _exp062_dump_stats():\n'
    '    _p = _exp062_os.environ.get("BIOHUB_EXP062_STATS_PATH")\n'
    '    if not _p:\n'
    '        return\n'
    '    try:\n'
    '        with open(_p, "a") as _f:\n'
    '            _f.write(_exp062_json.dumps(_EXP062_STATS) + chr(10))\n'
    '    except Exception:\n'
    '        pass\n'
    '_exp062_atexit.register(_exp062_dump_stats)\n'
)

STATS_ANCHOR = "def main() -> None:\n"


class Exp062Error(RuntimeError):
    """Fail-closed error. Never caught inside this module."""


def read_mode_beta(environ=None):
    env = os.environ if environ is None else environ
    mode = env.get(MODE_KEY, "none")
    if mode not in VALID_MODES:
        raise Exp062Error("%s=%r is not one of %s" % (MODE_KEY, mode, VALID_MODES))
    try:
        beta = float(env.get(BETA_KEY, "0"))
    except ValueError as exc:
        raise Exp062Error("%s=%r is not a float" % (BETA_KEY, env.get(BETA_KEY))) from exc
    if not (0.0 <= beta <= 1.0):
        raise Exp062Error("%s=%s outside the sane range [0, 1]" % (BETA_KEY, beta))
    if mode == "none" and beta != 0.0:
        raise Exp062Error("mode 'none' requires beta 0, got %s" % beta)
    return mode, beta


def apply_mutual_best_patch(script_path, source=None):
    """Insert the rank prior. FAIL-CLOSED: anchor must appear exactly once.

    Returns provenance for telemetry. Never silently no-ops -- that is the exp_061 admission v1 #2
    'false verified-null' defect this project has already been bitten by.
    """
    path = Path(script_path)
    text = path.read_text(encoding="utf-8") if source is None else source

    n = text.count(ANCHOR)
    if n != 1:
        raise Exp062Error(
            "exp_062 anchor matched %d times in %s (expected exactly 1). Refusing to run: an "
            "unpatched run would masquerade as a null result." % (n, path)
        )
    patched = text.replace(ANCHOR, MUTUAL_BEST_BLOCK, 1)

    m = patched.count(STATS_ANCHOR)
    if m != 1:
        raise Exp062Error("exp_062 stats anchor matched %d times (expected exactly 1)" % m)
    patched = patched.replace(STATS_ANCHOR, STATS_PREAMBLE + "\n\n" + STATS_ANCHOR, 1)

    compile(patched, str(path), "exec")
    if source is None:
        path.write_text(patched, encoding="utf-8")
    return {
        "anchor_match_count": n,
        "patched_region_sha256": hashlib.sha256(MUTUAL_BEST_BLOCK.encode("utf-8")).hexdigest(),
        "patched_script_sha256": hashlib.sha256(patched.encode("utf-8")).hexdigest(),
        "patched_script": str(path),
        "patched_source": patched if source is not None else None,
    }


def assert_resume_signature_discriminates(resume_env_keys):
    """The defect Codex found in round 2, closed.

    The parent's `_inference_resume_env_keys` is a fixed 13-key list that contains neither exp_062
    variable, while `_test_prediction_signature` hashes exactly those keys. Without this, a
    candidate run computes the SAME signature as the control, skips inference and replays the
    control's predictions with every other gate green.
    """
    missing = [k for k in EXP062_ENV_KEYS if k not in resume_env_keys]
    if missing:
        raise Exp062Error(
            "resume signature does not include %s; a candidate run could replay control "
            "predictions from cache. Refusing to run." % missing
        )


def assert_parent_sha_guard_cleared():
    """Candidate mode actively clears the historical-output guard, then proves it is gone.

    Source-level absence does not establish process-environment absence (Codex round 2).
    """
    os.environ.pop(EXPECT_SHA_KEY, None)
    if EXPECT_SHA_KEY in os.environ:
        raise Exp062Error("%s still set in candidate mode" % EXPECT_SHA_KEY)


def check_cache_hit(prediction_ready, measured_seconds, min_seconds=60.0):
    """Cache-hit alarm on MEASURED wall-clock.

    Parent line 1675 restores the historical `predict_seconds` from cached state on a hit, so the
    REPORTED time looks normal. Only an independently measured elapsed time is trustworthy.
    """
    hit = bool(prediction_ready) or float(measured_seconds) < float(min_seconds)
    return {
        "test_prediction_ready": bool(prediction_ready),
        "measured_inference_seconds": float(measured_seconds),
        "min_plausible_seconds": float(min_seconds),
        "cache_hit_suspected": bool(hit),
    }


def read_stats(stats_path):
    """Merge the per-subprocess stats lines the injected block appended."""
    merged = {"frames": 0, "frames_with_bonus": 0, "activation": None,
              "raw_absmax": 0.0, "raw_std_sum": 0.0, "stats_records": 0}
    p = Path(stats_path)
    if not p.is_file():
        return merged
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        merged["stats_records"] += 1
        merged["frames"] += int(rec.get("frames", 0))
        merged["frames_with_bonus"] += int(rec.get("frames_with_bonus", 0))
        merged["raw_absmax"] = max(merged["raw_absmax"], float(rec.get("raw_absmax", 0.0)))
        merged["raw_std_sum"] += float(rec.get("raw_std_sum", 0.0))
        if rec.get("activation"):
            merged["activation"] = rec["activation"]
    if merged["frames"]:
        merged["raw_std_mean"] = merged["raw_std_sum"] / merged["frames"]
    return merged


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def finalize(working_dir, telemetry, submission_path=None):
    """Write gated metrics.json + telemetry. The gate is fail-closed on every check."""
    working = Path(working_dir)
    mode, beta = read_mode_beta()

    sub_sha = None
    if submission_path and Path(submission_path).is_file():
        sub_sha = sha256_file(submission_path)

    telemetry = dict(telemetry)
    telemetry.update({
        "experiment": EXPERIMENT_ID,
        "parent": "repro_059_public_0947_exact_copy",
        "mode": mode,
        "beta": beta,
        "submission_sha256": sub_sha,
        "parent_submission_sha256": PARENT_SUBMISSION_SHA256,
        "submission_equals_parent": (sub_sha == PARENT_SUBMISSION_SHA256) if sub_sha else None,
    })

    expect_sha = os.environ.get(EXPECT_SHA_KEY)
    frames_with_bonus = int(telemetry.get("frames_with_bonus", 0))
    checks = {
        "mode_beta_valid": True,
        "patch_applied_exactly_once": telemetry.get("anchor_match_count") == 1,
        "resume_signature_includes_exp062_keys": bool(
            telemetry.get("resume_signature_inputs_include_exp062_keys")),
        "no_cache_hit": not telemetry.get("cache_hit_suspected", True),
        "submission_written": sub_sha is not None,
        "activation_is_softmax": telemetry.get("activation") == "softmax",
        "bonus_applied_iff_mode_on": (
            (frames_with_bonus > 0) if mode != "none" else (frames_with_bonus == 0)
        ),
    }
    if expect_sha:
        # Control variant only: historical public-output equality. Never armed in candidate mode,
        # because a hidden rerun operates on different input data.
        checks["control_reproduces_parent_submission"] = (sub_sha == expect_sha)

    passed = all(checks.values())
    telemetry["checks"] = checks
    telemetry["integrity_passed"] = passed

    (working / "exp062_telemetry.json").write_text(
        json.dumps(telemetry, indent=2, sort_keys=True), encoding="utf-8")

    metrics = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "validation": {"protocol": "public_0947_mutual_best_edge_association_v1"},
        "runtime_seconds": float(telemetry.get("runtime_seconds", 0.0)),
        "reproducible": False,
        "primary_metric": 1.0 if passed else 0.0,
        "primary_metric_meaning": "deployment integrity; no quality inference",
        "exp062_mutual_best_integrity_passed": passed,
        "checks": checks,
        "mode": mode,
        "beta": beta,
        "submission_sha256": sub_sha,
    }
    (working / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")

    if not passed:
        raise Exp062Error("exp_062 integrity gate FAILED: %s" % checks)
    return metrics
