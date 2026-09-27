# PLAN — the remaining four days

Written 2026-09-25. **Competition closes 2026-09-29 23:59.**

This is the working checklist. `STATE.json` remains the authority on *state*; this file is the
authority on *what we agreed to do next*. If they disagree, `STATE.json` wins on facts and this file
is stale — fix it.

**Nothing below is authorized yet. Nothing is running. No GPU is committed.**

Agreed between Claude Code and an independent Codex strategy review
(`docs/research/exp065_codex_independent_strategy_2026-09-25.md`), which was given a purely factual
brief with Claude's own ranking withheld so it would not be anchored. That review corrected three
material errors in Claude's analysis; all three were verified and are recorded in the same file.

---

## Where we stand

| | |
|---|---|
| Best Public LB | **0.953** — `exp_064`, submission 56535761, output sha `d52a5da2…` |
| Rank | **361 of 3899**, on a **249-team plateau** spanning ranks ~200–420 |
| What a thousandth buys | ~190 ranks. 0.954 → ~171 · 0.955 → ~121 · 0.956 → ~91 |
| GPU remaining | **17.70 h** |
| LB slots | **5 per America/New_York day**, 0 used on 09-25, ~25 before close |
| Private score | **unrevealed.** `privateScore` is empty on all 30 submissions |

**Total plan budget: ~7 GPU h and ≤5 slots. Stop all new research 2026-09-28** and keep the last day
for final selection and deployment reliability. Unused slots are not a target to fill.

---

## Step 0 — Reconcile the recoverability audit. ✅ **DONE 2026-09-25. Result: Step 2 CANCELLED.**

**Why first:** it costs no GPU and no slot, uses data we already have, and it decides whether Step 2
is the biggest prize on the board or worthless.

The `division_recoverability_audit()` already ran in our own exp_065 log and reported:

```
TOTAL: reproduced_ok=2  recoverable_by_postprocess=7  missing_second_daughter=3  parent_unmatched=0
```

That says **7 of the 9 division false-negatives have both ground-truth daughters already matched to
predicted nodes** — the detections exist, only the linking is missing — against only 3 that are
detection-limited. If true, post-processing can reach them and recovering 3 is worth **+0.02143**
proxy, four times the entire pruning family's best result.

**But it cannot be trusted yet.** Two defects:

1. The audit's `reproduced_ok` branch (notebook cell line 5649) counts a matched parent with ≥2
   outgoing edges as reproduced **without checking those edges reach the correct daughters**.
2. Concrete evidence of that: the audit says `reproduced_ok=2` while the official division scorer says
   `div_tp=3` on the same base config. **They disagree by one event.**

**Do:** reconcile the audit against the scorer using
`experiments/exp_065_metric_aligned_pruning/collection/validator_results.csv` and
`.../run_log_clean.txt`. Re-derive, per event, whether the parent and both daughters are matched and
whether the emitted edges reach the right daughters.

**Decision rule:** if the recoverable count survives reconciliation → Step 2 is the priority. If it
collapses (most "recoverable" events are really mis-linked or detection-limited) → **cancel Step 2**
and treat divisions as closed.

### Outcome — it collapsed. Write-up: `docs/research/step0_division_audit_reconciliation_2026-09-25.md`

- **Denominators agree** (12 GT events both ways), and the whole discrepancy is **one stem**,
  `44b6_2a2eff9f`: the scorer calls its division a **true positive** while the audit calls it
  `recoverable_by_postprocess`.
- **Cause: the official scorer's criterion is component-level, the audit's is node-level.**
  `compute_division_confusion` awards a TP when one weakly-connected component contains a node matched
  to the anchor (the GT parent *or its own parent*), is touched by some matched descendant of each
  daughter lineage, and contains **any** node with out-degree >= 2 — **the fork need not be at the
  matched parent.** The audit only asks whether the matched parent itself emits two edges.
  `44b6_2a2eff9f` is the existence proof that these differ.
- **So the audit's 7 is not a count of scorer-rewardable opportunities** — and decisively, the 9 FNs
  failed the *looser* test. Failing it means a daughter lineage has no matched node anywhere, or the
  anchor is unmatched, or the component has no fork at all, or **the two lineages sit in different
  components (fragmentation)**. The post-process division levers add or accept **forks**; they do not
  merge fragmented components and cannot create missing detections.
- Precedent that makes this decisive: **exp_055's joint cut-and-reconnect repair scored +0.0148537 on
  the local proxy and moved the Public LB 0.000.** Fragmentation is exactly that territory.
- Bonus caution: **every `div_fp` sits on a stem that also has a `div_tp`** — the signature of a fork
  landing on the wrong node near the right place. So "remove the 2 FPs" and "recover FNs" are **not
  independent levers**, and the +0.00165-per-FP arithmetic is an upper bound only.

**If Step 2 is ever revived, its first deliverable is the per-event branch assignment** (which of the
four failure modes each FN hits). That needs the validator prediction graphs, which the notebook holds
in memory as `VAL_BASE_PROCESSED` and never writes out — so it costs a new run.

---

## Step 1 — Probe `cx03`. ~0.3–0.5 GPU h, 1 slot.

`BIOHUB_COUNT_EXCESS_FRAC = 0.03` — the core-relative node budget.

**Why this is the first submission, not `ep015`:**

| | notebook aggregate delta | vs its 0.001 margin | worst per-embryo regression | vs the author's −0.0005 cap |
|---|---|---|---|---|
| **`cx03`** | +0.00090086 | misses by 0.0001 | **−0.00016144** | **PASSES** |
| `ep015` | +0.00512577 | clears | **−0.00849388** | **fails** |

`ep015`'s worst prefix regression is **52.6× larger**. `cx03` is the only measured candidate that
satisfies the notebook author's own anti-overfit cap, and it missed selection by a hair rather than by
showing no effect. Against an unrevealed private split that difference matters more than the headline
delta.

**Honest status:** `cx03` fails *our* Gate 2 on the aggregate bar (+0.00115 test-reweighted vs our
+0.0015 threshold). This is a registered exploratory probe, **not** a Gate 2 pass.

**Build:** adapt `scripts/build_exp065_pruning_sweep.py` per proposal v3 §4.5 — `VALIDATOR_ENABLE`
`"1"` → `"0"` and `COUNT_EXCESS_FRAC` `"0.0"` → `"0.03"`, one line each, no sweep, deterministic.
Keep the snapshot and the auto-attach assertions. **Prove at runtime that the setting changed the
output** — compare the output sha against `d52a5da2…`; if it is identical the lever did not fire.

**Read:** ≥0.955 adopt · 0.954 small real gain · 0.953 null, keep the parent · ≤0.952 revert.

---

## ~~Step 2 — Event-led division investigation~~ ❌ **CANCELLED by Step 0, 2026-09-25.**

Kept below for provenance and in case it is ever revived. **Do not start it without redoing
Step 0's reasoning** — the premise it rests on ("7 FNs are recoverable by post-processing")
was measured false.

The project has repeatedly intervened downstream and left `div_tp = 3 / 12` untouched across **30**
measured configurations. Nine missed divisions have never been explained at the level needed to
choose an intervention.

**Trace each of the 12 labelled events:** is the parent detected; are both daughters detected; are the
correct candidate links generated; **which gate rejects them, with its actual score and geometry**; do
accepted links survive the ILP solve and all later processing; does the scorer recognise the correct
parent–daughter identities. Trace the 2 false positives the same way.

**Then at most two targeted interventions**, chosen from what the trace actually shows — not from
suggestive names. The audit itself points at:

- correct candidates blocked by the DeepCenter veto → `dcsd010`
- correct candidates failing the divergence test → `diverge150`
- second daughter present but never linked → one `repd010` / `repd015` / `repd015w` configuration

⚠ **These were never scored, because narrowing the exp_065 sweep to the 15-member pruning family
excluded exactly this family.** Of the division candidates that *were* measured, most were harmful:
`sym075` −0.0054 proxy, `repd_divgap` −0.0066, `dcsd015` +0.0018, `divwide` ≈ 0.

**Optional enabler:** `BIOHUB_VALIDATOR_N_PER_TYPE` 4 → 8 enlarges the held-out sample at roughly
linear validator cost. The selector sorts by *contains any division* then **lexicographically**, not
by division count, so **12 events is not a ceiling** and more division-bearing movies may exist. This
buys measurement capacity, not score.

**Kill rule:** if the trace shows the required detections are missing, **abandon this route** — do not
spend the remaining days relaxing gates that were correctly rejecting negatives. A gate's high
rejection rate says nothing by itself about whether it rejects *true* divisions.

---

## Step 3 — Probe `ep015`. ~0.3–0.5 GPU h, 1 slot.

`BIOHUB_OUTPUT_MIN_EDGE_PROB = 0.15`. The largest measured effect (+0.00236 test-reweighted) and the
most distribution-sensitive.

**Explicitly a speculative exception to a pre-registered rejection**, not an adopt. It fails our Gate 2
on two of three conditions: 10 of the 36 test-shaped subsets are strictly negative (limit 3), and the
44b6 prefix regresses −0.0084939 (limit −0.001). 60.6 % of its gross positive sits in one held-out
movie.

Note: `ep010`, `ep020`, `ep_cx` and `prune_pack` are **bit-identical** to `ep015` in every field, so
the threshold magnitude between 0.10 and 0.20 has no effect and there is nothing to tune. Do not
search neighbouring values. Do not combine with `cx03` — there is no evidence a combination adds
anything, and `ep_cx` demonstrates it does not.

---

## Step 4 — Remove the V1284 head. ≤2 GPU h, 0–1 slot.

Run `thtennant/biohub-frontier947-readmit-v1`, archived at
`docs/research/public_notebook_archive/biohub-frontier947-readmit-v1.ipynb`. It is x138 **minus** the
third-party coordinate-refinement head and nothing else: identical across all 87 `BIOHUB_*` keys, a
strict source subset, needs only the three checkpoints we already mount. x138 adds 34 lines, all
head-related.

A matched single-mechanism A/B against exp_064, and it carries no third-party weights of unverifiable
provenance. **Its expected direction is unknown** — that is why it sits below Step 2. Require changed
coordinates and graphs before believing the arm is live.

---

## Step 5 — Read the three unanalysed public artifacts. Zero GPU. Timeboxed.

1. **`y3uanm`'s two notebooks** (author 0.956 / 62 subs) — they set **zero** `BIOHUB_*` keys and mount
   `hftams/zebrahub-zsns003`, a dataset no one else uses. **The only genuinely different lineage in the
   public set.** Pulled but never read.
2. `seyitkaangunes/biohub-035-deconfounded-edge-stack` (0.954 / 45) — a lighter base, x138 minus its 30
   flow / gapfill / readmit keys, plus `LEAF_PRUNE_MIN_EDGE_PROB=0.30`. Not a wholesale replacement
   candidate: it removes many settings at once and leaf pruning measured at +0.00018 on our base.
3. `haideptry/biohub-0-951-…` — mounts `giorgosi/biohub-divnet-v2`, a 5.6 MB 3D-CNN.
   ⚠ **DivNet is a veto**, driven by `BIOHUB_DIV_MIN_PROB=0.50`. It addresses `div_fp = 2` and
   **cannot touch `div_fn = 9`**; ceiling ≈ +0.0036. Do not adopt it expecting recall.

An unusually compelling finding here may re-order Step 4. Author scores do not establish notebook
scores — that is settled: x138's author sits at 0.956 while their published notebook measures 0.953.

---

## Two cheap things that matter more than any +0.001

- [ ] **Preserve the exact x138 notebook that actually scored 0.953** as the fallback, with its
      dependencies. Byte-identical *visible* output does **not** guarantee identical hidden-rerun
      behaviour across different notebook sources, so Gate 1's PASS is not a substitute for keeping the
      artefact that really scored.
- [ ] **Check on the competition site whether final submissions must be selected manually**, and if so
      that 0.953 is selected. No reliable API for this — needs a human look. If multiple finals are
      allowed, keep x138 alongside the strongest supported challenger.

---

## Standing rules that still bind

- **Never submit to the LB without being asked.** Record every submission in `SUBMISSION_BUDGET.json`
  with an authenticated `score_source`.
- Notebook-only competition: an arm's submission must be a kernel whose **own output is that arm**.
  **Never build another bespoke deployment adapter** — exp_061 burned 5 submissions and 3.094 GPU h
  across three transport mechanisms and never got a score.
- **Treat every "this knob should help" claim as unverified until its code path is shown to execute.**
  Seven recorded instances now of machinery that was present, wired and documented and did nothing:
  a competitor's sweep disabled by one flag; an empty-string setting whose polarity we read backwards;
  a config-drift guard we tripped ourselves; and an audit whose output sat unread in our own log.
- Claude Code never reviews its own proposal. Codex reviews: `gpt-6-astra`, effort `low`, read-only,
  model on the command line.
- Verify a reviewer's factual claims against the repo before accepting them — **and verify our own**.
  This project has now recorded fifteen corrections to claims it made before measuring.
- English only for code, notebooks, configs and docs. Never `git add -f` `.kaggle/` or `.private/`.
- ⚠ The GitHub repo is **public** and the recon commits are **held back from the remote until close**
  because they name un-run candidates. Check before pushing anything new.

---

## Honest expectation

The public ceiling is 0.953 and we are on it. Everything above the plateau was reached through
unpublished work. A realistic outcome for these four days is **0.953–0.955**, i.e. rank ~361 → possibly
~121. Step 2 is the only route with a mechanism that could plausibly go further, and its first move
costs nothing. **0.96+ has no evidenced path from here.**
