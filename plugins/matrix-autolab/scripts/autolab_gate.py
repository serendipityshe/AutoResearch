from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from autolab_common import append_jsonl, read_json, run_root, utc_now, validate_run_id, write_json


GATE_SCHEMA_VERSION = "0.1.0"


DEFAULT_PHASES = [
    {"id": "phase_1_paperbanana", "name": "Framework figure", "requires_confirmation": True},
    {"id": "phase_2_setup", "name": "Setup", "requires_confirmation": True},
    {"id": "phase_3_baseline_audit", "name": "Baseline audit", "requires_confirmation": True},
    {"id": "phase_4_modules", "name": "Module implementation", "requires_confirmation": True},
    {"id": "phase_4.5_loss_check", "name": "Loss consistency check", "requires_confirmation": True},
    {"id": "phase_5_integration", "name": "Integration", "requires_confirmation": True},
    {"id": "phase_6_short_train", "name": "Short training", "requires_confirmation": True},
    {"id": "phase_7_full_train", "name": "Full training", "requires_confirmation": True},
    {"id": "phase_8_eval", "name": "Evaluation and ablations", "requires_confirmation": True},
    {"id": "phase_9_final", "name": "Final summary", "requires_confirmation": True},
]


def default_phase_plan() -> dict[str, Any]:
    return {
        "schema_version": GATE_SCHEMA_VERSION,
        "created_at": utc_now(),
        "mode": "strict_sequential",
        "phases": DEFAULT_PHASES,
        "rules": [
            "Only the current gate step may be executed.",
            "Every step must declare artifacts, requirements, checks, or a user confirmation gate.",
            "A step cannot complete until autolab_gate.py check-step returns ok=true.",
        ],
    }


def empty_requirements() -> dict[str, Any]:
    return {"schema_version": GATE_SCHEMA_VERSION, "requirements": []}


def empty_gate_status(run_id: str) -> dict[str, Any]:
    return {
        "schema_version": GATE_SCHEMA_VERSION,
        "run_id": run_id,
        "current_step": None,
        "completed_steps": [],
        "blocked": [],
        "last_check": None,
        "updated_at": utc_now(),
    }


def gate_status_path(run_id: str, root: Path | None = None) -> Path:
    return run_root(run_id, root) / "gate_status.json"


def requirements_path(run_id: str, root: Path | None = None) -> Path:
    return run_root(run_id, root) / "requirements.json"


def phase_plan_path(run_id: str, root: Path | None = None) -> Path:
    return run_root(run_id, root) / "phase_plan.json"


def require_run(run_id: str, root: Path | None = None) -> Path:
    directory = run_root(run_id, root)
    if not (directory / "run.json").exists():
        raise FileNotFoundError(f"Run not found: {run_id}")
    return directory


def valid_project_path(raw_path: str) -> Path:
    relative_path = Path(raw_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Path must be project-relative and stay under the project root: {raw_path}")
    root = Path.cwd().resolve()
    target = (root / relative_path).resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path must stay under the project root: {raw_path}") from exc
    return target


def load_gate(run_id: str) -> dict[str, Any]:
    return read_json(gate_status_path(run_id), empty_gate_status(run_id))


def save_gate(run_id: str, status: dict[str, Any]) -> None:
    status["updated_at"] = utc_now()
    write_json(gate_status_path(run_id), status)


def load_requirements(run_id: str) -> dict[str, Any]:
    return read_json(requirements_path(run_id), empty_requirements())


def save_requirements(run_id: str, data: dict[str, Any]) -> None:
    write_json(requirements_path(run_id), data)


def find_requirement(data: dict[str, Any], requirement_id: str) -> dict[str, Any] | None:
    for item in data.get("requirements", []):
        if item.get("id") == requirement_id:
            return item
    return None


def append_event(directory: Path, event_type: str, message: str, data: dict[str, Any]) -> None:
    append_jsonl(
        directory / "events.jsonl",
        {
            "timestamp": utc_now(),
            "level": "info",
            "skill": "matrix-autolab",
            "phase": data.get("phase", ""),
            "event_type": event_type,
            "message": message,
            "data": data,
        },
    )


def cmd_init_control(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    if args.force or not phase_plan_path(args.run_id).exists():
        write_json(phase_plan_path(args.run_id), default_phase_plan())
    if args.force or not requirements_path(args.run_id).exists():
        write_json(requirements_path(args.run_id), empty_requirements())
    if args.force or not gate_status_path(args.run_id).exists():
        write_json(gate_status_path(args.run_id), empty_gate_status(args.run_id))
    append_event(directory, "gate_initialized", "Gate control files initialized", {"phase": ""})
    print(json.dumps({"run_id": args.run_id, "initialized": True}))
    return 0


def cmd_start_step(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    status = load_gate(args.run_id)
    current = status.get("current_step")
    if current and current.get("status") != "completed" and not args.replace:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "current_step_in_progress",
                    "current_step": current,
                }
            ),
            file=sys.stderr,
        )
        return 4
    step = {
        "phase": args.phase,
        "step": args.step,
        "summary": args.summary,
        "status": "in_progress",
        "started_at": utc_now(),
        "required_artifacts": args.required_artifact,
        "required_requirements": args.requirement,
        "acceptance_checks": args.check,
        "user_confirmation_required": args.user_confirmation_required,
        "user_confirmed": False,
        "report": args.report,
    }
    status["current_step"] = step
    status["blocked"] = []
    status["last_check"] = None
    save_gate(args.run_id, status)
    append_event(directory, "gate_step_started", f"Gate step started: {args.phase}/{args.step}", step)
    print(json.dumps({"run_id": args.run_id, "current_step": step}))
    return 0


def cmd_define_requirement(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    data = load_requirements(args.run_id)
    existing = find_requirement(data, args.id)
    item = existing or {"id": args.id, "evidence": []}
    item.update(
        {
            "id": args.id,
            "phase": args.phase,
            "kind": args.kind,
            "source": args.source,
            "requirement": args.text,
            "implementation_target": args.implementation_target,
            "test_target": args.test_target,
            "status": "pending" if not item.get("evidence") else "evidence_recorded",
            "updated_at": utc_now(),
        }
    )
    if existing is None:
        data["requirements"].append(item)
    save_requirements(args.run_id, data)
    append_event(directory, "requirement_defined", f"Requirement defined: {args.id}", item)
    print(json.dumps({"run_id": args.run_id, "requirement_id": args.id}))
    return 0


def cmd_add_evidence(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    data = load_requirements(args.run_id)
    item = find_requirement(data, args.id)
    if item is None:
        print(f"Requirement not found: {args.id}", file=sys.stderr)
        return 1
    path_exists = None
    if args.path:
        path_exists = valid_project_path(args.path).exists()
    evidence = {
        "type": args.type,
        "path": args.path,
        "path_exists": path_exists,
        "command": args.command_text,
        "notes": args.notes,
        "recorded_at": utc_now(),
    }
    item.setdefault("evidence", []).append(evidence)
    item["status"] = "evidence_recorded"
    item["updated_at"] = utc_now()
    save_requirements(args.run_id, data)
    append_event(directory, "requirement_evidence_added", f"Evidence added: {args.id}", evidence | {"requirement_id": args.id})
    print(json.dumps({"run_id": args.run_id, "requirement_id": args.id, "evidence_count": len(item["evidence"])}))
    return 0


def evaluate_gate(run_id: str) -> dict[str, Any]:
    status = load_gate(run_id)
    current = status.get("current_step")
    blockers: list[dict[str, str]] = []
    if not current:
        return {"ok": False, "blocked": [{"kind": "current_step", "message": "No current step is active"}]}

    artifacts = current.get("required_artifacts") or []
    requirement_ids = current.get("required_requirements") or []
    checks = current.get("acceptance_checks") or []
    if not artifacts and not requirement_ids and not checks and not current.get("user_confirmation_required"):
        blockers.append({"kind": "empty_gate", "message": "Current step declares no artifacts, requirements, checks, or confirmation gate"})

    for artifact in artifacts:
        if not valid_project_path(artifact).exists():
            blockers.append({"kind": "missing_artifact", "message": artifact})

    requirements = load_requirements(run_id)
    for requirement_id in requirement_ids:
        item = find_requirement(requirements, requirement_id)
        if item is None:
            blockers.append({"kind": "missing_requirement", "message": requirement_id})
        elif not item.get("evidence"):
            blockers.append({"kind": "missing_evidence", "message": requirement_id})

    if not checks:
        blockers.append({"kind": "missing_acceptance_checks", "message": "At least one explicit check is required"})

    if current.get("user_confirmation_required") and not current.get("user_confirmed"):
        blockers.append({"kind": "user_confirmation", "message": "Explicit user confirmation is still required"})

    return {"ok": not blockers, "blocked": blockers, "current_step": current}


def cmd_check_step(args: argparse.Namespace) -> int:
    require_run(args.run_id)
    result = evaluate_gate(args.run_id)
    status = load_gate(args.run_id)
    status["blocked"] = result["blocked"]
    status["last_check"] = {"checked_at": utc_now(), "ok": result["ok"]}
    save_gate(args.run_id, status)
    print(json.dumps(result))
    return 0 if result["ok"] else 3


def cmd_confirm_step(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    status = load_gate(args.run_id)
    current = status.get("current_step")
    if not current:
        print("No current step is active", file=sys.stderr)
        return 1
    if args.phase and current.get("phase") != args.phase:
        print(f"Current phase mismatch: {current.get('phase')}", file=sys.stderr)
        return 2
    if args.step and current.get("step") != args.step:
        print(f"Current step mismatch: {current.get('step')}", file=sys.stderr)
        return 2
    current["user_confirmed"] = True
    current["confirmed_at"] = utc_now()
    save_gate(args.run_id, status)
    append_event(directory, "gate_step_confirmed", f"Gate step confirmed: {current.get('phase')}/{current.get('step')}", current)
    print(json.dumps({"run_id": args.run_id, "confirmed": True, "current_step": current}))
    return 0


def cmd_complete_step(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    result = evaluate_gate(args.run_id)
    if not result["ok"]:
        print(json.dumps(result), file=sys.stderr)
        return 3
    status = load_gate(args.run_id)
    current = status["current_step"]
    current["status"] = "completed"
    current["completed_at"] = utc_now()
    status.setdefault("completed_steps", []).append(current)
    status["current_step"] = None
    status["blocked"] = []
    status["last_check"] = {"checked_at": utc_now(), "ok": True}
    save_gate(args.run_id, status)
    append_event(directory, "gate_step_completed", f"Gate step completed: {current.get('phase')}/{current.get('step')}", current)
    print(json.dumps({"run_id": args.run_id, "completed_step": current}))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    require_run(args.run_id)
    print(json.dumps(load_gate(args.run_id)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Matrix-AutoLab anti-skip gate controls")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-control")
    init.add_argument("--run-id", required=True)
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init_control)

    start = sub.add_parser("start-step")
    start.add_argument("--run-id", required=True)
    start.add_argument("--phase", required=True)
    start.add_argument("--step", required=True)
    start.add_argument("--summary", default="")
    start.add_argument("--required-artifact", action="append", default=[])
    start.add_argument("--requirement", action="append", default=[])
    start.add_argument("--check", action="append", default=[])
    start.add_argument("--report", default="")
    start.add_argument("--user-confirmation-required", action="store_true")
    start.add_argument("--replace", action="store_true")
    start.set_defaults(func=cmd_start_step)

    requirement = sub.add_parser("define-requirement")
    requirement.add_argument("--run-id", required=True)
    requirement.add_argument("--id", required=True)
    requirement.add_argument("--phase", default="")
    requirement.add_argument("--kind", default="paper", choices=("paper", "experiment_doc", "implementation", "test", "report"))
    requirement.add_argument("--source", default="")
    requirement.add_argument("--text", required=True)
    requirement.add_argument("--implementation-target", default="")
    requirement.add_argument("--test-target", default="")
    requirement.set_defaults(func=cmd_define_requirement)

    evidence = sub.add_parser("add-evidence")
    evidence.add_argument("--run-id", required=True)
    evidence.add_argument("--id", required=True)
    evidence.add_argument("--type", required=True, choices=("implementation", "test", "report", "command", "metric", "decision"))
    evidence.add_argument("--path", default="")
    evidence.add_argument("--command-text", default="")
    evidence.add_argument("--notes", default="")
    evidence.set_defaults(func=cmd_add_evidence)

    check = sub.add_parser("check-step")
    check.add_argument("--run-id", required=True)
    check.set_defaults(func=cmd_check_step)

    confirm = sub.add_parser("confirm-step")
    confirm.add_argument("--run-id", required=True)
    confirm.add_argument("--phase", default="")
    confirm.add_argument("--step", default="")
    confirm.set_defaults(func=cmd_confirm_step)

    complete = sub.add_parser("complete-step")
    complete.add_argument("--run-id", required=True)
    complete.set_defaults(func=cmd_complete_step)

    status = sub.add_parser("status")
    status.add_argument("--run-id", required=True)
    status.set_defaults(func=cmd_status)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        validate_run_id(args.run_id)
        return args.func(args)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
