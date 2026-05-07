# Matrix-AutoLab Local Recording Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the local `.autolab/` recording layer for Matrix-AutoLab with project/run metadata, append-only events/metrics/errors, artifact/report indexes, changed-file capture, and a `matrix-autolab` skill update.

**Architecture:** Add focused Python CLI utilities under `plugins/matrix-autolab/scripts/` backed by a small shared library. The scripts write portable JSON/JSONL files under `.autolab/` and do not change the existing phase-gated execution flow or move legacy outputs.

**Tech Stack:** Python 3 standard library, `unittest`, JSON/JSONL files, Git CLI for repository state.

---

## File Structure

- Create `plugins/matrix-autolab/scripts/autolab_common.py`
  Shared path helpers, timestamp generation, JSON read/write, JSONL append, run id generation, git metadata helpers, and status constants.
- Create `plugins/matrix-autolab/scripts/autolab_run.py`
  CLI for `init-project`, `start-run`, `finish-run`, and `status`.
- Create `plugins/matrix-autolab/scripts/autolab_event.py`
  CLI for appending event, metric, and error records.
- Create `plugins/matrix-autolab/scripts/autolab_collect.py`
  CLI for recording artifacts, recording reports, and collecting changed files.
- Modify `plugins/matrix-autolab/skills/matrix-autolab/SKILL.md`
  Document `.autolab/` detection and recording initialization behavior.
- Create `tests/test_autolab_recording.py`
  End-to-end tests for the CLI scripts using temporary project directories.

## Task 1: Shared Recording Library

**Files:**
- Create: `plugins/matrix-autolab/scripts/autolab_common.py`
- Test: `tests/test_autolab_recording.py`

- [ ] **Step 1: Write failing tests for shared behavior**

Add this initial test file:

```python
import json
import pathlib
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "plugins" / "matrix-autolab" / "scripts"


def run_script(project_dir, script_name, *args):
    script = SCRIPTS_DIR / script_name
    result = subprocess.run(
        ["python3", str(script), *args],
        cwd=project_dir,
        text=True,
        capture_output=True,
    )
    return result


class AutolabRecordingTests(unittest.TestCase):
    def test_init_project_creates_project_and_status_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            result = run_script(project, "autolab_run.py", "init-project", "--name", "Demo")
            self.assertEqual(result.returncode, 0, result.stderr)

            project_json = json.loads((project / ".autolab" / "project.json").read_text())
            self.assertEqual(project_json["schema_version"], "0.1.0")
            self.assertEqual(project_json["name"], "Demo")
            self.assertEqual(project_json["paper_source"], "main.tex")

            status_json = json.loads((project / ".autolab" / "workflow_status.json").read_text())
            self.assertEqual(status_json["schema_version"], "0.1.0")
            self.assertIn("paperbanana", status_json["skills"])
            self.assertIn("autolab", status_json["skills"])
            self.assertIn("autobaseline", status_json["skills"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python3 -m unittest tests/test_autolab_recording.py
```

Expected: FAIL because `plugins/matrix-autolab/scripts/autolab_run.py` does not exist.

- [ ] **Step 3: Implement shared helpers**

Create `plugins/matrix-autolab/scripts/autolab_common.py`:

```python
from __future__ import annotations

import json
import os
import secrets
import subprocess
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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{secrets.token_hex(3)}"


def project_root() -> Path:
    return Path.cwd()


def autolab_root(root: Path | None = None) -> Path:
    return (root or project_root()) / AUTOLAB_DIR


def run_root(run_id: str, root: Path | None = None) -> Path:
    return autolab_root(root) / "runs" / run_id


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def git_value(args: list[str], root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
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
```

- [ ] **Step 4: Run the test and verify it still fails for missing CLI**

Run:

```bash
python3 -m unittest tests/test_autolab_recording.py
```

Expected: FAIL because `autolab_run.py` is still missing.

## Task 2: Run Management CLI

**Files:**
- Create: `plugins/matrix-autolab/scripts/autolab_run.py`
- Modify: `tests/test_autolab_recording.py`

- [ ] **Step 1: Extend tests for run lifecycle**

Add this method inside `AutolabRecordingTests`:

```python
    def test_start_and_finish_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            start = run_script(
                project,
                "autolab_run.py",
                "start-run",
                "--kind",
                "ablation",
                "--entry-skill",
                "autolab",
            )
            self.assertEqual(start.returncode, 0, start.stderr)
            payload = json.loads(start.stdout)
            run_id = payload["run_id"]

            run_dir = project / ".autolab" / "runs" / run_id
            run_json = json.loads((run_dir / "run.json").read_text())
            self.assertEqual(run_json["kind"], "ablation")
            self.assertEqual(run_json["status"], "in_progress")
            self.assertEqual(run_json["entry_skill"], "autolab")

            status_json = json.loads((project / ".autolab" / "workflow_status.json").read_text())
            self.assertEqual(status_json["active_run_id"], run_id)

            finish = run_script(
                project,
                "autolab_run.py",
                "finish-run",
                "--run-id",
                run_id,
                "--status",
                "completed",
                "--summary",
                "Smoke run complete",
            )
            self.assertEqual(finish.returncode, 0, finish.stderr)
            updated = json.loads((run_dir / "run.json").read_text())
            self.assertEqual(updated["status"], "completed")
            self.assertEqual(updated["summary"], "Smoke run complete")
            self.assertTrue(updated["ended_at"])
```

- [ ] **Step 2: Run tests and verify failures**

Run:

```bash
python3 -m unittest tests/test_autolab_recording.py
```

Expected: FAIL because `autolab_run.py` does not exist.

- [ ] **Step 3: Implement `autolab_run.py`**

Create `plugins/matrix-autolab/scripts/autolab_run.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from autolab_common import (
    RUN_KINDS,
    RUN_STATUS,
    SCHEMA_VERSION,
    append_jsonl,
    autolab_root,
    default_workflow_status,
    ensure_project,
    git_metadata,
    new_run_id,
    read_json,
    run_root,
    utc_now,
    write_json,
)


def cmd_init_project(args: argparse.Namespace) -> int:
    project = ensure_project(Path.cwd(), name=args.name, paper_source=args.paper_source)
    print(json.dumps({"project_id": project["project_id"], "autolab_dir": ".autolab"}))
    return 0


def cmd_start_run(args: argparse.Namespace) -> int:
    if args.kind not in RUN_KINDS:
        print(f"Invalid run kind: {args.kind}", file=sys.stderr)
        return 2

    root = Path.cwd()
    project = ensure_project(root, name=args.name, paper_source=args.paper_source)
    run_id = args.run_id or new_run_id()
    now = utc_now()
    directory = run_root(run_id, root)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "reports").mkdir(exist_ok=True)

    run_data = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "project_id": project["project_id"],
        "kind": args.kind,
        "status": "in_progress",
        "started_at": now,
        "ended_at": "",
        "entry_skill": args.entry_skill,
        "paper_source": args.paper_source,
        "git": git_metadata(root),
        "summary": "",
    }
    write_json(directory / "run.json", run_data)
    write_json(directory / "config.json", {"schema_version": SCHEMA_VERSION, "captured_at": now})
    write_json(directory / "artifacts.json", {"artifacts": []})
    write_json(directory / "changed_files.json", {"captured_at": "", "git": git_metadata(root), "files": []})
    write_json(directory / "reports" / "reports_index.json", {"reports": []})

    status_path = autolab_root(root) / "workflow_status.json"
    status = read_json(status_path, default_workflow_status(project["project_id"]))
    status["active_run_id"] = run_id
    write_json(status_path, status)

    append_jsonl(
        directory / "events.jsonl",
        {
            "timestamp": now,
            "level": "info",
            "skill": args.entry_skill,
            "phase": "",
            "event_type": "run_created",
            "message": f"Run {run_id} created",
            "data": {"kind": args.kind},
        },
    )
    print(json.dumps({"run_id": run_id}))
    return 0


def cmd_finish_run(args: argparse.Namespace) -> int:
    if args.status not in RUN_STATUS:
        print(f"Invalid run status: {args.status}", file=sys.stderr)
        return 2
    path = run_root(args.run_id) / "run.json"
    run_data = read_json(path, None)
    if run_data is None:
        print(f"Run not found: {args.run_id}", file=sys.stderr)
        return 1
    run_data["status"] = args.status
    run_data["ended_at"] = utc_now()
    run_data["summary"] = args.summary
    write_json(path, run_data)
    append_jsonl(
        run_root(args.run_id) / "events.jsonl",
        {
            "timestamp": utc_now(),
            "level": "info",
            "skill": run_data.get("entry_skill", ""),
            "phase": "",
            "event_type": "run_status_changed",
            "message": f"Run status changed to {args.status}",
            "data": {"status": args.status},
        },
    )
    print(json.dumps({"run_id": args.run_id, "status": args.status}))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    status = read_json(autolab_root() / "workflow_status.json", None)
    if status is None:
        print(json.dumps({"initialized": False}))
    else:
        print(json.dumps({"initialized": True, "status": status}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Matrix-AutoLab run recording utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-project")
    init.add_argument("--name", default="AutoLab Project")
    init.add_argument("--paper-source", default="main.tex")
    init.set_defaults(func=cmd_init_project)

    start = sub.add_parser("start-run")
    start.add_argument("--kind", required=True)
    start.add_argument("--entry-skill", required=True)
    start.add_argument("--name", default="AutoLab Project")
    start.add_argument("--paper-source", default="main.tex")
    start.add_argument("--run-id", default="")
    start.set_defaults(func=cmd_start_run)

    finish = sub.add_parser("finish-run")
    finish.add_argument("--run-id", required=True)
    finish.add_argument("--status", required=True)
    finish.add_argument("--summary", default="")
    finish.set_defaults(func=cmd_finish_run)

    status = sub.add_parser("status")
    status.set_defaults(func=cmd_status)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests and verify they pass for run management**

Run:

```bash
python3 -m unittest tests/test_autolab_recording.py
```

Expected: PASS for current tests.

## Task 3: Event, Metric, and Error CLI

**Files:**
- Create: `plugins/matrix-autolab/scripts/autolab_event.py`
- Modify: `tests/test_autolab_recording.py`

- [ ] **Step 1: Add tests for JSONL append behavior**

Add this method inside `AutolabRecordingTests`:

```python
    def test_event_metric_and_error_append_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            start = run_script(project, "autolab_run.py", "start-run", "--kind", "ablation", "--entry-skill", "autolab")
            self.assertEqual(start.returncode, 0, start.stderr)
            run_id = json.loads(start.stdout)["run_id"]

            event = run_script(
                project,
                "autolab_event.py",
                "event",
                "--run-id",
                run_id,
                "--type",
                "phase_started",
                "--skill",
                "autolab",
                "--phase",
                "phase_4_modules",
                "--message",
                "Phase 4 started",
            )
            self.assertEqual(event.returncode, 0, event.stderr)

            metric = run_script(
                project,
                "autolab_event.py",
                "metric",
                "--run-id",
                run_id,
                "--name",
                "mIoU",
                "--value",
                "0.734",
                "--split",
                "val",
                "--epoch",
                "3",
            )
            self.assertEqual(metric.returncode, 0, metric.stderr)

            error = run_script(
                project,
                "autolab_event.py",
                "error",
                "--run-id",
                run_id,
                "--category",
                "oom",
                "--message",
                "CUDA out of memory",
            )
            self.assertEqual(error.returncode, 0, error.stderr)

            run_dir = project / ".autolab" / "runs" / run_id
            events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
            metrics = [json.loads(line) for line in (run_dir / "metrics.jsonl").read_text().splitlines()]
            errors = [json.loads(line) for line in (run_dir / "errors.jsonl").read_text().splitlines()]

            self.assertEqual(events[-1]["event_type"], "phase_started")
            self.assertEqual(metrics[0]["name"], "mIoU")
            self.assertEqual(metrics[0]["value"], 0.734)
            self.assertEqual(errors[0]["category"], "oom")
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_autolab_recording.py
```

Expected: FAIL because `autolab_event.py` does not exist.

- [ ] **Step 3: Implement `autolab_event.py`**

Create `plugins/matrix-autolab/scripts/autolab_event.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from autolab_common import append_jsonl, run_root, utc_now


def require_run(run_id: str) -> Path:
    directory = run_root(run_id)
    if not (directory / "run.json").exists():
        raise SystemExit(f"Run not found: {run_id}")
    return directory


def cmd_event(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    record = {
        "timestamp": utc_now(),
        "level": args.level,
        "skill": args.skill,
        "phase": args.phase,
        "event_type": args.type,
        "message": args.message,
        "data": json.loads(args.data) if args.data else {},
    }
    append_jsonl(directory / "events.jsonl", record)
    print(json.dumps({"recorded": "event"}))
    return 0


def cmd_metric(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    record = {
        "timestamp": utc_now(),
        "source": args.source,
        "phase": args.phase,
        "step": args.step,
        "epoch": args.epoch,
        "split": args.split,
        "name": args.name,
        "value": float(args.value),
        "unit": args.unit,
        "context": json.loads(args.context) if args.context else {"class_name": "", "run_config": "default"},
    }
    append_jsonl(directory / "metrics.jsonl", record)
    append_jsonl(
        directory / "events.jsonl",
        {
            "timestamp": utc_now(),
            "level": "info",
            "skill": "",
            "phase": args.phase,
            "event_type": "metric_recorded",
            "message": f"Metric recorded: {args.name}",
            "data": {"name": args.name, "value": float(args.value)},
        },
    )
    print(json.dumps({"recorded": "metric"}))
    return 0


def cmd_error(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    record = {
        "timestamp": utc_now(),
        "skill": args.skill,
        "phase": args.phase,
        "severity": args.severity,
        "category": args.category,
        "message": args.message,
        "command": args.command_text,
        "log_excerpt": args.log_excerpt,
        "suggested_next_step": args.suggested_next_step,
    }
    append_jsonl(directory / "errors.jsonl", record)
    append_jsonl(
        directory / "events.jsonl",
        {
            "timestamp": utc_now(),
            "level": "error",
            "skill": args.skill,
            "phase": args.phase,
            "event_type": "phase_failed",
            "message": args.message,
            "data": {"category": args.category},
        },
    )
    print(json.dumps({"recorded": "error"}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append Matrix-AutoLab events, metrics, and errors")
    sub = parser.add_subparsers(dest="command", required=True)

    event = sub.add_parser("event")
    event.add_argument("--run-id", required=True)
    event.add_argument("--type", required=True)
    event.add_argument("--skill", default="")
    event.add_argument("--phase", default="")
    event.add_argument("--message", required=True)
    event.add_argument("--level", default="info")
    event.add_argument("--data", default="")
    event.set_defaults(func=cmd_event)

    metric = sub.add_parser("metric")
    metric.add_argument("--run-id", required=True)
    metric.add_argument("--name", required=True)
    metric.add_argument("--value", required=True)
    metric.add_argument("--source", default="")
    metric.add_argument("--phase", default="")
    metric.add_argument("--step", type=int, default=0)
    metric.add_argument("--epoch", type=int, default=0)
    metric.add_argument("--split", default="")
    metric.add_argument("--unit", default="")
    metric.add_argument("--context", default="")
    metric.set_defaults(func=cmd_metric)

    error = sub.add_parser("error")
    error.add_argument("--run-id", required=True)
    error.add_argument("--category", required=True)
    error.add_argument("--message", required=True)
    error.add_argument("--skill", default="")
    error.add_argument("--phase", default="")
    error.add_argument("--severity", default="error")
    error.add_argument("--command-text", default="")
    error.add_argument("--log-excerpt", default="")
    error.add_argument("--suggested-next-step", default="")
    error.set_defaults(func=cmd_error)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
python3 -m unittest tests/test_autolab_recording.py
```

Expected: PASS for current tests.

## Task 4: Artifact, Report, and Changed Files Collection

**Files:**
- Create: `plugins/matrix-autolab/scripts/autolab_collect.py`
- Modify: `tests/test_autolab_recording.py`

- [ ] **Step 1: Add tests for artifact/report indexes and changed files**

Add this method inside `AutolabRecordingTests`:

```python
    def test_collect_artifact_report_and_changed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True, text=True)
            tracked = project / "model.py"
            tracked.write_text("print('v1')\n")
            subprocess.run(["git", "add", "model.py"], cwd=project, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "commit", "-m", "init"],
                cwd=project,
                check=False,
                capture_output=True,
                text=True,
            )
            tracked.write_text("print('v2')\n")

            start = run_script(project, "autolab_run.py", "start-run", "--kind", "ablation", "--entry-skill", "autolab")
            self.assertEqual(start.returncode, 0, start.stderr)
            run_id = json.loads(start.stdout)["run_id"]

            artifact_file = project / "outputs" / "best.pth"
            artifact_file.parent.mkdir()
            artifact_file.write_bytes(b"checkpoint")
            artifact = run_script(
                project,
                "autolab_collect.py",
                "artifact",
                "--run-id",
                run_id,
                "--type",
                "checkpoint",
                "--path",
                "outputs/best.pth",
                "--id",
                "best_checkpoint",
                "--description",
                "Best checkpoint",
            )
            self.assertEqual(artifact.returncode, 0, artifact.stderr)

            report_file = project / "experiment_docs" / "reports" / "phase.md"
            report_file.parent.mkdir(parents=True)
            report_file.write_text("# Phase\n")
            report = run_script(
                project,
                "autolab_collect.py",
                "report",
                "--run-id",
                run_id,
                "--type",
                "phase_report",
                "--phase",
                "phase_3_baseline_audit",
                "--path",
                "experiment_docs/reports/phase.md",
                "--title",
                "Baseline Audit",
            )
            self.assertEqual(report.returncode, 0, report.stderr)

            changed = run_script(project, "autolab_collect.py", "changed-files", "--run-id", run_id)
            self.assertEqual(changed.returncode, 0, changed.stderr)

            run_dir = project / ".autolab" / "runs" / run_id
            artifacts = json.loads((run_dir / "artifacts.json").read_text())["artifacts"]
            reports = json.loads((run_dir / "reports" / "reports_index.json").read_text())["reports"]
            files = json.loads((run_dir / "changed_files.json").read_text())["files"]
            self.assertEqual(artifacts[0]["id"], "best_checkpoint")
            self.assertEqual(artifacts[0]["size_bytes"], len(b"checkpoint"))
            self.assertEqual(reports[0]["title"], "Baseline Audit")
            self.assertTrue(any(item["path"] == "model.py" for item in files))
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_autolab_recording.py
```

Expected: FAIL because `autolab_collect.py` does not exist.

- [ ] **Step 3: Implement `autolab_collect.py`**

Create `plugins/matrix-autolab/scripts/autolab_collect.py`:

```python
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from autolab_common import append_jsonl, git_metadata, read_json, run_root, utc_now, write_json


def require_run(run_id: str) -> Path:
    directory = run_root(run_id)
    if not (directory / "run.json").exists():
        raise SystemExit(f"Run not found: {run_id}")
    return directory


def file_sha256(path: Path, limit_bytes: int = 100 * 1024 * 1024) -> str:
    if not path.exists() or not path.is_file() or path.stat().st_size > limit_bytes:
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cmd_artifact(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    target = Path.cwd() / args.path
    payload_path = directory / "artifacts.json"
    payload = read_json(payload_path, {"artifacts": []})
    item = {
        "id": args.id,
        "type": args.type,
        "path": args.path,
        "exists": target.exists(),
        "size_bytes": target.stat().st_size if target.exists() and target.is_file() else 0,
        "sha256": file_sha256(target),
        "phase": args.phase,
        "description": args.description,
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
            "phase": args.phase,
            "event_type": "artifact_recorded",
            "message": f"Artifact recorded: {args.id}",
            "data": item,
        },
    )
    print(json.dumps({"recorded": "artifact", "id": args.id}))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    payload_path = directory / "reports" / "reports_index.json"
    payload = read_json(payload_path, {"reports": []})
    item = {
        "type": args.type,
        "phase": args.phase,
        "path": args.path,
        "title": args.title,
        "created_at": utc_now(),
    }
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
    result = subprocess.run(["git", "status", "--short"], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return []
    files = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        status = line[:2].strip() or "modified"
        path = line[3:] if len(line) > 3 else line.strip()
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
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
python3 -m unittest tests/test_autolab_recording.py
```

Expected: PASS for current tests.

## Task 5: Matrix-AutoLab Skill Update

**Files:**
- Modify: `plugins/matrix-autolab/skills/matrix-autolab/SKILL.md`

- [ ] **Step 1: Add local recording instructions**

Modify the `Startup Procedure` section to include:

```markdown
3. Check local recording state:
   - If `.autolab/project.json` and `.autolab/workflow_status.json` exist, summarize the active run and latest known skill statuses.
   - If `.autolab/` does not exist, tell the user local recording is not initialized and recommend:
     `python3 plugins/matrix-autolab/scripts/autolab_run.py init-project`
   - If legacy files exist but `.autolab/` does not, explain that the project is readable in compatibility mode.
```

- [ ] **Step 2: Add script usage guidance**

Add a new section:

```markdown
## Local Recording Utilities

For new Matrix-AutoLab runs, recommend initializing local recording before phase work:

```bash
python3 plugins/matrix-autolab/scripts/autolab_run.py init-project
python3 plugins/matrix-autolab/scripts/autolab_run.py start-run --kind paper_reproduction --entry-skill matrix-autolab
```

During later phases, the specialized skills or the user may record important facts:

```bash
python3 plugins/matrix-autolab/scripts/autolab_event.py event --run-id <run_id> --type phase_started --skill autolab --phase phase_4_modules --message "Phase 4 started"
python3 plugins/matrix-autolab/scripts/autolab_event.py metric --run-id <run_id> --name mIoU --value 0.734 --split val --epoch 3
python3 plugins/matrix-autolab/scripts/autolab_collect.py changed-files --run-id <run_id>
```

These utilities are optional in this phase. Do not block legacy workflow execution when `.autolab/` is absent.
```

- [ ] **Step 3: Check Markdown for accidental nested fence breakage**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
text = Path("plugins/matrix-autolab/skills/matrix-autolab/SKILL.md").read_text()
assert text.count("```") % 2 == 0
print("markdown fences balanced")
PY
```

Expected: `markdown fences balanced`

## Task 6: Final Verification

**Files:**
- Verify all files above.

- [ ] **Step 1: Run unit tests**

Run:

```bash
python3 -m unittest tests/test_autolab_recording.py
```

Expected: all tests pass.

- [ ] **Step 2: Validate plugin JSON files**

Run:

```bash
python3 -m json.tool plugins/matrix-autolab/.codex-plugin/plugin.json
python3 -m json.tool plugins/matrix-autolab/.app.json
python3 -m json.tool .agents/plugins/marketplace.json
```

Expected: each command exits `0` and prints formatted JSON.

- [ ] **Step 3: Verify no old versioned skill references**

Run:

```bash
rg -n 'paperbanana-0\\.1\\.0|autolab-0\\.1\\.0|autobaseline-0\\.1\\.0' plugins/matrix-autolab tests docs/superpowers/specs docs/superpowers/plans
```

Expected: no matches.

- [ ] **Step 4: Inspect git status**

Run:

```bash
git status --short
```

Expected: only intended new or modified files are listed.

## Spec Coverage Review

- `.autolab/` layout: Tasks 1-4 create all specified files.
- Project and workflow metadata: Tasks 1-2.
- Run metadata and config snapshot: Task 2.
- Events, metrics, errors: Task 3.
- Artifacts, reports, changed files: Task 4.
- Matrix-AutoLab skill compatibility behavior: Task 5.
- Hooks/server/web excluded: No task implements them, matching non-goals.
- Testing strategy: Tasks 1-4 use `unittest`; Task 6 validates JSON and placeholder cleanup.
