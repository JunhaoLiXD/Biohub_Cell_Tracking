"""Generate ``parent_scorer.py`` by lifting the parent's scorer functions **verbatim**.

The metric is never reimplemented. This tool AST-extracts the exact source segments of the scoring
functions from the ``exp_064`` snapshot notebook and writes them into ``parent_scorer.py`` unchanged,
so byte-identity holds by construction; ``tests/test_exp067_scorer_parity.py`` re-verifies it
independently.

Usage::

    python -m scripts.exp067.extract_parent_scorer --check
    python -m scripts.exp067.extract_parent_scorer --write
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

PARENT_NOTEBOOK = Path("experiments/exp_064_x138_verbatim_repro/snapshot/source/biohub-x138.ipynb")
SCORER_CELL = 8
TARGET = Path("scripts/exp067/parent_scorer.py")

FUNCTIONS: tuple[str, ...] = (
    "match_nodes_bipartite",
    "compute_edge_confusion",
    "edge_jaccard",
    "adjusted_jaccard",
    "weakly_connected_components",
    "compute_division_confusion",
    "decompose_errors",
    "graph_to_plain",
    "nodes_by_id_to_plain",
    "score_sample",
    "aggregate_official",
)

HEADER = '''"""The parent's scorer, lifted verbatim from biohub-x138 cell {cell}.

DO NOT EDIT. Regenerate with ``python -m scripts.exp067.extract_parent_scorer --write``.

Generated from {notebook}
cell {cell} sha256 {cell_sha}

These functions keep the parent's own **partial-label** semantics: an edge between two unmatched
predicted nodes is neither a true nor a false positive, and unmatched nodes cost only through the
one-sided node-count factor. The stricter training mask in ``supervise.py`` is a different predicate
and is never substituted in here (codex_challenge_v1 item 7).

Module globals below reproduce the parent's resolved validator configuration (cell 7:13-15, cell 5:9).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

VOXEL_SCALE_UM = (1.625, 0.40625, 0.40625)
VALIDATOR_MATCH_RADIUS_UM = 7.0
VALIDATOR_NODE_COUNT_PENALTY_A = 0.1
VALIDATOR_DIVISION_WEIGHT = 0.1

'''


def read_cell(notebook: Path, index: int) -> str:
    payload = json.loads(notebook.read_text(encoding="utf-8"))
    return "".join(payload["cells"][index]["source"])


def extract(source: str, names: tuple[str, ...]) -> dict[str, str]:
    tree = ast.parse(source)
    found: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            found[node.name] = ast.get_source_segment(source, node, padded=False)
    missing = [name for name in names if name not in found]
    if missing:
        raise SystemExit(f"scorer functions not found in the parent cell: {missing}")
    return found


def render(notebook: Path) -> str:
    import hashlib

    cell_source = read_cell(notebook, SCORER_CELL)
    segments = extract(cell_source, FUNCTIONS)
    header = HEADER.format(
        cell=SCORER_CELL,
        notebook=notebook.as_posix(),
        cell_sha=hashlib.sha256(cell_source.encode("utf-8")).hexdigest(),
    )
    body = "\n\n".join(segments[name] for name in FUNCTIONS)
    return header + "\n" + body + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", default=str(PARENT_NOTEBOOK))
    parser.add_argument("--target", default=str(TARGET))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = render(Path(args.notebook))
    target = Path(args.target)
    if args.write:
        target.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"wrote {target} ({len(rendered)} bytes)")
        return 0
    if args.check:
        if not target.exists():
            print(f"{target} does not exist")
            return 1
        current = target.read_text(encoding="utf-8")
        if current != rendered:
            print(f"{target} differs from the parent notebook extraction")
            return 1
        print(f"{target} matches the parent notebook extraction")
        return 0
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
