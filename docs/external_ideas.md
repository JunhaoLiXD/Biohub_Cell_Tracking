# External Ideas & References — techniques to steal later

A survey of public approaches for this competition and the wider cell-tracking field, kept as a
**backlog of ideas we could implement later** (not all useful now). Newest / highest-priority at the top
of each section. This complements `docs/experiments.md` (what *we* tried) with **what others do**.

## How this was gathered (honesty caveat)

- The Kaggle "Code" tab and individual notebook pages are **JavaScript-rendered**, and this environment has
  **no Kaggle API credentials**, so the notebook *source code could not be scraped*. Notebook-specific claims
  below are **inferred** from the public title + search snippets + the matching method papers — flagged
  **[inferred]**. Claims from papers / tool docs / GitHub are flagged **[sourced]**.
- To turn any of these into a concrete, code-level study, download the `.ipynb` (Kaggle "Download" on the
  notebook page, or `kaggle kernels pull <owner>/<slug>`) into the gitignored `references/` folder and we can
  read it properly — same as we already did for the two SOTA reference notebooks.
- **Key context:** the competition host is **Royer Lab (royerlab) at the Chan Zuckerberg Biohub**, authors of
  **ultrack** and **tracksdata**, and close to the **Trackastra** authors. The "intended" strong solution is
  almost certainly one of their global/learned trackers — i.e. exactly our roadmap's **Phase 2**.

## Where we stand (so the ideas below are aimed correctly)

LB best = **0.844** (converged v1 UNet detector + v2 two-pass rule-based linking, divisions OFF). Proven
**closed / LB-negative**: high-recall detection density (v2.5b), rule-based post-hoc divisions (Version 7),
isotropic grid (v4). Detection recall is ~97% and **saturated for this metric**. The remaining loss (~7%) is
**"both endpoints detected but linked wrong" — a *linking* problem** — plus the untouched `0.1·division_jaccard`
term. So the highest-ROI ideas are **learned / global linking (Phase 2)**, which also yields divisions natively.

---

## 1. Public competitor notebooks (from the Kaggle Code tab)

| notebook (author) | approach (as read) | why it matters to us |
|---|---|---|
| **Learned Graph w/ Gap Recovery** (pilkwang) | **[inferred]** builds a **candidate graph** over detections and scores edges with a **learned model**, plus a **gap-recovery** step to bridge missed detections | This is the **learned-linking / edge-classification** direction we've flagged as Phase 2, done by a competitor in-notebook. Highest-priority notebook to actually read. |
| **Data Model, EDA, Baseline** (pilkwang) | **[inferred]** dataset/graph EDA + a simple baseline | Sanity-check our data assumptions; likely low novelty (we've done our own EDA). |
| **Classical Baseline** (xiaoleilian) | **[inferred]** classical detect + nearest-neighbour link | Same family as our v0; low novelty. |
| **Multi-Scale Blob Tracking / robust centroids** | **[inferred]** multi-scale DoG/LoG blob detection + robust centroid + baseline linking | Same family as our reference DoG detector (LB 0.835); detection is saturated for us, low priority. |
| **Getting Started w/ Nearest Neighbor** (inversion, host) | **[sourced]** official NN starter | The baseline everyone starts from; we're well past it. |

**Already in `references/` (gitignored, studied):** rule-based DoG detector (LB 0.835) and UNet-on-pooled-grid
detector with physical NMS (LB 0.843) — both use the **same two-pass motion linking we adopted**. Our converged
v1 (0.844) already matches the 0.843 reference, so more *detector* copying has little headroom; the gap to a
higher score is **linking + divisions**.

Source: [Kaggle competition code tab](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/code),
[pilkwang learned-graph notebook](https://www.kaggle.com/code/pilkwang/biohub-cell-tracking-learned-graph-w-gap-recovery).

---

## 2. Learned linking (Phase 2 — the top lever)

The remaining loss is dense-field identity swaps that a distance-greedy Hungarian can't fix. Learned association
models the *appearance + motion context* to pick correct edges, and several handle **divisions natively**.

- **Trackastra** — **[sourced]** transformer that learns **pairwise cell associations within a temporal window**
  from annotated tracks; **models dividing cells** so even *greedy* linking gives correct lineages; ships
  **pretrained models** (bacteria / cell-culture / particles) usable out of the box; **won the 7th Cell Tracking
  Challenge (ISBI 2024, generalizable linking)**. Operates on detections (not dense images) → cheap. **This is
  the single best fit for us**: we already have high-recall detections; Trackastra would replace the two-pass
  Hungarian *and* deliver the division term. Offline-packageable (needs torch, already present, + a small model
  checkpoint). Repo: `weigertlab/trackastra`. Paper: arXiv:2405.15700 (ECCV 2024).
  - *Two modes:* use the **pretrained** model zero-shot first (fast test); if promising, **fine-tune on the 199
    train pairs** (we have GT edges + divisions) for a specimen-specific model.
- **GNN edge classification** — **[sourced]** (Ben-Haim & Riklin-Raviv, ECCV 2022, arXiv:2202.04731) model the
  whole sequence as a graph, cast tracking as **binary "active edge" classification**, extract tracks as maximal
  paths. This is very likely what the pilkwang notebook approximates. Heavier to train than adopting Trackastra.
- **Practical note:** both need **negative examples** (wrong candidate edges). Our sparse GT gives positives for
  free; generate negatives from near-miss candidates within the gate.

Sources: [Trackastra (arXiv)](https://arxiv.org/abs/2405.15700), [Trackastra repo](https://github.com/weigertlab/trackastra),
[GNN cell tracking (arXiv)](https://arxiv.org/abs/2202.04731).

---

## 3. Global / ILP tracking (host's own tools — strong signal)

Instead of frame-to-frame greedy linking, solve the **whole lineage jointly** as an optimization. These handle
divisions as first-class (a node with 2 children is just an allowed configuration with a cost).

- **ultrack** — **[sourced]** the **host lab's** tracker. Builds **multiple segmentation/linking hypotheses** and
  solves an **Integer Linear Program** for segments + lineages jointly; robust under segmentation uncertainty;
  works **with or without deep learning**; scales to **3D+t, millions of instances**. Nature Methods 2025. Because
  the organizers wrote it, the data is essentially "designed" to be tractable by it → worth a serious look.
  Repo: `royerlab/ultrack`. **Caveat:** ultrack expects segmentation hypotheses / label images; we only have
  centroids — we'd feed point-based or small-region hypotheses, or pair it with a cheap segmentation (e.g.
  threshold blobs around detections).
- **motile** — **[sourced/known]** lighter ILP tracker on a candidate graph with explicit **appearance/motion/
  division costs**; easier to drop onto our existing per-frame centroids than ultrack. Good middle ground between
  our rule-based linker and full ultrack.
- **tracksdata** — **[sourced]** host lab's **graph data structure for multi-object tracking**: nodes/edges with
  arbitrary attributes, **built-in NN and ILP solvers**, **Cell-Tracking-Challenge format** + **evaluation-metric
  integration**. Could **replace our hand-rolled `TrackGraph`/linking code** and give us an ILP solver + a local
  scorer matching the official metric for free. Repo: `royerlab/tracksdata`.
- **Solver / offline concern:** ILP needs a solver. **Gurobi** (license, likely not offline-friendly on Kaggle)
  vs open **CBC / HiGHS** (pip-installable, wheel-packageable). Verify the chosen tool runs with an open solver
  under **internet OFF** before committing an LB slot.

Sources: [ultrack repo](https://github.com/royerlab/ultrack),
[Ultrack (Nature Methods)](https://www.nature.com/articles/s41592-025-02778-0),
[tracksdata repo](https://github.com/royerlab/tracksdata).

---

## 4. Detection-side ideas (lower priority — detection is saturated for our metric)

Kept only because detector *quality* (not recall) was our last positive lever (v1b +0.017). Recall pushes are
proven LB-negative, so only **localization precision / generalization** ideas belong here.

- **Distance-map regression + graph matching (KIT-GE / EmbedTrack family)** — **[sourced]** CNN predicts a
  **cell-distance / boundary map**; instances via watershed; then graph matching links them (arXiv:2004.01486,
  and EmbedTrack for embedding-based joint segment+track). More precise instance centers than heatmap peaks in
  dense fields — *might* help the dense `44b6_` specimen where our peaks merge. Speculative; only if the detector
  becomes the bottleneck again.
- **Test-time augmentation (TTA)** for the detector — average heatmaps over flips/rotations. Cheap, sometimes a
  small free localization gain. Untried by us.

Source: [CNN distance + graph matching (arXiv)](https://arxiv.org/abs/2004.01486).

---

## 5. Divisions (only via Phase 2, per our own findings)

Rule-based post-hoc divisions are **closed** (Version 7 net LB-negative). The `0.1·division_jaccard` term is only
reachable through a tracker that **models splits jointly** — i.e. **Trackastra** (native), **ultrack/motile**
(division cost/hypothesis). Every idea in §2–§3 gives divisions "for free," which is the main reason they beat
adding a division rider to our current 1:1 linker. Our one untried *standalone* discriminator (speculative): the
**UNet heatmap intensity at the mother** (dividing cells brighten/round) as a feature — but only worth it inside a
learned model, not another geometric gate.

---

## 6. Offline-packaging constraints (gate on ALL of the above)

Submissions rerun with **internet OFF**. Any new dependency must be **pip-downloaded as wheels** into a Kaggle
dataset (like our existing `zarr3-offline`) and installed with `--no-index --find-links`. Check before investing:

- **Trackastra:** torch (present) + package + a **pretrained checkpoint** (ship as a dataset). Likely the easiest
  to package. ✅ most promising.
- **ultrack / motile / tracksdata:** pure-Python + an **ILP solver**. Confirm an **open solver (CBC/HiGHS)** works
  offline — Gurobi's license flow probably won't. This is the main packaging risk.
- Always **verify end-to-end with internet OFF** before an LB slot (our standing rule).

---

## 7. Prioritized shortlist (mapped to our roadmap)

1. **Read the pilkwang "Learned Graph w/ Gap Recovery" notebook** (download into `references/`) — a competitor's
   in-notebook learned linking; cheapest way to see what's working *for this exact data/metric*.
2. **Trackastra, pretrained, zero-shot** on our existing detections — one experiment; if edge-J beats the v2
   two-pass linker locally, it's the Phase 2 winner *and* unlocks divisions. Package check = torch + a checkpoint.
3. **Trackastra fine-tuned** on the 199 train pairs, if zero-shot is promising.
4. **tracksdata** to replace our graph/linking plumbing + get an official-metric-aligned local scorer and an ILP
   solver in one library (infrastructure win even if the algorithm doesn't change).
5. **ultrack / motile ILP** as the heavier global-optimization alternative if learned linking plateaus — highest
   ceiling, highest packaging + integration cost (needs hypotheses + an offline ILP solver).

Everything here targets the **linking + division** loss, which is where the LB headroom now is; the detector
(0.844, matching the 0.843 reference) is not the bottleneck.
