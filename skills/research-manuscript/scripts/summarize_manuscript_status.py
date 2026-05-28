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


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize research-manuscript status")
    parser.add_argument("--root", default="research_autopilot", help="Artifact root directory")
    args = parser.parse_args()

    root = Path(args.root)
    audit = load_json(root / "manuscript_audit.json")
    citation_plan = load_json(root / "citation_plan.json")
    summary = {
        "root": str(root),
        "artifacts": {
            "research_design": (root / "research_design.json").exists(),
            "manuscript_blueprint": (root / "manuscript_blueprint.json").exists(),
            "search_evidence": (root / "search_evidence.json").exists(),
            "main_tex": (root / "main.tex").exists(),
            "citation_plan": (root / "citation_plan.json").exists(),
            "manuscript_source_map": (root / "manuscript_source_map.json").exists(),
            "manuscript_audit": (root / "manuscript_audit.json").exists(),
        },
        "audit": {
            "ok": bool(audit.get("ok")),
            "errors": len(audit.get("errors") or []),
            "warnings": len(audit.get("warnings") or []),
            "method_modules_detected": audit.get("method_modules_detected", 0),
        },
        "citations": {
            "included": len(citation_plan.get("included") or []),
            "excluded": len(citation_plan.get("excluded") or []),
        },
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
