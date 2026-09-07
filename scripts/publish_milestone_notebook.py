from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


CYRILLIC_RE = re.compile(r"[\u0400-\u04ff]")
MILESTONE_NAME_RE = re.compile(r"^biohub_v\d{2}_[a-z0-9_]+\.ipynb$")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish a cleaned, English milestone notebook under src/."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()

    source = args.source.resolve()
    destination = args.destination.resolve()
    project_root = Path(__file__).resolve().parents[1]
    src_root = (project_root / "src").resolve()

    if destination.parent != src_root:
        parser.error(f"destination must be directly under {src_root}")
    if not MILESTONE_NAME_RE.fullmatch(destination.name):
        parser.error("destination must match biohub_vNN_<short_name>.ipynb")
    if destination.exists():
        parser.error(f"refusing to overwrite existing milestone: {destination}")
    if not source.is_file():
        parser.error(f"source notebook is missing: {source}")

    raw = source.read_bytes()
    notebook = json.loads(raw.decode("utf-8"))
    if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
        parser.error("source is not a valid nbformat 4 notebook")

    source_text = "".join(
        "".join(cell.get("source", [])) for cell in notebook["cells"]
    )
    if CYRILLIC_RE.search(source_text):
        parser.error("source notebook contains Cyrillic text; milestone notebooks must use English")

    saved_errors = 0
    for cell in notebook["cells"]:
        if cell.get("cell_type") != "code":
            continue
        saved_errors += sum(
            output.get("output_type") == "error"
            for output in cell.get("outputs", []) or []
        )
        cell["execution_count"] = None
        cell["outputs"] = []
    if saved_errors:
        parser.error(f"source notebook contains {saved_errors} saved error output(s)")

    source_sha256 = hashlib.sha256(raw).hexdigest()
    published_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    provenance = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            f"# {args.title}\n",
            "\n",
            f"**Source experiment:** `{args.experiment}`  \n",
            f"**Source snapshot SHA256:** `{source_sha256}`  \n",
            f"**Published:** `{published_at}`\n",
            "\n",
            f"{args.summary.strip()}\n",
            "\n",
            "This is a cleaned milestone notebook. Execution outputs are intentionally removed; "
            "the immutable experiment directory retains the original run record and artifacts.\n",
        ],
    }
    notebook["cells"].insert(0, provenance)
    metadata = notebook.setdefault("metadata", {})
    metadata["biohub_milestone"] = {
        "experiment_id": args.experiment,
        "published_at": published_at,
        "source_sha256": source_sha256,
    }

    destination.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "destination": str(destination),
                "experiment_id": args.experiment,
                "source_sha256": source_sha256,
                "cells": len(notebook["cells"]),
                "saved_error_outputs": 0,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
