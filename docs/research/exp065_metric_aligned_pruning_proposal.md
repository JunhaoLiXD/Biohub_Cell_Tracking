> **SUPERSEDED 2026-09-25 by `exp065_metric_aligned_pruning_proposal_v2.md`.**
> Codex returned **REVISE** on this version with seven blocking `[CORRECTNESS]` findings
> (`exp065_codex_challenge_v1.md`); all seven were independently verified and all seven were genuine.
> Kept for provenance only. **Do not act on anything below.** In particular this version states, all
> incorrectly: that empty `FROZEN_PRESET_JSON`/`VAL_PRED_CACHE_DIR` disable those paths (they enable
> auto-detection); that Run 1 delivers a base control artifact (the sweep overwrites it); that the
> runs are configurable at environment level (cell-0 assignments are unconditional); that
> `REPAIR_DEADLINE_S` differs between x138 and the vehicle (it does not, both are 27000); that
> `MOTION_RELINK_TIGHT_UM` is inert (the sweep never varied it); that under-prediction is merely
> unpenalised (it is rewarded); and that 27 candidates are unmeasured (29 are).

---

# exp_065 — Metric-aligned pruning on the 0.953 parent

Status: **v1 — awaiting Codex challenge.** No CONSENSUS. No implementation, no launch, no
leaderboard submission is authorized by this document.
Author: Claude Code, 2026-09-25.
Parent: `exp_064_x138_verbatim_repro` — Public LB **0.953**, submission 56535761, output sha
`d52a5da2`.
Evidence base: `docs/research/lb_recon_2026-09-25_amanatar_sweep.md` and the telemetry archived at
`docs/research/public_notebook_archive/amanatar_v9_sweep_telemetry/`.

**Headline, stated first because it cuts against my own recommendation:** the lever that motivated
this proposal — `OUTPUT_MIN_EDGE_PROB=0.15` — **fails the robustness test I pre-register in §8.**
Its entire aggregate gain rests on one held-out movie out of eight. On current evidence **no
measured candidate qualifies for a submission.** That is precisely why this proposal's primary
deliverable is a *measurement*, not a bet, and why the bet is conditional on a rule fixed in
advance.

---

## 0. Motivation

We are at 0.953, rank 361 of 3899. **0.953 is a 249-team plateau spanning ranks ~200–420** — the
public-notebook ceiling. One thousandth of a point is worth roughly 190 ranks (0.954 → ~171,
0.955 → ~121, 0.956 → ~91). No public notebook scores above the plateau: every author at 0.956+
with published work reached it over 40–206 unpublished submissions.

The zero-cost recon of 2026-09-25 produced a real 14-config × 8-held-out-stem sweep table, and it
did three things at once:

- **It gave us the metric.** `proxy = adjusted_edge_jaccard + 0.1 × division_jaccard`, verified
  numerically on all 14 rows, with `adjusted_edge_jaccard = edge_jaccard × f(t_pred/t_true)` where
  the count adjustment is **one-sided**: over-prediction is penalised, under-prediction is not.
- **It closed two arms.** `MOTION_RELINK_TIGHT_UM`, `MOTION_RELINK_VELOCITY_WEIGHT` and
  `SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB` are *bit-identical to base* on all 8 stems, every column.
  And **no** post-process knob moves division recall: `div_tp = 3`/12 and `div_fn = 9` for all 14
  configs. Roughly 0.079 of proxy sits in divisions and is upstream-locked.
- **It identified one lever family worth testing** — pruning, because the one-sided count penalty
  makes it profitable on every movie — and then **disqualified the only member of that family with a
  score** (§3.2).

So the honest reading is: we know *where* the remaining reachable headroom is (the edge term, via
pruning), we know the mechanism, and we have **no** candidate that survives scrutiny. The gap
between those two facts is what this experiment closes.

## 1. Parent, and the vehicle problem

The parent is `exp_064` at 0.953. The difficulty is that **every lever worth testing is absent from
our parent's source.** `grep` of `biohub-x138.ipynb` returns **0 hits** for `OUTPUT_MIN_EDGE_PROB`,
`LEAF_PRUNE_MIN_EDGE_PROB`, `SEG_PRUNE_MIN_PROB`, `COUNT_EXCESS_FRAC`, `PPSWEEP_EXTENDED` and
`PPSWEEP_PREFIX_GUARD`. They exist only in `amanatar/optimized-biohub-max-score` (sha
`371fc1f9f4f20f692e0586616ff7d3eab4621d167f6c78516d3243c5a4fddfab`), which adds **862 lines** over
x138 and shares x138's 89 `BIOHUB_*` keys and its four datasets exactly.

**It is not a pure superset, and the 24 x138 lines it does not carry matter enough to enumerate.**
Four are the docstring, two are the `BIOHUB_PRESET` / `BIOHUB_SCORE_AXIS` labels, one is
`write_test_submission("base")` (re-emitted inside the try/finally of §5.1), one is a reflowed list
literal, and **twelve sit inside the validator/sweep selection block** that amanatar rewrote — dead
whenever `VALIDATOR_ENABLE=0`. That leaves four `os.environ` lines re-emitted with different trailing
comments, of which exactly **two carry a different value**:

| key | x138 | vehicle | bearing on H_control |
|---|---|---|---|
| `BIOHUB_VALIDATOR_ENABLE` | `0` | `1` | **intended** — this is the lever Run 1 turns on |
| `BIOHUB_REPAIR_DEADLINE_S` | `27000` | `os.environ.get("BIOHUB_REWRITE_DEADLINE_S", "30600")` → `30600` | a real difference |

Both deadlines are orders of magnitude beyond our 932 s run and neither can trip, but "cannot trip"
is an argument and this project has been burned by arguments. Run 1 therefore **sets
`BIOHUB_REPAIR_DEADLINE_S=27000` explicitly**, eliminating the difference for free rather than
reasoning about it (§4.1, §6 gate 3).

Two consequences, and the second is the whole design:

1. We cannot reach these levers by flipping an environment variable on the parent. Using them means
   running a **different notebook**.
2. Therefore the first thing this experiment must establish is that the different notebook **is** the
   parent when its levers are off. Not argue it — measure it.

Their own comment asserts it (*"At visible-run scale no gate trips and the floor is EXACTLY x138"*),
and my own static reading agrees: every v5 lever early-returns at its `0.0` default, the v9 deadline
gates are all time-based and cannot trip at our 932 s scale, `FROZEN_PRESET_JSON=""` leaves
`FROZEN_PRESET_OVERRIDES is None` so all frozen-preset branches are dead, and
`BIOHUB_VAL_PRED_CACHE_DIR=""` disables the cache path. **That is exactly the class of claim this
project has been wrong about five times.** It gets tested, not assumed.

## 2. The intervention

**Vehicle:** `amanatar/optimized-biohub-max-score`, taken verbatim, with exactly one authored change
(§4.3) plus environment settings.

**Lever family:** metric-aligned pruning — `OUTPUT_MIN_EDGE_PROB` (L1 weak-edge filter),
`SEG_PRUNE_MIN_PROB`/`SEG_PRUNE_MAX_LEN` (L2 weak pendant segments),
`LEAF_PRUNE_MIN_EDGE_PROB` (weak leaves), and `COUNT_EXCESS_FRAC` (L5 count-target budget), plus
their published stacks.

**Why this family and not another.** The count adjustment is one-sided, so removing a node that the
metric will not match is free on the count factor and costs only whatever correct edges go with it.
The telemetry confirms the free half empirically: for `ep015` the count factor improves on **8 of 8**
stems (+0.0010 … +0.0073). All risk sits in raw `edge_jaccard`.

**Why `COUNT_EXCESS_FRAC` is the most interesting member, despite having no score.** I read
`prune_to_node_count_target`. It needs no ground truth: it defines a *core* of nodes pinned by strong
evidence (frame 0, final frame, incident to an edge with `edge_prob is None` — gap / safe-div /
repair additions — or `>= CORE_EDGE_PROB` 0.60), sets the budget to `core_count × (1 + frac)`, and if
the graph exceeds it drops the weakest non-core, non-fork-parent nodes in a single pass with no
cascade. **That is per-movie adaptive by construction**, which is exactly the property a flat
probability threshold lacks — and `ep015`'s only two losses are movies where a flat threshold is the
wrong instrument (`44b6_341df25f`, base `edge_jaccard` already 0.995; `44b6_12dfb391`, already
predicting 0.752 × t_true). With hidden-test densities spanning 62.2 → 697.5 nodes/frame, an ~11×
range, adaptivity is not a nicety.

This is a mechanistic argument. **No `cx*` arm has a score.** It is a reason to *measure*, not to bet.

**Closed door, recorded so it is not re-proposed:** an exact per-movie count target is unavailable.
Both notebooks read `estimated_number_of_nodes`, but only from the TRAIN ground-truth path inside the
validator. I downloaded `test/44b6_0113de3b.zarr/zarr.json` (1,279 bytes) from the competition: its
attributes carry only `multiscales` and `image_statistics.quantiles`; no node-count hint, and no
`.zattrs` (404). The core-relative budget above is the best available proxy for it.

## 3. Hypotheses

### 3.1 H_control (the gate everything else depends on)

> With `BIOHUB_VALIDATOR_ENABLE=0`, `FROZEN_PRESET_JSON=""`, `VAL_PRED_CACHE_DIR=""` and every v5
> lever at its `0 = off` default, the vehicle's base `submission.csv` is **byte-identical** to
> exp_064's output sha `d52a5da2`.

Falsifiable, binary, and settled by one sha256. If true, the vehicle **is** the 0.953 parent and
inherits that score with **no leaderboard submission spent**. If false, the 862 lines are not inert
and every downstream comparison is confounded — see §8 stop rule.

### 3.2 H_lever, and why the obvious candidate does not qualify

> Some member of the pruning family improves the test-reweighted held-out aggregate over base by a
> margin that survives a leave-one-out jackknife.

Reweighting: the hidden test set is `44b6_0113de3b`, `44b6_0b24845f`, `6bba_05b6850b`,
`6bba_05db0fb1` — two movies per prefix, 45,250 / 75,969 nodes = **37 % / 63 %** (exp_064's own
collection). The validator's native weighting is 26 % / 74 %, so every delta below is recomputed at
the test split.

**`ep015` measured, and it fails.** Aggregate **+0.00236**. But:

| leave out | aggregate |
|---|---|
| — (all 8) | +0.00236 |
| `44b6_12dfb391` | +0.00841 |
| `44b6_341df25f` | +0.00314 |
| `6bba_085bf656` | +0.00247 |
| `44b6_2a2eff9f` | +0.00236 |
| `6bba_062c8d37` | +0.00204 |
| `6bba_07e24132` | +0.00185 |
| `44b6_267148e4` | +0.00115 |
| **`6bba_09961292`** | **−0.00295** |

7 of 8 leave-one-out subsets stay positive, but **`6bba_09961292` alone holds 60.6 % of the gross
positive contribution**, and dropping it flips the aggregate negative. Two movies are active drags
(`44b6_12dfb391` −0.0044, `44b6_341df25f` −0.0006). With only 4 test movies, a lever whose upside is
61 % one film is a coin-flip dressed as a measurement.

**No other measured candidate is even close.** `dcsd015` (+0.00014), `leaf040` (+0.00018) — both
inside noise. Everything else is zero or negative.

**Conclusion: on current evidence H_lever has no qualifying candidate.** The 27 never-scored members
of the same 41-candidate dict — including all three `cx*` arms, both other `ep*` thresholds, the
three `seg*` arms and the stacks `prune_pack`, `ep_cx`, `seg_cx`, `leaf_seg` — are unmeasured, and
measuring them is this experiment's primary product.

### 3.3 H_null

The pruning family produces no candidate passing §8. Then we submit nothing, keep 0.953, and have
bought a definitive map of the post-process space for ~3 GPU h and zero submissions. **This is an
acceptable outcome, not a failure**, and the proposal is designed so it costs no leaderboard slot.

## 4. Design — two runs, one submission

### 4.1 Run 1 — control and measurement, fused. Zero submissions.

The fusion is possible because of a property of the vehicle's own control flow: `write_test_submission("base")`
executes **before** the validator block. So a single validator-enabled run yields the control
artifact first and the sweep table second, and a mid-sweep failure still leaves the control intact —
demonstrated by amanatar's own crashed run, from which every artifact was recoverable.

Settings, all environment-level:

| key | value | purpose |
|---|---|---|
| `BIOHUB_VALIDATOR_ENABLE` | `1` | run the held-out validator |
| `BIOHUB_PPSWEEP_FAST_TIER` | `0` | sweep all **41** candidates, not the 12-item tier |
| `BIOHUB_PPSWEEP_EXTENDED` | `1` | (their default) the full candidate dict |
| `BIOHUB_PPSWEEP_PREFIX_GUARD` | `1` | **keep their guard on** — see §5.3 |
| every v5 lever | `0` / their defaults | the base pass must be the parent |
| `FROZEN_PRESET_JSON`, `VAL_PRED_CACHE_DIR` | `""` | dead branches |
| `BIOHUB_REPAIR_DEADLINE_S` | **`27000`** | restores x138's value; removes the one real config difference (§1) |
| the rest of the v9 deadline ladder | **unchanged** | see §5.2 |

Deliverables: `submission_base.csv` + its sha (the H_control test), `ppsweep_results.csv` and
`validator_results.csv` over 41 configs × 8 stems (the H_lever test), `ppsweep_selected.json`, and the
full log.

⚠ Run 1's own final `submission.csv` is rewritten by **their** selection guard and **must not be
submitted**. It is not our arm.

### 4.2 Run 2 — the bet. One submission, conditional on §8.

`VALIDATOR_ENABLE=0` plus the single winning override as a static environment value. Deterministic:
no validator, no sweep, no runtime re-selection — a genuinely clean one-variable change against a
byte-verified control. ~0.3 GPU h.

If §8 selects nothing, **Run 2 does not happen.**

### 4.3 The one authored change, and its exact scope

Their run died at `AttributeError: 'function' object has no attribute 'get'`. Cell index 11,
cell-local line 43:

```python
_v6env = os.environ.get          # then called as _v6env.get(...) on lines 44-50
```

Fix — delete four characters:

```python
_v6env = os.environ
```

Eight call sites on lines 44–50 become valid. They are **`print` arguments only**; the name `_v6env`
appears nowhere else in the notebook. The change cannot affect `submission.csv`, which is written
earlier. Under papermill the unfixed line fails the notebook, which is why amanatar sits at 0.953
with 116 submissions.

**Nothing else is authored.** Confirmed by a pre-launch diff gate (§6).

## 5. Risks

**5.1 H_control fails — the 862 lines are not inert.** The static reading says every added path is
guarded, but the diff contains three replacement hunks in the pre-validator region:
`write_test_submission("base")` wrapped in a try/finally that applies and then restores frozen-preset
overrides (a no-op while `FROZEN_PRESET_OVERRIDES is None`); the validator prediction-cache guard;
and one `if` condition gaining `and not _v7_val_pred_cache_hit`. Each is guarded by a variable we set
to its inert value, and §1 accounts for all 24 omitted lines — but "guarded by my reading" is not
"measured". If the sha differs we do not have a control, and §8 stops the experiment. This risk is
the reason Run 1 exists in this shape rather than as an assumption in a one-run design.

**5.2 Hidden-rerun wall.** The scored run is a server-side rerun — `exp_061` failed inside one. Our
x138-class run took 932 s on the visible set; 41 candidates extrapolates to ~2.5–3 h *there*.
amanatar built the v9 deadline ladder around a belief that "on Kaggle's hidden rerun the test set can
be larger"; that is their hedge, not a fact we have verified. Mitigation: **keep the ladder
unmodified.** It degrades to shipping the base configuration rather than timing out. Note Run 2 has
no validator or sweep at all, so the arm we would actually submit is the cheap one.

**5.3 Selection overfitting.** Their prefix guard rejected `ep015` and shipped a lever worth
+0.00014. That is not a flaw to route around — §3.2 shows the guard was **right**. We keep it on in
Run 1, and §8 adds a jackknife on top rather than relaxing anything.

**5.4 Public-LB overfitting, against an unrevealed private score.** `privateScore` is present and
**empty on all 30 of our submissions**; final standing is on data we have never scored. ~25 remaining
slots against a 4-movie visible set is the classic overfit shape. This proposal spends **at most
one** slot and requires held-out corroboration before spending it.

**5.5 Third-party weights.** The vehicle mounts `anvithpothula/biohub-v1284-head-s075`, exactly as
exp_064 did — an accepted, already-submitted risk, not a new one.

**5.6 Proxy→LB transfer is calibrated on one point.** Base proxy 0.95549 against measured LB 0.953,
offset −0.0025. A single point. No predicted score appears in this proposal's success criteria, and
none should appear in its report.

## 6. Local gates — zero GPU, all executable before launch

1. **Vehicle integrity:** sha256 of the pulled notebook == `371fc1f9f4f2…`; dataset list ==
   exp_064's four, exactly.
2. **Authored-change gate:** diff vehicle-as-run against the archived original; assert **exactly one**
   changed line, and that it is cell 11 line 43.
3. **Config gate:** assert all 89 x138 keys present with x138's values — **including
   `REPAIR_DEADLINE_S == 27000`**, the one key the vehicle changes (§1); assert every v5 lever at its
   off default; assert the rest of the v9 deadline ladder byte-unchanged; assert `FROZEN_PRESET_JSON`
   and `VAL_PRED_CACHE_DIR` empty. Also assert the **24 x138 lines the vehicle omits** are exactly
   the enumerated set from §1, so an unnoticed further omission cannot slip in on a re-pull.
4. **Candidate-dict gate:** assert `PP_CANDIDATES` has 41 entries and `FAST_TIER=0`, so the sweep
   cannot silently run 12. *(This is the fourth-instance failure mode; it gets an assertion.)*
5. **Snapshot smoke** per the standing admission requirement.

No local proxy gate is claimed: we cannot run the pipeline off-Kaggle. Stated as the limitation it is.

## 7. Budget

| item | GPU h |
|---|---|
| Run 1 (validator + 41-candidate sweep) | ~3.0 measured-analogue; **reserve 4.0** |
| Run 2 (deterministic single lever) | ~0.3 |
| **total reserved** | **4.3 of 19.741056** |

Submissions: **at most 1**, from Run 2 only, separately authorized. LB cap 5/NY-day; 0 used on 09-25.
Calendar: ~4 days to 2026-09-29 23:59; two serial runs of ~3 h and ~0.3 h fit with wide margin.

## 8. Pre-registered decision rules

**Gate 1 — H_control.** Run 1's base submission sha **must equal** `d52a5da2`.
*Pass* → the vehicle is the parent; proceed. *Fail* → **STOP.** Do not run Run 2, do not submit.
Report the diff, and reconsider whether any of this family is reachable at all.

**Gate 2 — lever selection.** Rank all 41 candidates by test-reweighted (37 %/63 %) aggregate
`adjusted_edge_jaccard` delta against base. A candidate qualifies only if **all** hold:

1. aggregate delta **≥ +0.0015**;
2. **every** leave-one-out subset of the 8 stems remains **> 0** (the jackknife);
3. it passes amanatar's own prefix guard (no embryo prefix regressing > 0.001).

Pick the highest-ranked qualifier. **If none qualifies, submit nothing** and report H_null.

These thresholds are fixed now, before Run 1 exists, and the rule is **executable**:
`docs/research/public_notebook_archive/amanatar_v9_sweep_telemetry/analyze_sweep_table.py` reads only
the two archived CSVs, needs no GPU, network or credentials, and reproduces every figure quoted in
this proposal. Reviewers should run it rather than trust my arithmetic. Its output on the 14 configs
we already hold:

```
ep015                    +0.00236   LOO worst -0.00295   6/2   fails 2+3
leaf040                  +0.00018   LOO worst -0.00006   6/2   fails 1+2
dcsd015                  +0.00014   LOO worst -0.00000   1/1   fails 1+2
... (every remaining config fails 1+2, several also 3)
Gate 2 selects NOTHING on this table -> H_null, no submission.
```

So the rule is not vacuous, and it is **not** reverse-engineered to admit the candidate I would
otherwise have picked — it rejects exactly that candidate. It also confirms
`proxy = adjusted_edge_jaccard + 0.1 × division_jaccard` to a maximum residual of 0 across all 14
rows.

**Gate 3 — LB read.** Against the 0.953 parent: **≥ 0.955** adopt · **0.954** a real but small gain,
adopt and stop · **0.953** null, keep the parent · **≤ 0.952** revert to exp_064 immediately.

**Rollback.** exp_064 (0.953, 56535761) and `repro_059` (0.947, 56313491) are untouched and remain
the fallbacks. Nothing in this experiment modifies them.

## 9. Governance

CONSENSUS on this record authorizes **nothing**. Remaining gates, in order: Codex challenge → my
revision → explicit CONSENSUS → build → fresh experiment-specific Codex admission PASS → snapshot
smoke → budget reservation → **one user-authorized launch of Run 1** → evaluation against §8 →
**separately authorized** Run 2 → **separately authorized** submission. Claude Code does not review
its own work; the admission review is Codex's.

## 10. What would change my mind

- **H_control fails.** Then the vehicle is not the parent, and the cheapest honest fallback is the
  demoted `readmit-v1` A/B on x138 itself (~0.26 GPU h), whose expected effect is unquantified.
- **Run 1 shows the `cx*` family is inert**, like `tight_um` before it. Then the mechanism argument
  in §2 is wrong and the pruning family reduces to `ep*`, which §3.2 already disqualifies → H_null,
  no submission.
- **Run 1's base pass diverges from amanatar's published telemetry** on the 8 shared stems. Their
  numbers came from a crashed run on a possibly different environment; a mismatch would mean the
  harvested table does not describe our pipeline, and §8 Gate 2 should be re-evaluated against our
  own numbers only — which it already is, by construction.

## Appendix — deliberately out of scope

- **Any division arm.** `div_tp = 3`/12 and `div_fn = 9` across all 14 measured configs; the ~0.079
  of proxy in divisions is upstream-locked. exp_056 and exp_058 already died here.
- **Any `tight_um` / velocity / short-track-rescue arm.** Measured bit-identical to base.
- **An exact per-movie count target.** The test zarr carries no node-count hint (§2).
- **Raising exp_062's β, or porting mutual-best.** k2 scored 0.944; the arc is closed.
- **Training or fine-tuning anything.** Four days, one unrevealed private score, no held-out
  training protocol. Not defensible at this stage.
