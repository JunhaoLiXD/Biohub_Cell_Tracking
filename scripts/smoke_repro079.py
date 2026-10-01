from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_SHA256 = "5c370da1bf31d28215e023c4e4208c0bb658943c6ea4840d0af996aac5305b30"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    args = parser.parse_args()

    raw = args.notebook.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
    doc = json.loads(raw)
    source = "\n".join("".join(cell.get("source", "")) for cell in doc["cells"])

    assert "public 0.953 base + validator-sweep-selected post-process configuration v2" in source
    assert '"DEEPCENTER_SAFE_DIV_THRESHOLD": 0.20' in source
    assert 'SUBMISSION_PATH = WORKING_DIR / "submission.csv"' in source
    assert "write_test_submission" in source
    assert "leaderboard_submission" not in source.lower()

    for index, cell in enumerate(doc["cells"]):
        if cell.get("cell_type") == "code":
            compile("".join(cell.get("source", "")), f"<cell{index}>", "exec")
        for output in cell.get("outputs", []):
            assert output.get("output_type") != "error"

    print("PASS: exact Kunal public notebook bytes, syntax, and submission output contract")


if __name__ == "__main__":
    main()
