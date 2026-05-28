from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DATASET_ROLES = ["primary", "validation", "external_test", "supplementary"]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def list_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def text(value: Any) -> str:
    return str(value or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize research-design artifact status")
    parser.add_argument("--root", default="research_autopilot", help="Artifact root directory")
    args = parser.parse_args()

    root = Path(args.root)
    design = load_json(root / "research_design.json")
    blueprint = load_json(root / "manuscript_blueprint.json")
    method = design.get("proposed_method") if isinstance(design.get("proposed_method"), dict) else {}
    modules = list_items(method.get("modules"))
    strategy = design.get("dataset_strategy") if isinstance(design.get("dataset_strategy"), dict) else {}
    present_roles = sorted(role for role in DATASET_ROLES if list_items(strategy.get(role)))
    alignments = list_items(design.get("experiment_alignment"))
    sections = [text(item.get("section")) for item in list_items(blueprint.get("section_plan")) if text(item.get("section"))]
    summary = {
        "root": str(root),
        "artifacts": {
            "research_design": (root / "research_design.json").exists(),
            "manuscript_blueprint": (root / "manuscript_blueprint.json").exists(),
        },
        "topic": text(design.get("topic")),
        "confirmed_route": bool(isinstance(design.get("confirmed_route"), dict) and design["confirmed_route"].get("user_confirmed") is True),
        "method_name": text(method.get("name")),
        "method_modules": len(modules),
        "dataset_roles": present_roles,
        "experiment_alignment_items": len(alignments),
        "blueprint_sections": sections,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
