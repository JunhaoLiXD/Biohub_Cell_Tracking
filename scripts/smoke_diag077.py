from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path


PARENT_SHA = "77ad3756b4e6e600bf45a36bc12c9f20329058ad20d12478fa5df2cfd39c4b3f"
OLD_ROOT = "/kaggle/input/biohub-exp065-pruning-sweep/tracking_repo/predictions/unknown/unet_transformer_val/split_0"
NEW_ROOT = "/kaggle/input/kernels/lingxd/biohub-exp065-pruning-sweep/tracking_repo/predictions/unknown/unet_transformer_val/split_0"


def main() -> None:
    notebook = Path(sys.argv[1])
    doc = json.loads(notebook.read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", "")) for cell in doc["cells"])
    assert OLD_ROOT not in source
    assert source.count(NEW_ROOT) == 1
    assert "diag077: namespaced cache preflight PASS" in source
    assert '_d77_actual == _D77_EXPECTED' in source
    assert '"status": "PASS"' in source
    assert "assert _v7_val_pred_cache_hit" in source
    assert "def _d72_tree_sha256(root: _D77Path) -> str:" in source
    preflight_functions = []
    for index, cell in enumerate(doc["cells"]):
        if cell.get("cell_type") == "code":
            cell_source = "".join(cell.get("source", ""))
            compile(cell_source, f"<cell{index}>", "exec")
            if "diag077: fail before TEST inference" in cell_source:
                tree = ast.parse(cell_source)
                preflight_functions.extend(
                    node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and node.name == "_d72_tree_sha256"
                )
    assert len(preflight_functions) == 1
    annotation = preflight_functions[0].args.args[0].annotation
    assert isinstance(annotation, ast.Name) and annotation.id == "_D77Path"
    base = subprocess.run([sys.executable, "scripts/smoke_diag072.py", str(notebook)],
                          text=True, capture_output=True, check=False)
    assert base.returncode == 0, base.stdout + base.stderr
    print("PASS: executable namespaced-cache annotation binding plus unchanged diag073 scientific gates")


if __name__ == "__main__":
    main()
