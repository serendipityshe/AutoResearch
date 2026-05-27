#!/usr/bin/env node
"use strict";

const childProcess = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const PLUGIN_NAME = "matrix-autolab";
const COPY_ENTRIES = [".codex-plugin", ".app.json", "skills", "scripts", "apps", "README.md"];
const BLOCKED_NAMES = new Set([
  ".autolab",
  ".git",
  ".hg",
  ".next",
  ".svn",
  ".turbo",
  "__pycache__",
  "build",
  "coverage",
  "dist",
  "lightning_logs",
  "mlruns",
  "node_modules",
  "tensorboard",
  "wandb"
]);
const BLOCKED_EXTENSIONS = new Set([
  ".ckpt",
  ".crt",
  ".key",
  ".log",
  ".onnx",
  ".pem",
  ".pt",
  ".pth",
  ".pyc",
  ".pyo",
  ".safetensors"
]);

function parseArgs(argv) {
  const args = { _: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith("--")) {
      args._.push(value);
      continue;
    }
    const key = value.slice(2);
    if (["target", "codex-home"].includes(key)) {
      const next = argv[index + 1];
      if (!next) throw new Error(`Missing value for --${key}`);
      args[key] = next;
      index += 1;
    } else {
      args[key] = true;
    }
  }
  return args;
}

function usage() {
  return [
    "Matrix-AutoLab Codex plugin installer",
    "",
    "Usage:",
    "  matrix-autolab install [--target <dir>] [--codex-home <dir>] [--force] [--dry-run] [--install-dashboard]",
    "  matrix-autolab doctor",
    "",
    "Defaults:",
    "  --target is $CODEX_PLUGIN_DIR or <codex-home>/plugins/matrix-autolab",
    "  --codex-home is $CODEX_HOME or ~/.codex"
  ].join("\n");
}

function codexHome(args) {
  return path.resolve(args["codex-home"] || process.env.CODEX_HOME || path.join(os.homedir(), ".codex"));
}

function targetDir(args) {
  if (args.target) return path.resolve(args.target);
  if (process.env.CODEX_PLUGIN_DIR) return path.resolve(process.env.CODEX_PLUGIN_DIR);
  return path.join(codexHome(args), "plugins", PLUGIN_NAME);
}

function isBlocked(filePath) {
  const base = path.basename(filePath);
  if (BLOCKED_NAMES.has(base)) return true;
  if (base === ".env" || base.startsWith(".env.")) return true;
  return BLOCKED_EXTENSIONS.has(path.extname(base).toLowerCase());
}

function removeIfExists(target) {
  if (fs.existsSync(target)) fs.rmSync(target, { recursive: true, force: true });
}

function copyRecursive(source, destination, copied) {
  if (isBlocked(source)) return;
  const stat = fs.statSync(source);
  if (stat.isDirectory()) {
    fs.mkdirSync(destination, { recursive: true });
    for (const child of fs.readdirSync(source)) {
      copyRecursive(path.join(source, child), path.join(destination, child), copied);
    }
    return;
  }
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.copyFileSync(source, destination);
  copied.push(path.relative(PACKAGE_ROOT, source).replace(/\\/g, "/"));
}

function requiredFiles() {
  return [
    ".codex-plugin/plugin.json",
    ".app.json",
    "skills/matrix-autolab/SKILL.md",
    "skills/autolab/SKILL.md",
    "skills/autobaseline/SKILL.md",
    "scripts/autolab_gate.py",
    "apps/dashboard/package.json"
  ];
}

function scanBlocked(root) {
  const matches = [];
  function walk(current) {
    if (!fs.existsSync(current)) return;
    if (current !== root && isBlocked(current)) {
      matches.push(path.relative(root, current).replace(/\\/g, "/"));
      return;
    }
    const stat = fs.statSync(current);
    if (!stat.isDirectory()) return;
    for (const child of fs.readdirSync(current)) walk(path.join(current, child));
  }
  for (const entry of COPY_ENTRIES) walk(path.join(root, entry));
  return matches;
}

function isCredentialPath(relativePath) {
  const base = path.basename(relativePath);
  const ext = path.extname(base).toLowerCase();
  return base === ".env" || base.startsWith(".env.") || [".crt", ".key", ".pem"].includes(ext);
}

function doctor() {
  const missing = requiredFiles().filter((file) => !fs.existsSync(path.join(PACKAGE_ROOT, file)));
  const blocked = scanBlocked(PACKAGE_ROOT);
  const credentialLike = blocked.filter(isCredentialPath);
  const ok = missing.length === 0 && credentialLike.length === 0;
  console.log(JSON.stringify({ ok, missing, excludedByInstaller: blocked, credentialLike }, null, 2));
  return ok ? 0 : 1;
}

function install(args) {
  const target = targetDir(args);
  const copied = [];
  if (args["dry-run"]) {
    console.log(JSON.stringify({ dryRun: true, target }, null, 2));
    return 0;
  }
  if (fs.existsSync(target) && !args.force) {
    throw new Error(`Target already exists: ${target}. Re-run with --force to replace it.`);
  }
  removeIfExists(target);
  fs.mkdirSync(target, { recursive: true });
  for (const entry of COPY_ENTRIES) copyRecursive(path.join(PACKAGE_ROOT, entry), path.join(target, entry), copied);
  if (args["install-dashboard"]) {
    const dashboard = path.join(target, "apps", "dashboard");
    const result = childProcess.spawnSync("npm", ["install"], { cwd: dashboard, stdio: "inherit", shell: process.platform === "win32" });
    if (result.status !== 0) return result.status || 1;
  }
  console.log(JSON.stringify({ installed: true, target, copied: copied.length }, null, 2));
  return 0;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const command = args._[0] || "help";
  if (command === "help" || args.help) {
    console.log(usage());
    return 0;
  }
  if (command === "doctor") return doctor();
  if (command === "install") return install(args);
  throw new Error(`Unknown command: ${command}\n\n${usage()}`);
}

try {
  process.exitCode = main();
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
