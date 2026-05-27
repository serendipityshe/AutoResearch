# Matrix Research Autopilot Architecture

## Summary

Matrix Research Autopilot extends Matrix-AutoLab from a `main.tex` paper-reproduction plugin into an idea-to-paper workflow for graduate students and researchers.

The first version remains a Codex plugin skill workflow, but its control plane is now adapter-based and protocol-checked:

```text
research idea
-> Research Discovery Layer
-> research_brief.md and search_evidence.json
-> route confirmation
-> main.tex or experiment scaffold
-> Matrix-AutoLab execution layer
-> experiment reports and metrics
-> manuscript_claims.json
-> Nature-Skills writing layer
```

`ml-intern` is no longer treated as the integration root. It may provide extractable implementation ideas, but the product architecture is `matrix-research-autopilot` plus adapter protocols, Matrix-AutoLab execution, and Nature-Skills writing.

## Layered Architecture

```text
matrix-research-autopilot
├─ Research Discovery Layer
│  ├─ Web search adapter
│  ├─ GitHub adapter
│  ├─ Hugging Face adapter
│  ├─ arXiv / Semantic Scholar adapter
│  ├─ PubMed adapter
│  └─ Zotero adapter
├─ Matrix-AutoLab execution layer
└─ Nature-Skills writing layer
```

## Component Roles

- `matrix-research-autopilot`: idea-to-paper controller. It creates research briefs, normalizes search evidence, selects routes, prepares experiment matrices, validates claims, and builds writing packets.
- Research Discovery Layer: a set of adapters that can use available tools, MCP servers, skills, manual sources, or future agent modules while writing the same `search_evidence.json` contract.
- Matrix-AutoLab execution layer: gated execution for `paperbanana`, `autolab`, and `autobaseline`.
- Nature-Skills writing layer: evidence-grounded writing, figures, citations, data statements, and Chinese revision notes.

## Research Discovery Adapters

| Adapter | Responsibility | Typical Tools |
|---|---|---|
| `web` | current project pages, benchmark pages, official docs, broad current search | Codex web search, browser |
| `github` | official repos, baseline repos, examples, training entrypoints, licenses, activity | GitHub MCP, GitHub app, GitHub search |
| `huggingface` | HF papers, datasets, models, Spaces, dataset cards, model cards | Hugging Face MCP, HF Hub search |
| `scholarly` | arXiv/Semantic Scholar paper discovery, citation graph, related work | arXiv MCP, Semantic Scholar MCP |
| `pubmed` | biomedical and clinical literature | `pubmed-search` skill, PubMed |
| `zotero` | local curated library, notes, PDFs, citation keys | Zotero skill |

The adapters are logical contracts, not mandatory installed runtimes. If a tool is unavailable, the agent records the adapter as `not_run`, `not_applicable`, `manual`, or `error` with notes.

## Protocol Artifacts

Use `.autolab/runs/<run_id>/` when a run exists. Before local recording is initialized, use `research_autopilot/`.

| Artifact | Purpose |
|---|---|
| `research_brief.md` | Chinese research framing, recommended route, novelty hypotheses, and risks. |
| `search_evidence.json` | Adapter-normalized papers, code repos, datasets, baselines, PubMed records, Zotero items, web sources, and user sources. |
| `paper_requirements.json` | Method modules, losses, datasets, metrics, baselines, and implementation requirements from `main.tex`, a selected paper, or scaffold. |
| `experiment_matrix.json` | Main experiment, ablations, baselines, metrics, budgets, server target, and Matrix-AutoLab handoff status. |
| `manuscript_claims.json` | Claim-to-evidence map with `supported`, `partial`, or `needs_evidence` status. |
| `writing_packet.md` | Evidence-grounded input for Nature-Skills writing, figures, citations, and data statements. |

## Deterministic Utilities

`scripts/research_autopilot.py` provides the protocol control plane:

```bash
python scripts/research_autopilot.py list-adapters
python scripts/research_autopilot.py init-artifacts --query "<research idea>"
python scripts/research_autopilot.py record-source --adapter github --target code_repositories --source-json '{"name":"repo","url":"https://github.com/org/repo"}'
python scripts/research_autopilot.py build-main-tex --template "<template-main.tex>" --topic "<research topic>"
python scripts/research_autopilot.py validate-search-evidence
python scripts/research_autopilot.py build-writing-packet --argument "<confirmed argument>"
python scripts/research_autopilot.py validate-claims
```

`autolab_run.py` now accepts `--kind idea_to_paper` so the research workflow can create a first-class run before handing work to execution skills.

## Workflow

1. User provides a research idea, topic, dataset, or hypothesis.
2. `matrix-research-autopilot` initializes protocol artifacts.
3. The Research Discovery Layer runs applicable adapters.
4. Search outputs are normalized into `search_evidence.json`.
5. `validate-search-evidence` checks adapter coverage, evidence shape, and locators.
6. The skill writes `research_brief.md` and recommends 2-3 routes.
7. User confirms one research route.
8. If `main.tex` exists, the skill extracts `paper_requirements.json`; otherwise it creates an experiment-first manuscript scaffold with unverified claims marked as `needs_evidence`.
9. It prepares `experiment_matrix.json` and hands off to Matrix-AutoLab.
10. Matrix-AutoLab runs `paperbanana`, `autolab`, and `autobaseline` with existing gates.
11. After experiment reports and metrics exist, `matrix-research-autopilot` creates `manuscript_claims.json`.
12. `build-writing-packet` puts only supported claims into the drafting section.
13. Nature-Skills produces Chinese explanation plus English Results, Discussion, figure captions, claim-evidence maps, and publication-quality figure contracts.

## Evidence-Gated Writing

Research search results justify background and route selection. Experimental claims require experiment evidence.

Each claim must identify:

- claim text
- evidence files or citations
- evidence type
- support status
- writing target

Claims without evidence remain `needs_evidence` and must not be presented as finished manuscript prose. `validate-claims` fails if a non-supported claim appears in the writing packet's `Supported Claims For Drafting` section.

## MVP Acceptance Criteria

- The plugin exposes `matrix-research-autopilot` as a skill entry.
- The Discovery Layer is explicitly represented by six adapters.
- `scripts/research_autopilot.py list-adapters` prints all adapters.
- `init-artifacts` creates all six protocol artifacts.
- `validate-search-evidence` verifies adapter entries and source locators.
- `build-writing-packet` excludes unsupported claims from the drafting section.
- README and plugin prompts make the idea-to-paper path discoverable for Chinese research users.
- `build-main-tex` can use a user-supplied `main.tex` only as a structural/style template while excluding that template's scientific content.
- `npm run doctor` succeeds.
- `npm run pack:dry-run` includes the skill, reference file, docs, and protocol utility script.

## Defaults

- First version is a Codex plugin workflow.
- Dashboard remains read-only and optional.
- Discovery is protocol-based rather than coupled to a single search agent.
- `ml-intern` is optional reference material, not the root architecture.
- Writing output defaults to Chinese reasoning notes plus English manuscript sections.
- DreamweaverAI AutoLab remains responsible for server execution and gated experiment progression.
