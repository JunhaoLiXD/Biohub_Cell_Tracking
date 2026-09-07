"""Static and negative-control tests for the public-0.941 motion-EMA screen."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_builder_is_deterministic_and_single_variable():
    from scripts.build_public_0941_motion_ema import build
    from scripts.validate_public_0941_motion_ema import validate

    expected = build()
    target = ROOT / ".private/current/public_0941_motion_ema.ipynb"
    assert json.loads(target.read_text(encoding="utf-8")) == expected
    summary = validate(target)
    assert summary["single_algorithm_change"] == "motion_velocity_estimator"
    assert summary["ema_alpha"] == 0.4


def test_builder_rejects_parent_hash_drift(monkeypatch):
    import scripts.build_public_0941_motion_ema as builder

    monkeypatch.setattr(builder, "PARENT_SHA", "0" * 64)
    with pytest.raises(ValueError, match="Frozen val_039 parent changed"):
        builder.build()


def test_config_requires_review_and_has_exact_gate():
    import yaml

    config = yaml.safe_load((ROOT / "configs/exp_040_public_0941_motion_ema.yaml").read_text(encoding="utf-8"))
    assert config["parent"] == "val_039_public_0941_train16"
    assert config["admission"]["require_claude_review"] is True
    assert config["evaluation"]["gate_field"] == "ema_candidate_gate_passed"
    assert config["success"]["minimum_improvement"] == 0.001
    assert config["validation"]["division_count_gates"] == {"minimum_tp": 4, "maximum_fp": 9, "maximum_fn": 8}
