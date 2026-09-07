from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml


EXPERIMENT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,79}$")

TERMINAL_STATES = {
    "EVALUATED",
    "KEEP",
    "REJECT",
    "INCONCLUSIVE",
    "LOCAL_FAILED",
    "REMOTE_FAILED",
    "TIMEOUT",
    "INVALID_METRIC",
    "BUDGET_BLOCKED",
    "MANUAL_REVIEW_REQUIRED",
}

TRANSITIONS = {
    "PROPOSED": {"REVIEWED", "LOCAL_TESTING", "MANUAL_REVIEW_REQUIRED"},
    "REVIEWED": {"LOCAL_TESTING", "MANUAL_REVIEW_REQUIRED"},
    "LOCAL_TESTING": {"READY", "LOCAL_FAILED"},
    "READY": {"SUBMITTED", "BUDGET_BLOCKED", "MANUAL_REVIEW_REQUIRED", "LOCAL_FAILED", "REMOTE_FAILED"},
    "SUBMITTED": {"RUNNING", "COLLECTING", "REMOTE_FAILED", "TIMEOUT"},
    "RUNNING": {"COLLECTING", "REMOTE_FAILED", "TIMEOUT"},
    "COLLECTING": {"EVALUATED", "INVALID_METRIC", "REMOTE_FAILED"},
    "EVALUATED": {"KEEP", "REJECT", "INCONCLUSIVE"},
    "MANUAL_REVIEW_REQUIRED": {"REVIEWED"},
    "BUDGET_BLOCKED": {"READY"},
    "REMOTE_FAILED": {"READY"},
}


class ControllerError(RuntimeError):
    """Expected validation or execution failure with a user-actionable message."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def find_project_root(start: str | Path | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "GOAL.md").exists() and (candidate / "GPU_BUDGET.json").exists():
            return candidate
    raise ControllerError(f"Could not find project root from {current}")


def read_json(path: Path, *, default: Any = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise ControllerError(f"Required JSON file is missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControllerError(f"Cannot read valid JSON from {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            handle.write(payload)
            temp_name = handle.name
        os.replace(temp_name, path)
    finally:
        if temp_name and Path(temp_name).exists():
            Path(temp_name).unlink(missing_ok=True)


@contextmanager
def state_lock(
    root: Path,
    *,
    name: str = ".controller.lock",
    timeout: float = 30.0,
    stale_after: float = 600.0,
    poll: float = 0.1,
) -> Iterator[None]:
    """Cross-process advisory lock guarding read-modify-write on shared state files.

    The controller is explicitly multi-agent (Codex, the reviewer, the controller itself).
    ``write_json`` is atomic per write, but the read -> mutate -> write cycles on
    ``GPU_BUDGET.json`` / ``results.json`` / ``CURRENT_BEST.json`` are not, so two writers
    interleaving would silently drop an update. Every such cycle must run inside this lock.

    ``timeout`` bounds how long we wait to acquire a contended lock before giving up.
    Only a lock older than ``stale_after`` (its owner presumably crashed) is reclaimed --
    kept well above ``timeout`` so a briefly-held lock is waited on, never stolen.
    """
    lock_path = root / name
    deadline = time.monotonic() + timeout
    fd: int | None = None
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            try:
                age = time.time() - lock_path.stat().st_mtime
            except FileNotFoundError:
                continue
            if age > stale_after:
                try:
                    lock_path.unlink()
                except OSError:
                    pass
                continue
            if time.monotonic() >= deadline:
                raise ControllerError(f"Could not acquire controller state lock within {timeout:.0f}s: {lock_path}")
            time.sleep(poll)
    try:
        os.write(fd, f"pid={os.getpid()} acquired={utc_now()}\n".encode("utf-8"))
        yield
    finally:
        os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_yaml_raw(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ControllerError(f"Cannot read valid YAML from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ControllerError(f"Experiment config must be a YAML mapping: {path}")
    return value


def load_config(path: str | Path, root: Path | None = None) -> tuple[Path, dict[str, Any]]:
    project_root = root or find_project_root()
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = project_root / config_path
    config_path = config_path.resolve()
    if not config_path.exists():
        raise ControllerError(f"Experiment config does not exist: {config_path}")
    config = _load_yaml_raw(config_path)
    validate_config(config, project_root)
    return config_path, config


def _require(mapping: dict[str, Any], key: str, context: str) -> Any:
    value = mapping.get(key)
    if value is None or value == "":
        raise ControllerError(f"Missing required field {context}.{key}")
    return value


def validate_config(config: dict[str, Any], root: Path) -> None:
    if config.get("schema_version") != 1:
        raise ControllerError("Only experiment config schema_version=1 is supported")
    experiment_id = str(_require(config, "experiment_id", "config"))
    if not EXPERIMENT_ID_RE.fullmatch(experiment_id):
        raise ControllerError(
            "experiment_id must be 3-80 lowercase letters, digits, underscores, or hyphens"
        )
    _require(config, "hypothesis", "config")
    if not isinstance(config.get("change"), dict):
        raise ControllerError("config.change must be a mapping")
    source = root / str(_require(config, "source_notebook", "config"))
    if not source.exists():
        raise ControllerError(f"source_notebook does not exist: {source}")
    if source.suffix.lower() != ".ipynb":
        raise ControllerError("source_notebook must be an .ipynb file")
    validation = config.get("validation")
    if not isinstance(validation, dict):
        raise ControllerError("config.validation must be a mapping")
    _require(validation, "protocol", "validation")
    _require(validation, "primary_metric", "validation")
    budget = config.get("budget")
    if not isinstance(budget, dict):
        raise ControllerError("config.budget must be a mapping")
    expected = budget.get("expected_gpu_hours")
    if not isinstance(expected, (int, float)) or not math.isfinite(float(expected)) or expected < 0:
        raise ControllerError("budget.expected_gpu_hours must be a finite non-negative number")
    success = config.get("success")
    if not isinstance(success, dict):
        raise ControllerError("config.success must be a mapping")
    for key in ("minimum_improvement", "regression_threshold"):
        if not isinstance(success.get(key), (int, float)):
            raise ControllerError(f"success.{key} must be numeric")


def experiment_dir(root: Path, experiment_id: str) -> Path:
    if not EXPERIMENT_ID_RE.fullmatch(experiment_id):
        raise ControllerError(f"Invalid experiment id: {experiment_id}")
    return root / "experiments" / experiment_id


def record_path(root: Path, experiment_id: str) -> Path:
    return experiment_dir(root, experiment_id) / "experiment.json"


def load_record(root: Path, experiment_id: str) -> dict[str, Any]:
    value = read_json(record_path(root, experiment_id))
    if not isinstance(value, dict):
        raise ControllerError(f"Experiment record is not an object: {experiment_id}")
    return value


def save_record(root: Path, record: dict[str, Any]) -> None:
    record["updated_at"] = utc_now()
    write_json(record_path(root, str(record["experiment_id"])), record)


def transition(root: Path, record: dict[str, Any], new_state: str, *, note: str | None = None) -> None:
    current = str(record.get("state"))
    if new_state != current and new_state not in TRANSITIONS.get(current, set()):
        raise ControllerError(f"Invalid state transition for {record['experiment_id']}: {current} -> {new_state}")
    if new_state != current:
        record.setdefault("state_history", []).append(
            {"from": current, "to": new_state, "at": utc_now(), "note": note}
        )
        record["state"] = new_state
    save_record(root, record)


def _git_commit(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={root.as_posix()}", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def experiment_signature(config: dict[str, Any]) -> str:
    canonical = {
        "parent": config.get("parent"),
        "hypothesis": str(config.get("hypothesis", "")).strip(),
        "change": config.get("change"),
        "validation_protocol": config.get("validation", {}).get("protocol"),
    }
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _existing_signatures(root: Path) -> Iterable[tuple[str, str]]:
    experiments_root = root / "experiments"
    if not experiments_root.exists():
        return []
    found: list[tuple[str, str]] = []
    for path in experiments_root.glob("*/experiment.json"):
        try:
            record = read_json(path)
        except ControllerError:
            continue
        if isinstance(record, dict) and record.get("signature"):
            found.append((str(record.get("experiment_id")), str(record["signature"])))
    return found


def create_experiment(
    config_path: str | Path,
    *,
    root: Path | None = None,
    allow_duplicate: bool = False,
) -> dict[str, Any]:
    project_root = root or find_project_root()
    resolved_config, config = load_config(config_path, project_root)
    experiment_id = str(config["experiment_id"])
    target = experiment_dir(project_root, experiment_id)
    if target.exists():
        raise ControllerError(f"Experiment directory already exists: {target}")

    signature = experiment_signature(config)
    if not allow_duplicate:
        for other_id, other_signature in _existing_signatures(project_root):
            if other_signature == signature:
                raise ControllerError(
                    f"Duplicate experiment hypothesis/change matches {other_id}; use --allow-duplicate only with justification"
                )

    source_path = (project_root / str(config["source_notebook"])).resolve()
    snapshot = target / "snapshot"
    source_snapshot = snapshot / "source" / source_path.name
    config_snapshot = snapshot / "config.yaml"
    source_snapshot.parent.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source_path, source_snapshot)
    shutil.copy2(resolved_config, config_snapshot)

    extras: list[dict[str, str]] = []
    for item in config.get("kaggle", {}).get("extra_files", []) or []:
        original = (project_root / str(item)).resolve()
        if not original.exists() or not original.is_file():
            raise ControllerError(f"Configured kaggle.extra_files entry is missing: {original}")
        destination = snapshot / "extra_files" / original.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, destination)
        extras.append({"path": destination.relative_to(project_root).as_posix(), "sha256": sha256_file(destination)})

    manifest = {
        "created_at": utc_now(),
        "files": [
            {"role": "config", "path": config_snapshot.relative_to(project_root).as_posix(), "sha256": sha256_file(config_snapshot)},
            {"role": "source_notebook", "path": source_snapshot.relative_to(project_root).as_posix(), "sha256": sha256_file(source_snapshot)},
            *[{"role": "extra_file", **entry} for entry in extras],
        ],
    }
    write_json(snapshot / "manifest.json", manifest)

    record = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "parent": config.get("parent"),
        "state": "PROPOSED",
        "hypothesis": config["hypothesis"],
        "change": config["change"],
        "signature": signature,
        "config": resolved_config.relative_to(project_root).as_posix(),
        "snapshot_config": config_snapshot.relative_to(project_root).as_posix(),
        "snapshot_source": source_snapshot.relative_to(project_root).as_posix(),
        "snapshot_manifest": (snapshot / "manifest.json").relative_to(project_root).as_posix(),
        "git_commit": _git_commit(project_root),
        "validation_protocol": config["validation"]["protocol"],
        "budget": {"expected_gpu_hours": float(config["budget"]["expected_gpu_hours"]), "reserved": False},
        "review": {"required": bool(config.get("admission", {}).get("require_claude_review", False)), "status": "PENDING"},
        "smoke_test": {"status": "PENDING"},
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "state_history": [],
    }
    write_json(target / "experiment.json", record)
    return record


def verify_snapshot(root: Path, record: dict[str, Any]) -> None:
    manifest_path = root / str(record["snapshot_manifest"])
    manifest = read_json(manifest_path)
    for entry in manifest.get("files", []):
        path = root / str(entry["path"])
        if not path.exists():
            raise ControllerError(f"Immutable snapshot file is missing: {path}")
        actual = sha256_file(path)
        if actual != entry.get("sha256"):
            raise ControllerError(f"Immutable snapshot was modified: {path}")


def _guard_expected_environment_keys(source: str) -> set[str]:
    if "Configuration drift detected" not in source:
        return set()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ControllerError(f"Configuration guard cell is not valid Python: {exc}") from exc
    expected: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = {target.id for target in node.targets if isinstance(target, ast.Name)}
        if not names.intersection({"_EXPECTED_NUMERIC", "_EXPECTED_TEXT"}):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        for key in node.value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                expected.add(key.value)
    return expected


def _explicit_environment_assignments(source: str) -> set[str]:
    pattern = re.compile(
        r"(?:\b[A-Za-z_][A-Za-z0-9_]*\.)?environ\[\s*['\"]([^'\"]+)['\"]\s*\]\s*="
    )
    return set(pattern.findall(source))


def validate_notebook(path: Path, *, require_metrics_contract: bool = False) -> dict[str, int]:
    notebook = read_json(path)
    if not isinstance(notebook, dict) or notebook.get("nbformat") != 4:
        raise ControllerError(f"Unsupported or invalid notebook: {path}")
    cells = notebook.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ControllerError(f"Notebook has no cells: {path}")
    code_cells = 0
    error_outputs = 0
    source_text: list[str] = []
    metrics_contract_indices: list[int] = []
    code_indices: list[int] = []
    prior_code_source = ""
    for index, cell in enumerate(cells):
        if cell.get("cell_type") == "code":
            code_cells += 1
            code_indices.append(index)
            cell_source = "".join(cell.get("source", []))
            if require_metrics_contract:
                try:
                    ast.parse(cell_source)
                except SyntaxError as exc:
                    raise ControllerError(
                        f"Notebook code cell {index} is not valid Python: {exc.msg} "
                        f"(line {exc.lineno})"
                    ) from exc
            source_text.extend(cell.get("source", []))
            expected_environment = _guard_expected_environment_keys(cell_source)
            if expected_environment:
                assigned_environment = _explicit_environment_assignments(prior_code_source)
                missing_environment = sorted(expected_environment - assigned_environment)
                if missing_environment:
                    raise ControllerError(
                        "Configuration guard expects environment keys that are not explicitly "
                        f"assigned in an earlier code cell: {missing_environment}"
                    )
            if "metrics.json" in cell_source:
                metrics_contract_indices.append(index)
            for output in cell.get("outputs", []) or []:
                if output.get("output_type") == "error":
                    error_outputs += 1
            prior_code_source += cell_source + "\n"
    if code_cells == 0:
        raise ControllerError(f"Notebook has no code cells: {path}")
    if error_outputs:
        raise ControllerError(f"Notebook contains {error_outputs} saved error output(s): {path}")
    if require_metrics_contract and "metrics.json" not in "".join(source_text):
        raise ControllerError(f"Notebook does not write the required structured metrics.json: {path}")
    if require_metrics_contract and metrics_contract_indices[-1] != code_indices[-1]:
        raise ControllerError(
            f"The metrics.json contract must be in the notebook's final code cell so it runs after metric definitions: {path}"
        )
    return {"cells": len(cells), "code_cells": code_cells, "saved_error_outputs": error_outputs}


def _command_from_config(root: Path, record: dict[str, Any], config: dict[str, Any]) -> list[str]:
    configured = config.get("local", {}).get("smoke_test")
    source = str((root / str(record["snapshot_source"])).resolve())
    if not configured:
        return [sys.executable, str(root / "scripts" / "validate_notebook.py"), source, "--require-metrics-contract"]
    if not isinstance(configured, list) or not all(isinstance(item, str) for item in configured):
        raise ControllerError("local.smoke_test must be a list of command arguments")
    replacements = {
        "{python}": sys.executable,
        "{source_notebook}": source,
        "{experiment_dir}": str(experiment_dir(root, str(record["experiment_id"])).resolve()),
        "{project_root}": str(root.resolve()),
    }
    return [replacements.get(item, item) for item in configured]


def run_smoke_test(root: Path, experiment_id: str) -> dict[str, Any]:
    record = load_record(root, experiment_id)
    _, config = load_config(root / str(record["snapshot_config"]), root)
    if record["review"].get("required") and record["review"].get("status") != "PASSED":
        transition(root, record, "MANUAL_REVIEW_REQUIRED", note="Claude review required before smoke test")
        raise ControllerError(f"{experiment_id} requires a completed Claude review before smoke testing")
    verify_snapshot(root, record)
    transition(root, record, "LOCAL_TESTING")
    command = _command_from_config(root, record, config)
    result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    log = (
        f"[{utc_now()}] smoke command: {json.dumps(command)}\n"
        f"exit_code={result.returncode}\nSTDOUT\n{result.stdout}\nSTDERR\n{result.stderr}\n"
    )
    append_text(experiment_dir(root, experiment_id) / "smoke-test.log", log)
    record = load_record(root, experiment_id)
    record["smoke_test"] = {
        "status": "PASSED" if result.returncode == 0 else "FAILED",
        "command": command,
        "completed_at": utc_now(),
        "exit_code": result.returncode,
    }
    if result.returncode == 0:
        transition(root, record, "READY")
    else:
        transition(root, record, "LOCAL_FAILED", note="Smoke-test command failed")
        raise ControllerError(f"Smoke test failed for {experiment_id}; see smoke-test.log")
    return record


def reserve_budget(root: Path, experiment_id: str, expected_hours: float, *, user_approved: bool = False) -> None:
    path = root / "GPU_BUDGET.json"
    with state_lock(root):
        budget = read_json(path)
        reserved = budget.setdefault("reserved_hours", {})
        if experiment_id in reserved:
            return
        approval_threshold = float(budget.get("require_user_approval_above_hours", math.inf))
        max_single = float(budget.get("max_single_experiment_hours", math.inf))
        if expected_hours > approval_threshold and not user_approved:
            raise ControllerError(
                f"Experiment requests {expected_hours:.2f} GPU h; explicit user approval is required above {approval_threshold:.2f} h"
            )
        if expected_hours > max_single and not user_approved:
            raise ControllerError(
                f"Experiment requests {expected_hours:.2f} GPU h, above max_single_experiment_hours={max_single:.2f}"
            )
        active_reserved = sum(float(value) for value in reserved.values())
        remaining = float(budget["remaining_hours"])
        reserve = float(budget["reserve_hours"])
        if remaining - active_reserved - expected_hours < reserve:
            raise ControllerError(
                f"Budget blocked: remaining={remaining:.2f}, active reservations={active_reserved:.2f}, "
                f"requested={expected_hours:.2f}, reserve={reserve:.2f} GPU h"
            )
        reserved[experiment_id] = expected_hours
        write_json(path, budget)


def release_budget(root: Path, experiment_id: str) -> None:
    path = root / "GPU_BUDGET.json"
    with state_lock(root):
        budget = read_json(path)
        budget.setdefault("reserved_hours", {}).pop(experiment_id, None)
        write_json(path, budget)


def consume_budget(root: Path, experiment_id: str, actual_hours: float) -> None:
    if not math.isfinite(actual_hours) or actual_hours < 0:
        raise ControllerError("Actual GPU hours must be finite and non-negative")
    path = root / "GPU_BUDGET.json"
    with state_lock(root):
        budget = read_json(path)
        prior = [
            item
            for item in budget.setdefault("consumed", [])
            if item.get("experiment_id") == experiment_id
        ]
        if prior:
            prior_hours = float(prior[-1]["actual_hours"])
            if not math.isclose(prior_hours, actual_hours, rel_tol=0.0, abs_tol=1e-12):
                raise ControllerError(
                    f"GPU budget was already consumed for {experiment_id}: "
                    f"recorded={prior_hours}, requested={actual_hours}"
                )
            budget.setdefault("reserved_hours", {}).pop(experiment_id, None)
            write_json(path, budget)
            return
        reserved = budget.setdefault("reserved_hours", {}).pop(experiment_id, None)
        budget["remaining_hours"] = max(0.0, float(budget["remaining_hours"]) - actual_hours)
        budget.setdefault("consumed", []).append(
            {"experiment_id": experiment_id, "reserved_hours": reserved, "actual_hours": actual_hours, "recorded_at": utc_now()}
        )
        write_json(path, budget)


def command_prefix(name: str, module_name: str | None = None, env_name: str | None = None) -> list[str]:
    if env_name and os.environ.get(env_name):
        return [os.environ[env_name]]
    executable = shutil.which(name)
    if executable:
        return [executable]
    if module_name and importlib.util.find_spec(module_name) is not None:
        return [sys.executable, "-m", module_name]
    hint = f" Set {env_name}." if env_name else ""
    raise ControllerError(f"Required command is unavailable: {name}.{hint}")
