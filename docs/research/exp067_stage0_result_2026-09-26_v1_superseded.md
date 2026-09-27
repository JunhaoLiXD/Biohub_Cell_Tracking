# Stage 0 result — candidate-headroom audit. Zero GPU.

**2026-09-26.** Run on the cached `exp_067d` export: 8 movies, 186,803 nodes, 1,088,256 bounded
alternatives, 8 label sets. No GPU, no submission. Oracle upper bound computed with labels — a
**diagnosis, not performance**, and it must never be quoted as a score.

## Two bugs of mine, before the result

The audit reported **"0 of 7 reachable — NO HEADROOM"** on its first run, and I was one step from
reporting that the arc was dead. It was wrong, twice, both mine:

1. `hypotheses.py` keys its arrays by node **row index**, not node id (`generate():134` builds
   `parent_pairs` through `row_of_node`; `_generate_events():339` indexes `node_id[r]`). The audit
   looked up node ids in a row-keyed set, so every lookup missed.
2. The first fix introduced a shadowed variable — `row` was both the row mapping and the per-event
   dict — so the corrected branch never executed and the numbers did not move.

Recorded because the project's standing rule is to verify our own claims before measuring, and this
is the ninth instance of machinery that looked like it was working and was not.

## The corrected result

| | |
|---|---|
| ground-truth divisions | 12 |
| mother and both daughters matched | 9 |
| already correct in the parent graph | 2 |
| **missed by the parent — the headroom** | **7** |
| both edges present in the candidate set | **6 of 7** |
| a division *event* generated over that pair | **0 of 7** |
| ...passing the geometry gates | **0 of 7** |

The edges exist. The **pairing** never does.

## Why: the generator inherits a symmetry prior the real divisions violate

`symmetric_event_geometry` rejects **7 of 7**. The true missed divisions are geometrically
**asymmetric** — one daughter essentially on top of the mother, the other far away:

| stem | d(mother→A) µm | d(mother→B) µm | sister µm |
|---|---|---|---|
| 44b6_12dfb391 | 2.67 | 8.56 | 11.10 |
| 44b6_267148e4 | 2.26 | 9.69 | 11.53 |
| 44b6_2a2eff9f | 11.52 | 0.34 | 11.52 |
| 44b6_341df25f | 1.50 | 8.53 | 9.70 |
| 6bba_07e24132 | 1.74 | 6.74 | 8.28 |
| 6bba_09961292 | 1.05 | 9.08 | 10.03 |
| 6bba_09961292 | 7.16 | 1.08 | 8.10 |

Relaxation sweep over the gate, offline:

| safe_div_max_um | sister_max | diverge | **symmetry_tau** | admissible |
|---|---|---|---|---|
| 9.0 | 14.0 | 2.25 | **0.60** | **0 / 7** |
| 12.0 | 14.0 | 2.25 | 0.60 | 0 / 7 |
| 14.0 | 18.0 | 0.00 | 0.60 | 0 / 7 |
| 14.0 | 18.0 | 0.00 | **0.00** | **7 / 7** |

**`safe_div_sister_symmetry_tau` is the wall.** Distance relaxation alone changes nothing; dropping
the symmetry prior admits all seven. The value 0.6 is inherited from x138's
`BIOHUB_SAFE_DIV_SISTER_SYMMETRY_TAU`, so it has been present in every configuration this project
has ever measured.

**This mechanistically explains the project's most durable mystery.** `div_tp` sat at 3/12 across 30
measured configurations not because the search or the scoring was weak, but because the geometry
prior forbids the shape the real missed divisions actually have.

## The catch, and it is decisive

The harvested public sweep (`amanatar_v9_sweep_telemetry/ppsweep_results.csv`) **already measured
the parent-side analogue**. Arm `sym075`:

| config | proxy | div_tp | div_fp | div_fn |
|---|---|---|---|---|
| base | 0.955489 | 3 | 2 | 9 |
| **sym075** | **0.950093** | **3** | **6** | **9** |
| ep015 (best) | 0.960615 | 3 | 2 | 9 |

Loosening the symmetry knob produced **four extra false-positive divisions and recovered zero true
ones**, and cost 0.0054 of proxy. Every one of the 14 swept configurations sits at `div_tp = 3`,
`div_fn = 9`.

So relaxing the geometry **alone** is measured not to work. It admits noise, not signal.

## Where that leaves exp067

Not dead — but the bar is now explicit and it is high. exp067 would have to do **both**:

1. relax its generator geometry so true asymmetric divisions become candidates at all (necessary;
   this audit shows it is currently impossible without it), **and**
2. learn a discriminator sharp enough to pick those few true divisions out of the flood that
   relaxation admits — from **≤45** training examples, concentrated in a handful of movies.

Step 2 is the thing the measured evidence gives no reason to expect from this sample size. The one
comparable effort we can see (`y3uanm`, `real_sparse_teacher_plus_synthetic_dense`) attacked exactly
this and used **dense synthetic labels** to do it.

## Recommendation

**Stop the arc, per the plan's default.** Stage 0 did its job: it returned "no" for zero GPU, and it
returned something better than a bare no — a mechanism.

What was gained, and is worth keeping regardless:

- The reason `div_tp` never moves is now known and is a **prior**, not a search failure.
- The candidate export is banked and the pipeline is proven end to end.
- The route a stronger effort would take is identified: relaxed geometry **plus** dense supervision,
  after the close, with ZebraHub (`hftams/zebrahub-zsns003`, 208 MB of dense tracks, public) as the
  obvious first source.

Q2 (negative control) and Q3 (positive control) were not run. They only matter if the arc continues;
they cost nothing and can be run on request.

## Artifacts

- `scripts/exp067_stage0_audit.py`, `scripts/exp067_stage0_why.py`
- `docs/research/exp067_stage0_q1_headroom.json`, `docs/research/exp067_stage0_q1_causes.json`
