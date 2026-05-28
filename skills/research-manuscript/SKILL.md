---
name: research-manuscript
description: Use after research-design when Codex must turn research_design.json, manuscript_blueprint.json, evidence, and optional LaTeX templates into an English main.tex manuscript draft with formal abstract logic, mathematical Method, TBD-only planned results, citation filtering, and audit checks.
---

# Research Manuscript

Use this skill for Module 1 Phase 3. Convert validated research design artifacts into a controlled English `main.tex`, then audit the draft before handoff.

## Boundary

This skill does not perform discovery, invent methods, execute experiments, or report measured results. It renders and audits manuscript text from `research_design.json`, `manuscript_blueprint.json`, and `search_evidence.json`.

## Required Outputs

Write these artifacts under `.autolab/runs/<run_id>/` when a run exists; otherwise use `research_autopilot/`.

- `main.tex`
- `citation_plan.json`
- `manuscript_source_map.json`
- `manuscript_audit.json`

## Workflow

1. Validate manuscript inputs before writing.
2. Use any supplied template only for preamble, section order, table style, and LaTeX conventions.
3. Draft sections from `manuscript_blueprint.json` and scientific details from `research_design.json`.
4. Write Abstract as: clinical problem -> current AI limitation -> We propose method -> core mechanism -> dataset/validation plan -> no fabricated results.
5. Keep Method mathematical: definitions, module equations, module losses, total objective, and ablations.
6. Keep planned Results as table shells with `TBD` only.
7. Filter bibliography sources through `citation_plan.json`; sources without stable locators do not enter bibliography.
8. Run the auditor and fix `main.tex` until it passes.

## References

- Phase contract: `references/phase-3-contract.md`
- Template logic: `references/template-writing-logic.md`
- Section architecture: `references/section-architecture.md`
- Method rules: `references/method-writing-rules.md`
- Planned results policy: `references/planned-results-policy.md`
- Citation policy: `references/citation-policy.md`
- Quality gates: `references/quality-gates.md`

## Commands

Validate inputs:

```bash
python skills/research-manuscript/scripts/validate_manuscript_inputs.py --root research_autopilot
```

Audit generated `main.tex`:

```bash
python skills/research-manuscript/scripts/audit_main_tex.py --root research_autopilot
```

Summarize status:

```bash
python skills/research-manuscript/scripts/summarize_manuscript_status.py --root research_autopilot
```
