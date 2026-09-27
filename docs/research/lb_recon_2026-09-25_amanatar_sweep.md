# Recon 2026-09-25 (afternoon): the two pending scores resolved, and a harvested held-out sweep table

Zero GPU. Zero submissions. Everything below is reproducible from the authenticated Kaggle CLI and
from the artifacts archived under `public_notebook_archive/`.

## 1. Both pending scores are in

| submission | arm | Public LB | pre-registered rule | verdict |
|---|---|---|---|---|
| **56535761** | exp_064 — x138 byte-verbatim | **0.953** | `>=0.953` -> adopt | **ADOPT x138 as parent** |
| **56530197** | exp_062 k2 — mutual-best beta=0.20 | **0.944** | `<=0.946` -> revert | **REVERT, arc closed** |

0.953 is +0.006 over `repro_059` 0.947 and is now the project's best authenticated score.
exp_062's edge prior is a measured **loss** of 0.003; do not raise beta, do not retry a variant.

**Independent corroboration of the 0.953.** `amanatar/optimized-biohub-max-score` cell 0 declares
`BIOHUB_SCORE_AXIS = 'x138 base (LB 0.953) + ...'`. A third party measured the same value for the
same notebook. It follows that anvithpothula's rank-67 0.956 is **not their published notebook's
score** — the 0.956 came from unshared work. The same reasoning now applies to thtennant's 0.959,
which weakens the case for the `readmit-v1` A/B that was the standing next step.

## 2. Standings, snapshot `2026-09-25T12:50`

3899 teams. Ours: **rank 361, score 0.953, 30 submissions.**

| rank | 50 | 100 | 150 | **200-420** | 450 | 500 |
|---|---|---|---|---|---|---|
| score | 0.959 | 0.955 | 0.954 | **0.953** | 0.951 | 0.949 |

**0.953 is a 249-team plateau** — the public-notebook ceiling. This is the single most actionable
fact on the board: one thousandth of a point is worth ~190 ranks.

| target | teams at or above | our rank would be |
|---|---|---|
| 0.954 | 171 | ~171 |
| 0.955 | 121 | ~121 |
| 0.956 | 91 | ~91 |

## 3. No public notebook scores above the plateau

Mapped every notebook author in the competition to their authenticated team score. The public ladder
tops out at the x138 / frontier947-readmit configuration, which we have now *measured* at 0.953.
Authors sitting at 0.956+ with published notebooks (`andrey4522` 0.956 / 206 subs, `anvithpothula`
0.956 / 123, `y3uanm` 0.956 / 62, `thtennant` 0.959 / 40) all reached those scores through
dozens-to-hundreds of submissions of work they did not publish.

Two artifacts are genuinely new since the 01:45 mining pass:

- **`amanatar/optimized-biohub-max-score`** (run 2026-09-25 01:59, 24 votes, author 0.953 / 116 subs)
  — a **near-superset of x138**: all 89 `BIOHUB_*` keys identical, +24 new keys, +862 source lines, and
  24 omitted x138 lines that are all accounted for (docstring, labels, the rewritten validator/sweep
  block, and two re-emitted `os.environ` values) — see the proposal §1. Same 4 datasets as x138 (including the V1284 head). It turns ON the validator
  and post-process sweep that x138 ships disabled, and adds a "v5 metric-aligned" lever ladder
  (L1-L7) plus a 9 h deadline governor and a per-embryo anti-overfit selection guard.
- **`seyitkaangunes/biohub-035-deconfounded-edge-stack`** (author 0.954 / 45 subs) — a *lighter* base
  (x138 minus all 30 flow / gapfill / readmit keys) plus `LEAF_PRUNE_MIN_EDGE_PROB=0.30` and
  `MOTION_RELINK_VELOCITY_WEIGHT=0.25`. Note section 4: the second of those two levers is measurably
  inert.

`raunakdey07/biohub-harmonic-fusion-v3` (97 votes, re-run 09-25 09:09) has a config **identical to
x138** in all 89 keys and roughly 50 lines of source difference. Not an advance; a sibling.

## 4. The harvest: a 14-config held-out sweep table, obtained for free

`amanatar`'s run had `BIOHUB_VALIDATOR_ENABLE=1`, and Kaggle publishes kernel output. So
`kaggle kernels output` yielded their `ppsweep_results.csv`, `ppsweep_selected.json`,
`validator_results.csv` (112 rows = 14 configs x 8 stems) and a 982 KB log. Archived under
`public_notebook_archive/amanatar_v9_sweep_telemetry/`, hashes in `SHA256SUMS_amanatar_v9.txt`.

**This is the telemetry that `lb_mining_2026-09-25.md`, correction 1, concluded we could not get.**
That conclusion was right about x138 and wrong as a general claim: the sweep is off in x138, but
another author's superset ran it and the output is public.

**The metric formula is now known from their code path:** `proxy = adjusted_edge_jaccard + 0.1 *
division_jaccard`, verified numerically on all 14 rows. And `adjusted_edge_jaccard = edge_jaccard *
f(t_pred / t_true)` where the count adjustment is **one-sided** — over-prediction is penalised,
under-prediction is not. Their own comment states this and it is what the numbers show.

### The table (8 held-out TRAIN stems, 4 per embryo prefix, base = x138 configuration)

| config | override | proxy | d proxy | d **test-reweighted** adjEJ | stems up/down |
|---|---|---|---|---|---|
| **ep015** | `OUTPUT_MIN_EDGE_PROB=0.15` | **0.9606** | **+0.0051** | **+0.00236** | 6 / 2 |
| dcsd015 | `DEEPCENTER_SAFE_DIV_THRESHOLD=0.15` | 0.9573 | +0.0018 | +0.00014 | 1 / 1 |
| divwide_dcsd010 | + geometry widening | 0.9573 | +0.0018 | +0.00014 | — |
| leaf040 | `LEAF_PRUNE_MIN_EDGE_PROB=0.40` | 0.9558 | +0.0003 | +0.00018 | 6 / 2 |
| **base** | — | 0.9555 | 0 | 0 | — |
| ~~tight55~~ | `MOTION_RELINK_TIGHT_UM=5.5` -- **same as base, a no-op comparison** | 0.9555 | n/a | n/a | n/a |
| **vel075** | `MOTION_RELINK_VELOCITY_WEIGHT=0.75` | 0.9555 | **+0.0000000** | 0 | **0 / 0** |
| **rescue085** | `SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB=0.85` | 0.9555 | **+0.0000000** | 0 | **0 / 0** |
| dcgap018 | `DEEPCENTER_GAP_THRESHOLD=0.18` | 0.9553 | -0.0002 | -0.00021 | — |
| minlen5 | `OUTPUT_MIN_TRACK_LEN=5` | 0.9550 | -0.0005 | -0.00050 | — |
| sym075 | `SAFE_DIV_SISTER_SYMMETRY_TAU=0.75` | 0.9501 | -0.0054 | -0.00056 | — |
| repd_divgap | second-daughter repair + div gap | 0.9489 | -0.0066 | -0.00092 | — |

"Test-reweighted" recomputes the weighted mean of `adjusted_edge_jaccard` after rescaling the two
embryo prefixes from the validator's native 26 % / 74 % split to the hidden test set's node split.
**The hidden test set is `44b6_0113de3b`, `44b6_0b24845f`, `6bba_05b6850b`, `6bba_05db0fb1` — two
movies of each prefix, 45,250 / 75,969 nodes = 37 % / 63 %** (from exp_064's own collection). So the
proxy's embryo balance is close to the test's, slightly over-favouring 6bba. Reweighting halves
`ep015`'s gain but leaves it roughly 13x larger than anything else and does not change the ordering.

### Four results that close off standing candidate arms

1. **`MOTION_RELINK_VELOCITY_WEIGHT` and `SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB` are inert.**
   `vel075` (default 0.5 -> 0.75) and `rescue085` (0.88 -> 0.85) are both genuine changes, and both
   are *bit-identical* to base on all 8 stems, on every column.
   **CORRECTION 2026-09-25, from the Codex challenge: `tight55` does NOT belong on this list and the
   "`MOTION_RELINK_TIGHT_UM` is inert" claim is WITHDRAWN.** x138 and the vehicle both already set
   `MOTION_RELINK_TIGHT_UM = 5.5`, and the `tight55` candidate sets 5.5 -- the sweep never varied the
   variable, so its identical row is a self-consistency check, not evidence about the lever. The
   `tight_um` question that `lb_mining_2026-09-25.md` left open is still open. A `tight60` arm is
   unsupported by this table in either direction.
2. **No post-process knob moves division recall.** `div_tp = 3` of 12 for **all 14 configs**,
   `div_fn = 9` for all 14. Only `div_fp` moves (2 -> 1 for the dcsd family, 2 -> 6/7 for sym075 and
   repd_divgap). With divisions weighted 0.1 and `division_jaccard = 0.214`, there is roughly 0.079
   of proxy sitting in divisions — and it is **upstream-locked in detection/association, not
   reachable from post-processing.** exp_056 and exp_058 both died in this territory; this is the
   measurement that explains why. **Do not open a third division arc.**
3. **The one-sided count adjustment is a free, universal lever.** Decomposing `ep015`: the count
   factor improves on **8 of 8** stems (+0.0010 to +0.0073). All the heterogeneity is in raw
   `edge_jaccard`, which is flat-or-up on 6 stems and down on exactly two — `44b6_341df25f`
   (base `edge_jaccard` 0.995, nothing to gain, -0.0144) and `44b6_12dfb391` (already predicting only
   **0.76263** x t_true, pruning it further is wrong, -0.0232; an earlier version of this document
   said 0.752, which is ep015's ratio, not base's). The mechanism is understood, and it points
   at the count-targeted variants rather than a flat threshold.
4. **Their selection guard rejected the only lever that mattered.** The logged rule is
   `>= +0.001 proxy AND per-embryo adj loss <= 0.0005`. `ep015` clears the margin easily but loses
   0.0085 on the 44b6 prefix, so `dcsd015` shipped instead — worth **+0.00014** test-reweighted, i.e.
   nothing. **Running their notebook verbatim would gain us approximately zero.**

### And their run failed anyway

The log ends in `AttributeError: 'function' object has no attribute 'get'` — they wrote
`_v6env = os.environ.get` and then called `_v6env.get(...)` in a summary `print` in cell 12, *after*
`submission.csv` was already written. Under papermill that is a notebook failure, which is why
`amanatar` is still sitting at 0.953 with 116 submissions. Fifth instance in this project's recon of
the same class of defect: correct, fully-wired machinery defeated by a trivial wiring fault.

## 5. 29 of their 41 declared candidates were never scored

Their sweep declares 41 candidates excluding base but `BIOHUB_PPSWEEP_FAST_TIER=1` ran only a 12-item curated tier
(plus base and one combo). Unscored, and reachable by setting `BIOHUB_PPSWEEP_FAST_TIER=0`:

- **the rest of the winning family:** `ep010`, `ep020`
- **weak pendant-segment pruning:** `seg030L3`, `seg035L4`, `seg040L6`
- **count-target pruning, the principled form of result 3:** `cx03`, `cx06`, `cx10`
- **stacked pruning:** `prune_pack` (leaf030 + seg035L4 + **ep015** + cx06), `ep_cx`, `seg_cx`,
  `leaf_seg`
- division family (deprioritise, see result 2): `dcsd010`, `diverge150`, `divgap60`, `divgap70`,
  `repd010`, `repd015`, `repd015w`
- motion/geometry: `gap45`, `relaxed9`, `bonus125`, `gap2step40`, `reuse28`, `dcgap035`, `leaf030`,
  `vel025`, `lfitclamp25`, `lfitclamp40`

Their full run cost **~7000 s = 1.94 GPU h** with 14 configs; all 41 extrapolates to ~2.5-3 h.

Every `ep*`, `seg*`, `cx*` and `lfitclamp*` lever is **implemented in amanatar's 862 added lines and
does not exist in x138 at all** (`grep` of x138: 0 hits for `OUTPUT_MIN_EDGE_PROB`,
`LEAF_PRUNE_MIN_EDGE_PROB`, `SEG_PRUNE_MIN_PROB`, `PPSWEEP_EXTENDED`, `PPSWEEP_PREFIX_GUARD`). They
cannot be reached by flipping an environment key on our exp_064 parent; using them means taking
amanatar's notebook as the parent. `DEEPCENTER_SAFE_DIV_THRESHOLD` is the exception — x138 has it,
set to 0.25.

## 6. Proxy -> LB calibration

One point only: base proxy `0.95549` against measured LB `0.953`, offset **-0.0025**. Treat as a
single calibration point, not a transfer function. Under it, `ep015` test-reweighted (+0.00236)
predicts **~0.955**, which on the current board is about rank 121. That is a prediction from one
offset and an 8-movie proxy and must not be reported as an expected score.

## 7. What this implies for the next step (analysis, not an authorised plan)

The `readmit-v1` A/B from `lb_mining_2026-09-25.md` is **weaker than it looked** — its premise was
thtennant's 0.959 versus anvithpothula's 0.956, and we now know neither number belongs to the
published notebook. Its expected gain is unquantified.

The better-evidenced route is amanatar's notebook as parent, with the `ep`/`seg`/`cx` pruning family
as the lever, because it is the only family with a measured, mechanistically-explained,
6-of-8-stems-positive effect on an x138-identical base.

A design that keeps it to one variable and spends no submission on the control:

- **Arm A (control, 0 submissions).** amanatar's notebook, cell-12 typo fixed,
  `BIOHUB_VALIDATOR_ENABLE=0`, every v5 lever at its 0 = off default. Their 24 extra keys are then
  either inert (the deadline ladder, which only the validator reads) or off (the L1-L7 levers), so
  this should **byte-reproduce exp_064's output sha `d52a5da2`**. If it does, their 862 lines are
  proven inert when off and the parent inherits the measured 0.953 with no LB cost. ~0.26 GPU h.
- **Arm B (the bet, 1 submission).** Arm A plus one lever. Deterministic, no sweep, no runtime
  re-selection — a genuinely clean one-variable experiment against a byte-verified control.
- **Arm C (information, 0-1 submissions).** Arm A with `BIOHUB_VALIDATOR_ENABLE=1` and
  `BIOHUB_PPSWEEP_FAST_TIER=0`: scores all 41 candidates on 8 held-out stems and produces the same
  table above for *our* pipeline, including the 27 unscored levers. ~2.5-3 h. Its own
  `submission.csv` is chosen by *their* guard and should not be submitted unthinkingly.

Sequencing Arm A+C first and Arm B second buys a measured table before spending a submission, at
roughly 3 h of a 19.74 h budget. All of this requires a strategy record, Codex challenge and
CONSENSUS, a fresh experiment-specific admission PASS, a snapshot smoke, and explicit user
authorisation, in that order. Nothing here is authorised.

## 8. Follow-up checks, 2026-09-25 (still zero GPU, zero submissions)

### `COUNT_EXCESS_FRAC` is self-normalising per movie — the reason to prefer it over `ep015`

Read `prune_to_node_count_target` in amanatar's source. It does **not** need ground truth. It defines
a *core* of nodes pinned by strong evidence (frame 0, final frame, incident to an edge with
probability `None` — gap / safe-div / repair additions — or `>= CORE_EDGE_PROB` 0.60), sets the
budget to `core_count * (1 + COUNT_EXCESS_FRAC)`, and if the graph exceeds it drops the weakest
non-core, non-fork-parent nodes (lowest max incident edge probability, then lowest degree) in a
single pass with no cascade.

That is **per-movie adaptive by construction**, and it is precisely the property `ep015` lacks.
`ep015`'s only two losses were on movies where a flat global probability threshold is the wrong
instrument: `44b6_341df25f` (base `edge_jaccard` already 0.995) and `44b6_12dfb391` (already
predicting 0.76263 x t_true). **CORRECTED 2026-09-25 by the Codex challenge:** a core-relative
budget adapts to the graph's own confident core, **not** to ground-truth excess, so it offers **no
under-prediction protection** and does not repair ep015's failure mode. What survives is only that it
is a structure-relative instrument rather than a global probability cut. Given the hidden test movies span 62.2 to 697.5 nodes per frame — an
~11x range — this matters.

`cx03`, `cx06`, `cx10`, `ep_cx` and `prune_pack` are therefore the highest-value **unmeasured**
candidates, and all five are in the 29 the fast tier skipped. This is a mechanistic argument, not
evidence: no `cx*` arm has a score. Arm C measures them.

### Closed door: the test movies do NOT carry `estimated_number_of_nodes`

Both x138 and amanatar read `estimated_number_of_nodes` via `read_estimated_true_node_count`, which
would allow pruning to an exact per-movie count target — the optimal attack on a one-sided count
penalty. **It is only read from the TRAIN ground-truth graph path (`gt_path`), inside the
validator.** Downloaded `test/44b6_0113de3b.zarr/zarr.json` (1,279 bytes) directly from the
competition: its attributes carry only `multiscales` and `image_statistics.quantiles`. No node-count
hint, and no `.zattrs` (404). So an exact count target is **not available at test time** and the
core-relative budget above is the best available proxy for it. Do not propose an exact-count arm.

### The final evaluation is a hidden code rerun, and the private score is unrevealed

`privateScore` exists as a column on our authenticated submission history and is **empty for all 30
submissions**. `exp_061`'s record shows a submission failing inside the *hidden code rerun*, so our
notebook is genuinely re-executed server-side. `sample_submission.csv` names the same 4 datasets we
see. Whether the final rerun uses additional movies is **unknown to us**; what is on record is that
amanatar built a whole deadline ladder (`WALL_BUDGET_S=32400`, `VALIDATOR_LATEST_START_S`,
`SWEEP_LATEST_START_S`, `SWEEP_DEADLINE_S`, `REWRITE_*`) around the belief that "on Kaggle's hidden
rerun the test set can be larger". That is a third-party author's hedge, not a fact.

Two consequences:

1. **If we adopt their notebook, keep the deadline governor.** Our x138-class run took 932 s on the
   visible set; a 41-candidate sweep is ~2.5-3 h there. If the rerun set is materially larger, an
   ungoverned sweep could approach the 9 h wall. Their ladder degrades to shipping the base
   configuration instead of failing, which is the behaviour we want.
2. **An unrevealed private score is the real argument against LB-shotgunning.** ~25 remaining slots
   against a 4-movie visible set is exactly the shape that overfits. Prefer levers with a named
   mechanism *and* held-out corroboration — which is what the harvested table and Arm C provide —
   over levers whose only support is a Public LB delta.
