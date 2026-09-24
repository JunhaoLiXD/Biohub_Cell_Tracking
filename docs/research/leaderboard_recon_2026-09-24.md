# Leaderboard recon — 2026-09-24 (supersedes the 09-23 recon's standings)

Authenticated `kaggle competitions leaderboard -d`, full download, 3888 teams,
snapshot `2026-09-24T20:03:35`. **This supersedes section 1 of
`public_frontier_recon_2026-09-23.md`, whose standings are now badly stale.**

## Where we actually stand — much worse than we thought

| | 09-23 recon | **09-24 measured** |
|---|---|---|
| total teams | not recorded | **3888** |
| rank 1 | 0.975 | 0.975 |
| rank 10 | — | 0.967 |
| rank 50 | — | 0.957 |
| rank 100 | — | 0.954 |
| **rank 200** | **0.949** | **0.953** |
| rank 300 | — | 0.950 |
| **our 0.947** | "outside the top 200" | **rank ~478** (477 teams strictly above) |

The rank-200 cutoff moved **0.949 → 0.953 in one day**. Our 0.947 is not marginally outside the top
200; it is **rank ~478 of 3888**. Any plan built on "we are 0.002 from the top 200" is obsolete —
the real gap is **0.006**.

## The decisive credibility split between the two authors

| | `haideptry` | `anvithpothula` |
|---|---|---|
| appears on the public LB | **NO — absent from all 3888 rows** | **YES — rank 62, score 0.956** |
| claim | "SOTA 0.951+", "0.948+" in notebook titles | none in the notebook text |
| votes | 5–23 | 104 |
| verifiable mechanism check | **DivNet gate provably broken** (see `exp_063/review.md`) | compliance clean, see below |

This is dispositive. `haideptry` makes headline claims, does not appear anywhere on a 3888-row
leaderboard, and ships a flagship "DivNet 3D Gate" that throws an exception on every call — their
numbers deserve no weight. `anvithpothula` claims nothing in the notebook and is **authenticated at
0.956, rank 62**.

**Recommendation: drop the haideptry family entirely. It was the wrong target.**

## `anvithpothula/biohub-x138`

Archived in-repo: `public_notebook_archive/biohub-x138.ipynb`, SHA256
`6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d`, pulled 2026-09-24.

- Same declared ancestor as our parent (`raykkretzschmar/…`, `3e65ca69…`); a diverged cousin at
  **43.2 %** line coverage of our parent (haideptry was 35.7 %).
- Same docker digest `sha256:37c64f7d…` we already run, same `NvidiaTeslaT4`, same **three Pilkwang
  checkpoints we already mount**.
- Fourth dataset `anvithpothula/biohub-v1284-head-s075` is **public and mountable** — 30 KB, 186
  downloads, 5 votes. The 09-23 recon called this "one extra **private** head dataset"; that is
  **wrong**, it is public.
- Distinctive mechanism: a **V1284 coordinate-refinement head** — *"frozen-feature coordinate
  regression at first-seen fused detection"*. This refines predicted node **coordinates**, which is
  a mechanism class we have **never** tried: every intervention in this project so far has been
  edge association, division gating or post-processing, never node position.

Compliance pre-check (ours, not the author's attestation): all four hidden-test dataset names appear
**zero** times, full or by stem; no `solution.csv` / `sample_submission` read; no network; the
notebook's own attestations record `metric_hack_used False`, `public_output_used False`,
`organizer_labels_used_for_configuration False`, `ground_truth_accessed False`.

### Open items, stated not hidden

- **x138 is not proven to be the notebook that scored 0.956.** It is a public share from a competitor
  who demonstrably reaches 0.956; their best work may be unshared. Treat "x138 ≈ 0.953–0.956" as
  plausible, not established.
- **`v1284_head.pt` training provenance is unverified**, exactly as for DivNet. It is the author's
  own trained head, publicly shared. `weights_only` appears twice in the notebook and must be
  checked before any run.
- 43 % coverage means this is **not** a small patch on our parent; porting the head alone is not a
  well-defined cheap task. Whole-pipeline reproduction is the tractable route.

## Implication

The 0.955–0.966 band the 09-23 recon called "unexplained by any public notebook" is at least
partly explained: **a rank-62 team at 0.956 has published theirs.**
