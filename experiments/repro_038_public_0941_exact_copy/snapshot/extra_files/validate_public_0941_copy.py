"""Static checks for the byte-identical public Ozan notebook reproduction."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import validate_notebook

EXPECTED_SHA256 = "24253cae5a958b83d69e201719388031f5758080c5d01ca1a8e374f3a8225389"


def validate(path: Path) -> dict:
    if hashlib.sha256(path.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise ValueError("The public notebook bytes have changed")
    result = validate_notebook(path, require_metrics_contract=False)
    notebook = json.loads(path.read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        source = "".join(cell["source"])
        if re.search(r"[\u0400-\u04ff\u4e00-\u9fff]", source):
            raise ValueError("Non-English source in active notebook")
        if cell["cell_type"] == "code":
            ast.parse(source)
    result.update(notebook_sha256=EXPECTED_SHA256, byte_identical_upstream=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.notebook), indent=2))
