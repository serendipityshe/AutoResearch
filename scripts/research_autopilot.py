from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from autolab_common import read_json, run_root, utc_now, validate_run_id, write_json


RESEARCH_SCHEMA_VERSION = "0.1.0"
PLANNING_DIR = "research_autopilot"

ADAPTER_STATUSES = {
    "not_run",
    "findings",
    "no_findings",
    "not_applicable",
    "manual",
    "error",
}

DISCOVERY_ADAPTERS: list[dict[str, Any]] = [
    {
        "id": "web",
        "name": "Web search adapter",
        "source_types": ["web_sources", "papers", "datasets", "baseline_candidates"],
        "preferred_tools": ["Codex web search", "browser"],
        "purpose": "Find current project pages, benchmark pages, official documentation, and news about active research areas.",
    },
    {
        "id": "github",
        "name": "GitHub adapter",
        "source_types": ["code_repositories", "baseline_candidates"],
        "preferred_tools": ["GitHub MCP", "GitHub search", "GitHub app"],
        "purpose": "Find official implementations, baseline repositories, training entrypoints, licenses, and recent activity.",
    },
    {
        "id": "huggingface",
        "name": "Hugging Face adapter",
        "source_types": ["papers", "datasets", "code_repositories", "baseline_candidates"],
        "preferred_tools": ["Hugging Face MCP", "HF Hub search"],
        "purpose": "Find HF papers, datasets, models, Spaces, dataset cards, and model cards.",
    },
    {
        "id": "scholarly",
        "name": "arXiv / Semantic Scholar adapter",
        "source_types": ["papers", "baseline_candidates"],
        "preferred_tools": ["arXiv MCP", "Semantic Scholar MCP", "official paper pages"],
        "purpose": "Find papers, citation links, related work, and methods that define baselines.",
    },
    {
        "id": "pubmed",
        "name": "PubMed adapter",
        "source_types": ["papers", "pubmed_records"],
        "preferred_tools": ["pubmed-search skill", "PubMed"],
        "purpose": "Find biomedical and clinical literature when the research idea is medical, biological, or healthcare related.",
    },
    {
        "id": "zotero",
        "name": "Zotero adapter",
        "source_types": ["papers", "zotero_items"],
        "preferred_tools": ["Zotero skill", "local Zotero library"],
        "purpose": "Reuse the researcher's curated local library, notes, citation keys, and indexed PDFs.",
    },
]

ADAPTER_IDS = {adapter["id"] for adapter in DISCOVERY_ADAPTERS}
SOURCE_ADAPTER_IDS = ADAPTER_IDS | {"manual"}

ARTIFACTS = [
    "research_brief.md",
    "search_evidence.json",
    "research_design.json",
    "paper_requirements.json",
    "experiment_matrix.json",
    "manuscript_claims.json",
    "writing_packet.md",
]

EVIDENCE_COLLECTIONS = [
    "papers",
    "code_repositories",
    "datasets",
    "baseline_candidates",
    "web_sources",
    "pubmed_records",
    "zotero_items",
    "user_sources",
]

DATASET_ROLES = ["primary", "validation", "external_test", "supplementary"]

DEFAULT_MAIN_TEX_PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=1in]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{booktabs,array,longtable,multirow}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{url}
\usepackage{caption}
\hypersetup{colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue}
\setstretch{1.12}"""

GENERIC_TEMPLATE_SECTIONS = [
    "Introduction",
    "Related Work and Design Rationale",
    "Problem Statement",
    "Method",
    "Experimental Design",
    "Planned Result Table Shells",
    "Discussion",
    "Limitations and Risk Control",
    "Reproducibility and Evidence Gate",
    "Conclusion",
]


def artifact_root(run_id: str = "") -> Path:
    if run_id:
        validate_run_id(run_id)
        directory = run_root(run_id)
        if not (directory / "run.json").exists():
            raise FileNotFoundError(f"Run not found: {run_id}")
        return directory
    return Path.cwd() / PLANNING_DIR


def artifact_path(root: Path, name: str) -> Path:
    if name not in ARTIFACTS:
        raise ValueError(f"Unknown research artifact: {name}")
    return root / name


def adapter_runs(query: str) -> list[dict[str, Any]]:
    return [
        {
            "adapter_id": adapter["id"],
            "status": "not_run",
            "query": query,
            "tool": "",
            "executed_at": "",
            "sources_found": 0,
            "notes": "",
        }
        for adapter in DISCOVERY_ADAPTERS
    ]


def search_evidence_template(query: str) -> dict[str, Any]:
    return {
        "schema_version": RESEARCH_SCHEMA_VERSION,
        "artifact": "search_evidence",
        "query": query,
        "generated_at": utc_now(),
        "discovery_layer": {
            "architecture_version": RESEARCH_SCHEMA_VERSION,
            "required_adapters": sorted(ADAPTER_IDS),
            "normalization_rule": "Every source item must include source_adapter and a URL, local path, DOI, PMID, or citation key.",
        },
        "adapter_runs": adapter_runs(query),
        "papers": [],
        "code_repositories": [],
        "datasets": [],
        "baseline_candidates": [],
        "web_sources": [],
        "pubmed_records": [],
        "zotero_items": [],
        "user_sources": [],
        "coverage": {
            "adapters_with_findings": [],
            "adapters_not_applicable": [],
            "adapters_pending": sorted(ADAPTER_IDS),
        },
        "normalization_notes": [],
    }


def research_design_template(query: str) -> dict[str, Any]:
    return {
        "schema_version": RESEARCH_SCHEMA_VERSION,
        "artifact": "research_design",
        "topic": query,
        "status": "needs_route_confirmation",
        "confirmed_route": {},
        "title_candidate": "",
        "dataset_strategy": {role: [] for role in DATASET_ROLES},
        "frontier_landscape": [],
        "domain_difficulties": [],
        "method_rationale": {
            "existing_method_problems": [],
            "design_direction": "",
        },
        "proposed_method": {
            "name": "",
            "overview": "",
            "modules": [],
            "total_objective": "",
        },
        "expected_results": [],
    }


def paper_requirements_template() -> dict[str, Any]:
    return {
        "schema_version": RESEARCH_SCHEMA_VERSION,
        "artifact": "paper_requirements",
        "source": "",
        "status": "not_started",
        "method_modules": [],
        "losses": [],
        "datasets": [],
        "metrics": [],
        "baselines": [],
        "implementation_requirements": [],
        "open_questions": [],
    }


def experiment_matrix_template() -> dict[str, Any]:
    return {
        "schema_version": RESEARCH_SCHEMA_VERSION,
        "artifact": "experiment_matrix",
        "status": "draft",
        "main_experiments": [],
        "ablations": [],
        "baseline_runs": [],
        "metrics": [],
        "server": {
            "target": "dreamweaverai-autolab",
            "requires_gate_confirmation": True,
            "notes": "",
        },
        "handoff": {
            "matrix_autolab_ready": False,
            "blockers": [],
        },
    }


def manuscript_claims_template() -> dict[str, Any]:
    return {
        "schema_version": RESEARCH_SCHEMA_VERSION,
        "artifact": "manuscript_claims",
        "claims": [],
    }


def research_brief_template(query: str) -> str:
    return "\n".join(
        [
            "# Research Brief",
            "",
            "## Research Idea",
            "",
            query or "TBD",
            "",
            "## Problem Framing",
            "",
            "- TBD",
            "",
            "## Candidate Novelty",
            "",
            "- TBD",
            "",
            "## Recommended Route",
            "",
            "- Status: needs user confirmation",
            "",
            "## Evidence Summary",
            "",
            "- See `search_evidence.json`.",
            "",
            "## Risks And Missing Evidence",
            "",
            "- TBD",
            "",
        ]
    )


def writing_packet_template() -> str:
    return "\n".join(
        [
            "# Writing Packet",
            "",
            "## Confirmed Research Argument",
            "",
            "TBD",
            "",
            "## Supported Claims For Drafting",
            "",
            "_No supported claims recorded yet._",
            "",
            "## Excluded Or Needs-Evidence Claims",
            "",
            "_No excluded claims recorded yet._",
            "",
            "## Metrics And Tables",
            "",
            "TBD",
            "",
            "## Figure Contracts",
            "",
            "TBD",
            "",
            "## Citation Needs",
            "",
            "TBD",
            "",
        ]
    )


def write_text_if_needed(path: Path, text: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\r\n") as handle:
        handle.write(text)
    return True


def write_json_if_needed(path: Path, payload: dict[str, Any], force: bool) -> bool:
    if path.exists() and not force:
        return False
    write_json(path, payload)
    return True


def latex_escape(value: Any) -> str:
    text = str(value or "")
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def clean_tex_template_preamble(template_path: str) -> str:
    if not template_path:
        return DEFAULT_MAIN_TEX_PREAMBLE
    path = Path(template_path)
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    text = path.read_text(encoding="utf-8-sig")
    stop_candidates = [index for token in (r"\title", r"\author", r"\date", r"\begin{document}") if (index := text.find(token)) >= 0]
    preamble = text[: min(stop_candidates)] if stop_candidates else text
    kept: list[str] = []
    allowed_prefixes = (
        r"\documentclass",
        r"\usepackage",
        r"\hypersetup",
        r"\setstretch",
        r"\newcommand",
        r"\renewcommand",
        r"\DeclareMathOperator",
    )
    for line in preamble.splitlines():
        stripped = line.strip()
        if not stripped:
            kept.append("")
        elif stripped.startswith(allowed_prefixes):
            kept.append(line.rstrip())
    cleaned = "\n".join(kept).strip()
    return cleaned or DEFAULT_MAIN_TEX_PREAMBLE


def load_json_if_exists(path: Path) -> dict[str, Any]:
    payload = read_json(path, None)
    return payload if isinstance(payload, dict) else {}


def collect_evidence_sources(root: Path, evidence_file: str = "") -> dict[str, Any]:
    path = Path(evidence_file) if evidence_file else root / "search_evidence.json"
    if not path.exists():
        return {}
    return load_json_if_exists(path)


def citation_key(item: dict[str, Any], prefix: str, index: int) -> str:
    existing = item.get("citation_key")
    if existing:
        return str(existing)
    title = str(item.get("title") or item.get("name") or prefix)
    year = str(item.get("year") or item.get("published_year") or "")
    base = "".join(char.lower() if char.isalnum() else "-" for char in f"{title}-{year}")
    parts = [part for part in base.split("-") if part]
    stem = "".join(parts[:4])[:32] or prefix
    return f"{stem}{index + 1}"


def evidence_citations(items: list[dict[str, Any]], prefix: str) -> tuple[str, list[str]]:
    keys: list[str] = []
    bibitems: list[str] = []
    for index, item in enumerate(items):
        key = citation_key(item, prefix, index)
        keys.append(key)
        title = latex_escape(item.get("title") or item.get("name") or f"Evidence source {index + 1}")
        venue = latex_escape(item.get("venue_or_source") or item.get("source") or item.get("publisher") or "")
        year = latex_escape(item.get("year") or item.get("published_year") or "")
        url = item.get("url") or item.get("paper_or_repo_url") or item.get("doi") or item.get("pmid") or ""
        locator = f" Available at: \\url{{{url}}}." if url else ""
        details = ", ".join(part for part in [venue, year] if part)
        suffix = f" {details}." if details else ""
        bibitems.append(f"\\bibitem{{{key}}} {title}.{suffix}{locator}")
    cite_text = ", ".join(f"\\cite{{{key}}}" for key in keys[:5])
    return cite_text, bibitems


def bullet_from_items(items: list[dict[str, Any]], empty: str) -> list[str]:
    if not items:
        return [f"    \\item {empty}"]
    lines: list[str] = []
    for item in items[:6]:
        label = latex_escape(item.get("title") or item.get("name") or item.get("url") or "Evidence item")
        reason = latex_escape(item.get("why_relevant") or item.get("task") or item.get("expected_role") or "to be reviewed")
        lines.append(f"    \\item \\textbf{{{label}}}: {reason}.")
    return lines


def main_tex_scaffold(
    *,
    title: str,
    topic: str,
    preamble: str,
    evidence: dict[str, Any],
) -> str:
    papers = [item for item in evidence.get("papers", []) if isinstance(item, dict)]
    repos = [item for item in evidence.get("code_repositories", []) if isinstance(item, dict)]
    datasets = [item for item in evidence.get("datasets", []) if isinstance(item, dict)]
    baselines = [item for item in evidence.get("baseline_candidates", []) if isinstance(item, dict)]
    paper_cites, bibitems = evidence_citations(papers, "paper")

    title_text = latex_escape(title or "Evidence-Gated Research Scaffold")
    topic_text = latex_escape(topic or evidence.get("query") or "TBD research topic")
    cite_sentence = f"Initial literature anchors include {paper_cites}." if paper_cites else "Initial literature anchors will be inserted after the Discovery Layer records verified papers."

    lines = [
        preamble,
        "",
        f"\\title{{{title_text}\\\\",
        "\\large A reproducible framework and validation protocol}",
        "\\author{Anonymous Authors}",
        f"\\date{{Draft prepared on {utc_now()[:10]}}}",
        "",
        "\\begin{document}",
        "\\maketitle",
        "",
        "\\begin{abstract}",
        f"We propose a reproducible research framework for \\textbf{{{topic_text}}}. The framework links verified literature, auditable datasets, baseline comparisons, and ablation analysis into a single manuscript structure. It defines the scientific motivation, mathematical problem setting, candidate method components, validation protocol, and reporting requirements needed to evaluate the proposed research question without relying on unsupported numerical claims.",
        "\\end{abstract}",
        "",
        f"\\noindent\\textbf{{Keywords:}} {topic_text}, machine learning, experimental protocol, evidence-gated writing, reproducibility",
        "",
        "\\section{Introduction}",
        f"The target research topic is \\textbf{{{topic_text}}}. This section should motivate the scientific or clinical problem, define the target task, and explain why existing approaches leave a meaningful gap. Background claims should cite only sources recorded in \\texttt{{search\\_evidence.json}}. " + cite_sentence,
        "",
        "The intended contribution paragraph should be completed only after route confirmation. Use it to state the proposed modeling idea, the dataset setting, the evaluation target, and the evidence required before any claim can enter the final manuscript.",
        "",
        "\\section{Related Work and Design Rationale}",
        "\\subsection{Current evidence from the Discovery Layer}",
        "The Discovery Layer should summarize peer-reviewed papers, official code repositories, datasets, and benchmark pages that justify the selected route. The following items are placeholders derived from verified evidence records:",
        "\\begin{enumerate}[leftmargin=1.3cm]",
        *bullet_from_items(papers, "Record relevant papers before completing this subsection."),
        "\\end{enumerate}",
        "",
        "\\subsection{Code, dataset, and baseline landscape}",
        "Implementation planning should be grounded in repositories, datasets, and baselines that can actually be audited:",
        "\\begin{enumerate}[leftmargin=1.3cm]",
        *bullet_from_items(repos, "Record official or high-quality repositories before implementation."),
        *bullet_from_items(datasets, "Record candidate datasets, access notes, and splits before training."),
        *bullet_from_items(baselines, "Record baseline candidates before finalizing comparison experiments."),
        "\\end{enumerate}",
        "",
        "\\subsection{Why direct transfer is insufficient}",
        "This subsection should explain why simply reusing prior methods is not enough for the selected setting. Keep the logic specific to the confirmed research route and mark any unverified novelty statement as \\texttt{needs\\_evidence}.",
        "",
        "\\section{Problem Statement}",
        "Define the data, labels, target prediction, and constraints using mathematical notation. Replace the placeholders below after the dataset and route are confirmed:",
        "\\begin{equation}",
        "\\mathcal{D}=\\left\\{\\left(x_i, y_i, m_i, s_i\\right)\\right\\}_{i=1}^{N},",
        "\\end{equation}",
        "where $x_i$ denotes the input sample, $y_i$ denotes the primary label, $m_i$ denotes optional structured supervision such as masks or annotations, and $s_i$ denotes metadata or stratification variables.",
        "",
        "\\section{Method}",
        "\\subsection{Overview}",
        "Describe the proposed framework at the level needed for implementation. Avoid performance language until experiments have run.",
        "",
        "\\subsection{Model or algorithm design}",
        "Specify modules, inputs, outputs, and data flow. Add equations only for components that are part of the confirmed route.",
        "",
        "\\subsection{Training objective}",
        "Define the loss terms and their roles. Example placeholder:",
        "\\begin{equation}",
        "\\mathcal{L}_{\\text{total}} = \\lambda_{1}\\mathcal{L}_{\\text{task}} + \\lambda_{2}\\mathcal{L}_{\\text{regularization}} + \\lambda_{3}\\mathcal{L}_{\\text{auxiliary}}.",
        "\\end{equation}",
        "",
        "\\subsection{Evidence-required claims}",
        "List claims that must be backed by experiments before writing:",
        "\\begin{enumerate}[leftmargin=1.3cm]",
        "    \\item \\texttt{needs\\_evidence}: the proposed method improves the primary metric over selected baselines.",
        "    \\item \\texttt{needs\\_evidence}: each ablation component contributes measurable value.",
        "    \\item \\texttt{needs\\_evidence}: results are robust across the planned data splits or external datasets.",
        "\\end{enumerate}",
        "",
        "\\section{Experimental Design}",
        "\\subsection{Study design}",
        "State whether the study is retrospective, prospective, simulation-based, benchmark-based, or mixed. Specify the unit of analysis and leakage-control strategy.",
        "",
        "\\subsection{Datasets}",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Dataset plan. Fill values only after access and preprocessing are verified.}",
        "\\label{tab:datasets}",
        "\\begin{tabular}{lllll}",
        "\\toprule",
        "Dataset & Role & Sample size & Labels & Access notes \\\\",
        "\\midrule",
        "TBD & Train/validation/test & TBD & TBD & TBD \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
        "\\subsection{Preprocessing and implementation preset}",
        "Document preprocessing, augmentations, seeds, optimizer, learning rate, batch size, epochs, hardware, and software versions. These fields should later be mirrored in Matrix-AutoLab contracts.",
        "",
        "\\subsection{Baselines}",
        "Define baseline families and expected comparison roles. Do not call a method state-of-the-art unless the Discovery Layer evidence supports it.",
        "",
        "\\subsection{Evaluation metrics}",
        "List primary, secondary, robustness, calibration, statistical, and runtime metrics. Tie each metric to a research question.",
        "",
        "\\subsection{Ablation plan}",
        "Each ablation should change exactly one meaningful component whenever feasible. Record the expected artifact path for every run.",
        "",
        "\\subsection{Statistical analysis}",
        "Specify paired tests, bootstrap intervals, multiple-comparison correction, subgroup analysis, and external validation criteria where applicable.",
        "",
        "\\section{Planned Result Table Shells}",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Main comparison table. Replace placeholders only with verified results.}",
        "\\label{tab:main-results}",
        "\\begin{tabular}{lcccc}",
        "\\toprule",
        "Method & Primary metric & Secondary metric & Robustness & Notes \\\\",
        "\\midrule",
        "Baseline 1 & TBD & TBD & TBD & TBD \\\\",
        "Proposed & TBD & TBD & TBD & \\texttt{needs\\_evidence} \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Ablation table shell.}",
        "\\label{tab:ablations}",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        "Variant & Changed component & Metric delta & Evidence path \\\\",
        "\\midrule",
        "Full model & -- & TBD & TBD \\\\",
        "Ablation 1 & TBD & TBD & TBD \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
        "\\section{Discussion}",
        "This section should interpret only supported claims from \\texttt{manuscript\\_claims.json}. Discuss plausible mechanisms, failure modes, domain relevance, and why the evidence does or does not support the original hypothesis.",
        "",
        "\\section{Limitations and Risk Control}",
        "List data limitations, annotation limitations, compute constraints, missing baselines, external validity risks, and negative or partial findings. Unsupported claims must remain visible here rather than being promoted into Results.",
        "",
        "\\section{Reproducibility and Evidence Gate}",
        "Before final writing, every result claim must link to metrics, logs, code paths, reports, figures, or citations. Matrix-AutoLab artifacts, \\texttt{experiment\\_matrix.json}, \\texttt{manuscript\\_claims.json}, and \\texttt{writing\\_packet.md} are the required audit trail.",
        "",
        "\\section{Conclusion}",
        "Summarize the planned contribution only at the level supported by confirmed route evidence. Replace this placeholder after experiments are complete.",
        "",
    ]
    if bibitems:
        lines.extend(["\\begin{thebibliography}{99}", *bibitems, "\\end{thebibliography}", ""])
    else:
        lines.extend(["% Bibliography will be generated after verified papers are recorded in search_evidence.json.", ""])
    lines.append("\\end{document}")
    return "\n".join(lines) + "\n"


def text_value(value: Any) -> str:
    return str(value or "").strip()


def list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def evidence_id(item: dict[str, Any]) -> str:
    for key in ("id", "source_id", "citation_key", "doi", "pmid"):
        value = text_value(item.get(key))
        if value:
            return value
    return ""


def item_evidence_ids(item: Any) -> list[str]:
    if not isinstance(item, dict):
        return []
    ids: list[str] = []
    for key in ("evidence_ids", "evidence_chain", "source_ids", "citations"):
        for value in list_value(item.get(key)):
            text = text_value(value)
            if text:
                ids.append(text)
    return ids


def design_evidence_ids(value: Any) -> list[str]:
    ids: list[str] = []
    if isinstance(value, dict):
        ids.extend(item_evidence_ids(value))
        for child in value.values():
            ids.extend(design_evidence_ids(child))
    elif isinstance(value, list):
        for child in value:
            ids.extend(design_evidence_ids(child))
    seen: set[str] = set()
    deduped: list[str] = []
    for item in ids:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def source_locator(item: dict[str, Any]) -> str:
    for key in ("url", "local_path", "doi", "pmid", "citation_key", "paper_or_repo_url"):
        value = text_value(item.get(key))
        if value:
            return value
    return ""


def indexed_sources(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for collection in EVIDENCE_COLLECTIONS:
        for item in list_value(evidence.get(collection)):
            if not isinstance(item, dict) or not source_locator(item):
                continue
            key = evidence_id(item)
            if key:
                index[key] = item
    return index


def citation_for_ids(ids: list[str], source_index: dict[str, dict[str, Any]]) -> str:
    keys = [citation_key(source_index[item], "ref", 0) for item in ids if item in source_index]
    if not keys:
        return ""
    return " ".join(f"\\cite{{{key}}}" for key in keys[:4])


def bibliography_from_design(design: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    source_index = indexed_sources(evidence)
    bibitems: list[str] = []
    seen_keys: set[str] = set()
    for source_id in design_evidence_ids(design):
        item = source_index.get(source_id)
        if item is None:
            continue
        key = citation_key(item, "ref", 0)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        title = latex_escape(item.get("title") or item.get("name") or source_id)
        venue = latex_escape(item.get("venue_or_source") or item.get("source") or item.get("publisher") or "")
        year = latex_escape(item.get("year") or item.get("published_year") or "")
        locator = source_locator(item)
        locator_text = f" Available at: \\url{{{locator}}}." if locator else ""
        details = ", ".join(part for part in [venue, year] if part)
        suffix = f" {details}." if details else ""
        bibitems.append(f"\\bibitem{{{key}}} {title}.{suffix}{locator_text}")
    return bibitems


def latex_sentence(value: Any, fallback: str = "") -> str:
    return latex_escape(text_value(value) or fallback)


def latex_item(label: str, body: str = "") -> str:
    if body:
        return f"    \\item \\textbf{{{latex_escape(label)}}}: {body}"
    return f"    \\item {latex_escape(label)}"


def latex_enumerate(items: list[str], empty: str) -> list[str]:
    lines = ["\\begin{enumerate}[leftmargin=1.3cm]"]
    if items:
        lines.extend(f"    \\item {latex_escape(item)}" for item in items)
    else:
        lines.append(f"    \\item {latex_escape(empty)}")
    lines.append("\\end{enumerate}")
    return lines


def latex_equation(formula: str) -> list[str]:
    formula = text_value(formula)
    if not formula:
        return []
    environment = "align" if "\\\\" in formula or "\n" in formula else "equation"
    return [f"\\begin{{{environment}}}", formula, f"\\end{{{environment}}}"]


def dataset_rows(strategy: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    role_labels = {
        "primary": "Primary",
        "validation": "Validation",
        "external_test": "External test",
        "supplementary": "Supplementary",
    }
    for role in DATASET_ROLES:
        datasets = list_value(strategy.get(role))
        if not datasets:
            rows.append(f"{role_labels[role]} & TBD & TBD & TBD \\\\")
            continue
        for dataset in datasets:
            if not isinstance(dataset, dict):
                continue
            name = latex_escape(dataset.get("name") or dataset.get("id") or "TBD")
            rationale = latex_escape(dataset.get("rationale") or dataset.get("role") or "TBD")
            risk = latex_escape(dataset.get("risk") or dataset.get("blocker") or "TBD")
            rows.append(f"{role_labels[role]} & {name} & {rationale} & {risk} \\\\")
    return rows


def method_modules(design: dict[str, Any]) -> list[dict[str, Any]]:
    method = dict_value(design.get("proposed_method"))
    return [item for item in list_value(method.get("modules")) if isinstance(item, dict)]


def method_name(design: dict[str, Any]) -> str:
    method = dict_value(design.get("proposed_method"))
    return text_value(method.get("name")) or "Proposed Framework"


def abstract_difficulty_text(difficulties: list[dict[str, Any]]) -> str:
    labels = [
        sentence_fragment(item.get("name") or item.get("impact"))
        for item in difficulties
        if isinstance(item, dict) and sentence_fragment(item.get("name") or item.get("impact"))
    ]
    if not labels:
        return "task-specific data limitations and external-validity constraints"
    if len(labels) == 1:
        return labels[0]
    return f"{labels[0]} and {labels[1]}"


def abstract_dataset_roles(strategy: dict[str, Any]) -> str:
    labels = {
        "primary": "primary training",
        "validation": "validation",
        "external_test": "external testing",
        "supplementary": "supplementary analysis",
    }
    roles = [labels[role] for role in DATASET_ROLES if list_value(strategy.get(role))]
    if not roles:
        return "training, validation, external testing, and supplementary analysis"
    if len(roles) == 1:
        return roles[0]
    return ", ".join(roles[:-1]) + f", and {roles[-1]}"


def sentence_fragment(value: Any, *, strip_leading_action: bool = False) -> str:
    text = " ".join(text_value(value).strip().split()).rstrip(".;:")
    if strip_leading_action:
        lowered = text.lower()
        for prefix in ("study ", "investigate ", "evaluate ", "develop "):
            if lowered.startswith(prefix):
                text = text[len(prefix) :].lstrip()
                lowered = text.lower()
                break
    if len(text) > 1 and text[0].isupper() and text[1].islower():
        text = text[0].lower() + text[1:]
    return text


def main_tex_scaffold(
    *,
    title: str,
    topic: str,
    preamble: str,
    evidence: dict[str, Any],
    design: dict[str, Any],
) -> str:
    source_index = indexed_sources(evidence)
    title_text = latex_escape(title or design.get("title_candidate") or "Evidence-Gated Research Manuscript")
    topic_text = latex_escape(topic or design.get("topic") or evidence.get("query") or "TBD research topic")
    route = dict_value(design.get("confirmed_route"))
    route_text = latex_escape(
        sentence_fragment(route.get("description") or design.get("confirmed_route"), strip_leading_action=True)
        or "the confirmed research route"
    )
    rationale = dict_value(design.get("method_rationale"))
    method = dict_value(design.get("proposed_method"))
    modules = method_modules(design)
    method_label = latex_escape(method_name(design))
    module_names = ", ".join(latex_escape(module.get("name") or f"Module {index + 1}") for index, module in enumerate(modules))
    expected = [item for item in list_value(design.get("expected_results")) if isinstance(item, dict)]
    problems = [text_value(item) for item in list_value(rationale.get("existing_method_problems")) if text_value(item)]
    design_direction = latex_escape(
        sentence_fragment(rationale.get("design_direction"), strip_leading_action=True)
        or "the design direction remains evidence-gated until experiments are complete"
    )
    difficulties = [item for item in list_value(design.get("domain_difficulties")) if isinstance(item, dict)]
    frontier = [item for item in list_value(design.get("frontier_landscape")) if isinstance(item, dict)]
    dataset_strategy = dict_value(design.get("dataset_strategy"))
    overview = latex_sentence(method.get("overview"), f"{method_label} contains evidence-gated modules: {module_names}.")
    total_objective = text_value(method.get("total_objective"))
    bibitems = bibliography_from_design(design, evidence)
    abstract_modules = "; ".join(
        latex_escape(module.get("name") or f"module {index + 1}") for index, module in enumerate(modules[:3])
    )
    if not abstract_modules:
        abstract_modules = "mathematically specified method modules"
    abstract_difficulties = latex_escape(abstract_difficulty_text(difficulties))
    abstract_roles = latex_escape(abstract_dataset_roles(dataset_strategy))
    route_clause = route_text.rstrip(".")

    lines = [
        preamble,
        "",
        f"\\title{{{title_text}\\\\",
        "\\large A reproducible mathematical framework and validation protocol}",
        "\\author{Anonymous Authors}",
        f"\\date{{Draft prepared on {utc_now()[:10]}}}",
        "",
        "\\begin{document}",
        "\\maketitle",
        "",
        "\\begin{abstract}",
        f"Existing approaches for \\textbf{{{topic_text}}} can be sensitive to {abstract_difficulties}, limiting their reliability when training and deployment data differ. We propose \\textbf{{{method_label}}}, a framework that translates these data and task constraints into explicit mathematical modules. The framework combines {abstract_modules} within a unified objective for supervision modeling, representation learning, and validation. Evaluation is organized around {abstract_roles} dataset roles, strong baseline comparisons, module-level ablations, external validation, and calibration analysis. This formulation enables controlled assessment of robustness, generalization, and reliability without introducing unsupported performance values.",
        "\\end{abstract}",
        "",
        f"\\noindent\\textbf{{Keywords:}} {topic_text}, medical artificial intelligence, robust learning, external validation, reproducibility",
        "",
        "\\section{Introduction}",
        f"\\textbf{{{topic_text}}} remains challenging when models must handle {abstract_difficulties} across development and deployment settings. This study focuses on {route_clause}, and uses this constraint to define the model components, training objective, dataset roles, and ablation endpoints.",
        "",
        "The design is organized around three questions: what current approaches fail to handle, why the data setting makes those failures important, and how the proposed modules convert that gap into testable experiments.",
        *latex_enumerate(problems, "Record current method limitations before completing the manuscript argument."),
        "",
        f"These limitations lead to the following design direction: {design_direction}.",
        "",
        "\\section{Related Work and Design Rationale}",
        "\\subsection{Frontier landscape}",
        "The following directions summarize the research frontier used to shape the design. Each direction links the method rationale to a concrete body of prior work or dataset evidence.",
        "\\begin{enumerate}[leftmargin=1.3cm]",
    ]
    for item in frontier:
        cite = citation_for_ids(item_evidence_ids(item), source_index)
        body = " ".join(part for part in [latex_escape(text_value(item.get("insight"))), cite] if part)
        lines.append(latex_item(text_value(item.get("direction")) or "Frontier direction", body))
    if not frontier:
        lines.append("    \\item Record frontier papers and journal directions before generating this section.")
    lines.extend(
        [
            "\\end{enumerate}",
            "",
            "\\subsection{Data and task difficulties}",
            "The main domain difficulties are treated as design constraints rather than background decoration. Each difficulty motivates at least one experimental endpoint or ablation.",
            "\\begin{enumerate}[leftmargin=1.3cm]",
        ]
    )
    for item in difficulties:
        cite = citation_for_ids(item_evidence_ids(item), source_index)
        body = " ".join(part for part in [latex_escape(text_value(item.get("impact"))), cite] if part)
        lines.append(latex_item(text_value(item.get("name")) or "Domain difficulty", body))
    if not difficulties:
        lines.append("    \\item Record data and task difficulties before completing this subsection.")
    lines.extend(
        [
            "\\end{enumerate}",
            "",
            "\\subsection{Why direct transfer is insufficient}",
            f"Direct reuse of existing architectures is insufficient because the target setting requires a model that can {design_direction}. The method therefore turns the literature gap into explicit modules, each with a mathematical interface, loss term, and ablation.",
            "",
            "\\section{Problem Statement}",
            "Let the training data be",
            "\\begin{equation}",
            "\\mathcal{D}=\\left\\{\\left(\\mathcal{X}_i, M_i, y_i, r_i\\right)\\right\\}_{i=1}^{N},",
            "\\end{equation}",
            "where $\\mathcal{X}_i$ denotes an image, clip, or paired-view sample, $M_i$ denotes pixel-level supervision when available, $y_i$ denotes optional diagnostic or outcome labels, and $r_i$ denotes optional clinical descriptors or metadata. The target is to learn a model that produces a structured prediction $\\hat{M}_i$ plus intermediate representations that can be audited through ablations and downstream measurements.",
            "",
            "\\section{Method}",
            "\\subsection{Overview}",
            overview,
            "",
        ]
    )
    for index, module in enumerate(modules, start=1):
        name = latex_escape(module.get("name") or f"Module {index}")
        purpose = latex_sentence(module.get("purpose") or module.get("rationale"), "This module requires a purpose statement.")
        inputs = ", ".join(latex_escape(item) for item in list_value(module.get("inputs")) if text_value(item)) or "TBD"
        outputs = ", ".join(latex_escape(item) for item in list_value(module.get("outputs")) if text_value(item)) or "TBD"
        loss_terms = ", ".join(f"${term}$" for term in list_value(module.get("loss_terms")) if text_value(term)) or "\\texttt{needs\\_evidence}"
        lines.extend(
            [
                f"\\subsection{{{name}}}",
                purpose,
                "",
                f"\\noindent\\textbf{{Inputs:}} {inputs}. \\textbf{{Outputs:}} {outputs}. \\textbf{{Loss terms:}} {loss_terms}.",
                "",
            ]
        )
        for formula in [text_value(formula) for formula in list_value(module.get("formulas")) if text_value(formula)]:
            lines.extend(latex_equation(formula))
            lines.append("")
    lines.extend(
        [
            "\\subsection{Overall objective}",
            "The full training objective combines the module-specific terms. The weights are validation-selected hyperparameters rather than claimed optimal values.",
            *latex_equation(total_objective or "\\mathcal{L}_{\\text{total}}=\\sum_m \\lambda_m \\mathcal{L}_m"),
            "",
            "\\section{Study Design and Experimental Protocol}",
            "\\subsection{Study design}",
            "The study is structured as a multi-dataset retrospective benchmark with explicit validation, external testing, and supplementary analyses. Patient-level or case-level split control should be used whenever identifiers are available.",
            "",
            "\\subsection{Candidate datasets and roles}",
            "\\begin{table}[htbp]",
            "\\centering",
            "\\caption{Datasets and their role in the experimental protocol.}",
            "\\label{tab:datasets}",
            "\\begin{tabular}{p{2.4cm}p{3.2cm}p{5.2cm}p{4.2cm}}",
            "\\toprule",
            "Role & Dataset & Rationale & Risk or access note \\\\",
            "\\midrule",
            *dataset_rows(dataset_strategy),
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
            "",
            "\\subsection{Baselines and endpoints}",
            "Baselines should include strong generic models, domain-specific methods identified during Discovery, and internal ablations that isolate each proposed module. Primary endpoints should match the task, while secondary endpoints should directly test the data difficulties identified above.",
            "",
            "\\subsection{Ablation plan}",
            "\\begin{enumerate}[leftmargin=1.3cm]",
        ]
    )
    for module in modules:
        ablation = text_value(module.get("ablation")) or f"remove {text_value(module.get('name')) or 'module'}"
        lines.append(f"    \\item {latex_escape(ablation)}.")
    lines.extend(
        [
            "\\end{enumerate}",
            "",
            "\\section{Results Reporting Plan}",
            "The following tables define the reporting structure. Replace \\texttt{TBD} only with measured values after training and evaluation.",
            "",
            "\\begin{table}[htbp]",
            "\\centering",
            "\\caption{Main comparison table.}",
            "\\label{tab:main-results}",
            "\\begin{tabular}{p{3.4cm}p{2.4cm}p{1.6cm}p{1.6cm}p{1.8cm}p{2.2cm}}",
            "\\toprule",
            "Method & Dataset & Primary metric & Secondary metric & Robustness & Notes \\\\",
            "\\midrule",
            "Best pixel baseline & Primary / external & TBD & TBD & TBD & TBD \\\\",
            f"\\textbf{{{method_label}}} & Primary / external & TBD & TBD & TBD & \\texttt{{needs\\_evidence}} \\\\",
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
            "",
            "\\begin{table}[htbp]",
            "\\centering",
            "\\caption{Ablation table.}",
            "\\label{tab:ablations}",
            "\\begin{tabular}{p{4.6cm}p{3.2cm}p{2.2cm}p{3.2cm}}",
            "\\toprule",
            "Variant & Removed or changed component & Metric delta & Evidence path \\\\",
            "\\midrule",
            f"\\textbf{{{method_label}}} & -- & TBD & TBD \\\\",
        ]
    )
    for module in modules:
        ablation = latex_escape(module.get("ablation") or f"without {module.get('name')}")
        lines.append(f"{ablation} & {latex_escape(module.get('name') or 'module')} & TBD & TBD \\\\")
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
            "",
            "\\section{Expected Contributions and Publication Value}",
            "If the experimental hypotheses are validated, the study is expected to contribute the following evidence-gated advances:",
            "\\begin{enumerate}[leftmargin=1.3cm]",
        ]
    )
    for item in expected:
        status = latex_escape(item.get("status") or "hypothesis")
        claim = latex_escape(item.get("claim") or item.get("description") or "Expected result")
        evidence_needed = latex_escape(item.get("evidence_needed") or "measured experimental evidence")
        lines.append(f"    \\item \\textbf{{{status}}}: {claim} Evidence needed: {evidence_needed}.")
    if not expected:
        lines.append("    \\item \\texttt{needs\\_evidence}: Record expected contributions before final writing.")
    lines.extend(
        [
            "\\end{enumerate}",
            "",
            "\\section{Potential Failure Modes and Risk Mitigation}",
            "The following risks should be treated as prespecified checks rather than post hoc excuses:",
            "\\begin{enumerate}[leftmargin=1.3cm]",
        ]
    )
    for item in difficulties:
        name = latex_escape(item.get("name") or "Risk")
        impact = latex_escape(item.get("impact") or item.get("risk") or "requires explicit validation")
        lines.append(f"    \\item \\textbf{{{name}}}: {impact}.")
    if not difficulties:
        lines.append("    \\item Record domain-specific risks before final submission.")
    lines.extend(
        [
            "\\end{enumerate}",
            "",
            "\\section{Discussion}",
            f"This study asks whether {method_label} can address the confirmed gap in {topic_text} through mathematically specified modules rather than through a generic architecture claim. The final Discussion should interpret measured evidence and explicitly separate supported results from hypotheses that remain unresolved.",
            "",
            "\\section{Conclusion}",
            f"This manuscript presents {method_label} as a mathematically specified, dataset-aware framework connected to explicit ablations and external validation. Final performance claims require completed experiments and validated external evidence.",
            "",
        ]
    )
    if bibitems:
        lines.extend(["\\begin{thebibliography}{99}", *bibitems, "\\end{thebibliography}", ""])
    else:
        lines.extend(["% Bibliography omitted because no referenced source in search_evidence.json has a stable locator.", ""])
    lines.append("\\end{document}")
    return "\n".join(lines) + "\n"


def cmd_list_adapters(_args: argparse.Namespace) -> int:
    print(json.dumps({"schema_version": RESEARCH_SCHEMA_VERSION, "adapters": DISCOVERY_ADAPTERS}, indent=2, ensure_ascii=False))
    return 0


def cmd_init_artifacts(args: argparse.Namespace) -> int:
    root = artifact_root(args.run_id)
    created: list[str] = []
    if write_text_if_needed(root / "research_brief.md", research_brief_template(args.query), args.force):
        created.append("research_brief.md")
    if write_json_if_needed(root / "search_evidence.json", search_evidence_template(args.query), args.force):
        created.append("search_evidence.json")
    if write_json_if_needed(root / "research_design.json", research_design_template(args.query), args.force):
        created.append("research_design.json")
    if write_json_if_needed(root / "paper_requirements.json", paper_requirements_template(), args.force):
        created.append("paper_requirements.json")
    if write_json_if_needed(root / "experiment_matrix.json", experiment_matrix_template(), args.force):
        created.append("experiment_matrix.json")
    if write_json_if_needed(root / "manuscript_claims.json", manuscript_claims_template(), args.force):
        created.append("manuscript_claims.json")
    if write_text_if_needed(root / "writing_packet.md", writing_packet_template(), args.force):
        created.append("writing_packet.md")
    print(json.dumps({"root": str(root), "created": created, "artifacts": ARTIFACTS}, indent=2, ensure_ascii=False))
    return 0


def parse_json_value(raw: str, option: str) -> dict[str, Any]:
    if raw.startswith("@"):
        text = Path(raw[1:]).read_text(encoding="utf-8")
    else:
        text = raw
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{option}: invalid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{option}: expected a JSON object")
    return parsed


def load_search_evidence(path: Path) -> dict[str, Any]:
    payload = read_json(path, None)
    if payload is None:
        raise FileNotFoundError(f"search_evidence not found: {path}")
    if not isinstance(payload, dict):
        raise ValueError(f"search_evidence must be a JSON object: {path}")
    return payload


def research_design_path(root: Path, design_file: str = "") -> Path:
    path = Path(design_file) if design_file else root / "research_design.json"
    return path if path.is_absolute() else root / path


def load_research_design(root: Path, design_file: str = "") -> dict[str, Any]:
    path = research_design_path(root, design_file)
    payload = read_json(path, None)
    if payload is None:
        raise FileNotFoundError(f"research_design.json not found: {path}")
    if not isinstance(payload, dict):
        raise ValueError(f"research_design.json must be a JSON object: {path}")
    return payload


def validate_research_design_payload(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("topic", "confirmed_route", "title_candidate", "dataset_strategy", "frontier_landscape", "domain_difficulties", "method_rationale", "proposed_method", "expected_results"):
        if field not in payload:
            errors.append(f"missing field: {field}")

    if not text_value(payload.get("topic")):
        errors.append("topic is required")
    if not text_value(payload.get("title_candidate")):
        errors.append("title_candidate is required")

    route = payload.get("confirmed_route")
    if isinstance(route, dict):
        if not (text_value(route.get("description")) or text_value(route.get("route_id"))):
            errors.append("confirmed_route must include route_id or description")
        if route.get("user_confirmed") is not True:
            errors.append("confirmed_route.user_confirmed must be true")
    elif not text_value(route):
        errors.append("confirmed_route is required")
    else:
        errors.append("confirmed_route must be an object with user_confirmed=true")

    dataset_strategy = dict_value(payload.get("dataset_strategy"))
    missing_roles = [role for role in DATASET_ROLES if role not in dataset_strategy]
    if missing_roles:
        errors.append(f"dataset_strategy missing roles: {missing_roles}")
    for role in DATASET_ROLES:
        if role in dataset_strategy and not isinstance(dataset_strategy.get(role), list):
            errors.append(f"dataset_strategy.{role} must be a list")
    if not list_value(dataset_strategy.get("primary")):
        errors.append("dataset_strategy.primary requires at least one dataset")
    if not list_value(dataset_strategy.get("external_test")):
        errors.append("dataset_strategy.external_test requires at least one dataset")

    if not list_value(payload.get("frontier_landscape")):
        errors.append("frontier_landscape requires at least one frontier direction")
    if not list_value(payload.get("domain_difficulties")):
        errors.append("domain_difficulties requires at least one difficulty")

    rationale = dict_value(payload.get("method_rationale"))
    if not list_value(rationale.get("existing_method_problems")):
        errors.append("method_rationale.existing_method_problems requires at least one problem")
    if not text_value(rationale.get("design_direction")):
        errors.append("method_rationale.design_direction is required")

    method = dict_value(payload.get("proposed_method"))
    if not text_value(method.get("name")):
        errors.append("proposed_method.name is required")
    modules = [item for item in list_value(method.get("modules")) if isinstance(item, dict)]
    if len(modules) < 3:
        errors.append("proposed_method requires at least 3 method modules")
    for index, module in enumerate(modules):
        label = text_value(module.get("name")) or f"module[{index}]"
        if not text_value(module.get("name")):
            errors.append(f"{label} missing name")
        if not text_value(module.get("purpose") or module.get("rationale")):
            errors.append(f"{label} missing purpose")
        if not list_value(module.get("formulas")):
            errors.append(f"{label} missing formulas")
        if not list_value(module.get("inputs")):
            errors.append(f"{label} missing inputs")
        if not list_value(module.get("outputs")):
            errors.append(f"{label} missing outputs")
        if not list_value(module.get("loss_terms")):
            errors.append(f"{label} missing loss_terms")
        if not text_value(module.get("ablation")):
            errors.append(f"{label} missing ablation")
    if not text_value(method.get("total_objective")):
        errors.append("proposed_method.total_objective is required")
    elif "\\mathcal{L}" not in text_value(method.get("total_objective")):
        warnings.append("proposed_method.total_objective does not look like a LaTeX loss formula")

    expected = list_value(payload.get("expected_results"))
    if not expected:
        errors.append("expected_results requires at least one planned hypothesis")
    allowed_status = {"hypothesis", "expected", "planned", "needs_evidence"}
    for index, item in enumerate(expected):
        if not isinstance(item, dict):
            errors.append(f"expected_results[{index}] must be an object")
            continue
        status = text_value(item.get("status")) or "hypothesis"
        if status not in allowed_status:
            errors.append(f"expected_results[{index}] status must be one of {sorted(allowed_status)}")
        if any(key in item for key in ("value", "measured_value", "numeric_result")):
            errors.append(f"expected_results[{index}] must not include measured result fields")
    return errors, warnings


def cmd_validate_research_design(args: argparse.Namespace) -> int:
    root = artifact_root(args.run_id)
    path = research_design_path(root, args.design_file)
    design = load_research_design(root, args.design_file)
    errors, warnings = validate_research_design_payload(design)
    result = {"ok": not errors, "path": str(path), "errors": errors, "warnings": warnings}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 3


def update_coverage(payload: dict[str, Any]) -> None:
    runs = payload.get("adapter_runs") or []
    findings = sorted(
        run.get("adapter_id")
        for run in runs
        if run.get("adapter_id") in ADAPTER_IDS and run.get("status") in {"findings", "manual"} and run.get("sources_found", 0) > 0
    )
    not_applicable = sorted(run.get("adapter_id") for run in runs if run.get("adapter_id") in ADAPTER_IDS and run.get("status") == "not_applicable")
    pending = sorted(run.get("adapter_id") for run in runs if run.get("adapter_id") in ADAPTER_IDS and run.get("status") == "not_run")
    payload["coverage"] = {
        "adapters_with_findings": findings,
        "adapters_not_applicable": not_applicable,
        "adapters_pending": pending,
    }


def cmd_record_source(args: argparse.Namespace) -> int:
    if args.adapter not in SOURCE_ADAPTER_IDS:
        raise ValueError(f"Unknown adapter: {args.adapter}")
    if args.target not in EVIDENCE_COLLECTIONS:
        raise ValueError(f"Unknown evidence target: {args.target}")
    if args.status not in ADAPTER_STATUSES:
        raise ValueError(f"Unknown adapter status: {args.status}")

    root = artifact_root(args.run_id)
    path = root / "search_evidence.json"
    payload = load_search_evidence(path)
    item = parse_json_value(args.source, "--source-json")
    item.setdefault("source_adapter", args.adapter)
    item.setdefault("recorded_at", utc_now())
    payload.setdefault(args.target, []).append(item)

    if args.adapter != "manual":
        runs = payload.setdefault("adapter_runs", adapter_runs(payload.get("query", "")))
        run = next((entry for entry in runs if entry.get("adapter_id") == args.adapter), None)
        if run is None:
            run = {"adapter_id": args.adapter}
            runs.append(run)
        run.update(
            {
                "status": args.status,
                "query": args.query or payload.get("query", ""),
                "tool": args.tool,
                "executed_at": utc_now(),
                "sources_found": int(run.get("sources_found") or 0) + 1,
                "notes": args.notes,
            }
        )
    payload["generated_at"] = utc_now()
    update_coverage(payload)
    write_json(path, payload)
    print(json.dumps({"recorded": True, "path": str(path), "target": args.target, "adapter": args.adapter}, ensure_ascii=False))
    return 0


def validate_search_payload(payload: dict[str, Any], strict: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for field in ["schema_version", "query", "adapter_runs", *EVIDENCE_COLLECTIONS]:
        if field not in payload:
            errors.append(f"missing field: {field}")

    runs = payload.get("adapter_runs") or []
    if not isinstance(runs, list):
        errors.append("adapter_runs must be a list")
        runs = []
    seen = {run.get("adapter_id") for run in runs if isinstance(run, dict)}
    missing_adapters = sorted(ADAPTER_IDS - seen)
    if missing_adapters:
        errors.append(f"adapter_runs missing adapters: {missing_adapters}")
    for run in runs:
        if not isinstance(run, dict):
            errors.append("adapter_runs item must be an object")
            continue
        adapter_id = run.get("adapter_id")
        status = run.get("status")
        if adapter_id not in ADAPTER_IDS:
            errors.append(f"unknown adapter_id: {adapter_id}")
        if status not in ADAPTER_STATUSES:
            errors.append(f"invalid status for {adapter_id}: {status}")
        if strict and status == "not_run":
            errors.append(f"strict mode: adapter not run: {adapter_id}")
        if status == "error" and not run.get("notes"):
            warnings.append(f"adapter error without notes: {adapter_id}")

    total_sources = 0
    for collection in EVIDENCE_COLLECTIONS:
        items = payload.get(collection) or []
        if not isinstance(items, list):
            errors.append(f"{collection} must be a list")
            continue
        total_sources += len(items)
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{collection}[{index}] must be an object")
                continue
            adapter_id = item.get("source_adapter")
            if adapter_id not in SOURCE_ADAPTER_IDS:
                errors.append(f"{collection}[{index}] has invalid source_adapter: {adapter_id}")
            if not any(item.get(key) for key in ("url", "local_path", "doi", "pmid", "citation_key", "paper_or_repo_url")):
                warnings.append(f"{collection}[{index}] lacks url/local_path/doi/pmid/citation_key")
    if total_sources == 0:
        warnings.append("no evidence sources recorded yet")
        if strict:
            errors.append("strict mode: no evidence sources recorded")
    return errors, warnings


def cmd_validate_search(args: argparse.Namespace) -> int:
    root = artifact_root(args.run_id)
    path = root / "search_evidence.json"
    payload = load_search_evidence(path)
    update_coverage(payload)
    write_json(path, payload)
    errors, warnings = validate_search_payload(payload, args.strict)
    result = {
        "ok": not errors,
        "path": str(path),
        "errors": errors,
        "warnings": warnings,
        "coverage": payload.get("coverage", {}),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 3


def read_claims(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path, None)
    if payload is None:
        raise FileNotFoundError(f"manuscript_claims not found: {path}")
    claims = payload.get("claims")
    if not isinstance(claims, list):
        raise ValueError("manuscript_claims.claims must be a list")
    return claims


def markdown_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start < 0:
        return ""
    next_start = text.find("\n## ", start + len(marker))
    if next_start < 0:
        return text[start:]
    return text[start:next_start]


def validate_claims(claims: list[dict[str, Any]], packet: str = "") -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    supported_section = markdown_section(packet, "Supported Claims For Drafting") if packet else ""
    allowed_status = {"supported", "partial", "needs_evidence"}
    for index, item in enumerate(claims):
        if not isinstance(item, dict):
            errors.append(f"claims[{index}] must be an object")
            continue
        claim = str(item.get("claim", "")).strip()
        status = item.get("status")
        evidence = item.get("evidence") or []
        if not claim:
            errors.append(f"claims[{index}] missing claim text")
        if status not in allowed_status:
            errors.append(f"claims[{index}] invalid status: {status}")
        if status == "supported" and not evidence:
            errors.append(f"claims[{index}] supported claim has no evidence")
        if status == "partial" and not evidence:
            warnings.append(f"claims[{index}] partial claim has no evidence")
        if status != "supported" and packet and claim and claim in supported_section:
            errors.append(f"unsupported claim appears in drafting section: {claim}")
    return errors, warnings


def cmd_validate_claims(args: argparse.Namespace) -> int:
    root = artifact_root(args.run_id)
    claims_path = root / "manuscript_claims.json"
    claims = read_claims(claims_path)
    packet = ""
    packet_path = root / "writing_packet.md"
    if packet_path.exists():
        packet = packet_path.read_text(encoding="utf-8")
    errors, warnings = validate_claims(claims, packet)
    result = {"ok": not errors, "path": str(claims_path), "errors": errors, "warnings": warnings}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 3


def render_claim_line(item: dict[str, Any]) -> str:
    evidence = item.get("evidence") or []
    target = item.get("writing_target", "")
    evidence_text = ", ".join(str(entry) for entry in evidence) if evidence else "missing evidence"
    suffix = f" Target: {target}." if target else ""
    return f"- {item.get('claim', '')} Evidence: {evidence_text}.{suffix}"


def cmd_build_packet(args: argparse.Namespace) -> int:
    root = artifact_root(args.run_id)
    claims = read_claims(root / "manuscript_claims.json")
    errors, warnings = validate_claims(claims)
    if errors:
        print(json.dumps({"ok": False, "errors": errors, "warnings": warnings}, indent=2, ensure_ascii=False), file=sys.stderr)
        return 3

    supported = [item for item in claims if item.get("status") == "supported"]
    excluded = [item for item in claims if item.get("status") != "supported"]
    lines = [
        "# Writing Packet",
        "",
        "## Confirmed Research Argument",
        "",
        args.argument or "TBD",
        "",
        "## Supported Claims For Drafting",
        "",
    ]
    lines.extend(render_claim_line(item) for item in supported)
    if not supported:
        lines.append("_No supported claims recorded yet._")
    lines.extend(["", "## Excluded Or Needs-Evidence Claims", ""])
    lines.extend(render_claim_line(item) for item in excluded)
    if not excluded:
        lines.append("_No excluded claims recorded yet._")
    lines.extend(
        [
            "",
            "## Metrics And Tables",
            "",
            "Use only metrics recorded in experiment reports, result CSV files, or phase reports.",
            "",
            "## Figure Contracts",
            "",
            "Each figure must name the source CSV, metric, baseline, and claim it supports.",
            "",
            "## Citation Needs",
            "",
            "Use search_evidence.json and Zotero/PubMed/Semantic Scholar records for background citations.",
            "",
            "## Chinese Notes",
            "",
            "正式英文写作只能使用 supported claims；partial 和 needs_evidence 只能作为待补证据或局限性说明。",
            "",
        ]
    )
    packet_path = root / "writing_packet.md"
    write_text_if_needed(packet_path, "\n".join(lines), True)
    errors, warnings = validate_claims(claims, packet_path.read_text(encoding="utf-8"))
    result = {"ok": not errors, "path": str(packet_path), "errors": errors, "warnings": warnings}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 3


def cmd_build_main_tex(args: argparse.Namespace) -> int:
    root = artifact_root(args.run_id)
    output_path = Path(args.output) if args.output else root / "main.tex"
    if not output_path.is_absolute():
        output_path = root / output_path
    if output_path.exists() and not args.force:
        raise ValueError(f"Output already exists: {output_path}. Re-run with --force to replace it.")

    design = load_research_design(root, args.design_file)
    errors, warnings = validate_research_design_payload(design)
    if errors:
        result = {
            "ok": False,
            "path": str(research_design_path(root, args.design_file)),
            "errors": errors,
            "warnings": warnings,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stderr)
        return 3

    evidence = collect_evidence_sources(root, args.evidence_file)
    preamble = clean_tex_template_preamble(args.template)
    topic = args.topic or design.get("topic") or evidence.get("query") or ""
    if args.title:
        title = args.title
    elif design.get("title_candidate"):
        title = str(design["title_candidate"])
    elif topic:
        title = f"{topic}: A Reproducible Research Framework"
    else:
        title = "Evidence-Aware Research Framework"
    scaffold = main_tex_scaffold(title=title, topic=topic, preamble=preamble, evidence=evidence, design=design)
    write_text_if_needed(output_path, scaffold, True)
    result = {
        "ok": True,
        "path": str(output_path),
        "design_file": str(research_design_path(root, args.design_file)),
        "template_used": args.template,
        "template_content_reused": False,
        "sections": [
            "Abstract",
            "Introduction",
            "Related Work and Design Rationale",
            "Problem Statement",
            "Method",
            "Study Design and Experimental Protocol",
            "Results Reporting Plan",
            "Expected Contributions and Publication Value",
            "Potential Failure Modes and Risk Mitigation",
            "Discussion",
            "Conclusion",
            "Bibliography",
        ],
        "method_modules": len(method_modules(design)),
        "paper_sources_used": len(evidence.get("papers", []) or []),
        "warnings": warnings,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Matrix Research Autopilot protocol utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    list_adapters = sub.add_parser("list-adapters")
    list_adapters.set_defaults(func=cmd_list_adapters)

    init = sub.add_parser("init-artifacts")
    init.add_argument("--run-id", default="")
    init.add_argument("--query", default="")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init_artifacts)

    record = sub.add_parser("record-source")
    record.add_argument("--run-id", default="")
    record.add_argument("--adapter", required=True, choices=sorted(SOURCE_ADAPTER_IDS))
    record.add_argument("--target", required=True, choices=EVIDENCE_COLLECTIONS)
    record.add_argument("--source-json", dest="source", required=True)
    record.add_argument("--status", default="findings", choices=sorted(ADAPTER_STATUSES))
    record.add_argument("--query", default="")
    record.add_argument("--tool", default="")
    record.add_argument("--notes", default="")
    record.set_defaults(func=cmd_record_source)

    validate_search = sub.add_parser("validate-search-evidence")
    validate_search.add_argument("--run-id", default="")
    validate_search.add_argument("--strict", action="store_true")
    validate_search.set_defaults(func=cmd_validate_search)

    validate_design = sub.add_parser("validate-research-design")
    validate_design.add_argument("--run-id", default="")
    validate_design.add_argument("--design-file", default="")
    validate_design.set_defaults(func=cmd_validate_research_design)

    validate_claims_cmd = sub.add_parser("validate-claims")
    validate_claims_cmd.add_argument("--run-id", default="")
    validate_claims_cmd.set_defaults(func=cmd_validate_claims)

    packet = sub.add_parser("build-writing-packet")
    packet.add_argument("--run-id", default="")
    packet.add_argument("--argument", default="")
    packet.set_defaults(func=cmd_build_packet)

    main_tex = sub.add_parser("build-main-tex")
    main_tex.add_argument("--run-id", default="")
    main_tex.add_argument("--template", default="", help="Optional main.tex style template; only structure/preamble are used")
    main_tex.add_argument("--evidence-file", default="", help="Optional search_evidence.json path")
    main_tex.add_argument("--design-file", default="", help="Optional research_design.json path")
    main_tex.add_argument("--output", default="", help="Output path. Defaults to artifact root/main.tex")
    main_tex.add_argument("--title", default="")
    main_tex.add_argument("--topic", default="")
    main_tex.add_argument("--force", action="store_true")
    main_tex.set_defaults(func=cmd_build_main_tex)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
