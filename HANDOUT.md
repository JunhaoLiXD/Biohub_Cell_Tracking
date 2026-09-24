# Session Handout — updated 2026-09-24T20:45Z

Purpose: hand the current state to the next session AND to the user. Read this FIRST, then
`STATE.json`, then the active `experiments/exp_064_x138_verbatim_repro/` record.

If anything here disagrees with `STATE.json`, **`STATE.json` wins.**

**Competition closes 2026-09-29 23:59 — five days out.**

---

## >>> NEXT SESSION: START HERE <<<

**Two things are in flight. DO NOT POLL either one.**

### 1. exp_064 — x138 verbatim reproduction, RUNNING

| | |
|---|---|
| kernel | `lingxd/biohub-exp064-x138-repro` **version 1** |
| launched | 2026-09-24T20:35:55Z, via the controller |
| what it is | **anvithpothula/biohub-x138, byte-for-byte. ZERO code authored by us.** |
| notebook sha | `6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d` |
| reserved | 2.5 GPU h (attended target, *not* a hard ceiling — see Budget) |
| watchdog | Monitor task; fires on terminal state or at 2h15m after launch |

⚠ **The watchdog must be RE-ARMED.** Monitor sessions expire after 30 minutes; an expiry notice is
**not** a terminal state. Re-arm until the kernel actually terminates. It has already been re-armed
once.

**When it finishes — collect ONCE, then run the adapter. Its exit code is the submission gate:**

```bash
kaggle kernels output lingxd/biohub-exp064-x138-repro -p <scratchpad-dir>
python scripts/collect_exp064_x138.py <scratchpad-dir>    # exit 0 = may submit; non-zero = DO NOT
```

Then reconcile actual GPU hours from **confirmed termination**, never a nominal figure.

### 2. exp_062 k2 — LB submission 56530197, PENDING

Submitted 2026-09-24T19:34:49Z. **No score yet.** Do not resubmit. Check with
`kaggle competitions submissions -c biohub-cell-tracking-during-development -v`.

Decision rule vs 0.947: **≥0.948** adopt as new parent · **==0.947** CLOSE the probe (equality
cannot distinguish cancellation from rounding, and does not license a larger β) · **≤0.946** revert.

### The submission gate for exp_064

- Adapter exit code 0, **and**
- output byte-differs from **both** `d3453380` (parent) and `ba9431c1` (exp_062 k2) — the adapter
  checks this; a match means zero information and a wasted slot, **and**
- **k2's score is resolved**, because the comparator is `max(0.947, k2)`, not a bare 0.947, **and**
- separate user authorization + a remote cap check.

Cap is **3 per America/New_York day** (project rule, stricter than the platform's 5).
**1 of 3 used on 2026-09-24.**

---

## Where we actually stand — corrected today, and it is worse than we thought

Full authenticated leaderboard download, 3888 teams, `2026-09-24T20:03:35`:

| | 09-23 recon (stale) | **09-24 measured** |
|---|---|---|
| rank 200 | 0.949 | **0.953** |
| rank 100 | — | 0.954 |
| rank 50 | — | 0.957 |
| rank 1 | 0.975 | 0.975 |
| **our 0.947** | "just outside the top 200" | **rank ~478 of 3888** |

The rank-200 cutoff moved **0.949 → 0.953 in a single day**. The real gap is **0.006**, not 0.002.
Any plan premised on "we're 0.002 away" is obsolete.
Record: `docs/research/leaderboard_recon_2026-09-24.md`.

## Why x138, and why NOT the notebook we were about to run

**exp_063 (the haideptry family) is ABANDONED.** It was the wrong target, and the admission caught
it before we spent a run on it:

| | `haideptry` | `anvithpothula` (x138) |
|---|---|---|
| on the 3888-row LB | **absent entirely** | **rank 62, score 0.956** |
| claim | "SOTA 0.951+" in the title | none in the notebook |
| votes | 5–23 | 104 |
| mechanism check | **DivNet gate provably throws on every call** | clean, see below |

haideptry's flagship "DivNet 3D Gate" builds a 6-D tensor and feeds it to a `Conv3d` that needs 5-D
with `in_channels=1`; the exception is swallowed, `None` is returned, and the veto fires only on
non-`None`. It can never veto anything. Details in `experiments/exp_063_.../review.md`.

**x138 is a different and far better-engineered artifact.** Its distinctive mechanism is a **V1284
coordinate-refinement head** — "frozen-feature coordinate regression at first-seen fused detections"
— which refines node **coordinates**. Every previous intervention in this project acted on edge
association, division gating or post-processing; none has touched node position.

⚠ But it is **not** "just a coordinate head", and it is **not orthogonal** to our edge work — the
head changes feature sampling as well as coordinates, so it feeds association. The notebook also
carries neighborhood-flow relinking (7.0 µm gate when a flow field exists vs 5.5 without), detection
re-admission, gap filling from sub-threshold peaks, continuous density-adaptive gap closing, and
dual-seed fusion. It is **not causally isolated** and is not presented as one: if it wins, we will
not know which part won.

## What "verbatim" means here, verified

Four copies hash identically — the fresh pull, the in-repo archive, the frozen snapshot, and
`kaggle_kernel/` (what was actually pushed): all `6b655e39…`. The push directory contains only the
notebook and a metadata file — no injected cells, no patches, no extra scripts. Our builder, parity
guard and behavioral tests were **not used**, because nothing was built.

Kernel metadata differs only in identity: `id`, `title`, `is_private`, omitted defaults, and
`docker_image_pinning_type: original` (which *locks* the digest). Every execution-relevant field —
all four `dataset_sources`, the docker digest, accelerator, GPU, internet — is identical to theirs.
This is the CLI equivalent of Kaggle's "Copy & Edit"; the only thing it lacks is the cosmetic
"forked from" lineage link.

## The one risk that is accepted, not eliminated

`anvithpothula/biohub-v1284-head-s075` (public, 30 KB) has **unverifiable training provenance**. The
notebook comments claim 20 TRAIN movies / 4,136 pairs / held-out-by-movie validation, but those are
comments, not an auditable manifest. Codex's ruling: *"Neither uncertainty alone must block this
bounded reproduction. Record them as unresolved risks and let the remote run test compatibility."*

⚠ **An earlier claim was withdrawn:** that a head mismatch "cannot silently produce a degraded
submission" was **too strong**. Strict state-dict matching and the displacement check catch *gross*
failures, but badly normalized features can still yield finite, bounded displacements and a quietly
worse result. **Only the LB score would reveal that.**

Safety: the head loads with `weights_only=True` — no unrestricted pickle. The one
`weights_only=False` (cell 5:365) is the DeepCenter checkpoint, which **our own parent loads
identically**, pinned to the same SHA `8040999a…`. Inherited surface, not a new one.

---

## Governance: the admission took five rounds and every one found real defects

Nearly all of them were **mine**. Worth remembering: this is the second consecutive experiment where
the review paid for itself outright.

| round | finding | whose |
|---|---|---|
| 1 | "coordinate head, orthogonal to our edge work" — incomplete and overstated; five mechanisms omitted | mine |
| 1 | no basis to infer a 0.947 score floor from the author's rank | mine |
| 2 | adapter false pass: `coords=1e30` passed, because `math.isfinite(1e30)` is True | mine |
| 2 | degradation regexes were **guessed**, not read from the notebook — none matched | mine |
| 3 | adapter false pass: stats lacking the degradation columns read as "no degradation"; dangling edges unchecked | mine |
| 3 | the "cannot silently degrade" claim was too strong | mine |
| 4 | adapter false pass: endpoint existence still admitted a **self-loop**; any non-`node` row treated as an edge | mine |
| 4 | budget text still said "enforceable ceiling"/"worst case" while disclaiming enforcement | mine |
| 5 | **PASS** | |

Round 1 also **cleared the notebook itself** by executing its patch chain in memory: all cells
compile, the patched predictor compiles, all 13 support-file hashes match, and V1284 is genuinely
wired in (refine at patched line 636; `_v1284_index` replacing `UNetNodeTransformer._index_features`
at 984), with correct shapes, bounded and clipped displacement, and no exception path silently
disabling it.

**Recurring lesson, three times now: never read a declaration as behaviour.** Marker counts,
environment assignments, and self-attested fields are not evidence of what executes — the notebook's
`ground_truth_accessed: False` is a hardcoded constant written *before* prediction, and citing it as
compliance evidence was caught three separate times.

## Budget

| | |
|---|---|
| remaining | **16.872382 h** |
| protected reserve | 6.0 h |
| **discretionary** | **10.872382 h** |
| reserved for exp_064 | 2.5 h |
| exp_062 total draw | 3.526292 h (k1 1.727487 + k2 1.798805) |

⚠ 2.5 h is an **attended target, not a hard ceiling**. Kaggle exposes no CLI cancel, so the watchdog
*detects* and a human cancels in the UI; operator response is not technically bounded and the run
can overrun. The 4.0 h cumulative allowance for exp_064 is a budgeting intent, not a guarantee.
Reconcile from confirmed termination.

---

## A free finding worth keeping: our tight55 is mis-set on 3 of 4 test movies

Measured from our own k1 output, zero GPU
(`docs/research/test_density_measurement_2026-09-24.md`):

| dataset | nodes/frame | public group | that group's `tight_um` | ours |
|---|---:|---|---:|---:|
| `6bba_05b6850b` | 61.5 | low | **7.25** | 5.5 |
| `44b6_0b24845f` | 207.3 | middle | **6.5** | 5.5 |
| `44b6_0113de3b` | 256.4 | middle | **6.5** | 5.5 |
| `6bba_05db0fb1` | 702.9 | high | 5.5 | 5.5 ✓ |

Density spans **11.4×**. Our frozen global `tight55` was selected as a *single* value over eight
held-out training movies and matches only the high-density one. This is the first lever in the
project with **independent measured support from our own data** rather than a third party's headline
number. It is the designated successor if x138 does not pan out.

Caveat: this shows our global value is *questionable*, not that 7.25/6.5 are *correct* — those are
another author's constants, selected on unknown data.

---

## Key pointers

- **Active:** `experiments/exp_064_x138_verbatim_repro/` — `experiment.json`, `review.md` (the
  5-round PASS), `snapshot/`, `kaggle_kernel/` (what was pushed).
- **Collection adapter:** `scripts/collect_exp064_x138.py` — the submission gate. Hardened against
  three Codex false-pass fixtures; regression-checked on 241k real rows / 118,548 edges with zero
  false failures.
- **Archived third-party notebooks (with hashes):** `docs/research/public_notebook_archive/` — kept
  in-repo because a notebook the 09-23 recon quoted **went 403 mid-analysis**.
- **Recon:** `docs/research/leaderboard_recon_2026-09-24.md` (current) supersedes the standings in
  `public_frontier_recon_2026-09-23.md` (stale).
- **Abandoned:** `experiments/exp_063_public_0951_pipeline_repro/` — BLOCKED, wrong target.
- **exp_062 (closed pending its score):** `experiments/exp_062_mutual_best_edge_association/`.
- **Parent:** `experiments/repro_059_public_0947_exact_copy/` — Public LB 0.947, submission 56313491.

## Standing rules

- **Never auto-submit to the LB without the user asking.** Record every submission in
  `SUBMISSION_BUDGET.json` with an authenticated `score_source`.
- Competition is **notebook-only**: any arm's LB submission needs a notebook whose own output *is*
  that arm. **Never build another bespoke deployment adapter** — exp_061 burned 5 submissions and
  3.094 GPU h across three transport mechanisms and never got a score.
- Codex reviews: `gpt-6-astra`, effort `low`, read-only, model passed on the command line.
- **Verify a reviewer's factual claims against the repo before accepting them** — though note that
  in this arc essentially every Codex finding was correct.
- Claude must **never** play the Codex reviewer role.
- English only for code, notebooks, configs and technical docs. Never `git add -f` `.kaggle/` or
  `.private/`.
- Regenerate the checkpoint block with `python scripts/render_checkpoint.py` after editing
  `STATE.json`; never hand-edit that block.
