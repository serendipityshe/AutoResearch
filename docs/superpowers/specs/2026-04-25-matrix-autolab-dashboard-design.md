# Matrix-AutoLab Plugin Dashboard Design

Date: 2026-04-25 Status: Draft for review

## Goal

Add a plugin-owned local dashboard to Matrix-AutoLab so users can visualize paper reproduction, method implementation, ablation, baseline comparison, training metrics, failures, reports, artifacts, and future sync readiness from the same plugin they install in Codex-style environments.

The dashboard should make AutoLab feel like an experiment flight recorder: every successful result, failed attempt, training curve, phase report, artifact, and code-change summary becomes durable research memory.

## Product Positioning

Matrix-AutoLab is a model-training and paper-reproduction workflow assistant. Its most valuable output is not only the final metric, but the full experiment trace:

- what paper or method was attempted
- what phases were completed or blocked
- what implementation changes were made
- what metrics improved, degraded, or failed to converge
- what errors happened and how they were resolved
- what reports, figures, checkpoints, and configs were produced
- which negative results are useful for future training or research decisions

The first dashboard version is local-first and read-only. It should prepare the product for later server sync without making upload mandatory.

## Non-Goals For The First Version

- No default server upload.
- No login or remote account system.
- No cloud database dependency.
- No direct training launch from the UI.
- No mutation of `.autolab/` records from the UI.
- No checkpoint, dataset, or full-log copying.
- No source-code upload.
- No replacement of the existing skill workflow or phase gates.

## Plugin Placement

The dashboard should live inside the existing plugin instead of a repo-level standalone app.

Recommended layout:

```text
plugins/matrix-autolab/
  .codex-plugin/
    plugin.json
  .app.json
apps/ dashboard/ app/ components/ lib/ package.json [README.md](http://README.md)scripts/ autolab_common.py autolab_run.py autolab_event.py autolab_collect.py skills/

```
    matrix-autolab/
    paperbanana/
    autolab/
    autobaseline/
```

Rationale:

- Users install one plugin and get skills plus visualization.
- Dashboard can share the plugin vocabulary and `.autolab/` schema.- The plugin can later expose server sync without splitting product ownership.
- `.app.json` is already present and can become the dashboard registration point.

## Recommended Frontend Stack

- Next.js with TypeScript.
- Tailwind CSS for design tokens and layout.
- shadcn/ui-compatible components for durable primitives.
- Recharts or a similar lightweight chart layer for metric curves.
- Node-side local file readers for `.autolab/`, legacy status files, and reports.

The UI should keep client components small. Local data loading should be implemented through server-side functions or local API routes, not browser-side direct file access.

## Visual Direction

The interface should avoid generic admin dashboards. It should feel like a research control room and experiment recorder.

Design principles:

- Workflow-first layout instead of card-only dashboards.
- Equal visibility for successful and failed runs.
- Clear phase state colors: pending, in progress, blocked, failed, completed, skipped.
- Dense but readable metric panels for training curves.
- Report and artifact surfaces that make evidence easy to inspect.
- A future sync panel that builds user trust through explicit data classification.

Suggested palette:

- Research blue for active workflow state.
- Data green for confirmed improvement or completed runs.
- Amber for blocked or needs-review states.
- Red for failed states.
- Graphite neutrals for the main interface.

## Information Architecture

### 1. Project Overview

Purpose: show the current project and the full AutoLab workflow state.

Primary content:

- project name, project id, paper source, task type, dataset summary
- active run id and status
- plugin skill status for matrix-autolab, paperbanana, autolab, autobaseline
- workflow map from PaperBanana to AutoLab phases to AutoBaseline
- latest events, latest failures, latest metrics
- compatibility status for legacy files
- recommended next action, displayed as guidance only

### 2. Run History

Purpose: compare and inspect all local experiment attempts.

Primary content:

- run id
- kind
- status
- entry skill
- start and end time
- git branch, commit, dirty state
- summary
- counts for events, metrics, errors, artifacts, and reports

### 3. Run Detail

Purpose: show one run as a complete experiment trace.

Primary content:

- run metadata
- phase timeline
- event stream
- metric charts
- error ledger
- artifact index
- report index
- changed files
- reproducibility snapshot from config.json

### 4. Metrics Console

Purpose: make training and comparison data useful even when results are negative.

Primary content:

- loss curves
- validation and test metrics
- baseline-vs-method comparisons
- ablation comparisons
- run overlays
- filters by phase, split, source, metric name, and status

### 5. Report Library

Purpose: centralize generated markdown evidence.

Primary content:

- paperbanana completion reports
- AutoLab phase reports
- implementation summary
- baseline comparison report
- linked artifacts and figures
- markdown preview

### 6. Failure Ledger

Purpose: treat failures as reusable research data.

Primary content:

- error severity and category
- failed phase
- command text if available
- log excerpt
- suggested next step
- linked event and run
- whether later runs recovered from a similar failure

### 7. Sync Readiness

Purpose: prepare later server upload without uploading in the first version.

Primary content:

- local-only fields
- safe-to-sync structured fields
- sensitive fields requiring review
- candidate payload preview
- estimated record count and payload size
- reasons certain fields are excluded

## Data Sources

Primary local-first source:

```text
.autolab/
  project.json
  workflow_status.json
  runs/
    <run_id>/
      run.json
      config.json
      events.jsonl
      metrics.jsonl
      errors.jsonl
      artifacts.json
      changed_files.json
      reports/
        reports_index.json
```

Legacy compatibility sources:

```text
workflow_status.json
paperbanana_completion_report.md
experiment_docs/progress.json
experiment_docs/reports/phase_*.md
experiment_docs/IMPLEMENTATION_SUMMARY.md
baselines/progress.json
baselines/BASELINE_COMPARISON_REPORT.md
```

The dashboard should show a useful empty state when `.autolab/` does not exist and explain how to initialize local recording.

## Frontend Data Model

The UI should not bind directly to raw files. It should normalize local and legacy records into stable view models:

```text
ProjectSummary
WorkflowStatusView
SkillStatusView
RunSummary
RunDetail
PhaseStatusView
EventRecordView
MetricPointView
ErrorRecordView
ArtifactRecordView
ReportRecordView
ChangedFileRecordView
SyncCandidateView
```

This adapter layer is important because server sync can later reuse the same models while replacing the data source.

## Local Reader Design

Recommended modules:

```text
apps/dashboard/lib/paths.ts
apps/dashboard/lib/json.ts
apps/dashboard/lib/jsonl.ts
apps/dashboard/lib/autolab-reader.ts
apps/dashboard/lib/legacy-reader.ts
apps/dashboard/lib/view-models.ts
apps/dashboard/lib/sync-classifier.ts
```

Reader behavior:

- tolerate missing files
- return empty arrays instead of throwing for optional records
- surface malformed JSON as dashboard warnings
- never read outside the configured project root
- keep absolute local paths out of sync candidate payloads by default
- avoid loading very large logs or binary artifacts into memory

## Sync Classification

The dashboard should classify data before any future upload feature exists.

### Local Only By Default

- absolute local paths
- source code contents
- full training logs
- checkpoint files
- datasets
- environment variables
- API keys or secrets
- private config values

### Optional After Review

- code diff summaries
- report bodies
- paper method summaries
- model architecture descriptions
- log excerpts
- artifact metadata

### Good Structured Sync Candidates

- project metadata without local paths
- run metadata
- phase statuses
- metric points
- error categories
- training duration
- environment summary without secrets
- baseline names
- ablation names
- final metrics

### High-Value Training Data Requiring Consent

- agent decisions and corrections
- failed attempt to fix pairings
- innovation idea to result pairings
- baseline versus method comparison summaries
- user confirmations and rejections
- phase report summaries

## Future Server Direction

The future remote platform should be opt-in and field-aware.

Suggested server entities:

```text
User
Workspace
Project
Run
Phase
Metric
Event
Error
ArtifactMetadata
ReportSummary
SyncAuditLog
```

Suggested first sync endpoints:

```text
POST /api/projects
POST /api/runs
POST /api/runs/{run_id}/metrics
POST /api/runs/{run_id}/events
POST /api/runs/{run_id}/errors
POST /api/runs/{run_id}/reports
```

The first remote sync implementation should upload structured metadata only. Source code, datasets, checkpoints, and full logs should stay local unless explicitly selected by the user and covered by policy.

## MVP Implementation Plan

### Phase 1: Plugin Dashboard Skeleton

- Create `plugins/matrix-autolab/apps/dashboard`.
- Add Next.js, TypeScript, Tailwind, and UI primitives.
- Add global layout, navigation, and dashboard shell.
- Register the dashboard through `.app.json` when the plugin app mechanism is confirmed.

### Phase 2: Local Read-Only Data Adapter

- Implement `.autolab/` readers.
- Implement JSONL parsing.
- Implement legacy status readers.
- Add empty, loading, warning, and malformed-data states.

### Phase 3: Core Views

- Project overview.
- Workflow map.
- Run history.
- Run detail timeline.
- Metrics console.
- Report library.
- Failure ledger.

### Phase 4: Sync Readiness Preview

- Implement field classification.
- Show local-only, optional, and safe sync candidates.
- Preview a future sync payload without sending it.
- Add clear explanations for excluded data.

### Phase 5: Server Sync MVP Later

- Add explicit user opt-in.
- Add authentication or API token handling.
- Add sync status records.
- Upload structured metadata only.
- Keep server sync independent from local workflow completion.

## Validation Strategy

- Unit test local readers with missing and malformed files.
- Unit test JSONL parsing with partial bad lines.
- Unit test sync classification so sensitive fields are excluded by default.
- Add fixture runs under a test fixture directory, not under real `.autolab/`.
- Manually test empty project, legacy-only project, and `.autolab/` project states.

## Open Questions

- What exact `.app.json` shape does the Codex plugin app runner expect for local web apps?
- Should the dashboard be launched by the plugin runtime or documented as a local dev command first?
- Should a minimal SQLite cache be introduced later for faster search across many runs?
- What server-side consent model is required before collecting data for training or business use?
- Which report fields should be summarized locally before upload?

## Recommended First Build

Start with a read-only plugin dashboard that runs locally, reads `.autolab/` plus legacy files, and visualizes workflow state, run history, run details, metrics, failures, and reports. Add sync readiness as a preview only. Defer actual server upload until the local data model and consent boundaries are stable.
