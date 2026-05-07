# Publishing Matrix-AutoLab

## Safety Model

The npm package is a distribution wrapper for the Codex plugin. It should contain reusable plugin code only, never user experiment data.

The package uses two layers of protection:

- `package.json` `files`: whitelist of publishable paths
- `.npmignore`: denylist for dependencies, build output, credentials, logs, checkpoints, and local run records

## Before Publishing

Run:

```bash
npm run doctor
npm run pack:dry-run
```

Review the `npm pack --dry-run` file list. It must not include:

- `.autolab/`
- `.env` or `.env.*`
- `node_modules/`
- `.next/`
- training logs or reports from a user project
- datasets, checkpoints, model weights, or prediction outputs
- personal paths, API keys, tokens, or provider credentials

## Package Name

The default package name is:

```text
@dreamweaverai/matrix-autolab
```

Change this before publishing if you use a different npm scope.

## Install Flow

Users install and copy the plugin locally:

```bash
npm install -g @dreamweaverai/matrix-autolab
matrix-autolab install
```

Optional:

```bash
matrix-autolab install --target /path/to/codex/plugins/matrix-autolab
matrix-autolab install --install-dashboard
```
