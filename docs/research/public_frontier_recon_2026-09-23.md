# Public-frontier recon — 2026-09-23

Record type: zero-GPU public-notebook and leaderboard recon.
Author: Claude Code. Status: evidence gathering only. **No experiment is authorized by this
document.** Supersedes the recon section of
`experiments/repro_059_public_0947_exact_copy/PROVENANCE.md` §4 (2026-09-18).

Trigger: the user abandoned the exp_061 zon LB-transport arc after five consecutive failed
submissions and asked whether a newer, reliable public strategy above 0.947 exists, and if not,
whether anyone has shared a next step.

---

## 1. Where we actually stand

| fact | value | source |
|---|---|---|
| our best Public LB | **0.947** (repro_059, submission 56313491) | authenticated submission history |
| our scored submissions | 15 | authenticated |
| **LB rank-200 cutoff** | **0.949** | `competitions leaderboard`, 200-row page, 2026-09-23 |
| LB top | **0.975** (Sergio Alvarez) | same |
| top-3 | 0.975 / 0.973 / 0.970 | same |
| teams ≥ 0.965 | ≥ 14 in the first 20 rows alone | same |
| competition deadline | **2026-09-29 23:59** | `competitions_list` |
| daily submission cap | **5** | `competitions_list max_daily_submissions` |

**0.947 is now outside the top 200.** On 2026-09-18 the frontier was ~0.970; it is 0.975 now, and a
very thick band sits at 0.955–0.966. The gap is no longer marginal.

## 2. Is there a verified public notebook above 0.947?

**No.** Every notebook inspected resolves to the same lineage and the same three Pilkwang
checkpoints (`biohub-deepcenter-unet3d-center-prior-v1`, `biohub-temporal-unet3d-seed314159-v1`,
`biohub-tracking-support-pack-50ep-v1`). Nobody wins via a better base model.

New high-vote notebooks published **since the last recon** (all pulled and inspected):

| notebook | votes | date | verdict |
|---|---|---|---|
| `amanatar/biohub-geometric-fusion` | 161 | 09-21 | same lineage, no markdown, no LB claim above 0.947 |
| `evgendvorkin/biohub-0-947-lb-proxy-score-0-9490` | 131 | 09-22 | **explicitly 0.947** — equal to ours, not above |
| `flexonafft/biohub-lineage-forge-precision-tracking` | 106 | 09-22 | same lineage, no LB claim above 0.947 |
| `anvithpothula/biohub-x138` | 104 | 09-21 | same lineage + one extra private head dataset; no LB claim |

`haideptry` publishes three notebooks titled **"SOTA 0.948+"**
(`biohub-sota-0-948-density-adaptive-2xt4-22m`, `biohub-0-948-sota-density-rank-2xt4-fast`,
`biohub-sota-0-948-mutual-best-density-2xt4`). **Treat the 0.948+ number as unverified:** the
author does not appear anywhere in the top 200 of the leaderboard (cutoff 0.949), and the notebooks
carry 5–23 votes. The *claim* is not evidence. **The mechanisms in them are real code, and that is
what makes them worth reading.**

### The most useful public artifact: evgendvorkin's evolution table

`evgendvorkin/biohub-0-947-lb-proxy-score-0-9490` publishes a full version history with LB and
proxy per step. Its v31 = 0.947 is our exact parent's configuration:

| ver | LB | proxy | key change |
|---|---|---|---|
| v28 | 0.942 | 0.9417 | safe-div geometry 9/14 + `SYMMETRY_TAU` 0.6 (**+0.008, the largest single jump**) |
| v29 | 0.944 | 0.9490 | Edge Feature TTA + `MOTION_RELINK_TIGHT` 5.5 |
| v30 | 0.945 | 0.9430 | Secondary Edge Feature TTA (w 0.75) |
| **v31** | **0.947** | **0.9511** | DeepCenter TTA + `SAFE_DIV_VETO` ON + PPSWEEP (tight55) |

It also confirms the public ceiling of *shared* work: its "sources" list tops out at
`sjlee101/biohub-lf-dctta` — **0.947**. Note the proxy/LB decoupling visible in its own table
(v29 proxy 0.9490 > v31 proxy 0.9511 but v30 proxy *fell* to 0.9430 while LB *rose*), which
independently corroborates our own repeated finding that the local proxy does not transfer.

## 3. Has anyone shared a next step? Yes — three concrete levers

All three sit on **our exact 0.947 base**: `haideptry`'s notebooks self-report
`source_kernel: raykkretzschmar/biohub-bidirectional-primary-union13-diagnostic-v1`,
`source_notebook_sha256: 3e65ca69…`, which is the documented upstream of our repro_059, with
`metric_hack_used: False`, `public_output_used: False`, `organizer_labels_used: False`. So these
deltas are **directly portable** to our parent rather than requiring a base change.

### Lever 1 — Mutual-best / relative-rank edge association (**recommended first**)

A small patch to the edge-logit computation, env-driven
(`BIOHUB_LB_SCORING_MODE=mutual_best`, `BIOHUB_LB_SCORING_BETA=0.20`):

```python
_lb_col_prob = torch.softmax(raw.float(), dim=0)
_lb_row_prob = torch.softmax(raw.float(), dim=1)
_lb_col_best = torch.argsort(torch.argsort(-_lb_col_prob, dim=0), dim=0) == 0
_lb_row_best = torch.argsort(torch.argsort(-_lb_row_prob, dim=1), dim=1) == 0
_lb_mutual   = _lb_col_best & _lb_row_best
_lb_rank_bonus = beta*_lb_col_best + 0.5*beta*_lb_row_best + 0.5*beta*_lb_mutual
if mode == "mutual_best":
    _lb_rank_bonus -= 0.20*beta*(~_lb_mutual)      # bounded non-mutual penalty
raw = raw + _lb_rank_bonus
```

**Why this one matters most for us.** It perturbs **edge association**, which carries ~85–90% of
the aggregate metric. Our last three causally-isolated probes (exp_055 edge-repair, exp_057 EMA,
exp_060 safe-div threshold) and the whole exp_061 arc all moved **division**, which is weighted
only 0.1 — the structural reason they were sub-precision nulls. This is the first shared lever
that targets the heavy term.

There is also a **systematic published series** by `yudaiyamauchi` probing exactly this axis, all
on the same base: **A** hard-negative margin, **B** hard-negative strong, **C**
disagreement-adaptive, **D** relative rank, **E** mutual-best association. `haideptry` carries
`BIOHUB_LB_EXPLORATION_ID = "e-mutual-best"`, i.e. **E is the variant that survived the series**.
The A–E notebooks have 0–2 votes: this is not widely picked up, so it is not priced in.

### Lever 2 — Density-adaptive grouped overrides

Per-dataset `tight_um` / `relaxed_um` / `velocity_weight` / `learned_bonus`, selected by
**measured** density:

```python
def determine_density_group(nodes_by_id):
    avg_per_frame = len(nodes_by_id) / max(len(set(n["t"] for n in nodes_by_id.values())), 1)
    return "low" if avg_per_frame < 120 else ("middle" if ... else "high")
```

| group | tight_um | relaxed_um | velocity_weight | learned_bonus |
|---|---|---|---|---|
| low | 7.25 | 11.0 | 0.5 | 3.0 |
| middle | 6.50 | 9.0 | 0.0 | 6.0 |
| high | **5.50** (= our frozen tight55) | 10.0 | 0.5 | 1.0 |

**Verified specimen-blind.** I checked explicitly: the four public test movie names appear **zero**
times in the notebook's code (only in prose), the group is decided by measured density, and test
discovery is a dynamic `TEST_DIR.iterdir()` scan. It therefore satisfies our ground-truth-free /
specimen-blind rule and would not silently break on a differently-shaped hidden set. Cell density
across embryos varies ~11× (≈61 → 703 cells/frame), so a single global `tight55` — which is what we
froze — is plausibly mis-set for three of the four movies.

### Lever 3 — DivNet 3D-CNN mitosis verification gate

`BIOHUB_DIVNET_VERIFY=1`, `BIOHUB_DIV_MIN_PROB=0.50`, weights from the public dataset
`giorgosi/biohub-divnet-v2` (5.2 MB, 455 downloads, available). This is a **model-level** addition
— the first one available to us; our entire arc so far has been post-processing on frozen weights.
**But** it acts on division, the 0.1-weighted term, so on our own evidence it is the *least* likely
of the three to register at 3-decimal LB. Rank it third.

## 4. Honest assessment

- There is **no free lunch**: no verified public notebook beats 0.947, exactly as in the 09-18
  recon. Switching base notebooks buys nothing.
- The 0.955–0.966 band is **not explained** by any public notebook I can find. Either those teams
  hold unshared work, or they are combining the shared micro-levers more aggressively than anyone
  has published. I could not establish which, and I am not going to guess.
- What *has* changed since 09-18 is that concrete, portable, **edge-side** levers are now public,
  and our entire failed arc was division-side. That is the actionable finding.
- Caveat on all three levers: their headline numbers are self-reported by an author absent from the
  top 200. Treat them as **hypotheses worth one cheap LB probe each**, not as known gains.

## 5. What this implies for the next step

The exp_061 zon arc is abandoned (five failed transports, no score ever returned). Reverting to the
exp_060 footing means: working parent stays **repro_059 = 0.947**, and exp_060's *infrastructure*
(single-config variant notebook writing one arm to `submission.csv`, the pattern that actually
scored: submission 56361673 COMPLETE) is the deployment template — it is the only transport in this
project with a proven record on the hidden rerun.

Ordering recommendation, cheapest and highest-leverage first:

1. **Mutual-best association** (β = 0.20, then 0.12) — edge-side, ~85–90% metric weight, tiny patch.
2. **Density-adaptive overrides** — generalizes the one parameter we froze; specimen-blind as written.
3. **DivNet gate** — model-level but division-weighted; lowest expected LB movement.

The **ARMED option B** (larger 0.15/0.12 safe-div move) remains outstanding but is division-side,
so on the evidence above it now ranks *below* levers 1 and 2.

No launch, submission, or implementation is authorized by this document. Any successor goes through
the normal Claude-proposes / Codex-challenges / CONSENSUS + fresh admission workflow.

---

### Reproduction pointers

```bash
kaggle competitions leaderboard biohub-cell-tracking-during-development -s --page-size 200 -v
kaggle kernels list --competition biohub-cell-tracking-during-development --sort-by voteCount -v
kaggle kernels list --competition biohub-cell-tracking-during-development --search density -v
kaggle kernels pull haideptry/biohub-sota-0-948-mutual-best-density-2xt4 -p <dir> -m
kaggle kernels list --user yudaiyamauchi -v            # the A-E exploration series
```
