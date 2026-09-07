from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def project_factory(tmp_path: Path):
    def build(*, experiment_id: str = "exp_100_test", protocol: str = "fixed_cv") -> tuple[Path, Path]:
        root = tmp_path / experiment_id
        (root / "configs").mkdir(parents=True)
        (root / "src").mkdir()
        (root / "GOAL.md").write_text("# Goal\n", encoding="utf-8")
        (root / "GPU_BUDGET.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "weekly_budget_hours": 30.0,
                    "remaining_hours": 20.0,
                    "reserve_hours": 5.0,
                    "max_single_experiment_hours": 4.0,
                    "require_user_approval_above_hours": 4.0,
                    "reserved_hours": {},
                    "consumed": [],
                }
            ),
            encoding="utf-8",
        )
        (root / "CURRENT_BEST.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "experiment_id": "baseline",
                    "validation_score": 0.8,
                    "validation_protocol": "fixed_cv",
                    "config": "configs/baseline.yaml",
                }
            ),
            encoding="utf-8",
        )
        (root / "results.json").write_text(
            json.dumps({"schema_version": 1, "experiments": []}), encoding="utf-8"
        )
        (root / "EXPERIMENTS.md").write_text("# Experiments\n", encoding="utf-8")
        notebook = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {},
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["open('/kaggle/working/metrics.json', 'w')\n"],
                }
            ],
        }
        (root / "src" / "run.ipynb").write_text(json.dumps(notebook), encoding="utf-8")
        config = {
            "schema_version": 1,
            "experiment_id": experiment_id,
            "parent": "baseline",
            "hypothesis": "One controlled test",
            "change": {"parameter": "x", "from": 1, "to": 2},
            "source_notebook": "src/run.ipynb",
            "validation": {
                "protocol": protocol,
                "primary_metric": "score",
                "required_specimens": ["44b6", "6bba"],
            },
            "budget": {"tier": 1, "expected_gpu_hours": 2.0},
            "success": {
                "minimum_improvement": 0.002,
                "regression_threshold": -0.002,
                "per_specimen_max_regression": 0.0,
            },
            "evaluation": {"mode": "compare"},
            "admission": {
                "require_claude_review": False,
                "methodology_valid": True,
                "require_reproducible_for_promotion": True,
            },
            "kaggle": {
                "owner": "tester",
                "slug": experiment_id,
                "competition_sources": ["biohub-cell-tracking-during-development"],
                "dataset_sources": [],
                "required_dataset_sources": 0,
            },
        }
        config_path = root / "configs" / f"{experiment_id}.yaml"
        config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        return root, config_path

    return build

