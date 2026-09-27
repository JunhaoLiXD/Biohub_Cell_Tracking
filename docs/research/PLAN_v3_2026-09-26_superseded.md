# PLAN — final 2.5 days (v3, post-Stage 0)

**v3, 2026-09-26 22:30 UTC.** v1 → Codex `REVISE` → v2 → Stage 0 executed → v3. Earlier versions:
`docs/research/PLAN_2026-09-25_superseded.md`, `docs/research/plan_v1_codex_review_2026-09-26.md`.
Competition closes **2026-09-29 23:59**.

---

## 1. Status

| | |
|---|---|
| Best Public LB | **0.953** — `exp_064`, submission 56535761, rank ~361 / 3899 |
| Final submission | **SELECTED by the user 2026-09-26.** Banked. Downside of stopping is zero. |
| Public ceiling | **0.953.** Re-verified across ~500 public notebooks. Nothing above it is published. |
| GPU remaining | **16.75 h**, none committed |
| LB submissions | 5/day available |
| Running | **Nothing.** |

**Closed:** `cx03` (LB 0.953, registered null) · Step 2 division investigation (cancelled by the
Step 0 audit) · Step 5 recon (done) · `exp_062` (0.944) · `exp_060` (0.947 null) · `exp_061`
transports (5 submissions, 3.09 GPU h, never scored) · **exp067 competition arc (see §2)**.

## 2. Stage 0 settled the exp067 arc, for zero GPU

Full report: `docs/research/exp067_stage0_result_2026-09-26.md`.

Of 12 ground-truth divisions across the 8 exported movies, 7 are missed by the parent. **Six of the
seven have both required edges already in the candidate set — but zero generate a division event.**
`symmetric_event_geometry` rejects 7 of 7, because the real missed divisions are **asymmetric**: one
daughter 0.34–2.67 µm from the mother, the other 6.74–11.52 µm. Relaxing distance gates changes
nothing; dropping `safe_div_sister_symmetry_tau` from 0.6 to 0.0 admits **7/7**.

That 0.6 is inherited from x138's `BIOHUB_SAFE_DIV_SISTER_SYMMETRY_TAU` and has been present in
**every configuration this project has ever measured**. It explains `div_tp = 3/12` across 30
configurations: a **prior**, not a search or scoring failure.

**And the decisive catch.** The harvested public sweep already measured the parent-side analogue —
arm `sym075`: `div_tp` unchanged at 3, `div_fp` **2 → 6**, `div_fn` unchanged at 9, proxy
**0.955489 → 0.950093**. Relaxing the geometry *alone* admits noise, not signal. exp067 would need
relaxation **and** a discriminator learned from ≤45 examples. Nothing in the evidence supports
expecting that.

**exp067 is stopped for this competition.** The export is banked and the finding is the real asset.

## 3. Primary objective: protect the 0.953

This outranks everything below. Concretely, before 2026-09-29:

- [ ] **Re-verify at close** that the selected final is submission **56535761** (0.953) and that
      nothing done in the remaining days silently displaced it. Needs a human on the site.
- [ ] Keep `experiments/exp_064_x138_verbatim_repro/` and its snapshot untouched.
- [ ] If any probe below scores higher, changing the selection is a **separate, explicit decision** —
      see the caution in §4.

## 4. Optional: one last probe, `ep015`. User's call. ~0.5 GPU h, 1 submission.

`OUTPUT_MIN_EDGE_PROB = 0.15` on the x138 parent. One environment key, deterministic, same vehicle
as `cx03`.

**This reverses v2 §7, which said "no post-processing knob probes."** The reason for the reversal,
stated plainly rather than quietly: `cx03` was preferred over `ep015` precisely because `ep015`
fails the vehicle author's own per-embryo cap, and `cx03` has now closed null. Stage 0 then closed
the model-level route. `ep015` is simply the last item on the board with any measured positive
signal. That is a weak reason, and it is the honest one.

**Expected value, corrected downward.** `docs/research/lb_recon_2026-09-25_amanatar_sweep.md`
predicts ~0.955 for `ep015` from a single calibration point. **That prediction predates `cx03` and
should not be read at face value now.** We have a second point:

| arm | test-reweighted proxy | predicted | **actual LB** |
|---|---|---|---|
| `cx03` | +0.00115 | positive | **0.953 — exactly null** |
| `ep015` | +0.00236 | ~0.955 | untested |

The one arm we actually flew transferred **zero**. `ep015` is 2× its magnitude, which is a different
regime but not a different mechanism. Treat ~0.955 as an upper bound that the only real measurement
we have argues against.

**Known risk:** `ep015`'s worst per-embryo regression is **52.6× larger** than `cx03`'s. A higher
public score with a bad worst-case per-embryo profile is not obviously the better *final* choice.
**Scoring higher is not by itself sufficient reason to re-select.**

**Pre-registered read rule, fixed now:**

| Public LB | Action |
|---|---|
| ≥ 0.955 | Real gain. Consider re-selecting the final — a deliberate decision, weighing the per-embryo risk, not automatic. |
| 0.954 | Marginal. Record it. Default is to **keep 0.953 selected**. |
| 0.953 | Null. Keep 0.953. Close the pruning family for good. |
| ≤ 0.952 | Loss. Keep 0.953. Close the family. |

**Gates before launch:** versioned record, Codex admission review (the Codex allowance has reset),
snapshot smoke, budget reservation, explicit launch authorization, explicit submission
authorization. The `exp067` export waiver does not cover this.

## 5. Zero-GPU closeout, do regardless

- [ ] **Write up the division-prior finding properly.** It is the most valuable thing this project
      produced and it is currently one research doc. It explains a result — `div_tp` frozen at 3/12
      across 30 configurations — that no amount of further sweeping would have explained.
- [ ] Reconcile the ledgers: `GPU_BUDGET.json` (16.75 h), `SUBMISSION_BUDGET.json`, `STATE.json`,
      `EXP067_STATUS.md`.
- [ ] Optional, cheap: Stage 0 **Q2** (negative control) and **Q3** (positive control). They only
      matter if the arc is ever resumed, and they complete the record of what the decoder can do.
- [ ] Decide what, if anything, gets pushed to the public GitHub remote at close — the recon commits
      are still held back.

## 6. After the close — the route Stage 0 identified

Not for these 2.5 days. Recorded so it is not lost:

**Relaxed division geometry + dense supervision.** Stage 0 shows relaxation is *necessary* and the
`sym075` arm shows it is *not sufficient*. The missing ingredient is enough labelled asymmetric
divisions to train a discriminator. `hftams/zebrahub-zsns003` is public and carries 208 MB of dense
lineage tracks. `y3uanm`, the only author above us with published work, reached their result via
`real_sparse_teacher_plus_synthetic_dense` — dense labels, not more sparse ones.

## 7. Hard stops

- **Nothing runs without explicit user authorization.** Nothing is running now.
- No exp067 training, TEST decode, or GPU spend. The arc is stopped.
- No second probe if `ep015` runs. One, or none.
- No external or synthetic training data before the close.
- No new deployment adapter, ever — `exp_061` settled that.
- **2026-09-29 12:00 UTC: everything stops.** The last 12 h are for verifying the final selection,
  nothing else.

## 8. Standing rules

- **Never submit to the LB without being asked.** Record every submission in `SUBMISSION_BUDGET.json`
  with an authenticated `score_source`. Kaggle's cap is 5/day.
- Notebook-only competition: an arm's submission must be a kernel whose **own output is that arm**.
- **Do not poll Kaggle run status.** The user watches the runs and reports.
- Claude Code never reviews its own proposal. Codex: `gpt-6-astra`, effort `low`, read-only, model on
  the command line.
- **Verify a reviewer's factual claims against the repo — and verify our own.** Stage 0's first run
  reported a spurious "0 of 7 reachable" from two of my own defects (row-index vs node-id, then a
  shadowed variable). Both were caught before any conclusion was drawn. That is now nine recorded
  instances of machinery that looked like it worked and did not.
- English only for code, notebooks, configs and docs. Never `git add -f` `.kaggle/` or `.private/`.
- ⚠ The GitHub repo is **public**; recon commits are held back from the remote until close.
