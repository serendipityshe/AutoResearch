# Matrix-AutoLab Local Recording Design

Date: 2026-04-25
Status: Draft for review

## Goal

Add a local `.autolab/` recording layer to Matrix-AutoLab so paper reproduction, ablation, and baseline runs leave structured, reusable records. The records should support later server sync and web dashboards, but this phase only implements local files and plugin-side utilities.

The recording layer is not a real-time monitoring system. It is a durable experiment journal for success, failure, configuration, metrics, artifacts, reports, and code changes.

## Non-Goals

- No web UI in this phase.
- No server API or remote sync in this phase.
- No database in this phase.
- No mandatory copying of large checkpoints, prediction images, or full training logs into `.autolab/`.
- No wholesale migration of existing `experiment_docs/`, `baselines/`, or root `workflow_status.json` behavior in this phase.
- No hooks until the data model and script behavior are stable.

## Directory Layout

Each project using Matrix-AutoLab can contain:

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

`<run_id>` should be stable and sortable. Use UTC timestamp plus a short suffix:

```text
20260425T153012Z-a1b2c3
```

## Recording Principles

`.autolab/` stores lightweight structured data and indexes. Large files stay where the training code writes them, unless a later user explicitly requests archival copying.

Large artifacts are recorded with:

- path
- type
- size if available
- hash if cheap and reasonable to compute
- producing phase or command
- description

This applies to checkpoints, full logs, prediction images, generated figures, and exported reports.

## Project Metadata

`.autolab/project.json` describes the project rather than a single run.

Required fields:

```json
{
  "schema_version": "0.1.0",
  "project_id": "string",
  "name": "string",
  "paper_source": "main.tex",
  "task_type": "unknown",
  "dataset": {
    "name": "",
    "path": ""
  },
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

`task_type` may be `unknown` until the paper has been parsed. Scripts should not fail only because metadata is incomplete.

## Workflow Status

`.autolab/workflow_status.json` is the plugin-local successor to root `workflow_status.json`.

It should track the four plugin entries:

- `matrix-autolab`
- `paperbanana`
- `autolab`
- `autobaseline`

Minimum shape:

```json
{
  "schema_version": "0.1.0",
  "project_id": "string",
  "active_run_id": "string",
  "skills": {
    "paperbanana": {
      "status": "pending",
      "user_confirmed": false,
      "current_phase": "",
      "report": "",
      "updated_at": ""
    },
    "autolab": {
      "status": "pending",
      "user_confirmed": false,
      "current_phase": "",
      "report": "",
      "updated_at": ""
    },
    "autobaseline": {
      "status": "pending",
      "user_confirmed": false,
      "current_phase": "",
      "report": "",
      "updated_at": ""
    }
  }
}
```

Allowed status values:

- `pending`
- `in_progress`
- `blocked`
- `failed`
- `completed`
- `skipped`

Existing root-level status files remain readable for compatibility. New script writes should prefer `.autolab/workflow_status.json`.

## Run Metadata

`.autolab/runs/<run_id>/run.json` describes one experiment attempt.

Required fields:

```json
{
  "schema_version": "0.1.0",
  "run_id": "20260425T153012Z-a1b2c3",
  "project_id": "string",
  "kind": "paper_reproduction",
  "status": "in_progress",
  "started_at": "ISO-8601",
  "ended_at": "",
  "entry_skill": "matrix-autolab",
  "paper_source": "main.tex",
  "git": {
    "commit": "",
    "branch": "",
    "dirty": true
  },
  "summary": ""
}
```

Allowed `kind` values:

- `paper_reproduction`
- `figure_generation`
- `method_implementation`
- `ablation`
- `baseline_comparison`
- `inspection`

Allowed run status values:

- `in_progress`
- `blocked`
- `failed`
- `completed`
- `aborted`

## Configuration Snapshot

`.autolab/runs/<run_id>/config.json` stores the reproducibility snapshot known at run time.

Important fields:

- dataset path and split
- seed
- model and backbone
- input resolution
- optimizer
- scheduler
- learning rate
- batch size
- epoch budget
- loss components and weights
- augmentation summary
- pretrained weights path
- environment summary

The first implementation may create an incomplete snapshot and update it as phases discover more information.

## Events

`.autolab/runs/<run_id>/events.jsonl` is append-only. Each line is one JSON object.

Minimum event:

```json
{
  "timestamp": "ISO-8601",
  "level": "info",
  "skill": "autolab",
  "phase": "phase_4_modules",
  "event_type": "phase_started",
  "message": "Phase 4 started",
  "data": {}
}
```

Allowed `event_type` should include:

- `run_created`
- `run_status_changed`
- `phase_started`
- `phase_completed`
- `phase_failed`
- `user_confirmation_requested`
- `user_confirmed`
- `report_recorded`
- `artifact_recorded`
- `metric_recorded`
- `command_recorded`

## Metrics

`.autolab/runs/<run_id>/metrics.jsonl` is append-only and stores training or evaluation metrics.

Minimum metric:

```json
{
  "timestamp": "ISO-8601",
  "source": "train_log",
  "phase": "phase_6_short_train",
  "step": 120,
  "epoch": 3,
  "split": "val",
  "name": "mIoU",
  "value": 0.734,
  "unit": "",
  "context": {
    "class_name": "",
    "run_config": "default"
  }
}
```

Metrics should support:

- loss curves
- learning rate
- validation metrics
- test metrics
- per-class metrics
- runtime and memory summaries

## Errors

`.autolab/runs/<run_id>/errors.jsonl` records failures and diagnoses.

Minimum error:

```json
{
  "timestamp": "ISO-8601",
  "skill": "autolab",
  "phase": "phase_6_short_train",
  "severity": "error",
  "category": "nan_loss",
  "message": "Loss became NaN during short training",
  "command": "",
  "log_excerpt": "",
  "suggested_next_step": ""
}
```

Expected categories:

- `oom`
- `nan_loss`
- `process_crash`
- `data_path`
- `label_mapping`
- `checkpoint_mismatch`
- `metric_regression`
- `dependency`
- `unknown`

## Artifacts

`.autolab/runs/<run_id>/artifacts.json` indexes files produced or used by a run.

Artifact examples:

- checkpoint
- training log
- evaluation report
- generated figure
- prediction visualization
- config file
- phase report

Minimum artifact:

```json
{
  "artifacts": [
    {
      "id": "best_checkpoint",
      "type": "checkpoint",
      "path": "outputs/checkpoints/best.pth",
      "exists": true,
      "size_bytes": 123456,
      "sha256": "",
      "phase": "phase_8_eval",
      "description": "Best checkpoint selected by validation metric"
    }
  ]
}
```

Hashes may be omitted for large files unless explicitly requested.

## Changed Files

`.autolab/runs/<run_id>/changed_files.json` records code changes associated with the run.

Minimum shape:

```json
{
  "captured_at": "ISO-8601",
  "git": {
    "commit": "",
    "branch": "",
    "dirty": true
  },
  "files": [
    {
      "path": "models/module.py",
      "status": "modified",
      "summary": ""
    }
  ]
}
```

The first implementation should collect `git status --short` and basic file status. Diff summaries can be added later.

## Reports

`.autolab/runs/<run_id>/reports/reports_index.json` indexes reports rather than duplicating every report immediately.

Minimum report entry:

```json
{
  "reports": [
    {
      "type": "phase_report",
      "phase": "phase_3_baseline_audit",
      "path": "experiment_docs/reports/phase_3_baseline_audit_report.md",
      "title": "Baseline Audit",
      "created_at": ""
    }
  ]
}
```

Later versions may copy small markdown reports into `.autolab/runs/<run_id>/reports/` for portability.

## Scripts

Add plugin-local utilities under:

```text
plugins/matrix-autolab/scripts/
  autolab_run.py
  autolab_event.py
  autolab_collect.py
```

### `autolab_run.py`

Responsibilities:

- initialize `.autolab/`
- create a run
- update run status
- show current status

Expected commands:

```bash
python3 plugins/matrix-autolab/scripts/autolab_run.py init-project
python3 plugins/matrix-autolab/scripts/autolab_run.py start-run --kind ablation --entry-skill autolab
python3 plugins/matrix-autolab/scripts/autolab_run.py finish-run --run-id <run_id> --status completed
python3 plugins/matrix-autolab/scripts/autolab_run.py status
```

### `autolab_event.py`

Responsibilities:

- append events
- append metrics
- append errors

Expected commands:

```bash
python3 plugins/matrix-autolab/scripts/autolab_event.py event --run-id <run_id> --type phase_started --skill autolab --phase phase_4_modules --message "Phase 4 started"
python3 plugins/matrix-autolab/scripts/autolab_event.py metric --run-id <run_id> --name mIoU --value 0.734 --split val --epoch 3
python3 plugins/matrix-autolab/scripts/autolab_event.py error --run-id <run_id> --category oom --message "CUDA out of memory"
```

### `autolab_collect.py`

Responsibilities:

- collect artifact indexes
- collect report indexes
- collect changed file status

Expected commands:

```bash
python3 plugins/matrix-autolab/scripts/autolab_collect.py changed-files --run-id <run_id>
python3 plugins/matrix-autolab/scripts/autolab_collect.py artifact --run-id <run_id> --type checkpoint --path outputs/best.pth --id best_checkpoint
python3 plugins/matrix-autolab/scripts/autolab_collect.py report --run-id <run_id> --type phase_report --phase phase_3_baseline_audit --path experiment_docs/reports/phase_3_baseline_audit_report.md
```

## Matrix-AutoLab Skill Update

Update the `matrix-autolab` skill to:

1. Prefer `.autolab/workflow_status.json` when present.
2. Fall back to legacy files:
   - `workflow_status.json`
   - `experiment_docs/progress.json`
   - `baselines/progress.json`
3. Tell the user whether the project has local recording initialized.
4. Recommend initializing `.autolab/` before new runs.
5. Avoid requiring `.autolab/` for reading old projects.

Specialized skills should not be fully rewritten in this phase. They can mention the recording utilities as optional commands, but their phase-gated behavior stays intact.

## Future Hooks

Hooks are intentionally deferred. Once scripts are stable, hooks can call them automatically for:

- run start and end
- command execution summaries
- phase report creation
- failure capture
- changed file capture
- optional sync scheduling

## Testing Strategy

Use focused tests for the scripts:

- initialize a temporary project
- create a run
- append one event, metric, and error
- record one artifact and one report
- collect changed files in a git repository
- validate all generated JSON and JSONL files parse
- verify repeated commands are idempotent where expected

Manual verification:

- run `python3 -m json.tool` on JSON files
- parse JSONL line by line with Python
- confirm legacy project files are still only read, not moved

## Open Decisions

No blocking open decisions remain for this phase. The exact server sync API, web UI shape, hook behavior, and artifact copying policy are intentionally reserved for later phases.
