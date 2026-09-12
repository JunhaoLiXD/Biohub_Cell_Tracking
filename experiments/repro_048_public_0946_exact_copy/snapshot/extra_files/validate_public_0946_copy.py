"""Static checks for the path-edited public 0.946 notebook reproduction."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

from _bootstrap import PROJECT_ROOT

SOURCE = PROJECT_ROOT / ".private/research/public_frontier_2026-09-08/reyhan_0946/biohub-cell-tracking-0-946-lb.ipynb"
SOURCE_SHA256 = "ae8e01a262211045161984e469e8be23e3386bab9140fe12df503dc6a1e010e6"
EDITED_SHA256 = "4eda3c3dae83f5ad21fee35513aad5f325e09b6de8f77fa55d9b7d6d4b50ca16"
REPLACEMENTS = {
    "/kaggle/input/datasets/reyhanksatria/biohub-tracking-support-pack":
        "/kaggle/input/biohub-tracking-support-pack-50ep-v1",
    "'biohub-tracking-support-pack'": "'biohub-tracking-support-pack-50ep-v1'",
    "/kaggle/input/datasets/reyhanksatria/biohub-deepcenterunet3d-center-prior-v1":
        "/kaggle/input/biohub-deepcenter-unet3d-center-prior-v1",
    "/kaggle/input/datasets/reyhanksatria/biohub-temporalunet3d-seed-314159-v1":
        "/kaggle/input/biohub-temporal-unet3d-seed314159-v1",
}


def validate(path: Path) -> dict:
    source_raw = SOURCE.read_bytes()
    if hashlib.sha256(source_raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Archived upstream notebook bytes changed")
    edited_raw = path.read_bytes()
    if hashlib.sha256(edited_raw).hexdigest() != EDITED_SHA256:
        raise ValueError("Edited public notebook bytes changed")
    expected = source_raw.decode("utf-8")
    for old, new in REPLACEMENTS.items():
        expected = expected.replace(old, new)
    if edited_raw.decode("utf-8") != expected:
        raise ValueError("Notebook differs by more than the declared dataset-path substitutions")

    notebook = json.loads(edited_raw)
    if notebook.get("nbformat") != 4 or not notebook.get("cells"):
        raise ValueError("Invalid or empty notebook structure")
    source_text = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    if "os.environ['BIOHUB_EDGE_FEATURE_TTA'] = '1'" not in source_text:
        raise ValueError("Edge-feature TTA is not enabled")
    if "BIOHUB_MOTION_RELINK_EMA_ALPHA" in source_text:
        raise ValueError("Public copy unexpectedly includes our motion EMA")
    for cell in notebook["cells"]:
        cell_source = "".join(cell["source"])
        if re.search(r"[\u0400-\u04ff\u4e00-\u9fff]", cell_source):
            raise ValueError("Non-English source in active notebook")
        if cell["cell_type"] == "code":
            ast.parse(cell_source)
            if any(output.get("output_type") == "error" for output in cell.get("outputs", [])):
                raise ValueError("Notebook contains a saved error output")
    result = dict(
        cells=len(notebook["cells"]),
        code_cells=sum(cell["cell_type"] == "code" for cell in notebook["cells"]),
        upstream_sha256=SOURCE_SHA256,
        edited_sha256=EDITED_SHA256,
        dataset_path_edits_only=True,
        edge_feature_tta=True,
        motion_ema=False,
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.notebook), indent=2))
