from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DATASET_ROLES = ["primary", "validation", "external_test", "supplementary"]
ALLOWED_EXPECTED_STATUS = {"hypothesis", "expected", "planned", "needs_evidence"}
MEASURED_RESULT_KEYS = {"value", "measured_value", "numeric_result", "dice", "iou", "auc", "accuracy"}


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


def dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def list_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def list_text(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text(item) for item in value if text(item)]


def formula_like(formula: str) -> bool:
    return "=" in formula or "\\mathcal" in formula or "\\operatorname" in formula or "\\arg" in formula


def item_label(item: dict[str, Any], fallback: str) -> str:
    return text(item.get("name") or item.get("section") or item.get("claim") or fallback)


def validate_route(design: dict[str, Any], errors: list[str]) -> None:
    route = design.get("confirmed_route")
    if not isinstance(route, dict):
        errors.append("confirmed_route must be an object with user_confirmed=true")
        return
    if route.get("user_confirmed") is not True:
        errors.append("confirmed route is not confirmed")
    if not (text(route.get("route_id")) or text(route.get("description"))):
        errors.append("confirmed_route must include route_id or description")


def validate_dataset_strategy(strategy: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    missing = [role for role in DATASET_ROLES if role not in strategy]
    if missing:
        errors.append(f"dataset_strategy missing roles: {missing}")
    for role in DATASET_ROLES:
        items = list_items(strategy.get(role))
        if role in strategy and not isinstance(strategy.get(role), list):
            errors.append(f"dataset_strategy.{role} must be a list")
        if not items:
            errors.append(f"dataset_strategy.{role} requires at least one dataset")
        for index, item in enumerate(items):
            label = item_label(item, f"{role}[{index}]")
            if not text(item.get("role")):
                warnings.append(f"dataset {label} has no role note")
            if not (text(item.get("rationale")) or text(item.get("reason"))):
                warnings.append(f"dataset {label} has no selection rationale")
            if not text(item.get("risk")):
                warnings.append(f"dataset {label} has no risk note")


def validate_evidence_linked_items(
    design: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    for collection in ("frontier_landscape", "domain_difficulties"):
        items = list_items(design.get(collection))
        if not items:
            errors.append(f"{collection} requires at least one item")
        for index, item in enumerate(items):
            label = item_label(item, f"{collection}[{index}]")
            if not list_text(item.get("evidence_ids")):
                errors.append(f"{collection}:{label} lacks evidence_ids")
            if collection == "domain_difficulties" and not (text(item.get("experiment_impact")) or text(item.get("impact"))):
                errors.append(f"domain difficulty {label} lacks experiment_impact")
            if len(list_text(item.get("evidence_ids"))) < 2:
                warnings.append(f"{collection}:{label} has fewer than 2 evidence ids")


def validate_method(design: dict[str, Any], errors: list[str], warnings: list[str]) -> list[dict[str, Any]]:
    rationale = dict_value(design.get("method_rationale"))
    if not list_text(rationale.get("existing_method_problems")):
        errors.append("method_rationale.existing_method_problems requires at least one problem")
    if not text(rationale.get("design_direction")):
        errors.append("method_rationale.design_direction is required")
    if not text(rationale.get("bridge_logic")):
        warnings.append("method_rationale.bridge_logic is recommended")

    method = dict_value(design.get("proposed_method"))
    if not text(method.get("name")):
        errors.append("proposed_method.name is required")
    modules = list_items(method.get("modules"))
    if len(modules) < 3:
        errors.append("proposed_method requires at least 3 method modules")
    for index, module in enumerate(modules):
        label = item_label(module, f"module[{index}]")
        if not text(module.get("name")):
            errors.append(f"{label} missing name")
        if not (text(module.get("purpose")) or text(module.get("rationale"))):
            errors.append(f"{label} missing purpose")
        if not list_text(module.get("inputs")):
            errors.append(f"{label} missing inputs")
        if not list_text(module.get("outputs")):
            errors.append(f"{label} missing outputs")
        formulas = list_text(module.get("formulas"))
        if not formulas:
            errors.append(f"{label} missing formulas")
        elif not any(formula_like(formula) for formula in formulas):
            errors.append(f"{label} formulas do not look mathematical")
        if not list_text(module.get("loss_terms")):
            errors.append(f"{label} missing loss_terms")
        if not text(module.get("ablation")):
            errors.append(f"{label} missing ablation")
        if not list_text(module.get("evidence_ids")):
            errors.append(f"{label} lacks evidence_ids")
    total = text(method.get("total_objective"))
    if not total:
        errors.append("proposed_method.total_objective is required")
    elif "\\mathcal{L}" not in total:
        warnings.append("proposed_method.total_objective does not look like a LaTeX loss formula")
    return modules


def validate_alignment(design: dict[str, Any], modules: list[dict[str, Any]], errors: list[str]) -> None:
    alignments = list_items(design.get("experiment_alignment"))
    if not alignments:
        errors.append("experiment_alignment requires at least one claim-to-experiment item")
        return
    aligned_modules = {text(item.get("module")).lower() for item in alignments if text(item.get("module"))}
    aligned_ablations = {text(item.get("ablation")).lower() for item in alignments if text(item.get("ablation"))}
    for index, item in enumerate(alignments):
        label = item_label(item, f"experiment_alignment[{index}]")
        for field in ("claim", "module", "ablation"):
            if not text(item.get(field)):
                errors.append(f"{label} missing {field}")
        for field in ("datasets", "baselines", "metrics"):
            if not list_text(item.get(field)):
                errors.append(f"{label} missing {field}")
    for module in modules:
        name = text(module.get("name")).lower()
        ablation = text(module.get("ablation")).lower()
        if name and name not in aligned_modules:
            errors.append(f"experiment_alignment missing module: {module.get('name')}")
        if ablation and ablation not in aligned_ablations:
            errors.append(f"experiment_alignment missing ablation: {module.get('ablation')}")


def validate_expected_and_risks(design: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    expected = list_items(design.get("expected_results"))
    if not expected:
        errors.append("expected_results requires at least one planned hypothesis")
    for index, item in enumerate(expected):
        status = text(item.get("status")) or "hypothesis"
        if status not in ALLOWED_EXPECTED_STATUS:
            errors.append(f"expected_results[{index}] status must be one of {sorted(ALLOWED_EXPECTED_STATUS)}")
        if MEASURED_RESULT_KEYS.intersection(item):
            errors.append(f"expected_results[{index}] must not include measured result fields")
        if not text(item.get("claim")):
            errors.append(f"expected_results[{index}] missing claim")
    risks = list_items(design.get("risk_review"))
    if not risks:
        errors.append("risk_review requires at least one risk")
    for index, item in enumerate(risks):
        if not text(item.get("risk")):
            warnings.append(f"risk_review[{index}] missing risk text")
        if not text(item.get("mitigation")):
            warnings.append(f"risk_review[{index}] missing mitigation")


def validate_blueprint(blueprint: dict[str, Any], errors: list[str]) -> None:
    if not text(blueprint.get("title")):
        errors.append("manuscript_blueprint.title is required")
    if not text(blueprint.get("central_argument")):
        errors.append("manuscript_blueprint.central_argument is required")
    sections = list_items(blueprint.get("section_plan"))
    if not sections:
        errors.append("manuscript_blueprint.section_plan requires at least one section")
    section_names = {item_label(item, "").lower() for item in sections}
    if "method" not in section_names:
        errors.append("manuscript_blueprint.section_plan must include Method")
    claim_map = list_items(blueprint.get("claim_to_experiment_map"))
    if not claim_map:
        errors.append("manuscript_blueprint.claim_to_experiment_map requires at least one item")
    for index, item in enumerate(claim_map):
        label = item_label(item, f"claim_to_experiment_map[{index}]")
        if not text(item.get("claim")):
            errors.append(f"{label} missing claim")
        if not (text(item.get("experiment")) or text(item.get("planned_evidence"))):
            errors.append(f"{label} missing experiment or planned_evidence")


def validate_design_package(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    design = load_json(root / "research_design.json", errors)
    blueprint = load_json(root / "manuscript_blueprint.json", errors)
    if design:
        for field in (
            "topic",
            "confirmed_route",
            "title_candidate",
            "dataset_strategy",
            "frontier_landscape",
            "domain_difficulties",
            "method_rationale",
            "proposed_method",
            "experiment_alignment",
            "expected_results",
            "risk_review",
        ):
            if field not in design:
                errors.append(f"research_design.json missing {field}")
        if not text(design.get("topic")):
            errors.append("topic is required")
        if not text(design.get("title_candidate")):
            errors.append("title_candidate is required")
        validate_route(design, errors)
        validate_dataset_strategy(dict_value(design.get("dataset_strategy")), errors, warnings)
        validate_evidence_linked_items(design, errors, warnings)
        modules = validate_method(design, errors, warnings)
        validate_alignment(design, modules, errors)
        validate_expected_and_risks(design, errors, warnings)
    if blueprint:
        validate_blueprint(blueprint, errors)
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate research-design artifacts")
    parser.add_argument("--root", default="research_autopilot", help="Artifact root directory")
    args = parser.parse_args()

    root = Path(args.root)
    errors, warnings = validate_design_package(root)
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
