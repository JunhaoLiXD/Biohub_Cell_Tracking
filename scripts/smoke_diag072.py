from __future__ import annotations

import ast
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "experiments/diag_073_fork_protected_cache_repair/kaggle_kernel/biohub-diag073-fork-protected-cache-repair.ipynb"
CACHE = ROOT / "experiments/diag_072_fork_protected_ep015_stage0/recovered_exp065_output/tracking_repo/predictions/unknown/unet_transformer_val/split_0"


def main() -> None:
    notebook = Path(sys.argv[1]) if len(sys.argv) > 1 else NB
    doc = json.loads(notebook.read_text(encoding="utf-8"))
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
    cache_block = source[source.index('# diag072: exp065 preserved'):source.index('predict_val_seconds = None')]
    assert '_v7_cache_key_path' not in cache_block
    assert '_v7_expected_key' not in cache_block
    assert '_d72_copy_verified_tree(Path(_V7_CACHE_DIR)' in source

    hash_function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_d72_tree_sha256")
    copy_function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_d72_copy_verified_tree")
    hash_ns = {"Path": Path, "_d72_hashlib": __import__("hashlib"), "_v7_shutil": shutil}
    exec(compile(ast.Module(body=[hash_function], type_ignores=[]), "<cache_hash>", "exec"), hash_ns)
    exec(compile(ast.Module(body=[copy_function], type_ignores=[]), "<cache_copy>", "exec"), hash_ns)
    expected = {
        "44b6_12dfb391": "3d889d4cc317a8442d53d3b9dd6a615c6c961517a59f78369c4b60804ac5c369",
        "44b6_267148e4": "7ab1de1f855211f70b44f9530b0b9c902428309f8112b044b988198fdb6b058d",
        "44b6_2a2eff9f": "c90a46cafce0c8042c0f2993e4ae15ef396f1f16b3ab6d1e6ae57f86eec761f9",
        "44b6_341df25f": "4dd881da8763dab6b2a788a58896f78d681a9fa09f2090380a0e9b7a6dc40cc1",
        "6bba_062c8d37": "02f8466df77d1e39eca01d01492347839a07b231bbe3d66a2e079979d5c37dad",
        "6bba_07e24132": "b3a5b8040d19d875ecf7f84c4d615de51b4eb353c5ac3c7e90f5ff0021388d61",
        "6bba_085bf656": "dd26d1a3da6cf4932b1b7d99530bf60e76d339b99a4e951c163167367effd157",
        "6bba_09961292": "4addb2ddd58448da91d6d3149bc117f79008bf5774dc3a75dbafd33a632e424a",
    }
    actual = {p.stem: hash_ns["_d72_tree_sha256"](p) for p in sorted(CACHE.glob("*.geff"))}
    assert actual == expected
    with tempfile.TemporaryDirectory() as tmp:
        copied = Path(tmp) / "copy.geff"
        hash_ns["_d72_copy_verified_tree"](
            CACHE / "44b6_12dfb391.geff", copied, expected["44b6_12dfb391"]
        )
        assert hash_ns["_d72_tree_sha256"](copied) == expected["44b6_12dfb391"]
        try:
            hash_ns["_d72_copy_verified_tree"](
                CACHE / "44b6_12dfb391.geff", copied, expected["44b6_12dfb391"]
            )
        except RuntimeError as exc:
            assert "pre-existing cache destination" in str(exc)
        else:
            raise AssertionError("pre-existing destination was silently reused")
        first_file = next(p for p in copied.rglob("*") if p.is_file())
        first_file.write_bytes(first_file.read_bytes() + b"tamper")
        assert hash_ns["_d72_tree_sha256"](copied) != expected["44b6_12dfb391"]
    for i, cell in enumerate(doc["cells"]):
        compile("".join(cell.get("source", "")), f"<cell{i}>", "exec")
    print("PASS: diag073 cache manifest/copy repair plus fork protection and primary-only gates")


if __name__ == "__main__":
    main()
