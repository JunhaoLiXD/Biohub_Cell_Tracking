"""Static and negative-control tests for the label-free adaptive EMA reset."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_builder_is_deterministic_and_rule_is_label_free():
    from scripts.build_public_0942_motion_ema_adaptive_reset import build
    from scripts.validate_public_0942_motion_ema_adaptive_reset import validate

    expected = build()
    target = ROOT / ".private/current/public_0942_motion_ema_adaptive_reset.ipynb"
    assert json.loads(target.read_text(encoding="utf-8")) == expected
    summary = validate(target)
    assert summary["single_algorithm_change"] == "label_free_adaptive_ema_reset"
    assert summary["base_alpha"] == 0.4
    assert summary["reset_alpha"] == summary["innovation_threshold"] == 1.0
    assert summary["velocity_weight"] == 0.5


def test_builder_rejects_parent_hash_drift(monkeypatch):
    import scripts.build_public_0942_motion_ema_adaptive_reset as builder

    monkeypatch.setattr(builder, "PARENT_SHA", "0" * 64)
    with pytest.raises(ValueError, match="Frozen alpha-0.4 parent changed"):
        builder.build()


def test_config_requires_review_and_runtime_only_rule():
    import yaml

    config = yaml.safe_load((ROOT / "configs/exp_043_public_0942_motion_ema_adaptive_reset.yaml").read_text(encoding="utf-8"))
    assert config["parent"] == "repro_041_public_0941_motion_ema"
    assert config["change"]["variables_changed"] == "motion_relink_adaptive_ema_reset_rule_only"
    assert config["admission"]["require_claude_review"] is True
    assert config["evaluation"]["gate_field"] == "adaptive_ema_candidate_gate_passed"
    rule = config["validation"]["adaptive_rule"]
    assert rule["data_dependencies"] == "runtime_selected_positions_only"
    assert set(rule["prohibited_dependencies"]) == {"specimen_id", "video_id", "ground_truth"}
    assert config["validation"]["division_count_gates"] == {
        "minimum_tp": 4, "maximum_fp": 8, "maximum_fn": 8}
