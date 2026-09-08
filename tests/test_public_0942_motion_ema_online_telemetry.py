"""Static and negative-control tests for the telemetry-only EMA diagnostic."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_builder_is_deterministic_and_behavior_gated():
    from scripts.build_public_0942_motion_ema_online_telemetry import build
    from scripts.validate_public_0942_motion_ema_online_telemetry import validate

    target = ROOT / ".private/current/public_0942_motion_ema_online_telemetry.ipynb"
    assert json.loads(target.read_text(encoding="utf-8")) == build()
    summary = validate(target)
    assert summary["single_change"] == "online_motion_telemetry_only"
    assert summary["base_alpha"] == 0.4
    assert summary["velocity_weight"] == 0.5
    assert summary["exact_parent_behavior_gates"] is True


def test_builder_rejects_parent_hash_drift(monkeypatch):
    import scripts.build_public_0942_motion_ema_online_telemetry as builder

    monkeypatch.setattr(builder, "PARENT_SHA", "0" * 64)
    with pytest.raises(ValueError, match="Frozen parent input changed"):
        builder.build()


def test_config_requires_review_and_forbids_labels():
    import yaml

    config = yaml.safe_load((ROOT / "configs/diag_044_public_0942_motion_ema_online_telemetry.yaml").read_text(encoding="utf-8"))
    assert config["parent"] == "repro_041_public_0941_motion_ema"
    assert config["change"]["variables_changed"] == "instrumentation_only_no_prediction_change"
    assert config["admission"]["require_claude_review"] is True
    assert config["evaluation"]["gate_field"] == "telemetry_diagnostic_passed"
    telemetry = config["validation"]["telemetry"]
    assert set(telemetry["prohibited_dependencies"]) == {"specimen_id", "video_id", "ground_truth"}
    assert telemetry["innovation_thresholds"] == [1.0, 1.25, 1.5, 2.0, 3.0]
