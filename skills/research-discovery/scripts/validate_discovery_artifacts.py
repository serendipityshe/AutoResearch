from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


LOCATOR_KEYS = {
    "url",
    "doi",
    "pmid",
    "pmcid",
    "arxiv_id",
    "paper_or_repo_url",
    "local_path",
    "citation_key",
    "hf_dataset_id",
    "figshare_doi",
    "zenodo_doi",
}

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

LANDSCAPE_COLLECTIONS = [
    "dataset_candidates",
    "frontier_hotspots",
    "domain_difficulties",
    "baseline_candidates",
    "method_gap_matrix",
    "route_candidates",
]


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


def has_locator(item: dict[str, Any]) -> bool:
    return any(str(item.get(key) or "").strip() for key in LOCATOR_KEYS)


def item_id(item: dict[str, Any], fallback: str) -> str:
    return str(item.get("id") or item.get("name") or item.get("title") or fallback)


def list_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def validate_evidence(evidence: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    for collection in EVIDENCE_COLLECTIONS:
        for index, item in enumerate(list_items(evidence.get(collection))):
            label = item_id(item, f"{collection}[{index}]")
            if not has_locator(item):
                errors.append(f"{collection}:{label} lacks a stable locator")
            if collection == "datasets":
                roles = item.get("candidate_roles") or item.get("roles") or item.get("role")
                if not roles:
                    warnings.append(f"dataset {label} has no candidate role")
                if not str(item.get("license") or "").strip():
                    warnings.append(f"dataset {label} has unknown license")
            if collection == "code_repositories":
                if not str(item.get("license") or "").strip():
                    warnings.append(f"repo {label} has unknown license")
                if not (item.get("train_entrypoints") or item.get("eval_entrypoints")):
                    warnings.append(f"repo {label} has no train/eval entrypoint recorded")


def validate_landscape(landscape: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    for collection in LANDSCAPE_COLLECTIONS:
        if collection not in landscape:
            errors.append(f"research_landscape.json missing {collection}")

    datasets = list_items(landscape.get("dataset_candidates"))
    routes = list_items(landscape.get("route_candidates"))
    hotspots = list_items(landscape.get("frontier_hotspots"))
    difficulties = list_items(landscape.get("domain_difficulties"))
    baselines = list_items(landscape.get("baseline_candidates"))

    if not datasets:
        errors.append("research_landscape.json must include at least one dataset candidate")
    if not routes:
        errors.append("research_landscape.json must include at least one route candidate")
    if not baselines:
        warnings.append("research_landscape.json has no baseline candidates")

    for index, dataset in enumerate(datasets):
        label = item_id(dataset, f"dataset_candidates[{index}]")
        roles = dataset.get("candidate_roles") or dataset.get("roles") or dataset.get("role")
        if not roles:
            errors.append(f"dataset candidate {label} lacks candidate_roles")

    for index, hotspot in enumerate(hotspots):
        label = item_id(hotspot, f"frontier_hotspots[{index}]")
        evidence_ids = hotspot.get("evidence_ids") or []
        if not isinstance(evidence_ids, list) or not evidence_ids:
            errors.append(f"frontier hotspot {label} lacks evidence_ids")
        if len(evidence_ids) < 2 and hotspot.get("signal_strength") not in {"weak_signal", "background"}:
            warnings.append(f"frontier hotspot {label} has fewer than 2 evidence ids")
        window = str(hotspot.get("time_window") or "")
        if "12" not in window and "1" not in window and hotspot.get("signal_strength") != "background":
            warnings.append(f"frontier hotspot {label} should record latest-12-month time_window")

    for index, difficulty in enumerate(difficulties):
        label = item_id(difficulty, f"domain_difficulties[{index}]")
        evidence_ids = difficulty.get("evidence_ids") or []
        if not isinstance(evidence_ids, list) or not evidence_ids:
            errors.append(f"domain difficulty {label} lacks evidence_ids")
        if not str(difficulty.get("experiment_impact") or "").strip():
            errors.append(f"domain difficulty {label} lacks experiment_impact")
        if len(evidence_ids) < 2:
            warnings.append(f"domain difficulty {label} has fewer than 2 evidence ids")

    for index, route in enumerate(routes):
        label = item_id(route, f"route_candidates[{index}]")
        evidence_ids = route.get("evidence_ids") or []
        if not isinstance(evidence_ids, list) or not evidence_ids:
            errors.append(f"route candidate {label} lacks evidence_ids")
        if not route.get("failure_risks"):
            warnings.append(f"route candidate {label} lacks failure_risks")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate research-discovery artifacts")
    parser.add_argument("--root", default="research_autopilot", help="Artifact root directory")
    args = parser.parse_args()

    root = Path(args.root)
    errors: list[str] = []
    warnings: list[str] = []

    plan = load_json(root / "discovery_plan.json", errors)
    evidence = load_json(root / "search_evidence.json", errors)
    landscape = load_json(root / "research_landscape.json", errors)
    brief = root / "research_brief.md"
    if not brief.exists():
        errors.append("missing required artifact: research_brief.md")

    if plan:
        for field in ["topic", "time_policy", "queries", "source_plan"]:
            if field not in plan:
                errors.append(f"discovery_plan.json missing {field}")
    if evidence:
        validate_evidence(evidence, errors, warnings)
    if landscape:
        validate_landscape(landscape, errors, warnings)

    result = {
        "ok": not errors,
        "root": str(root),
        "errors": errors,
        "warnings": warnings,
    }
    stream = sys.stdout if not errors else sys.stderr
    print(json.dumps(result, indent=2, ensure_ascii=False), file=stream)
    return 0 if not errors else 3


if __name__ == "__main__":
    raise SystemExit(main())
