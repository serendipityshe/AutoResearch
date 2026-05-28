from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def count_items(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    return len(value) if isinstance(value, list) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize research-discovery artifact status")
    parser.add_argument("--root", default="research_autopilot", help="Artifact root directory")
    args = parser.parse_args()

    root = Path(args.root)
    evidence = load_json(root / "search_evidence.json")
    landscape = load_json(root / "research_landscape.json")
    summary = {
        "root": str(root),
        "artifacts": {
            "discovery_plan": (root / "discovery_plan.json").exists(),
            "search_evidence": (root / "search_evidence.json").exists(),
            "research_landscape": (root / "research_landscape.json").exists(),
            "research_brief": (root / "research_brief.md").exists(),
        },
        "evidence_counts": {
            "papers": count_items(evidence, "papers"),
            "datasets": count_items(evidence, "datasets"),
            "code_repositories": count_items(evidence, "code_repositories"),
            "baseline_candidates": count_items(evidence, "baseline_candidates"),
            "web_sources": count_items(evidence, "web_sources"),
        },
        "landscape_counts": {
            "dataset_candidates": count_items(landscape, "dataset_candidates"),
            "frontier_hotspots": count_items(landscape, "frontier_hotspots"),
            "domain_difficulties": count_items(landscape, "domain_difficulties"),
            "baseline_candidates": count_items(landscape, "baseline_candidates"),
            "route_candidates": count_items(landscape, "route_candidates"),
        },
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
