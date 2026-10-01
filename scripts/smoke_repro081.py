from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


UPSTREAM_SHA256 = "5c370da1bf31d28215e023c4e4208c0bb658943c6ea4840d0af996aac5305b30"
MARKER = "# repro081 receipt"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("upstream", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    upstream_raw = args.upstream.read_bytes()
    assert hashlib.sha256(upstream_raw).hexdigest() == UPSTREAM_SHA256
    upstream = json.loads(upstream_raw)
    candidate = json.loads(args.candidate.read_bytes())
    assert len(upstream["cells"]) == len(candidate["cells"])
    for index, (left, right) in enumerate(zip(upstream["cells"], candidate["cells"])):
        assert left.get("cell_type") == right.get("cell_type")
        left_source = "".join(left.get("source", ""))
        right_source = "".join(right.get("source", ""))
        stripped = "".join(line for line in right_source.splitlines(keepends=True) if MARKER not in line)
        assert stripped == left_source, index
        if right.get("cell_type") == "code":
            compile(right_source, f"<cell{index}>", "exec")
        assert not any(output.get("output_type") == "error" for output in right.get("outputs", []))
    source = "\n".join("".join(cell.get("source", "")) for cell in candidate["cells"])
    for token in (
        "validator_enabled_effective", "effective_globals_during_test_write",
        "submission_sha256_after_selected_write", "final_submission_sha256",
        "final_contract_validated", "repro081_runtime_receipt.json",
    ):
        assert token in source
    print("PASS: repro081 is upstream-byte-reconstructable with prediction-neutral runtime receipt instrumentation")


if __name__ == "__main__":
    main()
