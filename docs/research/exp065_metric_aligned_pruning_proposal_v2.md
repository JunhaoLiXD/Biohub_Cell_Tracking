> **SUPERSEDED 2026-09-25 by `exp065_metric_aligned_pruning_proposal_v3.md`.**
> Codex returned **REVISE** on this version (`exp065_codex_challenge_v2.md`): round-1 findings F1, F2
> and F4 fixed, F3/F5/F6/F7 partially fixed, and **five new blocking `[CORRECTNESS]` findings**, all
> independently verified and all genuine. Kept for provenance. **Do not act on anything below.** In
> particular this version: counts unchanged subsets as losses (so `dcsd015` reads 18/36 instead of
> 9 negative + 9 unchanged, and `tight55` reads 36/36 instead of 0 + 36) and reports +0.00319 as a
> median where the true median is +0.002796470; budgets Run 1 at ~3 h and reserves 4.0 h when
> sweeping all 41 costs ~4.5 h; claims corrections propagated "everywhere" when several records still
> asserted the withdrawn claims; specifies an analysis gate that printed instead of failing closed;
> and states a Run 2 line budget that is wrong for `seg040L6`.

---

# exp_065 — Metric-aligned pruning on the 0.953 parent — v2

Status: **v2 — awaiting the second Codex challenge.** No CONSENSUS. No implementation, no launch, no
leaderboard submission is authorized by this document.
Author: Claude Code, 2026-09-25.
Parent: `exp_064_x138_verbatim_repro` — Public LB **0.953**, submission 56535761, output sha
`d52a5da2`.
Lineage: v1 → Codex **REVISE** (`docs/research/exp065_codex_challenge_v1.md`, **7 blocking
`[CORRECTNESS]` findings + 5 non-blocking**) → v2.

**All seven blocking findings were independently re-derived from the notebook sources and all seven
were genuine. Nothing in the review was rejected.** Two of them corrected claims that had already
propagated into `STATE.json`, `HANDOUT.md`, the recon document and the project's auto-memory; those
records were corrected in the same pass. The five non-blocking findings are accepted as written and
are carried into the design here rather than noted and ignored.

---

## What v2 fixes

| # | v1 claim | status | v2 |
|---|---|---|---|
| 1 | `FROZEN_PRESET_JSON=""` and `VAL_PRED_CACHE_DIR=""` leave those branches dead | **BACKWARDS** — cell 0 line 178 globs `/kaggle/input/*/ppsweep_selected.json` *when the string is empty* and applies a hit before the base write | §4.2: mount audit + a fail-closed runtime assertion |
| 2 | Run 1 delivers the base control artifact | **FALSE** — `write_test_submission(tag)` always opens the same `SUBMISSION_PATH` with `"w"` (cell 5 line 2733); `tag` is a statistics label; cell 10 rewrites it after selection | §4.3: an explicit 4-line snapshot; Gate 1 is otherwise undeliverable |
| 3 | Run 1/Run 2 configurable "at environment level"; `REPAIR_DEADLINE_S` differs 27000 → 30600 | **FALSE twice** — every cell-0 assignment is unconditional, so external env is overwritten; and cell 0 line 69 is already `27000`, identical to x138. The 30600 is cell 10 line 252, inside the pass-2 rewrite | §4.1 specifies cell-0 edits with an exact authored-line budget; the fabricated deadline difference is **withdrawn** |
| 4 | `analyze_sweep_table.py` implements the author's prefix guard | **FALSE** — the notebook uses **the candidate's own** weights and a single Jaccard over **pooled** div tp/fp/fn (cell 9 lines 121–134); the script used base weights and averaged per-movie division Jaccards | script rewritten and now **validated to residual 0.0** against the `prefix_proxy` column the notebook itself wrote |
| 5 | `MOTION_RELINK_TIGHT_UM` is bit-for-bit inert | **UNSUPPORTED** — x138 cell 0 line 76 and the vehicle cell 0 line 71 both already set **5.5**, and the `tight55` candidate sets **5.5**. The sweep never varied the variable | claim **withdrawn** everywhere; §3.4 and the appendix restate what survives |
| 6 | "over-prediction is penalised, under-prediction is not"; base ratio 0.752 on `44b6_12dfb391`; `cx*` repairs `ep015`'s failure mode | **IMPRECISE, WRONG, UNSUPPORTED** — the multiplier is `max(0, J·(1 − 0.1·(t_pred−t_true)/t_true))`, so under-prediction is actively **rewarded**; base is **0.76263** (0.752 was ep015's); and `prune_to_node_count_target` budgets against its own confident core, **not** ground-truth excess | §2 rewritten; the `cx*` argument is downgraded to what it actually supports |
| 7 | 41 candidates, 27 unmeasured | **WRONG** — `PP_CANDIDATES` holds **41 excluding base**; measured is base + 12 declared + 1 generated combination, so **29** declared candidates are unmeasured and a full run yields **42** configurations (43 with the generated combination) | arithmetic corrected throughout |

Non-blocking findings carried in: the 36 test-shaped subsets replace the globally-renormalised
leave-one-out as the robustness criterion (§3.3, `[DESIGN] 1`); "test-reweighted" is labelled a
modelling assumption (§3.2, `[DESIGN] 2`); Gate 1's byte equality is scoped to what it actually
proves (§5.1, `[RISK] 3`); the division result is restated as evidence about 14 configurations rather
than proof about every intervention (§3.4, `[RISK] 4`); and Gate 2 selection is narrowed to the
pruning family while measurement stays broad (§8, `[SCOPE] 5`).

**The headline is unchanged and is now supported three independent ways instead of one:** the lever
that motivated this experiment does not qualify, and **on current evidence nothing does.**

---

## 0. Motivation

0.953, rank 361 of 3899. **0.953 is a 249-team plateau spanning ranks ~200–420** — the
public-notebook ceiling. One thousandth of a point is worth roughly 190 ranks (0.954 → ~171,
0.955 → ~121, 0.956 → ~91). No public notebook scores above the plateau; every author at 0.956+ with
published work reached it over 40–206 unpublished submissions. Copying is exhausted. Anything further
has to be measured.

The 2026-09-25 recon harvested a real 14-config × 8-held-out-stem table at zero cost, and it gave us
the metric, disqualified the only pruning candidate with a score, and — after the challenge — turned
out to have told us **less** than v1 claimed about which knobs are dead.

## 1. Parent, and the vehicle problem

Every lever worth testing is absent from our parent's source: `grep` of `biohub-x138.ipynb` returns
**0 hits** for `OUTPUT_MIN_EDGE_PROB`, `LEAF_PRUNE_MIN_EDGE_PROB`, `SEG_PRUNE_MIN_PROB`,
`COUNT_EXCESS_FRAC`, `PPSWEEP_EXTENDED`, `PPSWEEP_PREFIX_GUARD`. They exist only in
`amanatar/optimized-biohub-max-score` (sha
`371fc1f9f4f20f692e0586616ff7d3eab4621d167f6c78516d3243c5a4fddfab`), which adds **862 lines** over
x138 and shares x138's 89 `BIOHUB_*` keys and four datasets exactly.

**There is exactly one intended configuration difference** — `BIOHUB_VALIDATOR_ENABLE`, `0` in x138
and `1` in the vehicle, which is the lever Run 1 wants on anyway. v1 also reported a
`REPAIR_DEADLINE_S` difference; **that was my error** (§"What v2 fixes" #3) and there is nothing to
reconcile.

The 24 x138 lines the vehicle omits: 4 docstring, 2 label assignments, `write_test_submission("base")`
(re-emitted inside a try/finally), 1 reflowed list literal, 4 `os.environ` lines re-emitted with
different comments (of which only `VALIDATOR_ENABLE` differs in value), and **12 inside the
validator/sweep selection block** the author rewrote.

So: using these levers means running a different notebook, and the first thing this experiment must
establish is that the different notebook **is** the parent when its levers are off. **v1 argued that
from a static reading and got a central premise backwards.** v2 does not argue it at all — §4 makes it
a measured gate with a fail-closed assertion behind it.

## 2. The intervention, and the mechanism restated correctly

**Vehicle:** `amanatar/optimized-biohub-max-score` with the authored changes itemised in §4.1.

**Lever family:** metric-aligned pruning — `OUTPUT_MIN_EDGE_PROB` (L1 weak edges),
`SEG_PRUNE_MIN_PROB`/`SEG_PRUNE_MAX_LEN` (L2 weak pendant segments), `LEAF_PRUNE_MIN_EDGE_PROB`
(weak leaves), `COUNT_EXCESS_FRAC` (L5 core-relative node budget), and the published stacks
`leaf_seg`, `prune_pack`, `ep_cx`, `seg_cx`. **15 candidates.**

**The count adjustment, stated exactly.** Cell 8 line 77:

```python
return max(0.0, jaccard * (1.0 - a * (t_pred - t_true) / t_true))      # a = 0.1
```

For `t_pred < t_true` the multiplier **exceeds 1**: under-prediction is actively **rewarded**, not
merely unpenalised. v1's phrasing was loose and the difference matters for the next paragraph.
Empirically the free half holds — for `ep015` the multiplier improves on **8 of 8** stems
(+0.0010 … +0.0073) — so all risk sits in raw `edge_jaccard`.

**`COUNT_EXCESS_FRAC`, with v1's overclaim removed.** `prune_to_node_count_target` needs no ground
truth: it pins a *core* (frame 0, final frame, incident to an edge with `edge_prob is None` — gap /
safe-div / repair additions — or `>= CORE_EDGE_PROB` 0.60), budgets `core_count × (1 + frac)`, and
drops the weakest non-core, non-fork-parent nodes in one pass, no cascade.

v1 claimed this repairs `ep015`'s failure mode. **It does not, and Codex was right to reject that.**
The budget is relative to the graph's own confident core, *not* to ground-truth excess: 800 predicted
nodes with a 500-node core at `frac = 0.06` gives a target of 530 whether the truth is 400 or 1,000.
It offers **no under-prediction protection**, and `44b6_12dfb391` — where `ep015` lost most — already
under-predicts at **0.76263 × t_true** (v1 quoted 0.752, which is `ep015`'s ratio, not base's).

What survives is narrower and still worth measuring: the `cx*` budget is **proportional to each
movie's own confident structure** rather than a single global probability cut, so it cannot remove
nodes from a graph that is mostly core, and it removes weak nodes preferentially. Across hidden-test
densities spanning 62.2 → 697.5 nodes/frame, a structure-relative instrument is a different bet from
a fixed threshold. **That is a hypothesis with no score behind it.** Its whole justification is that
it is cheap to measure in the same run.

**Closed door, recorded so it is not re-proposed:** an exact per-movie count target is unavailable.
Both notebooks read `estimated_number_of_nodes` only from the TRAIN ground-truth path inside the
validator. `test/44b6_0113de3b.zarr/zarr.json` (1,279 bytes, pulled from the competition) carries only
`multiscales` and `image_statistics.quantiles`; no node-count hint, no `.zattrs` (404).

## 3. Hypotheses

### 3.1 H_control — the gate everything depends on

> With the vehicle configured as §4 specifies, its **snapshotted base** `submission.csv` is
> byte-identical to exp_064's output sha `d52a5da2`.

Binary, settled by one sha256. Pass → the vehicle is the parent and inherits 0.953 with no submission
spent. Fail → **stop** (§8 Gate 1).

### 3.2 H_lever

> Some member of the 15-candidate pruning family improves the test-reweighted held-out aggregate by a
> margin that survives the test-shaped subset analysis and the author's own prefix guard.

**"Test-reweighted" is a modelling assumption, not a recovered official weighting** (`[DESIGN] 2`).
The hidden test set is two `44b6` and two `6bba` movies at 45,250 / 75,969 nodes = **37.329 % /
62.671 %**, but those are *our predicted output-node counts* from exp_064's `metrics.json`, whereas
the validator's own weights are edge-confusion denominators that can shift with the candidate. The
two are different quantities. Observed test densities also say nothing about private-test composition.
Every reweighted figure below should be read as "under this assumption", and §10 says what would
change it.

### 3.3 `ep015` fails, now three independent ways

v1 rested on a globally-renormalised leave-one-out. Codex correctly noted that renormalising after a
deletion **changes the prefix mixture**, and that the directly relevant analysis is the **36 subsets
containing two movies from each prefix** — the actual shape of the hidden test set — with the mixture
held fixed. Implemented, and it is far more damning:

| evidence | `ep015` |
|---|---|
| test-reweighted aggregate, all 8 stems | **+0.00236** |
| concentration | `6bba_09961292` holds **60.6 %** of the gross positive |
| **author's own prefix guard** | 44b6 regresses **−0.0084939**, against their limit of −0.001 → **rejected** |
| **36 test-shaped subsets** | **10 negative**, min **−0.00584**, median +0.00319, max +0.01371 |

Under the real 2 + 2 test shape, **28 % of draws lose.** No other measured candidate is close:
`leaf040` +0.00018 with 16/36 negative, `dcsd015` +0.00014 with 18/36.

**Conclusion: H_lever has no qualifying candidate on current evidence.** Of the 41 declared candidates
(excluding base), **29 have never been scored**, including all three `cx*` arms, `ep010`, `ep020`, the
three `seg*` arms and all four pruning stacks. Measuring them is this experiment's primary product.

### 3.4 What the harvested table does and does not close

**Withdrawn:** that `MOTION_RELINK_TIGHT_UM` is inert. Both notebooks already set 5.5 and the
candidate sets 5.5 — the variable was never varied, so its identical row is a self-consistency check.
The `tight_um` question `lb_mining_2026-09-25.md` left open is **still open**, and this table supports
a `tight60` arm in neither direction.

**Survives:** `MOTION_RELINK_VELOCITY_WEIGHT` (default 0.5, `vel075` sets 0.75) and
`SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB` (0.88, `rescue085` sets 0.85) are genuine changes that are
bit-identical to base on all 8 stems, every column.

**Survives, with Codex's qualification (`[RISK] 4`):** no post-process knob in this table moves
division recall — `div_tp = 3`/12 and `div_fn = 9` for all 14 configurations, only `div_fp` moves.
That is strong evidence about **these 14 interventions**, not proof that division recall is
unreachable by every untested one. It remains sufficient reason not to open a third division arc with
four days left, which is a scheduling judgement rather than a theorem.

### 3.5 H_null

Nothing passes §8 Gate 2. We submit nothing, keep 0.953, and hold a measured map of the pruning space
for ~3 GPU h and zero submissions. **An acceptable outcome**, and the design costs no leaderboard slot
to reach it.

## 4. Design — two runs, at most one submission

### 4.1 Authored changes, itemised and budgeted

v1 claimed "exactly one authored line". That was false once findings 2 and 3 landed. The real budget,
which §6 gate 2 asserts exactly:

**Run 1 — 2 lines changed, 6 lines added:**

| # | location | change | why |
|---|---|---|---|
| a | cell 11 line 44 | `_v6env = os.environ.get` → `_v6env = os.environ` | their run died here; the eight `_v6env.get(...)` call sites on lines 44–50 are `print` arguments only, and `submission.csv` is written earlier. Under papermill the unfixed line fails the notebook |
| b | cell 0 line 135 | `BIOHUB_PPSWEEP_FAST_TIER` `"1"` → `"0"` | sweep all 41 candidates instead of the 12-item tier. Must be a cell-0 edit: the assignment is unconditional |
| c | cell 0 after line 228 | **+2** assertion lines (§4.2) | fail closed if the preset/cache auto-attach fired |
| d | cell 5 after line 2880 | **+4** snapshot lines (§4.3) | preserve the base artifact before the sweep overwrites it |

`BIOHUB_VALIDATOR_ENABLE` needs **no** edit — the vehicle already ships `"1"`.

**Run 2 — 3 lines changed (+1 per extra lever key), 6 lines added:** (a), (c), (d) as above, plus
cell 0 line 67 `VALIDATOR_ENABLE` `"1"` → `"0"`, plus one line per key of the selected candidate set
to its winning value. Note several eligible candidates (`seg*`, the stacks) change **more than one
key**; v1's phrase "a single winning override" was ill-defined. §8 Gate 2 defines it as *one
candidate from the dict*, applied exactly as the dict declares it, however many keys that is.

### 4.2 The auto-attach guard — the defect this section exists to close

Cell 0 line 178 is `if FROZEN_PRESET_OVERRIDES is None and not os.environ.get("BIOHUB_FROZEN_PRESET_JSON","").strip():`
— the **empty string enables** a glob of `/kaggle/input/*/ppsweep_selected.json`; a valid hit is
loaded and its overrides applied to the base repair pass. Line 202 does the same for
`BIOHUB_VAL_PRED_CACHE_DIR` via `*/cache_key.txt`. v1 asserted the opposite.

Setting a non-existent path is **not** a fix: line 215 then calls `.read_text()` and raises. Two
defences instead:

1. **Pre-launch mount audit** (zero cost, already run). Top-level files of the four mounts —
   which is all the glob can see:
   `biohub-deepcenter-unet3d-center-prior-v1` → `ARTIFACT_MANIFEST.json`, `README.md`;
   `biohub-temporal-unet3d-seed314159-v1` and `biohub-tracking-support-pack-50ep-v1` → `name`,
   `ARTIFACT_MANIFEST.json`, `README.md`, 3 requirements/command text files;
   `biohub-v1284-head-s075` → `v1284_head.pt`. **No `ppsweep_selected.json`, no `cache_key.txt`.**
   Re-run this audit before each launch: a dataset re-version could change it.
2. **Fail-closed runtime assertion**, change (c), immediately after the preset block:

```python
assert not _V9_AUTO_SET_ENV, f"exp_065: preset/cache auto-attach fired: {_V9_AUTO_SET_ENV}"
assert FROZEN_PRESET_OVERRIDES is None, "exp_065: a frozen preset was loaded; base pass is not the parent"
```

The audit is evidence; the assertion is the guarantee. This is the fifth-instance failure mode in
reverse — I read a declaration and got its polarity wrong — so it gets an assertion, not a paragraph.

### 4.3 Preserving the control — without this, Gate 1 cannot run

`write_test_submission(tag)` (cell 5 line 2717) always opens `SUBMISSION_PATH` with `"w"` at line
2733; `tag` only labels statistics. Cell 10 rewrites the same path with the selected configuration.
**After a successful sweep the base artifact no longer exists.** Change (d), immediately after the
try/finally at cell 5 lines 2875–2880:

```python
import shutil as _x65_shutil
_X65_BASE_SNAPSHOT = WORKING_DIR / "submission_base.csv"
_x65_shutil.copy2(SUBMISSION_PATH, _X65_BASE_SNAPSHOT)
print(f"exp_065: base submission snapshotted to {_X65_BASE_SNAPSHOT}", flush=True)
```

Gate 1 hashes `submission_base.csv`, never `submission.csv`.

v1 also cited amanatar's crash as evidence that a mid-run failure preserves the control. **It is not:**
their `AttributeError` fired *after* selection and the rewrite, so the artifact we recovered from them
is the rewritten `dcsd015` output. The snapshot is the only thing that makes the control survive, and
it also makes it survive a crash at any later point.

### 4.4 Run 1 — control and measurement. Zero submissions.

Configuration after the §4.1 edits: validator on, all 41 candidates swept, prefix guard **on**, every
v5 lever at its `0 = off` default, the v9 deadline ladder **unmodified**.

Delivers `submission_base.csv` + sha (Gate 1); `ppsweep_results.csv` and `validator_results.csv` over
**42 configurations** (base + 41, possibly 43 with the generated combination) × 8 stems (Gate 2);
`ppsweep_selected.json`; the full log.

⚠ Run 1's own final `submission.csv` is rewritten by **their** guard. It is not our arm and must not
be submitted.

### 4.5 Run 2 — the bet. One submission, only if Gate 2 selects.

Validator off, the winning candidate's keys set statically. Deterministic: no validator, no sweep, no
runtime re-selection — one candidate against a byte-verified control. ~0.3 GPU h.

## 5. Risks

**5.1 What Gate 1 does and does not prove (`[RISK] 3`).** Byte equality on the four visible movies
establishes that *those output bytes* match under *that execution*. It does **not** prove every added
path inert in general, and it does **not** establish hidden-rerun equivalence. Accepted as the
strongest available evidence, not as proof. The residual risk is concentrated in paths that are
time-gated rather than flag-gated, which is 5.2.

**5.2 The governor is not a hard wall (`[RISK] 3`).** `WALL_BUDGET_S` is **reporting-only**, the
per-dataset repair cap is **disabled** (`0`), and the sweep checks deadlines **between** candidates —
so a single long candidate can overrun. Our x138-class run took 932 s visible and 41 candidates
extrapolates to ~3 h *there*; if the hidden rerun's set is materially larger this is real exposure.
Mitigations: keep the ladder unmodified; and note that **Run 2, the only arm we would submit, runs no
validator and no sweep at all**, so the submitted arm carries essentially the parent's runtime profile.
Run 1 is not submitted, so an overrun there costs GPU hours, not a slot.

**5.3 Selection overfitting.** Choosing the best of 15 on 8 movies is optimistic even with the gate;
the 36 subsets are **not** independent confirmation data (`[DESIGN] 1`). Gate 2 is therefore a
fragility screen, not evidence of transfer, and it is deliberately strict enough that the largest
measured effect fails it.

**5.4 Public-LB overfitting against an unrevealed private score.** `privateScore` is empty on all 30
of our submissions. This proposal spends **at most one** slot and requires held-out corroboration
first.

**5.5 Provenance (`[RISK] 4`).** The six SHA256 manifest entries match, which establishes **archived
byte integrity only** — not which source or environment produced them, and not whether V1284 training
excluded these movies. The validator's stem selector explicitly prefers train movies containing
divisions. The evidence comes from a stranger's crashed kernel; Gate 1 and Run 1's own table are what
convert it into evidence about *our* pipeline, and §10 says what a mismatch would mean.

**5.6 Third-party weights.** The vehicle mounts `anvithpothula/biohub-v1284-head-s075`, exactly as
exp_064 did — an accepted, already-submitted risk, not a new one.

**5.7 Proxy→LB calibration is one point.** Base proxy 0.95549 against LB 0.953, offset −0.0025. No
predicted score appears in this proposal's success criteria and none should appear in its report.

## 6. Local gates — zero GPU, all executable before launch

1. **Vehicle integrity:** sha256 == `371fc1f9f4f2…`; dataset list == exp_064's four exactly.
2. **Authored-change gate:** diff vehicle-as-run against the archived original and assert the exact
   §4.1 budget — Run 1: 2 changed lines at cell 11:44 and cell 0:135, 6 added lines at cell 0:228 and
   cell 5:2880. Any other delta fails the gate.
3. **Config gate:** assert all 89 x138 keys present at x138's values **except** `VALIDATOR_ENABLE`,
   the one intended difference; assert `REPAIR_DEADLINE_S == 27000` (it already is — this asserts, it
   does not change); assert every v5 lever at its off default; assert the v9 deadline ladder
   byte-unmodified.
4. **Omission gate:** assert the 24 x138 lines the vehicle omits are exactly the enumerated set, so a
   re-pull cannot silently drop more.
5. **Mount audit:** no `ppsweep_selected.json` and no `cache_key.txt` at the top level of any mounted
   dataset (§4.2).
6. **Candidate-dict gate:** assert `len(PP_CANDIDATES) == 41` and `FAST_TIER == "0"`, so the sweep
   cannot silently run 12. *(Fourth-instance failure mode; it gets an assertion.)*
7. **Analysis gate:** `analyze_sweep_table.py` must still reproduce the notebook's `prefix_proxy`
   column to residual 0.0 on the archived table before it is used to judge Run 1's table.
8. **Snapshot smoke** per the standing admission requirement.

No local proxy gate is claimed: we cannot run the pipeline off-Kaggle.

## 7. Budget

| item | GPU h |
|---|---|
| Run 1 (validator + 41-candidate sweep) | ~3.0 extrapolated from their 1.94 h / 14 configs; **reserve 4.0** |
| Run 2 (deterministic, no validator, no sweep) | ~0.3 |
| **total reserved** | **4.3 of 19.741056** |

Submissions: **at most 1**, from Run 2 only, separately authorized. LB cap 5/NY-day, 0 used on 09-25.
Two serial runs fit inside the ~4 days to 2026-09-29 23:59 with wide margin.

## 8. Pre-registered decision rules

**Gate 1 — H_control.** `sha256(submission_base.csv)` **must equal** `d52a5da2`.
Pass → proceed. Fail → **STOP**: no Run 2, no submission; report the diff and reconsider whether this
family is reachable at all.

**Gate 2 — lever selection.** Eligible: the **15-member pruning family** only (`[SCOPE] 5`). The run
measures all 41 because information is cheap; eligibility is narrower than measurement on purpose, so
that candidates from families this proposal declares out of scope cannot win a submission. Rank
eligible candidates by test-reweighted aggregate `adjusted_edge_jaccard` delta. Then:

1. aggregate delta **≥ +0.0015**;
2. **at most 3 of the 36** test-shaped subsets negative;
3. no embryo prefix regressing by more than **0.001** (the author's own guard, correctly implemented).

Highest-ranked candidate satisfying all three → Run 2. A candidate satisfying (1) and (3) with **4–9**
negative subsets is **MARGINAL**: not selected automatically, escalated to the user with its full
subset distribution. More than 9 negative → rejected. Nothing eligible → **submit nothing**, report
H_null.

Executable and calibrated:
`docs/research/public_notebook_archive/amanatar_v9_sweep_telemetry/analyze_sweep_table.py`
(no GPU, network or credentials) implements exactly this and, on the 14 configurations we already
hold, prints:

```
ep015     +0.00236  10/36  worst -0.00584  prefix -0.0084939  eligible  fails 2+3
leaf040   +0.00018  16/36  worst -0.00075  prefix -0.0003721  eligible  fails 1+2
dcsd015   +0.00014  18/36  ...                                not eligible
Gate 2 selects NOTHING on this table -> H_null, no submission.
```

It also confirms `proxy = adjEJ + 0.1·divJ` (residual 0) and the prefix guard against the notebook's
own column (residual 0). **The rule rejects the candidate I would otherwise have picked**, which is
the only evidence that it was not reverse-engineered.

**Gate 3 — LB read**, against the 0.953 parent: **≥ 0.955** adopt · **0.954** small real gain, adopt
and stop · **0.953** null, keep the parent · **≤ 0.952** revert to exp_064 immediately.

**Rollback.** exp_064 (0.953, 56535761) and `repro_059` (0.947, 56313491) are untouched.

## 9. Governance

CONSENSUS on this record authorizes **nothing**. Remaining gates: second Codex challenge → revision if
needed → explicit CONSENSUS → build → fresh experiment-specific Codex admission PASS → snapshot smoke
→ budget reservation → **one user-authorized launch of Run 1** → evaluation against §8 → **separately
authorized** Run 2 → **separately authorized** submission. Claude Code does not review its own work.

## 10. What would change my mind

- **Gate 1 fails.** The vehicle is not the parent. Cheapest honest fallback is the demoted
  `readmit-v1` A/B on x138 itself (~0.26 GPU h), expected effect unquantified.
- **Run 1's base pass diverges from amanatar's published table on the 8 shared stems.** Their numbers
  came from a crashed run in an environment we cannot inspect. A mismatch means the harvested table
  does not describe our pipeline — Gate 2 then judges **our** numbers only, which it already does by
  construction, but §2's mechanism reasoning would need re-deriving from our table.
- **The `cx*` family is inert in our table.** Then §2's surviving argument is wrong too, the pruning
  family reduces to `ep*`/`seg*`/`leaf*`, and if none of those clears Gate 2 → H_null, no submission.
- **A reviewer shows the 37.329/62.671 reweighting is the wrong model.** Every aggregate figure moves.
  §3.2 flags this as an assumption; an alternative weighting should be run through the same script
  before any selection.

## Appendix — deliberately out of scope

- **Any division arm.** `div_tp = 3`/12 and `div_fn = 9` across all 14 measured configurations. Not a
  theorem about every intervention (§3.4), but sufficient with four days left. exp_056 and exp_058
  already died here.
- **A `tight60` arm.** Not because the lever is dead — that claim is **withdrawn** — but because we
  still have **no evidence in either direction** and no measurement of it. Run 1 does not change this:
  the `tight55` candidate sets the value the base already has.
- **`vel*` and `rescue*` arms.** Genuine changes, measured bit-identical to base.
- **An exact per-movie count target.** The test zarr carries no node-count hint (§2).
- **Raising exp_062's β, or porting mutual-best.** k2 scored 0.944; the arc is closed.
- **Training or fine-tuning anything.** Four days, an unrevealed private score, no held-out training
  protocol.
