"""Collection adapter for exp_064 (verbatim x138 reproduction).

The third-party notebook emits no `metrics.json` and no gate field, so the controller's normal
contract cannot apply. This adapter inspects the artifacts the notebook DOES write and emits a
controller-compatible `metrics.json` carrying `x138_repro_integrity_passed`.

Revision history (this file is reviewed alongside the admission artifacts):
  v1  first cut. Codex admission round 2 derived a concrete FALSE-PASS fixture against it:
      a CSV with one node at node_id=-7, t=999999, coords 1e30 passed every check, because
      `math.isfinite(1e30)` is True, node_id was never required to be non-negative, t had no upper
      bound, and a single dataset satisfied the coverage check. Its degradation regexes were also
      guessed rather than read from the notebook, so none of them matched the real messages.
  v2  (this file) bounds derived from the notebook's own int16 cast (cell 5:2152-2154); non-negative
      ids; per-dataset frame contiguity; dataset coverage cross-checked against the notebook's own
      dynamically discovered count ("Found N test videos", cell 4:321); STRUCTURED degradation
      flags read from run_stats.csv (`repair_fallback`, `deadline_degraded`) in preference to log
      grepping; the remaining swallow cases matched against strings copied verbatim from the
      notebook; artifacts bound to one run; and `validation.protocol` + `runtime_seconds` emitted
      so the controller's metrics contract accepts the payload.

Usage:  python scripts/collect_exp064_x138.py <kernel_output_dir>
Exit 0 iff the gate passes. Writes <dir>/metrics.json.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

PARENT_SHA = "d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60"
EXP062_K2_SHA = "ba9431c1161ac89770cb1d1ffd268ac9248da31e3d738390b418c19fd3629cbb"
DEEPCENTER_SHA = "8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0"

EXPECTED_COLUMNS = [
    "id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id",
]

# The notebook casts coordinates to int16 (cell 5:2152-2154), so anything outside int16 or
# non-integral is structurally impossible in a healthy run. 1e30 is finite; this bound is what
# actually rejects it.
INT16_MAX = 32767
T_MAX = 10000

# Swallow cases that do NOT abort the notebook. Strings copied verbatim from the snapshot, not
# invented: cell 4:497, cell 5:1197/1202/1207, cell 5:1299, cell 5:2128, cell 5:354.
DEGRADATION_STRINGS = [
    ("LOW-DETECTION DUMP SKIPPED", "low-detection dump skipped (cell 4:497)"),
    ("gap filler idle", "gap filler idle (cell 5:1197/1202/1207)"),
    ("readmit skipped", "detection re-admission skipped (cell 5:1299)"),
    ("REPAIR FAILED", "repair failed, basic-filtered ILP fallback (cell 5:2128)"),
    ("repair gate skipped because torch is unavailable", "DeepCenter repair gate skipped (cell 5:354)"),
]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    out = Path(sys.argv[1])
    if not out.is_dir():
        print(f"not a directory: {out}")
        return 2

    checks: dict[str, bool] = {}
    details: dict[str, object] = {}
    failures: list[str] = []

    def ck(key: str, ok: bool, msg: str = "") -> None:
        checks[key] = bool(ok)
        if not ok:
            failures.append(f"{key}: {msg}")
            print(f"  FAIL  {key}: {msg}")

    # ---- submission present, and not a duplicate of anything already known ----------------
    sub = out / "submission.csv"
    if not sub.exists():
        ck("submission_written", False, "submission.csv absent")
        return emit(out, checks, details, failures, None)
    ck("submission_written", True)

    digest = hashlib.sha256(sub.read_bytes()).hexdigest()
    details["submission_sha256"] = digest
    ck("differs_from_parent", digest != PARENT_SHA, f"byte-identical to the 0.947 parent {PARENT_SHA[:12]}")
    ck("differs_from_exp062_k2", digest != EXP062_K2_SHA, f"byte-identical to exp_062 k2 {EXP062_K2_SHA[:12]}")

    # ---- schema + graph integrity ----------------------------------------------------------
    seen: set[tuple[str, int]] = set()
    dup = bad_id = bad_coord = bad_t = malformed = 0
    rows = 0
    nodes: dict[str, int] = defaultdict(int)
    edges: dict[str, int] = defaultdict(int)
    tset: dict[str, set[int]] = defaultdict(set)
    edge_endpoints: list[tuple[str, int, int]] = []
    node_t: dict[tuple[str, int], int] = {}
    bad_rowtype = 0

    with sub.open(newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        ck("schema_columns", header == EXPECTED_COLUMNS, f"got {header}")
        idx = {n: i for i, n in enumerate(header or [])}
        for row in reader:
            rows += 1
            if len(row) != len(EXPECTED_COLUMNS):
                malformed += 1
                continue
            ds = row[idx["dataset"]]
            rtype = row[idx["row_type"]]
            if rtype not in ("node", "edge"):
                bad_rowtype += 1
                continue
            if rtype != "node":
                edges[ds] += 1
                # Edge rows legitimately carry -1 sentinels in node_id/t/z/y/x, but their
                # source_id/target_id must reference real nodes. Collected and checked below,
                # after every node id is known.
                try:
                    edge_endpoints.append((ds, int(row[idx["source_id"]]), int(row[idx["target_id"]])))
                except ValueError:
                    malformed += 1
                continue
            try:
                nid = int(row[idx["node_id"]])
                t = int(row[idx["t"]])
                coords = [float(row[idx[a]]) for a in ("z", "y", "x")]
            except ValueError:
                malformed += 1
                continue
            if nid < 0:
                bad_id += 1
            if (ds, nid) in seen:
                dup += 1
            seen.add((ds, nid))
            if not (0 <= t <= T_MAX):
                bad_t += 1
            for v in coords:
                if not math.isfinite(v) or not (0 <= v <= INT16_MAX) or v != int(v):
                    bad_coord += 1
            nodes[ds] += 1
            tset[ds].add(t)
            node_t[(ds, nid)] = t

    details.update(
        rows=rows,
        datasets_in_submission=sorted(nodes),
        nodes_per_dataset=dict(nodes),
        edges_per_dataset=dict(edges),
        density_per_dataset={d: round(nodes[d] / max(len(tset[d]), 1), 1) for d in nodes},
    )
    ck("non_empty", rows > 0, "no data rows")
    ck("no_malformed_rows", malformed == 0, f"{malformed} malformed rows")
    ck("row_types_valid", bad_rowtype == 0,
       f"{bad_rowtype} rows whose row_type is neither 'node' nor 'edge'")
    ck("unique_node_ids", dup == 0, f"{dup} duplicate (dataset,node_id) pairs")
    ck("node_ids_non_negative", bad_id == 0, f"{bad_id} negative node_id on node rows")
    ck("coords_integral_in_int16", bad_coord == 0,
       f"{bad_coord} coordinates non-integral, negative, non-finite or outside int16")
    ck("t_within_bounds", bad_t == 0, f"{bad_t} t values outside [0,{T_MAX}]")
    noncontig = [d for d in tset if tset[d] and sorted(tset[d]) != list(range(min(tset[d]), max(tset[d]) + 1))]
    ck("frames_contiguous", not noncontig, f"non-contiguous frame indices in {noncontig}")
    ck("every_dataset_has_edges", all(edges.get(d, 0) > 0 for d in nodes),
       f"datasets with nodes but no edges: {[d for d in nodes if not edges.get(d)]}")
    dangling = [(d, s, t_) for (d, s, t_) in edge_endpoints
                if (d, s) not in seen or (d, t_) not in seen]
    details["dangling_edge_count"] = len(dangling)
    ck("edge_endpoints_exist", not dangling,
       f"{len(dangling)} edges reference node ids absent from their dataset, e.g. {dangling[:3]}")
    # Endpoint existence alone still admits a self-loop, so require time to advance strictly.
    backward = [(d, a, b) for (d, a, b) in edge_endpoints
                if (d, a) in node_t and (d, b) in node_t and node_t[(d, b)] <= node_t[(d, a)]]
    nonadjacent = [(d, a, b) for (d, a, b) in edge_endpoints
                   if (d, a) in node_t and (d, b) in node_t
                   and node_t[(d, b)] != node_t[(d, a)] + 1]
    details["backward_or_selfloop_edge_count"] = len(backward)
    details["non_adjacent_edge_count"] = len(nonadjacent)
    ck("edges_strictly_forward", not backward,
       f"{len(backward)} edges whose target time does not advance (self-loop or backward), "
       f"e.g. {backward[:3]}")

    # ---- dataset COVERAGE against the notebook's own dynamic discovery ---------------------
    # Never assume the four visible names; the hidden rerun sees a different set.
    logs_paths = sorted(out.glob("*.log"))
    logs = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in logs_paths)
    details["log_files"] = [p.name for p in logs_paths]
    found = re.findall(r"Found\s+(\d+)\s+test videos", logs)  # cell 4:321
    if found:
        discovered = int(found[-1])
        details["test_videos_discovered"] = discovered
        ck("dataset_coverage_matches_discovery", discovered == len(nodes),
           f"notebook discovered {discovered} test videos but the submission covers {len(nodes)}")
    else:
        ck("dataset_coverage_matches_discovery", False,
           "no 'Found N test videos' line; cannot confirm coverage against dynamic discovery")

    # ---- runtime integrity receipt: checkpoint identity only -------------------------------
    # Its ground_truth_accessed / compliance fields are HARDCODED ASSERTIONS (cell 3:681,
    # cell 6:131-134), not telemetry, and its guard config is stale (cell 6:138-147).
    # Only the checkpoint hashes are genuinely computed at runtime, so only those are read.
    receipts = sorted(out.glob("*runtime_integrity*.json"))
    details["runtime_receipts"] = [p.name for p in receipts]
    ck("exactly_one_runtime_receipt", len(receipts) == 1,
       f"expected exactly 1 receipt bound to this run, found {len(receipts)}")
    if len(receipts) == 1:
        data = json.loads(receipts[0].read_text(encoding="utf-8"))
        cks = {str(v) for v in (data.get("checkpoint_sha256") or {}).values()}
        details["checkpoint_sha256"] = data.get("checkpoint_sha256")
        ck("deepcenter_checkpoint_identity", DEEPCENTER_SHA in cks,
           f"expected {DEEPCENTER_SHA[:12]}, got {sorted(s[:12] for s in cks)}")

    # ---- V1284 actually executed ------------------------------------------------------------
    ck("v1284_patched", "V1284 head patched" in logs, "no 'V1284 head patched' line (cell 4:533)")
    ck("v1284_mode_candidate", re.search(r"mode\s*=\s*candidate", logs) is not None,
       "V1284_MODE is not 'candidate'")
    ck("v1284_no_runtime_error", "invalid V1284 displacement" not in logs,
       "the V1284 module raised 'invalid V1284 displacement'")

    # ---- no silent degradation: STRUCTURED flags first, logs as a backstop -----------------
    degraded: list[str] = []
    stats_path = out / "run_stats.csv"
    if stats_path.exists():
        with stats_path.open(newline="") as fh:
            stats_rows = list(csv.DictReader(fh))
        details["run_stats_rows"] = len(stats_rows)
        # Degradation telemetry is MANDATORY, not best-effort. A run_stats.csv that simply omits
        # these columns must fail, otherwise absent telemetry reads as "no degradation".
        missing_cols = [f for f in ("repair_fallback", "deadline_degraded")
                        if not stats_rows or f not in stats_rows[0]]
        ck("degradation_telemetry_present", not missing_cols,
           f"run_stats.csv lacks required degradation columns {missing_cols}")
        # It must also cover exactly the datasets the submission contains.
        stats_ds = {r.get("dataset") for r in stats_rows if r.get("dataset")}
        ck("run_stats_covers_datasets", stats_ds == set(nodes),
           f"run_stats datasets {sorted(stats_ds)} != submission datasets {sorted(nodes)}")
        for flag in ("repair_fallback", "deadline_degraded"):
            if stats_rows and flag in stats_rows[0]:
                hits = [r.get("dataset", "?") for r in stats_rows
                        if str(r.get(flag, "")).strip() not in ("0", "0.0")]
                if hits:
                    degraded.append(f"run_stats.{flag} set or unparseable for {hits}")
        ck("run_stats_present", True)
    else:
        ck("run_stats_present", False, "run_stats.csv absent; structured degradation flags unavailable")
        ck("degradation_telemetry_present", False, "no run_stats.csv at all")
        ck("run_stats_covers_datasets", False, "no run_stats.csv at all")
    for needle, label in DEGRADATION_STRINGS:
        if needle in logs:
            degraded.append(label)
    details["degradations_detected"] = degraded
    ck("no_silent_degradation", not degraded, "; ".join(degraded))

    # ---- measured runtime, for honest budget reconciliation --------------------------------
    runtime = None
    m = re.findall(r"kernel_elapsed_seconds[\"']?\s*[:=]\s*([0-9.]+)", logs)
    if m:
        runtime = float(m[-1])
    elif stats_path.exists():
        with stats_path.open(newline="") as fh:
            for r in csv.DictReader(fh):
                try:
                    runtime = max(runtime or 0.0, float(r.get("kernel_elapsed_seconds") or 0))
                except ValueError:
                    pass
    details["runtime_seconds_source"] = "kernel_elapsed_seconds" if runtime else "UNAVAILABLE"
    ck("runtime_measured", runtime is not None and math.isfinite(runtime) and runtime > 0,
       f"measured runtime absent or not finite-positive ({runtime}); budget cannot be reconciled")

    return emit(out, checks, details, failures, runtime)


def emit(out: Path, checks: dict, details: dict, failures: list, runtime: float | None) -> int:
    passed = bool(checks) and all(checks.values())
    metrics = {
        "schema_version": 1,
        "experiment_id": "exp_064_x138_verbatim_repro",
        "x138_repro_integrity_passed": passed,
        "primary_metric": 1.0 if passed else 0.0,
        "primary_metric_meaning": "deployment integrity; NO quality inference",
        "reproducible": False,
        "runtime_seconds": runtime if runtime is not None else 0.0,
        "validation": {"protocol": "x138_verbatim_repro_v1"},
        "checks": checks,
        "failures": failures,
        "details": details,
        "quality_evidence": (
            "NONE. Nothing in this run establishes any Public LB quality. The author's rank-62 "
            "0.956 is THEIR score on THEIR pipeline and is not inherited by this reproduction. "
            "Quality is decided solely by a separate authorized Public LB submission."
        ),
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    print(f"\n{'PASS' if passed else 'FAIL'}  x138_repro_integrity_passed={passed}")
    print(f"wrote {out / 'metrics.json'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
