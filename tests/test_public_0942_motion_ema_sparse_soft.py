"""Static, predicate, and negative-control tests for sparse soft motion EMA."""
import ast
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_builder_is_deterministic_and_policy_is_label_free():
    from scripts.build_public_0942_motion_ema_sparse_soft import build
    from scripts.validate_public_0942_motion_ema_sparse_soft import validate

    target = ROOT / ".private/current/public_0942_motion_ema_sparse_soft.ipynb"
    assert json.loads(target.read_text(encoding="utf-8")) == build()
    summary = validate(target)
    assert summary["single_algorithm_change"] == "label_free_sparse_soft_ema"
    assert summary["base_alpha"] == 0.4
    assert summary["soft_alpha"] == 0.6
    assert summary["innovation_threshold"] == 1.25
    assert summary["minimum_track_age"] == 3
    assert summary["minimum_assignment_margin"] == 0.5
    assert summary["velocity_weight"] == 0.5
    assert summary["strict_policy_count_contract"] is True


def test_builder_rejects_donor_hash_drift(monkeypatch):
    import scripts.build_public_0942_motion_ema_sparse_soft as builder

    monkeypatch.setattr(builder, "DONOR_SHA", "0" * 64)
    with pytest.raises(ValueError, match="Frozen input changed"):
        builder.build()


def test_sparse_predicate_boundaries_and_nonfinite_rejection():
    import math
    from scripts.build_public_0942_motion_ema_sparse_soft import build, source
    from scripts.validate_public_0942_motion_ema_sparse_soft import find_code, function_source

    class NumpyFiniteStub:
        isfinite = staticmethod(math.isfinite)

    notebook = build()
    cell_text = source(find_code(notebook["cells"], "def _use_sparse_soft_alpha"))
    predicate = function_source(cell_text, "_use_sparse_soft_alpha")
    namespace = {
        "np": NumpyFiniteStub,
        "MOTION_RELINK_EMA_INNOVATION_THRESHOLD": 1.25,
        "MOTION_RELINK_EMA_MIN_TRACK_AGE": 3,
        "MOTION_RELINK_EMA_MIN_ASSIGNMENT_MARGIN": 0.5,
    }
    exec(compile(ast.parse(predicate), "<predicate>", "exec"), namespace)
    use_soft = namespace["_use_sparse_soft_alpha"]
    assert use_soft(1.250001, 3, 0.5) is True
    assert use_soft(1.25, 3, 0.5) is False
    assert use_soft(1.3, 2, 0.5) is False
    assert use_soft(1.3, 3, 0.499999) is False
    assert use_soft(1.3, 3, float("nan")) is False
    assert use_soft(1.3, 3, float("inf")) is False


def test_config_requires_fresh_review_and_single_policy_change():
    import yaml

    config = yaml.safe_load(
        (ROOT / "configs/exp_046_public_0942_motion_ema_sparse_soft.yaml")
        .read_text(encoding="utf-8")
    )
    assert config["parent"] == "repro_041_public_0941_motion_ema"
    assert config["change"]["variables_changed"] == "motion_relink_sparse_soft_ema_rule_only"
    assert config["admission"]["require_claude_review"] is True
    assert config["evaluation"]["gate_field"] == "sparse_soft_ema_candidate_gate_passed"
    assert config["submission"]["user_authorized_count"] == 0
    rule = config["validation"]["adaptive_rule"]
    assert rule["innovation_threshold"] == 1.25
    assert rule["base_alpha"] == 0.4 and rule["soft_alpha"] == 0.6
    assert rule["minimum_track_age"] == 3
    assert rule["minimum_assignment_margin"] == 0.5
    assert set(rule["prohibited_dependencies"]) == {"specimen_id", "video_id", "ground_truth"}
