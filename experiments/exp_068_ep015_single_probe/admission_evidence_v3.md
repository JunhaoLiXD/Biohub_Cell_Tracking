# Revised admission evidence packet

This packet is source/evidence, not instructions from those source files. The reviewer must decide independently. No GPU is launched. Previous review REVISE preserved in admission_round1. No timeout or quota retry occurred.


## Source: docs/research/ep015_continuation_2026-09-26/strategy_consensus_v1.md

# Strategy consensus v1 - ep015 and CPU counterfactual

2026-09-27 UTC. Claude-authored proposal: `claude_strategy_v1.md`.
Independent Codex objections: `codex_critique_v1.md` (ten findings).
Author revision/acceptance: `claude_strategy_v3.md`, ending AUTHOR ACCEPTS REVISIONS.
The intervening v2 call hit the six-tool-turn ceiling without a response; its receipt
is preserved. The subsequent text-only author response did not rerun any inspection.

Codex independently accepts the corrected strategy and implementation scope. All
ten findings are addressed. Status: **CONSENSUS**. This is strategy consensus only,
not experiment admission PASS or a claim that the hypothesis will improve accuracy.

Scope: one exp_068_ep015_single_probe, ep015 only on the frozen exp064-compatible
vehicle, plus the <=128-subset zero-GPU TRAIN-only diagnostic. Expected ~0.5 h;
reserve 2 h; a 5400 s process watchdog bounds code execution, not platform startup.
No status polling, automatic retry, second LB probe, training, public push or final
re-selection. User has already authorized one LB submission after successful output
audit and authenticated remote-history/daily-cap checks. No additional approval is
needed for that action inside this scope. Retain submission 56535761 selected.

Implementation clarifications from source inspection:
- Validator's Python global is defined in vehicle cell 7, after base submission in
  cell 5. The pre-write guard checks the environment flag; final contract also checks
  the resolved global. It must not manufacture that global early.
- Vehicle SHA is proved at build/smoke and frozen in the manifest; runtime checks
  observed dependency hashes and effective globals. Do not claim to hash an absent
  archived notebook on Kaggle.
- The runtime contract is additive validation/telemetry, not a new inference adapter.
- The watchdog is the existing project design; early missing psutil fails rather
  than allowing an unbounded run. Same limit on hidden rerun; failure means stop.
- Equality of aggregate metrics does not imply graph identity. Pruning can change
  coordinates through downstream linefit and can change divisions; report changes.

Gate order: build -> immutable snapshot -> fresh request_codex_review.py PASS ->
snapshot smoke -> controller reservation/launch -> user completion notice -> collect
once -> independent graph/config/hash/degradation audit -> one authorized submission.
CPU diagnostic may execute now under this consensus; it cannot authorize training.


## Source: docs/research/ep015_continuation_2026-09-26/claude_strategy_v3.md

# exp_068_ep015_single_probe — strategy proposal v2 (revision)

Author: Claude Code. **STRATEGY: PROPOSED (revised)** — not reviewed, not admitted. Nothing built, pushed, launched or submitted. I do not grant CONSENSUS or an admission PASS; those are not mine to give.

## Disposition of each Codex correction

**1. "Two movies" — ACCEPT (with one retained caveat).** The exp065 table is 8 samples across 2 prefixes; I will say that. **I withdraw the quantized-probability-mass claim entirely**: equal aggregate columns across ep010/ep015/ep020 do not establish bit-identical graphs, so "plateau, not knife edge" is unsupported and is struck. Retained, undisputed: the per-prefix split (`6bba` +0.0099, `44b6` −0.0085) — two prefixes is still the governing transfer limitation, and the aggregate is one prefix carrying the other.

**2. Runtime anchors — ACCEPT.** exp064 932.2 s = 0.2589 h; cx03 1116.4 s = 0.3101 h. The 1.727 h figure was misattributed and is struck. Expected ~0.5 h.

**3. Watchdog — ACCEPT, and this is the biggest improvement.** My attended 5-minute polling watchdog violated the standing no-poll rule; it is removed. Replaced with the already-used in-notebook psutil/thread watchdog: 5400 s from first code-cell execution, kills descendants and exits; identical on visible and hidden runs; hidden overrun is accepted as failure with **no retry**. Reservation raised to **2 h** (platform startup sits outside the timer). Algorithmic repair deadlines unchanged. The watchdog, guard and contract are **infrastructure**, documented and diff-bound separately from the one scientific lever, and excluded from the authored-line budget for the lever itself.

**4. Assert, don't echo — ACCEPT.** Assert-only guard immediately before the base `write_test_submission` call (vehicle sha, checkpoint sha, effective globals: `VALIDATOR_ENABLE=0`, `OUTPUT_MIN_EDGE_PROB=0.15`, all other v5 levers 0.0, `_V9_AUTO_SET_ENV` empty, `FROZEN_PRESET_OVERRIDES is None`). Additive final `metrics.json` to the controller contract: elapsed, output hash, effective config, pruning counters, no-degradation checks. Neither may alter predictions. Build in scratchpad; **I will not pre-create the experiment directory** — the controller mints the immutable snapshot.

**5. Gate order — ACCEPT; my v1 order was wrong.** Corrected: CONSENSUS → controller snapshot → fresh experiment-specific Codex admission review *of that immutable source* → smoke → reservation → ONE controller launch → user's completion notice (never poll) → one collection. Wrapper/contract/check scripts ship as snapshot extras. No new deployment adapter.

**6. Divisions — ACCEPT.** "This lever does not touch divisions" is struck as a general claim and narrowed to: division counts are unchanged *in the local exp065 table only*. Pruning also removes internal orphan nodes and is followed by short-track filtering and linefit smoothing, so division scores can move. Checks 1–6 gain an explicit division-count delta report rather than a preservation assumption.

**7. Authorization scope — ACCEPT.** The ONE submission is already inside the authorized scope; I will not request additional authorization unless scope changes, and will run the metrics/graph/provenance audit first. Conservative 3/New-York-day cap, remote history checked. No final re-selection; 56535761 stays. Consistent with the standing rule, I still will not press submit unprompted.

**8. Q1 scripts — ACCEPT.** My v1 wrongly tainted HEADROOM: HEADROOM converts node IDs to rows correctly; only the WHY script misindexes. Deficits are still independently re-derived from the frozen graphs/labels, with an explicit assert of agreement with Q1 and no conflation of the two scripts' evidence. Removed conflicting edges are **reported as true or false**, not assumed true.

**9. CPU edit algebra — ACCEPT.** Union-of-requested-edges construction; remove conflicting incoming edges and every non-requested outgoing edge of edited mothers; reject conflicting selections; order-independent. No-op Gate 0 must reproduce **full per-movie scalar metrics**, not only 3/2/9. Cache per-movie scores, enumerate all ≤128 global subsets, call the existing aggregate scorer for exact weighting — no greedy shortcut.

**10. Interpretation — ACCEPT.** ≥0.954 is an exploratory public-split gain only; 0.953 is a registered null at displayed precision, not equality; retained 0.953 remains final.

Unchanged: parent, vehicle, the single lever, the 128-subset CPU diagnostic and its five-point self-critique, and the unmitigated public-split overfitting risk.

**STRATEGY: PROPOSED (v2)**

AUTHOR ACCEPTS REVISIONS


## Source: experiments/exp_068_ep015_single_probe/snapshot/config.yaml

schema_version: 1
experiment_id: exp_068_ep015_single_probe
parent: exp_064_x138_verbatim_repro
hypothesis: A fixed output edge-probability floor 0.15 on the exp064-compatible vehicle
  improves recorded Public LB from 0.953 to at least 0.954 at displayed precision.
change:
  component: output_edge_probability_floor
  from: 0.0
  to: 0.15
  exact: Same verified vehicle as exp066 cx03, but cx03 OFF and ep015 ON. Validator/sweep
    OFF, all other new levers OFF. Existing summary typo fix, auto-attach refusal
    and arm snapshot retained. Add prediction-neutral pre-write/final configuration
    and dependency assertions, output graph audit/metrics contract and 5400s process
    watchdog. No training, no alternative prediction algorithm.
source_notebook: scratchpad/exp068_build/biohub-exp068-ep015.ipynb
strategy_record: docs/research/ep015_continuation_2026-09-26/strategy_consensus_v1.md
execution_authorization: User accepted one ep015 run and one LB probe plus CPU diagnostic;
  no promotion or second attempt.
validation:
  protocol: ep015_single_probe_v1
  primary_metric: ep015_probe_integrity_passed
  limitations: Engineering gate only. Existing 8-movie/2-prefix proxy is reused exploratory
    evidence, not independent validation; worst prefix regression about 0.0085. LB
    is unknown. Exact graph hashes across different ep thresholds have not been established.
admission:
  require_codex_review: true
  reviewer_provider: codex
local:
  smoke_test:
  - '{python}'
  - scripts/smoke_exp068.py
  - '{source_notebook}'
budget:
  tier: 1
  expected_gpu_hours: 2.0
  note: Expected ~0.5h, planned reservation 2h; watchdog kills descendants and kernel
    at 5400 seconds from first cell. Platform startup is outside timer. No polling/retry;
    identical hidden-run timeout accepted as a failure risk.
success:
  minimum_improvement: 0.0
  regression_threshold: 0.0
evaluation:
  mode: gate
  gate_field: ep015_probe_integrity_passed
kaggle:
  owner: lingxd
  slug: biohub-exp068-ep015
  title: biohub-exp068-ep015
  accelerator: NvidiaTeslaT4
  docker_image: gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461
  inject_experiment_id: false
  competition_sources:
  - biohub-cell-tracking-during-development
  dataset_sources:
  - pilkwang/biohub-deepcenter-unet3d-center-prior-v1
  - pilkwang/biohub-temporal-unet3d-seed314159-v1
  - pilkwang/biohub-tracking-support-pack-50ep-v1
  - anvithpothula/biohub-v1284-head-s075
  required_dataset_sources: 4
  enable_gpu: true
  enable_internet: false
  is_private: true
  extra_files:
  - scripts/build_exp068_probe.py
  - scripts/exp068_build_support.py
  - scripts/exp068_contract.py
  - scripts/smoke_exp068.py
  - scripts/audit_exp068_collection.py
leaderboard:
  authorized: true
  max_submissions: 1
  daily_cap: 3
  rule: One only after current-output independent audit and authenticated remote cap/duplicate
    check. >=0.954 exploratory displayed gain, 0.953 registered null, <=0.952 reject.
    Keep 56535761 selected regardless; no automatic re-selection.
stop_rule: Any snapshot/config/identity/graph/degradation failure or duplicate output
  stops. Wait for user completion, collect once; no training, retry, second probe
  or public push.


## Source: experiments/exp_068_ep015_single_probe/admission_round1/review.md

## Summary

The versioned `strategy_consensus_v1.md` explicitly records **CONSENSUS**, linking Claude’s proposal, ten Codex objections, and accepted revisions. Strategy consensus is established; implementation admission remains incomplete.

## Methodology

- The fixed edge-probability floor, 0 → 0.15, is a testable single-variable intervention.
- The eight-movie proxy is reused exploratory evidence, not independent validation. Reported changes—approximately **44b6 −0.0085** and **6bba +0.0099**—do not establish cross-domain improvement.
- Frozen-model training exposure further limits proxy interpretation.
- Exp064 supplies a credible deployment parent, but its 0.953 result does not itself support pruning. One authorized probe offers bounded information; threshold sweeps or promotion are not justified.

## Implementation risks

The inspected contract checks effective settings, dependency receipts, graph structure, degradation, pruning activity, and duplicate output. It correctly labels its primary metric as engineering integrity.

However:

- The smoke script creates temporary files, so I did not execute it under the read-only instruction.
- Repeated tool infrastructure failures prevented completing snapshot notebook inspection, manifest verification, and history checks in `results.json` and `EXPERIMENTS.md`.
- Source-parity assertions in a smoke script are not evidence that the frozen snapshot actually passes them.
- Pruning can change orphan removal, subsequent smoothing, and divisions; unchanged division behavior must not be assumed.

## Budget

Expected runtime is approximately 0.5 hours, with a planned two-hour reservation and 5,400-second watchdog. This is reasonable against the reported 30 hours.

However, `GPU_BUDGET.json` sets `reserve_hours: 0.0`, conflicting with GOAL.md’s six-hour protection. The proposed run leaves sufficient funds, but the controller does not enforce that protection.

## Required changes

1. Restore the six-hour reserve or record explicit authorization superseding it.
2. Complete independent inspection of the frozen notebook, snapshot hashes, exact vehicle delta, and experiment history.
3. Obtain a recorded snapshot smoke PASS before launch.
4. Preserve post-run independent audit, authenticated submission-history checks, one-submission limit, and no automatic promotion.

## Recommendation

Do not advance on this review. Consensus is present, but incomplete implementation verification and the budget-policy inconsistency prevent admission PASS. No files were changed.

VERDICT: REVISE


## Source: experiments/exp_068_ep015_single_probe/direct_snapshot_smoke_v1.json

{
  "status": "PASSED",
  "scope": "Direct immutable-snapshot smoke before review revision; formal controller smoke still follows admission PASS.",
  "at_utc": "2026-09-27T02:21:16+00:00",
  "command": [
    "E:\\Project\\Biohub_CellTracking\\.venv\\Scripts\\python.exe",
    "scripts/smoke_exp068.py",
    "E:\\Project\\Biohub_CellTracking\\experiments\\exp_068_ep015_single_probe\\snapshot\\source\\biohub-exp068-ep015.ipynb"
  ],
  "exit_code": 0,
  "stdout": "PASS: exact vehicle delta, embedded contract, all code syntax, threshold/boundary/orphan behavior, config drift and graph-negative fixtures.\n",
  "stderr": "",
  "hash_checks": [
    {
      "path": "experiments/exp_068_ep015_single_probe/snapshot/config.yaml",
      "expected": "fa1265179a569aaae14e323e4c8163656da2a3b5aa8d3ef867eda273c1e66c15",
      "actual": "fa1265179a569aaae14e323e4c8163656da2a3b5aa8d3ef867eda273c1e66c15"
    },
    {
      "path": "experiments/exp_068_ep015_single_probe/snapshot/source/biohub-exp068-ep015.ipynb",
      "expected": "4dfc2bb121d67a47ddefd75a25c5559df7dc58e202ddaa1efb1bd9a98100555f",
      "actual": "4dfc2bb121d67a47ddefd75a25c5559df7dc58e202ddaa1efb1bd9a98100555f"
    },
    {
      "path": "experiments/exp_068_ep015_single_probe/snapshot/extra_files/build_exp068_probe.py",
      "expected": "67848b8dedd1a8b9668cd77c6fcff6c7ba4b3b838e1e3b98683b86dacccfbbeb",
      "actual": "67848b8dedd1a8b9668cd77c6fcff6c7ba4b3b838e1e3b98683b86dacccfbbeb"
    },
    {
      "path": "experiments/exp_068_ep015_single_probe/snapshot/extra_files/exp068_build_support.py",
      "expected": "b6d34a8c581e8e28392d865686f53bef3d008dec828ddb2924794cdfc734fa39",
      "actual": "b6d34a8c581e8e28392d865686f53bef3d008dec828ddb2924794cdfc734fa39"
    },
    {
      "path": "experiments/exp_068_ep015_single_probe/snapshot/extra_files/exp068_contract.py",
      "expected": "b6be3a42e66a134502cdded9d3846d64a704e3864a01cba2f38da7c504fe1faa",
      "actual": "b6be3a42e66a134502cdded9d3846d64a704e3864a01cba2f38da7c504fe1faa"
    },
    {
      "path": "experiments/exp_068_ep015_single_probe/snapshot/extra_files/smoke_exp068.py",
      "expected": "93e8fb4176ef85c51048e6d7cb13031557d6d67eac1e7ab0de03e19e1bf7e063",
      "actual": "93e8fb4176ef85c51048e6d7cb13031557d6d67eac1e7ab0de03e19e1bf7e063"
    },
    {
      "path": "experiments/exp_068_ep015_single_probe/snapshot/extra_files/audit_exp068_collection.py",
      "expected": "4109407aa8a83b4bb4c78d1e921768cdf3a50c7bc8aa3111269a3a4b9463e882",
      "actual": "4109407aa8a83b4bb4c78d1e921768cdf3a50c7bc8aa3111269a3a4b9463e882"
    }
  ]
}

## Source: experiments/exp_068_ep015_single_probe/source_delta_v1.diff

--- exp066_cx03
+++ exp068_frozen
@@ -1,3 +1,15 @@
+# Same bounded-process watchdog used by exp067 export; no status polling.
+import os, time, threading, psutil
+_exp068_started = time.monotonic()
+def _exp068_timeout():
+    time.sleep(5400)
+    print("EXP068 HARD WALLTIME: 5400 seconds", flush=True)
+    for _child in psutil.Process(os.getpid()).children(recursive=True):
+        try: _child.kill()
+        except psutil.Error: pass
+    os._exit(124)
+threading.Thread(target=_exp068_timeout, daemon=True).start()
+
 
 
 import os
@@ -64,7 +76,7 @@
 # Runtime hardening. None of these change the output on the visible test.
 import time as _t0_time
 os.environ["BIOHUB_KERNEL_START_TS"] = str(_t0_time.time())
-os.environ["BIOHUB_VALIDATOR_ENABLE"] = "0"  # exp_066: validator and sweep OFF -- this arm is deterministic, the base pass IS the arm
+os.environ["BIOHUB_VALIDATOR_ENABLE"] = "0"  # exp_068: validator and sweep OFF -- this arm is deterministic, the base pass IS the arm
 os.environ["BIOHUB_ILP_TIMEOUT_S"] = "1200"           # per dataset; SCIP keeps its incumbent at the limit (x138-proven)
 os.environ["BIOHUB_REPAIR_DEADLINE_S"] = "27000"      # x138-proven 7.5 h; past this the repair loop degrades to filtering
 os.environ["BIOHUB_FRAME_CACHE_MAX_FRAMES"] = "48"
@@ -105,7 +117,7 @@
 os.environ["BIOHUB_PPSWEEP_EXTENDED"] = "1"             # v4/v5 extended candidate set
 os.environ["BIOHUB_PPSWEEP_PREFIX_GUARD"] = "1"         # per-embryo anti-overfit selection guard
 os.environ["BIOHUB_SWEEP_DEADLINE_S"] = "26100"         # sweep inner-loop abort, keeps best-so-far (7.25 h)
-os.environ["BIOHUB_OUTPUT_MIN_EDGE_PROB"] = "0.0"       # v5 L1 weak-edge output filter (0 = off)
+os.environ["BIOHUB_OUTPUT_MIN_EDGE_PROB"] = "0.15"  # exp_068 arm ep015: THE single active v5 lever (was 0.0 = off)
 os.environ["BIOHUB_SEG_PRUNE_MIN_PROB"] = "0.0"         # v5 L2 weak pendant-segment pruning (0 = off)
 os.environ["BIOHUB_SEG_PRUNE_MAX_LEN"] = "6"
 os.environ["BIOHUB_GAP_CLOSE_DIV_UM"] = "0.0"           # v5 L3 division-priority gap continuation (0 = off)
@@ -113,7 +125,7 @@
 os.environ["BIOHUB_REPAIR_DEEPCENTER_THRESHOLD"] = "0.12"
 os.environ["BIOHUB_REPAIR_SISTER_SYMMETRY_TAU"] = "0.85"
 os.environ["BIOHUB_CORE_EDGE_PROB"] = "0.60"            # v5 L5 count-target pruning core definition
-os.environ["BIOHUB_COUNT_EXCESS_FRAC"] = "0.03"  # exp_066 arm cx03: THE single active v5 lever (was 0.0 = off)
+os.environ["BIOHUB_COUNT_EXCESS_FRAC"] = "0.0"          # v5 L5 count-target pruning (0 = off)
 os.environ["BIOHUB_LINEFIT_MAX_SHIFT_UM"] = "0.0"       # v5 L7 linefit shift clamp (0 = off)
 
 # --- v9 additions: restored hidden-rerun governor (x138 base, 9 h wall) ---
@@ -227,11 +239,11 @@
     print(f"V9 FROZEN PRESET loaded from {_V7_FROZEN_PATH}: {FROZEN_PRESET_LABEL} {FROZEN_PRESET_OVERRIDES}")
 
 
-# exp_066 probe: the empty-string preset/cache settings above ENABLE the
+# exp_068 probe: the empty-string preset/cache settings above ENABLE the
 # /kaggle/input/*/ppsweep_selected.json and */cache_key.txt auto-attach rather than disabling it.
 # Fail closed here, after loading and before any application to inference.
-assert not _V9_AUTO_SET_ENV, f"exp_066: preset/cache auto-attach fired: {_V9_AUTO_SET_ENV}"
-assert FROZEN_PRESET_OVERRIDES is None, "exp_066: a frozen preset was loaded; this is not a clean arm"
+assert not _V9_AUTO_SET_ENV, f"exp_068: preset/cache auto-attach fired: {_V9_AUTO_SET_ENV}"
+assert FROZEN_PRESET_OVERRIDES is None, "exp_068: a frozen preset was loaded; this is not a clean arm"
 print("BIOHUB_PRESET:", BIOHUB_PRESET)
 print("BIOHUB_SCORE_AXIS:", BIOHUB_SCORE_AXIS)
 
@@ -1853,6 +1865,122 @@
 
 predict_seconds = time.time() - start_time
 print(f"Prediction completed in {predict_seconds / 60:.2f} minutes")
+"""Assert-only runtime contract, embedded in the ep015 notebook; standard library only."""
+import csv
+import hashlib
+import json
+import math
+import os
+import time
+from collections import Counter
+from pathlib import Path
+
+EXP068_EXPECTED = {'OUTPUT_MIN_EDGE_PROB': .15, 'COUNT_EXCESS_FRAC': 0.,
+                  'SEG_PRUNE_MIN_PROB': 0., 'LEAF_PRUNE_MIN_EDGE_PROB': 0.,
+                  'GAP_CLOSE_DIV_UM': 0., 'REPAIR_PARENT_MAX_UM': 0., 'LINEFIT_MAX_SHIFT_UM': 0.}
+EXP068_CHECKPOINTS = {
+    'deepcenter': '8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0',
+    'primary': '12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771',
+    'secondary': '9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f'}
+EXP068_PARENT = 'd52a5da2ae5cb0d1b22499f6ca51a00838a6c32ae9a1986ec756ea72e7909e03'
+EXP068_CX03 = '135172dfefda1b5c8c43aca30eb8cc1357a84b7826ac0ada3bf80c0b53f11fef'
+
+
+def exp068_preflight(ns):
+    observed = {}
+    for key, value in EXP068_EXPECTED.items():
+        assert key in ns and type(ns[key]) in (int, float), ('missing resolved setting', key)
+        assert float(ns[key]) == value, ('resolved setting drift', key, ns[key])
+        assert float(os.environ['BIOHUB_' + key]) == value, ('environment drift', key)
+        observed[key] = ns[key]
+    assert os.environ['BIOHUB_VALIDATOR_ENABLE'] == '0'
+    assert ns['_V9_AUTO_SET_ENV'] == {} and ns['FROZEN_PRESET_OVERRIDES'] is None
+    root = Path(ns['WORKING_DIR'])
+    receipts = list(root.glob('*runtime_integrity*.json'))
+    assert len(receipts) == 1, 'Exactly one current runtime integrity receipt required'
+    receipt = json.loads(receipts[0].read_text())
+    assert receipt['checkpoint_sha256'] == EXP068_CHECKPOINTS
+    assert receipt['support_repo_python_manifest_sha256'] == '978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029'
+    return observed
+
+
+def exp068_audit_csv(path, discovered):
+    expected = ['id', 'dataset', 'row_type', 'node_id', 't', 'z', 'y', 'x', 'source_id', 'target_id']
+    nodes, edges, row_ids = {}, [], set()
+    with Path(path).open(newline='') as fh:
+        reader = csv.DictReader(fh)
+        assert reader.fieldnames == expected, 'Submission schema mismatch'
+        for row in reader:
+            assert None not in row and all(v is not None for v in row.values()), 'Malformed CSV row'
+            rid = int(row['id'])
+            assert rid >= 0 and rid not in row_ids, 'Duplicate/negative row id'
+            row_ids.add(rid)
+            ds = row['dataset']
+            if row['row_type'] == 'node':
+                nid, frame = int(row['node_id']), int(row['t'])
+                key = (ds, nid)
+                assert nid >= 0 and frame >= 0 and key not in nodes
+                xyz = tuple(float(row[a]) for a in ('z', 'y', 'x'))
+                assert all(math.isfinite(v) and 0 <= v <= 32767 for v in xyz)
+                nodes[key] = (frame, xyz)
+            else:
+                assert row['row_type'] == 'edge'
+                edges.append((ds, int(row['source_id']), int(row['target_id'])))
+    assert nodes and edges and set(d for d, _ in nodes) == set(discovered)
+    assert len(set(edges)) == len(edges)
+    incoming, outgoing = Counter(), Counter()
+    for ds, a, b in edges:
+        assert (ds, a) in nodes and (ds, b) in nodes
+        assert nodes[ds, b][0] == nodes[ds, a][0] + 1
+        incoming[ds, b] += 1
+        outgoing[ds, a] += 1
+    assert max(incoming.values()) <= 1 and max(outgoing.values()) <= 2
+    counts = {ds: {'nodes': sum(d == ds for d, _ in nodes),
+                   'edges': sum(d == ds for d, _, _ in edges),
+                   'forks': sum(d == ds and n == 2 for (d, _), n in outgoing.items())}
+              for ds in sorted(set(discovered))}
+    assert all(v['edges'] > 0 for v in counts.values())
+    return counts
+
+
+def exp068_finalize(ns):
+    observed = exp068_preflight(ns)
+    assert ns['VALIDATOR_ENABLE'] is False and ns['val_stems'] == []
+    root = Path(ns['WORKING_DIR'])
+    report = json.loads((root / 'biohub_v9_runtime_report.json').read_text())
+    assert report['deadline_degraded'] is False
+    assert report['frozen_preset_applied'] is False and report['auto_attached'] == {}
+    assert report['sweep_results_count'] == 0 and report['shipped_config'] == 'base'
+    assert report['shipped_overrides'] == {} and report['val_pred_cache_used'] is False
+    stats = list(csv.DictReader((root / 'run_stats.csv').open(newline='')))
+    assert stats and len(stats) == len(ns['test_stems'])
+    assert {r['dataset'] for r in stats} == set(ns['test_stems'])
+    for row in stats:
+        for key in ('repair_fallback', 'deadline_degraded', 'count_target_removed', 'leaf_prune_nodes', 'seg_prune_nodes', 'repairs_added', 'divgap_added'):
+            assert float(row[key]) == 0, (key, row['dataset'])
+    dropped = sum(int(r['weak_edge_dropped']) for r in stats)
+    assert dropped > 0, 'VOID: no weak edges dropped'
+    sub = root / 'submission.csv'
+    digest = hashlib.sha256(sub.read_bytes()).hexdigest()
+    assert digest not in (EXP068_PARENT, EXP068_CX03), 'VOID: known duplicate output'
+    assert (root / 'submission_arm.csv').read_bytes() == sub.read_bytes()
+    counts = exp068_audit_csv(sub, ns['test_stems'])
+    for row in stats:
+        assert int(row['nodes']) == counts[row['dataset']]['nodes']
+        assert int(row['edges']) == counts[row['dataset']]['edges']
+    runtime = time.monotonic() - ns['_exp068_started']
+    assert 0 < runtime < 5400
+    metrics = {'schema_version': 1, 'experiment_id': 'exp_068_ep015_single_probe',
+               'validation': {'protocol': 'ep015_single_probe_v1'},
+               'primary_metric': 1., 'primary_metric_meaning': 'Engineering integrity only; no accuracy claim',
+               'ep015_probe_integrity_passed': True, 'runtime_seconds': runtime, 'reproducible': False,
+               'submission_sha256': digest, 'effective_config': observed, 'weak_edge_dropped': dropped,
+               'per_dataset': counts, 'checkpoint_sha256': EXP068_CHECKPOINTS,
+               'quality_status': 'Unknown until separately audited authorized LB probe; never auto-promote.'}
+    print('EXP068 postflight PASS', digest, flush=True)
+    return metrics
+
+
 import tracksdata as td
 import numpy as np
 import blosc2
@@ -4728,19 +4856,20 @@
     _V7_FROZEN_APPLIED = True
     print(f"V7: frozen preset {FROZEN_PRESET_LABEL!r} applied to the base repair pass: {FROZEN_PRESET_OVERRIDES}", flush=True)
 try:
+    exp068_preflight(globals())
     write_test_submission("base")
 finally:
     if _v7_frozen_saved:
         for _v7_k, _v7_v in _v7_frozen_saved.items():
             globals()[_v7_k] = _v7_v
 
-# exp_066 probe: snapshot the written submission. With the validator off nothing rewrites
+# exp_068 probe: snapshot the written submission. With the validator off nothing rewrites
 # submission.csv, so this is a belt-and-braces copy that also makes the arm artefact explicit
 # in the kernel output.
 import shutil as _x66_shutil
 _X66_SNAPSHOT = WORKING_DIR / "submission_arm.csv"
 _x66_shutil.copy2(SUBMISSION_PATH, _X66_SNAPSHOT)
-print(f"exp_066: arm submission snapshotted to {_X66_SNAPSHOT}", flush=True)
+print(f"exp_068: arm submission snapshotted to {_X66_SNAPSHOT}", flush=True)
 
 # v9: measured cost of the full base pass -- the pass-2 rewrite's cost proxy.
 _V9_REPAIR_SECONDS = max(0.0, v7_kernel_elapsed() - _V9_REPAIR_T0)
@@ -6082,3 +6211,6 @@
     print("             Kaggle Dataset to this notebook -- v9 auto-detects it and")
     print("             ships the winning config in a single ~20 min base pass.")
 print(f"  report written to:     {_v9_report_path}")
+
+_exp068_metrics = exp068_finalize(globals())
+(WORKING_DIR / "metrics.json").write_text(json.dumps(_exp068_metrics, indent=2) + "\n")


## Source: experiments/exp_068_ep015_single_probe/snapshot/extra_files/smoke_exp068.py

"""CPU smoke of the actual frozen notebook: source parity, guards and pruning behavior."""
import ast
import copy
import csv
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import exp068_contract as contract
from scripts.exp068_build_support import WATCHDOG, FINAL
from experiment_controller.core import validate_notebook


def must_reject(fn):
    try:
        fn()
    except (AssertionError, KeyError, ValueError):
        return
    raise AssertionError('Invalid fixture was accepted')


def main():
    path = Path(sys.argv[1])
    validate_notebook(path, require_metrics_contract=True)
    nb = json.loads(path.read_text(encoding='utf-8'))
    old_path = ROOT / 'experiments/exp_066_probe_cx03/kaggle_kernel/biohub-exp066-cx03.ipynb'
    old = json.loads(old_path.read_text(encoding='utf-8'))
    assert len(nb['cells']) == len(old['cells']) + 2
    assert ''.join(nb['cells'][0]['source']) == WATCHDOG
    assert ''.join(nb['cells'][-1]['source']) == FINAL
    embedded = (ROOT / 'scripts/exp068_contract.py').read_text(encoding='utf-8')
    for i, before in enumerate(old['cells']):
        after = ''.join(nb['cells'][i + 1]['source'])
        if i == 5:
            assert after.startswith(embedded + '\n\n')
            after = after[len(embedded) + 2:]
            assert after.count('    exp068_preflight(globals())\n') == 1
            after = after.replace('    exp068_preflight(globals())\n', '')
        after = after.replace('exp_068', 'exp_066')
        expected = ''.join(before['source'])
        if i == 0:
            for key, value in [('BIOHUB_OUTPUT_MIN_EDGE_PROB', '0.15'), ('BIOHUB_COUNT_EXCESS_FRAC', '0.0')]:
                new_lines = [s for s in after.splitlines() if s.startswith(f'os.environ["{key}"] =')]
                old_lines = [s for s in expected.splitlines() if s.startswith(f'os.environ["{key}"] =')]
                assert len(new_lines) == len(old_lines) == 1
                assert new_lines[0].startswith(f'os.environ["{key}"] = "{value}"')
                after = after.replace(new_lines[0], old_lines[0])
        assert after == expected, f'Unexpected predictor/vehicle source delta in original cell {i}'

    # Exercise the EXACT archived filter function extracted from the frozen notebook.
    tree = ast.parse(''.join(nb['cells'][6]['source']))
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'filter_weak_edges')
    ns = {'np': SimpleNamespace(isfinite=math.isfinite), 'OUTPUT_MIN_EDGE_PROB': .15}
    exec(compile(ast.Module(body=[func], type_ignores=[]), '<frozen-filter>', 'exec'), ns)
    nodes = {0: {'t': 0}, 1: {'t': 1}, 2: {'t': 2}, 3: {'t': 1}, 4: {'t': 2}}
    edges = [{'source_id': 0, 'target_id': 1, 'edge_prob': .149},
             {'source_id': 1, 'target_id': 2, 'edge_prob': .1},
             {'source_id': 0, 'target_id': 3, 'edge_prob': .15},
             {'source_id': 3, 'target_id': 4, 'edge_prob': None}]
    stats = {'weak_edge_dropped': 0, 'weak_edge_orphan_nodes': 0}
    kept, links = ns['filter_weak_edges'](copy.deepcopy(nodes), copy.deepcopy(edges), stats)
    assert stats == {'weak_edge_dropped': 2, 'weak_edge_orphan_nodes': 1}
    assert set(kept) == {0, 2, 3, 4} and links == edges[2:]
    ns['OUTPUT_MIN_EDGE_PROB'] = 0.
    assert ns['filter_weak_edges'](nodes, edges, {'weak_edge_dropped': 0}) == (nodes, edges)

    with tempfile.TemporaryDirectory(prefix='exp068_smoke_') as td:
        root = Path(td)
        receipt = {'checkpoint_sha256': contract.EXP068_CHECKPOINTS,
                   'support_repo_python_manifest_sha256': '978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029'}
        (root / 'runtime_integrity.json').write_text(json.dumps(receipt))
        context = dict(contract.EXP068_EXPECTED, WORKING_DIR=root, _V9_AUTO_SET_ENV={}, FROZEN_PRESET_OVERRIDES=None)
        saved = dict(os.environ)
        try:
            for key, value in contract.EXP068_EXPECTED.items():
                os.environ['BIOHUB_' + key] = str(value)
            os.environ['BIOHUB_VALIDATOR_ENABLE'] = '0'
            contract.exp068_preflight(context)
            for key in contract.EXP068_EXPECTED:
                bad = dict(context, **{key: .9})
                must_reject(lambda: contract.exp068_preflight(bad))
            must_reject(lambda: contract.exp068_preflight(dict(context, _V9_AUTO_SET_ENV={'preset': 'bad'})))
            must_reject(lambda: contract.exp068_preflight(dict(context, FROZEN_PRESET_OVERRIDES={})))
            os.environ['BIOHUB_VALIDATOR_ENABLE'] = '1'
            must_reject(lambda: contract.exp068_preflight(context))
        finally:
            os.environ.clear()
            os.environ.update(saved)
        header = ['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
        rows = [[0,'test','node',0,0,1,1,1,-1,-1], [1,'test','node',1,1,1,1,1,-1,-1],
                [2,'test','edge',-1,-1,-1,-1,-1,0,1]]
        def check_csv(values, discover=['test']):
            file = root / 'submission.csv'
            with file.open('w', newline='') as fh:
                writer = csv.writer(fh); writer.writerow(header); writer.writerows(values)
            return contract.exp068_audit_csv(file, discover)
        assert check_csv(rows)['test']['edges'] == 1
        bad = copy.deepcopy(rows); bad[-1][-1] = 9
        must_reject(lambda: check_csv(bad))
        must_reject(lambda: check_csv(rows, ['test', 'missing']))
        bad = copy.deepcopy(rows); bad[1][4] = 0
        must_reject(lambda: check_csv(bad))
    print('PASS: exact vehicle delta, embedded contract, all code syntax, threshold/boundary/orphan behavior, config drift and graph-negative fixtures.')


if __name__ == '__main__':
    main()


## Source: experiments/exp_068_ep015_single_probe/snapshot/extra_files/audit_exp068_collection.py

"""Independent local audit after controller collection; does not submit or change selection."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exp068_contract import exp068_audit_csv, EXP068_CHECKPOINTS, EXP068_EXPECTED, EXP068_PARENT
from scripts.collect_exp064_x138 import DEGRADATION_STRINGS
from experiment_controller.core import load_record, verify_snapshot


def main():
    record = load_record(ROOT, 'exp_068_ep015_single_probe')
    verify_snapshot(ROOT, record)
    out = ROOT / 'experiments/exp_068_ep015_single_probe/artifacts'
    assert record.get('remote', {}).get('status') == 'COMPLETE'
    metrics = json.loads((out / 'metrics.json').read_text())
    assert metrics['experiment_id'] == record['experiment_id'] and metrics['ep015_probe_integrity_passed'] is True
    assert metrics['effective_config'] == EXP068_EXPECTED
    logs = '\n'.join(p.read_text(encoding='utf-8', errors='replace') for p in out.glob('*.log'))
    assert logs, 'Collected run log missing'
    assert not re.search(r'Traceback \(most recent call last\)|AssertionError|invalid V1284 displacement', logs)
    assert all(s not in logs for s, _ in DEGRADATION_STRINGS)
    assert 'V1284 head patched' in logs and re.search(r'mode\s*=\s*candidate', logs)
    assert 'EXP068 postflight PASS' in logs
    discovered = re.findall(r'Found\s+(\d+)\s+test videos', logs)
    assert discovered
    stats = list(csv.DictReader((out / 'run_stats.csv').open(newline='')))
    names = [r['dataset'] for r in stats]
    assert len(set(names)) == len(names) == int(discovered[-1])
    counts = exp068_audit_csv(out / 'submission.csv', names)
    assert counts == metrics['per_dataset']
    for row in stats:
        assert float(row['repair_fallback']) == float(row['deadline_degraded']) == 0
    receipt = json.loads((out / 'bidirectional_production_runtime_integrity.json').read_text())
    assert receipt['checkpoint_sha256'] == EXP068_CHECKPOINTS
    assert receipt['support_repo_python_manifest_sha256'] == '978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029'
    digest = hashlib.sha256((out / 'submission.csv').read_bytes()).hexdigest()
    assert digest == metrics['submission_sha256']
    assert (out / 'submission.csv').read_bytes() == (out / 'submission_arm.csv').read_bytes()
    ledger = json.loads((ROOT / 'SUBMISSION_BUDGET.json').read_text())
    assert digest != EXP068_PARENT and all(digest != r.get('submission_sha256') for r in ledger['submissions'])
    parent = json.loads((ROOT / 'experiments/exp_064_x138_verbatim_repro/collection/metrics.json').read_text())
    pn, pe = parent['details']['nodes_per_dataset'], parent['details']['edges_per_dataset']
    assert set(counts) == set(pn), 'Visible datasets differ; cannot certify isolated pruning direction'
    deltas = {d: {'nodes': counts[d]['nodes'] - pn[d], 'edges': counts[d]['edges'] - pe[d]} for d in counts}
    assert all(v['edges'] <= 0 and v['nodes'] <= 0 for v in deltas.values())
    assert sum(v['edges'] for v in deltas.values()) < 0
    report = {'status': 'PASS', 'experiment_id': record['experiment_id'], 'submission_sha256': digest,
              'parent_deltas': deltas, 'per_dataset': counts, 'runtime_seconds': metrics['runtime_seconds'],
              'scope': 'Current collected output only. Before submission also bind authenticated remote kernel/version/source to staged snapshot and query remote submission history; this audit does not perform or waive those checks.'}
    path = out.parent / 'independent_collection_audit.json'
    assert not path.exists(), 'Preserve prior audit'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()


## Current budget
{
  "remaining_hours": 30.0,
  "reserve_hours": 6.0,
  "reserved_hours": {}
}

## Parsed history checks
{
  "results_json_parsed": true,
  "experiments_md_sha256": "53e7c605970fc655cd73ccd89ec47e4f88d92fec73e00d7ec66d03c505904292",
  "prior_ep068_submission": false,
  "parent_and_cx03_receipts": [
    {
      "local_date": "2026-09-24",
      "gate_checked_at_utc": "2026-09-25T00:47:17.167382+00:00",
      "submitted_at_utc": "2026-09-25T00:44:57.010000Z",
      "competition": "biohub-cell-tracking-during-development",
      "submission_id": 56535761,
      "experiment_id": "exp_064_x138_verbatim_repro",
      "kernel": "lingxd/biohub-exp064-x138-repro",
      "kernel_version": 1,
      "file_name": "submission.csv",
      "submission_sha256": "d52a5da2ae5cb0d1b22499f6ca51a00838a6c32ae9a1986ec756ea72e7909e03",
      "status": "COMPLETE",
      "submit_method": "competition_submit_code (kaggle competitions submit -k lingxd/biohub-exp064-x138-repro -v 1 -f submission.csv)",
      "gate_verdict": {
        "allowed": true,
        "cap": 5,
        "remote_today": 1,
        "local_today": 1,
        "used": 1,
        "remaining": 4,
        "duplicate": false
      },
      "remote_history_checked_before_submit": true,
      "platform_remaining_reported_at_submit": 4,
      "duplicate_probe": false,
      "user_authorized": true,
      "arm": "x138 byte-verbatim reproduction (zero authored code)",
      "byte_parity": "Output sha d52a5da2 DIFFERS from parent d3453380 and from exp_062 k2 ba9431c1; the no-information duplicate rule did not fire. Adapter checks differs_from_parent and differs_from_exp062_k2 both true.",
      "integrity": "scripts/collect_exp064_x138.py exit 0, x138_repro_integrity_passed true, 25/25 checks, failures []. v1284_patched true, v1284_no_runtime_error true, v1284_mode_candidate true. 238260 rows, 4/4 test videos, 0 dangling edges, 0 backward/self-loop edges, 0 non-adjacent edges. Checkpoints: deepcenter 8040999a, primary 12f6881e, secondary 9bac2fa0. Measured runtime 932.2 s (kernel_elapsed_seconds).",
      "runtime_selector_state": "INERT. The notebook ships BIOHUB_VALIDATOR_ENABLE=0, so the validator never ran, ppsweep_selected.json records selected=base with held_out_stems [] and base_proxy null, and the log reads 'SWEEP: validator unavailable -- keeping the base configuration.' The submitted output is x138's BASE configuration; its inference-time self-tuning never engaged. This was NOT known before the run.",
      "baseline_for_comparison": {
        "experiment_id": "repro_059_public_0947_exact_copy",
        "submission_id": 56313491,
        "public_score": 0.947,
        "note": "Comparator is max(0.947, exp_062 k2 56530197). k2 was STILL PENDING at submit time; the user authorized this submission anyway and the 5/day cap removes the scarcity reason for waiting."
      },
      "decision_rule": "The author is authenticated at rank 62 / 0.956, but that is THEIR score on THEIR pipeline and is not inherited. >= 0.953 would put us near the rank-200 cutoff and makes x138 the new parent; 0.948-0.952 is a real gain over 0.947 and still adopts; ~0.947 means the reproduction carries no advantage over our own parent; < 0.947 rejects it.",
      "rationale": "User-authorized LB probe. exp_064 completed COMPLETE; collected once; the adapter exit code was the submission gate and returned 0. Competition is notebook-only; kernel version 1's own submission.csv IS this arm.",
      "public_score": 0.953,
      "score_source": "authenticated kaggle competitions submissions -c biohub-cell-tracking-during-development -v, read 2026-09-25T12:50Z",
      "score_read_at_utc": "2026-09-25T13:01:26.248062Z",
      "decision_verdict": "ADOPT as parent. 0.953 satisfies the pre-registered >=0.953 branch and equals the rank-200 cutoff. It is +0.006 over repro_059 0.947 and is now this project's best authenticated Public LB score. INDEPENDENTLY CORROBORATED: amanatar/optimized-biohub-max-score cell 0 states 'x138 base (LB 0.953)' -- a third party measured the same value for the same notebook."
    },
    {
      "local_date": "2026-09-25",
      "gate_checked_at_utc": "2026-09-26T02:55:00+00:00",
      "submitted_at_utc": "2026-09-26T02:56:41.973000Z",
      "competition": "biohub-cell-tracking-during-development",
      "submission_id": 56567455,
      "experiment_id": "exp_066_probe_cx03",
      "kernel": "lingxd/biohub-exp066-cx03",
      "kernel_version": 1,
      "file_name": "submission.csv",
      "submission_sha256": "135172dfefda1b5c8c43aca30eb8cc1357a84b7826ac0ada3bf80c0b53f11fef",
      "status": "COMPLETE",
      "submit_method": "competition_submit_code (kaggle competitions submit -k lingxd/biohub-exp066-cx03 -v 1 -f submission.csv)",
      "gate_verdict": {
        "allowed": true,
        "cap": 5,
        "remote_today": 0,
        "local_today": 0,
        "used": 1,
        "remaining": 4,
        "duplicate": false
      },
      "remote_history_checked_before_submit": true,
      "platform_remaining_reported_at_submit": 4,
      "duplicate_probe": false,
      "user_authorized": true,
      "arm": "PLAN.md Step 1 cx03: BIOHUB_COUNT_EXCESS_FRAC 0.0->0.03 with BIOHUB_VALIDATOR_ENABLE 1->0, single lever on the optimized-biohub-max-score vehicle (a strict superset of x138 whose base pass byte-reproduces exp_064).",
      "byte_parity": "Output sha 135172df DIFFERS from parent exp_064 d52a5da2 -> the lever fired, the probe is live and not void (PLAN's own void test).",
      "integrity": "Kernel COMPLETE in 1116 s (~0.31 GPU h), no traceback, no AssertionError, no config-drift trip. Manifest resolved cx=0.03; VALIDATOR disabled (BIOHUB_VALIDATOR_ENABLE=0); sweep skipped, shipped_config=base; auto_attached={}, frozen_preset_applied=false (both exp_066 fail-closed asserts passed). ground_truth_accessed=false. checkpoint_sha256 (primary 12f6881e, secondary 9bac2fa0, deepcenter 8040999a) and support_repo_python_manifest_sha256 978b626d all IDENTICAL to exp_064. Remote kernel source verified cell-for-cell identical to experiments/exp_066_probe_cx03/kaggle_kernel/biohub-exp066-cx03.ipynb before submitting.",
      "effect": "count-target pruning removed 988 nodes / 1242 edges; rows 238260 -> 236030 (-0.94%). Confined to two of four test movies: 44b6_0b24845f removed=917 (nodes 19522->18605, edges 18323->17162, divisions 6->5) and 6bba_05b6850b removed=71 (nodes 6220->6149, edges 6025->5944). 44b6_0113de3b and 6bba_05db0fb1 untouched (excess=0). Global divisions 62 -> 61.",
      "decision_rule": "Pre-registered in PLAN.md Step 1 vs parent 0.953: >=0.955 adopt; 0.954 small real gain; 0.953 null, keep the parent; <=0.952 revert.",
      "risk_note": "Registered exploratory probe, NOT a Gate 2 pass: cx03 measures +0.00115 test-reweighted against our +0.0015 aggregate bar. It does pass the vehicle author's own per-embryo cap (worst per-embryo regression -0.00016, 52.6x smaller than ep015). Unmodelled risk: 917 of the 988 pruned nodes sit on 44b6_0b24845f, the worst-retention test movie (median retention 0.86, 64/100 fallback frames), and that movie also loses one division. That concentration is outside the harvested held-out table.",
      "public_score": 0.953,
      "score_source": "authenticated_kaggle_submission_history (read 2026-09-26T17:20Z)",
      "score_verified_at_utc": "2026-09-26T17:30:00+00:00",
      "delta_vs_parent_0953": 0.0,
      "verdict": "NULL against the pre-registered PLAN.md Step 1 rule: 0.953 == parent exp_064 0.953, which is the \"null, keep the parent\" branch. cx03 is NOT adopted and the lever is closed. The probe was valid, not void -- output sha 135172df differs from the parent d52a5da2, so the lever demonstrably fired and removed 988 nodes / 1242 edges; it simply bought nothing on the Public LB. Working parent remains exp_064 x138 at 0.953 (submission 56535761)."
    }
  ]
}

## Unchanged frozen function
```python
def filter_weak_edges(
    nodes_by_id: dict[int, dict[str, object]],
    edges: list[dict[str, object]],
    stats: dict[str, int],
) -> tuple[dict[int, dict[str, object]], list[dict[str, object]]]:
    """v5 L1: drop learned edges below OUTPUT_MIN_EDGE_PROB, then remove nodes
    left with no edges at all (fragments created by the drop). Edges without a
    probability (gap/safe-div/repair additions) are exempt by construction, so
    division daughters can never be disconnected here. Nodes on frame 0 or the
    final frame are always kept (legitimate lineage starts / terminal cells)."""
    if OUTPUT_MIN_EDGE_PROB <= 0.0 or not edges:
        return nodes_by_id, edges
    kept_edges: list[dict[str, object]] = []
    for edge in edges:
        prob = edge.get("edge_prob")
        if prob is None:
            kept_edges.append(edge)
            continue
        try:
            prob = float(prob)
        except (TypeError, ValueError):
            kept_edges.append(edge)
            continue
        if np.isfinite(prob) and prob < OUTPUT_MIN_EDGE_PROB:
            stats["weak_edge_dropped"] += 1
            continue
        kept_edges.append(edge)
    if stats["weak_edge_dropped"] == 0:
        return nodes_by_id, edges
    incident = set()
    for edge in kept_edges:
        incident.add(int(edge["source_id"]))
        incident.add(int(edge["target_id"]))
    max_t = max(int(node["t"]) for node in nodes_by_id.values())
    kept_nodes: dict[int, dict[str, object]] = {}
    for node_id, node in nodes_by_id.items():
        if node_id in incident or int(node["t"]) == 0 or int(node["t"]) >= max_t:
            kept_nodes[node_id] = node
        else:
            stats["weak_edge_orphan_nodes"] += 1
    return kept_nodes, kept_edges
```

## Unchanged frozen function
```python
def write_test_submission(tag: str = "base") -> None:
    
    
    geffs = sorted((REPO_DIR / "predictions").glob(f"*/{METHOD}/split_0/*.geff"))
    print(f"Found {len(geffs)} prediction graphs")
    if len(geffs) != len(test_stems):
        found = {path.stem for path in geffs}
        missing = sorted(set(test_stems) - found)
        raise RuntimeError(f"Expected {len(test_stems)} graphs, found {len(geffs)}. Missing: {missing[:10]}")

    stats_rows: list[dict[str, object]] = []
    seen_datasets: set[str] = set()
    row_id = 0
    total_nodes = 0
    total_edges = 0

    with SUBMISSION_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for geff_path in geffs:
            dataset = geff_path.stem
            seen_datasets.add(dataset)
            graph = graph_from_geff(geff_path)

            nodes_by_id: dict[int, dict[str, object]] = {}
            for row in graph.node_attrs().iter_rows(named=True):
                node_id = int(row["node_id"])
                nodes_by_id[node_id] = {
                    "node_id": node_id,
                    "t": int(row["t"]),
                    "z": float(row["z"]),
                    "y": float(row["y"]),
                    "x": float(row["x"]),
                }

            raw_edges: list[dict[str, object]] = []
            for row in graph.edge_attrs().iter_rows(named=True):
                edge_prob = row.get("edge_prob") if hasattr(row, "get") else None
                raw_edges.append({
                    "source_id": int(row["source_id"]),
                    "target_id": int(row["target_id"]),
                    "edge_prob": None if edge_prob is None else float(edge_prob),
                })

            raw_node_count = len(nodes_by_id)
            _dataset_t0 = _time.time()
            _V7_DATASET_T0["t0"] = _dataset_t0
            if not _deadline_degraded and _dataset_t0 - KERNEL_START_TS > REPAIR_DEADLINE_S:
                _deadline_degrade()
            _nodes_snapshot = {node_id: dict(node) for node_id, node in nodes_by_id.items()}
            _edges_snapshot = [dict(edge) for edge in raw_edges]
            try:
                nodes_by_id, edges, filter_stats = filter_output_graph(nodes_by_id, raw_edges, dataset=dataset, deepcenter_bundle=DEEPCENTER_VETO_DETECTOR)
                filter_stats["repair_fallback"] = 0
                if not nodes_by_id:
                    raise AssertionError(f"{dataset}: post-processing removed every node")
            except Exception as _repair_exc:
                _traceback.print_exc()
                print(
                    f"  [{dataset}] REPAIR FAILED ({type(_repair_exc).__name__}: {_repair_exc});"
                    " writing the ILP graph with basic filtering instead",
                    flush=True,
                )
                nodes_by_id, edges, filter_stats = fallback_output_graph(_nodes_snapshot, _edges_snapshot)
            filter_stats["deadline_degraded"] = int(_deadline_degraded)
            filter_stats["repair_seconds"] = round(_time.time() - _dataset_t0, 1)
            filter_stats["kernel_elapsed_seconds"] = round(_time.time() - KERNEL_START_TS, 1)
            print(
                f"  [{dataset}] repair {_time.time() - _dataset_t0:.1f}s"
                f" | kernel elapsed {_time.time() - KERNEL_START_TS:.0f}s",
                flush=True,
            )
            if not nodes_by_id:
                raise AssertionError(f"{dataset}: post-processing removed every node")

            for node_id in sorted(nodes_by_id):
                node = nodes_by_id[node_id]
                writer.writerow({
                    "id": row_id,
                    "dataset": dataset,
                    "row_type": "node",
                    "node_id": int(node["node_id"]),
                    "t": int(node["t"]),
                    "z": max(0, int(round(float(node["z"])))),
                    "y": max(0, int(round(float(node["y"])))),
                    "x": max(0, int(round(float(node["x"])))),
                    "source_id": -1,
                    "target_id": -1,
                })
                row_id += 1

            division_sources: dict[int, int] = {}
            for edge in edges:
                source_id = int(edge["source_id"])
                target_id = int(edge["target_id"])
                if source_id not in nodes_by_id or target_id not in nodes_by_id:
                    raise AssertionError(f"{dataset}: dangling edge after filtering")
                writer.writerow({
                    "id": row_id,
                    "dataset": dataset,
                    "row_type": "edge",
                    "node_id": -1,
                    "t": -1,
                    "z": -1,
                    "y": -1,
                    "x": -1,
                    "source_id": source_id,
                    "target_id": target_id,
                })
                row_id += 1
                division_sources[source_id] = division_sources.get(source_id, 0) + 1

            node_count = len(nodes_by_id)
            edge_count = len(edges)
            total_nodes += node_count
            total_edges += edge_count
            stats_rows.append({
                "dataset": dataset,
                "raw_nodes": raw_node_count,
                "nodes": node_count,
                "raw_edges": filter_stats["raw_edges"],
                "edges": edge_count,
                "division_like_sources": sum(1 for count in division_sources.values() if count >= 2),
                "edge_to_node_ratio": edge_count / max(node_count, 1),
                "gap_added_nodes_frac": filter_stats.get("gap_added_nodes", 0) / max(raw_node_count, 1),
                **filter_stats,
            })

    expected_datasets = set(test_stems)
    missing_datasets = sorted(expected_datasets - seen_datasets)
    extra_datasets = sorted(seen_datasets - expected_datasets)
    if missing_datasets or extra_datasets:
        raise AssertionError({"missing": missing_datasets[:10], "extra": extra_datasets[:10]})
    assert row_id == total_nodes + total_edges, "Internal row counter mismatch"
    assert total_nodes > 0, "No node rows produced"

    header = SUBMISSION_PATH.open().readline().strip().split(",")
    assert header == CSV_COLUMNS, f"Bad CSV header: {header}"

    stats = pd.DataFrame(stats_rows).sort_values("dataset").reset_index(drop=True)
    stats["predict_minutes_total"] = predict_seconds / 60.0
    stats["experiment_tag"] = f"{EXPERIMENT_TAG}:{tag}"
    stats.to_csv(RUN_STATS_PATH, index=False)

    print(f"Wrote {SUBMISSION_PATH} with {row_id:,} rows")
    print(f"Node rows: {total_nodes:,} | edge rows: {total_edges:,}")
    print(f"Wrote {RUN_STATS_PATH}")
    display(pd.read_csv(SUBMISSION_PATH, nrows=8))
```

## Known limitations
Smoke creates disposable files, so review need not execute it. The provided receipt is actual execution on the frozen snapshot; inspect its harness and hashes. No scientific source change since first admission review. The original source delta includes every added guard/contract/watchdog line. The GPU reserve is now six; remaining 30, no reservations. Existing current output audit still requires remote source/version binding, remote-history check, max one submission and no automatic promotion. Historical ep064 V1284 identity uncertainty is inherited; no stronger weight provenance is claimed.


# Revision 3 supplement (supersedes audit v1 for post-collection use)

## admission_round2/review.md
The supplied evidence resolves the reserve discrepancy and establishes an executed smoke receipt, but two admission gaps remain.

- **Scientific lever and guard timing:** Consistent with ep015 alone relative to exp064: cx03 is disabled. Preflight runs immediately before the base writer; checking the validator environment there and its resolved global at finalization respects initialization order.
- **CSV contract:** Checks schema, dataset coverage, unique IDs/edges, finite coordinates, endpoint existence, adjacent frames, and lineage degrees. The writer supplies integer coordinates and sentinel fields. Pruning can affect divisions and downstream coordinates; the frozen function’s division-preservation docstring is not evidence otherwise.
- **Provenance gap:** The smoke command executes workspace `scripts/smoke_exp068.py`, which imports workspace helpers and reads the exp066 vehicle. The receipt hashes snapshot extras, but does not bind those executed workspace files or the comparison vehicle to recorded hashes. Supply those hash matches and the comparison vehicle’s frozen provenance; snapshot-extra hashes alone do not establish this.
- **Missing agreed audit:** `parent_deltas` reports only nodes and edges. Consensus explicitly requires division-count deltas. Add a required per-dataset parent/current fork comparison to the post-collection audit, with a versioned, hashed supplement if preserving the snapshot.
- **Budget and execution scope:** Thirty hours minus a two-hour reservation leaves 28, above the restored six-hour reserve. The 5,400-second watchdog excludes startup. One submission remains conditional on independent output audit, remote source/version binding, and authenticated duplicate/history checks under the current three-per-New-York-day cap. Keep 56535761 selected; no retry or promotion.

No tools, GPU execution, or submission performed. Resolve these evidence/audit gaps before admission.

VERDICT: REVISE

## direct_snapshot_smoke_v2.json
{
  "at_utc": "2026-09-27T02:24:23+00:00",
  "status": "PASSED",
  "command": [
    "E:\\Project\\Biohub_CellTracking\\.venv\\Scripts\\python.exe",
    "scripts/smoke_exp068.py",
    "E:\\Project\\Biohub_CellTracking\\experiments\\exp_068_ep015_single_probe\\snapshot\\source\\biohub-exp068-ep015.ipynb"
  ],
  "stdout": "PASS: exact vehicle delta, embedded contract, all code syntax, threshold/boundary/orphan behavior, config drift and graph-negative fixtures.\n",
  "executed_workspace_to_snapshot_hash_matches": [
    {
      "workspace_path": "scripts\\build_exp068_probe.py",
      "snapshot_path": "experiments/exp_068_ep015_single_probe/snapshot/extra_files/build_exp068_probe.py",
      "sha256": "67848b8dedd1a8b9668cd77c6fcff6c7ba4b3b838e1e3b98683b86dacccfbbeb",
      "match": true
    },
    {
      "workspace_path": "scripts\\exp068_build_support.py",
      "snapshot_path": "experiments/exp_068_ep015_single_probe/snapshot/extra_files/exp068_build_support.py",
      "sha256": "b6d34a8c581e8e28392d865686f53bef3d008dec828ddb2924794cdfc734fa39",
      "match": true
    },
    {
      "workspace_path": "scripts\\exp068_contract.py",
      "snapshot_path": "experiments/exp_068_ep015_single_probe/snapshot/extra_files/exp068_contract.py",
      "sha256": "b6be3a42e66a134502cdded9d3846d64a704e3864a01cba2f38da7c504fe1faa",
      "match": true
    },
    {
      "workspace_path": "scripts\\smoke_exp068.py",
      "snapshot_path": "experiments/exp_068_ep015_single_probe/snapshot/extra_files/smoke_exp068.py",
      "sha256": "93e8fb4176ef85c51048e6d7cb13031557d6d67eac1e7ab0de03e19e1bf7e063",
      "match": true
    },
    {
      "workspace_path": "scripts\\audit_exp068_collection.py",
      "snapshot_path": "experiments/exp_068_ep015_single_probe/snapshot/extra_files/audit_exp068_collection.py",
      "sha256": "4109407aa8a83b4bb4c78d1e921768cdf3a50c7bc8aa3111269a3a4b9463e882",
      "match": true
    }
  ],
  "comparison_vehicle_provenance": {
    "archive": "docs\\research\\public_notebook_archive\\optimized-biohub-max-score.ipynb",
    "archive_sha256": "371fc1f9f4f20f692e0586616ff7d3eab4621d167f6c78516d3243c5a4fddfab",
    "builder_sha256": "bf5047d1325a9839060310cc2617a6598c8e1f62b5fae71e8dde35fb9ceb508d",
    "comparison_path": "experiments\\exp_066_probe_cx03\\kaggle_kernel\\biohub-exp066-cx03.ipynb",
    "comparison_sha256": "b9cda287c6b9255a35af756a95e630fb41ab6c29dad613f4bd874e4769175b2f",
    "byte_exact_reproduction": true
  },
  "core_sha256": "7a0a8190c1c0c70b46a26a1269c50ac9c14660d7cdd68586ba95ddf475d3261e",
  "python_executable": "E:\\Project\\Biohub_CellTracking\\.venv\\Scripts\\python.exe"
}
## admission_supplement_manifest.json
{
  "at_utc": "2026-09-27T02:24:23+00:00",
  "purpose": "Versioned local post-collection audit supplement; frozen Kaggle notebook unchanged.",
  "files": [
    {
      "path": "scripts/audit_exp068_collection_v2.py",
      "sha256": "ebc1cda48f3cc462d55b19537a2cc42c62fd8e73b849fb6f04e6cf3d56a95b20"
    },
    {
      "path": "scripts/exp068_contract.py",
      "sha256": "b6be3a42e66a134502cdded9d3846d64a704e3864a01cba2f38da7c504fe1faa"
    },
    {
      "path": "scripts/collect_exp064_x138.py",
      "sha256": "40e3e5a36fff68ab23205b892f40e70ea63dd11e4dc700e3b0c757d9f53f1d0d"
    },
    {
      "path": "experiments/exp_064_x138_verbatim_repro/collection/run_stats.csv",
      "sha256": "6b523dd08ef496df392dc269ae88b79f23adeb7fe084d35bac93cce3eec598f1"
    },
    {
      "path": "experiments/exp_064_x138_verbatim_repro/collection/metrics.json",
      "sha256": "dfff5a795da2fce90a628b6eef2a2d00900e394c9897e841dad8ccda6da98feb"
    }
  ]
}
## Required local audit v2, complete source
"""Independent local audit after controller collection; does not submit or change selection."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exp068_contract import exp068_audit_csv, EXP068_CHECKPOINTS, EXP068_EXPECTED, EXP068_PARENT
from scripts.collect_exp064_x138 import DEGRADATION_STRINGS
from experiment_controller.core import load_record, verify_snapshot


def main():
    supplement = json.loads((ROOT / 'experiments/exp_068_ep015_single_probe/admission_supplement_manifest.json').read_text())
    for entry in supplement['files']:
        assert hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest() == entry['sha256'], entry['path']
    record = load_record(ROOT, 'exp_068_ep015_single_probe')
    verify_snapshot(ROOT, record)
    out = ROOT / 'experiments/exp_068_ep015_single_probe/artifacts'
    assert record.get('remote', {}).get('status') == 'COMPLETE'
    metrics = json.loads((out / 'metrics.json').read_text())
    assert metrics['experiment_id'] == record['experiment_id'] and metrics['ep015_probe_integrity_passed'] is True
    assert metrics['effective_config'] == EXP068_EXPECTED
    logs = '\n'.join(p.read_text(encoding='utf-8', errors='replace') for p in out.glob('*.log'))
    assert logs, 'Collected run log missing'
    assert not re.search(r'Traceback \(most recent call last\)|AssertionError|invalid V1284 displacement', logs)
    assert all(s not in logs for s, _ in DEGRADATION_STRINGS)
    assert 'V1284 head patched' in logs and re.search(r'mode\s*=\s*candidate', logs)
    assert 'EXP068 postflight PASS' in logs
    discovered = re.findall(r'Found\s+(\d+)\s+test videos', logs)
    assert discovered
    stats = list(csv.DictReader((out / 'run_stats.csv').open(newline='')))
    names = [r['dataset'] for r in stats]
    assert len(set(names)) == len(names) == int(discovered[-1])
    counts = exp068_audit_csv(out / 'submission.csv', names)
    assert counts == metrics['per_dataset']
    for row in stats:
        assert float(row['repair_fallback']) == float(row['deadline_degraded']) == 0
    receipt = json.loads((out / 'bidirectional_production_runtime_integrity.json').read_text())
    assert receipt['checkpoint_sha256'] == EXP068_CHECKPOINTS
    assert receipt['support_repo_python_manifest_sha256'] == '978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029'
    digest = hashlib.sha256((out / 'submission.csv').read_bytes()).hexdigest()
    assert digest == metrics['submission_sha256']
    assert (out / 'submission.csv').read_bytes() == (out / 'submission_arm.csv').read_bytes()
    ledger = json.loads((ROOT / 'SUBMISSION_BUDGET.json').read_text())
    assert digest != EXP068_PARENT and all(digest != r.get('submission_sha256') for r in ledger['submissions'])
    parent = json.loads((ROOT / 'experiments/exp_064_x138_verbatim_repro/collection/metrics.json').read_text())
    pn, pe = parent['details']['nodes_per_dataset'], parent['details']['edges_per_dataset']
    assert set(counts) == set(pn), 'Visible datasets differ; cannot certify isolated pruning direction'
    parent_stats_path = ROOT / 'experiments/exp_064_x138_verbatim_repro/collection/run_stats.csv'
    parent_stats = list(csv.DictReader(parent_stats_path.open(newline='')))
    parent_forks = {r['dataset']: int(r['division_like_sources']) for r in parent_stats}
    assert set(parent_forks) == set(counts) and len(parent_stats) == len(counts)
    for row in parent_stats:
        assert int(row['nodes']) == pn[row['dataset']] and int(row['edges']) == pe[row['dataset']]
    for row in stats:
        assert int(row['division_like_sources']) == counts[row['dataset']]['forks']
    deltas = {d: {'nodes': counts[d]['nodes'] - pn[d], 'edges': counts[d]['edges'] - pe[d],
                  'parent_forks': parent_forks[d], 'candidate_forks': counts[d]['forks'],
                  'fork_delta': counts[d]['forks'] - parent_forks[d]} for d in counts}
    assert all(v['edges'] <= 0 and v['nodes'] <= 0 for v in deltas.values())
    assert sum(v['edges'] for v in deltas.values()) < 0
    report = {'status': 'PASS', 'experiment_id': record['experiment_id'], 'submission_sha256': digest,
              'parent_deltas': deltas, 'per_dataset': counts, 'runtime_seconds': metrics['runtime_seconds'],
              'scope': 'Current collected output only. Before submission also bind authenticated remote kernel/version/source to staged snapshot and query remote submission history; this audit does not perform or waive those checks.'}
    path = out.parent / 'independent_collection_audit.json'
    assert not path.exists(), 'Preserve prior audit'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

## Resolution
Both requested gaps resolved without changing frozen notebook or config. Workspace smoke dependencies match their immutable snapshot extras before/after execution; historical comparison notebook reproduced byte-for-byte from pinned archive with unchanged builder in a disposable directory. Required collection audit is now scripts/audit_exp068_collection_v2.py, bound by admission_supplement_manifest.json; it checks parent/current fork counts and emits their difference. Fork counts are structural, not TEST TP/FP labels. No GPU or LB submission yet.
