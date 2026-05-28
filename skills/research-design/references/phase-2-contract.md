# Phase 2 Contract

## Goal

Convert a user-confirmed research route into a strict design package. The package must explain why the route is worth studying, what method will be proposed, how the method is mathematical rather than narrative, and how each claim will be tested.

## Inputs

- `research_landscape.json`
- `search_evidence.json`
- `research_brief.md`
- User-confirmed route id, route description, or preferred paper direction
- Optional constraints: target journal tier, compute budget, available data, method family, or template paper

## Required Artifacts

### `research_design.json`

Required top-level fields:

- `topic`
- `confirmed_route`
- `title_candidate`
- `dataset_strategy`
- `frontier_landscape`
- `domain_difficulties`
- `method_rationale`
- `proposed_method`
- `experiment_alignment`
- `expected_results`
- `risk_review`

### `manuscript_blueprint.json`

Required top-level fields:

- `title`
- `central_argument`
- `section_plan`
- `claim_to_experiment_map`

## Handoff

Run `scripts/validate_research_design_artifacts.py`. Then run the plugin-level `validate-research-design` command before `build-main-tex`.
