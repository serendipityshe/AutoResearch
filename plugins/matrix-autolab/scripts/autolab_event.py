from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from autolab_common import append_jsonl, run_root, utc_now


def parse_json_arg(value: str, option: str) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for {option}: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"Invalid JSON for {option}: expected an object")
    return parsed


def require_run(run_id: str) -> Path:
    directory = run_root(run_id)
    if not (directory / "run.json").exists():
        raise FileNotFoundError(f"Run not found: {run_id}")
    return directory


def cmd_event(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    now = utc_now()
    record = {
        "timestamp": now,
        "level": args.level,
        "skill": args.skill,
        "phase": args.phase,
        "event_type": args.type,
        "message": args.message,
        "data": parse_json_arg(args.data, "--data"),
    }
    append_jsonl(directory / "events.jsonl", record)
    print(json.dumps({"recorded": "event"}))
    return 0


def metric_value(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid metric value: {value}") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"Metric value must be finite: {value}")
    return parsed


def cmd_metric(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    now = utc_now()
    value = metric_value(args.value)
    record = {
        "timestamp": now,
        "source": args.source,
        "phase": args.phase,
        "step": args.step,
        "epoch": args.epoch,
        "split": args.split,
        "name": args.name,
        "value": value,
        "unit": args.unit,
        "context": parse_json_arg(args.context, "--context"),
    }
    append_jsonl(directory / "metrics.jsonl", record)
    append_jsonl(
        directory / "events.jsonl",
        {
            "timestamp": now,
            "level": "info",
            "skill": args.source,
            "phase": args.phase,
            "event_type": "metric_recorded",
            "message": f"Metric recorded: {args.name}",
            "data": {"name": args.name, "value": value},
        },
    )
    print(json.dumps({"recorded": "metric"}))
    return 0


def cmd_error(args: argparse.Namespace) -> int:
    directory = require_run(args.run_id)
    now = utc_now()
    record = {
        "timestamp": now,
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
            "timestamp": now,
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
    event.add_argument("--level", default="info", choices=("debug", "info", "warning", "error"))
    event.add_argument("--data", default="")
    event.set_defaults(func=cmd_event)

    metric = sub.add_parser("metric")
    metric.add_argument("--run-id", required=True)
    metric.add_argument("--name", required=True)
    metric.add_argument("--value", required=True)
    metric.add_argument("--source", default="")
    metric.add_argument("--phase", default="")
    metric.add_argument("--step", type=int, default=None)
    metric.add_argument("--epoch", type=int, default=None)
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
    error.add_argument("--severity", default="error", choices=("warning", "error", "critical"))
    error.add_argument("--command-text", default="")
    error.add_argument("--log-excerpt", default="")
    error.add_argument("--suggested-next-step", default="")
    error.set_defaults(func=cmd_error)
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
