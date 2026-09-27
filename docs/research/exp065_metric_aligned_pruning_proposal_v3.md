# exp_065 — Metric-aligned pruning on the 0.953 parent — v3

Status: **v3 — awaiting the third Codex challenge.** No CONSENSUS. No implementation, no launch, no
leaderboard submission is authorized by this document.
Author: Claude Code, 2026-09-25.
Parent: `exp_064_x138_verbatim_repro` — Public LB **0.953**, submission 56535761, output sha
`d52a5da2`.
Lineage: v1 → Codex **REVISE** (7 blocking) → v2 → Codex **REVISE** (`exp065_codex_challenge_v2.md`:
round-1 **F1, F2, F4 fixed**, F3/F5/F6/F7 partially fixed, **5 new blocking**) → v3.

**Twelve blocking findings across two rounds. All twelve were independently re-derived from the
notebook sources and all twelve were genuine. None was rejected.**

**The biggest change in v3 is not a wording fix.** Round 2 showed from the `seconds` column that
v2's "~3 h, reserve 4.0" was wrong — sweeping all 41 candidates costs **~4.5 h** and the notebook's
own bound is 7.25 h, so nothing would have stopped it at our reservation. Rather than raise the
reservation, v3 **sweeps only the 15 candidates Gate 2 can actually select from**: **~2.2 h**, with
an enforced deadline, and it answers the cost objection and the multiplicity objection at the same
time.

---

## What v3 fixes (round 2)

| # | v2 | status | v3 |
|---|---|---|---|
| B1 | Gate 2 counts subsets with `v <= 0` as negative; median read off index 18 of 36 | **BUG** — `dcsd015` is 9 negative **+ 9 exactly zero** (v2 said 18); `tight55` is 0 **+ 36** (v2 said 36, absurd for a config identical to base); `ep015`'s true median is **+0.002796470**, not +0.00319 | script counts **strictly** negative, reports `unchanged` in its own column, uses `statistics.median`; §3.3 and §8 restated. `ep015` is 10 either way |
| B2 | Run 1 ~3 h, reserve 4.0 | **WRONG** — median **324.83 s**/config over 14 configs, so `7000 + 29×324.83 = 16,420 s = 4.56 h`; and `SWEEP_DEADLINE_S = 26100 s` (7.25 h) is the notebook's own bound, checked *between* candidates | §4.4: sweep **only the 15 eligible candidates** (~**2.2 h**), reserve **4.0 h**, and lower `SWEEP_DEADLINE_S` to **12,600 s** so there is an *enforced* bound, not just a reservation |
| B3 | "corrections propagated everywhere" | **FALSE** — `STATE.json`, the recon doc and `HANDOUT.md` still asserted tight-distance inertness, "exactly one authored line", the crashed-run preservation argument, leave-one-out over all 41, the imprecise multiplier, 0.752 and 27 unmeasured | those fields **rewritten, not annotated**; superseded operational keys removed from `STATE.exp065_proposal` and replaced with `*_current` |
| B4 | §6 gate 7 "must reproduce … before it is used" | **UNENFORCED** — the script printed `MATCH`/`MISMATCH`, accepted residuals under `1e-9`, and continued to selection; it also checked only a shared stem set | both validations `raise SystemExit`; a 4-stems-per-prefix check raises; a missing-eligible-candidate check sets `SELECTION_ALLOWED = False` and **refuses selection**. On today's archive it correctly refuses — 13 of 15 eligible candidates are absent |
| B5 | Run 2 = "one changed line per selected key" | **FALSE** — `seg040L6` sets `SEG_PRUNE_MAX_LEN = 6`, already the cell 0 line 110 default | §4.5 gives the **per-candidate** budget as a table; `seg040L6` changes **1** line, not 2 |

Non-blocking changes: §3.1 no longer says Gate 1 establishes "the vehicle **is** the parent" (§5.1
always limited it correctly; the two now agree); MARGINAL is reframed as a **documented exception,
not a Gate 2 outcome**; the claim that rejecting `ep015` proves the thresholds were not
reverse-engineered is **withdrawn** — it is evidence about one candidate, not about the rule's
construction; and "28 % of draws lose" is labelled an empirical subset fraction over **dependent**
subsets, not an estimated hidden-test loss probability.

**The headline is unchanged: on current evidence nothing qualifies for a submission.**

---

## 0. Motivation

0.953, rank 361 of 3899, on a **249-team plateau spanning ranks ~200–420** — the public-notebook
ceiling. One thousandth is worth ~190 ranks (0.954 → ~171, 0.955 → ~121, 0.956 → ~91). No public
notebook scores above the plateau; every author at 0.956+ with published work got there over 40–206
unpublished submissions. Copying is exhausted; anything further must be measured.

## 1. Parent and vehicle

Every lever worth testing is absent from the parent's source — `grep` of `biohub-x138.ipynb` returns
**0 hits** for `OUTPUT_MIN_EDGE_PROB`, `LEAF_PRUNE_MIN_EDGE_PROB`, `SEG_PRUNE_MIN_PROB`,
`COUNT_EXCESS_FRAC`, `PPSWEEP_EXTENDED`, `PPSWEEP_PREFIX_GUARD`. They exist only in
`amanatar/optimized-biohub-max-score` (sha `371fc1f9f4f2…`), which adds **862 lines** over x138 and
shares x138's 89 `BIOHUB_*` keys and four datasets exactly.

**Exactly one intended configuration difference:** `BIOHUB_VALIDATOR_ENABLE`, `0` in x138 and `1` in
the vehicle — which Run 1 wants on anyway. v1's claimed `REPAIR_DEADLINE_S` difference was **my
error**; cell 0 line 69 is `27000` in both.

The 24 x138 lines the vehicle omits: 4 docstring, 2 labels, `write_test_submission("base")`
(re-emitted in a try/finally), 1 reflowed list literal, 4 `os.environ` lines re-emitted with
different comments (only `VALIDATOR_ENABLE` differing in value), and **12 inside the validator/sweep
selection block** the author rewrote.

So using these levers means running a different notebook, and the first thing to establish is that it
reproduces the parent when its levers are off. **v1 argued that statically and got a premise
backwards.** v3 makes it a measured gate with a fail-closed assertion behind it.

## 2. The intervention and the mechanism

**Lever family (the 15 eligible candidates):** `ep010`, `ep015`, `ep020` (L1 weak-edge filter);
`seg030L3`, `seg035L4`, `seg040L6` (L2 weak pendant segments); `leaf030`, `leaf040` (weak leaves);
`cx03`, `cx06`, `cx10` (L5 core-relative node budget); and the stacks `leaf_seg`, `prune_pack`,
`ep_cx`, `seg_cx`.

**The count adjustment, exactly.** Cell 8 line 77:

```python
return max(0.0, jaccard * (1.0 - a * (t_pred - t_true) / t_true))      # a = 0.1
```

For `t_pred < t_true` the multiplier **exceeds 1**: under-prediction is actively **rewarded**, not
merely unpenalised. Empirically the free half holds — for `ep015` the multiplier improves on **8 of 8**
stems (+0.0010 … +0.0073) — so all risk sits in raw `edge_jaccard`.

**`COUNT_EXCESS_FRAC`, with the overclaim removed.** `prune_to_node_count_target` needs no ground
truth: it pins a core (frame 0, final frame, edges with `edge_prob is None`, or `>= CORE_EDGE_PROB`
0.60), budgets `core_count × (1 + frac)`, and drops the weakest non-core, non-fork-parent nodes in one
pass.

v1 claimed this repairs `ep015`'s failure mode. **It does not.** The budget is relative to the graph's
own core, not to ground-truth excess: 800 nodes with a 500-node core at `frac = 0.06` targets 530
whether the truth is 400 or 1,000. It gives **no under-prediction protection**, and `44b6_12dfb391` —
where `ep015` lost most — already under-predicts at **0.76263 × t_true** (v1 quoted 0.752, which is
`ep015`'s ratio). What survives: the `cx*` budget is proportional to each movie's own confident
structure rather than a global probability cut, so it cannot strip a graph that is mostly core.
**That is a hypothesis with no score behind it**; its justification is that it is cheap to measure in
the same run.

**Closed door:** an exact per-movie count target is unavailable. `estimated_number_of_nodes` is read
only from the TRAIN ground-truth path inside the validator; `test/44b6_0113de3b.zarr/zarr.json`
(1,279 bytes, pulled from the competition) carries only `multiscales` and
`image_statistics.quantiles`, and there is no `.zattrs` (404).

## 3. Hypotheses

### 3.1 H_control

> With the vehicle configured as §4 specifies, its **snapshotted** base `submission.csv` is
> byte-identical to exp_064's output sha `d52a5da2`.

Pass → the vehicle **reproduces the parent on the four visible movies under this execution**, which is
the strongest available evidence that its 862 added lines are inert when off. It does **not** prove
general inertness and does **not** establish hidden-rerun equivalence (§5.1). Fail → **stop** (§8).

### 3.2 H_lever

> Some member of the 15-candidate pruning family improves the test-reweighted held-out aggregate by a
> margin that survives the test-shaped subset analysis and the author's own prefix guard.

**"Test-reweighted" is a modelling assumption.** The hidden test set is two `44b6` and two `6bba`
movies at 45,250 / 75,969 nodes = **37.329 % / 62.671 %**, but those are *our predicted output-node
counts* from exp_064's `metrics.json`, while the validator's own weights are edge-confusion
denominators that shift with the candidate. Different quantities. Observed test densities also say
nothing about private-test composition.

### 3.3 `ep015` fails, three independent ways

| evidence | `ep015` |
|---|---|
| test-reweighted aggregate, all 8 stems | **+0.00236** |
| concentration | `6bba_09961292` holds **60.6 %** of the gross positive |
| author's own prefix guard | 44b6 regresses **−0.0084939** vs their −0.001 limit → **rejected** |
| 36 test-shaped subsets | **10 strictly negative**, 0 unchanged; min **−0.00584**, median **+0.002796470**, max +0.01371 |

Empirically 10 of 36 test-shaped draws lose. **These 36 subsets are heavily dependent** (they reuse
the same 8 movies), so that fraction is a fragility indicator, **not** an estimated probability of
losing on the hidden test.

Next best: `leaf040` +0.00018 with 16/36 negative; `dcsd015` +0.00014 with **9 negative and 9
unchanged** (v2 mis-stated this as 18 negative) and not eligible anyway.

**H_lever has no qualifying candidate on current evidence.** **13 of the 15 eligible candidates have
never been scored** — only `ep015` and `leaf040` appear in the archive.

### 3.4 What the harvested table does and does not close

**Withdrawn:** that `MOTION_RELINK_TIGHT_UM` is inert. Both notebooks already set 5.5 and the
candidate sets 5.5 — the variable was never varied. That question is **still open** and this table
supports a `tight60` arm in neither direction.

**Survives:** `MOTION_RELINK_VELOCITY_WEIGHT` (default 0.5, `vel075` = 0.75) and
`SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB` (0.88, `rescue085` = 0.85) are genuine changes, bit-identical
to base on all 8 stems, every column.

**Survives with a qualification:** no post-process knob in this table moves division recall
(`div_tp = 3`/12, `div_fn = 9` across all 14; only `div_fp` moves). Strong evidence about **these 14
interventions**, not proof about every untested one. Sufficient reason not to open a third division
arc with four days left — a scheduling judgement, not a theorem.

### 3.5 H_null

Nothing passes Gate 2 → submit nothing, keep 0.953, and hold a measured map of the eligible pruning
family for ~2.2 GPU h and zero submissions. **An acceptable outcome**, reachable at no leaderboard
cost.

## 4. Design — two runs, at most one submission

### 4.1 Run 1 authored changes: 4 lines removed, 21 lines added

| # | location | change | why |
|---|---|---|---|
| a | cell 11 line 44 | `_v6env = os.environ.get` → `_v6env = os.environ` | their run died here; the eight `_v6env.get(...)` sites on lines 44–50 are `print` arguments and `submission.csv` is written earlier, but under papermill the unfixed line **fails the notebook** |
| b | cell 0 line 107 | `SWEEP_DEADLINE_S` `"26100"` → `"12600"` | an **enforced** 3.5 h bound on the sweep (§4.4). Cannot affect Gate 1: the base pass completes before the sweep starts |
| c | cell 10 lines 135–136 | replace the 12-name `_V7_FAST_TIER` tuple with the **15 eligible candidates** (2 changed, 2 added) | sweep exactly what Gate 2 can select from (§4.4) |
| d | cell 0 after line 228 | **+2** fail-closed assertions (§4.2) | the auto-attach hole |
| e | cell 5 after line 2880 | **+4** snapshot lines (§4.3) | preserve the control before the sweep overwrites it |

`BIOHUB_VALIDATOR_ENABLE` and `BIOHUB_PPSWEEP_FAST_TIER` need **no** edit — the vehicle already ships
`"1"` for both. Every cell-0 assignment is unconditional, so these must be **source edits**; setting
environment variables outside the notebook is overwritten.

**Exact budget, comments included**, which is what `scripts/build_exp065_pruning_sweep.py` asserts:
**4 lines removed, 21 added** — (a) 1/1, (b) 1/1, (c) 2 removed for 5 added (a comment plus four name
lines), (d) 0/6 (a blank, 3 comments, 2 assertions), (e) 0/8 (a blank, 3 comments, 4 code lines). An
earlier draft of this section said "4 changed, 8 added", which counted only the code lines; the build
gate now matches this document exactly and fails on any other delta.

### 4.2 The auto-attach guard

Cell 0 line 178 is
`if FROZEN_PRESET_OVERRIDES is None and not os.environ.get("BIOHUB_FROZEN_PRESET_JSON","").strip():`
— the **empty string enables** a glob of `/kaggle/input/*/ppsweep_selected.json`, and a valid hit is
loaded and applied to the base repair pass. Line 202 does the same for `BIOHUB_VAL_PRED_CACHE_DIR` via
`*/cache_key.txt`. v1 asserted the opposite. Setting a non-existent path is **not** a fix — line 215
would `read_text()` and raise. Two defences:

1. **Pre-launch mount audit** (run; zero cost). Top-level files, which is all the non-recursive glob
   sees: `biohub-deepcenter-unet3d-center-prior-v1` → `ARTIFACT_MANIFEST.json`, `README.md`;
   `biohub-temporal-unet3d-seed314159-v1` and `biohub-tracking-support-pack-50ep-v1` → `name`,
   `ARTIFACT_MANIFEST.json`, `README.md`, 3 requirements/command text files;
   `biohub-v1284-head-s075` → `v1284_head.pt`. **No `ppsweep_selected.json`, no `cache_key.txt`.**
   Re-run before each launch — a dataset re-version could change it. ⚠ The audit covers the four
   mounted datasets and **not** the competition mount, which the glob can also reach; defence 2 is
   what covers that.
2. **Fail-closed runtime assertions**, change (d), placed after the preset block at cell 0 line 228
   and therefore **after loading but before any application to inference** (cell 5 line 2872):

```python
assert not _V9_AUTO_SET_ENV, f"exp_065: preset/cache auto-attach fired: {_V9_AUTO_SET_ENV}"
assert FROZEN_PRESET_OVERRIDES is None, "exp_065: a frozen preset was loaded; the base pass is not the parent"
```

The audit is evidence; the assertion is the guarantee.

### 4.3 Preserving the control

`write_test_submission(tag)` (cell 5 line 2717) always opens `SUBMISSION_PATH` with `"w"` at line
2733; `tag` only labels statistics. Cell 10 rewrites the same path after selection, so **after a
successful sweep the base artifact no longer exists**. Change (e), immediately after the try/finally
at cell 5 lines 2875–2880, whose `finally` only restores globals:

```python
import shutil as _x65_shutil
_X65_BASE_SNAPSHOT = WORKING_DIR / "submission_base.csv"
_x65_shutil.copy2(SUBMISSION_PATH, _X65_BASE_SNAPSHOT)
print(f"exp_065: base submission snapshotted to {_X65_BASE_SNAPSHOT}", flush=True)
```

`WORKING_DIR` resolves to `/kaggle/working`, so the snapshot is retrievable via
`kaggle kernels output`. Gate 1 hashes `submission_base.csv`, never `submission.csv`.

v1 also cited amanatar's crash as evidence that a mid-run failure preserves the control. **It is
not** — their `AttributeError` fired *after* selection and the rewrite, so the artifact recovered from
them is the rewritten `dcsd015` output. The snapshot is the only thing that makes the control survive.

### 4.4 Run 1 — control and measurement. Zero submissions.

**Sweep scope: the 15 eligible candidates, not all 41.** Round 2's cost finding is the reason, and it
also removes the objection that ineligible rows broaden runtime and invite post-hoc reasoning.
Re-costed from the `seconds` column (14 configs, sum 4,652 s, median **324.83 s**, min 316.77, max
386.26), so their fixed pipeline + validator cost is `7000 − 14 × 324.83 ≈ 2,452 s`:

| scope | configs | estimate |
|---|---|---|
| **15 eligible + base** | 16 | **7,650 s ≈ 2.12 h** |
| 15 + base + a generated combination | 17 | 7,974 s ≈ 2.22 h |
| ~~all 41 + base (v2's plan)~~ | 42 | ~~16,095 s ≈ 4.47 h~~ — exceeded v2's own reservation |

**These are estimates from one run's timings, not guaranteed durations**, which is why change (b)
lowers `SWEEP_DEADLINE_S` to **12,600 s (3.5 h)**. Cell 10 lines 145–148 check it **between
candidates** and `break`, keeping partial results and shipping the base configuration — so the run
degrades instead of overrunning. A truncated table then hits the analysis script's
missing-candidate check and **selection is refused** (§8), which is the intended fail-closed
behaviour rather than a silent partial selection.

Other settings: validator on, prefix guard **on**, every v5 lever at its `0 = off` default, the rest
of the v9 deadline ladder **unmodified**.

Delivers `submission_base.csv` + sha (Gate 1); `ppsweep_results.csv` and `validator_results.csv` over
16–17 configurations × 8 stems (Gate 2); `ppsweep_selected.json`; the full log.

⚠ Run 1's own final `submission.csv` is rewritten by **their** guard. It is not our arm and must not
be submitted.

### 4.5 Run 2 — the bet. One submission, only if Gate 2 selects.

Changes (a), (d), (e) as above, **plus** cell 0 line 67 `VALIDATOR_ENABLE` `"1"` → `"0"`, plus the
selected candidate's keys. The per-candidate budget, since a key already at its default changes no
line (B5):

| candidate | override keys | cell-0 lines changed | note |
|---|---|---|---|
| `ep010` / `ep015` / `ep020` | 1 | 1 | |
| `leaf030` / `leaf040` | 1 | 1 | |
| `cx03` / `cx06` / `cx10` | 1 | 1 | |
| `seg030L3` / `seg035L4` | 2 | 2 | |
| **`seg040L6`** | 2 | **1** | `SEG_PRUNE_MAX_LEN=6` is already the cell 0 line 110 default |
| `ep_cx` | 2 | 2 | |
| `leaf_seg` / `seg_cx` | 3 | 3 | |
| `prune_pack` | 5 | 5 | |

So Run 2 is `3 + k` changed and 6 added, where `k` is that row's value. Deterministic: no validator,
no sweep, no runtime re-selection. ~0.3 GPU h.

## 5. Risks

**5.1 What Gate 1 proves.** Byte equality on the four visible movies establishes that *those output
bytes* match under *that execution*. Not general inertness of the added paths, and not hidden-rerun
equivalence. Accepted as the strongest available evidence, not as proof. §3.1 and this section now
say the same thing.

**5.2 The governor is not a hard wall.** `WALL_BUDGET_S` is **reporting-only**, the per-dataset repair
cap is **disabled** (`0`), and deadline checks happen **between** candidates, so one long candidate can
overrun. Mitigations: change (b) gives the sweep a 3.5 h enforced bound; the rest of the ladder is
unmodified; **Run 1 is never submitted**, so an overrun there costs GPU hours, not a slot; and Run 2,
the only arm we would submit, runs no validator and no sweep. Run 2 is still not runtime-identical to
the parent — it applies the selected pruning, carries the snapshot, and repair timing is
time-dependent.

**5.3 Selection overfitting.** Choosing the best of 15 on 8 movies is optimistic. The 36 subsets are
**dependent** and are **not** independent confirmation data. Gate 2 is a fragility screen, not evidence
of transfer.

**5.4 Public-LB overfitting against an unrevealed private score.** `privateScore` is empty on all 30
of our submissions. At most **one** slot is spent, and only after held-out corroboration.

**5.5 Provenance.** The six SHA256 manifest entries match, which establishes **archived byte integrity
only** — not which source or environment produced them, nor whether V1284 training excluded these
movies. The validator's stem selector explicitly prefers train movies containing divisions. The
evidence comes from a stranger's crashed kernel; Gate 1 and Run 1's own table are what convert it into
evidence about *our* pipeline.

**5.6 Third-party weights.** The vehicle mounts `anvithpothula/biohub-v1284-head-s075`, exactly as
exp_064 did — an accepted, already-submitted risk.

**5.7 Proxy→LB calibration is one point.** Base proxy 0.95549 vs LB 0.953, offset −0.0025. No
predicted score appears in this proposal's success criteria.

## 6. Local gates — zero GPU, executable before launch

Applicability is stated per run, since v2 left it ambiguous (B5).

| gate | Run 1 | Run 2 |
|---|---|---|
| 1. vehicle sha256 == `371fc1f9f4f2…`; dataset list == exp_064's four | ✓ | ✓ |
| 2. authored-change diff == the exact budget (§4.1 for Run 1; §4.5 for the selected candidate) | ✓ | ✓ |
| 3. all 89 x138 keys at x138's values **except** `VALIDATOR_ENABLE`; `REPAIR_DEADLINE_S == 27000` | ✓ | ✓ |
| 4. the 24 omitted x138 lines are exactly the enumerated set | ✓ | ✓ |
| 5. mount audit: no `ppsweep_selected.json`, no `cache_key.txt` at any mount's top level | ✓ | ✓ |
| 6. `_V7_FAST_TIER` == the 15 eligible names; `FAST_TIER == "1"`; `SWEEP_DEADLINE_S == "12600"` | ✓ | n/a (no sweep) |
| 7. every v5 lever at its off default | ✓ | only the unselected ones |
| 8. `VALIDATOR_ENABLE == "1"` | ✓ | `"0"` |
| 9. `analyze_sweep_table.py` runs clean on the archived table (it **raises** otherwise) | ✓ | n/a |
| 10. snapshot smoke per the standing admission requirement | ✓ | ✓ |

No local proxy gate is claimed: the pipeline cannot run off-Kaggle.

## 7. Budget

| item | GPU h |
|---|---|
| Run 1 (validator + 15-candidate sweep) | ~2.2 estimated; enforced sweep bound 3.5; **reserve 4.0** |
| Run 2 (deterministic, no validator, no sweep) | ~0.3 |
| **total reserved** | **4.3 of 19.741056** |

Submissions: **at most 1**, from Run 2, separately authorized. LB cap 5/NY-day, 0 used on 09-25. Two
serial runs fit inside the ~4 days to 2026-09-29 23:59 with wide margin.

## 8. Pre-registered decision rules

**Gate 1 — H_control.** `sha256(submission_base.csv)` must equal `d52a5da2`. Fail → **STOP**: no
Run 2, no submission; report the diff.

**Gate 2 — lever selection.** Eligible: the **15-member pruning family**, which is also exactly what
Run 1 sweeps. Rank by test-reweighted aggregate `adjusted_edge_jaccard` delta. A candidate qualifies
only if **all** hold:

1. aggregate delta **≥ +0.0015**;
2. **at most 3 of the 36** test-shaped subsets **strictly negative** (subsets that are exactly
   unchanged are not losses — the B1 bug);
3. no embryo prefix regressing by more than **0.001** (the author's guard, correctly implemented).

Highest-ranked qualifier → Run 2. **Nothing qualifies → submit nothing, report H_null.**

**The MARGINAL band is an exception, not an outcome.** A candidate meeting (1) and (3) with **4–9**
strictly-negative subsets has **not passed Gate 2**. It is reported to the user with its full subset
distribution, and any decision to run it would be a **documented exception to this record**, not a
Gate 2 PASS. More than 9 → rejected outright.

**Refusal on a partial table.** If Run 1's sweep was truncated by change (b)'s deadline, the analysis
script's missing-candidate check sets `SELECTION_ALLOWED = False` and refuses to select. Missing
candidates are **unmeasured, not rejected**.

Executable and fail-closed:
`docs/research/public_notebook_archive/amanatar_v9_sweep_telemetry/analyze_sweep_table.py`
implements exactly this, `raise`s if the proxy identity or the prefix-guard reproduction fails, and on
today's archive prints:

```
[0] INCOMPLETE MEASUREMENT: 13 of 15 eligible pruning candidates are absent ... Selection is REFUSED.
[1] proxy identity, 14 rows, residual 0.000e+00  CONFIRMED
[2] prefix guard vs the notebook's own column, residual 0.000e+00  MATCH
ep015    +0.00236  neg 10  =0  0  worst -0.00584  prefix -0.0084939  eligible  fails 2+3
leaf040  +0.00018  neg 16  =0  0  worst -0.00075  prefix -0.0003721  eligible  fails 1+2
Selection REFUSED: the eligible pruning family was not fully measured.
```

**On the construction of the thresholds:** v2 claimed that rejecting `ep015` showed the rule was not
reverse-engineered. **That claim is withdrawn** — it is evidence about one candidate, not about how
the rule was built. The honest statement is that the thresholds are recorded here, in a versioned
document, before Run 1 exists, and the script that applies them is committed alongside.

**Gate 3 — LB read**, against 0.953: **≥ 0.955** adopt · **0.954** small real gain, adopt and stop ·
**0.953** null, keep the parent · **≤ 0.952** revert to exp_064 immediately.

**Rollback.** exp_064 (0.953, 56535761) and `repro_059` (0.947, 56313491) untouched.

## 9. Governance

CONSENSUS authorizes **nothing**. Remaining: third Codex challenge → revision if needed → explicit
CONSENSUS → build → fresh experiment-specific Codex admission PASS → snapshot smoke → budget
reservation → **one user-authorized launch of Run 1** → evaluation against §8 → **separately
authorized** Run 2 → **separately authorized** submission. Claude Code does not review its own work.

## 10. What would change my mind

- **Gate 1 fails.** The vehicle does not reproduce the parent. Cheapest fallback is the demoted
  `readmit-v1` A/B on x138 itself (~0.26 GPU h), expected effect unquantified.
- **Run 1's base pass diverges from amanatar's table on the 8 shared stems.** Their numbers came from
  a crashed run in an environment we cannot inspect. Gate 2 already judges only our numbers, but §2's
  mechanism reasoning would need re-deriving.
- **The `cx*` family is inert in our table.** Then §2's surviving argument is wrong, the family reduces
  to `ep*`/`seg*`/`leaf*`, and if none clears Gate 2 → H_null.
- **A reviewer shows the 37.329/62.671 reweighting is the wrong model.** Every aggregate moves; an
  alternative weighting must go through the same script before any selection.
- **A reviewer shows max-3-of-36 is unachievable in principle** rather than merely strict. It is a
  risk-tolerance choice, not a calibrated error rate, and a broadly positive candidate can pass all 36.

## Appendix — deliberately out of scope

- **Any division arm.** `div_tp = 3`/12, `div_fn = 9` across all 14 measured configurations (§3.4).
- **A `tight60` arm.** Not because the lever is dead — that claim is **withdrawn** — but because there
  is **no evidence in either direction**. Run 1 does not change this; the `tight55` candidate sets the
  value the base already has, and it is not in the 15 swept.
- **`vel*` and `rescue*` arms.** Genuine changes, measured bit-identical to base.
- **The other 26 declared candidates.** Measured cost ~2.3 GPU h for rows Gate 2 cannot select from,
  and their interpretation would have to stay separate from this experiment anyway. If a later
  experiment wants them, that is its own record.
- **An exact per-movie count target.** The test zarr carries no node-count hint (§2).
- **Raising exp_062's β or porting mutual-best.** k2 scored 0.944; the arc is closed.
- **Training or fine-tuning.** Four days, an unrevealed private score, no held-out training protocol.
