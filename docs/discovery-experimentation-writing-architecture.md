# Codex-Native Research Kernel Architecture

## Purpose

DreamweaverAI AutoLab should evolve from a collection of paper reproduction and writing skills into a Codex-native research operating system with three first-class lanes:

- Discovery: turn an idea, topic, dataset, or rough hypothesis into evidence, route options, and an experiment-ready research design.
- Experimentation: turn a paper source or confirmed experiment plan into implementation, runs, ablations, baselines, metrics, and verification reports.
- Writing: turn verified evidence into claims, figures, citations, manuscript sections, revision material, data statements, and presentation assets.

AutoResearchClaw is a reference for stage discipline, checkpointing, gate handling, and evidence-based paper generation. It is not the architecture root and should not be copied as a 23-stage pipeline.

The intended product form is a Codex plugin shell wrapped around a local research agent kernel and a durable research memory layer. The plugin is the user-facing entry point; the kernel owns decisions, recovery, verification, and human-in-the-loop policy; the knowledge layer accumulates evidence, failures, and lessons across runs.

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
├─ Research Kernel
│  ├─ Debate Engine
│  ├─ Recovery and Decision Loop
│  ├─ Verification Ledger
│  ├─ HITL Policy Engine
│  └─ Evolution Memory
├─ Knowledge Layer
│  ├─ event log
│  ├─ artifact registry
│  ├─ evidence graph
│  ├─ claim graph
│  ├─ failure graph
│  └─ lesson graph
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
- Do not treat dashboard screens as the architecture source of truth.
- Do not let self-evolution edit skills, prompts, or validators without evidence and review gates.

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

### Kernel Before Dashboard

The first-class product is the research kernel and its durable memory, not the dashboard. A dashboard can read the kernel state later, but it should not define phase semantics, artifact contracts, or gate behavior.

## Research Kernel

The research kernel is the reusable agent logic behind the Codex plugin. It is not a standalone autonomous agent in the first phase. Codex remains the orchestrator, and the kernel provides the protocols, artifacts, validators, and decision rules that make research runs auditable and resumable.

### Debate Engine

The Debate Engine runs structured multi-perspective reviews for high-leverage reasoning points:

- Discovery: generate and challenge hypotheses, route options, novelty claims, dataset choices, and baseline requirements.
- Experimentation: review implementation plans, failure causes, metric interpretation, ablation meaning, and baseline fairness.
- Writing: challenge manuscript claims, figure interpretation, limitation wording, and citation use.

Each debate should produce a structured artifact, not just prose:

```text
debates/
├─ <phase>_<topic>_debate.json
└─ <phase>_<topic>_summary.md
```

The JSON record should include roles, claims, evidence references, objections, resolution, confidence, and the final decision. Debate outputs can inform decisions, but they do not override validators or user gates.

### Recovery And Decision Loop

The Recovery and Decision Loop turns execution failure into a controlled decision instead of a dead end. It should support these decisions:

- `PROCEED`: evidence is sufficient; continue.
- `REFINE`: keep the route, adjust parameters, implementation, data handling, or analysis.
- `PIVOT`: change hypothesis, method, dataset, or baseline strategy.
- `RETRY`: rerun after infrastructure or transient failure.
- `STOP_WEAK`: stop because the route is not worth continuing.
- `ESCALATE`: require user or expert input before continuing.

Every recovery decision must write to `decisions.jsonl` and, when relevant, create a `Failure` and `Lesson` node in the knowledge layer.

### Verification Ledger

The Verification Ledger prevents metric fabrication, data leakage, unsupported claims, and citation hallucination.

It should track:

- source evidence and stable locators
- dataset identity and preprocessing hashes
- experiment commands and environment fingerprints
- metrics and the files that produced them
- claim-to-evidence links
- citation inclusion and exclusion reasons
- figure provenance

Writing can only use measured claims that point back to verified experiment outputs. Background citations can support context, but they cannot support experimental result claims.

### HITL Policy Engine

The HITL Policy Engine controls how autonomous a run is allowed to be. The architecture supports seven intervention modes:

| Mode | Meaning | Typical Use |
|---|---|---|
| `full_auto` | Run without stopping unless a hard validator fails | low-risk exploration |
| `gate_only` | Stop only at major gates | routine research workflow |
| `checkpoint` | Stop after every coarse phase | medium-risk projects |
| `co_pilot` | Collaborate on key decisions and tradeoffs | research design and interpretation |
| `step_by_step` | Require confirmation for every meaningful step | high-risk or new workflows |
| `audit_only` | Run first, then require full audit before writing/export | batch exploration |
| `manual_lock` | High-risk steps require explicit unlock | expensive experiments, clinical/biomedical claims, external submission |

The selected mode must be stored in `run.json` and reflected in `gate_status.json`.

### Evolution Memory

Evolution Memory converts repeated failures and corrections into future risk defenses. It is evidence-gated, not automatic self-modification.

The loop is:

1. A run produces a failure, warning, rejection, or manual correction.
2. The kernel records a `Failure` and a candidate `Lesson`.
3. Cross-run aggregation detects repeated lessons.
4. The system proposes one of: validator patch, skill patch, prompt rule, checklist item, experiment template, or dashboard read model.
5. Codex prepares the patch.
6. Tests and user review gate the change.
7. Accepted improvements are recorded as `Lesson -> improves -> Skill/Prompt/Validator`.

This keeps the system self-improving without letting it silently rewrite its own behavior.

## Knowledge Layer

The knowledge layer is the long-term research memory. The first version should be local-first and simple:

```text
.autolab/
├─ memory/
│  ├─ knowledge.db
│  ├─ evidence/
│  ├─ lessons/
│  └─ indexes/
└─ runs/<run_id>/
   ├─ evidence.jsonl
   ├─ decisions.jsonl
   └─ artifact_manifest.json
```

`knowledge.db` can start as SQLite. A graph database can be added later if query volume or relationship complexity requires it.

### Graph Nodes

Initial node types:

- `Run`
- `Paper`
- `Dataset`
- `Method`
- `Baseline`
- `CodeRepo`
- `Experiment`
- `Metric`
- `Claim`
- `Citation`
- `Figure`
- `Decision`
- `Failure`
- `Lesson`
- `Skill`
- `Prompt`
- `Validator`

### Graph Relationships

Initial relationship types:

- `Paper -> proposes -> Method`
- `Paper -> cites -> Paper`
- `CodeRepo -> implements -> Method`
- `Dataset -> evaluates -> Method`
- `Experiment -> uses -> Dataset`
- `Experiment -> produces -> Metric`
- `Metric -> supports -> Claim`
- `Citation -> supports_background_for -> Claim`
- `Claim -> appears_in -> manuscript section`
- `Figure -> visualizes -> Metric/Claim`
- `Decision -> changes -> Route/Experiment/Writing`
- `Failure -> caused_by -> Decision/Code/Data/Environment`
- `Lesson -> prevents -> Failure`
- `Lesson -> improves -> Skill/Prompt/Validator`
- `Run -> generated -> Artifact`

The graph should store references to artifacts, not duplicate large files.

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

- structured agent debate for hypothesis generation and result interpretation
- self-healing execution with `PROCEED`, `REFINE`, `PIVOT`, `RETRY`, `STOP_WEAK`, and `ESCALATE` decisions
- verifiable result reporting that blocks metric fabrication and citation hallucination
- human-in-the-loop modes from full autonomy to step-by-step supervision
- cross-run evolution that turns historical failures into future risk defenses
- checkpoints, resume, gate rollback targets, and pipeline summary artifacts

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
- a Research Kernel read model with Debate Engine, Recovery and Decision Loop, Verification Ledger, HITL Policy Engine, and Evolution Memory entries
- seven HITL modes stored in `run.json` and reflected in `gate_status.json`
- a local-first knowledge layer under `.autolab/memory/`
- initial graph schema for papers, datasets, methods, baselines, experiments, metrics, claims, failures, lessons, skills, prompts, and validators
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
7. Add kernel metadata to run records: debate records, recovery decisions, verification ledger status, HITL policy, and lesson candidates.
8. Add `.autolab/memory/knowledge.db` or an equivalent local graph store after event and artifact records are stable.
9. Update the dashboard only as a read-only viewer of the normalized run and memory model.

## Implementation Defaults

- `research_autopilot.py init-artifacts` should create lane folders by default for new runs.
- Legacy root-level artifacts should be referenced from `artifact_manifest.json` first, not physically moved.
- `artifact_manifest.json` should be rewritten as the current normalized state changes.
- `evidence.jsonl` and `decisions.jsonl` should be append-only audit logs.
- Final packet readiness should be owned by the protocol layer; the dashboard only displays the result.
- Self-evolution proposals should be recorded as candidate lessons first; accepted skill, prompt, or validator changes require tests and review.
- The first knowledge graph implementation should be SQLite-backed unless query complexity proves it needs a dedicated graph database.

The recommended default is conservative: reference legacy outputs from `artifact_manifest.json` first, then migrate physical paths only when a phase touches the artifact.
