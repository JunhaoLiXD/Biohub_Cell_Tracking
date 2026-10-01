from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_biohub_submission_csv import audit_submission


EXPECTED_DATASETS = {
    "44b6_0113de3b",
    "44b6_0b24845f",
    "6bba_05b6850b",
    "6bba_05db0fb1",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("submission", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit_submission(
        args.submission,
        expected_datasets=EXPECTED_DATASETS,
        image_bounds=(64, 256, 256),
    )
    report["output_integrity_passed"] = report["status"] == "PASS"
    report["contract"] = {
        "columns": ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"],
        "expected_datasets": sorted(EXPECTED_DATASETS),
        "coordinate_bounds_zyx_exclusive": [64, 256, 256],
        "requires": [
            "contiguous unique row ids",
            "unique nodes per dataset",
            "valid edge endpoints",
            "adjacent-frame temporal edges",
            "indegree at most one",
            "outdegree at most two",
            "nonempty node output",
            "SHA256 artifact identity",
        ],
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["output_integrity_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
