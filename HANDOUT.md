# Session Handout — updated 2026-09-25T00:55Z

Purpose: hand the current state to the next session AND to the user. Read this FIRST, then
`STATE.json`, then the active `experiments/exp_064_x138_verbatim_repro/` record.

If anything here disagrees with `STATE.json`, **`STATE.json` wins.**

**Competition closes 2026-09-29 23:59.**

---

## >>> NEXT SESSION: START HERE <<<

**Nothing is running. No GPU is committed. Two LB submissions are PENDING. DO NOT POLL.**

| submission | arm | status |
|---|---|---|
| **56535761** | exp_064 — x138 byte-verbatim reproduction | **PENDING** |
| **56530197** | exp_062 k2 — mutual-best β=0.20 on our 0.947 parent | **PENDING** |

```bash
kaggle competitions submissions -c biohub-cell-tracking-during-development -v
```

**exp_064 decision rule.** ≥0.953 → adopt x138 as the new parent (that is the rank-200 cutoff) ·
0.948–0.952 → a real gain over 0.947, adopt · ~0.947 → the reproduction carries no advantage over
our own parent · <0.947 → reject. If it comes back **~0.939**, the likely explanation is in the log:
the base configuration that actually ran is labelled "public 0.939 configuration" by the author
themselves (see the selector finding below).

**exp_062 k2 decision rule** (unchanged): ≥0.948 adopt · ==0.947 close the probe · ≤0.946 revert.

**The one authorized zero-GPU work item while waiting:** LB mining. From the 3888-row download, find
authenticated teams at ≥0.956 who have published notebooks, then **read each notebook's mechanism**.
A team's score does **not** authenticate any particular public notebook — that is the DivNet lesson,
and it is the single most expensive mistake this project nearly made.

---

## exp_064 result — integrity PASS, quality UNKNOWN

| | |
|---|---|
| kernel | `lingxd/biohub-exp064-x138-repro` v1, **COMPLETE** |
| runtime | **932.2 s = 0.258944 GPU h** (reserved 2.5 h) |
| collected | once, `2026-09-25T00:40Z` |
| adapter | `scripts/collect_exp064_x138.py` → **exit 0**, 25/25 checks, `failures: []` |
| output | sha `d52a5da2`, 238,260 rows, 4/4 test videos |
| differs from | parent `d3453380` ✓ and exp_062 k2 `ba9431c1` ✓ |
| V1284 head | patched ✓, active ✓, no runtime error ✓ |
| graph | 0 dangling, 0 backward/self-loop, 0 non-adjacent edges |
| evidence | `experiments/exp_064_x138_verbatim_repro/collection/` |

`primary_metric: 1.0` means **deployment integrity only**. It carries **no** quality inference. The
author's rank-62 0.956 is their score on their pipeline and is **not inherited**.

**A recorded waiver.** The pre-registered gate also required that k2's score be resolved first,
because the comparator is `max(0.947, k2)`. k2 was still PENDING. That is an *interpretation* gate,
not a safety gate, and the 5/day ruling removed the scarcity reason for waiting; the user authorized
the submission explicitly. Logged as a waiver in `SUBMISSION_BUDGET.json`, not as a pass.

---

## Three corrections recorded today. All three were ours, and all three were made before measuring.

### 1. x138's runtime self-tuning is INERT — measured from our own log

```
VALIDATOR: disabled (BIOHUB_VALIDATOR_ENABLE=0).
SWEEP: validator unavailable -- keeping the base configuration.
Keeping the base submission.csv (public 0.939 configuration).
```
`ppsweep_selected.json`: `selected: "base"`, `overrides: {}`, `held_out_stems: []`, `base_proxy: null`.

**The notebook disables its own validator.** Consequences, both directions:

- ✗ **There is no free telemetry.** The plan to read `ppsweep_results.csv` / `validator_stats.csv`
  and pick the next knob from them yields **nothing** — those files were never written.
- ✓ **x138 as run is a deterministic single-policy pipeline.** No runtime re-selection of
  post-process configuration. This **removes the reviewer's main objection** to single-knob variants
  on x138: a one-variable change is now a genuinely clean one-variable experiment.
- → **It creates a new arm:** `BIOHUB_VALIDATOR_ENABLE=1` switches on the self-tuning the author
  disabled. One line, real hypothesis, costs the held-out validator inference.

Verified in the notebook but **moot while the validator is off** — and live again the moment it is
turned on: cell 0:63 overrides the sweep margin to **0.001**; cell 10:33–49 also scores a
**combination** of individually-positive candidates at +0.0005; cell 10:99–108 **rewrites
`submission.csv`** with the selected configuration.

### 2. The density argument is withdrawn as directional evidence

What still stands: the four hidden-test movies run at **62.2 / 195.2 / 257.3 / 697.5** nodes per
frame (exp_064's own figures), an ~11× span, while our `tight55` was selected as a **single global
value** over 8 mixed-density train movies. That makes the global constant **questionable**.

What is withdrawn:
- It does **not** establish the constant is *mistuned*. Predicted nodes/frame is not an optimal
  relink radius.
- It supports **no direction** — not 5.5 → 6.5, not anything.
- "Density is a mechanism class x138 never touches" is **false**: x138 ships
  `BIOHUB_GAP_DENSITY_ADAPTIVE=1` and uses a separate **7.0 µm flow gate whenever a flow field
  exists**, with 5.5 only on the non-flow path. Any `tight_um` arm must first show the non-flow path
  carries consequential decisions.
- "Not in the `_EXPECTED_NUMERIC` drift guard" means only that the guard will not reject it. It is
  **not** evidence the knob is effective.

### 3. GPU is no longer a binding constraint

exp_064 drew **0.259 h** where our own comparable runs cost 1.73–2.0 h. The most plausible cause —
stated as a hypothesis, not a measurement — is exactly correction #1: our parent runs a held-out
validator and post-process sweep over 8 train movies; x138 skips both.

---

## Budget — user ruling 2026-09-24 (late stage)

> Treat GPU as 20 h with **all limits released**; raise the daily LB cap to 5.

| | |
|---|---|
| GPU remaining | **19.741056 h** (20 h − exp_064's confirmed 0.258944 h) |
| protected reserve | **none** (was 6 h) |
| per-experiment ceiling | **none** (was 4 h) |
| LB cap | **5 per America/New_York day** (was a stricter project rule of 3) |
| used today (NY 09-24) | **2 of 5** |

At ~0.26 h per x138-class run, 19.74 h buys **dozens** of runs, and ~120 h of calendar fits them
serially. **The binding constraints are now evidence quality and Public-LB overfitting risk.**

⚠ ~25 remaining submission slots **can** overfit the Public LB, and more slots do not improve the
signal's statistical quality. Freeze small batches before reading their scores, record every result,
require local corroboration for small gains, always preserve a robust baseline, and do not treat
unused slots as wasted.

---

## Where we stand

Full authenticated LB download, 3888 teams, `2026-09-24T20:03:35`:

| rank | 1 | 10 | 50 | 100 | 200 | 300 |
|---|---|---|---|---|---|---|
| score | 0.975 | 0.967 | 0.957 | 0.954 | **0.953** | 0.950 |

Our 0.947 is **rank ~478 of 3888**. The rank-200 cutoff moved 0.949 → 0.953 in one day. The gap is
**0.006**. Record: `docs/research/leaderboard_recon_2026-09-24.md`.

---

## Next steps, ranked

1. **Zero GPU, authorized now:** LB mining (above).
2. **Resolve the two pending scores.** They decide the parent. Everything downstream waits on them.
3. **Single-knob arms on x138 — each must earn its slot** with an active-path check, a named failure
   mechanism, and a predicted measurable effect. No pre-allocated run budget. Candidates:
   `BIOHUB_VALIDATOR_ENABLE=1`, `MOTION_RELINK_FLOW_TIGHT_UM` (the gate actually active when flow
   exists).
4. **Port exp_062 mutual-best onto x138** only if k2 ≥ 0.948, and only after a semantic overlap
   check — x138 already ships `BIDIRECTIONAL_FUSION_MODE=harmonic_probability` with reverse-time
   edge weight 0.15, so additivity must **not** be assumed. k2's evidence belongs to *its own*
   parent.
5. **A measurement run** — spending GPU to learn rather than to score — is now affordable and was
   not before.

## Governance notes from this arc

Two Codex challenge rounds, 2026-09-24:

- **Round 1 (repo-audited).** Four notebook claims, all independently re-verified by me, all
  correct. Produced corrections #1 and #2 above.
- **Round 2 (NOT repo-audited — Codex's file access failed; it reasoned from supplied evidence).**
  Corrected my throughput arithmetic: 8 runs × 2.5 h = 20 execution hours against ~120 calendar
  hours, so serial execution was never the ceiling and concurrency was never the key unknown.
  Rejected my proposal to tier admission by authored line count — correctly noting I was arguing for
  less scrutiny of my own work immediately after five rounds found defects in exactly that work. The
  right reading of five rounds is that the admission **materials** were defective, not that the
  review was excessive; reduce rework with reusable regression fixtures, not by lowering the bar.

**Recurring lesson, now four times: never read a declaration as behaviour.** Correction #1 is the
purest instance yet — every pre-run plan assumed the sweep would run because the code for it is
right there in the notebook. One environment variable made all of it dead code.

## Standing rules

- **Never auto-submit to the LB without the user asking.** Record every submission in
  `SUBMISSION_BUDGET.json` with an authenticated `score_source`.
- Competition is **notebook-only**: any arm's LB submission needs a kernel whose own output *is*
  that arm. **Never build another bespoke deployment adapter** — exp_061 burned 5 submissions and
  3.094 GPU h across three transport mechanisms and never got a score.
- Codex reviews: `gpt-6-astra`, effort `low`, read-only, model passed on the command line.
- **Verify a reviewer's factual claims against the repo before accepting them** — in this arc
  essentially every Codex finding was correct, and I verified each one anyway.
- Claude must **never** play the Codex reviewer role.
- English only for code, notebooks, configs and technical docs. Never `git add -f` `.kaggle/` or
  `.private/`.
- Regenerate the checkpoint block with `python scripts/render_checkpoint.py` after editing
  `STATE.json`; never hand-edit that block.

## Key pointers

- **exp_064:** `experiments/exp_064_x138_verbatim_repro/` — `experiment.json`, `review.md` (the
  5-round PASS), `collection/` (metrics, ppsweep record, log excerpt), `kaggle_kernel/`.
- **Collection adapter:** `scripts/collect_exp064_x138.py` — the submission gate.
- **Archived third-party notebooks (with hashes):** `docs/research/public_notebook_archive/`.
- **Recon:** `docs/research/leaderboard_recon_2026-09-24.md` (current) supersedes the standings in
  `public_frontier_recon_2026-09-23.md` (stale).
- **Density measurement:** `docs/research/test_density_measurement_2026-09-24.md` — read it together
  with correction #2 above, which downgrades its conclusion.
- **Abandoned:** `experiments/exp_063_public_0951_pipeline_repro/` — wrong target.
- **exp_062 (closed pending its score):** `experiments/exp_062_mutual_best_edge_association/`.
- **Parent:** `experiments/repro_059_public_0947_exact_copy/` — Public LB 0.947, submission 56313491.
