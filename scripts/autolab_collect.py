from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from autolab_common import append_jsonl, git_metadata, read_json, run_root, utc_now, write_json


MAX_HASH_BYTES = 100 * 1024 * 1024


def require_run(run_id: str) -> Path:
    directory = run_root(run_id)
    if not (directory / "run.json").exists():
        raise FileNotFoundError(f"Run not found: {run_id}")
    return directory


def validated_project_path(raw_path: str, path_kind: str) -> Path:
    relative_path = Path(raw_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Invalid {path_kind} path: {raw_path}")

    root = Path.cwd().resolve()
    try:
        target = (root / relative_path).resolve(strict=False)
        target.relative_to(root)
    except (OSError, ValueError) as exc:
        raise ValueError(f"Invalid {path_kind} path: {raw_path}") from exc
    return target


def file_sha256(path: Path, limit_bytes: int = MAX_HASH_BYTES) -> str:
    if not path.exists() or not path.is_file():
        return ""
    if path.stat().st_size > limit_bytes:
        return ""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_size(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    return path.stat().st_size


def cmd_artifact(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    target = validated_project_path(args.path, "artifact")
    payload_path = directory / "artifacts.json"
    payload = read_json(payload_path, {"artifacts": []})
    existing = next((entry for entry in payload.get("artifacts", []) if entry.get("id") == args.id), {})
    phase = args.phase or existing.get("phase", "")
    description = args.description or existing.get("description", "")
    item = {
        "id": args.id,
        "type": args.type,
        "path": args.path,
        "exists": target.exists(),
        "size_bytes": file_size(target),
        "sha256": file_sha256(target),
        "phase": phase,
        "description": description,
    }
    payload["artifacts"] = [entry for entry in payload.get("artifacts", []) if entry.get("id") != args.id]
    payload["artifacts"].append(item)
    write_json(payload_path, payload)

    append_jsonl(
        directory / "events.jsonl",
        {
            "timestamp": utc_now(),
            "level": "info",
            "skill": "",
            "phase": phase,
            "event_type": "artifact_recorded",
            "message": f"Artifact recorded: {args.id}",
            "data": item,
        },
    )
    print(json.dumps({"recorded": "artifact", "id": args.id}))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    validated_project_path(args.path, "report")
    payload_path = directory / "reports" / "reports_index.json"
    payload = read_json(payload_path, {"reports": []})
    now = utc_now()
    key = (args.type, args.phase, args.path)
    existing = next(
        (
            entry
            for entry in payload.get("reports", [])
            if (entry.get("type"), entry.get("phase"), entry.get("path")) == key
        ),
        {},
    )
    item = {
        "type": args.type,
        "phase": args.phase,
        "path": args.path,
        "title": args.title,
        "created_at": existing.get("created_at", now),
        "updated_at": now,
    }
    payload["reports"] = [
        entry for entry in payload.get("reports", []) if (entry.get("type"), entry.get("phase"), entry.get("path")) != key
    ]
    payload["reports"].append(item)
    write_json(payload_path, payload)

    append_jsonl(
        directory / "events.jsonl",
        {
            "timestamp": utc_now(),
            "level": "info",
            "skill": "",
            "phase": args.phase,
            "event_type": "report_recorded",
            "message": f"Report recorded: {args.path}",
            "data": item,
        },
    )
    print(json.dumps({"recorded": "report"}))
    return 0


def git_status_files() -> list[dict[str, str]]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z"],
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            capture_output=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []

    if result.returncode != 0:
        return []

    files = []
    entries = result.stdout.split(b"\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        status_xy = entry[:2].decode("utf-8", errors="surrogateescape")
        path = entry[3:].decode("utf-8", errors="surrogateescape") if len(entry) > 3 else ""
        status = status_xy.strip() or "modified"
        if "R" in status_xy or "C" in status_xy:
            old_path = ""
            if index < len(entries):
                old_path = entries[index].decode("utf-8", errors="surrogateescape")
                index += 1
            files.append({"path": path, "old_path": old_path, "status": status.strip()[0], "summary": ""})
        else:
            files.append({"path": path, "status": status, "summary": ""})
    return files


def cmd_changed_files(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    payload = {"captured_at": utc_now(), "git": git_metadata(Path.cwd()), "files": git_status_files()}
    write_json(directory / "changed_files.json", payload)
    print(json.dumps({"recorded": "changed_files", "count": len(payload["files"])}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect Matrix-AutoLab artifacts, reports, and changed files")
    sub = parser.add_subparsers(dest="command", required=True)

    artifact = sub.add_parser("artifact")
    artifact.add_argument("--run-id", required=True)
    artifact.add_argument("--type", required=True)
    artifact.add_argument("--path", required=True)
    artifact.add_argument("--id", required=True)
    artifact.add_argument("--phase", default="")
    artifact.add_argument("--description", default="")
    artifact.set_defaults(func=cmd_artifact)

    report = sub.add_parser("report")
    report.add_argument("--run-id", required=True)
    report.add_argument("--type", required=True)
    report.add_argument("--phase", default="")
    report.add_argument("--path", required=True)
    report.add_argument("--title", default="")
    report.set_defaults(func=cmd_report)

    changed = sub.add_parser("changed-files")
    changed.add_argument("--run-id", required=True)
    changed.set_defaults(func=cmd_changed_files)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
