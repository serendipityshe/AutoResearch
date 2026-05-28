# Quality Gates

Run `scripts/validate_discovery_artifacts.py` before handoff.

## Hard Failures

- Missing `discovery_plan.json`.
- Missing `search_evidence.json`.
- Missing `research_landscape.json`.
- Missing `research_brief.md`.
- Evidence item lacks any stable locator.
- No dataset candidates.
- No route candidates.
- Route candidate lacks evidence ids.
- Dataset lacks candidate role.
- Frontier hotspot uses no latest-12-month evidence and is not marked as weak or background.

## Warnings

- No code repositories found.
- No baseline candidates found.
- Dataset has unknown license.
- Dataset access is gated or ambiguous.
- Repo has no license.
- Repo has no train/eval entrypoint.
- Domain difficulty has only one evidence item.
- Route candidate has no explicit failure risk.

## Handoff Rule

Do not move to `research-design` until the user has at least two route candidates or one clearly recommended route with strong evidence and explicit risks.

## Writing Rule

`research_brief.md` should be in Chinese for user review. It may include English paper titles and dataset names.
