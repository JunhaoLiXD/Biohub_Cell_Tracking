# Session Handout — updated 2026-09-23 (exp_061 arc ABANDONED after 5 failed transports; recon done; awaiting direction)

Purpose: hand the current state to the next session AND to the user. Read this FIRST, then the
deeper authority in order: `STATE.json`, the active `experiments/exp_061_zon_lb_submission_repair_v5/`
and `.../v4/` records, `.private/current/CONTINUATION.md`, `docs/research/PROJECT_HANDOFF.md`.

If anything here disagrees with `STATE.json`, **`STATE.json` wins** (this file is a human-readable
summary; `STATE.json` is the machine source of truth).

---

## >>> NEXT SESSION: START HERE <<<

**Nothing is running. Nothing is pending on the LB. Nothing is authorized. Awaiting the user's
choice of the next lever.**

### Where we stand — read this first

| fact | value |
|---|---|
| our best Public LB | **0.947** (repro_059, submission 56313491) |
| **LB rank-200 cutoff** | **0.949** — our 0.947 is *outside the top 200* |
| LB top / top-3 | 0.975 / 0.975-0.973-0.970 |
| **deadline** | **2026-09-29 23:59** — about 6 days |
| daily submission cap | **5** (authenticated; older records said 3) |
| GPU remaining | **20.399 h**, no reservations outstanding |
| working parent | `repro_059_public_0947_exact_copy` — unchanged |

### exp_061 is closed

Submission `56493252` (v5) failed with the same hidden-rerun error as v4 and v2. That is **five
consecutive failed LB transports across three distinct mechanisms**, zero scores, 3.094 GPU-h.
The user abandoned the whole arc. v5 had *confirmed* both scale fixes active on the real pipeline
with byte-identical predictions, so **neither the watchdog nor the 20 GB cap was the cause** — a
third, unidentified property of the hidden rerun is, and the tracebacks are not exposed to us.

**The zon Z-reflection TTA is UNRESOLVED, not falsified.** It was never scored.

**Transport lesson (important):** the only deployment pattern in this project with a *proven*
hidden-rerun record is **exp_060's single-config variant notebook** (submission 56361673, COMPLETE
at 0.947). Use that pattern for any future LB run. Do not build another bespoke deployment adapter.

### The recon — and the three levers now available

Full record: **`docs/research/public_frontier_recon_2026-09-23.md`**. Headlines:

- **No verified public notebook beats 0.947.** Same conclusion as 09-18. Every candidate shares the
  same three Pilkwang checkpoints. The four new high-vote notebooks claim nothing above 0.947
  (`evgendvorkin/...0-947...` is explicitly 0.947). The `haideptry` "SOTA 0.948+" titles are
  **unverified** — that author is not in the top 200.
- **But three concrete, portable levers are now public on our exact 0.947 base** (they self-report
  `source_notebook_sha256 3e65ca69…`, the documented upstream of repro_059, `metric_hack_used:
  false`):

| # | lever | why | rank |
|---|---|---|---|
| 1 | **Mutual-best / relative-rank edge association** (`BIOHUB_LB_SCORING_MODE=mutual_best`, β 0.20→0.12) | Perturbs **edge association, ~85–90% of the metric**. Every probe we ran (exp_055/057/060/061) moved **division, weight 0.1** — the structural reason they were sub-precision nulls. First shared lever aimed at the heavy term. | **FIRST** |
| 2 | **Density-adaptive overrides** (measured cells/frame → tight/relaxed/velocity/bonus) | Generalizes the single global `tight55` we froze; density varies ~11× across embryos. **Verified specimen-blind** — zero movie names in code, dynamic test discovery. | SECOND |
| 3 | **DivNet 3D mitosis gate** (`giorgosi/biohub-divnet-v2`, public, 5.2 MB) | First **model-level** addition available to us — but division-weighted, so least likely to register. | THIRD |

Lever 1 has a published pedigree: `yudaiyamauchi` ran a systematic **A–E** series on this axis
(A hard-negative margin, B hard-negative strong, C disagreement-adaptive, D relative rank,
E mutual-best); `haideptry` carries `BIOHUB_LB_EXPLORATION_ID="e-mutual-best"`, so **E is the
survivor**. Those notebooks have 0–2 votes — not priced in.

**Honest caveat:** all three headline numbers are self-reported by an author absent from the top
200. They are hypotheses worth one cheap LB probe each, not known gains. And the 0.955–0.966 band
is **not explained** by anything public I could find.

### The ARMED option-B reminder — delivered, and deprioritised

It is hereby delivered: option B = a larger safe-div move (0.15/0.12). But it is **division-side**,
the same 0.1-weighted class that produced three straight nulls, so on the recon evidence it now
ranks **below levers 1 and 2**. Not withdrawn; the choice is the user's.

---

## What happened this session (2026-09-23, later)

### v4's submission errored; v4 is abandoned

`56481730` resolved as `COMPLETE_WITH_ERROR` — the *same* generic message as v2's `56454236`
("notebook hit an unhandled error while rerunning your code"), no score. **User decision: drop v4,
do not resubmit it.**

**This weakens the scale hypothesis that motivated v5.** v4's visible run finished in 32.5 min using
**27%** of its watchdog and **22%** of the 20 GB `/kaggle/working` cap. Unless the hidden dataset is
**≥3.7×** the public one, *neither* hazard v5 removes can explain that failure — so a third unknown
cause may well remain. The pre-submit audit found no defect capable of producing a wrong score, so
the failure lies in the rerun environment or its scale, not in the zon prediction policy.

### v5 ran, was collected and audited, and went to the LB

`lingxd/biohub-exp061-zon-deploy-v5` v1 ran **COMPLETE in 1992.12 s (33.2 min)**. Collected once
(no polling) and audited read-only — receipt:
`experiments/exp_061_zon_lb_submission_repair_v5/collect-audit.json`. **Verdict PASS.**

| check | result |
|---|---|
| integrity gate | `exp061_zon_deployment_integrity_passed` true — **19/19** checks true |
| zon CSV sha256 | `2593a543…6c840a1` — byte-identical to the historical hash **and** to v4's current run |
| size | 241365 rows / 122813 nodes / 118552 edges |
| `config_equal_frozen_parent` | true (tight55 pinned) |
| checkpoint provenance | verified, deepcenter `8040999a…` |
| views/frame | 16 incl. 8 Z-reflected (`ZV0…ZTa`), 267 distinct frames, 4272 forwards @ 0.1023 s |
| numerical health | 0 nonfinite heatmaps/logits, 0 cache-integrity failures, `run_exception` null, 845 veto records accounted |
| **fix #1** deadline | `is_competition_rerun` false, `hard_stop_seconds` 7200, elapsed 1992.1 s, 5207.9 s left — visible-run branch chosen correctly, consistency guard did not refuse publication |
| **fix #2** cache | root `/kaggle/temp/exp061_viewcache`, `view_cache_outside_working_dir` true, no fallback; **collected output 58.75 MB / 182 files** vs v4's ~4.5 GB, **0** viewcache entries |

The identical hash is the point: v5's changes are resource-only and moved no predicted value.
**Caveat:** a *visible* run cannot exercise the 30600 s rerun branch — only the local executable
deadline matrix does.

On that audit, and on the user's instruction, v5 went to the LB → `56493252` (cap 5/day, 1 used in
the rolling 24 h, allowed).

### GPU ledger reconciled

Three stale 2.0 h reservations (v2, v4, v5) released and replaced with actuals: v2 **2.0 h**
(conservative upper bound — wall-clock was never captured), v4 **0.541 h** (1947.5 s), v5 **0.553 h**
(1992.12 s). Net draw 3.094 h; **2.906 h returned to the pool**. `remaining_hours` 23.493 →
**20.399**, `reserved_hours` now empty — no GPU work outstanding.

Also corrected: the authenticated daily submission cap is **5**, not the 3 recorded in older entries
(no past verdict changes under the true cap).

---

## Earlier this session: the v4 audit that produced v5

`lingxd/biohub-exp061-zon-deploy-v4` v1 ran **COMPLETE in 32.5 min** (1947.5 s). Claude audited it
**read-only** and found **no defect that could produce a wrong score** (same check table as v5's
above, plus: test discovery is a dynamic `TEST_DIR.iterdir()` over `*.zarr` with no hardcoded movie
names, and the pushed code matched the snapshot except the one-line `EXPERIMENT_ID` injection).

On that audit the user authorized one LB submission → `56481730`, since errored and abandoned.

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
  4. `56481730` v4 zon-only, 32.5 min → **same unhandled rerun error**, no score ⇒ **abandoned**.
  5. `56493252` v5 (same predictions, both scale hazards removed) → **PENDING**.
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
- **v5 does not prove the scale hypothesis — and v4's failure argues against it.** The v2 and v4 hidden
  tracebacks are unavailable. v5 removes two ways a rerun can abort, but v4 died from a 32.5-min run with
  3.7× watchdog and 4.5× disk headroom, so unless the hidden set is ≥3.7× the public one a third unknown
  cause remains.
- **B reminder still ARMED** (`STATE.json.pending_followup`): after the zon LB result, remind the user to
  do option **B** (larger 0.15/0.12 safe-div threshold move).
- **Submission count is not a research constraint** (user, 2026-09-18) — the Public LB is a usable
  held-out signal. Still record every submission in `SUBMISSION_BUDGET.json`; **never auto-submit without
  the user asking**. Kaggle's own cap is a platform fact — **5/day**, authenticated 2026-09-23 (older
  entries recorded 3) — check remote history before submitting. Competition deadline **2026-09-29 23:59**.
- **Transfer lesson:** train16 proxy gains twice failed to transfer (exp_055, exp_057). Prefer
  distribution-general levers; validate on the LB, not train16.
- **Budget:** remaining **20.399 h**, six protected hours preserved; **no reservations outstanding**
  (v2/v4/v5 reconciled 2026-09-23 — v2 2.0 h upper bound, v4 0.541 h, v5 0.553 h). Every inference policy
  stays ground-truth-free and specimen/video-blind. Never `git add -f` `.kaggle/` or `.private/`.
- **Launch governance:** the controller `launch` gate enforces a Codex-PASS review; exp_060, exp_061 and
  both v4/v5 runs were launched OUTSIDE it by explicit user authorization (documented). Do not silently
  bypass the gate without the user's explicit call. (Risk #9 in `PROJECT_RISK_REVIEW.md`.)
- **Dev deps:** numpy 2.5.3 + tzdata are in `.venv`, unpinned (test-only).

---

## Key files / pointers

- **Active (v5, LB-pending):** `experiments/exp_061_zon_lb_submission_repair_v5/` — `experiment.json`,
  `collect-audit.json` (the read-only run audit), `leaderboard-submission.json` (56493252),
  `artifacts/` (metrics, telemetry, receipt — CSVs and the scratch cache are not committed),
  `strategy_amendment_v1.md`, `snapshot/` (nb sha `da4d933b…`), `user-waiver-smoke.json`,
  `kaggle-launch.log`. Implementation: `scripts/build_exp061_zon_submission_repair_v5.py`,
  `scripts/exp061_zon_deployment_v5.py`, `scripts/validate_exp061_zon_deployment_v5.py`,
  `scripts/launch_exp061_v5_user_waiver.py`.
- **v4 (errored, abandoned):** `experiments/exp_061_zon_lb_submission_repair_v4/` — `experiment.json`,
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
