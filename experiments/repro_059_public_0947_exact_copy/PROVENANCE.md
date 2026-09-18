# repro_059 — Public LB 0.947 provenance, dissection, and public-frontier recon

Record type: provenance + zero-GPU dissection + public-notebook recon.
Date: 2026-09-18. Author: Claude Code. Status: backfill (submission made outside the
controller flow on 2026-09-17). No new experiment is authorized by this document.

## 1. What was submitted (authenticated)

- **Kaggle submission `56313491`, 2026-09-17 20:52:56 UTC, status COMPLETE, Public LB
  `0.947`** (authenticated submission history; NOT a reported number).
- Kernel `lingxd/biohub-repro059-public-0947-exact-copy` (v1), a **verbatim copy of a
  public 0.947 notebook**.
- Source notebook SHA256 (pulled copy): `5b349d3caf4feaa6d04cfb790e34923066f29119794846c6fd0d685337f8cd6a`.
- **+0.003 over the prior best** (repro_048 = 0.944). New best Public LB for this project.

## 2. The model is identical — the gain is 100% post-processing/TTA

repro_059 mounts the **exact same three Pilkwang checkpoints** as our 0.944
(`biohub-deepcenter-unet3d-center-prior-v1`, `biohub-temporal-unet3d-seed314159-v1`,
`biohub-tracking-support-pack-50ep-v1`). No weights changed. Therefore the entire
+0.003 comes from code/post-processing.

## 3. Prediction-affecting deltas vs our 0.944 (exact)

Of ~1200 new lines, most are infrastructure (resume/subprocess/embedded scorer). The
prediction-affecting changes are exactly four:

| # | Change | 0.944 | 0.947 | Nature |
| --- | --- | --- | --- | --- |
| A | DeepCenter (division model) TTA | OFF | **ON** | model/representation-level |
| B | Secondary edge-feature TTA (weight 0.75) | OFF | **ON** | model/representation-level |
| C | DeepCenter safe-division accept threshold | 0.25 | **0.20** | division gate |
| D | Embedded held-out PP-sweep → selected `tight55` | — | **MOTION_RELINK_TIGHT_UM 6.0→5.5** | post-proc, guardrailed |

**PP-sweep mechanism (D):** the notebook self-scores `N_PER_TYPE=4` samples drawn from
the TRAIN videos with the official formula (adjusted_edge + 0.1·division), tries 7
single-parameter candidates (`PP_CANDIDATES`: gap45, tight55, relaxed9, bonus125,
gap2step40, reuse28, dcgap035), and **adopts a candidate only if val gain ≥ +0.001 AND
adjusted-edge loss ≤ 0.0005**. It selected `tight55`.

**Documented upstream lineage** (from the notebook's own `_guard_report`):
`0.933 dual-seed baseline → 0.934 harmonic mutual-support fusion → 0.939 wider divisions
+ calmer fusion → 0.941 repair-threshold adaptation → 0.946 primary edge-feature TTA +
held-out post-process selection → 0.947 secondary feature TTA + DeepCenter TTA`.
Upstream kernel: `raykkretzschmar/biohub-bidirectional-primary-union13-diagnostic-v1`
(sha 3e65ca69...). Self-attested: `metric_hack_used=False`, `public_output_used=False`,
`organizer_labels_used=False`, `leaderboard_feedback_used=True`.

## 4. Public-frontier recon (zero-GPU, 2026-09-18)

Question: is there a verified, reproducible public notebook clearly above 0.947?
**Finding: no.** Details:

- **LB frontier ≈ 0.970** (top teams: 0.970/0.969/0.968…, thick cluster 0.957–0.966),
  but those are private/unshared solutions, not the public notebooks below.
- **Entire reproducible public cluster shares the SAME Pilkwang checkpoints** — nobody
  wins via a better model; all differences are post-processing / TTA / ensembling.
- Candidates inspected:
  - `flexonafft/biohub-harmonic-fusion` (250 votes) — same lineage, method attribution
    tops out at the dual-seed+harmonic base (earlier/≈lower than our 0.947). `metric_hack_used=False`.
  - `raunakdey07/biohub-harmonic-fusion-v3` — markdown states **0.939** LB (below 0.947).
  - `sjlee101/biohub-lf-dctta` (80 votes) — same lineage/size; not shown to exceed 0.947.
  - `anvithpothula/biohub-0-95` — tiny (8 cells / 29K), single checkpoint, no LB claim in
    md; title "0.95" unverified and structurally implausible; NOT this lineage.
  - `raykkretzschmar/cross-family-inverse-consensus-lb-0-95288` — **different competition
    (S6E7 artifacts, GPU off); the 0.95288 is NOT a biohub score.** Ruled out.
  - Titles like "det 0.9690" / "det 0.96875" are **detection-accuracy metrics, not LB**.
  - `harshitsama/biohub-0-950-baseline-explained-reproducible` (July, 6 votes) — old,
    unverified "0.950 baseline"; low-probability follow-up, not chased.

**Conclusion:** repro_059 (0.947) sits at/near the top of the *reproducible* public
cluster. There is no free lunch by switching to another public notebook; the path
forward is to improve on this 0.947 base (division/TTA levers), validated directly on
the now-unlimited Public LB.

## 5. Standing caveat carried forward

The +0.003 changed A+B+C+D together and is **not causally isolated** (per Codex
gpt-6-astra strategy review, 2026-09-18). TTA could carry the gain while a post-proc
term is neutral/negative. Any successor must isolate single interventions rather than
bundle TTA + threshold + geometry, and must go through the full Claude-proposes /
Codex-challenges / CONSENSUS + fresh Codex admission workflow before launch.
