from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

from _bootstrap import PROJECT_ROOT  # noqa: F401
from experiment_controller.core import ControllerError, validate_notebook


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate final validation graph export instrumentation")
    parser.add_argument("notebook", type=Path)
    args = parser.parse_args()

    summary = validate_notebook(args.notebook, require_metrics_contract=True)
    notebook = json.loads(args.notebook.read_text(encoding="utf-8"))
    code = [
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    ]
    for index, source in enumerate(code):
        try:
            ast.parse(source)
        except SyntaxError as exc:
            raise ControllerError(f"Code cell {index} does not compile: {exc}") from exc
    joined = "\n".join(code)
    required = (
        'os.environ["BIOHUB_FINAL_VALIDATION_GRAPH_EXPORT"] = "1"',
        'WORKING_DIR / "final_validation_graphs"',
        '"stage": "post_filter_output_graph_pre_validator_scoring"',
        '"final_validation_graph_export_passed"',
        '"final_validation_graph_hashes_match"',
        "_CONTROLLER_EXPECTED_FINAL_VALIDATION_GRAPHS = 16",
    )
    missing = [snippet for snippet in required if snippet not in joined]
    if missing:
        raise ControllerError(f"Final validation graph export is missing required code: {missing}")
    summary["final_graph_export"] = True
    summary["hash_gate"] = True
    summary["expected_graphs"] = 16
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
