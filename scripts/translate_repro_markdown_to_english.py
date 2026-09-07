from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / ".private" / "current" / "repro_public_0933.ipynb"

ENGLISH_MARKDOWN = {
    "fe725c59": """# Biohub Cell Tracking — Dual-Seed Harmonic Bidirectional Fusion

This is an annotated working copy of a strong public solution for the competition.

The active experiment is a controlled reproduction gate, not promotion evidence. Its main components are:

- a TemporalUNet3D cell detector;
- a node transformer for adjacent-frame association scores;
- an ILP lineage-graph solver;
- a DeepCenter veto for uncertain recovered nodes;
- a two-seed primary/secondary ensemble;
- harmonic bidirectional association fusion.
""",
    "a4bbd0b8": """## 1. Global pipeline configuration

This cell defines the effective runtime configuration through environment variables. It performs no inference.

The main controls cover the detection threshold, ILP appearance/disappearance/division costs, gap closing, safe-division geometry, DeepCenter vetoes, bidirectional association fusion, and the frame-retention fallback. Later runtime guards verify the exact effective values so accidental edits fail closed.

The selected reproduction uses secondary detection weight 0.81, secondary edge weight 0.15, bidirectional edge weight 0.15, gap-close radius 5.8 µm, and the DeepCenter veto. The printed preset and score-axis labels are descriptive; runtime variables are authoritative.
""",
    "3c58fe33": """# Team Fusion v6 — Optimal Balance

Embedded validation proxy: **0.9382** (`adjusted_edge_jaccard=0.9215`, `division_jaccard=0.1667`).

Key effective parameters:

| Parameter | Value | Purpose |
|---|---:|---|
| Secondary detection weight | 0.81 | Primary/secondary detection balance |
| Bidirectional weight | 0.15 | Limit distortion from reverse associations |
| Gap-close radius | 5.8 µm | Recover short gaps conservatively |
| Detection threshold | 0.965 | Candidate confidence threshold |
| ILP disappearance cost | 2.0 | Discourage fragmented tracks |
| Safe-division geometry | 7.0/12.0 µm | Conservative division recovery |

These train-derived proxy values are optimistic because the frozen feature extractors saw the training videos. They are used only as a reproduction gate, not as a leaderboard claim.
""",
    "dfdd4397": """## 2. Configuration guard

This cell compares the effective environment variables against the reviewed reproduction settings. It checks numerical thresholds and weights as well as categorical fusion modes. Any mismatch raises an exception before expensive work begins; an exact match prints `Configuration guard: PASS`.
""",
    "ab00a07b": """## 3. Imports, paths, and resolved configuration

This cell imports the required libraries, locates the competition input, and resolves all environment-backed parameters into Python values. It defines the test, working, repository, submission, and diagnostics paths. The final JSON display reports the effective configuration used by later cells.
""",
    "0feecfc4": """## 4. Offline dependencies, model discovery, and source integrity

This cell prepares the inference environment without using the internet. It:

1. discovers offline wheel directories in attached Kaggle datasets;
2. installs only missing graph, Zarr, ILP, and serialization dependencies with dependency resolution disabled;
3. materializes the reviewed inference repository and primary checkpoint;
4. verifies every tracked Python source file against the source-integrity manifest;
5. verifies the primary, secondary-seed, and DeepCenter checkpoint SHA256 values;
6. configures the secondary model and ensemble weights; and
7. writes a runtime integrity receipt.

PyTorch is intentionally not replaced by this dependency step. Hardware compatibility is checked separately before inference.
""",
    "c7c8f170": """## 5. Inference patches and parallel prediction

This cell first performs a hardware preflight. The active reproduction requires Kaggle T4 x2: two visible CUDA devices, each with compute capability at least 7.0. This prevents the current PyTorch build from reaching inference on an incompatible P100.

The cell then applies the reviewed source patches for eight-view planar TTA, secondary-model blending, frame-retention fallback, harmonic bidirectional fusion, and coordinate diagnostics. With two GPUs, test videos are split into independent subprocess shards by video; each process sees exactly one GPU. Output coverage and overlap are verified before the shard directories are merged. A shard failure terminates its peer and fails the notebook.
""",
    "e8272f12": """## 6. Graph post-processing and submission generation

This cell converts prediction graphs into the final competition CSV. The post-processing sequence enforces temporal and distance-valid edges, motion-aware relinking, one-frame and strict two-frame gap recovery, conservative safe divisions, isolated-node pruning, short-track filtering, and optional line-fit coordinate smoothing.

DeepCenter is used only as an add-only veto for uncertain gap or division repairs. Every added node and edge is checked against topology and geometry constraints. The final writer emits only valid node and edge rows that reference existing nodes and cover every test movie.
""",
    "a8042e3d": """## 7. Submission and frame-retention audit

This label-free audit validates the completed `submission.csv` and all `retention_guard_*.jsonl` diagnostics. It checks the exact schema, contiguous row IDs, test-dataset coverage, unique `(dataset, frame)` diagnostics, retention-decision consistency, non-negative coordinates, valid node references, strictly adjacent-frame edges, maximum indegree one, and maximum outdegree two.

The resulting report records effective parameters, per-movie retention statistics, submission SHA256, topology counts, and an evidence-derived `graph_audit.complete` flag. It does not use ground truth and does not make an automated no-metric-hack claim.
""",
    "253ab114": """## 8. Held-out training-video validator inference

This diagnostic validator selects a small deterministic sample from the competition training split while excluding any stem present in the test split. Selection is grouped by specimen prefix and prioritizes videos containing a ground-truth division so both `44b6` and `6bba` contribute division evidence.

The selected stems are processed through the same reviewed inference pipeline. On T4 x2, validation videos are split into two independent GPU shards and verified before merging. This validator does not alter the test submission.
""",
    "0d1b5538": """## 9. Official-metric proxy calculation

This cell evaluates the held-out training-video predictions with the competition metric structure. It performs per-frame bipartite node matching in physical coordinates, computes edge TP/FP/FN, applies the node-count-adjusted edge Jaccard, computes organizer-compatible division confusion, and aggregates

`score = adjusted_edge_jaccard + 0.1 * division_jaccard`.

It also reports missed and spurious nodes, recovered and fragmented edges, detection losses, and wrong associations. Metrics are written per specimen and in aggregate. Because the frozen models saw training videos, absolute values are optimistic and are used only to verify reproduction consistency.
""",
    "4b9cb475": """## 10. Resolved pipeline manifest

This final diagnostic cell prints the actual runtime state of the secondary model, bidirectional fusion, DeepCenter veto, safe-division thresholds, validator, and hardware. Its purpose is to catch silent fallbacks where a requested component was not loaded or activated. The structured controller contract in the final code cell converts these checks into `metrics.json`.
""",
}


def main() -> int:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    found: set[str] = set()
    for cell in notebook["cells"]:
        cell_id = cell.get("id")
        replacement = ENGLISH_MARKDOWN.get(cell_id)
        if replacement is None:
            continue
        cell["source"] = replacement.splitlines(keepends=True)
        found.add(cell_id)

    missing = sorted(set(ENGLISH_MARKDOWN) - found)
    if missing:
        raise RuntimeError(f"Expected markdown cell IDs are missing: {missing}")

    NOTEBOOK_PATH.write_text(
        json.dumps(notebook, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Translated {len(found)} active markdown cells to English: {NOTEBOOK_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
