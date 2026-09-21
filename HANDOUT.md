# Session Handout — updated 2026-09-21

Purpose: hand the current state to the next session AND to the user. Read this FIRST, then the
deeper authority in order: `STATE.json`, `experiments/exp_061_deepcenter_tta/` (experiment.json,
review.md), `.private/current/CONTINUATION.md`, `docs/research/PROJECT_HANDOFF.md`.

If anything here disagrees with `STATE.json`, **`STATE.json` wins** (this file is a human-readable
summary; `STATE.json` is the machine source of truth).

---

## 🚀 CURRENT: exp_061 is RUNNING on Kaggle GPU — awaiting completion

Best Public LB still **0.947** (`repro_059`). Nothing new has scored yet.

- **Kernel:** `lingxd/biohub-exp061-deepcenter-tta` (v1, **private**, T4, internet off) — **RUNNING**.
  https://www.kaggle.com/code/lingxd/biohub-exp061-deepcenter-tta
- **Launched** 2026-09-21 by manual `kaggle kernels push` (outside the controller gate, under explicit
  user launch authorization — same path as exp_060/repro_059).
- **What it is:** DeepCenter repair-heatmap TTA probe on the frozen 0.947 pipeline, 3 arms
  **xyonly** (byte-parity control) / **zon** (add Z-reflection, primary) / **xyd4** (XY-D4 repair).
  Parent = repro_059 (0.947). 2.0 h SIGALRM watchdog. **No auto LB submission.**
- **Notebook sha256** `2a8c65f1f45651245598f7a768213c845d54664f6c15b99a43f45fe85585b656` (== validated snapshot).
- **GPU:** 2.0 h reserved (`GPU_BUDGET.json`; remaining 24.493 → 22.493) — reconcile to actual on completion.

**Do NOT poll.** The user will notify when it finishes.

---

## >>> WHEN THE RUN FINISHES (what to do) <<<

### A. If it COMPLETED
1. **Pull the output:** `kaggle kernels output lingxd/biohub-exp061-deepcenter-tta -p <dir>`.
2. **Verify the integrity gate** (`metrics.json` is authoritative):
   - `exp061_deepcenter_tta_integrity_passed == true`, and
   - the **xyonly** arm submission byte-reproduces the parent 0.947 submission
     (sha256 `d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60`) — this is the
     real-pipeline proof. If the gate is False or the xyonly SHA mismatches → run INVALID; do not
     trust zon/xyd4; diagnose from `metrics.json` + the telemetry.
3. **Read the `mechanism{}` block per arm** (in `metrics.json`): for `zon` and `xyd4` check
   `heatmap_differs_from_xyonly` / `submission_differs_from_xyonly` / `verified_null` / `active`.
   - `verified_null` (heatmap identical to xyonly) = the TTA change had **zero** effect → a recorded
     mechanism null, NOT a bug (and it blocks a duplicate LB submission).
   - `active` (heatmap differs) = the arm actually changed the division read → worth an LB submission.
4. **Reconcile GPU hours:** replace `actual_hours: null` for `exp_061_deepcenter_tta` in
   `GPU_BUDGET.json` with the kernel's real runtime.
5. **Then decide the LB submission** (SEPARATE explicit user authorization). ⚠️ Competition is
   **notebook-only**: the LB scores the notebook's OUTPUT `submission.csv`, which is the parent 0.947
   — the arms are written to a side dir. To score an **active** arm you need an arm-promotion variant
   notebook whose OUTPUT `submission.csv` IS that arm, then `competition_submit_code`.
   Decision vs 0.947: **≥0.948 adopt** as new parent · **==0.947** sub-precision null → then do option
   **B** (larger 0.15/0.12 safe-div move, still ARMED) · **≤0.946** revert, keep repro_059.

### B. If it FAILED / timed out
Pull output + logs; read `metrics.json` (the watchdog + outer handler write a fail-closed
`metrics.json` even on error/timeout); diagnose; report. Do **not** relaunch without user go-ahead.
Reconcile the GPU reservation to actual runtime if known.

---

## How we got here (compressed)

- **The parent:** `repro_059` = a verbatim copy of a public **0.947** notebook on the same Pilkwang
  checkpoints as our 0.944, so the +0.003 is 100% post-processing/TTA. Recon found no reproducible
  public checkpoint above 0.947 → improve ON 0.947.
- **Three straight LB nulls** on the frozen pipeline: exp_055 edge (0.942==0.942), exp_057 EMA
  (0.944==0.944), exp_060 safe-div threshold (0.947==0.947). Division is weighted only 0.1 in the
  aggregate, so tiny division tweaks don't register at 3-decimal LB. User chose pivot **(A) = exp_061**
  (change division CANDIDATE GENERATION via DeepCenter TTA, not just the accept gate).
- **exp_061 strategy** reached CONSENSUS (Codex gpt-6-astra, v1–v4 REVISE → v5 CONSENSUS).
- **Admission loop diagnosed (this session):** exp_061 went v1→v4 all REVISE, like exp_060's 4 formal
  REVISE rounds. Root cause is structural — a **zero-GPU local harness cannot prove real-GPU-pipeline
  behaviour**, so a diligent reviewer always finds another "verify X locally" item and it never goes
  green. Decision: split genuine correctness bugs from verification-depth items; fix the former, let
  the LB be the truth. (Recorded as risk #8 in `PROJECT_RISK_REVIEW.md`.)
- **v4 #1 REAL BUG fixed:** `EXP061_PARENT_BASE_DEFAULTS` (`scripts/exp061_deepcenter_tta.py`) was
  built from the parent's *declaration fallbacks*, but the parent sets `os.environ['BIOHUB_*']`
  overrides BEFORE the declarations → 18-knob mismatch that would have fail-closed the real run. Rebuilt
  the table to the parent-**effective** config (derived programmatically from the notebook env-setup
  block, `env override if set else fallback`, + the tight55 5.5 override); strengthened `test_N` to
  parse BOTH layers with a regression guard. **Both local gates PASS**
  (`test_exp061_behavioral.py`, `validate_exp061_notebook.py`); snapshot + manifest rebuilt.
- **User authorized launch directly** (informed v4 #2–#6 remain open) → pushed → RUNNING.

---

## Open items / guardrails

- **v4 #2–#6 remain OPEN** (deferred/downgraded — verification-depth, NOT correctness/leakage): config-key
  completeness incl. the adaptive short-track rescue family (#2), fail-fast-before-arms ordering (#3),
  partial-run `all_started_arms_completed` gate (#4), per-frame view-geometry validation (#5), stage
  edge identities-not-counts + conservative first-arm admission (#6). Detail: `experiments/
  exp_061_deepcenter_tta/review.md`. On the corrected config the runtime config gate already fails
  closed on drift, so these are defense-in-depth. Revisit only if a future run motivates them.
- **B reminder ARMED** (`STATE.json.pending_followup`): after exp_061's LB result, remind the user to do
  option **B** (larger 0.15/0.12 safe-div threshold move).
- **Submission count is not a research constraint** (user, 2026-09-18) — the Public LB is a usable
  held-out signal. Still record every submission in `SUBMISSION_BUDGET.json`; never auto-submit without
  the user asking.
- **Transfer lesson:** train16 proxy gains twice failed to transfer (exp_055, exp_057). Prefer
  distribution-general levers; validate on the LB, not train16.
- **Budget:** preserve six protected GPU hours + ≥10% weekly allowance (~22.5 h remain after the
  exp_061 reservation). Every inference policy stays ground-truth-free and specimen/video-blind. Never
  `git add -f` `.kaggle/` or `.private/`.
- **Launch governance:** the controller `launch` gate enforces a Codex-PASS review; exp_060 and exp_061
  were launched OUTSIDE it by explicit user authorization (documented). Do not silently bypass the gate
  for a future experiment without the user's explicit call, and **Claude must never play the Codex
  reviewer role.** (Risk #9 in `PROJECT_RISK_REVIEW.md`.)
- **Uncommitted:** this whole arc's records + the v4 #1 fix + the launch ledger are uncommitted on
  branch `exp058-v3-doc-reconcile-block2`; test dev-deps (numpy 2.5.3, tzdata) are in `.venv`, unpinned.
  Say the word to commit (artifacts stay ignored; publishing during the competition is your call).

---

## Key files / pointers

- **Active experiment:** `experiments/exp_061_deepcenter_tta/` — `experiment.json`, `review.md`
  (Codex v4 REVISE record), `snapshot/` (validated: nb sha `2a8c65f1…`). Built notebook:
  `.private/current/exp061_deepcenter_tta.ipynb`.
- **Implementation:** `scripts/exp061_deepcenter_tta.py` (the appended module + frozen config +
  runtime gates), `scripts/build_exp061_deepcenter_tta.py`, `scripts/validate_exp061_notebook.py`,
  `scripts/test_exp061_behavioral.py`.
- **Strategy:** `docs/research/exp061_z_reflection_deepcenter_tta_proposal.md` (v5 CONSENSUS) +
  `exp061_codex_challenge_v1..v5.md`.
- **Parent:** `experiments/repro_059_public_0947_exact_copy/` — `PROVENANCE.md` (0.947 dissection +
  public-frontier recon), `artifacts/ppsweep_selected.json` (`MOTION_RELINK_TIGHT_UM: 5.5`), snapshot
  `kernel-metadata.json` (dataset/GPU config mirrored for exp_061).
- **Canonical state:** `STATE.json` (`exp061_launch` block = launch record + on-completion steps;
  regenerates the `CLAUDE.md`/`GOAL.md`/`AGENTS.md` checkpoint via `scripts/render_checkpoint.py`).
- **Risk register:** `PROJECT_RISK_REVIEW.md` (2026-09-21 review on top).
- **Kaggle:** `kaggle kernels status lingxd/biohub-exp061-deepcenter-tta` /
  `kaggle kernels output ...`; `kaggle competitions submissions -c biohub-cell-tracking-during-development`
  for authenticated LB history.
- **Codex reviews** used model `gpt-6-astra` effort `low` (via `request_codex_review.py`, which swaps
  `~/.codex/config.toml` temporarily and always restores it).
- **History:** exp_060 (safe-div threshold sweep, 0.947==0.947 null) is COMPLETE; exp_058 division
  diagnostic is SHELVED. Both superseded by the 0.947 parent + LB-as-truth policy.
