from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from _bootstrap import PROJECT_ROOT


def command_info(name: str) -> dict:
    path = shutil.which(name)
    return {"available": path is not None, "path": path}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check deterministic controller prerequisites without exposing secrets")
    parser.add_argument("--verify-kaggle-auth", action="store_true")
    args = parser.parse_args()

    kaggle_config_dir = Path(os.environ.setdefault("KAGGLE_CONFIG_DIR", str(PROJECT_ROOT / ".kaggle")))
    kaggle_config_dir.mkdir(parents=True, exist_ok=True)
    kaggle = command_info("kaggle")
    claude = command_info("claude")
    credential_files = sorted(path.name for path in kaggle_config_dir.iterdir() if path.is_file())
    oauth_credentials = Path.home() / ".kaggle" / "credentials.json"
    report = {
        "python": {"available": True, "executable": sys.executable, "version": sys.version.split()[0]},
        "packages": {
            "yaml": importlib.util.find_spec("yaml") is not None,
            "pytest": importlib.util.find_spec("pytest") is not None,
            "kaggle": importlib.util.find_spec("kaggle") is not None,
        },
        "commands": {"kaggle": kaggle, "claude": claude},
        "kaggle_identity": {
            "username_env_set": bool(os.environ.get("KAGGLE_USERNAME")),
            "api_token_env_set": bool(os.environ.get("KAGGLE_API_TOKEN")),
            "oauth_credentials_exist": oauth_credentials.exists(),
            "legacy_config_exists": (kaggle_config_dir / "kaggle.json").exists(),
            "credential_file_detected": bool(credential_files),
            "credential_file_names": credential_files,
            "config_dir": str(kaggle_config_dir),
        },
        "project": {"root": str(PROJECT_ROOT)},
        "blockers": [],
    }
    if not report["packages"]["yaml"]:
        report["blockers"].append("PyYAML is missing")
    if not (kaggle["available"] or report["packages"]["kaggle"]):
        report["blockers"].append("Kaggle CLI is missing")
    if not claude["available"]:
        report["blockers"].append("Claude Code CLI is missing")
    if not (
        report["kaggle_identity"]["api_token_env_set"]
        or report["kaggle_identity"]["oauth_credentials_exist"]
        or report["kaggle_identity"]["credential_file_detected"]
    ):
        report["blockers"].append("No Kaggle API credential location was detected")

    if args.verify_kaggle_auth and not report["blockers"]:
        prefix = [kaggle["path"]] if kaggle["available"] else [sys.executable, "-m", "kaggle"]
        result = subprocess.run(
            [*prefix, "kernels", "list", "--mine", "--page-size", "1"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        report["kaggle_auth_check"] = {"ok": result.returncode == 0, "exit_code": result.returncode}
        if result.returncode != 0:
            report["blockers"].append("Kaggle authentication check failed")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
