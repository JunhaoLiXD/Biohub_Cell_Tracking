from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_SHA256 = "e6c3f729835b28ca61ec7634526fb9e798df43e43e40f5e1a0a794dcd8521c2e"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    args = parser.parse_args()
    raw = args.notebook.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
    doc = json.loads(raw)
    source = "\n".join("".join(cell.get("source", "")) for cell in doc["cells"])
    assert 'BIOHUB_SCORE_AXIS = \'0.965+ grandmaster multi-horizon flow + quantile-consensus ensembling\'' in source
    assert 'write_test_submission("base")' in source
    assert 'SUBMISSION_PATH = WORKING_DIR / "submission.csv"' in source
    assert "leaderboard_submission" not in source.lower()
    for index, cell in enumerate(doc["cells"]):
        if cell.get("cell_type") == "code":
            compile("".join(cell.get("source", "")), f"<cell{index}>", "exec")
        for output in cell.get("outputs", []):
            assert output.get("output_type") != "error"
    print("PASS: exact Aman Atar public notebook bytes, syntax, and submission output contract")


if __name__ == "__main__":
    main()
