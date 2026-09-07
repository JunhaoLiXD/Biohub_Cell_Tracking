from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from _bootstrap import PROJECT_ROOT  # noqa: F401
from experiment_controller.core import ControllerError, validate_notebook


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the embedded Phase-0 oracle notebook")
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args()

    summary = validate_notebook(args.notebook, require_metrics_contract=True)
    notebook = json.loads(args.notebook.read_text(encoding="utf-8"))
    source = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    required = (
        "def run(",
        "def _load_relevant_candidates(",
        "def _load_final_graph(",
        "def _division_confusion(",
        "def _match_nodes_bipartite(",
        "Final graph hash mismatch",
        "post_filter_output_graph_pre_validator_scoring",
        'parent_root = _find_experiment_output(search_root, FINAL_GRAPH_EXPERIMENT_ID)',
        "final_graph_root = parent_root",
        '"candidate_id_space_valid": True',
        '"pruned_endpoint_rows": 0',
        '"invalid_distance_rows": 0',
        "Candidate/final-graph retained node-id mapping failed metadata checks",
        "payload = run()",
        "/kaggle/working/metrics.json",
    )
    missing = [snippet for snippet in required if snippet not in source]
    if missing:
        raise ControllerError(f"Embedded oracle notebook is missing required code: {missing}")
    forbidden = ("module_hits", "from run_phase0_candidate_oracle import")
    present = [snippet for snippet in forbidden if snippet in source]
    if present:
        raise ControllerError(f"Notebook still depends on unstaged external modules: {present}")
    summary["embedded_runner"] = True
    summary["candidate_id_guard"] = True
    summary["stage_aware_endpoint_guard"] = True
    summary["final_graph_hash_guard"] = True
    if args.artifact_root is not None:
        metrics = json.loads((args.artifact_root / "metrics.json").read_text(encoding="utf-8"))
        names = [
            name
            for specimen in ("44b6", "6bba")
            for name in metrics["specimen_metrics"][specimen]["samples"]
        ]
        summary_rows = [
            json.loads(line)
            for line in (args.artifact_root / "final_validation_graph_summary.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line
        ]
        summary_by_name = {row["dataset"]: row for row in summary_rows}
        retained_rows = 0
        time_mismatches = 0
        invalid_distances = 0
        mismatch_examples = []
        for name in names:
            graph_path = args.artifact_root / "final_validation_graphs" / f"{name}.json.gz"
            if hashlib.sha256(graph_path.read_bytes()).hexdigest() != summary_by_name[name]["sha256"]:
                raise ControllerError(f"Final graph hash mismatch for {name}")
            with gzip.open(graph_path, "rt", encoding="utf-8") as handle:
                graph = json.load(handle)
            node_times = {int(row[0]): int(row[1]) for row in graph["nodes"]}
            candidate_path = args.artifact_root / "preilp_edge_audit" / f"{name}.jsonl.gz"
            with gzip.open(candidate_path, "rt", encoding="utf-8") as handle:
                for line in handle:
                    row = json.loads(line)
                    source = int(row["source_id"])
                    target = int(row["target_id"])
                    if source not in node_times or target not in node_times:
                        continue
                    retained_rows += 1
                    t_src = int(row["t_src"])
                    t_tgt = int(row["t_tgt"])
                    time_mismatch = (
                        t_src != node_times[source]
                        or t_tgt != node_times[target]
                        or t_tgt != t_src + 1
                    )
                    time_mismatches += int(time_mismatch)
                    if time_mismatch and len(mismatch_examples) < 20:
                        mismatch_examples.append(
                            {
                                "dataset": name,
                                "source_id": source,
                                "target_id": target,
                                "candidate_times": [t_src, t_tgt],
                                "final_times": [node_times[source], node_times[target]],
                            }
                        )
                    distance = float(row["distance_um"])
                    invalid_distances += int(
                        not math.isfinite(distance) or distance < 0.0 or distance > 12.0 + 1e-6
                    )
        expected_time_mismatches = 17
        if retained_rows == 0 or time_mismatches != expected_time_mismatches or invalid_distances:
            raise ControllerError(
                "Same-run artifact preflight failed: "
                f"retained={retained_rows}, time_mismatches={time_mismatches}, "
                f"invalid_distances={invalid_distances}, examples={mismatch_examples}"
            )
        summary["artifact_preflight"] = {
            "datasets": len(names),
            "retained_candidate_rows": retained_rows,
            "time_mismatches": time_mismatches,
            "expected_time_mismatches": expected_time_mismatches,
            "invalid_distances": invalid_distances,
        }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
