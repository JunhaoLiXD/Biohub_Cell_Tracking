# Project Risk Review & Remediation — Biohub Cell Tracking

**Living document.** Newest review on top; older dated reviews below are preserved as historical
evidence (they record what was true and what was changed at the time, and are not rewritten).

- **2026-09-21** — refresh after the exp_055→exp_061 post-processing arc (three LB nulls) and the
  exp_061 launch. Reconciles the 2026-09-06 items and records new process/strategy risks. *(current)*
- **2026-09-06** — original whole-project hazard scan + remediation (repro_041 / exp_040 era).

---

## 2026-09-21 review — post-processing-null arc + admission-loop + manual launches

**Context shift since 2026-09-06.** The project moved from the repro_041/exp_040 era to a frozen
public **0.947** parent (`repro_059`) and a run of causally-isolated post-processing probes. The
controller rails audited in 2026-09-06 (atomic writes, `STATE.json` single-source, `state_lock`,
submission gate) are **still holding**. The new risks are less about the code rails and more about
*process discipline, verification that outran its evidence, and scientific direction.*

### Status at a glance (2026-09-21)

| # | Risk | Severity | Status |
|---|------|----------|--------|
| 5 | Budget weekly-reset manual; expected-not-actual booking | MED | **Still open — materialized** (exp_061 reserved 2.0h manually, `actual_hours: null`) |
| 7 | Headline gain may be inside the noise band | MED (sci.) | **Escalated → confirmed**: three straight LB nulls (0.942/0.944/0.947 each == parent) |
| 8 | Admission-review loop pathology (no-GPU harness proving GPU behaviour) | MED/HIGH | **Mitigated this session** (correctness vs verification-depth split; LB is the truth) |
| 9 | Launching outside the controller Codex-PASS gate | MED | **Open — accepted** (exp_060 + exp_061 manual pushes, user-authorized + logged) |
| 10 | Frozen-config derived from wrong resolution layer | MED | **Fixed** (exp_061 v4 #1: effective env-overrides, strengthened `test_N`) |
| 11 | This arc's records/dev-deps uncommitted on a feature branch | LOW/MED | **Open** (single-disk exposure until committed) |
| 12 | Strategic exhaustion of the post-processing lever | MED (sci.) | **Open — decision rule pre-committed** |

### 5 (recheck). Budget booking is still expected-not-actual — **materialized**
The 2026-09-06 fix was deferred. It just bit in a benign way: exp_061 was launched by a manual push
outside the controller, so I booked a **2.0 h reservation by hand** (`GPU_BUDGET.json.reserved_hours`,
`consumed[].actual_hours: null`, remaining 24.493 → 22.493). Until the run completes and is
reconciled to real wall-clock, `remaining_hours` is an estimate, not truth. **Do on completion:**
replace the null with the kernel's actual runtime; let overruns show rather than clamp at zero.

### 7 (recheck). The noise-band worry is now a confirmed pattern — **escalated**
2026-09-06 flagged a sub-0.003 gain as possibly variance. Since then three causally-isolated
post-processing changes each moved **exactly zero** at 3-decimal Public LB: exp_055 edge
(0.942==0.942), exp_057 EMA (0.944==0.944), exp_060 division-threshold (0.947==0.947). The
discipline recommendation held; the empirical finding is stronger than a worry now — see #12.

### 8. Admission-review loop pathology — MED/HIGH → **mitigated**
**What was found.** exp_060 (4 formal REVISE rounds; the standing objection was self-described as
*circular*) and exp_061 (v1→v4 all REVISE) both stalled for the same structural reason: the admission
harness is a **zero-GPU local** artifact, but a diligent reviewer legitimately keeps asking it to
*prove behaviour of the real GPU postprocessing pipeline* — which only the gated GPU run can show. So
each round produces a new "verify X locally" item and the harness grows without ever going green.
This burns wall-clock and attention (not GPU) and can masquerade as diligence indefinitely.
**What was changed / recommended.** This session we separated **genuine correctness/leakage bugs**
(fix before launch — e.g. #10) from **verification-depth items** (downgrade to fail-closed runtime
asserts *inside* the authorized run, or accept), and let the **Public LB be the held-out truth**.
Going forward, scope admission to what is checkable without a GPU (provenance, leakage, graph
semantics, numerical stability, reproducibility, byte-parity of the control, budget); route
"does the real pipeline actually do X" into the run's own gates rather than the pre-launch review.

### 9. Launches now bypass the controller's Codex-PASS gate — MED → **open, accepted**
**What was found.** Both exp_060 and exp_061 were shipped by manual `kaggle kernels push`, outside
the controller `launch` path that enforces a recorded Codex PASS. Each was explicitly user-authorized
and logged (exp_061: `STATE.json.exp061_launch`, this file), so it is legitimate — but the *effective*
launch control is now user discretion, not the programmatic gate. **Risk:** normalization — a later
launch could skip the gate without the same deliberation, or Claude could drift toward self-certifying
(which the contract forbids — Claude must never play the Codex reviewer). **Recommendation:** keep
every bypass (a) explicitly user-authorized and (b) logged with parent/change/hypothesis + open-item
disclosure in `STATE.json`; treat a manual launch as a deliberate exception, never the default.

### 10. Frozen "independent reference" derived from the wrong resolution layer — MED → **fixed**
**What was found.** exp_061's frozen parent config (`EXP061_PARENT_BASE_DEFAULTS`) was transcribed
from the parent notebook's *declaration fallbacks* (`float(os.environ.get('BIOHUB_X','DEFAULT'))`),
but the parent **sets `os.environ['BIOHUB_X']` overrides before those declarations**, so the effective
0.947 config differs on **18 knobs** (safe-div 0.12→0.20, gap 0.10→0.25, gap2 off→on, div-weight
1.0→1.2, the safe-div geometry family, expected-epoch 0→2, …). The runtime `live_config_equals_
frozen_parent` gate would then have fail-closed the real GPU run; worse, `test_N` parsed only the same
fallbacks, so it **false-PASSed** (self-consistent with the wrong table). The admission gate did catch
it before any GPU/LB spend.
**What was changed.** The frozen table is now the parent-**effective** config, derived programmatically
from the notebook's env-setup block (`env override if set else declaration fallback`, then the tight55
ppsweep override); `test_N` was strengthened to parse **both** layers, recompute the effective value,
and assert it actually consulted the env overrides. Both local gates pass; snapshot rebuilt.
**Lesson (general).** Any "independent frozen reference" must reproduce the **same resolution order**
the real pipeline uses, and its guard test must exercise **every layer** or it will agree with its own
mistake.

### 11. This arc's records and dev-deps are uncommitted — LOW/MED → **open**
The exp_055→exp_061 records, the fixes above, and the launch ledger live **uncommitted** on branch
`exp058-v3-doc-reconcile-block2`; test dev-deps (`numpy 2.5.3`, `tzdata`) were installed into `.venv`
and are not pinned in a tracked requirements file. This is the residual of 2026-09-06 #1: provenance
exists on one disk until committed. **Recommendation:** commit the records (artifacts stay ignored per
the existing `.gitignore`) and pin the test deps; publishing to a remote remains a user decision during
the active competition.

### 12. The post-processing lever may be exhausted — MED (scientific) → **open, rule pre-committed**
**What was found.** Three straight LB nulls on the frozen 0.947 pipeline, plus recon finding no
reproducible public checkpoint above 0.947, suggest post-processing tweaks no longer register at
3-decimal LB. exp_061 is honestly priored as *possibly a fourth null* (division is weighted only 0.1
in the aggregate; `zon` may even regress if the DeepCenter checkpoint is not Z-symmetric).
**Recommendation (pre-committed, before seeing the number).** exp_061 arm vs 0.947: **≥0.948 adopt**;
**==0.947** = sub-precision null → do option **B** (larger 0.15/0.12 safe-div move); **≤0.946** revert.
If exp_061 **and** B both null, treat the frozen-pipeline post-processing lever as **closed** and
either step back to a distribution-general lever (model/representation) or accept the 0.947 plateau.
Competition deadline **2026-09-29** (~8 days) bounds how many more probes are worth the wall-clock.

---

## 2026-09-06 review — original whole-project hazard scan (historical evidence)

**Date:** 2026-09-06
**Scope:** Whole-project hazard scan (governance, controller code, state/budget handling, reproducibility), followed by remediation of the agreed items.
**Intent:** Surface plausible latent risks, then record exactly what was changed to address them.

The engineering here is genuinely careful: atomic JSON writes, an explicit state machine, immutable snapshots with SHA-256 manifests, a budget-reservation gate, and a mandatory independent review before launch. The risks below were mostly about *durability, single-source-of-truth discipline, and a few fragile assumptions* — not the core logic being wrong.

---

## Status at a glance

| # | Risk | Severity | Status |
|---|------|----------|--------|
| 1 | Experiment ledger + handoff state unversioned / un-backed-up | HIGH | **Fixed** (records now trackable; artifacts stay out) |
| 2 | Six overlapping "current override" sources of truth | HIGH/MED | **Fixed** (one source: `STATE.json` + generator) |
| 3 | Shared JSON counters have no locking (lost-update race) | MED | **Fixed** (`state_lock` around all shared writes) |
| 4 | Remote-status parsing is substring-based & order-sensitive | MED | **Fixed** (token parser) |
| 5 | Budget weekly-reset manual; expected-not-actual on failure | MED | **Open** (deferred by request) |
| 6 | Daily submission cap enforced only by prose | MED | **Fixed** (`gate_submission` code gate) |
| 6b | (found while fixing #6) `zoneinfo` can't resolve NY on Windows | MED | **Fixed** (loud error + `tzdata` pinned/installed) |
| 7 | Headline improvement may be inside the noise band | MED (sci.) | **Open** (decision discipline; repro_041 gate already correct) |

### Files changed during remediation
- `.gitignore` — rewritten (track records/snapshots, ignore heavy artifacts).
- `.git/info/exclude` — reset to default (it was hiding all code/records/docs from git).
- `experiment_controller/core.py` — added `state_lock`; wrapped the three budget mutators.
- `experiment_controller/metrics.py` — wrapped `results.json` + `CURRENT_BEST.json` writes in `state_lock`.
- `experiment_controller/kaggle.py` — new token-based `parse_remote_status`; new `gate_submission`, `fetch_remote_submissions`, `_resolve_zone`, `_local_date`.
- `scripts/gate_submission.py` — new CLI for the submission gate.
- `scripts/render_checkpoint.py` — new generator for the single-source checkpoint block.
- `STATE.json` — new machine-readable source of current state.
- `CLAUDE.md`, `GOAL.md`, `AGENTS.md` — de-duplicated; auto-checkpoint block + canonical detail in `GOAL.md`.
- `requirements-controller.txt` — pinned `tzdata`.
- `tests/test_controller.py` — added 5 tests (gate dedup/cap/within-cap, tz conversion, lock exclusivity).

All 56 controller tests pass after the changes, including a deterministic daily-cap
test that no longer depends on the UTC time at which the suite happens to run.

---

## 1. Experiment ledger and handoff state were unversioned and un-backed-up — HIGH → **Fixed**

**What was found.** The system-of-record for the whole workflow had no off-site copy:
- `experiments/` (44 experiment records, immutable snapshots, manifests, metrics) was excluded from git via **`.git/info/exclude`** (`/experiments/`) — hidden even from the visible `.gitignore`.
- In fact the exclude file hid **everything of value**: `experiments/`, `experiment_controller/`, `scripts/`, `tests/`, `configs/`, `research/`, and the top-level governance/state files. Only `src/`, `docs/`, and `README.md` were ever tracked. `git ls-files experiments/` returned 0.
- `.private/` (~5.3 MB, including the *authoritative* `.private/current/CONTINUATION.md` and `MEMORY.md`) is excluded via `.gitignore`.
- The reproducibility guarantee (`verify_snapshot`) checks SHA-256 of snapshot files that existed on exactly one local disk. A disk failure or accidental delete would erase the full provenance chain with no recovery.

**What was changed.**
- **Reset `.git/info/exclude`** back to git's default template, so code, configs, experiment records, tests, and governance docs are now visible to git.
- **Rewrote `.gitignore`** to keep the *records and immutable snapshots* under version control while excluding the heavy, re-downloadable outputs:
  - `experiments/**/artifacts/` and `experiments/**/kaggle_kernel*/` are ignored — that is where ~1.29 GB of the 1.3 GB total lives (model checkpoints, `submission.csv`, `.geff/` graph dirs).
  - The authoritative per-experiment `metrics.json` (written to the experiment dir, not under `artifacts/`) stays tracked, so ignoring `artifacts/` loses no evidence.
- **Verified the result:** the newly-trackable set is **592 files / 13 MB**, with zero `artifacts/` paths and no file over 5 MB. Credentials (`.kaggle/`), private workspace (`.private/`), and `.claude/` remain ignored.

**Still your call / not done here.**
- No commit or push was made — publishing is outward-facing. Before pushing, confirm whether the GitHub repo is public (and whether sharing the full solution during an active competition is intended); if it must stay private, keep the repo private or push these to a private remote.
- `.private/current/` (the resume context) is still local-only by design. If you want it backed up too, add a private remote or a scheduled zip; even a nightly copy removes the single-point-of-failure.

---

## 2. Multiple overlapping "current override" sources of truth — HIGH/MED → **Fixed**

**What was found.** The active checkpoint was duplicated, near-verbatim, across six files: `CLAUDE.md`, `GOAL.md`, `AGENTS.md`, `.private/current/CONTINUATION.md`, `.private/current/MEMORY.md`, and the auto-memory `MEMORY.md`. The repro_041 "Current override" block was byte-identical in the first three. Keeping six prose copies in sync is manual; a resumed agent reading a stale copy could re-launch, re-poll, re-collect, or re-submit — each of which burns GPU budget or a scarce daily submission slot. The instructions themselves warned "older material must not override a newer dated checkpoint," a sign the risk was already materializing.

**What was changed.**
- Added **`STATE.json`** as the single machine-readable source of current state (active experiment, phase, next action, leaderboard-submission flag).
- Added **`scripts/render_checkpoint.py`**, which renders one auto-generated block (between `<!-- BEGIN/END AUTO-CHECKPOINT -->` markers) into `CLAUDE.md`, `GOAL.md`, and `AGENTS.md`. The block also reads the live controller `state` from the active `experiments/<id>/experiment.json`, so the prose cannot silently disagree with the actual record. `--check` reports drift without writing.
- **De-duplicated the prose:** the full authorization detail now lives **once** in `GOAL.md` ("Active authorization detail (repro_041) — canonical"). `CLAUDE.md` and `AGENTS.md` keep only the auto-block plus a one-line pointer to `GOAL.md`.
- Going forward: edit `STATE.json`, run `python scripts/render_checkpoint.py`. (Consider wiring `render_checkpoint.py --check` into a pre-commit hook so drift can't be committed.)

---

## 3. Shared JSON counters had no locking — race / lost-update risk — MED → **Fixed**

**What was found.** `write_json` is atomic per write, but the **read-modify-write cycles** on shared state were not guarded: `reserve_budget` / `consume_budget` / `release_budget` on `GPU_BUDGET.json`, the `results.json` rewrite in `evaluate`, and `CURRENT_BEST.json` in `promote_current_best`. The workflow is explicitly multi-agent (Codex, the reviewer, the controller), so two writers interleaving between a read and its write would silently drop an update — a silent correctness failure in exactly the budget/ledger rails that prevent runaway spend.

**What was changed.**
- Added `state_lock()` to `core.py`: a cross-process advisory lock via `os.open(..., O_CREAT|O_EXCL)` on `.controller.lock` (ignored by git), with a bounded acquire `timeout` (30 s) and a separate, larger `stale_after` reclaim threshold (600 s) so a briefly-held lock is waited on, never stolen.
- Wrapped the full read→mutate→write cycle of `reserve_budget`, `release_budget`, `consume_budget` (`core.py`) and the `results.json` + `CURRENT_BEST.json` writes in `evaluate` (`metrics.py`) inside `state_lock`.
- Added `test_state_lock_is_exclusive` to confirm a second acquisition blocks and then raises.

---

## 4. Remote-status parsing was substring-based and order-sensitive — MED → **Fixed**

**What was found.** `parse_remote_status` scanned the combined stdout+stderr for words: it returned `ERROR` if `"error"`/`"failed"`/`"cancelled"` appeared *anywhere*, and checked `ERROR` *before* `COMPLETE`. So a benign line such as `"0 errors"` or `"no error"`, or an error-like token in an otherwise successful log, would classify a finished run as `ERROR` — stranding the run, booking the reservation as consumed, and forcing a rerun.

**What was changed.**
- Rewrote `parse_remote_status` to extract only the single authoritative status token that Kaggle prints (`... has status "KernelWorkerStatus.COMPLETE"` or `"complete"`) via an anchored regex, then map that token exactly. Unrecognized output returns `UNKNOWN` (a non-transition, so it surfaces rather than mishandles).
- Verified the exact former false-positives are gone: `"...0 errors... status COMPLETE"` → `COMPLETE`; `"no error here... complete"` → `COMPLETE`; `CANCELACKNOWLEDGED` → `ERROR`; `garbage` → `UNKNOWN`. The existing `test_remote_status_mapping` cases still pass.

---

## 5. Budget weekly-reset is manual; failure paths book expected-not-actual hours — MED → **Open (deferred)**

**What was found (unchanged, left as-is by request).**
- `GPU_BUDGET.json` has `weekly_budget_hours: 30` but nothing resets `remaining_hours` weekly — it only ever decreases, so "remaining" drifts from reality across week boundaries.
- On failure paths (`collect` output failure, `INVALID_METRIC`, `check_status` → ERROR), the code books the **expected** hours, not actual runtime; and `remaining_hours = max(0.0, ...)` floors at zero, hiding overruns.

**Suggested fix when you pick it up:** record a `week_start` and reset/verify `remaining_hours` against it; log actual runtime even on failure when available; let `remaining_hours` go negative (or warn) instead of clamping so overruns are visible.

---

## 6. Daily leaderboard cap was enforced only by prose — MED → **Fixed**

**What was found.** The "≤3 submissions per America/New_York day, query remote history first, no duplicate probes" rule lived entirely in `AGENTS.md`, and `SUBMISSION_BUDGET.json` was appended by hand. Unlike GPU budget (a code gate in `reserve_budget`), the submission cap had **no** programmatic backstop — it relied on agent discipline at the exact moment an agent might act on a stale checkpoint.

**What was changed.**
- Added `gate_submission()` and `fetch_remote_submissions()` to `kaggle.py`, plus CLI wrapper **`scripts/gate_submission.py`**. The gate:
  1. **Requires** a successful remote-history query first — a failed query raises rather than allowing a blind submission (the "query before submit" policy is now enforced, not asserted).
  2. Counts today's non-error submissions in the configured timezone (remote and local) and blocks at the cap.
  3. Rejects a candidate whose SHA-256 duplicates an already-recorded submission.
  Returns a verdict dict on success; `user_override=True` exists for explicit, justified exceptions.
- Added `test_gate_submission_blocks_duplicate_sha`, `..._blocks_when_daily_cap_reached`, `..._allows_within_cap`.

### 6b. Latent timezone bug found while fixing #6 — MED → **Fixed**
- **Found:** on this Windows Python, `zoneinfo.ZoneInfo("America/New_York")` raises `ZoneInfoNotFoundError` (no system tz database, `tzdata` not installed). The first draft silently fell back to UTC, which would shift the daily-cap midnight boundary by the local offset and could wrongly allow a 4th submission (or block a valid one) near midnight.
- **Changed:** `_resolve_zone()` now raises a clear, actionable `ControllerError` instead of silently using UTC; `tzdata` was installed into `.venv` and pinned in `requirements-controller.txt`. Verified `2026-09-02 03:17 UTC → 2026-09-01` in New York, and added `test_local_date_uses_configured_zone`.

---

## 7. The headline improvement may be inside the noise band — MED (scientific) → **Open (discipline, not code)**

**What was found (unchanged).** `exp_040` is recorded KEEP at **+0.00276**, but the project's own notes say `reproducible: false`, per-video adjusted-edge deltas are heterogeneous (8 positive, 1 zero, 7 negative; worst −0.0037), and the train16 score is an acknowledged optimistic proxy. A sub-0.003 aggregate gain with roughly balanced per-video wins/losses is the shape of run-to-run variance, not a robust effect.

**Recommendation (already in motion).** The exact independent reproduction `repro_041` — gated on byte-identical submission and 1e-12 metric tolerance — is the correct control. The residual risk is over-reading a "close but not identical" result. Decide the noise band **before** seeing the number, and treat a non-reproducing delta of this size as null. No code change is appropriate here.

---

## Lower-severity notes (unchanged, informational)

- **Credentials look clean.** `.kaggle/` and `.private/` are ignored, no API keys appear in any tracked file, and `enable_internet` defaults to `False`. Never `git add -f` the `.kaggle` dir.
- **Review gate is a text match.** `review.py` accepts launch on `VERDICT: PASS`; a garbled review yields `MISSING` → blocks (fail-safe). Its strength is inherent to the design, not a bug.
- **Environment reproducibility across time.** `docker_image` pinning is optional per experiment; pin it for anything you intend to reproduce exactly.
- **Pre-existing test-environment issue (not code):** the default `pytest` run errors with a Windows permission error on `%TEMP%\pytest-of-Ling`. Runs cleanly with `--basetemp` pointed elsewhere; consider a fixed `basetemp` or `tmp_path_retention_policy` in pytest config.
