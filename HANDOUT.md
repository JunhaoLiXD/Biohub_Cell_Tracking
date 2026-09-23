# Session Handout — updated 2026-09-21

Purpose: hand this session's work to the next session AND to the user. Read this FIRST,
then the deeper authority in order: `STATE.json`, `experiments/exp_061_deepcenter_tta/`
(experiment.json, review.md), `.private/current/CONTINUATION.md`,
`docs/research/PROJECT_HANDOFF.md`.

If anything here disagrees with `STATE.json`, **`STATE.json` wins** (this file is a
human-readable summary; `STATE.json` is the machine source of truth).

---

## ⏸️ CURRENT (2026-09-21): exp_061 admission v4 = REVISE — fixes DEFERRED to next session

User decision 2026-09-21: **record the v4 findings here and fix them NEXT session** (do not fix now).

**Where exp_061 stands.** Strategy is CONSENSUS. Best Public LB still **0.947** (repro_059). exp_061 =
DeepCenter repair-heatmap TTA probe, 3 arms xyonly/zon/xyd4. This session addressed the Codex **v3**
REVISE (5 items) and ran a FRESH Codex admission review — which returned **v4 = REVISE** (round 4).
Nothing is launched; nothing on Kaggle. Local gates (build parity / validator / behavioral A–N) all PASS,
but Codex found a **real bug in the v3 #1 fix** plus 5 contract-hardening items. The admission gate caught
the bug BEFORE any GPU/LB spend (working as intended).

Review record: `experiments/exp_061_deepcenter_tta/review.md` (== `CODEX_REVIEW.md`); verdict logged in
`experiments/exp_061_deepcenter_tta/experiment.json` (review.status=CHANGES_REQUESTED, verdict=REVISE).

### >>> NEXT SESSION: the 6 v4 fixes (in priority order) <<<

1. **[REAL BUG — hard blocker] Frozen parent config was built from the WRONG source.**
   `EXP061_PARENT_BASE_DEFAULTS` in `scripts/exp061_deepcenter_tta.py` (~line 100) used the parent's
   DECLARATION FALLBACKS (`= float(os.environ.get('BIOHUB_X','DEFAULT'))`). But the parent notebook SETS
   `os.environ['BIOHUB_*']` overrides **before** those declarations (env-setup block, notebook code-cell
   lines ~35–90), so the EFFECTIVE config differs. Confirmed mismatches (mine → parent-effective):
   `DEEPCENTER_SAFE_DIV_THRESHOLD 0.12→0.20`, `DEEPCENTER_GAP_THRESHOLD 0.10→0.25`,
   `MOTION_RELINK_LEARNED_BONUS 0.75→1.0`, `OUTPUT_GAP2_RECOVERY False→True`, `GAP_CLOSE_MAX_GAP 1→2`,
   `GAP_CLOSE_UM 6.0→5.0`, `GAP_DENSITY_ADAPTIVE False→True`, `ILP_APPEARANCE_WEIGHT 0.1→0.0`,
   `ILP_DISAPPEARANCE_WEIGHT 0.1→2`, `ILP_DIVISION_WEIGHT 1.0→1.2`, `SAFE_DIV_MAX_UM 4.7→9.0`,
   `SAFE_DIV_SISTER_MAX_UM 7.2→14.0`, `SAFE_DIV_SISTER_SYMMETRY_TAU 0.0→0.6`,
   `SAFE_DIV_EXISTING_CHILD_MAX_UM 7.8→10.0`, `SAFE_DIV_FRAME_FRAC_CAP 0.008→0.0076`,
   `SAFE_DIV_GLOBAL_FRAC_CAP 0.004→0.00375`, `DEEPCENTER_EXPECTED_EPOCH 0→2`,
   `DEEPCENTER_GAP_CONFIRM_MIN_SPAN_UM 0.0→8.5`. (`MOTION_RELINK_TIGHT_UM`: env sets 6.0 then the
   ppsweep selects **5.5** — the tight55 override is still correct.)
   FIX: derive the frozen table by parsing the env-setup assignments (`os.environ['BIOHUB_X']='V'`) first,
   fall back to the declaration default only for knobs never set in env, then apply the tight55 override.
   Then **strengthen `test_N`** to parse BOTH the env-setup block AND the declarations (it currently only
   reads fallbacks → gave a FALSE PASS), and add negative fixtures for the 0.25/0.20/motion-bonus/gap2/
   adaptive-rescue overrides.
2. **Config coverage incomplete.** `EXP061_CONFIG_KEYS` omits parent-active knobs, notably the adaptive
   short-track rescue family (`BIOHUB_ADAPTIVE_SHORT_TRACK_RESCUE`, `SHORT_TRACK_RESCUE_MIN_LEN`,
   `..._MIN_MEAN_EDGE_PROB`, `..._MAX_MEAN_EDGE_DIST_UM`, `..._MAX_NODES_FRAC`, `..._MAX_NODES_ABS`) and
   others set in the env block. Add every behaviorally-relevant replay knob so the freeze is complete.
3. **Fail fast BEFORE arm execution.** On `live_config_equals_frozen_parent` False (or checkpoint
   provenance invalid) the harness currently only prints and continues into the arms. Make it write
   fail-closed metrics.json and RETURN before any inference/replay.
4. **Partial-run metrics contract.** A started experimental arm that budget-aborts is excluded from
   `arm_summaries`, so the gate can pass without that started arm producing an artifact. Add an explicit
   `all_started_arms_completed` gate (or formally declare + interpret partial-run semantics).
5. **Per-frame view-execution validation.** `_expected_views` infers "square-only expected" from whether
   any square-only view was observed (circular: if all silently fail, the guard still passes). Record each
   frame's geometry (square vs not) and validate the EXACT expected view sequence/count per frame.
6. **Stage edge IDENTITIES (not just counts) + conservative first-arm admission.** gap1/gap2 stage
   counters describe edges ADDED during a stage, not stage-specific edges SURVIVING in the final graph.
   Persist per-stage edge identities and intersect with the final edge_set. Also make the FIRST-arm/runtime
   admission conservative (control still starts at a zero estimate + mean-cost projection; use a
   prelaunch/parent timing estimate for initial admission and an upper-bound, not mean, projection).

After fixing: rebuild notebook+snapshot+manifest (`python scripts/build_exp061_deepcenter_tta.py` then
copy into `snapshot/` + regenerate `manifest.json`), re-run `scripts/test_exp061_behavioral.py` +
`scripts/validate_exp061_notebook.py`, then a FRESH `scripts/request_codex_review.py exp_061_deepcenter_tta`.
Honest note: Codex flagged that some items (byte-parity, feasibility) arguably belong INSIDE the authorized
run; a leaner pass may still REVISE. Consider whether continued no-GPU iteration is worth it vs. option B.

**Dev note:** local test run requires numpy — installed into `.venv` this session (numpy 2.5.3, not committed).

**B reminder still ARMED** (`STATE.json.pending_followup`): after exp_061's LB result, remind the user to
do option B (larger 0.15/0.12 safe-div threshold move).

---

## (SUPERSEDED 2026-09-18 content below — exp_060 has since completed: Public LB 0.947 == parent, a null)

## TL;DR — where the project is right now

**New best Public LB = 0.947** (`repro_059`, authenticated submission 56313491) — a verbatim
copy of a public 0.947 notebook, same Pilkwang checkpoints as our 0.944, so the +0.003 is 100%
post-processing/TTA. Backfilled to `experiments/repro_059_public_0947_exact_copy/`.

**Active experiment: `exp_060_deepcenter_safe_div_threshold_sweep` — LAUNCHED on Kaggle, GPU
running, awaiting completion.**
- Kernel: `lingxd/biohub-exp060-deepcenter-safe-div-threshold-sweep` (v1),
  https://www.kaggle.com/code/lingxd/biohub-exp060-deepcenter-safe-div-threshold-sweep
- Launched 2026-09-18 by **manual `kaggle kernels push`** (outside the controller), like repro_059.
- Parent = repro_059 (0.947). It sweeps the DeepCenter safe-division accept threshold
  **{0.20 control, 0.18, 0.22}** on the frozen 0.947 pipeline, pinning everything else. Division
  is the known bottleneck; on the parent the 0.20 gate accepts 316 / **rejects 414** candidate
  divisions, so 0.18/0.22 WILL move the accepted set. **0.18 is the primary arm** (division is
  FN-dominated: held-out 3/1/9).
- ~1.3–1.6 GPU-h expected; a 2.0-h SIGALRM watchdog enforces the budget. **No auto LB submission.**

---

## >>> NEXT STEP (what Claude should tell the user / do next session) <<<

**First, check whether the Kaggle run has finished** (the user will usually say so; do NOT poll).

### A. If the exp_060 run has COMPLETED
1. Pull the kernel output: `kaggle kernels output lingxd/biohub-exp060-deepcenter-safe-div-threshold-sweep -p <dir>`.
2. **Verify the integrity gate (metrics.json is authoritative):**
   - `exp060_threshold_sweep_integrity_passed == true`, and
   - `arm_submission_sha256.thr020 == d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60`
     (the 0.20 arm must byte-reproduce the parent 0.947 submission — this is the real-pipeline proof).
   - If the gate is False or the SHA mismatches → the run is INVALID; do not trust the 0.18/0.22
     arms; diagnose from `metrics.json.checks` + `exp060/exp060_telemetry.json`.
3. **Analyze the division telemetry** (`exp060/exp060_telemetry.json`): `delta_vs_control.thr018`
   and `.thr022` — how many final forks/edges each arm added/removed vs 0.20, with full node IDs;
   plus `candidate_counts` (survived_final, missing_bypass). This tells us whether 0.18 recovers
   real missed divisions (FN) or just adds false ones.
4. **Then decide the LB submission** (SEPARATE user authorization). ⚠️ The competition is
   **notebook-only** (code submission): the LB scores the notebook's OUTPUT `submission.csv`, but
   this notebook's main `submission.csv` is the parent 0.947 and the arms are in `exp060/`. To
   score the **0.18 arm** on the LB you need a variant notebook whose OUTPUT `submission.csv` IS the
   0.18 arm — cleanest is to add an env flag (e.g. `BIOHUB_EXP060_PROMOTE_ARM=thr018`) that copies
   `exp060/submission_thr018.csv` to `SUBMISSION_PATH` at the end, re-run, then `competition_submit_code`.
   Decision rule vs 0.947: **≥0.948 adopt** that threshold as the new parent; **==0.947** unresolved
   below displayed precision; **≤0.946** revert, retain repro_059.

### B. If the run has NOT finished / failed
- Not finished: wait (no polling). Failed: pull output/logs, read `metrics.json` (the watchdog and
  outer handler write a fail-closed metrics.json even on error/timeout), diagnose, report — do not
  relaunch without user go-ahead.

---

## How exp_060 got here (this session, in order)

1. **User reported "0.974" — it was actually 0.947.** Authenticated Kaggle history showed the newest
   submission (56313491) = `repro_059`, a verbatim copy of a public 0.947 notebook, **Public LB
   0.947** (+0.003 vs 0.944). Backfilled its provenance; adopted 0.947 as working parent; recorded
   the user's new policy that **LB submission count is no longer a constraint** (LB is now a usable
   held-out signal).
2. **Recon:** the public frontier is ~0.970 but those are private/unshared; the reproducible public
   cluster all shares the same Pilkwang checkpoints (no better model to steal). No verified public
   notebook clearly above 0.947 was found. → improve ON 0.947.
3. **Dissected 0.947 vs 0.944:** identical model; the +0.003 = DeepCenter(division) TTA ON +
   secondary edge-feature TTA ON + **DeepCenter safe-div threshold 0.25→0.20** + an embedded
   held-out PP-sweep that picked `tight55` (MOTION_RELINK_TIGHT_UM 6.0→5.5). Division/TTA is exactly
   where we never looked.
4. **Strategy (Codex `gpt-6-astra` low): 3 rounds → CONSENSUS.** Codex redirected the first probe
   from "Z-TTA" to the **safe-div threshold micro-sweep** (better-isolated, cheaper). Records:
   `docs/research/exp060_codex_challenge_v1..v3.md`, proposal `exp060_deepcenter_division_tta_proposal.md`.
5. **Recovered the parent's authoritative resolved config** from `repro_059`'s kernel OUTPUT
   (`ppsweep_selected.json` → `{MOTION_RELINK_TIGHT_UM: 5.5}`; parent submission SHA `d3453380`).
6. **Built the implementation** (purely additive; parent notebook byte-unchanged, parity by strip):
   `scripts/exp060_threshold_sweep.py` + `scripts/build_exp060_threshold_sweep.py` +
   `scripts/validate_exp060_notebook.py` + `scripts/test_exp060_behavioral.py` +
   `configs/exp_060_deepcenter_safe_div_threshold_sweep.yaml`.
7. **Admission — 9 more Codex rounds.** 5 custom-prompt admission rounds (v1..v5) → **PASS**; then
   the mandated controller admission (`request_codex_review.py`, generic prompt) went **4 rounds,
   all REVISE**. Every fixable finding was fixed and re-confirmed by Codex (byte-parity, fail-closed
   gate incl. nonfinite-as-missing detection + telemetry-persistence gate + commit-time deadline
   recheck, whole-run watchdog with GPU child reaping + KeyboardInterrupt, 74-global+env+threshold
   config fingerprint + shared-input immutability, both-daughter fork survival + exact edge deltas).
   The **standing objection is CIRCULAR** — it demands verifying the REAL GPU postprocessing pipeline
   *locally*, which needs the very GPU run the review gates. Full trail:
   `experiments/exp_060_.../admission_review_v1..v4.md` + `formal_admission_status.md`.
8. **User authorized launch despite the formal REVISE** (core verified across **12 Codex rounds**;
   residuals are verification-depth/process, not correctness/leakage; the runtime 0.20 byte-parity
   assert IS the real-pipeline proof). Launched by manual push.

---

## Guardrails (current)

- **exp_060 is a diagnostic-style probe.** Its LB submission (0.18/0.22 arms) is a SEPARATE explicit
  user authorization, needs the arm-promotion variant notebook (competition is notebook-only), and
  is compared to 0.947 by the decision rule above.
- **Submission count is no longer a research constraint** (user, 2026-09-18) — the Public LB may be
  used directly and repeatedly as the held-out validation signal. Still record every submission in
  `SUBMISSION_BUDGET.json` with authenticated `score_source`; never auto-submit without the user asking.
- **Standing transfer lesson:** train16 proxy gains have twice failed to transfer (exp_055, exp_057).
  Prefer distribution-general (model/representation/TTA) levers; validate on the LB, not train16.
- Preserve **six protected GPU hours** and **≥10% weekly allowance** (~26 h remain; a ~1.5 h run is
  affordable). Every inference policy stays ground-truth-free and specimen/video-blind. Never
  `git add -f` `.kaggle/` or `.private/`.
- The controller `launch` gate enforces a Codex-PASS review; exp_060 was launched OUTSIDE it by
  explicit user authorization (documented). Do not silently bypass the gate for a future experiment
  without the user's explicit call, and Claude must never play the Codex reviewer role.

---

## Key files / pointers

- **Active:** `experiments/exp_060_deepcenter_safe_div_threshold_sweep/` — `build_status.md`
  (design + recovered parent config + headroom diagnostic), `admission_review_v1..v4.md`,
  `formal_admission_status.md` (the 4 formal rounds + convergence conclusion), snapshot under
  `snapshot/`. Built notebook: `.private/current/exp060_deepcenter_safe_div_threshold_sweep.ipynb`.
- **New parent:** `experiments/repro_059_public_0947_exact_copy/` — `PROVENANCE.md` (0.947 dissection
  + public-frontier recon), `experiment.json`, `artifacts/ppsweep_selected.json` (resolved config).
- **Implementation:** `scripts/exp060_threshold_sweep.py`, `scripts/build_exp060_threshold_sweep.py`,
  `scripts/validate_exp060_notebook.py`, `scripts/test_exp060_behavioral.py`,
  `configs/exp_060_deepcenter_safe_div_threshold_sweep.yaml`.
- **Strategy/challenge:** `docs/research/exp060_deepcenter_division_tta_proposal.md` (v3 CONSENSUS),
  `exp060_codex_challenge_v1..v3.md`, `docs/research/transfer_failure_analysis_and_direction.md`.
- **Canonical state:** `STATE.json` (`exp060_launch` block has the launch record + on-completion
  steps; regenerates the `CLAUDE.md`/`GOAL.md`/`AGENTS.md` checkpoint via `scripts/render_checkpoint.py`).
- **Kaggle:** run `kaggle kernels status lingxd/biohub-exp060-deepcenter-safe-div-threshold-sweep`
  and `kaggle kernels output ...` to check/pull; `kaggle competitions submissions -c biohub-cell-tracking-during-development`
  for authenticated LB history.
- **Codex reviews** used model `gpt-6-astra` effort `low` (via `request_codex_review.py` with a
  temporary `~/.codex/config.toml` model swap that is always restored).
- **Prior superseded:** exp_058 division diagnostic (BLOCK #2, never launched) is SHELVED — the
  parent moved to 0.947 and the LB is now the cheaper truth.

---

## Open decisions for the user (next session)

1. After the run completes and 0.20 parity verifies: **authorize the LB submission of the 0.18 arm**
   (and/or 0.22)? This needs the arm-promotion variant notebook + `competition_submit_code`.
2. If 0.18 ≥ 0.948 → adopt as new parent and probe a neighbor; if ==0.947 → the division gate is
   LB-insensitive at this bracket, pivot to the next division lever (e.g. corrected Z-reflection
   DeepCenter TTA = the deferred **exp_061**, or a division-candidate-generation change).
3. Git: this session's work is uncommitted on branch `exp058-v3-doc-reconcile-block2`. Say the word
   to commit/push (competition-period publishing is your call).
