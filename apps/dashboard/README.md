# Matrix-AutoLab Dashboard

A plugin-owned, local-first dashboard for visualizing Matrix-AutoLab paper reproduction and model-training workflows.

## Scope

The first version is read-only:

- reads `.autolab/` project and run records
- reads legacy workflow and report files when available
- visualizes workflow state, run history, metrics, failures, and reports
- previews future sync boundaries without uploading anything
- does not start training, mutate records, or contact a server

## Run Locally

From this directory:

```bash
npm install
npm run dev
```

Then open:

```text
http://127.0.0.1:3217
```

If you launch the dashboard from another working directory, set the project root explicitly:

```bash
AUTOLAB_PROJECT_ROOT=/path/to/AutoLab npm run dev
```

## Expected Project Layout

The dashboard resolves the AutoLab project root from the plugin app location and reads:

```text
.autolab/project.json
.autolab/workflow_status.json
.autolab/runs/<run_id>/run.json
.autolab/runs/<run_id>/events.jsonl
```.autolab/runs/<run_id>/metrics.jsonl
.autolab/runs/<run_id>/errors.jsonl
.autolab/runs/<run_id>/artifacts.json
.autolab/runs/<run_id>/changed_files.json
.autolab/runs/<run_id>/reports/reports_index.json
```

It also checks legacy files such as `workflow_status.json`, `experiment_docs/`, and `baselines/`.

## Future Work

- Confirm the final Codex plugin `.app.json` schema for launching local web apps.
- Add server sync as an explicit opt-in flow only after local schemas and consent boundaries are stable.
- Add tests for local readers, JSONL parsing, and sync classification.
