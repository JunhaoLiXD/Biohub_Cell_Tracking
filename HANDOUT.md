# Session Handout — updated 2026-09-25T13:10Z

<!-- BEGIN EP068 CURRENT -->
## Current ep068 continuation - 2026-09-27T02:26:01.458634+00:00

Experiment `exp_068_ep015_single_probe`: **SUBMITTED**. Fresh review: **PASS**.
The user authorized one ep015 run and one audited LB submission; 30 GPU hours were
reported at the new epoch. Ledger now 30.000000 h, reservations
`{"exp_068_ep015_single_probe": 2.0}`. No final re-selection, second probe or public push.

Wait for user completion notice; do not poll, rebuild or relaunch. Then check/collect once, run scripts/audit_exp068_collection_v2.py (verify admission_supplement_manifest.json), bind remote version/source, check remote history and conservative three/day cap, and perform the one already authorized LB submission if all gates pass.

CPU counterfactual is complete: all 128 subsets audited; original full per-movie
metrics reproduced. True-edge repair can change TP/FP/FN from 3/2/9 to 9/2/3 in this
restricted family. This is GT-assisted TRAIN diagnosis, not a learned result or LB
forecast. Report: `docs/research/ep015_continuation_2026-09-26/division_counterfactual_report.md`.
Older ep015-OFF and exp067-current instructions below are historical. exp067 training
remains stopped. Final retained submission remains 56535761 (recorded Public LB 0.953).
<!-- END EP068 CURRENT -->
## Current closeout - 2026-09-26 (supersedes historical directives below)

Local closeout is complete. Read `PLAN.md` v4 and
`docs/research/closeout_review_2026-09-26.md`; `STATE.json` owns current status.
exp067d is EVALUATED, export complete; exp067 is stopped for this competition.
Retain exp064 submission 56535761, recorded Public LB 0.953. No training, GPU launch,
submission, successor preparation or public push is authorized. ep015 remains OFF.
Ledger remaining is 16.752765 h with no reservations. Next: verify the final selection
on the site before close; this closeout did not verify live selection or remote quota.
The corrected CPU audit reproduces scorer TP/FP/FN 3/2/9 and separates those semantics
from two exact direct-edge events. Geometry-only controls give 4/7 for tau-off alone
and 7/7 with distance14 plus tau-off; they do not establish decoded performance.
Historical RUNNING, next-launch and broad causal claims below are superseded.
Review waivers remain historical NO_PASS, never retroactively converted to PASS.


Purpose: hand the current state to the next session AND to the user. Read this FIRST, then
`STATE.json`, then `docs/research/lb_recon_2026-09-25_amanatar_sweep.md`.

If anything here disagrees with `STATE.json`, **`STATE.json` wins.**

**Competition closes 2026-09-29 23:59.**

---

## >>> NEXT SESSION: START HERE <<<

**Nothing is running. No GPU is committed. Both submissions are RESOLVED. Nothing is authorized.**

> **The agreed next steps live in `PLAN.md` at the repo root.** Start there: Step 0 is free and
> decides whether the division route is the biggest prize left or is closed.

| submission | arm | Public LB | rule | verdict |
|---|---|---|---|---|
| **56535761** | exp_064 — x138 byte-verbatim | **0.953** | `>=0.953` → adopt | **ADOPT as parent** |
| **56530197** | exp_062 k2 — mutual-best β=0.20 | **0.944** | `<=0.946` → revert | **REVERT, arc closed** |

**Our parent is now x138 at 0.953**, replacing `repro_059` 0.947. `exp_062`'s edge prior is a
measured loss of 0.003 — do not raise β, do not retry a variant.

**`exp_065` proposal v2 is WRITTEN and awaiting the SECOND Codex challenge:**
`docs/research/exp065_metric_aligned_pruning_proposal_v2.md`. v1 was challenged and returned
**REVISE** with **7 blocking `[CORRECTNESS]` findings** (`exp065_codex_challenge_v1.md`); all seven
were independently re-derived from the notebook sources and **all seven were genuine**. v2 addresses
all seven and carries all five non-blocking findings into the design. `exp065_metric_aligned_pruning_proposal.md`
(v1) is banner-marked SUPERSEDED — **do not act on it.**

The next step is **Codex's challenge of v2**, then revision if needed, then explicit CONSENSUS.
Claude Code must never review its own proposal.

⚠ **Two of v1's errors had already reached these records and are now corrected here and in
`STATE.json`:** `MOTION_RELINK_TIGHT_UM` is **not** shown inert (both notebooks already set 5.5 and
the candidate sets 5.5 — the sweep never varied it), and the count multiplier **rewards**
under-prediction rather than merely not penalising it.

⚠ **`ep015` now fails three independent ways**, not one: 60.6 % of its gain sits in one held-out movie;
it regresses **−0.0084939** on the 44b6 prefix against the author's own −0.001 limit; and **10 of the
36 test-shaped subsets are negative**. Under the real two-per-prefix test shape, 28 % of draws lose.
**On current evidence nothing qualifies for a submission**, and the deliverable is a 29-candidate
measurement rather than a bet.

---

## The board: 0.953 is a 249-team plateau

Snapshot `2026-09-25T12:50`, 3899 teams. **Ours: rank 361, score 0.953, 30 submissions.**

| rank | 1 | 50 | 100 | 150 | **200–420** | 450 | 500 |
|---|---|---|---|---|---|---|---|
| score | 0.975 | 0.959 | 0.955 | 0.954 | **0.953** | 0.951 | 0.949 |

This is the most actionable fact on the board. **One thousandth of a point is worth ~190 ranks.**

| target | teams at or above | our rank would be |
|---|---|---|
| 0.954 | 171 | ~171 |
| 0.955 | 121 | ~121 |
| 0.956 | 91 | ~91 |

⚠ The board still moves fast — our rank went ~478 → ~533 in six hours on 09-24/25 before this
score landed. Any plan quoting a rank more than a few hours old is quoting a stale number.

---

## No public notebook scores above the plateau

Every notebook author in the competition was mapped to their authenticated team score. The public
ladder tops out at the x138 / `frontier947-readmit` configuration, and we have now **measured** that
configuration at 0.953. The authors sitting above it with published work — `andrey4522` 0.956/206
subs, `anvithpothula` 0.956/123, `y3uanm` 0.956/62, `thtennant` 0.959/40 — all got there through
dozens-to-hundreds of submissions of work they did **not** publish.

**Independent corroboration of our own 0.953:** `amanatar/optimized-biohub-max-score` cell 0 declares
`BIOHUB_SCORE_AXIS = 'x138 base (LB 0.953) + ...'`. A third party measured the same value for the
same notebook. So anvithpothula's rank-67 0.956 is **not** their published notebook's score — and by
the same reasoning neither is thtennant's 0.959. **This is what downgrades the `readmit-v1` A/B:**
its whole premise was 0.959-without-the-head versus 0.956-with-it, and neither number belongs to a
published notebook. It now tests a mechanism with no quantified expected effect.

There is no shortcut left on the public side. Copying is exhausted at 0.953; anything further has to
be measured.

---

## The harvest: a real held-out sweep table, for free

`lb_mining_2026-09-25.md` correction #1 concluded that x138's sweep telemetry was unobtainable
because the notebook ships `BIOHUB_VALIDATOR_ENABLE=0`. That was right about x138 and **wrong as a
general claim.** `amanatar/optimized-biohub-max-score` is a **near-superset of x138** (x138's 89
`BIOHUB_*` keys and 4 datasets exactly, +24 keys, +862 source lines; it omits 24 x138 lines, all
accounted for — see the proposal §1) and it runs
the validator with `ENABLE=1`. Kaggle publishes kernel output. So `kaggle kernels output` handed us
their `ppsweep_results.csv`, `ppsweep_selected.json`, `validator_results.csv` (112 rows = 14 configs
× 8 held-out stems) and a 982 KB log — zero GPU, zero submissions.

Archived: `docs/research/public_notebook_archive/amanatar_v9_sweep_telemetry/`, hashes in
`SHA256SUMS_amanatar_v9.txt`.

**The metric is now known from their code path:** `proxy = adjusted_edge_jaccard + 0.1 ×
division_jaccard` (verified numerically on all 14 rows), and `adjusted_edge_jaccard = edge_jaccard ×
f(t_pred/t_true)` where the count adjustment is **one-sided** — over-prediction is penalised,
under-prediction is not.

### The table (base = the x138 configuration)

| config | override | proxy | Δ | Δ **test-reweighted** | stems ↑/↓ |
|---|---|---|---|---|---|
| **ep015** | `OUTPUT_MIN_EDGE_PROB=0.15` | **0.9606** | **+0.0051** | **+0.00236** | 6 / 2 |
| dcsd015 | `DEEPCENTER_SAFE_DIV_THRESHOLD=0.15` | 0.9573 | +0.0018 | +0.00014 | 1 / 1 |
| leaf040 | `LEAF_PRUNE_MIN_EDGE_PROB=0.40` | 0.9558 | +0.0003 | +0.00018 | 6 / 2 |
| **base** | — | 0.9555 | 0 | 0 | — |
| **vel075 / rescue085** | the two genuine motion changes | 0.9555 | **0.0000000** | 0 | **0 / 0** |
| ~~tight55~~ | **same value as base — a no-op comparison** | 0.9555 | n/a | n/a | n/a |
| minlen5 · sym075 · repd_divgap | — | ↓ | −0.0005 … −0.0066 | negative | — |

"Test-reweighted" rescales the two embryo prefixes from the validator's native 26 %/74 % split to
the hidden test set's node split. **The hidden test set is `44b6_0113de3b`, `44b6_0b24845f`,
`6bba_05b6850b`, `6bba_05db0fb1` — two movies of each prefix, 45,250 / 75,969 nodes = 37 %/63 %**
(from exp_064's own collection). Reweighting halves `ep015`'s gain but leaves it ~13× larger than
anything else and does not change the ordering.

### Four results that close off standing arms

1. **`MOTION_RELINK_VELOCITY_WEIGHT` and `SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB` are INERT** —
   both are genuine changes (0.5→0.75 and 0.88→0.85) and both are *bit-identical* to base on all 8
   stems, every column. ⚠ **`tight55` is NOT on this list any more.** x138 already sets
   `MOTION_RELINK_TIGHT_UM = 5.5` and the candidate sets 5.5, so the sweep never varied it. The
   "`tight_um` is inert" claim is **withdrawn** (Codex challenge, 2026-09-25); that question is open
   again, and this table supports a `tight60` arm in neither direction.
2. **No post-process knob moves division recall.** `div_tp = 3` of 12 and `div_fn = 9` for **all 14
   configs**; only `div_fp` moves. With divisions weighted 0.1 and `division_jaccard = 0.214` there
   is ~0.079 of proxy sitting there, and it is **upstream-locked in detection/association**.
   exp_056 and exp_058 both died in this territory; this is the measurement that explains why.
   **Do not open a third division arc.**
3. **The one-sided count adjustment is a free, universal lever.** Decomposing `ep015`: the count
   factor improves on **8 of 8** stems (+0.0010 … +0.0073). All the heterogeneity is in raw
   `edge_jaccard`, down on exactly two stems — `44b6_341df25f` (base 0.995, nothing to gain) and
   `44b6_12dfb391` (already predicting 0.752 × t_true; pruning it further is simply wrong). The
   mechanism is understood, and it points at count-*targeted* variants over a flat threshold.
4. **Their guard rejected the only lever that mattered.** Logged rule: `>= +0.001 proxy AND
   per-embryo adj loss <= 0.0005`. `ep015` clears the margin but loses 0.0085 on the 44b6 prefix, so
   `dcsd015` shipped instead — worth **+0.00014** reweighted, i.e. nothing. **Running their notebook
   verbatim would gain us approximately zero.**

### And their run failed anyway

The log ends in `AttributeError: 'function' object has no attribute 'get'` — they assign
`_v6env = os.environ.get` then call `_v6env.get(...)` in a cell-12 summary `print`, *after*
`submission.csv` was written. Under papermill that fails the notebook, which is why `amanatar` is
still at 0.953 with 116 submissions. **Fifth instance in this project's recon of correct,
fully-wired machinery defeated by a trivial wiring fault.**

### 29 of their 41 declared candidates were never scored

`PP_CANDIDATES` holds **41 entries excluding base**, and `BIOHUB_PPSWEEP_FAST_TIER=1` limits the
sweep to a 12-item tier, so the archive is base + 12 declared + 1 generated combination = 14 rows and
**29** declared candidates are unmeasured. Unscored and high-value:
`ep010`, `ep020` (the rest of the winning family), `seg030L3`/`seg035L4`/`seg040L6` (pendant-segment
pruning), `cx03`/`cx06`/`cx10` (**count-target pruning — the principled form of result #3**), and
the stacks `prune_pack` (leaf030 + seg035L4 + ep015 + cx06), `ep_cx`, `seg_cx`, `leaf_seg`.

⚠ **Every `ep*`/`seg*`/`cx*`/`lfitclamp*` lever lives in amanatar's 862 added lines and does not
exist in x138 at all** (0 grep hits). They cannot be reached by flipping an env key on our exp_064
parent — using them means adopting amanatar's notebook as the parent.
`DEEPCENTER_SAFE_DIV_THRESHOLD` is the exception (x138 has it, at 0.25).

**Proxy → LB calibration: ONE point.** Base proxy `0.95549` against measured LB `0.953`, offset
−0.0025. Not a transfer function. Under it `ep015` predicts ~0.955; that is a prediction from one
offset and an 8-movie proxy and must not be quoted as an expected score.

---

## Next steps, ranked

1. ~~Write the proposal~~, ~~challenge round 1~~, ~~write v2~~, ~~challenge round 2~~ — all **done**.
   v2 is at `exp065_metric_aligned_pruning_proposal_v2.md`; both challenges returned **REVISE**
   (`exp065_codex_challenge_v1.md`, `exp065_codex_challenge_v2.md`). Round 2 fixed F1/F2/F4 and
   raised **5 new blocking findings, all verified genuine**. **The live work item is proposal v3** —
   see `STATE.json.next_action` for the five required changes, the largest being that the Run 1
   reservation must rise: the `seconds` column gives a 324.83 s median per configuration, so
   7000 + 29×324.83 = **16,420 s = 4.56 h**, which exceeds the 4.0 h v2 reserved. The design, for
   reference — vehicle is `amanatar/optimized-biohub-max-score` over the exp_064 parent, lever is the
   `ep`/`seg`/`cx` pruning family, and control and measurement are **fused into one run** because
   `write_test_submission("base")` runs before the validator block **and an authored 4-line snapshot
   preserves it** (without the snapshot the sweep overwrites the control and Gate 1 cannot run):
   - **Run 1 — control *and* measurement, 0 submissions, ~3 GPU h (reserve 4).** Their notebook with
     the one-line typo fixed (cell index 11, papermill's `In [12]`: `_v6env = os.environ.get` →
     `_v6env = os.environ`), `VALIDATOR_ENABLE=1`, `PPSWEEP_FAST_TIER=0`, prefix guard **kept on**,
     every v5 lever at its `0 = off` default, v9 deadline ladder **unchanged**. Delivers (a) the base
     `submission.csv`, which must **byte-reproduce exp_064's `d52a5da2`** — the control, proving their
     862 lines inert when off and letting the parent inherit 0.953 at no LB cost — and (b) all 41
     candidates scored on 8 held-out stems. ⚠ Run 1's *own* final `submission.csv` is rewritten by
     **their** guard and **must not be submitted**.
   - **Run 2 — the bet, 1 submission, ~0.3 GPU h.** `VALIDATOR_ENABLE=0` plus the single winning
     override as a static value. Deterministic, no sweep, against a byte-verified control. **Only
     happens if Gate 2 selects something.**

   **Proposal → Codex challenge → CONSENSUS → build → fresh experiment-specific Codex admission
   PASS → snapshot smoke → budget reservation → explicit user authorization.** Nothing launches
   before all of it.
2. **`readmit-v1` — demoted, not dead.** Still cheap (~0.26 GPU h) and still a matched
   single-mechanism A/B against exp_064, but its expected effect is now unquantified. Keep it as a
   fallback, not the headline.
3. ~~LB mining~~ — done twice, 09-25 morning and afternoon. The public side is exhausted.
4. **Single-knob arms must still earn their slot** with an active-path check, a named failure
   mechanism, and a predicted measurable effect. The harvested table disqualifies the **velocity**
   and **short-track-rescue** knobs (genuine changes, bit-identical results) and the
   **division post-process** family; ⚠ it does **not** disqualify `tight_um`, whose claim was
   withdrawn — that question is simply unmeasured. Check the table before proposing any knob.
5. **Do not port exp_062 mutual-best anywhere.** k2 scored 0.944. The arc is closed.

---

## Budget — user ruling 2026-09-24 (late stage)

> Treat GPU as 20 h with **all limits released**; raise the daily LB cap to 5.

| | |
|---|---|
| GPU remaining | **19.741056 h** (20 h − exp_064's confirmed 0.258944 h) |
| protected reserve / per-experiment ceiling | **none** |
| LB cap | **5 per America/New_York day** |
| used | 3 of 5 on NY 09-24; **0 on NY 09-25** |

At ~0.26 h per x138-class run and ~2–3 h for a full validator+sweep run, **GPU is not binding.**
The binding constraints are evidence quality and Public-LB overfitting risk.

⚠ ~25 remaining slots **can** overfit the Public LB, and more slots do not improve the signal's
statistical quality. Freeze small batches before reading their scores, record every result, require
local corroboration for small gains, always preserve a robust baseline, and do not treat unused
slots as wasted.

---

## Governance notes

- **Recurring lesson, now five times: never read a declaration as behaviour.** x138's sweep is dead
  code behind one env flag; amanatar's whole v9 layer is defeated by a one-line typo *after* it
  produced a correct `submission.csv`. Before proposing any lever, prove the code path executes.
- Two Codex challenge rounds on 2026-09-24. Round 1 (repo-audited) produced four notebook claims,
  all independently re-verified and all correct. Round 2 (Codex's file access failed; it reasoned
  from supplied evidence) corrected my throughput arithmetic and rejected my proposal to tier
  admission by authored line count — correctly noting I was arguing for less scrutiny of my own work
  right after five rounds found defects in exactly that work. The right reading is that the
  admission **materials** were defective, not that the review was excessive; reduce rework with
  reusable regression fixtures, not by lowering the bar.

## Standing rules

- **Never auto-submit to the LB without the user asking.** Record every submission in
  `SUBMISSION_BUDGET.json` with an authenticated `score_source`.
- Competition is **notebook-only**: any arm's LB submission needs a kernel whose own output *is*
  that arm. **Never build another bespoke deployment adapter** — exp_061 burned 5 submissions and
  3.094 GPU h across three transport mechanisms and never got a score.
- Codex reviews: `gpt-6-astra`, effort `low`, read-only, model passed on the command line.
- **Verify a reviewer's factual claims against the repo before accepting them.** Equally: verify
  *our own* claims before acting on them — this arc has now produced five corrections to things the
  project asserted before measuring.
- Claude must **never** play the Codex reviewer role.
- English only for code, notebooks, configs and technical docs. Never `git add -f` `.kaggle/` or
  `.private/`.
- **Git: work on `main` and push to `main`** (user ruling 2026-09-25; the old feature-branch flow is
  retired). ⚠ **The GitHub repo is PUBLIC.** The LB mining recon — commits `e4f8c4a`, `972e812`,
  their merge, and now the 09-25 afternoon recon — is **deliberately held back from the remote until
  the competition closes**, because it names un-run candidates. Local `main` carries it; remote
  `main` stops at `e8f233c`. A `.git/hooks/pre-push` guard blocks any push that would publish them;
  push the safe prefix explicitly (`git push origin <safe-commit>:refs/heads/main`), or after the
  deadline override deliberately with `ALLOW_RECON_PUSH=1 git push origin main`. Before pushing
  anything new, check whether it discloses un-run strategy.
- Regenerate the checkpoint block with `python scripts/render_checkpoint.py` after editing
  `STATE.json`; never hand-edit that block.

## Key pointers

- **Current recon (read this first):** `docs/research/lb_recon_2026-09-25_amanatar_sweep.md`.
  Supersedes the "next step" in `docs/research/lb_mining_2026-09-25.md`, whose §"correction #1"
  no-telemetry conclusion it also overturns. Both supersede
  `leaderboard_recon_2026-09-24.md` (standings) and `public_frontier_recon_2026-09-23.md` (stale).
- **The harvested telemetry:** `docs/research/public_notebook_archive/amanatar_v9_sweep_telemetry/`
  — `ppsweep_results.csv`, `ppsweep_selected.json`, `validator_results.csv` (112 per-stem rows),
  `sweep_decision_log_excerpt.txt`. Hashes: `SHA256SUMS_amanatar_v9.txt`.
- **Archived third-party notebooks (with hashes):** `docs/research/public_notebook_archive/` — now
  also holds `optimized-biohub-max-score.ipynb` (the proposed new parent),
  `biohub-035-deconfounded-edge-stack.ipynb`, `biohub-x138.ipynb` (current parent),
  `biohub-frontier947-readmit-v1.ipynb` + `-fast-v1` + `-fast-tight60-v1`.
- **Parent:** `experiments/exp_064_x138_verbatim_repro/` — Public LB **0.953**, submission 56535761;
  `experiment.json`, `review.md` (the 5-round PASS), `collection/`, `kaggle_kernel/`. Collection
  adapter / submission gate: `scripts/collect_exp064_x138.py`.
- **Previous parent:** `experiments/repro_059_public_0947_exact_copy/` — 0.947, submission 56313491.
  Keep as the robust fallback baseline.
- **Closed:** `experiments/exp_062_mutual_best_edge_association/` (0.944, reverted);
  `experiments/exp_063_public_0951_pipeline_repro/` (abandoned, wrong target).
- **Density measurement:** `docs/research/test_density_measurement_2026-09-24.md` — read with
  result #1 above, which retires the lever it was pointing at.
