"""Add a read-only final validation graph export to the active reproduction notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / ".private" / "current" / "repro_public_0933.ipynb"


notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))

config_source = "".join(notebook["cells"][4]["source"])
config_anchor = 'os.environ["BIOHUB_RUN_OUTPUT_DIAGNOSTICS"] = "0"'
config_replacement = (
    'os.environ["BIOHUB_FINAL_VALIDATION_GRAPH_EXPORT"] = "1"\n'
    + config_anchor
)
if config_source.count(config_anchor) != 1:
    raise RuntimeError("Expected one final graph export configuration anchor")
if "BIOHUB_FINAL_VALIDATION_GRAPH_EXPORT" not in config_source:
    config_source = config_source.replace(config_anchor, config_replacement, 1)
notebook["cells"][4]["source"] = config_source.splitlines(keepends=True)

validator_source = "".join(notebook["cells"][20]["source"])
validator_anchor = '''        finally:
            globals()["TEST_DIR"] = _real_test_dir
        pred_nodes_plain = nodes_by_id_to_plain(processed_nodes)
'''
validator_replacement = '''        finally:
            globals()["TEST_DIR"] = _real_test_dir

        # Read-only export of the exact post-processing graph used by the validator.
        if os.environ.get("BIOHUB_FINAL_VALIDATION_GRAPH_EXPORT", "0") == "1":
            import gzip as _final_graph_gzip
            import hashlib as _final_graph_hashlib

            _final_graph_dir = WORKING_DIR / "final_validation_graphs"
            _final_graph_dir.mkdir(parents=True, exist_ok=True)
            _final_graph_path = _final_graph_dir / f"{stem}.json.gz"
            _final_graph_payload = {
                "schema_version": 1,
                "dataset": stem,
                "stage": "post_filter_output_graph_pre_validator_scoring",
                "nodes": [
                    [
                        int(node_id),
                        int(node["t"]),
                        float(node["z"]),
                        float(node["y"]),
                        float(node["x"]),
                    ]
                    for node_id, node in sorted(processed_nodes.items())
                ],
                "edges": sorted(
                    [int(edge["source_id"]), int(edge["target_id"])]
                    for edge in processed_edges
                ),
            }
            with _final_graph_gzip.open(
                _final_graph_path, "wt", encoding="utf-8"
            ) as _final_graph_handle:
                _controller_json_text = json.dumps(
                    _final_graph_payload, separators=(",", ":"), sort_keys=True
                )
                _final_graph_handle.write(_controller_json_text)
            _final_graph_summary = {
                "schema_version": 1,
                "dataset": stem,
                "stage": _final_graph_payload["stage"],
                "nodes": len(_final_graph_payload["nodes"]),
                "edges": len(_final_graph_payload["edges"]),
                "sha256": _final_graph_hashlib.sha256(
                    _final_graph_path.read_bytes()
                ).hexdigest(),
            }
            with (WORKING_DIR / "final_validation_graph_summary.jsonl").open(
                "a", encoding="utf-8"
            ) as _final_graph_summary_handle:
                _final_graph_summary_handle.write(
                    json.dumps(_final_graph_summary, sort_keys=True) + "\\n"
                )

        pred_nodes_plain = nodes_by_id_to_plain(processed_nodes)
'''
if "post_filter_output_graph_pre_validator_scoring" not in validator_source:
    if validator_source.count(validator_anchor) != 1:
        raise RuntimeError("Expected one validator final graph export anchor")
    validator_source = validator_source.replace(validator_anchor, validator_replacement, 1)
notebook["cells"][20]["source"] = validator_source.splitlines(keepends=True)

contract_source = "".join(notebook["cells"][23]["source"])
constant_anchor = "_CONTROLLER_EXPECTED_PREILP_DATASETS = 20"
if "_CONTROLLER_EXPECTED_FINAL_VALIDATION_GRAPHS" not in contract_source:
    contract_source = contract_source.replace(
        constant_anchor,
        constant_anchor + "\n_CONTROLLER_EXPECTED_FINAL_VALIDATION_GRAPHS = 16",
        1,
    )

summary_anchor = "\ndef _controller_score_summary(records):"
summary_block = '''
_controller_final_graph_summary_path = (
    WORKING_DIR / "final_validation_graph_summary.jsonl"
)
_controller_final_graph_records = []
if _controller_final_graph_summary_path.is_file():
    _controller_final_graph_records = [
        _controller_json.loads(line)
        for line in _controller_final_graph_summary_path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
_controller_final_graph_files = {
    path.name.removesuffix(".json.gz"): path
    for path in (WORKING_DIR / "final_validation_graphs").glob("*.json.gz")
}
_controller_final_graph_datasets = [
    str(record.get("dataset", ""))
    for record in _controller_final_graph_records
]
_controller_final_graph_hashes_match = all(
    dataset in _controller_final_graph_files
    and _controller_hashlib.sha256(
        _controller_final_graph_files[dataset].read_bytes()
    ).hexdigest() == str(record.get("sha256", ""))
    for dataset, record in zip(
        _controller_final_graph_datasets, _controller_final_graph_records
    )
)
_controller_final_graph_summary = {
    "expected_datasets": len(_controller_val_stem_set),
    "summary_records": len(_controller_final_graph_records),
    "artifact_files": len(_controller_final_graph_files),
    "datasets_exact": (
        len(_controller_final_graph_datasets)
        == len(set(_controller_final_graph_datasets))
        and set(_controller_final_graph_datasets) == _controller_val_stem_set
        and set(_controller_final_graph_files) == _controller_val_stem_set
    ),
    "graphs_nonempty": bool(_controller_final_graph_records)
    and all(
        int(record.get("nodes", 0)) > 0
        and int(record.get("edges", 0)) > 0
        for record in _controller_final_graph_records
    ),
    "stage_exact": bool(_controller_final_graph_records)
    and all(
        record.get("stage")
        == "post_filter_output_graph_pre_validator_scoring"
        for record in _controller_final_graph_records
    ),
    "hashes_match": bool(_controller_final_graph_records)
    and _controller_final_graph_hashes_match,
}
'''
if "_controller_final_graph_summary_path" not in contract_source:
    if contract_source.count(summary_anchor) != 1:
        raise RuntimeError("Expected one controller summary insertion anchor")
    contract_source = contract_source.replace(
        summary_anchor, "\n" + summary_block + summary_anchor, 1
    )

checks_anchor = '''    "preilp_edge_audit_hashes_match": bool(
        _controller_preilp_summary["hashes_match"]
    ),
'''
checks_block = checks_anchor + '''    "final_validation_graph_export_enabled": (
        os.environ.get("BIOHUB_FINAL_VALIDATION_GRAPH_EXPORT", "0") == "1"
    ),
    "final_validation_graph_datasets_exact": bool(
        _controller_final_graph_summary["datasets_exact"]
    ) and len(_controller_val_stem_set) == _CONTROLLER_EXPECTED_FINAL_VALIDATION_GRAPHS,
    "final_validation_graphs_nonempty": bool(
        _controller_final_graph_summary["graphs_nonempty"]
    ),
    "final_validation_graph_stage_exact": bool(
        _controller_final_graph_summary["stage_exact"]
    ),
    "final_validation_graph_hashes_match": bool(
        _controller_final_graph_summary["hashes_match"]
    ),
'''
if '"final_validation_graph_export_enabled"' not in contract_source:
    if contract_source.count(checks_anchor) != 1:
        raise RuntimeError("Expected one controller checks insertion anchor")
    contract_source = contract_source.replace(checks_anchor, checks_block, 1)

passed_anchor = "_controller_preilp_export_passed = _controller_validation_contract_passed"
if "_controller_final_validation_graph_export_passed" not in contract_source:
    contract_source = contract_source.replace(
        passed_anchor,
        passed_anchor
        + "\n_controller_final_validation_graph_export_passed = "
        + "_controller_validation_contract_passed",
        1,
    )

metrics_anchor = '''        "preilp_export_passed": _controller_preilp_export_passed,
        "preilp_edge_audit": _controller_preilp_summary,
'''
metrics_block = '''        "preilp_export_passed": _controller_preilp_export_passed,
        "final_validation_graph_export_passed": _controller_final_validation_graph_export_passed,
        "preilp_edge_audit": _controller_preilp_summary,
        "final_validation_graph_export": _controller_final_graph_summary,
'''
if '"final_validation_graph_export_passed"' not in contract_source:
    if contract_source.count(metrics_anchor) != 1:
        raise RuntimeError("Expected one controller metrics insertion anchor")
    contract_source = contract_source.replace(metrics_anchor, metrics_block, 1)

notebook["cells"][23]["source"] = contract_source.splitlines(keepends=True)
NOTEBOOK.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
print(NOTEBOOK)
