# Matrix-AutoLab Plugin

Matrix-AutoLab is a Codex-style plugin for paper-to-experiment workflows. It packages coordinated skills, local recording scripts, and a local-first dashboard app.

This repository is laid out as the npm package root for:

```text
@dreamweaverai/matrix-autolab
```

## What It Includes

- `matrix-autolab`: unified entry point for the full workflow
- `paperbanana`: framework figure generation from paper methodology
- `autolab`: method implementation, training, evaluation, and ablations
- `autobaseline`: SOTA baseline training and comparison
- `scripts/`: local `.autolab/` recording utilities
- `apps/dashboard`: read-only local dashboard for workflow, runs, metrics, failures, reports, artifacts, and sync readiness

## Install From npm

Install the package and copy the plugin into the local Codex plugin directory:

```bash
npm install -g @dreamweaverai/matrix-autolab
matrix-autolab install
```

Use a custom destination when needed:

```bash
matrix-autolab install --target /path/to/codex/plugins/matrix-autolab
```

Install dashboard dependencies during plugin installation:

```bash
matrix-autolab install --install-dashboard
```

## Recommended Prompt

```text
根据 main.tex 帮我完成论文方法实现、训练和相关消融实验。请按阶段推进，每个阶段生成报告并等待我确认。
```

## Anti-Skip Control Plane

Long paper-reproduction runs must be driven by local gate files, not only by chat memory or checklist prose. Each run created by `start-run` initializes:

- `.autolab/runs/<run_id>/phase_plan.json`: strict sequential phase map
- `.autolab/runs/<run_id>/requirements.json`: paper and experiment requirements with evidence
- `.autolab/runs/<run_id>/gate_status.json`: the single current executable step

Before work starts on a phase or substep, declare the gate:

```bash
python scripts/autolab_gate.py start-step --run-id <run_id> --phase phase_4_modules --step module_name --requirement method.module_name --required-artifact experiment_docs/reports/phase_4_modules_report.md --check "implementation, smoke test, and report evidence are present" --user-confirmation-required
```

Before completing that step, run:

```bash
python scripts/autolab_gate.py check-step --run-id <run_id>
```

If the gate reports blockers, stop and resolve them instead of moving forward. Use `define-requirement` and `add-evidence` to map paper details to concrete files, commands, tests, reports, and metrics.

## Package Structure

```text
matrix-autolab/
  .codex-plugin/plugin.json
  .app.json
  apps/dashboard/
  bin/
  scripts/
  skills/
  package.json
  PUBLISHING.md
  README.md
```

## Development

Run a package health check:

```bash
npm run doctor
```

Review package contents before publishing:

```bash
npm run pack:dry-run
```

The npm package uses a `files` whitelist and `.npmignore` denylist so local experiment records, logs, dependencies, build output, credentials, checkpoints, and model weights are not published.

## Local Dashboard

From `apps/dashboard`:

```bash
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:3217
```

The dashboard is local-first and read-only in the first version. It does not upload data or mutate experiment records.

## Local Recording

Initialize local project records from the project root:

```bash
python scripts/autolab_run.py init-project
```

Start a run:

```bash
python scripts/autolab_run.py start-run --kind paper_reproduction --entry-skill matrix-autolab
```

Record events, metrics, errors, artifacts, reports, and changed files with the scripts in `scripts/`.

## Source Control

This repository should track the plugin package source directly from the repository root. Do not commit generated or local-only files such as:

```text
node_modules/
.next/
.turbo/
dist/
build/
.autolab/
runs/
outputs/
logs/
.env
*.ckpt
*.pt
*.pth
*.onnx
*.safetensors
```
