# Publishing Matrix-AutoLab

This repository ships as **both a Codex plugin and a Claude Code plugin** from one source tree. The two platforms read separate manifests and never conflict:

- Codex reads `.codex-plugin/plugin.json` (distributed as the npm package below).
- Claude Code reads `.claude-plugin/plugin.json` and installs through the `.claude-plugin/marketplace.json` catalog (see [Claude Code (Plugin Marketplace)](#claude-code-plugin-marketplace)).

Both share the same `skills/` directory, so a skill change ships to both platforms at once.

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

## Claude Code (Plugin Marketplace)

For Claude Code, the repository itself is the plugin **and** a single-plugin marketplace. No npm step is involved — Claude Code clones the repo directly.

### Validate before publishing

```bash
claude plugin validate . --strict
```

This checks `marketplace.json` schema, source path traversal, and version consistency against `plugin.json`. `--strict` treats warnings as errors.

### Install flow

Once the repo is pushed to GitHub, users add the marketplace and install the plugin:

```text
/plugin marketplace add serendipityshe/AutoResearch
/plugin install dreamweaverai-autolab@dreamweaverai-autolab
```

Test locally before pushing:

```text
/plugin marketplace add ./
/plugin install dreamweaverai-autolab@dreamweaverai-autolab
```

### Notes

- `marketplace.json` uses `"source": "./"` (the plugin lives at the repo root). Relative-path sources only resolve when the marketplace is added via git (GitHub / git URL), not via a direct URL to `marketplace.json`. For URL-based distribution, switch the entry to a `github` source instead.
- Version is read from `.claude-plugin/plugin.json`. Bump `version` there on each release, or omit it to let every commit count as a new version. Do not also set `version` in the marketplace entry — the `plugin.json` value always wins.
- The `apps/dashboard` app is a Codex-only integration; Claude Code does not auto-mount it. Run it manually with `cd apps/dashboard && npm run dev` if needed.
