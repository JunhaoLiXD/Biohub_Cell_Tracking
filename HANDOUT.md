# Session Handout — updated 2026-09-23 (v4 LB submitted + PENDING; v5 fallback built & RUNNING)

Purpose: hand the current state to the next session AND to the user. Read this FIRST, then the
deeper authority in order: `STATE.json`, the active `experiments/exp_061_zon_lb_submission_repair_v5/`
and `.../v4/` records, `.private/current/CONTINUATION.md`, `docs/research/PROJECT_HANDOFF.md`.

If anything here disagrees with `STATE.json`, **`STATE.json` wins** (this file is a human-readable
summary; `STATE.json` is the machine source of truth).

---

## >>> NEXT SESSION: START HERE <<<

**Two things are in flight. Neither may be polled — the user reports both.**

### 1. Public LB submission `56481730` (v4 zon) — PENDING

Submitted 2026-09-23T03:47:28Z from kernel `lingxd/biohub-exp061-zon-deploy-v4` v1 via
`competition_submit_code`. This is the **fourth** attempt to get any score back for the zon arm.

When the user reports it:

```bash
# one authenticated query, no loop
python -c "from kaggle.api.kaggle_api_extended import KaggleApi; a=KaggleApi(); a.authenticate(); \
[print(s.ref, s.status, s.public_score, s.error_description) for s in \
 a.competition_submissions('biohub-cell-tracking-during-development')[:2]]"
```

Record the outcome in **`SUBMISSION_BUDGET.json`** (entry 56481730, status PENDING → final),
**`STATE.json.exp061_v4_deploy.lb_submission`**, and
**`experiments/exp_061_zon_lb_submission_repair_v4/leaderboard-submission.json`**. Then:

| result | action |
|---|---|
| **≥0.948** | Z-reflection DeepCenter TTA is a real gain → adopt zon as the new parent, record it, probe a neighbour. **v5 becomes unnecessary** for scoring. |
| **==0.947** | a **fourth** sub-precision null → fire the ARMED **option B** (larger 0.15/0.12 safe-div move) and treat frozen-pipeline post-processing as near-exhausted. |
| **≤0.946** | zon's division changes are net-harmful → revert, keep repro_059 0.947. |
| **errors again** | **do NOT resubmit v4.** Go to §2 — v5 exists precisely for this. |

### 2. v5 fallback kernel — RUNNING

`lingxd/biohub-exp061-zon-deploy-v5` v1, pushed 2026-09-23T04:08:52Z, 2.0 GPU-h reserved.
When the user says it finished, **collect once** and verify:

```bash
kaggle kernels status lingxd/biohub-exp061-zon-deploy-v5
kaggle kernels output lingxd/biohub-exp061-zon-deploy-v5 -p <scratchpad-dir>
```

- current-run zon CSV sha256 still `2593a5438a17e5649736fcd6ad2f7af4c2fa8f822a759e9f51d877cdf6c840a1`
- `feasibility_worksheet.view_cache_outside_working_dir == true`
- `feasibility_worksheet.is_competition_rerun == false` and `hard_stop_seconds == 7200` on this visible run
- **the kernel output is no longer multi-GB** (that is the whole point of fix #2)
- reconcile actual GPU hours into `GPU_BUDGET.json`

**If `56481730` scored, v5 is a spare — do not submit it.** If `56481730` errored, v5 is the next
LB candidate and needs its **own explicit user authorization + a daily-cap check** before submitting.

---

## What happened this session (2026-09-23)

### v4 ran, was audited, and went to the LB

`lingxd/biohub-exp061-zon-deploy-v4` v1 ran **COMPLETE in 32.5 min** (1947.5 s). Claude audited it
**read-only** and found **no defect that could produce a wrong score**:

| check | result |
|---|---|
| zon CSV sha256 | `2593a543…6c840a1` — **exactly** the historical development hash |
| size | 241365 rows / 122813 nodes / 118552 edges |
| `config_equal_frozen_parent` | true (tight55 pinned) |
| checkpoint provenance | verified, deepcenter `8040999a…` |
| views/frame | 16 incl. 8 Z-reflected (`ZV0…ZTa`) |
| numerical health | no nonfinite heatmaps/logits, 0 cache-integrity failures, `run_exception` null, 845 veto records all accounted |
| test discovery | dynamic `TEST_DIR.iterdir()` over `*.zarr` — **no hardcoded movie names** |
| pushed vs snapshot | identical except the one-line `EXPERIMENT_ID` injection |

On that audit the user authorized one LB submission → `56481730`.

### The audit found two scale hazards — hence v5

Neither can mis-score; both **abort the hidden rerun**. Both trip near a **~4× larger** hidden workload:

1. **Hard `signal.alarm(7200)`** (cell 2), handler raises `KeyboardInterrupt`. v4 used 27% of it
   (3.7× headroom). **This is the leading hypothesis for the v2 failure** — v2's *visible* run already
   took ~2 h, so its hidden rerun had essentially zero headroom → "notebook hit an unhandled error",
   `totalBytes=0`.
2. **4.48 GB view cache under `/kaggle/working`** (4272 `.npy` files) — collected as kernel output and
   charged against the 20 GB cap (~4.5× headroom). Also why the v4 output was ~4.5 GB to download.

Note: a per-dataset budget abort is *graceful* but still yields no `submission.csv`, so it surfaces as
the same generic rerun error.

### v5 = both hazards fixed, zero prediction change

Built by `scripts/build_exp061_zon_submission_repair_v5.py`, which **hash-locks** the immutable v4
notebook (`39eba1b9…`) and module (`74e35298…`), copies parent cells 0–1 byte-for-byte, and confines
every cell-2 edit to `# exp061`-marked lines (a builder guard strips those lines and asserts the
remainder is identical — **it caught a mistake on the first run**).

- **Fix #1 — rerun-aware deadline.** 7200 s on a visible run (protects our 2.0 h reservation);
  **30600 s (8.5 h)** when Kaggle sets `KAGGLE_IS_COMPETITION_RERUN`; `BIOHUB_EXP061_HARD_STOP_SECONDS`
  overrides both. Cell 2 and the module derive it from the same environment, and the final cell
  **refuses to publish if they disagree**. 20-min finalization reserve unchanged.
- **Fix #2 — cache off the collected output path.** Scratch root order: explicit override →
  `/kaggle/temp` → platform temp → `WORKING_DIR` last resort. The fallback is reported in telemetry but
  **deliberately not gated** — a correct submission must never be withheld for a non-correctness reason.

Same views, same accumulation order, same bytes; only location and time ceiling differ.

**Bug caught while writing the tests:** the deadline-consistency guard was first placed *before* the
adapter unlinks the parent's `submission.csv`, so a mismatch would have left the parent 0.947 artifact
on disk to be scored silently — exactly the fallback this adapter exists to prevent. The guard now runs
**after** the unlink, and the validator asserts that ordering.

**Local gates, all PASS:** builder parity guard; `scripts/validate_exp061_zon_deployment_v5.py`
(8 groups — incl. an *executable* deadline matrix over `KAGGLE_IS_COMPETITION_RERUN` on/off/garbage/
override where cell 2 and the module must agree every time, scratch-root override/fallback/bad-override,
a mocked end-to-end run asserting no cache under `WORKING_DIR`, and a new deadline-mismatch publication
negative); `scripts/test_exp061_behavioral.py`.

---

## ⚠️ Governance: two one-time waivers, no Codex PASS

Both the **v4 kernel run** and the **v5 build+push** ran under explicit one-time user waivers of the
Codex admission gate. Both records carry `review.verdict = "NO_PASS"` and
`status = "WAIVED_BY_USER_FOR_ONE_V*_KERNEL_RUN"`. **Neither is a Codex PASS.** `require_codex_review`
stays true in policy. Claude audited v4 read-only and authored v5 — **Claude must never play the Codex
reviewer role.** External evidence for v5 = local gates only.

---

## How we got here (compressed)

- **The parent:** `repro_059` = verbatim copy of a public **0.947** notebook on the same Pilkwang
  checkpoints as our 0.944 → the +0.003 is 100% post-processing/TTA. Recon found no reproducible public
  checkpoint above 0.947 → improve ON 0.947.
- **Three straight LB nulls** on the frozen pipeline: exp_055 edge (0.942==0.942), exp_057 EMA
  (0.944==0.944), exp_060 safe-div threshold (0.947==0.947). Division is weighted only 0.1 in the
  aggregate, so tiny division tweaks don't register at 3-decimal LB. User chose pivot **(A) = exp_061**
  (change division CANDIDATE GENERATION via DeepCenter TTA, not just the accept gate).
- **exp_061 strategy** reached CONSENSUS (Codex gpt-6-astra, v1–v4 REVISE → v5 CONSENSUS). The run was
  clean and zon is the **first non-null mechanism in this arc**: heatmap `max_abs_delta` 0.142,
  safe-div accepted 316→318, +9 rows vs parent; xyonly == parent (control), xyd4 sub-threshold == parent.
- **Then four LB transport failures, three distinct causes:**
  1. `56442230` zon via a **static-copy** kernel → incorrect format.
  2. `56447637` xyonly (byte-identical to the known-good 0.947) via the **same copy** mechanism → same
     error. ⇒ proves the copy mechanism was the problem, not zon content. Code competitions **re-run the
     notebook** at scoring.
  3. `56454236` v2 **full-inference** notebook → visible run COMPLETE and audited, but the hidden rerun
     hit an unhandled error, `totalBytes=0`. ⇒ motivated the zon-only v3/v4 redesign.
  4. `56481730` v4 zon-only, 32.5 min → **PENDING** (this session).
- **Admission-loop lesson:** exp_060 and exp_061 each went 4+ formal REVISE rounds. Root cause is
  structural — a zero-GPU local harness cannot prove real-GPU-pipeline behaviour, so a diligent reviewer
  always finds another "verify X locally" item. Policy: split genuine correctness bugs from
  verification-depth items, fix the former, let the LB be the truth. (Risk #8 in `PROJECT_RISK_REVIEW.md`.)

---

## Open items / guardrails

- **v4 items #2–#6 remain OPEN** and are **inherited unchanged by v5** (verification-depth, NOT
  correctness/leakage): config-key completeness incl. the adaptive short-track rescue family (#2),
  fail-fast-before-arms ordering (#3), partial-run `all_started_arms_completed` gate (#4), per-frame
  view-geometry validation (#5), stage edge identities-not-counts (#6). Detail:
  `experiments/exp_061_deepcenter_tta/review.md`. The runtime config gate already fails closed on drift.
- **v5 does not prove the scale hypothesis.** The v2 and v4 hidden tracebacks are unavailable. v5 removes
  two ways a rerun can abort; a third unknown cause may remain.
- **B reminder still ARMED** (`STATE.json.pending_followup`): after the zon LB result, remind the user to
  do option **B** (larger 0.15/0.12 safe-div threshold move).
- **Submission count is not a research constraint** (user, 2026-09-18) — the Public LB is a usable
  held-out signal. Still record every submission in `SUBMISSION_BUDGET.json`; **never auto-submit without
  the user asking**. Kaggle's own 3/day cap is a platform fact — check remote history before submitting.
- **Transfer lesson:** train16 proxy gains twice failed to transfer (exp_055, exp_057). Prefer
  distribution-general levers; validate on the LB, not train16.
- **Budget:** remaining **23.493 h**, six protected hours preserved; reservations outstanding for v2/v4/v5
  (2.0 h each). v4's actual was ~0.54 h — **reconcile v4 and v5 actuals** when collecting. Every inference
  policy stays ground-truth-free and specimen/video-blind. Never `git add -f` `.kaggle/` or `.private/`.
- **Launch governance:** the controller `launch` gate enforces a Codex-PASS review; exp_060, exp_061 and
  both v4/v5 runs were launched OUTSIDE it by explicit user authorization (documented). Do not silently
  bypass the gate without the user's explicit call. (Risk #9 in `PROJECT_RISK_REVIEW.md`.)
- **Dev deps:** numpy 2.5.3 + tzdata are in `.venv`, unpinned (test-only).

---

## Key files / pointers

- **Active (v5):** `experiments/exp_061_zon_lb_submission_repair_v5/` — `experiment.json`,
  `strategy_amendment_v1.md`, `snapshot/` (nb sha `da4d933b…`), `user-waiver-smoke.json`,
  `kaggle-launch.log`. Implementation: `scripts/build_exp061_zon_submission_repair_v5.py`,
  `scripts/exp061_zon_deployment_v5.py`, `scripts/validate_exp061_zon_deployment_v5.py`,
  `scripts/launch_exp061_v5_user_waiver.py`.
- **v4 (LB-pending):** `experiments/exp_061_zon_lb_submission_repair_v4/` — `experiment.json`,
  `leaderboard-submission.json` (full pre-submit audit + the two scale hazards), `snapshot/`
  (nb sha `39eba1b9…`). Same four script roles with `_v4` suffixes.
- **Diagnosis:** `docs/research/exp061_three_submission_failure_diagnosis.md`,
  `docs/research/exp061_lb_submission_repair.md`.
- **Strategy:** `docs/research/exp061_z_reflection_deepcenter_tta_proposal.md` (v5 CONSENSUS) +
  `exp061_codex_challenge_v1..v5.md`.
- **Parent:** `experiments/repro_059_public_0947_exact_copy/` — `PROVENANCE.md` (0.947 dissection +
  public-frontier recon), `artifacts/ppsweep_selected.json` (`MOTION_RELINK_TIGHT_UM: 5.5`).
- **Canonical state:** `STATE.json` — blocks `exp061_v4_deploy` and `exp061_v5_deploy` carry the launch
  records, audits and on-completion steps. Regenerate the `CLAUDE.md`/`GOAL.md`/`AGENTS.md` checkpoint
  with `python scripts/render_checkpoint.py` after editing it (never hand-edit that block).
- **Risk register:** `PROJECT_RISK_REVIEW.md`.
- **Kaggle:** `kaggle kernels status|output lingxd/biohub-exp061-zon-deploy-v5`;
  `kaggle competitions submissions -c biohub-cell-tracking-during-development` for authenticated history.
- **Codex reviews** use model `gpt-6-astra` effort `low` via `request_codex_review.py` (swaps
  `~/.codex/config.toml` temporarily and always restores it).
- **History:** exp_060 (safe-div sweep, 0.947==0.947 null) COMPLETE; exp_058 division diagnostic SHELVED.
