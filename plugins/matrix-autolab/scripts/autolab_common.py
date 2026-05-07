from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.1.0"
AUTOLAB_DIR = ".autolab"
RUN_STATUS = {"in_progress", "blocked", "failed", "completed", "aborted"}
SKILL_STATUS = {"pending", "in_progress", "blocked", "failed", "completed", "skipped"}
RUN_KINDS = {
    "paper_reproduction",
    "figure_generation",
    "method_implementation",
    "ablation",
    "baseline_comparison",
    "inspection",
}
RUN_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{6}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{secrets.token_hex(3)}"


def validate_run_id(run_id: str) -> str:
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError(f"Invalid run id: {run_id}")
    return run_id


def project_root() -> Path:
    return Path.cwd()


def autolab_root(root: Path | None = None) -> Path:
    return (root or project_root()) / AUTOLAB_DIR


def run_root(run_id: str, root: Path | None = None) -> Path:
    return autolab_root(root) / "runs" / validate_run_id(run_id)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            encoding="utf-8",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def parse_json_object(value: str, option: str) -> dict[str, Any]:
    """Parse a JSON object from a CLI value. A leading '@' reads from a file path."""
    if not value:
        raise ValueError(f"{option}: value required")
    if value.startswith("@"):
        file_path = Path(value[1:])
        if not file_path.exists():
            raise ValueError(f"{option}: file not found: {file_path}")
        text = file_path.read_text(encoding="utf-8")
    else:
        text = value
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{option}: invalid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{option}: expected a JSON object")
    return parsed


def git_value(args: list[str], root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def git_metadata(root: Path | None = None) -> dict[str, Any]:
    base = root or project_root()
    branch = git_value(["branch", "--show-current"], base)
    commit = git_value(["rev-parse", "HEAD"], base)
    status = git_value(["status", "--short"], base)
    return {"commit": commit, "branch": branch, "dirty": bool(status)}


def default_project(name: str, paper_source: str) -> dict[str, Any]:
    now = utc_now()
    project_id = secrets.token_hex(8)
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "name": name,
        "paper_source": paper_source,
        "task_type": "unknown",
        "dataset": {"name": "", "path": ""},
        "created_at": now,
        "updated_at": now,
    }


def default_workflow_status(project_id: str, active_run_id: str = "") -> dict[str, Any]:
    def skill() -> dict[str, Any]:
        return {
            "status": "pending",
            "user_confirmed": False,
            "current_phase": "",
            "report": "",
            "updated_at": "",
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "active_run_id": active_run_id,
        "skills": {
            "matrix-autolab": skill(),
            "paperbanana": skill(),
            "autolab": skill(),
            "autobaseline": skill(),
        },
    }


def ensure_project(root: Path, name: str = "AutoLab Project", paper_source: str = "main.tex") -> dict[str, Any]:
    base = autolab_root(root)
    project_path = base / "project.json"
    project = read_json(project_path, None)
    if project is None:
        project = default_project(name=name, paper_source=paper_source)
        write_json(project_path, project)
    else:
        project["updated_at"] = utc_now()
        write_json(project_path, project)

    status_path = base / "workflow_status.json"
    status = read_json(status_path, None)
    if status is None:
        write_json(status_path, default_workflow_status(project["project_id"]))
    return project
