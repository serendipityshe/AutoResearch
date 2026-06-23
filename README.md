# DreamweaverAI AutoLab

> **从研究想法到论文的全流程科研副驾 —— 不是无情的科研机器,而是科研的辅助伙伴。**
> An auditable **idea → paper** and **paper → experiment** research autopilot. Works as **both** a Codex plugin and a Claude Code plugin from one source tree.

![plugin](https://img.shields.io/badge/plugin-Codex%20%2B%20Claude%20Code-2563EB)
![license](https://img.shields.io/badge/license-MIT--0-green)
![node](https://img.shields.io/badge/node-%E2%89%A518-339933)
![python](https://img.shields.io/badge/python-3.9%2B-3776AB)

DreamweaverAI AutoLab packages a research autopilot, experiment runner, baseline comparison, and a full suite of Nature-style writing skills into a single plugin. Every claim is traced back to real evidence, and every irreversible step is gated behind explicit confirmation — the agent helps you do the research, it does not fabricate a paper for you.

> **Scope / 适用范围:** the first version is focused on the **deep-learning / computer-vision** domain (视觉方向). The writing, search, and experiment-recording layers are general; the experiment lane assumes a code-based ML project.

---

## Highlights

- **Two entry points.** Start from a rough *idea* (`matrix-research-autopilot`) or from an existing *`main.tex`* (`matrix-autolab`).
- **Three-lane architecture.** Discovery → Design → Experimentation → Writing, each with stable artifact contracts.
- **Evidence-gated.** Only `supported` claims reach manuscript prose; unsupported claims are marked `needs_evidence` and excluded.
- **Phase gates with human-in-the-loop.** Each phase produces a report and waits for your confirmation; protocol artifacts (not chat memory) are the source of truth.
- **20 built-in skills** including 9 Nature-style writing skills (prose, figures, citations, data statements, polishing, reviewer responses, paper→PPT, academic search).
- **Local-first dashboard** (Next.js, read-only) to inspect runs, metrics, gates, and reports — never uploads anything.

---

## Install

This repository is itself both the plugin and a single-plugin marketplace.

### Claude Code (plugin marketplace)

```text
/plugin marketplace add serendipityshe/AutoResearch
/plugin install dreamweaverai-autolab@dreamweaverai-autolab
```

Skills are then available namespaced, e.g. `/dreamweaverai-autolab:matrix-research-autopilot`.

To test from a local clone instead:

```text
/plugin marketplace add ./            # run with the repo as the working directory
/plugin install dreamweaverai-autolab@dreamweaverai-autolab
```

### Codex (npm package)

```bash
npm install -g @dreamweaverai/matrix-autolab
matrix-autolab install                 # copies the plugin into your personal Codex marketplace
codex plugin marketplace add %USERPROFILE%
```

Optional flags:

```bash
matrix-autolab install --target /path/to/codex/plugins/matrix-autolab
matrix-autolab install --install-dashboard
```

See [PUBLISHING.md](PUBLISHING.md) for the full Codex flow, and [docs/README.zh-en.md](docs/README.zh-en.md) for the detailed bilingual guide.

---

## Quick start

**From a research idea (中文):**

```text
请使用 matrix-research-autopilot，围绕我的研究 idea 完成文献、代码、数据集和 baseline 搜索，
生成 research_brief.md 和 search_evidence.json。请先给出候选研究路线，等我确认后再生成 main.tex 和实验计划。
```

**From a research idea (English):**

```text
Use matrix-research-autopilot to search papers, code, datasets, and baselines for my idea.
Generate research_brief.md and search_evidence.json first, recommend candidate routes,
and wait for my confirmation before generating main.tex and the experiment plan.
```

**From an existing paper:**

```text
Use matrix-autolab with main.tex to implement the method, train models, run ablations,
and compare baselines. Produce a phase report for each stage and wait for my confirmation.
```

**From results to writing:**

```text
Build writing_packet.md from experiment_matrix.json, result CSVs, phase reports, and
manuscript_claims.json. Then use nature-writing, nature-figure, nature-citation, and
nature-data to prepare English prose, captions, citations, and data statements.
Do not include unsupported claims in final prose.
```

---

## Workflow

```
                 ┌── DISCOVERY ──┐   ┌── DESIGN ──┐   ┌── EXPERIMENTATION ──┐   ┌── WRITING ──┐
   research      hotspot search   →  research      →  PaperBanana figure     →  nature-writing
   idea       →  solution search  →  design        →  AutoLab (9 gated       →  nature-figure
               route judge (gate)    contract +       phases: setup → train     nature-citation
                                     blueprint        → ablate → eval)          nature-data ...
                       │                  │           AutoBaseline (optional)        │
                       ▼                  ▼                    ▼                      ▼
              domain_landscape    research_design    experiment_matrix         supported claims,
              solution_landscape  manuscript_        + result CSVs +           Results/Discussion,
              route_judgement     blueprint          phase reports +           figures, citations,
                                  → main.tex         manuscript_claims         data statements
```

- **Path A — Idea → Paper:** `matrix-research-autopilot` drives Discovery → Design → `main.tex`, then hands off to the experiment lane.
- **Path B — Paper → Experiment:** `matrix-autolab` runs PaperBanana → AutoLab → AutoBaseline from a `main.tex`.

`main.tex` is only generated **after** the research route is confirmed and a valid `research_design.json` exists (formula-bearing modules, losses, dataset roles, ablations) — otherwise `build-main-tex` fails rather than emitting a generic scaffold.

---

## Skills

### Orchestration

| Skill | Purpose |
|---|---|
| `matrix-research-autopilot` | Idea-to-paper controller: discovery evidence → design contract → experiments → writing packet. |
| `matrix-autolab` | Unified PaperBanana → AutoLab → AutoBaseline entry point for paper-to-experiment. |
| `research-discovery` | Backwards-compatible wrapper for legacy `research_landscape.json` generation. |

### Discovery

| Skill | Purpose |
|---|---|
| `research-hotspot-discovery` | Scan recent target-domain papers/datasets/code/baselines → `domain_landscape.json` + problem candidates. |
| `research-solution-discovery` | Find transferable methods for a chosen problem → `solution_landscape.json` (1–3 method options). |
| `research-route-judge` | Independent reviewer of problem–purpose–method fit → `PROCEED` / `REFINE` / `PIVOT` / `STOP_WEAK`. |
| `nature-academic-search` | Multi-source literature search (PubMed, CrossRef, arXiv) and reference-format conversion. |

### Design

| Skill | Purpose |
|---|---|
| `research-design` | Confirmed route → `research_design.json` (method contract) + `manuscript_blueprint.json`. |
| `research-manuscript` | Validated design → English `main.tex` with formal abstract, method math, and citation/audit checks. |

### Experimentation

| Skill | Purpose |
|---|---|
| `paperbanana` | Publication-quality framework/pipeline figures from method text (multi-agent rendering). |
| `autolab` | Implement method, train, ablate, and collect metrics via 9 gated phases. |
| `autobaseline` | Identify, clone, adapt, and benchmark independent SOTA baselines against the AutoLab result. |

### Writing (Nature skills)

| Skill | Purpose |
|---|---|
| `nature-writing` | Draft/rebuild Nature-style sections (abstract, intro, results, discussion) from claims and results. |
| `nature-polishing` | Restructure and polish prose into Nature-leaning English. |
| `nature-figure` | Figure contracts → journal-ready plots (matplotlib / ggplot2) exported to SVG/PDF/TIFF. |
| `nature-citation` | Add strict Nature/CNS citations with reference-manager-ready exports. |
| `nature-data` | Data Availability statements, repository plans, dataset citations, FAIR checklists. |
| `nature-reader` | Bilingual side-by-side full-paper Markdown readers. |
| `nature-response` | Point-by-point reviewer response letters with evidence-based rebuttals. |
| `nature-paper2ppt` | Paper → Chinese PPTX deck with figure selection and speaker notes. |

---

## Dashboard

A local-first, **read-only** Next.js dashboard for inspecting AutoLab runs, metrics, gates, failures, and reports. It reads `.autolab/` records and never starts training, mutates records, or contacts external servers.

```bash
cd apps/dashboard
npm install
npm run dev
# open http://127.0.0.1:3217
```

---

## Repository layout

```
.claude-plugin/        Claude Code manifest + single-plugin marketplace
.codex-plugin/         Codex plugin manifest (interface metadata, default prompts)
skills/                20 skills (orchestration, discovery, design, experimentation, writing)
scripts/               Python orchestration: autolab_run / autolab_gate / research_autopilot / ...
bin/                   matrix-autolab.js — Codex installer / doctor / packager
apps/dashboard/        Next.js read-only run dashboard (port 3217)
docs/                  Architecture docs + bilingual guide + third-party license
.app.json              Codex app descriptor for the dashboard
```

---

## Requirements

- **Node.js ≥ 18** (plugin tooling and dashboard).
- **Python 3.9+** — the orchestration scripts use only the standard library; no `pip install` is required for the research loop. Your own experiment code brings its own ML stack (e.g. PyTorch).
- **Git** for repository detection and metadata.
- **GPU/CUDA** only if you run model training in the experimentation lane.
- Discovery uses the host agent's search/MCP layer (web, GitHub, Hugging Face, arXiv, PubMed, Zotero); no API keys are hardcoded in this repo.

---

## Development & validation

```bash
# Codex package health
npm run doctor
npm run pack:dry-run

# Claude Code plugin / marketplace manifest
claude plugin validate . --strict
```

`doctor` checks the manifest, core scripts, and all built-in skills. `pack:dry-run` confirms the publishable package contents. `claude plugin validate` checks the marketplace schema, source paths, and version consistency.

---

## Documentation

- [docs/README.zh-en.md](docs/README.zh-en.md) — full bilingual user guide.
- [docs/matrix-research-autopilot-architecture.md](docs/matrix-research-autopilot-architecture.md) — autopilot architecture.
- [docs/discovery-experimentation-writing-architecture.md](docs/discovery-experimentation-writing-architecture.md) — three-lane architecture.
- [docs/research-kernel-contract.md](docs/research-kernel-contract.md) — research kernel / artifact contracts.

---

## Third-party notice

The built-in Nature skills are integrated from [`Yuan1z0825/nature-skills`](https://github.com/Yuan1z0825/nature-skills) and redistributed under the MIT license. The license text is kept in [docs/third-party-nature-skills-LICENSE.md](docs/third-party-nature-skills-LICENSE.md).

## License

[MIT-0](https://spdx.org/licenses/MIT-0.html) — Matrix-AutoLab Contributors.
