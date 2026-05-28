---
name: research-design
description: Use after research-discovery when a user has confirmed a research route and Codex must turn evidence, datasets, domain difficulties, hotspots, and baselines into a formula-rich research_design.json and manuscript blueprint before main.tex generation.
---

# Research Design

Use this skill for Module 1 Phase 2. Convert a confirmed route into a design contract that can survive reviewer-style scrutiny.

## Boundary

This skill does not perform broad web discovery, execute experiments, or generate `main.tex`. It consumes `research_landscape.json`, `search_evidence.json`, `research_brief.md`, and the user's confirmed route, then produces design artifacts for the `build-main-tex` renderer.

## Required Outputs

Write these artifacts under `.autolab/runs/<run_id>/` when a run exists; otherwise use `research_autopilot/`.

- `research_design.json`
- `manuscript_blueprint.json`

## Workflow

1. Read Phase 1 discovery artifacts and identify the user-confirmed route.
2. Run a route clarification pass: problem, novelty hypothesis, domain risks, dataset feasibility.
3. Run a method construction pass: at least 3 named modules, each with inputs, outputs, formulas, losses, ablation, and evidence ids.
4. Run an experiment alignment pass: map every module and claim to datasets, baselines, metrics, and ablations.
5. Write `research_design.json` as the strict contract for `build-main-tex`.
6. Write `manuscript_blueprint.json` as the paper argument and section plan.
7. Run the validator before calling `validate-research-design` or `build-main-tex`.

## References

- Required artifacts and schema: `references/phase-2-contract.md`
- Route-to-design synthesis: `references/route-to-design.md`
- Method modules: `references/method-module-patterns.md`
- Formula requirements: `references/formula-requirements.md`
- Experiment alignment: `references/experiment-alignment.md`
- Novelty and risk review: `references/novelty-risk-review.md`
- Manuscript blueprint: `references/manuscript-blueprint.md`
- Quality checks: `references/quality-gates.md`

## Commands

Validate before handoff:

```bash
python skills/research-design/scripts/validate_research_design_artifacts.py --root research_autopilot
```

Summarize status:

```bash
python skills/research-design/scripts/summarize_design_status.py --root research_autopilot
```
