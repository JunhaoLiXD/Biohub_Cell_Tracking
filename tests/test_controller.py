from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess

import pytest

import experiment_controller.kaggle as kaggle_module
import experiment_controller.review as review_module
from experiment_controller.core import (
    ControllerError,
    consume_budget,
    create_experiment,
    load_config,
    load_record,
    read_json,
    reserve_budget,
    save_record,
    transition,
    validate_notebook,
    verify_snapshot,
)
from experiment_controller.kaggle import (
    _next_page_token,
    launch,
    prepare_kernel_directory,
    parse_remote_status,
    resolve_kernel_settings,
)
from experiment_controller.metrics import decide, parse_metrics
from experiment_controller.review import request_review


def valid_metrics(experiment_id: str, protocol: str = "fixed_cv") -> dict:
    return {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "primary_metric": 0.805,
        "runtime_seconds": 3600,
        "reproducible": True,
        "validation": {"protocol": protocol},
        "specimen_metrics": {
            "44b6": {"primary_metric": 0.81, "baseline_primary_metric": 0.80},
            "6bba": {"primary_metric": 0.82, "baseline_primary_metric": 0.81},
        },
    }


def test_validate_notebook_requires_structured_contract(project_factory):
    root, _ = project_factory()
    result = validate_notebook(root / "src" / "run.ipynb", require_metrics_contract=True)
    assert result["code_cells"] == 1


def test_metrics_contract_must_be_final_code_cell(project_factory):
    root, _ = project_factory()
    path = root / "src" / "run.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    notebook["cells"].append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["later_variable = 1\n"],
        }
    )
    path.write_text(json.dumps(notebook), encoding="utf-8")
    with pytest.raises(ControllerError, match="final code cell"):
        validate_notebook(path, require_metrics_contract=True)


def test_metrics_contract_validation_rejects_python_syntax_error(project_factory):
    root, _ = project_factory()
    path = root / "src" / "run.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    notebook["cells"][0]["source"].insert(0, "broken = {\n")
    path.write_text(json.dumps(notebook), encoding="utf-8")
    with pytest.raises(ControllerError, match="not valid Python"):
        validate_notebook(path, require_metrics_contract=True)


def test_configuration_guard_requires_prior_explicit_environment_assignment(tmp_path):
    path = tmp_path / "guard.ipynb"
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
                "source": ["import os\nos.environ['BIOHUB_PRESENT'] = '1'\n"],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "_EXPECTED_NUMERIC = {\n",
                    "    'BIOHUB_PRESENT': 1.0,\n",
                    "    'BIOHUB_MISSING': 0.12,\n",
                    "}\n",
                    "_EXPECTED_TEXT = {}\n",
                    "raise RuntimeError('Configuration drift detected')\n",
                ],
            },
        ],
    }
    path.write_text(json.dumps(notebook), encoding="utf-8")
    with pytest.raises(ControllerError, match="BIOHUB_MISSING"):
        validate_notebook(path)


def test_configuration_guard_accepts_prior_explicit_environment_assignments(tmp_path):
    path = tmp_path / "guard.ipynb"
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
                "source": [
                    "import os\n",
                    "os.environ['BIOHUB_NUMERIC'] = '0.12'\n",
                    "os.environ['BIOHUB_TEXT'] = 'enabled'\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "_EXPECTED_NUMERIC = {'BIOHUB_NUMERIC': 0.12}\n",
                    "_EXPECTED_TEXT = {'BIOHUB_TEXT': 'enabled'}\n",
                    "raise RuntimeError('Configuration drift detected')\n",
                ],
            },
        ],
    }
    path.write_text(json.dumps(notebook), encoding="utf-8")
    result = validate_notebook(path)
    assert result["code_cells"] == 2


def test_create_experiment_freezes_source_and_config(project_factory):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    assert record["state"] == "PROPOSED"
    assert (root / record["snapshot_source"]).exists()
    verify_snapshot(root, record)


def test_launch_recovers_pre_submission_remote_failure(project_factory, monkeypatch):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    record["state"] = "REMOTE_FAILED"
    record["smoke_test"] = {"status": "PASSED"}
    record["budget"]["reserved"] = True
    save_record(root, record)

    monkeypatch.setattr(kaggle_module, "kaggle_command", lambda: ["kaggle"])
    monkeypatch.setattr(
        kaggle_module,
        "prepare_kernel_directory",
        lambda root, record, config: (root / "kernel", "tester/kernel"),
    )
    monkeypatch.setattr(
        kaggle_module,
        "_run_kaggle",
        lambda *args, **kwargs: CompletedProcess(
            args=["kaggle"], returncode=0, stdout="", stderr=""
        ),
    )

    launched = launch(root, record["experiment_id"])
    assert launched["state"] == "SUBMITTED"
    assert launched["budget"]["reserved"] is True
    assert any(
        item.get("note") == "Retrying a pre-submission Kaggle push failure"
        for item in launched["state_history"]
    )


def test_duplicate_signature_is_rejected(project_factory):
    root, config = project_factory()
    create_experiment(config, root=root)
    data = config.read_text(encoding="utf-8").replace("exp_100_test", "exp_101_test")
    second = root / "configs" / "exp_101_test.yaml"
    second.write_text(data, encoding="utf-8")
    with pytest.raises(ControllerError, match="Duplicate experiment"):
        create_experiment(second, root=root)


def test_snapshot_tampering_is_detected(project_factory):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    (root / record["snapshot_source"]).write_text("tampered", encoding="utf-8")
    with pytest.raises(ControllerError, match="modified"):
        verify_snapshot(root, record)


def test_metrics_parser_rejects_protocol_mismatch(project_factory):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    source = root / "bad_metrics.json"
    payload = valid_metrics(record["experiment_id"], protocol="wrong")
    source.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ControllerError, match="protocol mismatch"):
        parse_metrics(root, record["experiment_id"], source)


def test_metrics_parser_rejects_nonfinite_primary(project_factory):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    source = root / "bad_metrics.json"
    payload = valid_metrics(record["experiment_id"])
    payload["primary_metric"] = float("nan")
    source.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ControllerError, match="finite"):
        parse_metrics(root, record["experiment_id"], source)


def test_keep_decision_uses_paired_specimen_guards(project_factory):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    metrics = valid_metrics(record["experiment_id"])
    decision, baseline, delta = decide(root, record["experiment_id"], metrics)
    assert decision == "KEEP"
    assert baseline == pytest.approx(0.8)
    assert delta == pytest.approx(0.005)


def test_specimen_regression_rejects_overall_gain(project_factory):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    metrics = valid_metrics(record["experiment_id"])
    metrics["specimen_metrics"]["6bba"] = {
        "primary_metric": 0.80,
        "baseline_primary_metric": 0.81,
    }
    decision, _, _ = decide(root, record["experiment_id"], metrics)
    assert decision == "REJECT"


def test_changed_protocol_requires_paired_baseline(project_factory):
    root, config = project_factory(protocol="new_cv")
    record = create_experiment(config, root=root)
    metrics = valid_metrics(record["experiment_id"], protocol="new_cv")
    with pytest.raises(ControllerError, match="paired baseline_primary_metric"):
        decide(root, record["experiment_id"], metrics)
    metrics["baseline_primary_metric"] = 0.8
    assert decide(root, record["experiment_id"], metrics)[0] == "KEEP"


def test_budget_reservation_and_consumption(project_factory):
    root, _ = project_factory()
    reserve_budget(root, "exp_100_test", 2.0)
    budget = read_json(root / "GPU_BUDGET.json")
    assert budget["reserved_hours"]["exp_100_test"] == 2.0
    consume_budget(root, "exp_100_test", 1.5)
    budget = read_json(root / "GPU_BUDGET.json")
    assert "exp_100_test" not in budget["reserved_hours"]
    assert budget["remaining_hours"] == pytest.approx(18.5)


def test_budget_consumption_is_idempotent(project_factory):
    root, _ = project_factory()
    reserve_budget(root, "exp_100_test", 2.0)

    consume_budget(root, "exp_100_test", 1.5)
    consume_budget(root, "exp_100_test", 1.5)

    budget = read_json(root / "GPU_BUDGET.json")
    assert budget["remaining_hours"] == pytest.approx(18.5)
    assert [item["experiment_id"] for item in budget["consumed"]] == ["exp_100_test"]


def test_budget_rejects_conflicting_second_consumption(project_factory):
    root, _ = project_factory()
    reserve_budget(root, "exp_100_test", 2.0)
    consume_budget(root, "exp_100_test", 1.5)

    with pytest.raises(ControllerError, match="already consumed"):
        consume_budget(root, "exp_100_test", 1.25)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('Kernel has status "complete"', "COMPLETE"),
        ('Kernel has status "running"', "RUNNING"),
        ('Kernel has status "queued"', "PENDING"),
        ('Kernel has status "error"', "ERROR"),
        ("unexpected response", "UNKNOWN"),
    ],
)
def test_remote_status_mapping(text, expected):
    assert parse_remote_status(text) == expected


def test_error_status_is_persisted_before_remote_failure(project_factory, monkeypatch):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    record["state"] = "RUNNING"
    record["remote"] = {
        "kernel_id": "owner/kernel",
        "status": "RUNNING",
        "submitted_at": "2026-01-01T00:00:00+00:00",
        "last_checked_at": None,
    }
    save_record(root, record)
    monkeypatch.setattr(
        kaggle_module,
        "_run_kaggle",
        lambda *args, **kwargs: CompletedProcess(
            args=["kaggle"], returncode=0, stdout='kernel has status "ERROR"', stderr=""
        ),
    )

    failed = kaggle_module.check_status(root, record["experiment_id"])

    assert failed["state"] == "REMOTE_FAILED"
    assert failed["remote"]["status"] == "ERROR"
    assert failed["remote"]["last_checked_at"] is not None


def _write_submission_budget(root: Path, submissions: list[dict]) -> None:
    (root / "SUBMISSION_BUDGET.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "timezone": "America/New_York",
                "max_submissions_per_day": 3,
                "submissions": submissions,
            }
        ),
        encoding="utf-8",
    )


def test_local_date_uses_configured_zone():
    zone = kaggle_module._resolve_zone("America/New_York")
    # 03:17 UTC is still the previous calendar day in New York.
    assert kaggle_module._local_date("2026-09-02 03:17:53", zone) == "2026-09-01"


def test_gate_submission_blocks_duplicate_sha(project_factory, monkeypatch):
    root, _ = project_factory()
    _write_submission_budget(
        root,
        [{"local_date": "2000-01-01", "submission_sha256": "abc", "experiment_id": "exp_prior"}],
    )
    monkeypatch.setattr(kaggle_module, "fetch_remote_submissions", lambda *a, **k: [])
    with pytest.raises(ControllerError, match="Duplicate submission SHA256"):
        kaggle_module.gate_submission(root, competition="comp", candidate_sha256="ABC")


def test_gate_submission_blocks_when_daily_cap_reached(project_factory, monkeypatch):
    root, _ = project_factory()
    _write_submission_budget(root, [])
    fixed_now = "2026-09-07T16:00:00+00:00"
    monkeypatch.setattr(kaggle_module, "utc_now", lambda: fixed_now)
    monkeypatch.setattr(
        kaggle_module,
        "fetch_remote_submissions",
        lambda *a, **k: [{"date_utc": fixed_now, "status": "COMPLETE", "description": ""}] * 3,
    )
    with pytest.raises(ControllerError, match="Daily submission cap reached"):
        kaggle_module.gate_submission(root, competition="comp", candidate_sha256="new")


def test_gate_submission_allows_within_cap(project_factory, monkeypatch):
    root, _ = project_factory()
    _write_submission_budget(root, [])
    monkeypatch.setattr(kaggle_module, "fetch_remote_submissions", lambda *a, **k: [])
    verdict = kaggle_module.gate_submission(root, competition="comp", candidate_sha256="new")
    assert verdict["remaining"] == 3
    assert verdict["duplicate"] is False


def test_fetch_remote_submissions_forces_utf8(project_factory, monkeypatch):
    root, _ = project_factory()
    captured = {}
    monkeypatch.setattr(kaggle_module, "kaggle_command", lambda: ["kaggle"])

    def fake_run(*args, **kwargs):
        captured.update(kwargs)
        return CompletedProcess(
            args=["kaggle"],
            returncode=0,
            stdout="date,status,description\n2026-09-07,complete,0.935978 → 0.938733\n",
            stderr="",
        )

    monkeypatch.setattr(kaggle_module.subprocess, "run", fake_run)
    rows = kaggle_module.fetch_remote_submissions(root, "comp")

    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"
    assert captured["env"]["PYTHONIOENCODING"] == "utf-8"
    assert rows[0]["description"] == "0.935978 → 0.938733"


def test_state_lock_is_exclusive(project_factory):
    from experiment_controller.core import state_lock

    root, _ = project_factory()
    with state_lock(root):
        assert (root / ".controller.lock").exists()
        with pytest.raises(ControllerError, match="Could not acquire"):
            with state_lock(root, timeout=0.2):
                pass
    assert not (root / ".controller.lock").exists()


def test_kaggle_next_page_token_from_stdout():
    result = CompletedProcess(
        args=["kaggle"],
        returncode=0,
        stdout="Next Page Token = abc-123_DEF=\n",
        stderr="",
    )
    assert _next_page_token(result) == "abc-123_DEF="


def test_kaggle_next_page_token_absent():
    result = CompletedProcess(args=["kaggle"], returncode=0, stdout="done\n", stderr="")
    assert _next_page_token(result) is None


def test_kernel_settings_block_missing_dataset_references():
    config = {
        "kaggle": {
            "owner": "tester",
            "slug": "kernel",
            "dataset_sources": [],
            "required_dataset_sources": 4,
            "source_dataset_version_ids": [1, 2, 3, 4],
        }
    }
    with pytest.raises(ControllerError, match="at least 4 dataset_sources"):
        resolve_kernel_settings(config)


def test_kernel_settings_accept_t4_accelerator():
    settings = resolve_kernel_settings(
        {"kaggle": {"owner": "tester", "slug": "kernel", "accelerator": "NvidiaTeslaT4"}}
    )
    assert settings["accelerator"] == "NvidiaTeslaT4"


def test_kernel_settings_reject_unknown_accelerator():
    with pytest.raises(ControllerError, match="Unsupported kaggle.accelerator"):
        resolve_kernel_settings(
            {"kaggle": {"owner": "tester", "slug": "kernel", "accelerator": "Gpu"}}
        )


def test_kernel_staging_injects_experiment_id(project_factory):
    root, config = project_factory()
    notebook_path = root / "src" / "run.ipynb"
    notebook_text = notebook_path.read_text(encoding="utf-8")
    notebook_path.write_text(
        notebook_text.replace(
            "open('/kaggle/working/metrics.json', 'w')",
            "open('/kaggle/working/metrics.json', 'w'); experiment_id='__CONTROLLER_EXPERIMENT_ID__'",
        ),
        encoding="utf-8",
    )
    record = create_experiment(config, root=root)
    _, loaded_config = load_config(root / record["snapshot_config"], root)
    loaded_config["kaggle"]["inject_experiment_id"] = True
    kernel_dir, _ = prepare_kernel_directory(root, record, loaded_config)
    staged = (kernel_dir / "run.ipynb").read_text(encoding="utf-8")
    assert "__CONTROLLER_EXPERIMENT_ID__" not in staged
    assert record["experiment_id"] in staged


def test_kernel_staging_retry_preserves_prior_directory(project_factory):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    _, loaded_config = load_config(root / record["snapshot_config"], root)
    first_dir, _ = prepare_kernel_directory(root, record, loaded_config)
    second_dir, _ = prepare_kernel_directory(root, record, loaded_config)
    assert first_dir.name == "kaggle_kernel"
    assert second_dir.name == "kaggle_kernel_retry_001"
    assert first_dir.is_dir()
    assert second_dir.is_dir()


def test_invalid_state_transition_is_rejected(project_factory):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    with pytest.raises(ControllerError, match="Invalid state transition"):
        transition(root, record, "SUBMITTED")


def test_ready_experiment_can_receive_pre_launch_review(project_factory, monkeypatch):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    record["state"] = "READY"
    record["smoke_test"] = {"status": "PASSED"}
    save_record(root, record)
    monkeypatch.setattr(review_module, "claude_command", lambda: ["claude"])
    monkeypatch.setattr(
        review_module.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(
            args=["claude"], returncode=0, stdout="Summary\n\nVERDICT: PASS\n", stderr=""
        ),
    )

    reviewed = request_review(root, record["experiment_id"])

    assert reviewed["state"] == "READY"
    assert reviewed["review"]["status"] == "PASSED"


def test_claude_review_uses_explicit_utf8_decoding(project_factory, monkeypatch):
    root, config = project_factory()
    record = create_experiment(config, root=root)
    captured = {}
    monkeypatch.setattr(review_module, "claude_command", lambda: ["claude"])

    def fake_run(*args, **kwargs):
        captured.update(kwargs)
        return CompletedProcess(
            args=["claude"], returncode=0,
            stdout="Methodology: paired validation is sound. — review\n\nVERDICT: PASS\n",
            stderr="",
        )

    monkeypatch.setattr(review_module.subprocess, "run", fake_run)
    reviewed = request_review(root, record["experiment_id"])

    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"
    assert reviewed["review"]["status"] == "PASSED"
    assert reviewed["review"]["provider"] == "claude"
    assert (root / "experiments" / record["experiment_id"] / "claude-prompt.md").exists()
    assert (root / "experiments" / record["experiment_id"] / "claude-review-run.json").exists()
    assert (root / "CLAUDE_REVIEW.md").exists()


def test_codex_review_uses_read_only_command_and_provider_artifacts(project_factory, monkeypatch):
    root, config = project_factory()
    config_text = config.read_text(encoding="utf-8")
    config.write_text(
        config_text.replace(
            "require_claude_review: false",
            "require_codex_review: true\n  reviewer_provider: codex",
        ),
        encoding="utf-8",
    )
    record = create_experiment(config, root=root)
    assert record["review"]["required"] is True
    assert record["review"]["provider"] == "codex"
    captured = {}
    monkeypatch.setattr(review_module, "codex_command", lambda: [
        "codex", "exec", "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check", "-"
    ])

    def fake_run(*args, **kwargs):
        captured.update({"args": args, **kwargs})
        return CompletedProcess(args=args[0], returncode=0, stdout="Independent review\n\nVERDICT: PASS\n", stderr="")

    monkeypatch.setattr(review_module.subprocess, "run", fake_run)
    reviewed = request_review(root, record["experiment_id"])

    assert captured["args"] == (
        ["codex", "exec", "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check", "-"],
    )
    assert "Challenge the proposed strategy, methodology, and implementation independently" in captured["input"]
    assert "Claude-authored strategy, Codex objections, and resulting revisions" in captured["input"]
    assert "explicit ``CONSENSUS``" in captured["input"]
    assert "high-risk or framework-changing experiment may bundle coupled" in captured["input"]
    for gate in ("leakage", "provenance", "hash-integrity", "budget", "leaderboard-submission", "promotion"):
        assert gate in captured["input"]
    exp_dir = root / "experiments" / record["experiment_id"]
    assert reviewed["review"]["provider"] == "codex"
    assert (exp_dir / "codex-prompt.md").exists()
    assert (exp_dir / "codex-review-run.json").exists()
    assert (root / "CODEX_REVIEW.md").exists()
    assert not (root / "CLAUDE_REVIEW.md").exists()
