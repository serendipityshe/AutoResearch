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
        "\\large A manuscript-ready study design and evidence-gated experimental protocol}",
        "\\author{Anonymous Authors}",
        f"\\date{{Draft prepared on {utc_now()[:10]}}}",
        "",
        "\\begin{document}",
        "\\maketitle",
        "",
        "\\begin{abstract}",
        f"This scaffold describes a planned study on \\textbf{{{topic_text}}}. It follows the supplied main.tex file as a structural and formatting template only; no domain-specific claims, datasets, methods, or results from that template are reused. The manuscript is intentionally evidence-gated: background claims must be tied to verified literature sources, and experimental claims must remain placeholders until Matrix-AutoLab records metrics, reports, logs, and figures. The current draft therefore provides a study rationale, method placeholders, experiment protocol, baseline plan, ablation matrix, result-table shells, limitations, and reproducibility requirements rather than fabricated numerical results.",
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

    evidence = collect_evidence_sources(root, args.evidence_file)
    preamble = clean_tex_template_preamble(args.template)
    topic = args.topic or evidence.get("query") or ""
    if args.title:
        title = args.title
    elif topic:
        title = f"{topic}: Evidence-Gated Study Design"
    else:
        title = "Evidence-Gated Study Design"
    scaffold = main_tex_scaffold(title=title, topic=topic, preamble=preamble, evidence=evidence)
    write_text_if_needed(output_path, scaffold, True)
    result = {
        "ok": True,
        "path": str(output_path),
        "template_used": args.template,
        "template_content_reused": False,
        "sections": GENERIC_TEMPLATE_SECTIONS,
        "paper_sources_used": len(evidence.get("papers", []) or []),
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
