from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import ControllerError, validate_notebook


PATCH_START = "# Apply eight-view planar detection TTA before graph prediction."
PATCH_END = "def list_test_stems() -> list[str]:"
REQUIRED_TRANSFORMED_SNIPPETS = (
    "preilp_edge_audit_records: list[dict[str, object]] = []",
    'os.environ.get("BIOHUB_PREILP_EDGE_AUDIT", "0") == "1"',
    '"fused_logit": float(_audit_logits[_i, _j])',
    '"parent_rank_for_target": int(_parent_rank[_i, _j])',
    '"child_rank_for_source": int(_child_rank[_i, _j])',
    '"distance_um": _distance_um',
    '"stage": "post_fusion_pre_threshold_pre_graph_pre_ilp"',
    "candidates = sorted(",
    "all_edges.append((gi, gj, float(prob), dist))",
)


def _patch_cell_source(notebook: dict[str, object]) -> str:
    cells = notebook.get("cells", [])
    matches = [
        "".join(cell.get("source", []))
        for cell in cells
        if isinstance(cell, dict)
        and cell.get("cell_type") == "code"
        and PATCH_START in "".join(cell.get("source", []))
    ]
    if len(matches) != 1:
        raise ControllerError(
            f"Expected one runtime patch cell containing {PATCH_START!r}, found {len(matches)}"
        )
    source = matches[0]
    if PATCH_END not in source:
        raise ControllerError(f"Runtime patch cell is missing end marker {PATCH_END!r}")
    return source[source.index(PATCH_START) : source.index(PATCH_END)]


def validate_runtime_transform(notebook_path: Path, support_source: Path) -> dict[str, object]:
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    patch_code = _patch_cell_source(notebook)

    with tempfile.TemporaryDirectory(prefix="biohub_preilp_smoke_") as temp_dir:
        temp_root = Path(temp_dir)
        repo_dir = temp_root / "repo"
        working_dir = temp_root / "working"
        scripts_dir = repo_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        working_dir.mkdir()
        transformed_path = scripts_dir / "predict_unet_transformer.py"
        shutil.copy2(support_source, transformed_path)

        previous_weight = os.environ.get("BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT")
        previous_retention = os.environ.get("BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION")
        os.environ["BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT"] = "0.15"
        os.environ["BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION"] = "0.90"
        namespace = {
            "REPO_DIR": repo_dir,
            "WORKING_DIR": working_dir,
            "os": os,
        }
        try:
            exec(compile(patch_code, str(notebook_path), "exec"), namespace)
        finally:
            if previous_weight is None:
                os.environ.pop("BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT", None)
            else:
                os.environ["BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT"] = previous_weight
            if previous_retention is None:
                os.environ.pop("BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION", None)
            else:
                os.environ["BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION"] = previous_retention

        transformed = transformed_path.read_text(encoding="utf-8")
        compile(transformed, str(transformed_path), "exec")
        missing = [snippet for snippet in REQUIRED_TRANSFORMED_SNIPPETS if snippet not in transformed]
        if missing:
            raise ControllerError(f"Transformed runtime is missing required snippets: {missing}")
        audit_position = transformed.index(
            'if os.environ.get("BIOHUB_PREILP_EDGE_AUDIT", "0") == "1"'
        )
        candidate_position = transformed.index("candidates = sorted(", audit_position)
        writer_position = transformed.index("_preilp_dir = Path(", candidate_position)
        return_position = transformed.index("return coords, all_edges", writer_position)
        if not audit_position < candidate_position < writer_position < return_position:
            raise ControllerError("Pre-ILP export stage ordering is not preserved")

    return {
        "runtime_transform_compiles": True,
        "required_snippets": len(REQUIRED_TRANSFORMED_SNIPPETS),
        "stage_ordering_valid": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the notebook and its generated pre-ILP runtime patch"
    )
    parser.add_argument("notebook", type=Path)
    parser.add_argument(
        "--support-source",
        type=Path,
        default=(
            PROJECT_ROOT
            / "references"
            / "biohub-tracking-support-pack"
            / "repo"
            / "scripts"
            / "predict_unet_transformer.py"
        ),
    )
    args = parser.parse_args()
    notebook_path = args.notebook.resolve()
    support_source = args.support_source.resolve()
    try:
        notebook_result = validate_notebook(notebook_path, require_metrics_contract=True)
        runtime_result = validate_runtime_transform(notebook_path, support_source)
    except (ControllerError, OSError, ValueError, SyntaxError) as exc:
        parser.error(str(exc))
    print(json.dumps({**notebook_result, **runtime_result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
