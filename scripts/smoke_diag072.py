from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "experiments/diag_072_fork_protected_ep015_stage0/kaggle_kernel/biohub-diag072-fork-protected-stage0.ipynb"


def main() -> None:
    doc = json.loads(NB.read_text(encoding="utf-8"))
    source = "\n".join("".join(c.get("source", "")) for c in doc["cells"])
    tree = ast.parse(source)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "filter_weak_edges")
    module = ast.Module(body=[function], type_ignores=[])
    ns = {
        "np": np,
        "OUTPUT_MIN_EDGE_PROB": 0.0,
        "FORK_PROTECTED_EP_MIN_EDGE_PROB": 0.15,
    }
    exec(compile(module, "<filter_weak_edges>", "exec"), ns)
    nodes = {
        1: {"t": 1}, 2: {"t": 2}, 3: {"t": 2},
        4: {"t": 1}, 5: {"t": 2}, 6: {"t": 0}, 7: {"t": 3},
    }
    edges = [
        {"source_id": 1, "target_id": 2, "edge_prob": 0.10},
        {"source_id": 1, "target_id": 3, "edge_prob": 0.20},
        {"source_id": 4, "target_id": 5, "edge_prob": 0.10},
        {"source_id": 6, "target_id": 7, "edge_prob": None},
    ]
    stats = {"weak_edge_dropped": 0, "weak_edge_orphan_nodes": 0}
    kept_nodes, kept_edges = ns["filter_weak_edges"](nodes, edges, stats)
    pairs = {(e["source_id"], e["target_id"]) for e in kept_edges}
    assert (1, 2) in pairs, "weak fork daughter was not protected"
    assert (1, 3) in pairs, "strong fork daughter was lost"
    assert (4, 5) not in pairs, "weak non-fork edge was not pruned"
    assert (6, 7) in pairs, "probability-free edge was not exempt"
    assert stats["weak_edge_dropped"] == 1
    assert 6 in kept_nodes and 7 in kept_nodes

    assert '_V7_FAST_TIER = ("fork_protected_ep015",)' in source
    assert 'PP_SELECT_MARGIN = 99.0' in source
    assert '"confirmatory_computed": any(' in source
    assert 'assert _d72_evaluated == ["base", "fork_protected_ep015"]' in source
    assert '"leaderboard_submission_authorized": False' in source
    assert '_v9_preset_hits = []' in source
    for i, cell in enumerate(doc["cells"]):
        compile("".join(cell.get("source", "")), f"<cell{i}>", "exec")
    print("PASS: diag072 fork protection, non-fork pruning, exemptions, primary-only and no-selection gates")


if __name__ == "__main__":
    main()
