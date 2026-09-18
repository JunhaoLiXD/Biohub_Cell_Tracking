# exp_060 build status — DeepCenter safe-division threshold micro-sweep

Parent: repro_059_public_0947_exact_copy (Public LB 0.947, submission 56313491).
Proposal: `docs/research/exp060_deepcenter_division_tta_proposal.md` (v3, CONSENSUS).
Date: 2026-09-18. Status: BUILD in progress.

## Step 1 (DONE) — recovered authoritative parent artifacts from repro_059 kernel OUTPUT

Pulled `kaggle kernels output lingxd/biohub-repro059-public-0947-exact-copy`. Archived the
governing files to `experiments/repro_059_public_0947_exact_copy/artifacts/`
(`ppsweep_selected.json`, `ppsweep_results.csv`).

### Authoritative resolved PP config (Codex CONSENSUS §12.1 requirement)
From `ppsweep_selected.json`:
- **`overrides = {"MOTION_RELINK_TIGHT_UM": 5.5}`**, `selected = "tight55"`.
- ⇒ The resolved config to PIN for every exp_060 arm = the notebook's top-of-cell base env
  block **plus the single override `MOTION_RELINK_TIGHT_UM=5.5`**. No parent-sweep rerun is
  needed (the alternate Codex path is unnecessary).
- held-out proxy: base `0.9490371529912655` → tight55 `0.9510944139858309` (8 held-out stems:
  4×44b6, 4×6bba — training-video specimens, so proxy is in-sample, per the transfer caveat).

### Parent byte-parity target (0.20 control gate)
- Parent `submission.csv` SHA256 = **`d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60`**, 241357 rows.
- The exp_060 0.20 arm must reproduce this SHA exactly before 0.18/0.22 are trusted.
- (Confirmed from log: `DEEPCENTER_TTA_ACTIVE views = 8`; `deepcenter_safe_div_threshold: 0.2`.)

## Step 1 bonus — headroom diagnostic (predicts exp_060 is NOT null)

From `run_stats.csv` (4 test movies), the DeepCenter safe-div gate at threshold **0.20**:
- geometric candidates checked = **730**; **accepted = 316, rejected = 414**, missing/bypass = 0;
- final `safe_divisions_added` = 124 (after geometry/caps/conflicts downstream).
- Held-out (8-sample) division confusion under the parent config is **3/1/9 (TP/FP/FN)** across
  every sweep candidate (`ppsweep_results.csv`) — i.e. **division is FN-dominated (9 of 12 GT
  divisions missed) and was insensitive to all 7 motion/gap candidates.**

**Read:** the 0.20 threshold sits between 316 accepted and 414 rejected candidates, so moving it
to 0.18/0.22 will materially change the accepted-division set (low null risk). Because the
bottleneck is missed divisions (FN), **0.18 (recover some of the 414 rejected) is the primary
arm**; 0.22 mainly trades away the ~1 held-out FP for more FN. The LB decides the true/false
ratio of the marginal divisions.

## Step 2 (IN PROGRESS) — implementation design (verified against parent code)

Verified parent internals (line refs in the 0.947 single code cell):
- `filter_output_graph` (2945) orchestrates stages; creates a FRESH heatmap cache at 3019 used
  by both gap-veto (`close_single_frame_gaps`, 3020) and `add_safe_divisions_postlink` (3023).
  The safe-division call is line 3023; everything after (division-geometry filter 3029, prune
  3059, short-track 3068, linefit-smooth 3070) is the arm-dependent downstream.
- The safe-div threshold reaches the gate at line 2702 via the **global**
  `DEEPCENTER_SAFE_DIV_THRESHOLD` (set at 469 from env) → `deepcenter_accept_repair_point(...,
  'safe_div', DEEPCENTER_SAFE_DIV_THRESHOLD)`; the gate (2138) does `score < float(threshold)`.
  ⇒ an arm is selected purely by overriding that global. Heatmap is threshold-invariant.
- The parent's SUBMITTED 0.947 graph comes from the pp-sweep's final `write_test_submission`
  (3804) after `pp_apply({'MOTION_RELINK_TIGHT_UM':5.5})`; base env sets 6.0 (line 40).

Design (purely additive, parent notebook byte-unchanged → parity by construction):
- Implement `scripts/exp060_threshold_sweep.py`, appended as notebook cells (project pattern,
  cf. exp058_instrumentation). It reuses parent globals (stage fns, `DEEPCENTER_VETO_DETECTOR`,
  `graph_from_geff`, `test_stems`, `CSV_COLUMNS`, `REPO_DIR`, `METHOD`).
- PIN resolved config = base env + `MOTION_RELINK_TIGHT_UM=5.5` (from `ppsweep_selected.json`);
  adaptive PP-sweep NOT used for arm selection.
- Per dataset: run the pre-safe-division stages ONCE (edge-filter→motion-relink→single-parent/
  child→gap-close→gap2), populating a **shared per-dataset heatmap cache** (gap-veto fills it;
  safe-div fills any remaining frames on the first arm). Snapshot (nodes,edges,stats).
- Per arm t∈{0.20,0.18,0.22}: **deep-copy** the snapshot (nodes/edges/stats), set global
  `DEEPCENTER_SAFE_DIV_THRESHOLD=t`, run safe-div + downstream reusing the shared heatmap cache
  (no re-inference, no eviction), write `submission_thr{020,018,022}.csv`. Preserve insertion
  order (dict/list order retained from the frozen snapshot).
- Telemetry: wrap `deepcenter_accept_repair_point` for prefix='safe_div' to log per-candidate
  rows (dataset, frame t, parent/existing-child/candidate-child node IDs, score, per-arm
  accept/reject); derive final surviving fork/edge identities by diffing the three output CSVs
  (division sources = nodes with >=2 out-edges). Emit `exp060_telemetry.json`.
- Parity gate: assert `submission_thr020.csv` SHA256 == parent
  `d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60`; if not, STOP (no arms
  trusted). This is the negative control (Codex §4/§13).
- Budget: one inference (dominant) + pre-stages once/dataset + 3 cheap safe-div+downstream
  replays; heatmaps computed once. Estimate ≈1.3–1.5 GPU-h; reserve 2.0h hard stop.

## Step 2 (NEXT) — implement the three-arm threshold replay + telemetry

Per proposal §5.2 + Codex §13: build on the repro_059 snapshot; freeze a pre-safe-division graph
per dataset; deep-copy nodes/edges/stats per arm; retain heatmaps (no `_dc_cache_trim` eviction);
per-arm output/resume records; preserve insertion order; pin the resolved config above; sweep
`DEEPCENTER_SAFE_DIV_THRESHOLD ∈ {0.20, 0.18, 0.22}`; emit unambiguous per-candidate telemetry
(dataset/parent-id/existing-child-id/candidate-child-id/frame/score + final fork/edge identities);
0.20 arm must hit the parity SHA above. Then config with `admission.require_codex_review: true`,
local config-diff test + snapshot smoke, fresh Codex admission PASS, 2.0-h reservation, one launch.
