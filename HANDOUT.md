# Session Handout — updated 2026-09-24 (exp_062 k2 CANDIDATE running; k1 control PASSED)

Purpose: hand the current state to the next session AND to the user. Read this FIRST, then the
deeper authority in order: `STATE.json`, the active
`experiments/exp_062_mutual_best_edge_association/` record,
`docs/research/exp062_mutual_best_edge_association_proposal_v3.md`,
`docs/research/PROJECT_HANDOFF.md`.

If anything here disagrees with `STATE.json`, **`STATE.json` wins** (this file is a human-readable
summary; `STATE.json` is the machine source of truth).

---

## >>> NEXT SESSION: START HERE <<<

**One thing is in flight. DO NOT POLL — the user reports completion.**

### exp_062 k2 (CANDIDATE) is RUNNING

| | |
|---|---|
| kernel | `lingxd/biohub-exp062-mutual-best` **version 2** |
| variant | **CANDIDATE** — `BIOHUB_LB_SCORING_MODE=mutual_best`, β 0.20, `EXPECT_PARENT_SHA` popped + asserted unset |
| launched | 2026-09-24T14:37:15Z via `scripts/launch_kaggle.py` (the controller) |
| reserved | **1.75 GPU h** (k1 measured 1.727 h, so the original ~1.3 h/version estimate was low) |
| staged nb | `1a135feb…` — byte-identical to the admission-PASSED candidate snapshot |
| staged dir | `kaggle_kernel_retry_001` — the name says "retry", but this is the k2 push, not a retry |

When the user says it finished, **collect once**, and verify everything k1 verified **plus**
`frames_with_bonus > 0`, then diff `submission.csv` against the control's `d3453380`.

### The submission rule

| k2 output | action |
|---|---|
| **byte-identical to the control** | **Do NOT submit.** Zero information, wasted slot. Close the probe. |
| **differs** | **ONE** LB submission, **separately authorized by the user**, remote cap checked first |

Decision rule vs `repro_059` 0.947:

| k2 Public LB | action |
|---|---|
| **≥ 0.948** | adopt as the new parent; any further β probe needs its own justification |
| **== 0.947** | **CLOSE the probe.** Equality cannot distinguish cancellation, unannotated changes or rounding, so it does **not** license a bigger β |
| **≤ 0.946** | revert, keep repro_059 0.947 |

Designated successor either way: **density-adaptive relinking** — needs its own proposal, challenge
and authorization.

---

## k1 (CONTROL) — DONE, PASSED, collected once. Do not re-run or re-collect.

Collected 2026-09-24. Kernel version 1, COMPLETE in 6218.95 s (**1.727487 GPU h** measured).

- **`submission.csv` independently hashes to `d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60`** —
  verified with `sha256sum` over the downloaded file (241 357 lines), *not* the notebook's
  self-report. Byte-identical to parent `repro_059` (submission 56313491, Public LB 0.947).
  **The insertion is inert → the arc proceeds.**
- All nine integrity checks true; `anchor_match_count` 1; activation softmax; `no_cache_hit` true on
  **measured** wall-clock (543.08 s inference vs the 60 s floor), so the parent's restored
  `predict_seconds` was never trusted; `frames_with_bonus` 0 as required for `mode=none`.
- `pre_raw_* == raw_*` **exactly** on all four shard records — the bonus block ran and provably
  changed nothing at β = 0.
- Test-stage telemetry present with both expected shards (`0/2`, `1/2`, 198 frames each) and
  **distinct** from the two validation records: the admission round-3 telemetry-substitution gap is
  now closed on a real run, not just in review.
- **Never submitted to the LB, and never will be** — its output *is* the already-scored 0.947 file,
  so it carries zero information and would burn one of three daily slots.

**Budget:** remaining **18.671187 h** after booking k1. The k1 row is filed under the ledger key
`exp_062_mutual_best_edge_association#k1_control`, deliberately: the controller's `consume_budget()`
allows only **one** consumed row per `experiment_id`, so a bare `exp_062` key would have blocked the
k2 booking. Book k2 under a matching `#k2_candidate` key.

⚠ **Controller/experiment shape mismatch worth knowing:** the controller models one `experiment_id`
as one run, but exp_062 deliberately has two kernel versions. Launching k2 therefore required
flipping `snapshot_source` from the control to the candidate and returning `state` to `READY`
by hand (`K1_CONTROL_COLLECTED` is a bookkeeping marker, not a state in the `TRANSITIONS` table).
Both are recorded in `state_history`. Review PASS and smoke PASS already stood against the
**candidate** notebook — the recorded smoke command targets `exp062_mutual_best_candidate.ipynb`.

**Pre-k2-launch local gates, all re-run green:** `validate_exp062_notebook.py` ALL PASS (5 groups),
`test_exp062_behavioral.py` ALL PASS, `validate_notebook.py --require-metrics-contract` PASS. The
control/candidate diff is confined to **cell 3's env block** (run id, mode, β, guard pop + assert);
cells 0, 1, 2 and 4 are byte-identical.

---
## What exp_062 is

A mutual-best / relative-rank prior added to the edge logits of the frozen 0.947 pipeline,
**upstream of the ILP solve** — the first intervention in this arc placed there. Net bonus:

| pair status | bonus |
|---|---:|
| mutual | `2.0 β` |
| column-best only (best **source** for its target) | `0.8 β` |
| row-best only (best **target** for its source) | `0.3 β` |
| neither | `−0.2 β` |

`raw` is `(n_src, n_tgt)`: **dim 0 reduces sources, dim 1 reduces targets**
(`predict_unet_transformer.py:452`). The parent's own activation is `softmax(raw, dim=0)`, i.e. it
already normalises over sources — the **target** axis is the one it does not.

**Honest prior, carried from the strategy record:** the prior *reinforces* the parent's existing
fused ranking rather than adding independent evidence, and its largest term (`col_best`) largely
re-expresses a signal the `low_margin_consensus` blend already computes at parent lines 1199–1220.
Codex's phrase: a **rank-sharpening heuristic**, not a ratio test. A null is genuinely likely. β =
0.20 is a *published starting point* from an author absent from the LB top 200 — not a known gain.

Full record: `docs/research/exp062_mutual_best_edge_association_proposal_v3.md` (v3, CONSENSUS).

---

## Governance: exp_062 cleared every gate properly

Unlike exp_060/exp_061, this one went **through the controller**, not around it.

| gate | status |
|---|---|
| strategy CONSENSUS | ✅ Codex PASS after 3 rounds (`exp062_codex_challenge_v1..v3.md`) |
| build + local gates | ✅ parity guard, validator 5 groups, behavioral 13 tests |
| **Codex ADMISSION PASS** | ✅ 2026-09-24, after 3 substantive REVISE rounds (`experiments/exp_062_.../review.md`) |
| snapshot smoke | ✅ `scripts/run_smoke_test.py`, exit 0 |
| budget reservation | ✅ via the controller (3.0 h at k1; revised to 1.75 h for k2 after k1 measured 1.727 h) |
| k1 launch | ✅ COMPLETE — control PASSED, reproduces `d3453380` |
| k2 launch | ✅ RUNNING — version 2, launched 2026-09-24T14:37:15Z |
| LB submission | ⬜ needs separate user authorization, and none at all if k2 == control |

**No waivers were used.** That is the first time in this arc.

Two admission attempts returned `BLOCK` for **tool-access reasons only** —
`helper_unknown_error: setup refresh had errors` — and Codex itself labelled both *"an
evidence-access block, not rejection of the hypothesis"*. **Those are not findings; just retry.**

### Three things the admission caught that are worth remembering

1. **Resume-signature collision (round 2 of the strategy review).**
   `_inference_resume_env_keys` (parent cell 2 line **1669**) is a fixed 13-key list containing
   neither exp_062 variable, and `_test_prediction_signature` (line **1670**) hashes exactly those
   keys. The candidate could therefore compute the **same** signature as the control, skip inference
   at 1672–1680 and replay the control's predictions with every gate green. Closed by extending the
   key list **between 1669 and 1670**. ⚠ Parent line **1675 restores the historical
   `predict_seconds`** on a cache hit, so the cache alarm must use **measured** wall-clock.
2. **Validation telemetry could substitute for test telemetry (admission round 3) — DEMONSTRATED.**
   The parent runs the patched predict script **twice** (test inference, then validation) and both
   append to one telemetry file. Codex executed the frozen code and showed a lone `val_single`
   record, with **no test telemetry at all**, producing a green gate. Closed by end-to-end stage
   separation (`BIOHUB_EXP062_STAGE`), `require_stage="test"`, and expected-shard coverage.
3. **The controller smoke gate was corrected, not waived.** Codex refused "it's inherited, so
   document it": *"documenting it does not satisfy the smoke gate."* `experiment_controller/core.py`
   now honours assignment-before-guard **within the same cell**. That unblocked the gate for the
   **whole lineage** — repro_059, exp_060, exp_061 and both exp_062 variants now pass, where all
   four previously failed — while guard-before-assignment and never-assigned notebooks are still
   rejected. Duplicating the frozen config into an earlier cell was rejected as the remedy: it would
   create a second source of truth, the defect class behind the exp_061 v4 BLOCK.

**One post-admission change, disclosed:** the `kaggle` launch block was added to the config after
the PASS (slug, datasets, T4, docker image pinned to the one exp_060 ran on,
`inject_experiment_id: false`). Verified by hash that **both notebooks, the module and all tests are
byte-identical** to the admission-PASSED snapshot. Only `config.yaml` changed.

---

## How we got here (compressed)

- **The parent:** `repro_059` = verbatim copy of a public **0.947** notebook on the same Pilkwang
  checkpoints as our 0.944 → the +0.003 is 100% post-processing/TTA, and is **not causally
  isolated**. Two recons (09-18, 09-23) found no verified public notebook above 0.947.
- **Where 0.947 stands (09-23):** **outside the top 200** — rank-200 cutoff 0.949, LB top 0.975,
  with an unexplained 0.955–0.966 band. Deadline **2026-09-29 23:59**.
- **Four LB probes, zero movement:** exp_055 (0.942), exp_057 (0.944), exp_060 (0.947), and exp_061
  which was **never scored**. ⚠ **exp_055 was an EDGE intervention**, not a division one — its whole
  proxy gain was adjusted-edge with `division_jaccard` unchanged at 0.2. **Never claim the edge side
  is untried.** The real common factor is that all four acted *downstream of the ILP solve*.
- **exp_061 abandoned (09-23):** five consecutive LB submissions across three transport mechanisms
  returned no score. v5 confirmed both scale fixes active with byte-identical predictions, so
  neither the watchdog nor the 20 GB cap was the cause; a third rerun property is, and the hidden
  tracebacks are never exposed. **zon is UNRESOLVED, not falsified.** Cost: 5 submissions, 0 scores,
  3.094 GPU h.
- **Transport lesson:** use a **single-config variant notebook** whose own `submission.csv` *is* the
  candidate. exp_060's lb-submit kernel (56361673, COMPLETE at 0.947) is the closest successful
  minimal-change precedent — *not* the only one: repro_059, exp_057 and exp_055 also scored via code
  submission. **Never build another bespoke deployment adapter.**
- **The other two public levers** (`docs/research/public_frontier_recon_2026-09-23.md`):
  density-adaptive relinking (verified specimen-blind) and the DivNet mitosis gate.

---

## Open items / guardrails

- **Submission cap: THREE per America/New_York calendar day** — the project rule in `AGENTS.md:86`,
  which is **stricter than and therefore overrides** the platform's authenticated
  `max_daily_submissions` of 5. A 2026-09-23 edit wrongly replaced the rule with the platform fact;
  corrected. Record every submission in `SUBMISSION_BUDGET.json`; **never auto-submit without the
  user asking**; check remote history first.
- **Budget:** remaining **20.399 h**, of which **3.0 h is reserved for exp_062** and six are
  protected. Reconcile actual hours at collection.
- **ARMED option B** (`STATE.json.pending_followup`): larger 0.15/0.12 safe-div move. Division-side,
  so it ranks **below** density-adaptive — but Codex explicitly **refused to dismiss division
  categorically**, and the A0 audit gives division the *largest* optimistic headroom (+0.085 perfect
  vs +0.045 all-edge-FN). Not withdrawn.
- **No pre-LB quality estimate exists for exp_062.** Dropping the proxy gate was a *resource*
  decision. Note exp_055 is the one genuine transfer failure (+0.0148537 proxy → 0.000 LB);
  **exp_057 skipped proxy scoring entirely** and is not transfer evidence.
- **The numpy shim establishes logic, not PyTorch numerical parity** — axis semantics, truth table,
  inertness, fail-closed. Torch is not installed locally. Recorded, non-blocking.
- **The inherited validator is not specimen-disjoint** (it picks division-prioritised training
  videos within both 44b6 and 6bba). Never present its scores as independent generalization
  evidence.
- Every inference policy stays ground-truth-free and specimen/video-blind. Never `git add -f`
  `.kaggle/` or `.private/`.
- **Dev deps:** numpy 2.5.3 + tzdata in `.venv`, unpinned, test-only.

---

## Key files / pointers

- **Active:** `experiments/exp_062_mutual_best_edge_association/` — `experiment.json` (carries
  `launch_k1_control`, `launch_plan`, `admission_round_1..3`), `review.md` (the admission PASS),
  `snapshot/` (manifest + both notebooks + config + the four scripts), `kaggle_kernel/` (what was
  actually pushed).
- **Implementation:** `scripts/exp062_mutual_best.py` (runtime),
  `scripts/build_exp062_mutual_best.py` (builder + parity guard, `--variant control|candidate`),
  `scripts/validate_exp062_notebook.py` (5 groups; **group 4 replays the parent's own patch chain**
  and proves the anchor is unique in the really-patched source),
  `scripts/test_exp062_behavioral.py` (13 tests against a numpy torch shim running the real block).
- **Strategy:** `docs/research/exp062_mutual_best_edge_association_proposal_v3.md` (v3, CONSENSUS) +
  `exp062_codex_challenge_v1..v3.md`. v1/v2 are superseded and list their own known-wrong claims.
- **Recon:** `docs/research/public_frontier_recon_2026-09-23.md`.
- **Parent:** `experiments/repro_059_public_0947_exact_copy/` — `PROVENANCE.md`,
  `artifacts/ppsweep_selected.json` (`MOTION_RELINK_TIGHT_UM: 5.5`).
- **Abandoned arc:** `experiments/exp_061_zon_lb_submission_repair_v5/` (`collect-audit.json`,
  `leaderboard-submission.json`) and `.../v4/`.
- **Canonical state:** `STATE.json` — `exp062_strategy` holds the whole chain. Regenerate the
  `CLAUDE.md`/`GOAL.md`/`AGENTS.md` checkpoint with `python scripts/render_checkpoint.py` after
  editing it (never hand-edit that block).
- **Risk register:** `PROJECT_RISK_REVIEW.md`.
- **Kaggle:** `kaggle kernels status|output lingxd/biohub-exp062-mutual-best`;
  `kaggle competitions submissions -c biohub-cell-tracking-during-development` for authenticated
  history.
- **Codex reviews:** model `gpt-6-astra`, effort `low`, read-only. The controller path is
  `scripts/request_codex_review.py`; it reads `~/.codex/config.toml`, so pin the model by swapping
  that file temporarily and **always restore it in a `finally`**.
