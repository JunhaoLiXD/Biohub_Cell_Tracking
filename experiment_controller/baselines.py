from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from .core import ControllerError, command_prefix, find_project_root, utc_now, write_json


KERNEL_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*/[A-Za-z0-9][A-Za-z0-9_-]*$")


def _kaggle() -> list[str]:
    config_dir = Path(os.environ.setdefault("KAGGLE_CONFIG_DIR", str(find_project_root() / ".kaggle")))
    config_dir.mkdir(parents=True, exist_ok=True)
    return command_prefix("kaggle", "kaggle", "KAGGLE_COMMAND")


def _csv_payload(output: str) -> str:
    lines = output.splitlines()
    for index, line in enumerate(lines):
        lowered = line.lower()
        if "," in line and (lowered.startswith("ref,") or "title" in lowered):
            return "\n".join(lines[index:])
    raise ControllerError("Kaggle output did not contain a CSV header")


def discover(root: Path, competition: str, top_k: int = 20) -> list[dict[str, Any]]:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]+", competition):
        raise ControllerError(f"Invalid competition slug: {competition}")
    if not 1 <= top_k <= 100:
        raise ControllerError("top_k must be between 1 and 100")
    command = [
        *_kaggle(),
        "kernels",
        "list",
        "--competition",
        competition,
        "--sort-by",
        "voteCount",
        "--page-size",
        str(top_k),
        "--csv",
    ]
    result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise ControllerError(f"Kaggle baseline discovery failed: {result.stderr.strip()}")
    reader = csv.DictReader(io.StringIO(_csv_payload(result.stdout)))
    rows: list[dict[str, Any]] = []
    for raw in reader:
        lowered = {str(key).strip().lower(): value for key, value in raw.items()}
        ref = lowered.get("ref") or lowered.get("kernelref") or lowered.get("kernel")
        if not ref:
            continue
        rows.append(
            {
                "kernel": ref,
                "title": lowered.get("title") or lowered.get("name") or ref,
                "author": ref.split("/", 1)[0],
                "votes": _int_or_none(lowered.get("votecount") or lowered.get("votes")),
                "last_run_time": lowered.get("lastruntime") or lowered.get("last_run_time"),
                "language": lowered.get("language"),
                "discovered_at": utc_now(),
                "competition": competition,
                "status": "UNREVIEWED",
            }
        )
        if len(rows) >= top_k:
            break
    research = root / "research"
    research.mkdir(parents=True, exist_ok=True)
    write_json(research / "baseline_candidates.json", {"schema_version": 1, "candidates": rows})
    lines = [
        "# Baseline Candidates",
        "",
        f"Competition: `{competition}`  ",
        f"Discovered: {date.today().isoformat()}",
        "",
        "| Kernel | Title | Votes | Status |",
        "|---|---|---:|---|",
    ]
    for item in rows:
        lines.append(
            f"| `{item['kernel']}` | {str(item['title']).replace('|', '/')} | "
            f"{item['votes'] if item['votes'] is not None else '-'} | UNREVIEWED |"
        )
    (research / "BASELINE_CANDIDATES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def pull(root: Path, kernel: str) -> Path:
    if not KERNEL_REF_RE.fullmatch(kernel):
        raise ControllerError("Kernel reference must be owner/kernel-slug")
    destination = root / "external_baselines" / kernel.replace("/", "_")
    if destination.exists():
        raise ControllerError(f"Baseline destination already exists; refusing to overwrite: {destination}")
    original = destination / "ORIGINAL"
    original.mkdir(parents=True)
    command = [*_kaggle(), "kernels", "pull", kernel, "-p", str(original), "--metadata"]
    result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        (destination / "PULL_FAILED.txt").write_text(result.stderr, encoding="utf-8")
        raise ControllerError(f"Kaggle kernel pull failed; see {destination / 'PULL_FAILED.txt'}")
    notes = f"""# Baseline provenance

- Kaggle kernel: `{kernel}`
- Pulled at: {utc_now()}
- Original files: `ORIGINAL/` (gitignored)
- Review status: UNREVIEWED

Do not copy this baseline directly into `src/`. Review data sources, validation, rules,
dependencies, and reproducibility first; then extract a single attributable idea.
"""
    (destination / "NOTES.md").write_text(notes, encoding="utf-8")
    (destination / "REVIEW.md").write_text("# Review\n\nPending.\n", encoding="utf-8")
    (destination / "REPRODUCTION.md").write_text("# Reproduction\n\nNot attempted.\n", encoding="utf-8")
    return destination
