"""Smoke check inference identity and negative reproduction controls without GPUs."""
import argparse
import copy
import json
import math
from pathlib import Path
from build_public_0941_ema_repro import PARENT, ROOT, build
from _bootstrap import PROJECT_ROOT
from experiment_controller.core import validate_notebook


def validate(path):
    actual = json.loads(Path(path).read_text(encoding="utf-8"))
    assert actual == build(), "Candidate differs from deterministic builder"
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    assert actual["cells"][1:-1] == parent["cells"][:-1], "Inference or validation drift"
    result = validate_notebook(Path(path), require_metrics_contract=True)
    text = "".join(actual["cells"][-1]["source"])
    # Execute only the evidence suffix using recorded parent metrics, not inference.
    suffix = text[text.index("REPRO_EXPECTED = "):text.index('(WORKING_DIR / "validation_stage_stats.json").write_text(')]
    reference = json.loads((ROOT / "experiments/exp_040_public_0941_motion_ema/artifacts/metrics.json").read_text())
    for fault in (None, "score", "specimen", "hash", "ema", "division", "integrity"):
        metrics = copy.deepcopy(reference)
        digest = metrics["metrics"]["candidate_submission_sha256"]
        if fault == "score": metrics["primary_metric"] += 1e-10
        if fault == "specimen": metrics["specimen_metrics"]["44b6"]["adjusted_edge_jaccard"] += 1e-10
        if fault == "hash": digest = "0" * 64
        if fault == "ema": metrics["metrics"]["motion_relink_ema_execution"]["6bba"]["ema_predictions"] += 1
        if fault == "division": metrics["metrics"]["division_counts"]["div_fp"] += 1
        if fault == "integrity": metrics["metrics"]["ema_candidate_gate_passed"] = False
        context = {"_metrics": metrics, "_specimens": metrics["specimen_metrics"],
                   "_ema_execution": metrics["metrics"]["motion_relink_ema_execution"],
                   "_sha256_file": lambda path: digest, "SUBMISSION_PATH": None, "_contract_math": math}
        exec(compile(suffix, "<reproduction-negative-control>", "exec"), context)
        assert context["_reproduction_passed"] is (fault is None), fault
        assert metrics["reproducible"] is (fault is None), fault
    result.update(inference_cells_identical=True, negative_controls=6, passed=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    print(json.dumps(validate(parser.parse_args().notebook), indent=2))
