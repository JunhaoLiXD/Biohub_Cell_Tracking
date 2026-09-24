# Measured density of the four hidden-test movies — 2026-09-24

Zero-GPU, zero-submission measurement. Author: Claude Code. **This is our own measurement on our own
output, not a third-party claim.**

## Method

Counted `row_type == node` rows per `dataset` in the exp_062 **k1 control** `submission.csv`
(SHA256 `d34533806b…`, byte-identical to our 0.947 parent `repro_059`, submission 56313491), and
divided by the number of distinct `t` values. This is exactly the statistic
`determine_density_group` computes in the public notebooks:
`avg_per_frame = len(nodes_by_id) / n_distinct_t`.

Note this uses our **predicted** node counts, which is also what the public code uses at inference
time — it is not ground truth and needs none.

## Result

| dataset | nodes | frames | avg/frame | public group | that group's `tight_um` | ours |
|---|---:|---:|---:|---|---:|---:|
| `44b6_0113de3b` | 25,637 | 100 | 256.4 | middle | 6.5 | **5.5** |
| `44b6_0b24845f` | 20,729 | 100 | 207.3 | middle | 6.5 | **5.5** |
| `6bba_05b6850b` | 6,152 | 100 | 61.5 | **low** | **7.25** | **5.5** |
| `6bba_05db0fb1` | 70,290 | 100 | 702.9 | high | 5.5 | 5.5 ✓ |

Group thresholds are the public table's: `< 120` low, `< 400` middle, else high.

## What this establishes

**Three of the four hidden-test movies run a `tight_um` that the public density table says is wrong,
and only one — the high-density movie — matches our frozen global `tight55 = 5.5`.**

The worst mismatch is `6bba_05b6850b` at 61.5 cells/frame: the table would use **7.25 µm** where we
use 5.5 µm, i.e. we relink ~24 % tighter than the public policy on the sparsest movie.

Density spans **11.4×** across the four movies (61.5 → 702.9). The 09-23 recon *speculated* "~11×
(≈61 → 703 cells/frame) … a single global tight55 is plausibly mis-set for three of the four
movies." That speculation is now **measured and confirmed on the actual test set**.

Our `tight55` was selected by the parent's embedded PP-sweep over **eight held-out training videos**
(`ppsweep_selected.json`: `44b6_12dfb391`, `44b6_267148e4`, `44b6_2a2eff9f`, `44b6_341df25f`,
`6bba_062c8d37`, `6bba_07e24132`, `6bba_085bf656`, `6bba_09961292`) as a **single global value**.
A global optimum over a mixed-density panel is not the per-movie optimum for a panel spanning 11×.

## Why this matters for what we do next

This is the first time in this project that a proposed lever has **independent, measured,
mechanistic support from our own data** rather than a third-party headline number. It changes the
justification for testing density-adaptive relinking:

- **Before:** "an author claiming 0.948/0.951, absent from the LB top 200, published this."
- **Now:** "we measured our own pipeline applying a single global parameter to a panel spanning 11×
  in density, and 3 of 4 test movies fall outside the regime that parameter was selected for."

We are no longer trusting `haideptry`'s claim. Their notebook is merely a convenient existing
implementation of a hypothesis **we verified ourselves**. That distinction matters, because the
DivNet finding (a "SOTA … + DivNet 3D Gate" notebook whose gate throws on every call — see
`experiments/exp_063_public_0951_pipeline_repro/review.md`) shows the author does not validate their
own pipeline, so their headline numbers deserve little weight.

## What it does NOT establish

- **Not** that the public table's specific values (7.25 / 6.5 / 5.5) are the right ones. They are
  another author's constants, selected on unknown data. A mismatch with our global 5.5 is evidence
  the global value is *questionable*, not that 7.25 is *correct*.
- **Not** any LB delta. Relinking tightness interacts with the rest of the pipeline; a looser gate
  adds both true and false links. Direction of effect is unknown until measured.
- **Not** applicable to division. This is edge/relinking only.
