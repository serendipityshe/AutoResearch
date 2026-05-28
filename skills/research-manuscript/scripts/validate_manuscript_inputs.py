from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DATASET_ROLES = ["primary", "validation", "external_test", "supplementary"]
EVIDENCE_COLLECTIONS = [
    "papers",
    "datasets",
    "code_repositories",
    "baseline_candidates",
    "web_sources",
    "pubmed_records",
    "zotero_items",
    "user_sources",
]
LOCATOR_KEYS = {
    "url",
    "doi",
    "pmid",
    "pmcid",
    "arxiv_id",
    "citation_key",
    "local_path",
    "paper_or_repo_url",
}


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing required artifact: {path.name}")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name} is not valid JSON: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{path.name} must contain a JSON object")
        return {}
    return data


def text(value: Any) -> str:
    return str(value or "").strip()


def list_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def has_locator(item: dict[str, Any]) -> bool:
    return any(text(item.get(key)) for key in LOCATOR_KEYS)


def source_id(collection: str, index: int, item: dict[str, Any]) -> str:
    return text(item.get("id") or item.get("title") or item.get("name") or f"{collection}[{index}]")


def build_citation_plan(evidence: dict[str, Any]) -> dict[str, Any]:
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for collection in EVIDENCE_COLLECTIONS:
        for index, item in enumerate(list_items(evidence.get(collection))):
            entry = {
                "id": source_id(collection, index, item),
                "collection": collection,
                "title": text(item.get("title") or item.get("name")),
                "locator": next((key for key in LOCATOR_KEYS if text(item.get(key))), ""),
            }
            if has_locator(item):
                included.append(entry)
            else:
                entry["reason"] = "missing stable locator"
                excluded.append(entry)
    return {"included": included, "excluded": excluded}


def build_source_map(design: dict[str, Any], blueprint: dict[str, Any], citation_plan: dict[str, Any]) -> dict[str, Any]:
    method = design.get("proposed_method") if isinstance(design.get("proposed_method"), dict) else {}
    strategy = design.get("dataset_strategy") if isinstance(design.get("dataset_strategy"), dict) else {}
    return {
        "sections": [
            {
                "section": text(item.get("section")),
                "source": "manuscript_blueprint.section_plan",
                "purpose": text(item.get("purpose")),
            }
            for item in list_items(blueprint.get("section_plan"))
        ],
        "method_modules": [
            {
                "name": text(item.get("name")),
                "source": "research_design.proposed_method.modules",
                "evidence_ids": item.get("evidence_ids") or [],
                "ablation": text(item.get("ablation")),
            }
            for item in list_items(method.get("modules"))
        ],
        "dataset_roles": {
            role: [
                {
                    "name": text(item.get("name")),
                    "source": f"research_design.dataset_strategy.{role}",
                    "evidence_ids": item.get("evidence_ids") or [],
                }
                for item in list_items(strategy.get(role))
            ]
            for role in DATASET_ROLES
        },
        "citations": citation_plan.get("included", []),
    }


def validate_design(design: dict[str, Any], errors: list[str]) -> int:
    for field in ("topic", "confirmed_route", "title_candidate", "dataset_strategy", "proposed_method", "experiment_alignment"):
        if field not in design:
            errors.append(f"research_design.json missing {field}")
    route = design.get("confirmed_route")
    if not isinstance(route, dict) or route.get("user_confirmed") is not True:
        errors.append("confirmed_route.user_confirmed must be true")
    strategy = design.get("dataset_strategy") if isinstance(design.get("dataset_strategy"), dict) else {}
    missing_roles = [role for role in DATASET_ROLES if not list_items(strategy.get(role))]
    if missing_roles:
        errors.append(f"dataset_strategy missing populated roles: {missing_roles}")
    method = design.get("proposed_method") if isinstance(design.get("proposed_method"), dict) else {}
    modules = list_items(method.get("modules"))
    if len(modules) < 3:
        errors.append("proposed_method requires at least 3 method modules")
    if not text(method.get("total_objective")):
        errors.append("proposed_method.total_objective is required")
    for index, module in enumerate(modules):
        label = text(module.get("name")) or f"module[{index}]"
        for field in ("inputs", "outputs", "formulas", "loss_terms"):
            if not module.get(field):
                errors.append(f"{label} missing {field}")
        if not text(module.get("ablation")):
            errors.append(f"{label} missing ablation")
    if not list_items(design.get("experiment_alignment")):
        errors.append("experiment_alignment requires at least one item")
    return len(modules)


def validate_blueprint(blueprint: dict[str, Any], errors: list[str]) -> int:
    if not text(blueprint.get("central_argument")):
        errors.append("manuscript_blueprint.central_argument is required")
    sections = list_items(blueprint.get("section_plan"))
    names = {text(item.get("section")).lower() for item in sections}
    required = {
        "abstract",
        "introduction",
        "related work and design rationale",
        "problem statement",
        "method",
        "planned study design",
        "planned results presentation",
        "risks",
        "discussion",
    }
    missing = sorted(required - names)
    if missing:
        errors.append(f"manuscript_blueprint.section_plan missing sections: {missing}")
    if not list_items(blueprint.get("claim_to_experiment_map")):
        errors.append("manuscript_blueprint.claim_to_experiment_map requires at least one item")
    return len(sections)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate research-manuscript inputs")
    parser.add_argument("--root", default="research_autopilot", help="Artifact root directory")
    args = parser.parse_args()

    root = Path(args.root)
    errors: list[str] = []
    warnings: list[str] = []
    design = load_json(root / "research_design.json", errors)
    blueprint = load_json(root / "manuscript_blueprint.json", errors)
    evidence = load_json(root / "search_evidence.json", errors)

    module_count = validate_design(design, errors) if design else 0
    section_count = validate_blueprint(blueprint, errors) if blueprint else 0
    citation_plan = build_citation_plan(evidence) if evidence else {"included": [], "excluded": []}
    if evidence and not citation_plan["included"]:
        errors.append("search_evidence.json has no citable sources with stable locators")
    if citation_plan["excluded"]:
        warnings.append(f"{len(citation_plan['excluded'])} evidence sources excluded from bibliography")

    if evidence:
        (root / "citation_plan.json").write_text(json.dumps(citation_plan, indent=2, ensure_ascii=False), encoding="utf-8")
    if design and blueprint and evidence:
        source_map = build_source_map(design, blueprint, citation_plan)
        (root / "manuscript_source_map.json").write_text(json.dumps(source_map, indent=2, ensure_ascii=False), encoding="utf-8")

    result = {
        "ok": not errors,
        "root": str(root),
        "errors": errors,
        "warnings": warnings,
        "method_modules": module_count,
        "blueprint_sections": section_count,
        "citable_sources": len(citation_plan["included"]),
        "excluded_sources": len(citation_plan["excluded"]),
    }
    stream = sys.stdout if not errors else sys.stderr
    print(json.dumps(result, indent=2, ensure_ascii=False), file=stream)
    return 0 if not errors else 3


if __name__ == "__main__":
    raise SystemExit(main())
