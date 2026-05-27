# Research Discovery Layer Reference

Use this reference when `matrix-research-autopilot` needs to choose discovery tools, normalize evidence, or explain why a source was included.

## Adapter Contract

Every adapter writes into `search_evidence.json`. Keep all six adapter entries in `adapter_runs`; use `not_applicable` for irrelevant sources rather than deleting the adapter.

Each evidence item must include:

- `source_adapter`: one of `web`, `github`, `huggingface`, `scholarly`, `pubmed`, `zotero`, or `manual`
- at least one locator: `url`, `paper_or_repo_url`, `doi`, `pmid`, `citation_key`, or `local_path`
- `why_relevant`: short reason the source matters to route selection, implementation, dataset choice, or baseline selection

Recommended status values:

- `not_run`: adapter has not been attempted yet
- `findings`: adapter found one or more useful sources
- `no_findings`: adapter was attempted but found no useful sources
- `not_applicable`: adapter is irrelevant to the domain or user constraints
- `manual`: source was supplied by the user or manually curated
- `error`: adapter failed; explain the failure in `notes`

## Adapter Selection

| Adapter | Use For | Preferred Tooling |
|---|---|---|
| `web` | Official project pages, benchmark pages, docs, active announcements, broad current search | Codex web search, browser |
| `github` | Code repos, examples, baselines, training scripts, license/activity checks | GitHub MCP, GitHub app, GitHub search |
| `huggingface` | HF papers, datasets, models, Spaces, dataset/model cards | Hugging Face MCP, HF Hub search |
| `scholarly` | arXiv papers, Semantic Scholar metadata, citation graph, related work | arXiv MCP, Semantic Scholar MCP, official paper pages |
| `pubmed` | Biomedical, clinical, medical AI, biology, health data evidence | `pubmed-search` skill, PubMed |
| `zotero` | User's curated papers, PDFs, notes, citation keys, prior reading | Zotero skill, local Zotero library |

## Normalization Targets

Use these targets with `scripts/research_autopilot.py record-source`:

- `papers`: papers from scholarly, PubMed, HF, Zotero, or web sources
- `code_repositories`: GitHub or official code repositories
- `datasets`: dataset pages, dataset cards, benchmark datasets, clinical datasets
- `baseline_candidates`: methods or repos that should be compared against
- `web_sources`: web pages that are not better represented as paper/code/dataset records
- `pubmed_records`: PubMed-specific records with PMID and biomedical context
- `zotero_items`: Zotero-specific records with local library key, citation key, or note path
- `user_sources`: sources supplied directly by the user

## ml-intern Extraction Policy

Do not use `ml-intern` as the orchestrator. If it is useful, treat it as a source of implementation patterns:

- map its paper search behavior to the `scholarly` or `huggingface` adapters
- map its dataset inspection behavior to the `huggingface` adapter
- map its example-first GitHub search behavior to the `github` adapter

The adapter output must still be normalized into `search_evidence.json` and pass `validate-search-evidence`.

## Literature Supplementation For `main.tex`

When generating a new `main.tex`, use verified papers and reporting guidelines only to fill generic scholarly scaffolding:

- background anchors in Introduction and Related Work
- method families and baseline families
- dataset and validation expectations
- reporting checklist reminders, especially for medical AI
- limitation and reproducibility prompts

Never copy domain content from a user-provided template. If the supplied template is about another disease, modality, dataset, or method, keep only its LaTeX style, generic section rhythm, table-shell structure, and evidence-gated wording style.

For medical AI or imaging AI drafts, check whether the topic should account for CLAIM, TRIPOD+AI, CONSORT-AI, or SPIRIT-AI style reporting requirements. Record those guideline papers or pages in `search_evidence.json` before using them as citation anchors.
