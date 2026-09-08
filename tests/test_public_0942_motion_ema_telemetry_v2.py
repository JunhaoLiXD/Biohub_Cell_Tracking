"""Static, runtime-type, and negative-control tests for telemetry v2."""
import ast
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_builder_is_deterministic_and_behavior_gated():
    from scripts.build_public_0942_motion_ema_telemetry_v2 import build
    from scripts.validate_public_0942_motion_ema_telemetry_v2 import validate

    target = ROOT / ".private/current/public_0942_motion_ema_telemetry_v2.ipynb"
    assert json.loads(target.read_text(encoding="utf-8")) == build()
    summary = validate(target)
    assert summary["single_change"] == "corrected_decomposed_online_motion_telemetry_only"
    assert summary["base_alpha"] == 0.4
    assert summary["velocity_weight"] == 0.5
    assert summary["thresholds"] == [1.0, 1.25, 1.5, 1.75]
    assert summary["native_count_regression"] is True
    assert summary["strict_json_contract"] is True
    assert summary["exact_parent_behavior_gates"] is True


def test_builder_rejects_failed_predecessor_hash_drift(monkeypatch):
    import scripts.build_public_0942_motion_ema_telemetry_v2 as builder

    monkeypatch.setattr(builder, "PARENT_SHA", "0" * 64)
    with pytest.raises(ValueError, match="Frozen parent input changed"):
        builder.build()


def test_numpy_boolean_regression_serializes_as_native_int():
    np = pytest.importorskip("numpy")
    margins = [float("nan"), 0.75, 0.25]
    old = sum(
        innovation > 1.0 and age >= 3 and np.isfinite(margin) and margin >= 0.5
        for innovation, age, margin in zip([1.2, 1.3, 1.4], [4, 4, 4], margins)
    )
    assert isinstance(old, np.integer)
    with pytest.raises(TypeError, match="not JSON serializable"):
        json.dumps({"guarded": old})

    corrected = int(sum(bool(
        innovation > 1.0 and age >= 3 and bool(np.isfinite(margin)) and margin >= 0.5
    ) for innovation, age, margin in zip([1.2, 1.3, 1.4], [4, 4, 4], margins)))
    assert type(corrected) is int
    assert json.loads(json.dumps({"guarded": corrected}, allow_nan=False)) == {"guarded": 1}


def test_config_requires_review_and_records_exact_scope():
    import yaml

    config = yaml.safe_load(
        (ROOT / "configs/diag_045_public_0942_motion_ema_telemetry_v2.yaml")
        .read_text(encoding="utf-8")
    )
    assert config["parent"] == "repro_041_public_0941_motion_ema"
    assert config["provenance"]["failed_predecessor"] == "diag_044_public_0942_motion_ema_online_telemetry"
    assert config["change"]["variables_changed"] == "instrumentation_only_no_prediction_change"
    assert config["admission"]["require_claude_review"] is True
    assert config["evaluation"]["gate_field"] == "telemetry_diagnostic_passed"
    assert config["submission"]["user_authorized_count"] == 0
    telemetry = config["validation"]["telemetry"]
    assert telemetry["innovation_thresholds"] == [1.0, 1.25, 1.5, 1.75]
    assert telemetry["strict_json_serialization"] is True
    assert set(telemetry["prohibited_dependencies"]) == {"specimen_id", "video_id", "ground_truth"}


def test_notebook_has_native_count_and_strict_serialization_guards():
    from scripts.build_public_0942_motion_ema_telemetry_v2 import build, source

    notebook = build()
    text = "\n".join(source(cell) for cell in notebook["cells"])
    assert "return int(sum(bool(value) for value in values))" in text
    assert "type(values[field]) is int" in text
    assert text.count("allow_nan=False") >= 3
    assert "motion_relink_telemetry_finite_margin_updates" in text
    assert "motion_relink_telemetry_nonfinite_margin_updates" in text
    assert "motion_relink_telemetry_margin_ge0500_gt_" in text
    assert "motion_relink_telemetry_proposed_gt_2000" not in text
    assert "motion_relink_telemetry_proposed_gt_3000" not in text
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            ast.parse(source(cell))
