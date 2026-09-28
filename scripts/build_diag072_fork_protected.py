from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "experiments/exp_065_metric_aligned_pruning/kaggle_kernel/biohub-exp065-pruning-sweep.ipynb"
OUT = ROOT / "experiments/diag_072_fork_protected_ep015_stage0/kaggle_kernel"
KERNEL = "lingxd/biohub-diag072-fork-protected-stage0"
CACHE = "/kaggle/input/biohub-exp065-pruning-sweep/tracking_repo/predictions/unknown/unet_transformer_val/split_0"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    nb = json.loads(PARENT.read_text(encoding="utf-8"))
    parent_sha = hashlib.sha256(PARENT.read_bytes()).hexdigest()

    c0 = "".join(nb["cells"][0]["source"])
    c0 = replace_once(
        c0,
        'os.environ["BIOHUB_VAL_PRED_CACHE_DIR"] = ""',
        f'os.environ["BIOHUB_VAL_PRED_CACHE_DIR"] = "{CACHE}"',
        "cache path",
    )
    c0 = replace_once(
        c0,
        '_v9_preset_hits = sorted(_V9_INPUT_ROOT.glob("*/ppsweep_selected.json"))',
        '_v9_preset_hits = []  # diag072: never auto-load a prior selected policy',
        "preset disable",
    )
    c0 += '''

# diag072: hard one-hour process cap, armed from the first cell.
import threading as _d72_threading, os as _d72_os
_d72_watchdog = _d72_threading.Timer(3540.0, lambda: _d72_os._exit(124))
_d72_watchdog.daemon = True
_d72_watchdog.start()
'''
    nb["cells"][0]["source"] = c0

    config_index = next(
        i for i, c in enumerate(nb["cells"])
        if 'OUTPUT_MIN_EDGE_PROB = float(os.environ.get' in "".join(c.get("source", ""))
    )
    c1 = "".join(nb["cells"][config_index]["source"])
    c1 = replace_once(
        c1,
        'OUTPUT_MIN_EDGE_PROB = float(os.environ.get("BIOHUB_OUTPUT_MIN_EDGE_PROB", "0.0"))',
        'OUTPUT_MIN_EDGE_PROB = float(os.environ.get("BIOHUB_OUTPUT_MIN_EDGE_PROB", "0.0"))\n'
        'FORK_PROTECTED_EP_MIN_EDGE_PROB = float(os.environ.get("BIOHUB_FORK_PROTECTED_EP_MIN_EDGE_PROB", "0.0"))',
        "fork threshold global",
    )
    nb["cells"][config_index]["source"] = c1

    filter_index = next(
        i for i, c in enumerate(nb["cells"])
        if "def filter_weak_edges" in "".join(c.get("source", ""))
    )
    c1 = "".join(nb["cells"][filter_index]["source"])
    old_filter = '''    if OUTPUT_MIN_EDGE_PROB <= 0.0 or not edges:
        return nodes_by_id, edges
    kept_edges: list[dict[str, object]] = []
    for edge in edges:
        prob = edge.get("edge_prob")'''
    new_filter = '''    _weak_floor = max(OUTPUT_MIN_EDGE_PROB, FORK_PROTECTED_EP_MIN_EDGE_PROB)
    if _weak_floor <= 0.0 or not edges:
        return nodes_by_id, edges
    _pre_out_degree: dict[int, int] = {}
    for _edge in edges:
        _source = int(_edge["source_id"])
        _pre_out_degree[_source] = _pre_out_degree.get(_source, 0) + 1
    _protected_sources = {s for s, degree in _pre_out_degree.items() if degree == 2}
    _protected_pairs = sorted((int(e["source_id"]), int(e["target_id"])) for e in edges
                              if int(e["source_id"]) in _protected_sources)
    stats["fork_protected_sources"] = len(_protected_sources)
    stats["fork_protected_edges_expected"] = len(_protected_pairs)
    kept_edges: list[dict[str, object]] = []
    for edge in edges:
        prob = edge.get("edge_prob")'''
    c1 = replace_once(c1, old_filter, new_filter, "filter preamble")
    c1 = replace_once(
        c1,
        '        if np.isfinite(prob) and prob < OUTPUT_MIN_EDGE_PROB:',
        '        if (np.isfinite(prob) and prob < _weak_floor\n'
        '                and not (FORK_PROTECTED_EP_MIN_EDGE_PROB > 0.0\n'
        '                         and int(edge["source_id"]) in _protected_sources)):',
        "fork exemption",
    )
    c1 = replace_once(
        c1,
        '    if stats["weak_edge_dropped"] == 0:\n        return nodes_by_id, edges',
        '    _kept_pairs = {(int(e["source_id"]), int(e["target_id"])) for e in kept_edges}\n'
        '    stats["fork_protected_edges_retained"] = sum(p in _kept_pairs for p in _protected_pairs)\n'
        '    stats["fork_protection_complete"] = int(stats["fork_protected_edges_retained"] == len(_protected_pairs))\n'
        '    assert stats["fork_protection_complete"] == 1, "diag072: protected fork edge lost"\n'
        '    if stats["weak_edge_dropped"] == 0:\n        return nodes_by_id, edges',
        "fork telemetry assertion",
    )
    nb["cells"][filter_index]["source"] = c1

    validator_index = next(i for i, c in enumerate(nb["cells"])
                           if "_v7_val_pred_cache_hit = False" in "".join(c.get("source", "")))
    validator_source = "".join(nb["cells"][validator_index]["source"])
    frozen = '''_D72_EXPECTED_STEMS = {"44b6_12dfb391", "44b6_267148e4", "44b6_2a2eff9f", "44b6_341df25f", "6bba_062c8d37", "6bba_07e24132", "6bba_085bf656", "6bba_09961292"}
assert set(val_stems) == _D72_EXPECTED_STEMS, (val_stems, _D72_EXPECTED_STEMS)
assert sum(s.startswith("44b6_") for s in val_stems) == 4
assert sum(s.startswith("6bba_") for s in val_stems) == 4
assert _v7_val_pred_cache_hit, "diag072: frozen cache invalid; inference fallback prohibited"

predict_val_seconds = None
'''
    validator_source = replace_once(validator_source, "predict_val_seconds = None\n", frozen,
                                    "cache/stem fail-closed gate")
    nb["cells"][validator_index]["source"] = validator_source

    sweep_index = next(i for i, c in enumerate(nb["cells"]) if "PP_SWEEP_KEYS = [" in "".join(c.get("source", "")))
    sweep = "".join(nb["cells"][sweep_index]["source"])
    sweep = replace_once(
        sweep,
        '    "OUTPUT_MIN_EDGE_PROB", "SEG_PRUNE_MIN_PROB", "SEG_PRUNE_MAX_LEN",',
        '    "OUTPUT_MIN_EDGE_PROB", "FORK_PROTECTED_EP_MIN_EDGE_PROB", "SEG_PRUNE_MIN_PROB", "SEG_PRUNE_MAX_LEN",',
        "sweep key",
    )
    nb["cells"][sweep_index]["source"] = sweep

    candidate_index = next(
        i for i, c in enumerate(nb["cells"])
        if '"ep010": {"OUTPUT_MIN_EDGE_PROB": 0.10}' in "".join(c.get("source", ""))
        and "_V7_FAST_TIER" in "".join(c.get("source", ""))
    )
    sweep = "".join(nb["cells"][candidate_index]["source"])
    score_index = next(
        i for i, c in enumerate(nb["cells"])
        if 'row["safe_divisions_added"] = _stage_stats.get' in "".join(c.get("source", ""))
    )
    score_source = "".join(nb["cells"][score_index]["source"])
    sweep = replace_once(
        sweep,
        '    PP_CANDIDATES.update({\n        # -- L1 weak-edge output filter',
        '    PP_CANDIDATES.update({\n        "fork_protected_ep015": {"FORK_PROTECTED_EP_MIN_EDGE_PROB": 0.15},\n'
        '        # -- L1 weak-edge output filter',
        "primary candidate",
    )
    start = sweep.index("    _V7_FAST_TIER = (")
    end = sweep.index("    )", start) + len("    )")
    sweep = sweep[:start] + '    _V7_FAST_TIER = ("fork_protected_ep015",)' + sweep[end:]
    sweep = replace_once(
        sweep,
        'PP_SELECT_MARGIN = float(os.environ.get("BIOHUB_PPSWEEP_SELECT_MARGIN", "0.002"))',
        'PP_SELECT_MARGIN = 99.0  # diag072 never rewrites or selects a submission',
        "disable selection",
    )
    score_source = replace_once(
        score_source,
        '            row["safe_divisions_added"] = _stage_stats.get("safe_divisions_added", 0)',
        '            row["safe_divisions_added"] = _stage_stats.get("safe_divisions_added", 0)\n'
        '            row["pred_node_count"] = len(processed_nodes)\n'
        '            row["pred_edge_count"] = len(processed_edges)\n'
        '            row["pred_fork_count"] = sum(v == 2 for v in __import__("collections").Counter(int(e["source_id"]) for e in processed_edges).values())\n'
        '            for _d72_key in ("fork_protected_sources", "fork_protected_edges_expected", "fork_protected_edges_retained", "fork_protection_complete"):\n'
        '                row[_d72_key] = int(_stage_stats.get(_d72_key, 0))',
        "row telemetry",
    )
    nb["cells"][score_index]["source"] = score_source
    receipt = '''

# diag072 primary-only raw receipt. Final scientific gates are recomputed after collection.
_d72_rows = [r for r in validator_sample_rows if r.get("config") in {"base", "fork_protected_ep015"}]
_d72_evaluated = sorted(PP_RESULTS)
assert OUTPUT_MIN_EDGE_PROB == 0.0
assert FORK_PROTECTED_EP_MIN_EDGE_PROB == 0.0
assert _d72_evaluated == ["base", "fork_protected_ep015"], _d72_evaluated
assert selected_label == "base" and selected_config == {}
_d72_doc = {
    "schema": "diag072-primary-raw-v1",
    "primary": "fork_protected_ep015",
    "threshold": 0.15,
    "controls": ["base"],
    "rows": _d72_rows,
    "summaries": {k: v for k, v in PP_RESULTS.items() if k in {"base", "fork_protected_ep015"}},
    "runtime_contract": {"flat_floor": 0.0, "candidate_fork_floor": 0.15,
                         "evaluated_configs": _d72_evaluated,
                         "preset_loaded": FROZEN_PRESET_OVERRIDES is not None,
                         "selection_margin": PP_SELECT_MARGIN, "selected_label": selected_label},
    "confirmatory_computed": any(x not in {"base", "fork_protected_ep015"} for x in _d72_evaluated),
    "leaderboard_submission_authorized": False,
}
(WORKING_DIR / "diag072_primary_raw.json").write_text(
    json.dumps(_d72_doc, indent=2, sort_keys=True) + "\\n"
)
print("diag072: primary raw receipt written; no confirmatory arm and no selection", flush=True)
'''
    anchor = 'if FROZEN_PRESET_OVERRIDES is not None:\n'
    sweep = replace_once(sweep, anchor, receipt + "\n" + anchor, "receipt anchor")
    nb["cells"][candidate_index]["source"] = sweep

    for i, cell in enumerate(nb["cells"]):
        compile("".join(cell.get("source", "")), f"<cell{i}>", "exec")

    OUT.mkdir(parents=True, exist_ok=True)
    notebook = OUT / "biohub-diag072-fork-protected-stage0.ipynb"
    notebook.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    metadata = {
        "id": KERNEL,
        "title": KERNEL.split("/")[1],
        "code_file": notebook.name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": False,
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": [
            "pilkwang/biohub-deepcenter-unet3d-center-prior-v1",
            "pilkwang/biohub-temporal-unet3d-seed314159-v1",
            "pilkwang/biohub-tracking-support-pack-50ep-v1",
            "anvithpothula/biohub-v1284-head-s075",
        ],
        "competition_sources": ["biohub-cell-tracking-during-development"],
        "kernel_sources": ["lingxd/biohub-exp065-pruning-sweep"],
        "docker_image": "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        "docker_image_pinning_type": "original",
    }
    (OUT / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "parent": str(PARENT.relative_to(ROOT)).replace("\\", "/"),
        "parent_sha256": parent_sha,
        "notebook_sha256": hashlib.sha256(notebook.read_bytes()).hexdigest(),
        "adjudicator_sha256": hashlib.sha256((ROOT / "scripts/adjudicate_diag072.py").read_bytes()).hexdigest(),
        "primary": "fork_protected_ep015",
        "gpu_cap_hours": 1.0,
        "lb_submissions": 0,
    }
    (OUT.parent / "build_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
