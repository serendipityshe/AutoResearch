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
├─ Research Design Layer
├─ Research Manuscript Layer
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
python skills/research-design/scripts/validate_research_design_artifacts.py --root research_autopilot
python scripts/research_autopilot.py validate-research-design
python skills/research-manuscript/scripts/validate_manuscript_inputs.py --root research_autopilot
python scripts/research_autopilot.py build-main-tex --design-file research_design.json --template "<path/to/template/main.tex>" --topic "<research topic>"
python skills/research-manuscript/scripts/audit_main_tex.py --root research_autopilot
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
| `research_design.json` | Route-confirmed research design contract for `main.tex`: dataset roles, frontier landscape, domain difficulties, method rationale, mathematical modules, ablations, and expected hypotheses. |
| `manuscript_blueprint.json` | Paper argument, section plan, and claim-to-experiment map used before LaTeX rendering. |
| `citation_plan.json` | Bibliography inclusion/exclusion plan; only sources with stable locators enter references. |
| `manuscript_source_map.json` | Trace map from manuscript sections, claims, formulas, datasets, and citations back to design/evidence ids. |
| `manuscript_audit.json` | Post-render audit of abstract logic, section structure, Method formulas, TBD-only results, risks, and citations. |
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
-> use research-discovery for Phase 1
-> discovery_plan.json, search_evidence.json, research_landscape.json, research_brief.md
-> user confirms route
-> use research-design for Phase 2
-> research_design.json, manuscript_blueprint.json
-> use research-manuscript for Phase 3
-> main.tex, citation_plan.json, manuscript_source_map.json, manuscript_audit.json
-> paper_requirements.json and experiment_matrix.json
-> Matrix-AutoLab execution layer
-> manuscript_claims.json
-> writing_packet.md
-> built-in Nature Skills writing layer
```

## Phase 1: Research Discovery

Delegate this phase to `research-discovery`.

The Phase 1 output must include:

- `discovery_plan.json`
- `search_evidence.json`
- `research_landscape.json`
- `research_brief.md`

Use latest-12-month evidence for frontier hotspots, latest 3-5 year evidence for stable domain difficulties, and no hard year filter for public datasets or classical baselines. Prefer primary sources: papers, official repositories, official datasets, benchmark pages, project documentation, PubMed records, and the user's Zotero library.

Run the `research-discovery` validator before route selection. If the discovery package lacks datasets, baselines, route candidates, or stable locators, continue discovery instead of asking the user to confirm a weak route.

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

Route candidates should come from `research_landscape.json`. Recommend one route and ask the user to confirm before generating execution artifacts. If the user gives a preferred paper or `main.tex`, treat that as the selected route.

## Phase 2.5: Research Design

Delegate this phase to `research-design`.

The Phase 2 design output must include:

- `research_design.json`
- `manuscript_blueprint.json`

Use `research-design` to convert the confirmed route into a strict design contract. It should not restart broad discovery. It should bind each method decision to evidence ids, dataset roles, domain difficulties, formulas, losses, ablations, baselines, metrics, and risks.

Run the `research-design` validator before `build-main-tex`:

```bash
python skills/research-design/scripts/validate_research_design_artifacts.py --root research_autopilot
python scripts/research_autopilot.py validate-research-design
```

If the validator reports an unconfirmed route, fewer than three modules, missing formulas, missing module evidence ids, or missing experiment alignment, revise `research_design.json` instead of generating `main.tex`.

## Phase 3: Manuscript Rendering

Delegate this phase to `research-manuscript` when `main.tex` does not exist or when a generated manuscript needs audit.

The Phase 3 manuscript output must include:

- `main.tex`
- `citation_plan.json`
- `manuscript_source_map.json`
- `manuscript_audit.json`

Use `research-manuscript` to render the validated design as an English paper draft. It should follow the manuscript template's writing logic only: formal Abstract progression, motivated Introduction, grouped Related Work, mathematical Problem Statement, formula-rich Method, realistic Study Design, TBD-only planned Results, and restrained Risks/Discussion. It must not copy the template's scientific content.

Run the manuscript checks around `build-main-tex`:

```bash
python skills/research-manuscript/scripts/validate_manuscript_inputs.py --root research_autopilot
python scripts/research_autopilot.py build-main-tex --design-file research_design.json --template "<template-main.tex>" --force
python skills/research-manuscript/scripts/audit_main_tex.py --root research_autopilot
```

If the auditor reports internal abstract phrasing, missing `Why direct transfer is insufficient`, missing mathematical symbols, missing Method modules/formulas/losses/ablations, fake numeric results, or weak Study Design, revise `main.tex` before any execution handoff.

## Phase 3.5: Paper Intake Or Scaffold

If `main.tex` exists:

1. Read `main.tex` and included files.
2. Extract title, abstract, method modules, losses, datasets, metrics, baseline table, and experiment protocol.
3. Write `paper_requirements.json`.
4. Build `experiment_matrix.json`.
5. Hand off to `matrix-autolab`.

If `main.tex` does not exist:

1. Use `research-design` to produce `research_design.json` and `manuscript_blueprint.json` first. These files are the mandatory contract between the research synthesis step and `main.tex` generation.
2. The design must include:
   - `topic`, `confirmed_route`, and `title_candidate`
   - `dataset_strategy` with `primary`, `validation`, `external_test`, and `supplementary`
   - `frontier_landscape` from papers, journals, datasets, and code evidence
   - `domain_difficulties` that explain task/data blockers and their experiment impact
   - `method_rationale` with current method problems and the proposed design bridge
   - `proposed_method` with at least three named modules, each with inputs, outputs, formulas, loss terms, and an ablation
   - `experiment_alignment` mapping each module to datasets, baselines, metrics, and ablations
   - `expected_results` as `hypothesis`, `expected`, `planned`, or `needs_evidence`; never write measured values before experiments
3. Run `research-design` validation and `validate-research-design` before generating `main.tex`. If validation fails, fix `research_design.json`; do not generate a generic fallback.
4. If the user provides a `main.tex` template, use it only for LaTeX style, preamble, generic manuscript organization, and table-shell feel; do not copy the template paper's domain content, claims, datasets, methods, citations, or results.
5. Prefer `research-manuscript` plus `build-main-tex` so the generated `main.tex` follows the template style while staying evidence-gated:

```bash
python skills/research-manuscript/scripts/validate_manuscript_inputs.py --root research_autopilot
python scripts/research_autopilot.py validate-research-design --run-id <run_id>
python scripts/research_autopilot.py build-main-tex --run-id <run_id> --design-file research_design.json --template "<template-main.tex>" --topic "<confirmed research topic>" --force
python skills/research-manuscript/scripts/audit_main_tex.py --root research_autopilot
```

6. The generated English manuscript must include a complete design logic: current method limitations, domain/data difficulties, frontier-driven rationale, grouped related work, a direct-transfer insufficiency section, at least three mathematical method modules, a total objective, ablations, dataset roles, planned results shells, expected hypotheses, risks, discussion, and bibliography.
7. Mark all unverified claims as `needs_evidence`, `hypothesis`, `expected`, or `planned`.
8. Do not call `matrix-autolab` until the user confirms the experiment plan and provides baseline code, dataset paths, or a paper source.

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
