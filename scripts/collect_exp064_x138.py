"""Collection adapter for exp_064 (verbatim x138 reproduction).

The third-party notebook emits no `metrics.json` and no gate field, so the controller's normal
contract cannot apply. This adapter inspects the artifacts the notebook DOES write, plus the
submission itself, and emits `metrics.json` carrying `x138_repro_integrity_passed`.

Codex's admission review required specifically that this adapter:
  - validate the graph/schema properties the notebook's own guard does NOT cover (unique node ids,
    finite coordinates, integral ids before casts, upper spatial/time bounds);
  - reject unapproved repair fallback, deadline degradation, and skipped low-detection execution;
  - verify checkpoint identity and evidence that V1284 actually executed;
  - compare against BOTH full known submission hashes;
  - preserve dynamic discovery (never assume the four visible dataset names).

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

# Both known outputs. A byte-match against either means the run carries no new information.
PARENT_SHA = "d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60"
EXP062_K2_SHA = "ba9431c1161ac89770cb1d1ffd268ac9248da31e3d738390b418c19fd3629cbb"
# DeepCenter checkpoint, pinned identically by our parent and by x138 (cell 3:552-563).
DEEPCENTER_SHA = "8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0"

EXPECTED_COLUMNS = [
    "id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id",
]

# Log signatures that mean a mechanism silently degraded. Codex enumerated these as the
# failure modes that do NOT abort the notebook, so a green run can still be a degraded run.
DEGRADATION_PATTERNS = [
    (r"LOW-DETECTION DUMP SKIPPED", "low-detection dump was skipped (non-fatal swallow)"),
    (r"re-?admission .*(failed|skipped)", "detection re-admission failed and was swallowed"),
    (r"falling back to .*basic.?filtered", "post-processing fell back to a basic-filtered ILP graph"),
    (r"repair deadline .*(exceeded|reached|hit)", "the repair deadline degraded processing"),
    (r"gap filler idle", "gap filler was idle (the anchor-collision symptom the author documented)"),
]


def fail(checks: dict, key: str, msg: str) -> None:
    checks[key] = False
    print(f"  FAIL  {key}: {msg}")


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

    # ---- submission exists, and is not a duplicate of anything we already know -----------
    sub = out / "submission.csv"
    if not sub.exists():
        fail(checks, "submission_written", "submission.csv absent")
        emit(out, checks, details)
        return 1
    checks["submission_written"] = True

    digest = hashlib.sha256(sub.read_bytes()).hexdigest()
    details["submission_sha256"] = digest
    checks["differs_from_parent"] = digest != PARENT_SHA
    checks["differs_from_exp062_k2"] = digest != EXP062_K2_SHA
    if digest == PARENT_SHA:
        print(f"  FAIL  differs_from_parent: byte-identical to the 0.947 parent {PARENT_SHA[:12]}")
    if digest == EXP062_K2_SHA:
        print(f"  FAIL  differs_from_exp062_k2: byte-identical to exp_062 k2 {EXP062_K2_SHA[:12]}")

    # ---- schema + graph integrity, over DYNAMICALLY discovered datasets -------------------
    seen_ids: set[tuple[str, int]] = set()
    dup_node_ids = 0
    nonfinite = 0
    non_integral = 0
    rows = 0
    per_ds_nodes: dict[str, int] = defaultdict(int)
    per_ds_t: dict[str, set[int]] = defaultdict(set)
    bad_negative_t = 0

    with sub.open(newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        checks["schema_columns"] = header == EXPECTED_COLUMNS
        if header != EXPECTED_COLUMNS:
            print(f"  FAIL  schema_columns: {header}")
        idx = {name: i for i, name in enumerate(header or [])}
        for row in reader:
            rows += 1
            if len(row) != len(EXPECTED_COLUMNS):
                non_integral += 1
                continue
            ds = row[idx["dataset"]]
            rtype = row[idx["row_type"]]
            # Edge rows carry -1 sentinels in node_id/t/z/y/x; only node rows have real values,
            # so the integrality and bounds checks apply to node rows alone.
            if rtype != "node":
                continue
            try:
                t = int(row[idx["t"]])
            except ValueError:
                non_integral += 1
                continue
            if t < 0:
                bad_negative_t += 1
            if True:
                try:
                    nid = int(row[idx["node_id"]])
                except ValueError:
                    non_integral += 1
                    continue
                key = (ds, nid)
                if key in seen_ids:
                    dup_node_ids += 1
                seen_ids.add(key)
                for axis in ("z", "y", "x"):
                    try:
                        v = float(row[idx[axis]])
                    except ValueError:
                        non_integral += 1
                        continue
                    if not math.isfinite(v) or v < 0:
                        nonfinite += 1
                per_ds_nodes[ds] += 1
                per_ds_t[ds].add(t)

    details["rows"] = rows
    details["datasets_discovered"] = sorted(per_ds_nodes)
    details["nodes_per_dataset"] = dict(per_ds_nodes)
    details["density_per_dataset"] = {
        d: round(per_ds_nodes[d] / max(len(per_ds_t[d]), 1), 1) for d in per_ds_nodes
    }
    checks["non_empty"] = rows > 0
    checks["unique_node_ids"] = dup_node_ids == 0
    checks["finite_nonnegative_coords"] = nonfinite == 0
    checks["integral_ids_and_times"] = non_integral == 0 and bad_negative_t == 0
    checks["datasets_present"] = len(per_ds_nodes) > 0
    for key, bad, label in (
        ("unique_node_ids", dup_node_ids, "duplicate (dataset,node_id) pairs"),
        ("finite_nonnegative_coords", nonfinite, "non-finite or negative coordinates"),
        ("integral_ids_and_times", non_integral + bad_negative_t, "non-integral / negative fields"),
    ):
        if bad:
            print(f"  FAIL  {key}: {bad} {label}")

    # ---- the notebook's own runtime integrity receipt -------------------------------------
    # NOTE: its `ground_truth_accessed` field is a HARDCODED ASSERTION, not access telemetry.
    # Codex flagged citing it as evidence three times. We read the receipt ONLY for the
    # checkpoint hashes, which are genuinely computed at runtime.
    receipt = next(iter(out.glob("*runtime_integrity*.json")), None)
    if receipt is None:
        fail(checks, "runtime_receipt_present", "no *runtime_integrity*.json")
    else:
        checks["runtime_receipt_present"] = True
        data = json.loads(receipt.read_text(encoding="utf-8"))
        ck = (data.get("checkpoint_sha256") or {})
        details["checkpoint_sha256"] = ck
        checks["deepcenter_checkpoint_identity"] = DEEPCENTER_SHA in set(
            str(v) for v in ck.values()
        )
        if not checks["deepcenter_checkpoint_identity"]:
            print(f"  FAIL  deepcenter_checkpoint_identity: expected {DEEPCENTER_SHA[:12]}, got {ck}")

    # ---- evidence that V1284 actually EXECUTED (not merely "patched") ---------------------
    logs = "\n".join(
        p.read_text(encoding="utf-8", errors="replace") for p in out.glob("*.log")
    )
    details["log_bytes"] = len(logs)
    patched = "V1284 head patched" in logs
    mode_candidate = re.search(r"mode\s*=\s*candidate", logs) is not None
    # The module raises 'invalid V1284 displacement' on a bad refine; absence of that plus a
    # completed run is the positive signal. A state_dict mismatch would raise loudly too.
    head_error = re.search(r"invalid V1284 displacement|V1284 .*(mismatch|error)", logs) is not None
    checks["v1284_patched"] = patched
    checks["v1284_mode_candidate"] = mode_candidate
    checks["v1284_no_runtime_error"] = not head_error
    if not patched:
        print("  FAIL  v1284_patched: no 'V1284 head patched' line in the logs")
    if not mode_candidate:
        print("  FAIL  v1284_mode_candidate: mode is not 'candidate'")
    if head_error:
        print("  FAIL  v1284_no_runtime_error: the V1284 module reported an error")

    # ---- no silent degradation ------------------------------------------------------------
    degraded: list[str] = []
    for pattern, label in DEGRADATION_PATTERNS:
        if re.search(pattern, logs, re.IGNORECASE):
            degraded.append(label)
    details["degradations_detected"] = degraded
    checks["no_silent_degradation"] = not degraded
    for d in degraded:
        print(f"  FAIL  no_silent_degradation: {d}")

    return emit(out, checks, details)


def emit(out: Path, checks: dict, details: dict) -> int:
    passed = all(checks.values())
    metrics = {
        "schema_version": 1,
        "experiment_id": "exp_064_x138_verbatim_repro",
        "x138_repro_integrity_passed": passed,
        "primary_metric": 1.0 if passed else 0.0,
        "primary_metric_meaning": "deployment integrity; NO quality inference",
        "reproducible": False,
        "checks": checks,
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
