"""Build the launchable 0.946 public-notebook copy with dataset-path edits only."""
from __future__ import annotations

import hashlib
from pathlib import Path

from _bootstrap import PROJECT_ROOT

SOURCE = PROJECT_ROOT / ".private/research/public_frontier_2026-09-08/reyhan_0946/biohub-cell-tracking-0-946-lb.ipynb"
TARGET = PROJECT_ROOT / ".private/current/public_0946_edge_feature_tta_copy.ipynb"
SOURCE_SHA256 = "ae8e01a262211045161984e469e8be23e3386bab9140fe12df503dc6a1e010e6"

REPLACEMENTS = {
    "/kaggle/input/datasets/reyhanksatria/biohub-tracking-support-pack":
        "/kaggle/input/biohub-tracking-support-pack-50ep-v1",
    "'biohub-tracking-support-pack'": "'biohub-tracking-support-pack-50ep-v1'",
    "/kaggle/input/datasets/reyhanksatria/biohub-deepcenterunet3d-center-prior-v1":
        "/kaggle/input/biohub-deepcenter-unet3d-center-prior-v1",
    "/kaggle/input/datasets/reyhanksatria/biohub-temporalunet3d-seed-314159-v1":
        "/kaggle/input/biohub-temporal-unet3d-seed314159-v1",
}


def main() -> None:
    raw = SOURCE.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != SOURCE_SHA256:
        raise RuntimeError(f"Archived upstream notebook changed: {actual}")
    text = raw.decode("utf-8")
    for old, new in REPLACEMENTS.items():
        count = text.count(old)
        if count == 0:
            raise RuntimeError(f"Expected dataset path is absent: {old}")
        text = text.replace(old, new)
        print(f"Replaced {count} occurrence(s): {old} -> {new}")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(text, encoding="utf-8", newline="")
    print(f"Built {TARGET.relative_to(PROJECT_ROOT)}")
    print(f"Edited SHA256: {hashlib.sha256(TARGET.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
