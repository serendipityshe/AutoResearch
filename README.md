# DreamweaverAI AutoLab Plugin

DreamweaverAI AutoLab is a Codex-style plugin for idea-to-paper and paper-to-experiment workflows. It packages coordinated skills, adapter-based research discovery protocols, local recording scripts, and a local-first dashboard app.

This repository is laid out as the npm package root for:

```text
@dreamweaverai/matrix-autolab
```

## What It Includes

- `matrix-research-autopilot`: idea-to-paper research workflow for graduate students and researchers
- `matrix-autolab`: unified entry point for the full workflow
- `paperbanana`: framework figure generation from paper methodology
- `autolab`: method implementation, training, evaluation, and ablations
- `autobaseline`: SOTA baseline training and comparison
- `scripts/research_autopilot.py`: Research Discovery Layer adapter registry, protocol artifact initialization, evidence validation, and writing packet construction
- `scripts/`: local `.autolab/` recording utilities
- `apps/dashboard`: read-only local dashboard for workflow, runs, metrics, failures, reports, artifacts, and sync readiness

## Install From npm

Install the package, copy the plugin into the local personal plugin directory, and update the
personal marketplace file:

```bash
npm install -g @dreamweaverai/matrix-autolab
matrix-autolab install
```

Use a custom destination when needed:

```bash
matrix-autolab install --target /path/to/codex/plugins/matrix-autolab
```

By default, local development installs to:

```text
~/plugins/dreamweaverai-autolab
```

and updates:

```text
~/.agents/plugins/marketplace.json
```

Register the personal marketplace with the current Codex CLI:

```bash
codex plugin marketplace add %USERPROFILE%
```

Then enable `dreamweaverai-autolab@personal` in the Codex app plugin UI. If the UI is not available
in the current build, add this block to `~/.codex/config.toml`:

```toml
[plugins."dreamweaverai-autolab@personal"]
enabled = true
```

Start a new Codex thread after enabling it so new skills are loaded.

Install dashboard dependencies during plugin installation:

```bash
matrix-autolab install --install-dashboard
```

## Recommended Prompt

Start from a research idea:

```text
我有一个医学 AI 研究想法，请使用 matrix-research-autopilot 帮我完成文献/代码/数据集搜索、研究路线推荐、实验计划、服务器实验和 Nature 风格写作准备。请每个阶段生成可审计证据并等待我确认。
```

Start from an existing paper source:

```text
根据 main.tex 帮我完成论文方法实现、训练和相关消融实验。请按阶段推进，每个阶段生成报告并等待我确认。
```

## Idea-To-Paper Workflow

`matrix-research-autopilot` is the recommended entry point when a researcher starts with a rough idea instead of a ready `main.tex`. It uses a protocol-checked Research Discovery Layer rather than a hard runtime dependency on `ml-intern`.

The Discovery Layer has six logical adapters:

```text
Research Discovery Layer
├─ Web search adapter
├─ GitHub adapter
├─ Hugging Face adapter
├─ arXiv / Semantic Scholar adapter
├─ PubMed adapter
└─ Zotero adapter
```

Adapters can be backed by Codex web search, GitHub MCP, Hugging Face MCP, arXiv/Semantic Scholar MCP, PubMed search, Zotero, user-provided sources, or extracted modules from another agent. The normalized output is always `search_evidence.json`.

The first-version workflow is:

```text
research idea
-> Research Discovery Layer adapter search
-> research_brief.md and search_evidence.json
-> user-confirmed research route
-> main.tex or experiment-first manuscript scaffold
-> matrix-autolab server execution
-> ablations and baseline comparison
-> manuscript_claims.json and writing_packet.md
-> nature-skills writing, figures, citations, and data statements
```

The key rule is evidence-gated writing: every manuscript claim, result figure, and baseline statement must link back to a real report, metric, log, code path, source, or citation. Unsupported claims are marked `needs_evidence` and must not enter final manuscript prose.

Useful protocol commands:

```bash
python scripts/research_autopilot.py list-adapters
python scripts/research_autopilot.py init-artifacts --query "my research idea"
python scripts/research_autopilot.py validate-search-evidence
python scripts/research_autopilot.py build-main-tex --template "D:/DreamweaverAI/test/main.tex" --topic "my confirmed research topic"
python scripts/research_autopilot.py build-writing-packet --argument "confirmed research argument"
python scripts/research_autopilot.py validate-claims
```

When a user supplies a `main.tex` as a template, Matrix Research Autopilot treats it as style and structure only. The generated manuscript scaffold must not copy the template paper's content, methods, datasets, claims, citations, or results.

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
dreamweaverai-autolab/
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

For idea-to-paper runs:

```bash
python scripts/autolab_run.py start-run --kind idea_to_paper --entry-skill matrix-research-autopilot
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
