# Quality Gates

## Hard Failures

- Missing `research_design.json`, `manuscript_blueprint.json`, or `search_evidence.json`.
- Missing `main.tex` after drafting.
- Abstract contains internal phrases: `this document`, `manuscript-ready`, `study design draft`, `manuscript-grade`.
- Abstract does not contain `We propose`.
- Missing Introduction, Related Work, Problem Statement, Method, Study Design, Planned Results, Risks, or Discussion.
- Related Work lacks `Why direct transfer is insufficient`.
- Problem Statement lacks mathematical definitions for `x`, `M`, `P`, `R_g`, or `\hat{M}`.
- Method lacks 3+ modules, formulas, losses, ablations, or `\mathcal{L}_{total}`.
- Study Design lacks dataset roles, inclusion/exclusion, preprocessing, implementation preset, baselines, metrics, ablations, or statistics.
- Planned Results include numeric values instead of `TBD`.
- Bibliography contains sources without stable locators.

## Handoff Rule

Do not hand off `main.tex` until `audit_main_tex.py` returns `ok: true`.
