# AutoLab

AutoLab is the source repository for the `@dreamweaverai/matrix-autolab` npm package. The package distributes a Codex-style plugin for paper-to-experiment workflows, including coordinated skills, local recording scripts, and a read-only dashboard.

## Package

The published npm package is:

```text
@dreamweaverai/matrix-autolab
```

Current package source lives under:

```text
plugins/matrix-autolab/
```

The dashboard package under `plugins/matrix-autolab/apps/dashboard` is private and is bundled as part of the plugin package. It is not published as a separate npm package.

## What It Includes

- `matrix-autolab`: unified entry point for the full workflow
- `paperbanana`: framework figure generation from paper methodology
- `autolab`: method implementation, training, evaluation, and ablations
- `autobaseline`: SOTA baseline training and comparison
- `scripts/`: local `.autolab/` recording utilities
- `apps/dashboard`: local-first read-only dashboard for runs, metrics, reports, artifacts, and sync readiness

## Install From npm

Install the published package globally:

```bash
npm install -g @dreamweaverai/matrix-autolab
```

Copy the plugin into the local Codex plugin directory:

```bash
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

## Use In a Project

Start from a research project that contains a paper source such as `main.tex` and the baseline code or dataset you want to reproduce against.

Recommended prompt:

```text
根据 main.tex 帮我完成论文方法实现、训练和相关消融实验。请按阶段推进，每个阶段生成报告并等待我确认。
```

AutoLab records local workflow state under `.autolab/` in the target research project. That directory is local experiment state and should not be committed to this source repository.

## Local Dashboard

From the dashboard directory:

```bash
cd plugins/matrix-autolab/apps/dashboard
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:3217
```

The dashboard is local-first and read-only. It does not upload data or mutate experiment records.

## Development

Work on the package from:

```bash
cd plugins/matrix-autolab
```

Run the plugin health check:

```bash
npm run doctor
```

Review the package contents before publishing:

```bash
npm run pack:dry-run
```

The package uses a `files` whitelist in `package.json` and a `.npmignore` denylist so local experiment records, dependencies, build output, credentials, checkpoints, and model weights are not published.

## Source Control

Track these source files:

```text
.gitignore
README.md
plugins/matrix-autolab/
```

Do not commit generated or local-only files:

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

## Repository Layout

```text
AutoLab/
  .gitignore
  README.md
  plugins/
    matrix-autolab/
      .codex-plugin/
      apps/dashboard/
      bin/
      scripts/
      skills/
      package.json
      PUBLISHING.md
      README.md
```

## Publishing

Before publishing, run:

```bash
cd plugins/matrix-autolab
npm run doctor
npm run pack:dry-run
```

Check that the package does not include local experiment records, credentials, dependency directories, build output, datasets, checkpoints, model weights, logs, or personal machine paths.

Publishing notes are maintained in:

```text
plugins/matrix-autolab/PUBLISHING.md
```

## License

The npm package is declared as `MIT-0` in `plugins/matrix-autolab/package.json`.
