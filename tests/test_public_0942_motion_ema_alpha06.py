"""Static and negative-control tests for the public-0.942 EMA alpha-0.6 experiment."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_builder_is_deterministic_and_changes_only_alpha():
    from scripts.build_public_0942_motion_ema_alpha06 import build
    from scripts.validate_public_0942_motion_ema_alpha06 import validate

    expected = build()
    target = ROOT / ".private/current/public_0942_motion_ema_alpha06.ipynb"
    assert json.loads(target.read_text(encoding="utf-8")) == expected
    summary = validate(target)
    assert summary["single_variable_change"] == "motion_relink_ema_alpha_0.4_to_0.6"
    assert summary["ema_alpha"] == 0.6
    assert summary["velocity_weight"] == 0.5


def test_builder_rejects_parent_hash_drift(monkeypatch):
    import scripts.build_public_0942_motion_ema_alpha06 as builder

    monkeypatch.setattr(builder, "PARENT_SHA", "0" * 64)
    with pytest.raises(ValueError, match="Frozen alpha-0.4 parent changed"):
        builder.build()


def test_config_requires_review_and_robustness_gates():
    import yaml

    config = yaml.safe_load((ROOT / "configs/exp_042_public_0942_motion_ema_alpha06.yaml").read_text(encoding="utf-8"))
    assert config["parent"] == "repro_041_public_0941_motion_ema"
    assert config["change"]["variables_changed"] == "motion_relink_ema_alpha_only"
    assert config["admission"]["require_claude_review"] is True
    assert config["evaluation"]["gate_field"] == "alpha06_candidate_gate_passed"
    assert config["validation"]["worst_video_delta_floor_vs_val039"] == -0.002
    assert config["validation"]["division_count_gates"] == {
        "minimum_tp": 4, "maximum_fp": 8, "maximum_fn": 8}
