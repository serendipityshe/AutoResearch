---
name: matrix-research-autopilot
description: Use when the user starts from a research idea, topic, hypothesis, dataset, or rough direction and wants literature/code/data/baseline discovery, experiment planning, Matrix-AutoLab execution, or evidence-grounded manuscript writing.
---

# Matrix Research Autopilot

Matrix Research Autopilot is the idea-to-paper entry point for graduate students and researchers. It turns a rough idea into auditable research evidence, a confirmed experiment plan, a Matrix-AutoLab run, and Nature-style writing inputs.

## Architecture

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
└─ Built-in Nature Skills writing layer
```

The Discovery Layer is adapter-based. Do not make `ml-intern` the architecture root or a hard runtime dependency. If useful, extract only specific `ml-intern` ideas behind adapters, such as paper operations or example-first GitHub search. The source of truth remains the protocol artifacts and validators in this plugin.

## When To Use

Use this skill when the user:

- starts with a research idea, topic, hypothesis, dataset, or vague direction
- asks what research direction is worth doing
- wants literature, GitHub, Hugging Face, dataset, or baseline discovery before experiments
- wants a full workflow from idea to experiments and paper writing
- needs Chinese guidance plus English manuscript outputs
- has no `main.tex` yet but wants an experiment-ready manuscript scaffold

If the user already has `main.tex` and only wants implementation, training, ablations, or baselines, delegate directly to `matrix-autolab`.

## Protocol Commands

Use `scripts/research_autopilot.py` to reduce prompt drift:

```bash
python scripts/research_autopilot.py list-adapters
python scripts/research_autopilot.py init-artifacts --query "<research idea>"
python scripts/research_autopilot.py validate-search-evidence
python scripts/research_autopilot.py record-source --adapter github --target code_repositories --source-json '{"name":"repo","url":"https://github.com/org/repo"}'
python scripts/research_autopilot.py build-main-tex --template "<path/to/template/main.tex>" --topic "<research topic>"
python scripts/research_autopilot.py build-writing-packet --argument "<confirmed argument>"
python scripts/research_autopilot.py validate-claims
```

When an `.autolab` run exists, pass `--run-id <run_id>` so artifacts live in `.autolab/runs/<run_id>/`. Otherwise use the temporary `research_autopilot/` planning folder.

## Protocol Artifacts

Create or update these artifacts under `.autolab/runs/<run_id>/` when a run exists. If `.autolab/` is not initialized yet, create them in `research_autopilot/`.

| Artifact | Purpose |
|---|---|
| `research_brief.md` | Human-readable research direction, problem framing, candidate novelty, risks, and recommended route. |
| `search_evidence.json` | Structured adapter evidence from papers, GitHub repos, datasets, baselines, PubMed, Zotero, HF, and web sources. |
| `paper_requirements.json` | Method modules, losses, datasets, metrics, baselines, and implementation requirements from `main.tex`, a selected paper, or a scaffold. |
| `experiment_matrix.json` | Main experiment, ablations, baselines, metrics, budgets, server target, and Matrix-AutoLab handoff status. |
| `manuscript_claims.json` | Claim-to-evidence map. Only supported claims may enter final writing. |
| `writing_packet.md` | Evidence-grounded input for built-in Nature Skills writing, figures, captions, citations, data statements, and Chinese reviewer notes. |

## Research Discovery Layer

Read `references/discovery-layer.md` when choosing tools or normalizing search results. Each source item recorded in `search_evidence.json` must include `source_adapter` and at least one stable locator such as `url`, `doi`, `pmid`, `citation_key`, `local_path`, or `paper_or_repo_url`.

Adapter roles:

- `web`: current project pages, benchmark pages, official docs, release pages, and broad web evidence
- `github`: official repos, baseline repos, training entrypoints, licenses, activity, and examples
- `huggingface`: HF papers, datasets, models, Spaces, dataset cards, and model cards
- `scholarly`: arXiv and Semantic Scholar papers, citation graphs, related work, and method lineage
- `pubmed`: biomedical and clinical literature when the idea is medical, biological, or healthcare related
- `zotero`: the user's local curated library, notes, PDFs, citation keys, and prior reading

`search_evidence.json` should keep all six `adapter_runs` entries. Mark irrelevant adapters as `not_applicable`, not by deleting them.

## Default Pipeline

```text
research idea
-> initialize artifacts and Discovery Layer adapter runs
-> search papers/code/data/baselines with adapters
-> research_brief.md and search_evidence.json
-> user confirms route
-> main.tex or experiment-first manuscript scaffold
-> paper_requirements.json and experiment_matrix.json
-> Matrix-AutoLab execution layer
-> manuscript_claims.json
-> writing_packet.md
-> built-in Nature Skills writing layer
```

## Phase 1: Research Discovery

1. Restate the user's research idea in one sentence.
2. Run or coordinate the six Discovery Layer adapters that fit the domain.
3. Prefer primary sources: papers, official repos, official datasets, benchmark pages, project docs, PubMed records, and the user's Zotero library.
4. Record every source into `search_evidence.json`; use `record-source` when possible.
5. Run `validate-search-evidence`. Use `--strict` before route confirmation when all relevant adapters have been attempted.
6. Write `research_brief.md` in Chinese with English technical names where useful.

Search results are evidence for background and route selection. They are not proof of experimental claims.

## Phase 2: Route Selection

Present 2-3 possible research routes. For each route include:

- problem statement
- novelty hypothesis
- required dataset
- candidate baseline set
- implementation difficulty
- expected experiment budget
- risk or blocker

Recommend one route and ask the user to confirm before generating execution artifacts. If the user gives a preferred paper or `main.tex`, treat that as the selected route.

## Phase 3: Paper Intake Or Scaffold

If `main.tex` exists:

1. Read `main.tex` and included files.
2. Extract title, abstract, method modules, losses, datasets, metrics, baseline table, and experiment protocol.
3. Write `paper_requirements.json`.
4. Build `experiment_matrix.json`.
5. Hand off to `matrix-autolab`.

If `main.tex` does not exist:

1. Produce an experiment-first manuscript scaffold rather than pretending a complete paper exists.
2. If the user provides a `main.tex` template, use it only for LaTeX style, preamble, generic manuscript organization, and table-shell feel; do not copy the template paper's domain content, claims, datasets, methods, citations, or results.
3. Prefer `build-main-tex` so the generated `main.tex` follows the template style while staying evidence-gated:

```bash
python scripts/research_autopilot.py build-main-tex --run-id <run_id> --template "<template-main.tex>" --topic "<confirmed research topic>" --force
```

4. Include a title candidate, abstract skeleton, method placeholders, experiment plan, result table shells, and required evidence list.
5. Mark all unverified claims as `needs_evidence`.
6. Do not call `matrix-autolab` until the user confirms the experiment plan and provides baseline code, dataset paths, or a paper source.

The generated scaffold may cite papers from `search_evidence.json`, but only as verified literature anchors. It must not invent references or transform template content into project claims.

## Phase 4: Matrix-AutoLab Execution Layer

Delegate execution to `matrix-autolab` when there is an experiment-ready paper source or confirmed experiment plan.

Recommended run initialization:

```bash
python scripts/autolab_run.py init-project --paper-source main.tex
python scripts/autolab_run.py start-run --kind idea_to_paper --entry-skill matrix-research-autopilot --paper-source main.tex
```

The handoff must include:

- selected research route
- `main.tex` path or scaffold path
- baseline codebase path or candidate repos
- dataset path or dataset acquisition notes
- target server or runtime environment
- `experiment_matrix.json`
- known blockers

The delegated workflow remains phase-gated:

1. `paperbanana` for model structure and framework figures.
2. `autolab` for method implementation, training, evaluation, and ablations.
3. `autobaseline` for SOTA baseline comparison.

Do not bypass `matrix-autolab`, `autolab`, or `autobaseline` user confirmation gates.

## Phase 5: Evidence Pack And Claims

After experiments produce reports and metrics, build `manuscript_claims.json`.

Each claim must have:

- claim text
- evidence files
- evidence type: metric, ablation, baseline, figure, code, log, or citation
- support status: `supported`, `partial`, or `needs_evidence`
- writing target: Abstract, Introduction, Results, Discussion, Figure caption, or Limitations

Claims with no evidence must be marked `needs_evidence` and excluded from final manuscript prose. Run:

```bash
python scripts/research_autopilot.py validate-claims --run-id <run_id>
```

## Phase 6: Built-In Nature Skills Writing Layer

Create `writing_packet.md` before invoking the built-in Nature Skills. Prefer:

```bash
python scripts/research_autopilot.py build-writing-packet --run-id <run_id> --argument "<confirmed research argument>"
```

`writing_packet.md` must include:

- confirmed research argument
- supported claims only in the drafting section
- key metrics and tables
- ablation conclusions
- baseline comparison conclusions
- figure contracts
- missing evidence and limitations
- citation needs

Default output policy:

- Provide Chinese notes explaining logic, evidence gaps, and revision risks.
- Use built-in `nature-writing` for Results, Discussion, Abstract, figure captions, and claim-evidence prose.
- `nature-writing` may only draft from supported claims in `writing_packet.md`; `needs_evidence` claims stay in limitations or missing-evidence notes.
- Use built-in `nature-figure` with `experiment_matrix.json`, result CSV files, phase reports, and figure contracts to plan or generate publication figures.
- Use built-in `nature-citation` only for background, related-work, discussion, method-context, and already verified literature claims; do not use citations to fabricate support for experimental results.
- Use built-in `nature-data` for Data Availability statements, FAIR checks, repository plans, dataset citations, and Chinese-to-English author notes.
- Use `nature-polishing`, `nature-response`, `nature-reader`, `nature-paper2ppt`, and `nature-academic-search` when the user asks for polishing, revision replies, paper reading, presentations, or additional literature verification.

## Evidence Rules

- Do not invent papers, datasets, metrics, model results, limitations, or citations.
- Do not let unsupported claims enter `writing_packet.md` as finished prose.
- If evidence is incomplete, write a placeholder and list the missing experiment or citation.
- Prefer reproducible commands, file paths, metrics, reports, and stable source IDs over narrative summaries.
- Use `validate-search-evidence` and `validate-claims` before route confirmation and final writing handoff.

## User Confirmation Gates

Ask for explicit confirmation at these points:

1. After `research_brief.md`, before choosing a route.
2. After route selection, before creating `paper_requirements.json` or manuscript scaffold.
3. Before handing off to `matrix-autolab`.
4. At every `matrix-autolab`, `autolab`, and `autobaseline` phase gate.
5. Before using built-in Nature Skills to produce final manuscript prose, figures, citations, or data statements.

## Recovery

When resuming:

1. Inspect `.autolab/project.json` and active run metadata if present.
2. Read `research_brief.md`, `search_evidence.json`, `paper_requirements.json`, `experiment_matrix.json`, and `manuscript_claims.json` if they exist.
3. Resume from the first missing, invalid, or unconfirmed artifact.
4. If `matrix-autolab` has an active gate, resume that gate first.

## Output To User

Use concise Chinese progress summaries. Include exact artifact paths and clearly state the next required user confirmation.
