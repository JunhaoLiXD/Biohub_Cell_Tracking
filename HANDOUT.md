# Session Handout — updated 2026-09-18

Purpose: hand this session's work to the next session AND to the user. Read this FIRST,
then the deeper authority in order: `STATE.json`, `experiments/exp_060_deepcenter_safe_div_threshold_sweep/`
(build_status.md, formal_admission_status.md), `.private/current/CONTINUATION.md`,
`docs/research/PROJECT_HANDOFF.md`.

If anything here disagrees with `STATE.json`, **`STATE.json` wins** (this file is a
human-readable summary; `STATE.json` is the machine source of truth).

---

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
