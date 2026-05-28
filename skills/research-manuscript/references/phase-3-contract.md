# Phase 3 Contract

## Goal

Render a validated design package into an English `main.tex` manuscript draft that reads like a formal paper, not an internal scaffold.

## Inputs

- `research_design.json`
- `manuscript_blueprint.json`
- `search_evidence.json`
- Optional LaTeX template

## Required Outputs

- `main.tex`
- `citation_plan.json`
- `manuscript_source_map.json`
- `manuscript_audit.json`

## Handoff

Run `validate_manuscript_inputs.py` before drafting and `audit_main_tex.py` after drafting. Do not hand off a draft with audit errors.
