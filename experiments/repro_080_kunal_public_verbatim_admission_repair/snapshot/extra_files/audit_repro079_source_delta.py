from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PARENT_SHA256 = "6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d"
CANDIDATE_SHA256 = "5c370da1bf31d28215e023c4e4208c0bb658943c6ea4840d0af996aac5305b30"


def _raw(path: Path) -> tuple[bytes, dict]:
    raw = path.read_bytes()
    return raw, json.loads(raw)


def _lines(cell: dict) -> list[str]:
    return [line for line in "".join(cell.get("source", "")).splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    parent_raw, parent = _raw(args.parent)
    candidate_raw, candidate = _raw(args.candidate)
    assert hashlib.sha256(parent_raw).hexdigest() == PARENT_SHA256
    assert hashlib.sha256(candidate_raw).hexdigest() == CANDIDATE_SHA256
    assert len(parent["cells"]) == 12
    assert len(candidate["cells"]) == 13
    assert [cell.get("cell_type") for cell in candidate["cells"][:12]] == [
        cell.get("cell_type") for cell in parent["cells"]
    ]
    assert candidate["cells"][12].get("cell_type") == "code"
    assert not _lines(candidate["cells"][12])

    replacements = {
        "BIOHUB_SCORE_AXIS = 'public 0.953 base + validator-sweep-selected post-process configuration v2'":
            "BIOHUB_SCORE_AXIS = 'public 0.939 base + holdout-selected post-process configuration'",
        'os.environ["BIOHUB_PPSWEEP_SELECT_MARGIN"] = "0.0005"':
            'os.environ["BIOHUB_PPSWEEP_SELECT_MARGIN"] = "0.001"',
        'os.environ["BIOHUB_PPSWEEP_MAX_ADJ_LOSS"] = "0.0010"':
            'os.environ["BIOHUB_PPSWEEP_MAX_ADJ_LOSS"] = "0.0005"',
        'os.environ["BIOHUB_VALIDATOR_ENABLE"] = "1"          # enabled: runs held-out pp-sweep for best config':
            'os.environ["BIOHUB_VALIDATOR_ENABLE"] = "0"          # in-sample train proxy, ~11 min of GPU per run',
    }
    candidate_cell0 = [replacements.get(line, line) for line in _lines(candidate["cells"][0])]
    assert candidate_cell0 == _lines(parent["cells"][0])

    for index in range(1, 10):
        assert _lines(candidate["cells"][index]) == _lines(parent["cells"][index]), index

    cell10 = _lines(candidate["cells"][10])
    start = cell10.index("    # --- new candidates (v2) ---")
    end = cell10.index('    "relaxed11": {"MOTION_RELINK_RELAXED_UM": 11.0},')
    expected_inserted = [
        "    # --- new candidates (v2) ---",
        "    # Tighter symmetry tau for division geometry: fewer spurious division FPs",
        '    "sym_tau04": {"SAFE_DIV_SISTER_SYMMETRY_TAU": 0.4},',
        "    # More permissive gap2 total span: rescues more 2-frame dropout tracks",
        '    "gap2tot92": {"GAP2_MAX_TOTAL_UM": 9.2},',
        "    # Tighter DeepCenter safe-div veto: fewer hallucinated division links",
        '    "dcsafediv020": {"DEEPCENTER_SAFE_DIV_THRESHOLD": 0.20},',
        "    # Tighter edge-length cap: prunes long spurious association edges",
        '    "edgemax12": {"OUTPUT_EDGE_MAX_UM": 12.0},',
        "    # Pre-built combo: tighter symmetry + tighter DC safe-div veto together",
        '    "sym_dcsd": {"SAFE_DIV_SISTER_SYMMETRY_TAU": 0.4, "DEEPCENTER_SAFE_DIV_THRESHOLD": 0.20},',
        "    # Tighter velocity weight in motion re-link",
        '    "vel04": {"MOTION_RELINK_VELOCITY_WEIGHT": 0.4},',
        "    # Slightly wider relaxed gate for motion re-link",
        '    "relaxed11": {"MOTION_RELINK_RELAXED_UM": 11.0},',
    ]
    assert cell10[start:end + 1] == expected_inserted
    candidate_cell10 = cell10[:start] + cell10[end + 1:]
    assert candidate_cell10 == _lines(parent["cells"][10])
    assert _lines(candidate["cells"][11]) == _lines(parent["cells"][11])

    print("PASS: candidate preserves all nonblank parent source except four declared validator settings, seven appended sweep candidates, and one empty cell")


if __name__ == "__main__":
    main()
