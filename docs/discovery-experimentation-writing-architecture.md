# Discovery, Experimentation, and Writing Architecture

## Purpose

DreamweaverAI AutoLab should evolve from a collection of paper reproduction and writing skills into a Codex-native research operating system with three first-class lanes:

- Discovery: turn an idea, topic, dataset, or rough hypothesis into evidence, route options, and an experiment-ready research design.
- Experimentation: turn a paper source or confirmed experiment plan into implementation, runs, ablations, baselines, metrics, and verification reports.
- Writing: turn verified evidence into claims, figures, citations, manuscript sections, revision material, data statements, and presentation assets.

AutoResearchClaw is a reference for stage discipline, checkpointing, gate handling, and evidence-based paper generation. It is not the architecture root and should not be copied as a 23-stage pipeline.

## Design Decision

Keep `dreamweaverai-autolab` as the Codex plugin. Do not create a separate `researchclaw-codex` plugin for this phase.

The plugin becomes a facade over protocol artifacts, validators, scripts, and skills. Codex remains the orchestration layer: it reads project state, invokes the right skill, runs protocol utilities, inspects evidence, edits files when needed, and stops at gates. Deterministic Python scripts remain the source of truth for run records, artifact validation, gate status, and evidence contracts.

```text
dreamweaverai-autolab
├─ Codex Plugin Layer
│  ├─ .codex-plugin/plugin.json
│  ├─ .app.json
│  ├─ skills/
│  └─ apps/dashboard/
├─ Protocol Layer
│  ├─ scripts/autolab_run.py
│  ├─ scripts/autolab_gate.py
│  ├─ scripts/autolab_contract.py
│  ├─ scripts/autolab_event.py
│  └─ scripts/research_autopilot.py
├─ Discovery Lane
├─ Experimentation Lane
└─ Writing Lane
```

## Non-Goals

- Do not rewrite the entire workflow as one monolithic skill.
- Do not make AutoResearchClaw a runtime dependency.
- Do not move all legacy outputs into `.autolab/` automatically.
- Do not let chat history become the source of truth for phase state.
- Do not allow unsupported claims into final manuscript prose.

## Core Concepts

### Codex-Native Rhythm

The workflow should match how Codex works best:

1. Inspect local project state.
2. Read protocol artifacts.
3. Resume from the last confirmed gate.
4. Execute one bounded phase or step.
5. Record evidence.
6. Run validators.
7. Stop when user confirmation is required.

Large autonomous loops can exist, but they must write inspectable state after every meaningful step.

### Protocol Before Prose

Every major decision must appear in a machine-readable artifact before it appears as narrative. Reports can summarize, but they cannot replace the source artifacts.

### Evidence Before Claims

Discovery evidence supports route selection and background claims. Experiment evidence supports results claims. Writing must distinguish `supported`, `partial`, and `needs_evidence`.

## Run State Layout

Use `.autolab/` as the single project-local run archive.

```text
.autolab/
├─ project.json
├─ workflow_status.json
└─ runs/
   └─ <run_id>/
      ├─ run.json
      ├─ gate_status.json
      ├─ phase_plan.json
      ├─ requirements.json
      ├─ artifact_manifest.json
      ├─ evidence.jsonl
      ├─ decisions.jsonl
      ├─ discovery/
      ├─ experimentation/
      ├─ writing/
      └─ final_packet/
```

`gate_status.json` is the control-plane source of truth. Skill instructions and chat summaries must defer to it.

## Three Lanes

### Discovery

Discovery starts from an idea, topic, dataset, paper seed, user hypothesis, or broad research direction. Its job is to produce a route that is worth testing and a design that can be handed to experimentation.

Primary artifacts:

- `discovery/research_brief.md`
- `discovery/search_evidence.json`
- `discovery/domain_landscape.json`
- `discovery/solution_landscape.json`
- `discovery/route_judgement.json`
- `discovery/research_loop_state.json`
- `discovery/research_design.json`
- `discovery/manuscript_blueprint.json`
- `experimentation/experiment_matrix.json`

Responsible skills:

- `matrix-research-autopilot`
- `research-hotspot-discovery`
- `research-solution-discovery`
- `research-route-judge`
- `research-design`
- `research-manuscript` when a scaffold is needed

Discovery exits only when there is a confirmed route, a validated research design, and an experiment matrix or a clear blocker.

### Experimentation

Experimentation starts from `main.tex`, `paper_requirements.json`, or `experiment_matrix.json`. Its job is to produce implementation evidence, metrics, ablations, baselines, and verified result artifacts.

Primary artifacts:

- `experimentation/paper_requirements.json`
- `experimentation/experiment_matrix.json`
- `experimentation/contract.json`
- `experimentation/data_pipeline.json`
- `experimentation/implementation_report.md`
- `experimentation/run_metrics.json`
- `experimentation/ablation_report.md`
- `experimentation/baseline_report.md`
- `experimentation/result_verification.json`

Responsible skills:

- `matrix-autolab`
- `paperbanana`
- `autolab`
- `autobaseline`

The experiment contract should lock hyperparameters, dataset paths, preprocessing hashes, augmentation hashes, module flags, environment fingerprints, and ablation differences before expensive execution.

### Writing

Writing starts only after enough verified evidence exists. It may also produce planned manuscript scaffolds before experiments, but measured claims remain blocked until experiment evidence exists.

Primary artifacts:

- `writing/manuscript_claims.json`
- `writing/writing_packet.md`
- `writing/figure_contracts.json`
- `writing/citation_plan.json`
- `writing/data_availability.md`
- `writing/manuscript_sections/`
- `writing/polishing_report.md`
- `writing/response_packet.md`
- `writing/presentation_packet.md`

Responsible skills:

- `nature-writing`
- `nature-figure`
- `nature-citation`
- `nature-data`
- `nature-polishing`
- `nature-response`
- `nature-reader`
- `nature-paper2ppt`
- `nature-academic-search`

Writing exits when supported claims have been converted into the requested deliverable and unsupported claims remain explicitly marked as missing evidence, limitations, or future work.

## Nine-Phase Workflow

The three lanes should expose nine coarse phases rather than AutoResearchClaw's 23 stages.

| Phase | Lane | Goal | Gate |
|---|---|---|---|
| `D1_problem_framing` | Discovery | Clarify topic, scope, problem, audience, constraints | User confirms research intent |
| `D2_evidence_discovery` | Discovery | Collect papers, code, datasets, baselines, web, PubMed, Zotero | Evidence validator passes |
| `D3_route_selection` | Discovery | Select route and produce research design | User or judge confirms route |
| `E1_experiment_contract` | Experimentation | Freeze requirements, data, metrics, environment, ablations | Contract locks |
| `E2_implementation` | Experimentation | Implement method and runnable pipeline | Required implementation evidence exists |
| `E3_evaluation_ablation_baseline` | Experimentation | Run evaluation, ablations, baselines, verification | Results verified |
| `W1_claim_mapping` | Writing | Map claims to evidence | Claim validator passes |
| `W2_manuscript_figure_citation` | Writing | Draft prose, figures, citations, data statements | Unsupported claims excluded |
| `W3_polish_export` | Writing | Polish, response, PPT, final packet | Final artifact manifest passes |

Each phase can contain smaller steps, but only one step should be active at a time in `gate_status.json`.

## Gate Protocol

Every meaningful phase step follows the same anti-skip protocol:

1. Define requirements.
2. Start exactly one active step.
3. Execute that step.
4. Record evidence.
5. Validate step output.
6. Present blockers or confirmation request.
7. Complete the step only after validation and required confirmation.

The protocol maps to existing utilities:

```bash
python scripts/autolab_gate.py define-requirement ...
python scripts/autolab_gate.py start-step ...
python scripts/autolab_gate.py add-evidence ...
python scripts/autolab_gate.py check-step ...
python scripts/autolab_gate.py confirm-step ...
```

## Artifact Contracts

### Discovery Contract

Discovery artifacts must answer:

- What problem is being solved?
- Why is it worth doing now?
- Which papers, repositories, datasets, and baselines support the route?
- What route was selected?
- What did the independent judge decide?
- What method modules, formulas, datasets, metrics, and ablations are required?

### Experimentation Contract

Experimentation artifacts must answer:

- What exactly must be implemented?
- Which dataset and preprocessing pipeline are used?
- Which hyperparameters and environment details are locked?
- Which metrics, ablations, and baselines are required?
- Which result files support each conclusion?
- Which failures or deviations occurred?

### Writing Contract

Writing artifacts must answer:

- Which claims are supported?
- Which claims are partial or missing evidence?
- Which sections, captions, figures, citations, and data statements use each claim?
- Which citations are for background only?
- Which measured claims are backed by experiment outputs?

## Dashboard Role

The dashboard should remain read-only in this architecture phase. It should visualize:

- active run and phase
- current gate
- blockers
- discovery coverage
- experiment contract status
- metrics and ablations
- claim support status
- final packet readiness

It should not mutate `.autolab/` records until the protocol layer is stable.

## Relationship To AutoResearchClaw

Borrow these ideas:

- stage summaries
- checkpoints and resume
- gate rollback targets
- result verification before writing
- citation and claim checks
- pipeline summary artifacts
- human-in-the-loop pause points

Do not borrow these directly:

- a fixed 23-stage state machine
- a monolithic runner as the primary Codex interface
- Codex as only a text-only ACP backend
- AutoResearchClaw's project identity or directory layout

## MVP Scope

The first architecture milestone should deliver:

- one unified `.autolab/runs/<run_id>/` layout
- lane-specific folders for discovery, experimentation, and writing
- `artifact_manifest.json`
- `evidence.jsonl`
- `decisions.jsonl`
- nine coarse phases in the gate plan
- discovery validators wired to existing `research_autopilot.py`
- experiment contract reuse from `autolab_contract.py`
- claim validation before writing packet generation
- updated `matrix-research-autopilot` and `matrix-autolab` instructions that refer to the three lanes
- dashboard read model for the three lanes

## Migration Strategy

1. Preserve all existing skill entry points.
2. Add the three-lane vocabulary to docs and plugin prompts.
3. Introduce the run layout without moving legacy outputs.
4. Teach `matrix-research-autopilot` to create lane folders and manifests.
5. Teach `matrix-autolab` to read the same run state before executing.
6. Teach writing skills to consume `writing_packet.md` and `manuscript_claims.json` from the lane layout.
7. Update the dashboard to read the normalized run model.

## Implementation Defaults

- `research_autopilot.py init-artifacts` should create lane folders by default for new runs.
- Legacy root-level artifacts should be referenced from `artifact_manifest.json` first, not physically moved.
- `artifact_manifest.json` should be rewritten as the current normalized state changes.
- `evidence.jsonl` and `decisions.jsonl` should be append-only audit logs.
- Final packet readiness should be owned by the protocol layer; the dashboard only displays the result.

The recommended default is conservative: reference legacy outputs from `artifact_manifest.json` first, then migrate physical paths only when a phase touches the artifact.
