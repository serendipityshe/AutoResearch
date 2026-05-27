from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

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
    parse_json_object,
    read_json,
    run_root,
    utc_now,
    validate_run_id,
    write_json,
)
from autolab_contract import (
    contract_path,
    derive_ablation_contract,
    diff_contracts,
    empty_contract,
    freeze_pipeline,
    is_locked,
    load_contract,
    lock_contract,
    save_contract,
    validate_against_contract,
)
import autolab_environment as env_scanner
from autolab_gate import default_phase_plan, empty_gate_status, empty_requirements


def _create_run_skeleton(
    *,
    run_id: str,
    project: dict[str, Any],
    kind: str,
    entry_skill: str,
    paper_source: str,
    root: Path,
) -> tuple[Path, str]:
    directory = run_root(run_id, root)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "reports").mkdir(exist_ok=True)
    now = utc_now()
    git = git_metadata(root)
    run_data = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "project_id": project["project_id"],
        "kind": kind,
        "status": "in_progress",
        "started_at": now,
        "ended_at": "",
        "entry_skill": entry_skill,
        "paper_source": paper_source,
        "git": git,
        "summary": "",
    }
    write_json(directory / "run.json", run_data)
    write_json(directory / "config.json", {"schema_version": SCHEMA_VERSION, "captured_at": now})
    write_json(directory / "artifacts.json", {"artifacts": []})
    write_json(directory / "changed_files.json", {"captured_at": "", "git": git, "files": []})
    write_json(directory / "reports" / "reports_index.json", {"reports": []})
    write_json(directory / "phase_plan.json", default_phase_plan())
    write_json(directory / "requirements.json", empty_requirements())
    write_json(directory / "gate_status.json", empty_gate_status(run_id))
    return directory, now


def _activate_run(root: Path, project_id: str, run_id: str) -> None:
    status_path = autolab_root(root) / "workflow_status.json"
    status = read_json(status_path, default_workflow_status(project_id))
    status["active_run_id"] = run_id
    write_json(status_path, status)


def cmd_init_project(args: argparse.Namespace) -> int:
    project = ensure_project(Path.cwd(), name=args.name, paper_source=args.paper_source)
    print(json.dumps({"project_id": project["project_id"], "autolab_dir": ".autolab"}))
    return 0


def cmd_start_run(args: argparse.Namespace) -> int:
    root = Path.cwd()
    try:
        run_id = validate_run_id(args.run_id) if args.run_id else new_run_id()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if run_root(run_id, root).exists():
        print(f"Run already exists: {run_id}", file=sys.stderr)
        return 1

    project = ensure_project(root, name=args.name, paper_source=args.paper_source)
    directory, now = _create_run_skeleton(
        run_id=run_id,
        project=project,
        kind=args.kind,
        entry_skill=args.entry_skill,
        paper_source=args.paper_source,
        root=root,
    )
    save_contract(run_id, empty_contract(), root)
    _activate_run(root, project["project_id"], run_id)

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
    try:
        directory = run_root(args.run_id)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    path = directory / "run.json"
    run_data = read_json(path, None)
    if run_data is None:
        print(f"Run not found: {args.run_id}", file=sys.stderr)
        return 1

    if run_data.get("status") == args.status:
        print(json.dumps({"run_id": args.run_id, "status": args.status, "unchanged": True}))
        return 0

    now = utc_now()
    run_data["status"] = args.status
    run_data["ended_at"] = now
    run_data["summary"] = args.summary
    write_json(path, run_data)
    append_jsonl(
        directory / "events.jsonl",
        {
            "timestamp": now,
            "level": "info",
            "skill": run_data.get("entry_skill", ""),
            "phase": "",
            "event_type": "run_status_changed",
            "message": f"Run status changed to {args.status}",
            "data": {"status": args.status},
        },
    )
    print(json.dumps({"run_id": args.run_id, "status": args.status, "unchanged": False}))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    status = read_json(autolab_root() / "workflow_status.json", None)
    if status is None:
        print(json.dumps({"initialized": False}))
    else:
        print(json.dumps({"initialized": True, "status": status}))
    return 0


def cmd_scan_environment(args: argparse.Namespace) -> int:
    root = Path.cwd()
    try:
        validate_run_id(args.run_id)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    directory = run_root(args.run_id, root)
    if not (directory / "run.json").exists():
        print(f"Run not found: {args.run_id}", file=sys.stderr)
        return 1

    prior: dict[str, Any] | None = None
    if args.against:
        prior_path = Path(args.against)
        if not prior_path.exists():
            print(f"Prior snapshot not found: {args.against}", file=sys.stderr)
            return 1
        prior = read_json(prior_path, None)
        if prior is None or "items" not in prior:
            print(f"Prior snapshot invalid: {args.against}", file=sys.stderr)
            return 1

    workdir = Path(args.workdir).expanduser()
    try:
        snapshot = env_scanner.scan(workdir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    write_json(directory / "environment_snapshot.json", snapshot)
    decisions_path = directory / "environment_decisions.json"
    if not decisions_path.exists():
        write_json(decisions_path, env_scanner.initial_decisions(snapshot))

    report_path = directory / "reports" / "phase_2.5_environment_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(env_scanner.render_report(snapshot), encoding="utf-8")

    new_items: list[dict[str, Any]] = []
    if prior is not None:
        diff = env_scanner.diff_against(prior, snapshot)
        new_items = diff["new_items"]

    append_jsonl(
        directory / "events.jsonl",
        {
            "timestamp": utc_now(),
            "level": "warning" if (snapshot["items"] or new_items) else "info",
            "skill": args.skill,
            "phase": "phase_2.5_environment",
            "event_type": "environment_scanned",
            "message": f"Environment scan: {len(snapshot['items'])} items, {len(new_items)} new since prior",
            "data": {"item_count": len(snapshot["items"]), "new_items": len(new_items)},
        },
    )

    payload: dict[str, Any] = {
        "run_id": args.run_id,
        "items": len(snapshot["items"]),
        "snapshot": str(directory / "environment_snapshot.json"),
        "report": str(report_path),
    }
    if args.against:
        payload["new_items"] = len(new_items)

    print(json.dumps(payload))
    if new_items:
        return 3
    return 0


def cmd_freeze_pipeline(args: argparse.Namespace) -> int:
    try:
        validate_run_id(args.run_id)
        preprocess = parse_json_object(args.pre, "--pre")
        augment = parse_json_object(args.aug, "--aug")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        result = freeze_pipeline(args.run_id, preprocess, augment)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except PermissionError as exc:
        print(str(exc), file=sys.stderr)
        return 4

    append_jsonl(
        run_root(args.run_id) / "events.jsonl",
        {
            "timestamp": utc_now(),
            "level": "info",
            "skill": args.skill,
            "phase": "phase_4.7_pipeline_freeze",
            "event_type": "pipeline_frozen",
            "message": "Data pipeline frozen",
            "data": result,
        },
    )
    print(json.dumps(result))
    return 0


def cmd_lock_contract(args: argparse.Namespace) -> int:
    try:
        validate_run_id(args.run_id)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        result = lock_contract(args.run_id)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 5

    if not result.get("unchanged"):
        append_jsonl(
            run_root(args.run_id) / "events.jsonl",
            {
                "timestamp": utc_now(),
                "level": "info",
                "skill": args.skill,
                "phase": "phase_7_full_train",
                "event_type": "contract_locked",
                "message": f"Contract locked at {result['locked_at']}",
                "data": {"locked_at": result["locked_at"]},
            },
        )
    print(json.dumps(result))
    return 0


def cmd_validate_contract(args: argparse.Namespace) -> int:
    try:
        validate_run_id(args.run_id)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    pre = None
    aug = None
    try:
        if args.pre:
            pre = parse_json_object(args.pre, "--pre")
        if args.aug:
            aug = parse_json_object(args.aug, "--aug")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        result = validate_against_contract(
            args.run_id,
            preprocess=pre,
            augment=aug,
            require_locked=args.strict,
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result))
    if not result["ok"]:
        if result.get("reason") == "contract_not_locked":
            return 5
        return 3
    return 0


def cmd_derive_ablation(args: argparse.Namespace) -> int:
    root = Path.cwd()
    try:
        validate_run_id(args.parent)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    parent_contract = load_contract(args.parent, root)
    if parent_contract is None:
        print(f"Parent contract not found: {args.parent}", file=sys.stderr)
        return 1
    if not is_locked(parent_contract):
        print(f"Parent contract must be locked before deriving ablation: {args.parent}", file=sys.stderr)
        return 5

    toggles: dict[str, bool] = {}
    for raw in args.toggle:
        if "=" not in raw:
            print(f"Invalid toggle (expected NAME=true|false): {raw}", file=sys.stderr)
            return 2
        name, _, value = raw.partition("=")
        name = name.strip()
        normalized = value.strip().lower()
        if normalized not in ("true", "false", "1", "0"):
            print(f"Invalid toggle value (expected true|false|1|0): {raw}", file=sys.stderr)
            return 2
        toggles[name] = normalized in ("true", "1")
    if not toggles:
        print("At least one --toggle is required", file=sys.stderr)
        return 2

    try:
        child_contract = derive_ablation_contract(
            parent_contract,
            toggles,
            allow_pipeline_change=args.allow_pipeline_change,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 6

    try:
        child_id = validate_run_id(args.run_id) if args.run_id else new_run_id()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if run_root(child_id, root).exists():
        print(f"Run already exists: {child_id}", file=sys.stderr)
        return 1

    project = ensure_project(root, name=args.name, paper_source=args.paper_source)
    directory, now = _create_run_skeleton(
        run_id=child_id,
        project=project,
        kind="ablation",
        entry_skill=args.entry_skill,
        paper_source=args.paper_source,
        root=root,
    )

    child_contract["parent_run_id"] = args.parent
    child_contract["captured_at"] = now
    save_contract(child_id, child_contract, root)
    _activate_run(root, project["project_id"], child_id)

    append_jsonl(
        directory / "events.jsonl",
        {
            "timestamp": now,
            "level": "info",
            "skill": args.entry_skill,
            "phase": "phase_8_eval",
            "event_type": "ablation_derived",
            "message": f"Ablation derived from {args.parent}",
            "data": {
                "parent_run_id": args.parent,
                "toggles": toggles,
                "ablation_diff": child_contract["ablation_diff"],
            },
        },
    )
    print(
        json.dumps(
            {
                "run_id": child_id,
                "parent_run_id": args.parent,
                "ablation_diff": child_contract["ablation_diff"],
            }
        )
    )
    return 0


def cmd_compare_runs(args: argparse.Namespace) -> int:
    try:
        validate_run_id(args.run_a)
        validate_run_id(args.run_b)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    a = load_contract(args.run_a)
    b = load_contract(args.run_b)
    if a is None or b is None:
        missing = args.run_a if a is None else args.run_b
        print(f"Contract not found: {missing}", file=sys.stderr)
        return 1

    diffs = diff_contracts(a, b)
    print(json.dumps({"run_a": args.run_a, "run_b": args.run_b, "diffs": diffs}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Matrix-AutoLab run recording utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-project")
    init.add_argument("--name", default="AutoLab Project")
    init.add_argument("--paper-source", default="main.tex")
    init.set_defaults(func=cmd_init_project)

    start = sub.add_parser("start-run")
    start.add_argument("--kind", required=True, choices=sorted(RUN_KINDS))
    start.add_argument("--entry-skill", required=True)
    start.add_argument("--name", default="AutoLab Project")
    start.add_argument("--paper-source", default="main.tex")
    start.add_argument("--run-id", default="")
    start.set_defaults(func=cmd_start_run)

    finish = sub.add_parser("finish-run")
    finish.add_argument("--run-id", required=True)
    finish.add_argument("--status", required=True, choices=sorted(RUN_STATUS))
    finish.add_argument("--summary", default="")
    finish.set_defaults(func=cmd_finish_run)

    status = sub.add_parser("status")
    status.set_defaults(func=cmd_status)

    scan = sub.add_parser(
        "scan-environment",
        help="Phase 2.5: scan a working directory for stale checkpoints, caches, outputs",
    )
    scan.add_argument("--run-id", required=True)
    scan.add_argument("--workdir", required=True)
    scan.add_argument("--against", default="", help="Path to a prior environment_snapshot.json to diff against")
    scan.add_argument("--skill", default="autolab")
    scan.set_defaults(func=cmd_scan_environment)

    freeze = sub.add_parser(
        "freeze-pipeline",
        help="Phase 4.7: hash and persist preprocess + augment pipeline specs",
    )
    freeze.add_argument("--run-id", required=True)
    freeze.add_argument("--pre", required=True, help="JSON object (or @file) describing preprocess transforms")
    freeze.add_argument("--aug", required=True, help="JSON object (or @file) describing augmentation transforms")
    freeze.add_argument("--skill", default="autolab")
    freeze.set_defaults(func=cmd_freeze_pipeline)

    lock = sub.add_parser(
        "lock-contract",
        help="Validate required fields and lock the contract; subsequent edits to frozen fields are refused",
    )
    lock.add_argument("--run-id", required=True)
    lock.add_argument("--skill", default="autolab")
    lock.set_defaults(func=cmd_lock_contract)

    validate_cmd = sub.add_parser(
        "validate-contract",
        help="Recompute current preprocess/augment hashes and compare to the locked contract",
    )
    validate_cmd.add_argument("--run-id", required=True)
    validate_cmd.add_argument("--pre", default="", help="JSON object (or @file) for the current preprocess spec")
    validate_cmd.add_argument("--aug", default="", help="JSON object (or @file) for the current augment spec")
    validate_cmd.add_argument("--strict", action="store_true", help="Fail if the contract is not yet locked")
    validate_cmd.set_defaults(func=cmd_validate_contract)

    derive = sub.add_parser(
        "derive-ablation",
        help="Create a child run from a locked parent contract; only --toggle changes are accepted",
    )
    derive.add_argument("--parent", required=True)
    derive.add_argument("--toggle", action="append", default=[], required=True, metavar="NAME=true|false")
    derive.add_argument("--entry-skill", default="autolab")
    derive.add_argument("--name", default="AutoLab Project")
    derive.add_argument("--paper-source", default="main.tex")
    derive.add_argument("--run-id", default="")
    derive.add_argument(
        "--allow-pipeline-change",
        action="store_true",
        help="Permit ablations whose only diff would be data/hyperparams (rare; for studying augmentation effects)",
    )
    derive.set_defaults(func=cmd_derive_ablation)

    compare = sub.add_parser(
        "compare-runs",
        help="Output a field-level diff between two contracts",
    )
    compare.add_argument("--run-a", required=True)
    compare.add_argument("--run-b", required=True)
    compare.set_defaults(func=cmd_compare_runs)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
