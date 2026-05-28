# Evidence Schema

Use stable ids so later artifacts can cite evidence without copying full source text.

## Common Fields

Every evidence item should include:

- `id`
- `source_adapter`
- `title` or `name`
- at least one locator: `url`, `doi`, `pmid`, `pmcid`, `arxiv_id`, `paper_or_repo_url`, `local_path`, `citation_key`, `hf_dataset_id`, `figshare_doi`, or `zenodo_doi`
- `why_relevant`
- `limitations`

## Paper Fields

Recommended:

- `year`
- `venue`
- `authors`
- `abstract_summary`
- `task`
- `method_family`
- `evidence_summary`
- `claim_status`

## Dataset Fields

Required:

- `name`
- `task`
- `reported_size`
- `label_type`
- `access_status`
- `license`
- `candidate_roles`
- `recent_usage`
- `risk_notes`

`candidate_roles` can include `primary`, `validation`, `external_test`, or `supplementary`.

## Code Repository Fields

Required:

- `name`
- `url`
- `repo_role`
- `official_status`
- `license`
- `train_entrypoints`
- `eval_entrypoints`
- `dataset_support`
- `maintenance_status`
- `reproducibility_risk`

## Baseline Fields

Required:

- `name`
- `baseline_type`
- `why_required`
- `expected_comparison_role`
- `source_ids`

## Landscape Fields

`frontier_hotspots`:

- `time_window`
- `hotspot`
- `why_now`
- `evidence_ids`
- `signal_strength`

`domain_difficulties`:

- `time_window`
- `difficulty`
- `experiment_impact`
- `evidence_ids`

`route_candidates`:

- `route_id`
- `name`
- `core_claim`
- `dataset_requirements`
- `method_direction`
- `baseline_requirements`
- `evidence_ids`
- `failure_risks`
- `recommendation`
