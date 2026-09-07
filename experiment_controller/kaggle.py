from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # Python 3.9+
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - fallback when tzdata is unavailable
    ZoneInfo = None  # type: ignore[assignment]

from .core import (
    ControllerError,
    append_text,
    command_prefix,
    consume_budget,
    experiment_dir,
    load_config,
    load_record,
    read_json,
    release_budget,
    reserve_budget,
    run_smoke_test,
    save_record,
    transition,
    utc_now,
    verify_snapshot,
    write_json,
    find_project_root,
)
from .metrics import evaluate, parse_metrics


KERNEL_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*/[A-Za-z0-9][A-Za-z0-9_-]*$")
KAGGLE_ACCELERATORS = {"NvidiaTeslaT4", "NvidiaTeslaP100"}
EXPERIMENT_ID_PLACEHOLDER = "__CONTROLLER_EXPERIMENT_ID__"
NEXT_PAGE_TOKEN_RE = re.compile(r"^Next Page Token = (\S+)\s*$", re.MULTILINE)


def kaggle_command() -> list[str]:
    config_dir = Path(os.environ.setdefault("KAGGLE_CONFIG_DIR", str(find_project_root() / ".kaggle")))
    config_dir.mkdir(parents=True, exist_ok=True)
    return command_prefix("kaggle", "kaggle", "KAGGLE_COMMAND")


def resolve_kernel_settings(config: dict[str, Any]) -> dict[str, Any]:
    settings = dict(config.get("kaggle") or {})
    owner = settings.get("owner")
    if not owner and settings.get("owner_env"):
        owner = os.environ.get(str(settings["owner_env"]))
    if not owner:
        raise ControllerError(
            "Kaggle owner is unset. Set KAGGLE_USERNAME or fill kaggle.owner in the experiment config."
        )
    slug = settings.get("slug")
    if not slug:
        raise ControllerError("kaggle.slug is required")
    kernel_id = f"{owner}/{slug}"
    if not KERNEL_REF_RE.fullmatch(kernel_id):
        raise ControllerError(f"Invalid Kaggle kernel id: {kernel_id}")
    dataset_sources = settings.get("dataset_sources") or []
    required = int(settings.get("required_dataset_sources", 0))
    if len(dataset_sources) < required:
        source_ids = settings.get("source_dataset_version_ids") or []
        hint = f" Resolve notebook dataset version IDs {source_ids} to owner/dataset-slug references." if source_ids else ""
        raise ControllerError(
            f"Kaggle launch needs at least {required} dataset_sources, but config has {len(dataset_sources)}.{hint}"
        )
    accelerator = settings.get("accelerator")
    if accelerator is not None and accelerator not in KAGGLE_ACCELERATORS:
        raise ControllerError(
            f"Unsupported kaggle.accelerator={accelerator!r}; expected one of {sorted(KAGGLE_ACCELERATORS)}"
        )
    settings["owner"] = owner
    settings["kernel_id"] = kernel_id
    settings["dataset_sources"] = dataset_sources
    return settings


def prepare_kernel_directory(root: Path, record: dict[str, Any], config: dict[str, Any]) -> tuple[Path, str]:
    verify_snapshot(root, record)
    settings = resolve_kernel_settings(config)
    experiment_path = experiment_dir(root, str(record["experiment_id"]))
    target = experiment_path / "kaggle_kernel"
    retry_index = 0
    while target.exists():
        retry_index += 1
        target = experiment_path / f"kaggle_kernel_retry_{retry_index:03d}"
    target.mkdir(parents=True)
    source = root / str(record["snapshot_source"])
    notebook_name = source.name
    staged_notebook = target / notebook_name
    shutil.copy2(source, staged_notebook)
    notebook_text = staged_notebook.read_text(encoding="utf-8")
    placeholder_count = notebook_text.count(EXPERIMENT_ID_PLACEHOLDER)
    inject_experiment_id = bool(settings.get("inject_experiment_id", False))
    if inject_experiment_id and placeholder_count != 1:
        raise ControllerError(
            f"Expected exactly one {EXPERIMENT_ID_PLACEHOLDER} placeholder in the staged notebook, "
            f"found {placeholder_count}"
        )
    if not inject_experiment_id and placeholder_count:
        raise ControllerError(
            f"Notebook contains {EXPERIMENT_ID_PLACEHOLDER} but kaggle.inject_experiment_id is not enabled"
        )
    if inject_experiment_id:
        staged_notebook.write_text(
            notebook_text.replace(EXPERIMENT_ID_PLACEHOLDER, str(record["experiment_id"])),
            encoding="utf-8",
        )

    manifest = json.loads((root / str(record["snapshot_manifest"])).read_text(encoding="utf-8"))
    for item in manifest.get("files", []):
        if item.get("role") == "extra_file":
            extra = root / str(item["path"])
            shutil.copy2(extra, target / extra.name)

    metadata = {
        "id": settings["kernel_id"],
        "title": settings.get("title") or str(record["experiment_id"]),
        "code_file": notebook_name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": bool(settings.get("is_private", True)),
        "enable_gpu": bool(settings.get("enable_gpu", True)),
        "enable_internet": bool(settings.get("enable_internet", False)),
        "machine_shape": settings.get("accelerator"),
        "dataset_sources": list(settings.get("dataset_sources") or []),
        "competition_sources": list(settings.get("competition_sources") or []),
        "kernel_sources": list(settings.get("kernel_sources") or []),
    }
    # Preserve the public reference image for explicitly pinned reproductions.
    if settings.get("docker_image"):
        metadata["docker_image"] = str(settings["docker_image"])
        metadata["docker_image_pinning_type"] = "original"
    write_json(target / "kernel-metadata.json", metadata)
    return target, settings["kernel_id"]


def _run_kaggle(root: Path, experiment_id: str, args: list[str], log_name: str) -> subprocess.CompletedProcess[str]:
    command = [*kaggle_command(), *args]
    result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    append_text(
        experiment_dir(root, experiment_id) / log_name,
        f"[{utc_now()}] command={json.dumps(command)}\nexit_code={result.returncode}\n"
        f"STDOUT\n{result.stdout}\nSTDERR\n{result.stderr}\n",
    )
    return result


def _next_page_token(result: subprocess.CompletedProcess[str]) -> str | None:
    text = f"{result.stdout}\n{result.stderr}"
    match = NEXT_PAGE_TOKEN_RE.search(text)
    return match.group(1) if match else None


def _mark_record_budget_consumed(
    root: Path,
    experiment_id: str,
    actual_hours: float,
) -> dict[str, Any]:
    consume_budget(root, experiment_id, actual_hours)
    record = load_record(root, experiment_id)
    record.setdefault("budget", {})["reserved"] = False
    record["budget"]["consumed_gpu_hours"] = actual_hours
    save_record(root, record)
    return record


def launch(
    root: Path,
    experiment_id: str,
    *,
    user_approved_budget: bool = False,
) -> dict[str, Any]:
    record = load_record(root, experiment_id)
    _, config = load_config(root / str(record["snapshot_config"]), root)
    resolve_kernel_settings(config)
    kaggle_command()

    if record.get("review", {}).get("required") and record["review"].get("status") != "PASSED":
        if record["state"] in {"PROPOSED", "REVIEWED", "READY"}:
            transition(root, record, "MANUAL_REVIEW_REQUIRED", note="Required Claude review is missing")
        raise ControllerError(f"{experiment_id} requires Claude review before remote launch")
    if record.get("smoke_test", {}).get("status") != "PASSED":
        record = run_smoke_test(root, experiment_id)
    if record["state"] == "BUDGET_BLOCKED" and record.get("smoke_test", {}).get("status") == "PASSED":
        transition(root, record, "READY", note="Retrying after budget configuration changed")
        record = load_record(root, experiment_id)
    if (
        record["state"] == "REMOTE_FAILED"
        and not record.get("remote")
        and record.get("smoke_test", {}).get("status") == "PASSED"
    ):
        record.setdefault("budget", {})["reserved"] = False
        save_record(root, record)
        transition(root, record, "READY", note="Retrying a pre-submission Kaggle push failure")
        record = load_record(root, experiment_id)
    if record["state"] != "READY":
        raise ControllerError(f"Experiment must be READY before launch, got {record['state']}")

    expected = float(config["budget"]["expected_gpu_hours"])
    try:
        reserve_budget(root, experiment_id, expected, user_approved=user_approved_budget)
    except ControllerError as exc:
        transition(root, record, "BUDGET_BLOCKED", note=str(exc))
        raise
    record["budget"]["reserved"] = True
    save_record(root, record)

    try:
        kernel_dir, kernel_id = prepare_kernel_directory(root, record, config)
        push_args = ["kernels", "push", "-p", str(kernel_dir)]
        accelerator = (config.get("kaggle") or {}).get("accelerator")
        if accelerator:
            push_args.extend(["--accelerator", str(accelerator)])
        result = _run_kaggle(root, experiment_id, push_args, "kaggle-launch.log")
    except Exception:
        release_budget(root, experiment_id)
        record = load_record(root, experiment_id)
        record.setdefault("budget", {})["reserved"] = False
        save_record(root, record)
        raise
    if result.returncode != 0:
        release_budget(root, experiment_id)
        record = load_record(root, experiment_id)
        record.setdefault("budget", {})["reserved"] = False
        save_record(root, record)
        transition(root, record, "REMOTE_FAILED", note="kaggle kernels push failed")
        raise ControllerError(f"Kaggle launch failed for {experiment_id}; see kaggle-launch.log")

    record = load_record(root, experiment_id)
    record["remote"] = {
        "kernel_id": kernel_id,
        "submitted_at": utc_now(),
        "status": "SUBMITTED",
        "last_checked_at": None,
    }
    transition(root, record, "SUBMITTED")
    return record


# Kaggle prints one authoritative status token, e.g.
#   `owner/slug has status "KernelWorkerStatus.COMPLETE"` or `... has status "complete"`.
# Match only that token instead of sniffing the whole log, so a benign line such as
# "0 errors" can never be misread as a failure.
_STATUS_TOKEN_RE = re.compile(
    r'status\s*[:=]?\s*"?\s*(?:KernelWorkerStatus\.)?([A-Za-z_]+)\s*"?',
    re.IGNORECASE,
)
_STATUS_MAP = {
    "complete": "COMPLETE",
    "completed": "COMPLETE",
    "error": "ERROR",
    "failed": "ERROR",
    "failure": "ERROR",
    "cancelled": "ERROR",
    "canceled": "ERROR",
    "cancelrequested": "ERROR",
    "cancelacknowledged": "ERROR",
    "running": "RUNNING",
    "queued": "PENDING",
    "pending": "PENDING",
    "submitted": "PENDING",
}


def parse_remote_status(output: str) -> str:
    match = _STATUS_TOKEN_RE.search(output or "")
    if not match:
        return "UNKNOWN"
    return _STATUS_MAP.get(match.group(1).lower(), "UNKNOWN")


def check_status(root: Path, experiment_id: str) -> dict[str, Any]:
    record = load_record(root, experiment_id)
    remote = record.get("remote") or {}
    kernel_id = remote.get("kernel_id")
    if not kernel_id:
        raise ControllerError(f"Experiment has no remote kernel id: {experiment_id}")
    if record["state"] not in {"SUBMITTED", "RUNNING"}:
        raise ControllerError(f"Status checks require SUBMITTED or RUNNING state, got {record['state']}")
    result = _run_kaggle(root, experiment_id, ["kernels", "status", kernel_id], "kaggle-status.log")
    if result.returncode != 0:
        raise ControllerError(f"Kaggle status command failed for {experiment_id}; see kaggle-status.log")
    status = parse_remote_status(result.stdout + "\n" + result.stderr)
    record = load_record(root, experiment_id)
    record.setdefault("remote", {})["status"] = status
    record["remote"]["last_checked_at"] = utc_now()
    if status == "RUNNING" and record["state"] == "SUBMITTED":
        transition(root, record, "RUNNING")
    elif status == "ERROR":
        save_record(root, record)
        expected = float(record.get("budget", {}).get("expected_gpu_hours", 0.0))
        record = _mark_record_budget_consumed(root, experiment_id, expected)
        transition(root, record, "REMOTE_FAILED", note="Kaggle reported an error state")
    else:
        save_record(root, record)
    return record


def collect(root: Path, experiment_id: str, *, promote: bool = False) -> dict[str, Any]:
    record = load_record(root, experiment_id)
    remote = record.get("remote") or {}
    kernel_id = remote.get("kernel_id")
    if not kernel_id:
        raise ControllerError(f"Experiment has no remote kernel id: {experiment_id}")
    if remote.get("status") != "COMPLETE":
        record = check_status(root, experiment_id)
        remote = record.get("remote") or {}
    if remote.get("status") != "COMPLETE":
        raise ControllerError(f"Kaggle kernel is not complete; current status is {remote.get('status')}")

    artifacts = experiment_dir(root, experiment_id) / "artifacts"
    resuming_collection = record["state"] == "COLLECTING"
    if artifacts.exists() and any(artifacts.iterdir()) and not resuming_collection:
        raise ControllerError(f"Artifacts directory is not empty; refusing to overwrite: {artifacts}")
    artifacts.mkdir(parents=True, exist_ok=True)
    if not resuming_collection:
        transition(root, record, "COLLECTING")

    page_token: str | None = None
    seen_page_tokens: set[str] = set()
    while True:
        output_args = [
            "kernels",
            "output",
            kernel_id,
            "-p",
            str(artifacts),
            "--page-size",
            "200",
        ]
        if page_token:
            output_args.extend(["--page-token", page_token])
        result = _run_kaggle(
            root,
            experiment_id,
            output_args,
            "kaggle-collect.log",
        )
        if result.returncode != 0:
            record = load_record(root, experiment_id)
            expected = float(record.get("budget", {}).get("expected_gpu_hours", 0.0))
            record = _mark_record_budget_consumed(root, experiment_id, expected)
            transition(root, record, "REMOTE_FAILED", note="kaggle kernels output failed")
            raise ControllerError(
                f"Kaggle output download failed for {experiment_id}; see kaggle-collect.log"
            )
        page_token = _next_page_token(result)
        if page_token is None:
            break
        if page_token in seen_page_tokens:
            raise ControllerError(f"Kaggle output pagination repeated page token: {page_token}")
        seen_page_tokens.add(page_token)

    try:
        metrics = parse_metrics(root, experiment_id)
    except ControllerError as exc:
        record = load_record(root, experiment_id)
        expected = float(record.get("budget", {}).get("expected_gpu_hours", 0.0))
        record = _mark_record_budget_consumed(root, experiment_id, expected)
        transition(root, record, "INVALID_METRIC", note=str(exc))
        raise
    runtime_hours = float(metrics.get("runtime_seconds", 0.0)) / 3600.0
    if runtime_hours <= 0:
        runtime_hours = float(record.get("budget", {}).get("expected_gpu_hours", 0.0))
    _mark_record_budget_consumed(root, experiment_id, runtime_hours)
    return evaluate(root, experiment_id, metrics, promote=promote)


def _resolve_zone(tz_name: str) -> Any:
    """Resolve a timezone or raise an actionable error.

    A silent fallback to UTC would shift the daily-cap boundary by the local offset and
    could wrongly allow or block a submission near midnight, so an unresolved zone is a
    hard error that tells the operator to install ``tzdata``.
    """
    if ZoneInfo is None:
        raise ControllerError(
            "zoneinfo is unavailable; cannot evaluate the daily submission cap in "
            f"{tz_name}. Use Python 3.9+ and install tzdata."
        )
    try:
        return ZoneInfo(tz_name)
    except Exception as exc:  # ZoneInfoNotFoundError on systems without a tz database
        raise ControllerError(
            f"Could not resolve timezone {tz_name!r} for the daily submission cap: {exc}. "
            "Install the tzdata package (see requirements-controller.txt)."
        ) from exc


def _local_date(value: str, zone: Any) -> str:
    """Return the YYYY-MM-DD calendar date of a timestamp in the given resolved zone."""
    text = str(value).strip().replace("Z", "+00:00")
    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
    if parsed is None:
        # Last resort: assume a leading ISO date is present.
        return text[:10]
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(zone).date().isoformat()


def fetch_remote_submissions(root: Path, competition: str) -> list[dict[str, str]]:
    """Query Kaggle for this competition's submission history.

    Returns a list of ``{"date_utc", "status", "description"}`` rows. Raises if the
    query fails: the policy requires confirming remote history *before* submitting,
    so a failed query must block rather than silently allow a blind submission.
    """
    command_env = os.environ.copy()
    # Kaggle descriptions may contain Unicode (for example, an arrow in a metric
    # comparison). On Windows the child CLI otherwise inherits a legacy console
    # codec and can fail before emitting CSV at all.
    command_env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [*kaggle_command(), "competitions", "submissions", competition, "--csv"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=command_env,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ControllerError(
            f"Could not query remote submission history for {competition}; refusing to submit blind. "
            f"STDERR: {result.stderr.strip()}"
        )
    rows: list[dict[str, str]] = []
    reader = csv.DictReader(io.StringIO(result.stdout))
    for row in reader:
        normalized = {(key or "").strip().lower(): (value or "").strip() for key, value in row.items()}
        rows.append(
            {
                "date_utc": normalized.get("date", ""),
                "status": normalized.get("status", ""),
                "description": normalized.get("description", ""),
            }
        )
    return rows


def gate_submission(
    root: Path,
    *,
    competition: str,
    candidate_sha256: str,
    experiment_id: str | None = None,
    user_override: bool = False,
) -> dict[str, Any]:
    """Enforce the daily leaderboard-submission cap and duplicate-probe guard in code.

    Mirrors ``reserve_budget`` for GPU hours: reads the local ``SUBMISSION_BUDGET.json``
    and the live remote history, then blocks if the day's count has reached the cap or
    the candidate bytes duplicate an already-recorded submission. Returns a verdict dict
    on success; raises ``ControllerError`` when a submission must not proceed.
    """
    budget_path = root / "SUBMISSION_BUDGET.json"
    budget = read_json(budget_path)
    cap = int(budget.get("max_submissions_per_day", 3))
    tz_name = str(budget.get("timezone", "America/New_York"))
    zone = _resolve_zone(tz_name)
    local_submissions = budget.get("submissions", []) or []

    duplicate = [
        item
        for item in local_submissions
        if str(item.get("submission_sha256", "")).lower() == str(candidate_sha256).lower()
    ]
    if duplicate and not user_override:
        prior = duplicate[0]
        raise ControllerError(
            "Duplicate submission SHA256 already recorded for "
            f"{prior.get('experiment_id', '?')} (submission {prior.get('submission_id', '?')}); "
            "refusing a duplicate probe. Pass user_override=True only with explicit justification."
        )

    remote = fetch_remote_submissions(root, competition)
    today = _local_date(utc_now(), zone)
    remote_today = [
        row
        for row in remote
        if _local_date(row["date_utc"], zone) == today and row["status"].upper() != "ERROR"
    ]
    local_today = [item for item in local_submissions if item.get("local_date") == today]
    used = max(len(remote_today), len(local_today))

    verdict = {
        "date": today,
        "timezone": tz_name,
        "cap": cap,
        "remote_today": len(remote_today),
        "local_today": len(local_today),
        "used": used,
        "remaining": cap - used,
        "duplicate": bool(duplicate),
        "experiment_id": experiment_id,
        "checked_at": utc_now(),
    }
    if used >= cap and not user_override:
        raise ControllerError(
            f"Daily submission cap reached: {used}/{cap} counted for {today} ({tz_name}). "
            "Wait for the next local day or pass user_override=True with explicit approval."
        )
    return verdict
