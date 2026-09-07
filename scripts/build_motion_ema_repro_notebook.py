"""Build an independent reproducibility run for the accepted motion-EMA candidate."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".private" / "current" / "motion_ema_train16_v2.ipynb"
TARGET = ROOT / ".private" / "current" / "motion_ema_repro_train16.ipynb"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one {label} replacement target, found {count}")
    return source.replace(old, new, 1)


notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
notebook["cells"].insert(
    0,
    {
        "cell_type": "markdown",
        "id": "motion-ema-reproduction-summary",
        "metadata": {},
        "source": (
            "# Independent motion-EMA reproducibility gate\n\n"
            "This notebook keeps the accepted exp_035 algorithm and frozen train16 protocol "
            "unchanged. It adds only a controller-owned reproducibility contract requiring exact "
            "aggregate and per-specimen metrics plus a byte-identical test submission. The expected "
            "values and SHA256 digest come from the collected exp_035 artifacts.\n"
        ).splitlines(keepends=True),
    },
)

code_cells = [cell for cell in notebook["cells"] if cell.get("cell_type") == "code"]
contract = code_cells[-1]
source = "".join(contract["source"])
source = replace_once(
    source,
    '_controller_ema_execution_by_specimen = {\n',
    '_CONTROLLER_REPRO_EXPECTED_PRIMARY = 0.9273163492758533\n'
    '_CONTROLLER_REPRO_EXPECTED_ADJUSTED_EDGE = 0.9162052381647422\n'
    '_CONTROLLER_REPRO_EXPECTED_DIVISION = 0.1111111111111111\n'
    '_CONTROLLER_REPRO_EXPECTED_SPECIMEN = {\n'
    '    "44b6": 0.9050173749768016,\n'
    '    "6bba": 0.9355045025356437,\n'
    '}\n'
    '_CONTROLLER_REPRO_EXPECTED_SUBMISSION_SHA256 = (\n'
    '    "93eec4d1e2f47d3b93f08fc7b0385cf3c80b7a7311e1eef8e0934ea2755f3ca3"\n'
    ')\n\n'
    '_controller_ema_execution_by_specimen = {\n',
    "reproduction expectations",
)
source = replace_once(
    source,
    '_controller_checks = {\n',
    '_controller_checks = {\n'
    '    "reproduction_primary_exact": _controller_math.isclose(\n'
    '        _controller_primary, _CONTROLLER_REPRO_EXPECTED_PRIMARY, abs_tol=1e-12\n'
    '    ),\n'
    '    "reproduction_adjusted_edge_exact": _controller_math.isclose(\n'
    '        float(_controller_summary["adjusted_edge_jaccard"]),\n'
    '        _CONTROLLER_REPRO_EXPECTED_ADJUSTED_EDGE,\n'
    '        abs_tol=1e-12,\n'
    '    ),\n'
    '    "reproduction_division_exact": _controller_math.isclose(\n'
    '        float(_controller_summary["division_jaccard"]),\n'
    '        _CONTROLLER_REPRO_EXPECTED_DIVISION,\n'
    '        abs_tol=1e-12,\n'
    '    ),\n'
    '    "reproduction_specimens_exact": all(\n'
    '        _controller_math.isclose(\n'
    '            _controller_specimen_metrics.get(specimen, {}).get(\n'
    '                "primary_metric", float("nan")\n'
    '            ),\n'
    '            expected,\n'
    '            abs_tol=1e-12,\n'
    '        )\n'
    '        for specimen, expected in _CONTROLLER_REPRO_EXPECTED_SPECIMEN.items()\n'
    '    ),\n'
    '    "reproduction_submission_sha256_exact": (\n'
    '        str(_guard_report.get("submission", {}).get("sha256", ""))\n'
    '        == _CONTROLLER_REPRO_EXPECTED_SUBMISSION_SHA256\n'
    '    ),\n',
    "reproduction checks",
)
source = replace_once(
    source,
    '_controller_final_validation_graph_export_passed = _controller_validation_contract_passed\n\n'
    '_controller_metrics = {\n',
    '_controller_final_validation_graph_export_passed = _controller_validation_contract_passed\n'
    '_controller_reproduction_passed = _controller_validation_contract_passed\n\n'
    '_controller_metrics = {\n',
    "reproduction decision",
)
source = replace_once(
    source,
    '    "reproducible": False,\n',
    '    "reproducible": _controller_reproduction_passed,\n',
    "reproducible flag",
)
source = replace_once(
    source,
    '        "validation_contract_passed": _controller_validation_contract_passed,\n',
    '        "validation_contract_passed": _controller_validation_contract_passed,\n'
    '        "reproduction_passed": _controller_reproduction_passed,\n'
    '        "reproduction_reference_experiment": "exp_035_train16_motion_ema_reviewfix",\n'
    '        "reproduction_expected_submission_sha256": _CONTROLLER_REPRO_EXPECTED_SUBMISSION_SHA256,\n',
    "reproduction metrics",
)
contract["source"] = source.splitlines(keepends=True)

TARGET.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
print(TARGET)
