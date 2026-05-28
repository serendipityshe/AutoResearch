---
name: research-discovery
description: Use when starting from a research idea, topic, disease, modality, dataset hint, or rough hypothesis and Codex must discover public datasets, current 12-month literature frontiers, 3-5 year domain difficulties, code repositories, baselines, and route candidates before research design or main.tex generation.
---

# Research Discovery

Use this skill for Module 1 Phase 1. Turn a rough research idea into an auditable discovery package, not a pile of links.

## Boundary

This skill does not generate `main.tex`, design methods, or claim results. It stops after producing route candidates with evidence, datasets, baselines, and risks.

## Required Outputs

Write these artifacts under `.autolab/runs/<run_id>/` when a run exists; otherwise use `research_autopilot/`.

- `discovery_plan.json`
- `search_evidence.json`
- `research_landscape.json`
- `research_brief.md`

## Workflow

1. Build `discovery_plan.json` from the user's idea.
2. Search public datasets and dataset papers.
3. Search latest 12-month frontier hotspots.
4. Search 3-5 year domain difficulties.
5. Search code repositories and baseline candidates.
6. Normalize all sources into `search_evidence.json`.
7. Synthesize `research_landscape.json`.
8. Write a Chinese `research_brief.md` with 2-3 route candidates.
9. Run the validator before handing off to research design.

## Time Windows

- Frontier hotspots: latest 12 months.
- Domain difficulties: latest 3-5 years.
- Public datasets: no hard year filter; prioritize current availability and recent usage.
- Classical baselines: no hard year filter; explain why each remains necessary.

## References

- Required artifacts and handoff: `references/phase-1-contract.md`
- Source selection: `references/source-routing.md`
- Evidence fields: `references/evidence-schema.md`
- Dataset search: `references/dataset-discovery.md`
- Literature frontier search: `references/literature-frontier.md`
- Code and baselines: `references/code-baseline-discovery.md`
- Quality checks: `references/quality-gates.md`

## Commands

Validate before handoff:

```bash
python skills/research-discovery/scripts/validate_discovery_artifacts.py --root research_autopilot
```

Summarize status:

```bash
python skills/research-discovery/scripts/summarize_discovery_status.py --root research_autopilot
```
