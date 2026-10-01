from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml


EXPECTED_DATASETS = [
    "pilkwang/biohub-deepcenter-unet3d-center-prior-v1",
    "pilkwang/biohub-temporal-unet3d-seed314159-v1",
    "pilkwang/biohub-tracking-support-pack-50ep-v1",
    "anvithpothula/biohub-v1284-head-s075",
]
EXPECTED_COMPETITIONS = ["biohub-cell-tracking-during-development"]
EXPECTED_KERNELS = ["lingxd/biohub-exp065-pruning-sweep"]
EXPECTED_DOCKER = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()

    base = subprocess.run(
        [sys.executable, "scripts/smoke_diag072.py", str(args.notebook)],
        text=True,
        capture_output=True,
        check=False,
    )
    if base.returncode:
        raise AssertionError(base.stdout + base.stderr)

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    kaggle = config["kaggle"]
    assert kaggle["dataset_sources"] == EXPECTED_DATASETS
    assert kaggle["competition_sources"] == EXPECTED_COMPETITIONS
    assert kaggle["kernel_sources"] == EXPECTED_KERNELS
    assert kaggle["required_dataset_sources"] == len(EXPECTED_DATASETS)
    assert kaggle["docker_image"] == EXPECTED_DOCKER
    assert config["leaderboard"] == {"authorized": False, "max_submissions": 0}
    print("PASS: byte-identical diag073 science plus complete pinned remote-source contract")


if __name__ == "__main__":
    main()
