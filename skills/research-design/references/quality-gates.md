# Quality Gates

Run `scripts/validate_research_design_artifacts.py` before handoff.

## Hard Failures

- Missing `research_design.json`.
- Missing `manuscript_blueprint.json`.
- Route is not explicitly user-confirmed.
- Missing dataset role: primary, validation, external_test, or supplementary.
- Fewer than 3 method modules.
- Any module lacks formula, loss term, ablation, inputs, outputs, or evidence ids.
- Missing total objective.
- Missing experiment alignment.
- Any module lacks a corresponding experiment alignment.
- Expected results include measured values.
- Blueprint has no central argument, Method section, or claim-to-experiment map.

## Warnings

- Dataset lacks rationale or risk notes.
- Formula does not look like a mathematical expression.
- Risk review is too thin.
- Baseline list lacks a recent strong baseline.

## Handoff Rule

Do not run `build-main-tex` until the design validator passes and the user has confirmed the route.
