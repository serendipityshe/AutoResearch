# Phase 1 Contract

## Goal

Convert a rough research idea into a structured discovery package that can support later research design. The output must explain what can be studied, what data exists, what the recent frontier is, what stable domain difficulties exist, which baselines matter, and which research routes are worth designing.

## Inputs

- User topic, disease, modality, task, dataset hint, or hypothesis.
- Optional constraints: target journal tier, preferred task, available data, compute budget, language, or template paper.
- Optional run root: `.autolab/runs/<run_id>/`; otherwise use `research_autopilot/`.

## Required Artifacts

### `discovery_plan.json`

Search plan before heavy synthesis.

Required fields:

- `topic`
- `created_at`
- `time_policy`
- `concepts`
- `source_plan`
- `queries`
- `screening_rules`

### `search_evidence.json`

Raw normalized evidence. Keep it close to sources. Do not turn it into a narrative.

Required collections:

- `papers`
- `datasets`
- `code_repositories`
- `baseline_candidates`
- `web_sources`
- `adapter_runs`

### `research_landscape.json`

Structured synthesis.

Required collections:

- `dataset_candidates`
- `frontier_hotspots`
- `domain_difficulties`
- `baseline_candidates`
- `method_gap_matrix`
- `route_candidates`

### `research_brief.md`

Chinese user-facing summary.

Required sections:

- 研究方向理解
- 可用公开数据集
- 近 1 年前沿热点
- 近 3-5 年稳定难点
- 必跑 baseline 和代码资源
- 候选路线 1-3
- 最大风险和下一步建议

## Handoff

This phase hands off only after the user can choose a route. The next phase, `research-design`, consumes `research_landscape.json`, the selected route, and evidence ids.
