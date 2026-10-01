from __future__ import annotations

import ast
import hashlib
import json
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "experiments/diag_073_fork_protected_cache_repair/snapshot/source/biohub-diag073-fork-protected-cache-repair.ipynb"
OUTPUT = ROOT / ".private/current/biohub-diag078-namespaced-cache-mount.ipynb"
OLD_ROOT = "/kaggle/input/biohub-exp065-pruning-sweep/tracking_repo/predictions/unknown/unet_transformer_val/split_0"
NEW_ROOT = "/kaggle/input/kernels/lingxd/biohub-exp065-pruning-sweep/tracking_repo/predictions/unknown/unet_transformer_val/split_0"
EXPECTED = {
    "44b6_12dfb391": "3d889d4cc317a8442d53d3b9dd6a615c6c961517a59f78369c4b60804ac5c369",
    "44b6_267148e4": "7ab1de1f855211f70b44f9530b0b9c902428309f8112b044b988198fdb6b058d",
    "44b6_2a2eff9f": "c90a46cafce0c8042c0f2993e4ae15ef396f1f16b3ab6d1e6ae57f86eec761f9",
    "44b6_341df25f": "4dd881da8763dab6b2a788a58896f78d681a9fa09f2090380a0e9b7a6dc40cc1",
    "6bba_062c8d37": "02f8466df77d1e39eca01d01492347839a07b231bbe3d66a2e079979d5c37dad",
    "6bba_07e24132": "b3a5b8040d19d875ecf7f84c4d615de51b4eb353c5ac3c7e90f5ff0021388d61",
    "6bba_085bf656": "dd26d1a3da6cf4932b1b7d99530bf60e76d339b99a4e951c163167367effd157",
    "6bba_09961292": "4addb2ddd58448da91d6d3149bc117f79008bf5774dc3a75dbafd33a632e424a",
}


doc = json.loads(PARENT.read_text(encoding="utf-8"))
all_source = "\n".join("".join(cell.get("source", "")) for cell in doc["cells"])
assert all_source.count(OLD_ROOT) == 1
assert NEW_ROOT not in all_source

hash_source = None
for cell in doc["cells"]:
    if cell.get("cell_type") != "code":
        continue
    source = "".join(cell.get("source", ""))
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_d72_tree_sha256":
            lines = source.splitlines()
            hash_source = textwrap.dedent("\n".join(lines[node.lineno - 1:node.end_lineno]))
            break
    if hash_source:
        break
assert hash_source is not None
assert "root: Path" in hash_source
hash_source = hash_source.replace("root: Path", "root: _D77Path", 1)
assert "root: Path" not in hash_source
assert "root: _D77Path" in hash_source

preflight = f'''

# diag077: fail before TEST inference if the namespaced exp065 kernel output is absent or altered.
from pathlib import Path as _D77Path
import hashlib as _d72_hashlib
{hash_source}
_D77_EXPECTED = {EXPECTED!r}
_d77_cache_root = _D77Path(os.environ["BIOHUB_VAL_PRED_CACHE_DIR"])
_d77_actual = {{
    stem: (_d72_tree_sha256(_d77_cache_root / f"{{stem}}.geff")
           if (_d77_cache_root / f"{{stem}}.geff").is_dir() else None)
    for stem in sorted(_D77_EXPECTED)
}}
assert _d77_actual == _D77_EXPECTED, (
    f"diag077: namespaced exp065 cache preflight failed at {{_d77_cache_root}}: {{_d77_actual}}"
)
(_D77Path("/kaggle/working") / "diag077_cache_preflight.json").write_text(
    json.dumps({{"cache_root": str(_d77_cache_root), "tree_sha256": _d77_actual,
                "status": "PASS"}}, indent=2, sort_keys=True) + "\\n"
)
print(f"diag077: namespaced cache preflight PASS at {{_d77_cache_root}}", flush=True)
'''

changed = 0
for cell in doc["cells"]:
    if cell.get("cell_type") != "code":
        continue
    source = "".join(cell.get("source", ""))
    if OLD_ROOT in source:
        source = source.replace(OLD_ROOT, NEW_ROOT)
        source += preflight
        cell["source"] = source
        cell["outputs"] = []
        cell["execution_count"] = None
        changed += 1
assert changed == 1

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(json.dumps({"output": str(OUTPUT.relative_to(ROOT)),
                  "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}, indent=2))
