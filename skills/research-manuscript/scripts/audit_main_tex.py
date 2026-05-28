from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


BANNED_ABSTRACT_PHRASES = [
    "this document",
    "manuscript-ready",
    "study design draft",
    "manuscript-grade",
    "draft prepared",
    "present interaction",
]


def read_text(path: Path, errors: list[str]) -> str:
    if not path.exists():
        errors.append(f"missing required artifact: {path.name}")
        return ""
    return path.read_text(encoding="utf-8")


def extract_environment(tex: str, name: str) -> str:
    match = re.search(rf"\\begin\{{{name}\}}(.*?)\\end\{{{name}\}}", tex, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_section(tex: str, heading_patterns: list[str]) -> str:
    starts: list[tuple[int, str]] = []
    for match in re.finditer(r"\\section\*?\{([^}]*)\}", tex):
        title = match.group(1).strip()
        if any(pattern.lower() in title.lower() for pattern in heading_patterns):
            starts.append((match.end(), title))
    if not starts:
        return ""
    start = starts[0][0]
    next_match = re.search(r"\\section\*?\{", tex[start:])
    end = start + next_match.start() if next_match else len(tex)
    return tex[start:end]


def has_section(tex: str, patterns: list[str]) -> bool:
    return bool(extract_section(tex, patterns))


def count_method_modules(method_section: str) -> int:
    return len(re.findall(r"\\subsection\*?\{", method_section))


def audit_abstract(tex: str, errors: list[str]) -> None:
    abstract = extract_environment(tex, "abstract")
    if not abstract:
        errors.append("missing abstract environment")
        return
    lower = abstract.lower()
    for phrase in BANNED_ABSTRACT_PHRASES:
        if phrase in lower:
            errors.append(f"banned abstract phrase: {phrase}")
    if "we propose" not in lower:
        errors.append("abstract must use formal paper phrasing with 'We propose'")
    if not any(term in lower for term in ("imaging", "image", "mri", "ultrasound", "ct", "radiology")):
        errors.append("abstract missing expected move: imaging context")
    for needed in ("method", "dataset"):
        if needed not in lower and needed + "s" not in lower:
            errors.append(f"abstract missing expected move: {needed}")
    if "limit" not in lower and "existing" not in lower:
        errors.append("abstract missing expected move: limitation")
    if "tbd" in lower:
        errors.append("abstract must not contain TBD")


def audit_related_work(tex: str, errors: list[str]) -> None:
    section = extract_section(tex, ["Related Work"])
    if not section:
        errors.append("missing Related Work and Design Rationale section")
        return
    required_groups = {
        "static segmentation": ("static", "segmentation"),
        "anatomical context": ("context", "prior"),
        "boundary or topology": ("boundary", "topology", "shape", "graph"),
        "uncertainty": ("uncertain", "uncertainty"),
        "cross-dataset": ("cross-dataset", "cross dataset", "multicenter", "external"),
        "Why direct transfer is insufficient": ("why direct transfer is insufficient",),
    }
    lower = section.lower()
    for label, alternatives in required_groups.items():
        if not any(item in lower for item in alternatives):
            errors.append(f"Related Work missing group: {label}")


def audit_problem_statement(tex: str, errors: list[str]) -> None:
    section = extract_section(tex, ["Problem Statement"])
    if not section:
        errors.append("missing Problem Statement section")
        return
    required_symbols = ["x", "M", "P", "R_g", "\\hat{M}", "\\mathcal{D}"]
    for symbol in required_symbols:
        if symbol not in section:
            errors.append(f"Problem Statement missing mathematical symbol: {symbol}")
    if "objective" not in section.lower():
        errors.append("Problem Statement missing objective language")


def audit_method(tex: str, errors: list[str]) -> int:
    section = extract_section(tex, ["Method"])
    if not section:
        errors.append("missing Method section")
        return 0
    modules = count_method_modules(section)
    if modules < 3:
        errors.append("Method requires at least 3 module subsections")
    if "\\mathcal{L}_{total}" not in section and "\\mathcal{L}_{\\text{total}}" not in section:
        errors.append("Method missing total objective \\mathcal{L}_{total}")
    equation_count = len(re.findall(r"\\begin\{equation\}|\\\[", section))
    if equation_count < 3:
        errors.append("Method requires at least 3 equations")
    for keyword in ("Input", "Output", "Loss", "Ablation"):
        if len(re.findall(keyword, section, re.IGNORECASE)) < 3:
            errors.append(f"Method modules missing repeated {keyword} statements")
    return modules


def audit_study_design(tex: str, errors: list[str]) -> None:
    section = extract_section(tex, ["Study Design", "Experimental Protocol"])
    if not section:
        errors.append("missing Planned Study Design section")
        return
    required = [
        "dataset",
        "primary",
        "validation",
        "external",
        "supplementary",
        "inclusion",
        "exclusion",
        "preprocessing",
        "implementation preset",
        "baselines",
        "metrics",
        "ablation",
        "statistics",
    ]
    lower = section.lower()
    for item in required:
        if item not in lower:
            errors.append(f"Study Design missing required element: {item}")


def audit_results(tex: str, errors: list[str]) -> None:
    section = extract_section(tex, ["Planned Results", "Results Presentation"])
    if not section:
        errors.append("missing Planned Results Presentation section")
        return
    if "TBD" not in section and "to be filled" not in section.lower():
        errors.append("Planned Results must contain TBD or to be filled placeholders")
    for line in section.splitlines():
        if "&" not in line or "TBD" in line or "to be filled" in line.lower():
            continue
        if re.search(r"(?<![A-Za-z])0?\.\d+(?![A-Za-z])", line):
            errors.append(f"non-TBD numeric result in planned table: {line.strip()}")
            break


def audit_risks_and_discussion(tex: str, errors: list[str]) -> None:
    risks = extract_section(tex, ["Risks", "Failure Modes", "Risk Mitigation"])
    discussion = extract_section(tex, ["Discussion"])
    if not risks:
        errors.append("missing Risks or Failure Modes section")
        return
    if not discussion:
        errors.append("missing Discussion section")
    lower = risks.lower()
    for item in ("dataset", "external", "topology", "baseline"):
        if item not in lower:
            errors.append(f"Risks section missing restrained risk topic: {item}")


def audit_tex(root: Path, tex_path: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    tex = read_text(tex_path, errors)
    module_count = 0
    if tex:
        audit_abstract(tex, errors)
        for label, patterns in {
            "Introduction": ["Introduction"],
            "Expected Contributions": ["Expected Contributions", "Contributions"],
            "Conclusion": ["Conclusion"],
        }.items():
            if not has_section(tex, patterns):
                warnings.append(f"missing optional/recommended section: {label}")
        audit_related_work(tex, errors)
        audit_problem_statement(tex, errors)
        module_count = audit_method(tex, errors)
        audit_study_design(tex, errors)
        audit_results(tex, errors)
        audit_risks_and_discussion(tex, errors)
        if "\\begin{thebibliography}" not in tex and "\\bibliography{" not in tex:
            warnings.append("bibliography not found")
    result = {
        "ok": not errors,
        "root": str(root),
        "path": str(tex_path),
        "errors": errors,
        "warnings": warnings,
        "method_modules_detected": module_count,
    }
    (root / "manuscript_audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit research-manuscript main.tex")
    parser.add_argument("--root", default="research_autopilot", help="Artifact root directory")
    parser.add_argument("--tex", default="main.tex", help="main.tex path relative to root or absolute")
    args = parser.parse_args()
    root = Path(args.root)
    tex_path = Path(args.tex)
    if not tex_path.is_absolute():
        tex_path = root / tex_path
    result = audit_tex(root, tex_path)
    stream = sys.stdout if result["ok"] else sys.stderr
    print(json.dumps(result, indent=2, ensure_ascii=False), file=stream)
    return 0 if result["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
