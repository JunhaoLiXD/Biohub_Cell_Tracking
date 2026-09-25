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
import math
import os
from pathlib import Path

EXPERIMENT_ID = "exp_062_mutual_best_edge_association"
PARENT_SUBMISSION_SHA256 = "d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60"

# Environment contract -------------------------------------------------------------------------
MODE_KEY = "BIOHUB_LB_SCORING_MODE"
BETA_KEY = "BIOHUB_LB_SCORING_BETA"
EXPECT_SHA_KEY = "BIOHUB_EXP062_EXPECT_PARENT_SHA"
STATS_PATH_KEY = "BIOHUB_EXP062_STATS_PATH"
RUN_ID_KEY = "BIOHUB_EXP062_RUN_ID"
STAGE_KEY = "BIOHUB_EXP062_STAGE"
EXP062_ENV_KEYS = (MODE_KEY, BETA_KEY)

# Every stats record must carry all of these; a missing field is rejected, never defaulted.
REQUIRED_STAT_FIELDS = ("frames", "frames_with_bonus", "activation", "raw_absmax", "raw_std_sum",
                        "pre_raw_absmax", "pre_raw_std_sum", "run_id", "mode", "beta", "shard",
                        "pid", "stage")
NUMERIC_STAT_FIELDS = ("frames", "frames_with_bonus", "raw_absmax", "raw_std_sum",
                       "pre_raw_absmax", "pre_raw_std_sum")
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
    '            _lb_pre_std = float(raw.float().std().item())\n'
    '            _lb_pre_absmax = float(raw.abs().max().item())\n'
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
    '            _EXP062_STATS["pre_raw_std_sum"] += _lb_pre_std\n'
    '            _EXP062_STATS["pre_raw_absmax"] = max(_EXP062_STATS["pre_raw_absmax"], _lb_pre_absmax)\n'
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
    '                 "raw_absmax": 0.0, "raw_std_sum": 0.0,\n'
    '                 "pre_raw_absmax": 0.0, "pre_raw_std_sum": 0.0}\n'
    'import atexit as _exp062_atexit, json as _exp062_json, os as _exp062_os\n'
    'def _exp062_dump_stats():\n'
    '    _p = _exp062_os.environ.get("BIOHUB_EXP062_STATS_PATH")\n'
    '    if not _p:\n'
    '        return\n'
    '    _rec = dict(_EXP062_STATS)\n'
    '    _rec["run_id"] = _exp062_os.environ.get("BIOHUB_EXP062_RUN_ID", "")\n'
    '    _rec["mode"] = _exp062_os.environ.get("BIOHUB_LB_SCORING_MODE", "none")\n'
    '    _rec["beta"] = _exp062_os.environ.get("BIOHUB_LB_SCORING_BETA", "0")\n'
    '    _rec["shard"] = _exp062_os.environ.get("BIOHUB_GPU_SHARD", "single")\n'
    '    _rec["stage"] = _exp062_os.environ.get("BIOHUB_EXP062_STAGE", "unknown")\n'
    '    _rec["pid"] = _exp062_os.getpid()\n'
    '    with open(_p, "a") as _f:\n'
    '        _f.write(_exp062_json.dumps(_rec, sort_keys=True) + chr(10))\n'
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


def reset_stats(stats_path, run_id):
    """Truncate the stats file and bind this run's id.

    Without this, records from an EARLIER run (or the other kernel version) persist in the file
    and can satisfy the aggregate execution checks -- stale evidence passing as fresh. That is the
    same fail-open class as the resume-cache defect, so it is closed the same way: at the source.
    """
    p = Path(stats_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        p.unlink()
    p.write_text("", encoding="utf-8")
    os.environ[RUN_ID_KEY] = str(run_id)
    return {"stats_path": str(p), "run_id": str(run_id)}


def _beta_equal(recorded, expected, tol=1e-12):
    """Compare a recorded beta string to the expected value numerically."""
    try:
        return abs(float(recorded) - float(expected)) <= tol
    except (TypeError, ValueError):
        return False


def read_stats(stats_path, run_id=None, expect_mode=None, expect_beta=None,
               expect_shards=None, require_stage="test"):
    """Merge the per-subprocess stats records, FAIL-CLOSED on anything unreliable.

    Rejects rather than skips: malformed JSON, records from another run/mode/beta, missing or
    nonfinite fields, zero-frame records, duplicate shards, conflicting activation branches.
    A skipped record is indistinguishable from an absent one, and this project has already been
    burned repeatedly by evidence that quietly degraded into a passing null.

    `require_stage` closes the gap Codex demonstrated at admission round 3: the parent runs the
    patched predict script TWICE -- once for test inference (the run that produces the
    submission) and once for validation -- and both append here. Without stage separation a
    single validation record, with NO test-inference telemetry at all, satisfied every aggregate
    check and produced a passing gate. The returned `frames`/`frames_with_bonus` therefore count
    the REQUIRED STAGE ONLY; other stages are reported separately and never substitute for it.
    """
    merged = {"frames": 0, "frames_with_bonus": 0, "activation": None,
              "raw_absmax": 0.0, "raw_std_sum": 0.0,
              "pre_raw_absmax": 0.0, "pre_raw_std_sum": 0.0,
              "stats_records": 0, "stats_shards": [],
              "required_stage": require_stage, "stage_counts": {}, "other_stage_records": 0}
    p = Path(stats_path)
    if not p.is_file():
        raise Exp062Error("stats file %s is missing; the patched subprocess never ran" % p)

    for lineno, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError as exc:
            raise Exp062Error("stats %s line %d is malformed: %s" % (p, lineno, exc)) from exc

        # --- validate the record COMPLETELY before any of it is aggregated -------------------
        # Aggregating first is how invalid evidence slips through: `max()` silently drops a NaN
        # (max(0.0, nan) == 0.0), and a zero-frame record disappears into a valid neighbour's sum.
        for field in REQUIRED_STAT_FIELDS:
            if field not in rec:
                raise Exp062Error(
                    "stats %s line %d is missing the required field %r" % (p, lineno, field))
        if run_id is not None and str(rec["run_id"]) != str(run_id):
            raise Exp062Error(
                "stats %s line %d belongs to run %r, not this run %r (stale evidence)"
                % (p, lineno, rec["run_id"], run_id))
        if expect_mode is not None and rec["mode"] != expect_mode:
            raise Exp062Error(
                "stats %s line %d was written under mode %r, expected %r"
                % (p, lineno, rec["mode"], expect_mode))
        if expect_beta is not None and not _beta_equal(rec["beta"], expect_beta):
            raise Exp062Error(
                "stats %s line %d was written under beta %r, expected %r"
                % (p, lineno, rec["beta"], expect_beta))
        for key in NUMERIC_STAT_FIELDS:
            try:
                value = float(rec[key])
            except (TypeError, ValueError) as exc:
                raise Exp062Error(
                    "stats %s line %d field %r is not numeric: %r"
                    % (p, lineno, key, rec[key])) from exc
            if not math.isfinite(value):
                raise Exp062Error(
                    "stats %s line %d field %r is nonfinite: %r" % (p, lineno, key, value))
        if int(rec["frames"]) <= 0:
            raise Exp062Error(
                "stats %s line %d recorded 0 frames; that subprocess never saw an edge batch"
                % (p, lineno))
        act = rec["activation"]
        if merged["activation"] is not None and act != merged["activation"]:
            raise Exp062Error(
                "conflicting activation branches across shards: %r vs %r"
                % (merged["activation"], act))
        stage = rec["stage"]
        if stage == "unknown":
            raise Exp062Error(
                "stats %s line %d has no stage marker; test and validation telemetry would be "
                "indistinguishable" % (p, lineno))
        shard = rec["shard"]

        # --- only now aggregate -------------------------------------------------------------
        merged["activation"] = act
        merged["stage_counts"][stage] = merged["stage_counts"].get(stage, 0) + 1
        if stage != require_stage:
            merged["other_stage_records"] += 1
            continue  # counted, reported, but NEVER allowed to stand in for the required stage

        if shard in merged["stats_shards"]:
            raise Exp062Error(
                "stats %s line %d duplicates %s shard %r; subprocess coverage is ambiguous"
                % (p, lineno, stage, shard))
        merged["stats_records"] += 1
        merged["stats_shards"].append(shard)
        merged["frames"] += int(rec["frames"])
        merged["frames_with_bonus"] += int(rec["frames_with_bonus"])
        for fld in ("raw_absmax", "pre_raw_absmax"):
            merged[fld] = max(merged[fld], float(rec[fld]))
        for fld in ("raw_std_sum", "pre_raw_std_sum"):
            merged[fld] += float(rec[fld])

    if merged["stats_records"] == 0:
        raise Exp062Error(
            "stats file %s has NO %r-stage records (stages seen: %r). The %r stage is the run "
            "that produces the submission; telemetry from any other stage must never substitute "
            "for it."
            % (p, require_stage, merged["stage_counts"], require_stage))
    if merged["frames"] <= 0:
        raise Exp062Error("stats recorded 0 frames; the patched block never saw an edge batch")
    for key in ("raw_absmax", "raw_std_sum", "pre_raw_absmax", "pre_raw_std_sum"):
        if not math.isfinite(merged[key]):
            raise Exp062Error("stats aggregate %s is nonfinite: %r" % (key, merged[key]))
    if expect_shards is not None and sorted(merged["stats_shards"]) != sorted(expect_shards):
        raise Exp062Error(
            "subprocess coverage mismatch: recorded shards %r, expected %r"
            % (sorted(merged["stats_shards"]), sorted(expect_shards)))
    merged["raw_std_mean"] = merged["raw_std_sum"] / merged["frames"]
    merged["pre_raw_std_mean"] = merged["pre_raw_std_sum"] / merged["frames"]
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
        "candidate_quality_evidence": (
            "NONE. The 0.947 figure is the PARENT's authenticated Public LB score "
            "(repro_059, submission 56313491). Nothing in this run establishes any quality "
            "for the candidate; the notebook's inherited provenance text describes the parent "
            "lineage only. Quality is decided solely by a separate Public LB submission."),
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
        "stats_fresh_and_attributable": bool(telemetry.get("stats_records", 0) > 0),
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
