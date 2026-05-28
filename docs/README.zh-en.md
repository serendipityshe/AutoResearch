# DreamweaverAI AutoLab Plugin

## 中文说明

DreamweaverAI AutoLab 是一个面向研究生和科研用户的 Codex 插件。它把研究想法、文献和代码检索、实验设计、服务器实验、消融和 baseline 对比，以及 Nature 风格论文写作放到同一个可审计工作流里。

它不是单独的网页 wizard，也不是把某个外部 agent 硬塞进运行时。第一版更适合作为 Codex 的研究插件：由 `matrix-research-autopilot` 负责从 idea 启动，由 `matrix-autolab` 负责实验执行和记录，由内置 `nature-*` skills 负责写作、图、引用和数据声明。

### 适合的使用场景

- 你只有一个研究方向、假设、数据集想法或粗略 idea，需要先判断能不能做。
- 你已经有 `main.tex`，想从论文内容进入方法实现、训练、消融和 baseline 复现。
- 你已经跑完实验，想把结果组织成 supported claims、英文 Results/Discussion、图注和引用。
- 你希望每个 claim 都能追溯到真实证据，而不是让 agent 直接“编一篇论文”。

### 内置能力

- `matrix-research-autopilot`：从研究 idea 到文献/代码/数据/baseline 搜索、研究路线、实验计划和写作包。
- `matrix-autolab`：PaperBanana -> AutoLab -> AutoBaseline 的统一入口。
- `paperbanana`：根据论文方法部分生成论文框架图和方法图。
- `autolab`：实现方法、训练、评估、消融和 phase report。
- `autobaseline`：搜索、适配和运行 baseline 对比。
- `nature-writing`：基于 `writing_packet.md` 写 Results、Discussion 和论文段落。
- `nature-figure`：基于 `experiment_matrix.json`、结果 CSV 和 figure contracts 组织图、图注和图形说明。
- `nature-citation`：为背景、相关工作、讨论和方法上下文补引用，不伪造实验结果支撑。
- `nature-data`：生成 Data Availability、FAIR 检查和数据仓库声明。
- `nature-polishing`、`nature-reader`、`nature-response`、`nature-paper2ppt`、`nature-academic-search`：覆盖润色、读文献、回复审稿、论文转 PPT 和学术搜索。
- `apps/dashboard`：本地只读实验看板，查看 workflow、runs、metrics、failures、reports 和 artifacts。

### 推荐工作流

```text
research idea
-> Research Discovery Layer 搜索论文、代码、数据集和 baseline
-> research_brief.md + search_evidence.json
-> 用户确认研究路线
-> 生成 main.tex 或实验型 manuscript scaffold
-> matrix-autolab 执行服务器实验、消融和 baseline
-> experiment_matrix.json + 结果 CSV + phase reports
-> manuscript_claims.json
-> writing_packet.md
-> nature-writing / nature-figure / nature-citation / nature-data
```

关键规则：只有 `supported` claim 可以进入正式论文写作。没有证据的 claim 必须标记为 `needs_evidence`，并从 `writing_packet.md` 的正式写作区排除。

### main.tex 在哪一步生成

`main.tex` 出现在研究路线确认之后。

如果你从 idea 开始，`matrix-research-autopilot` 会先搜索并生成 `research_brief.md` 和 `search_evidence.json`。你确认研究路线后，如果还没有论文源码，它必须先生成 `research_design.json`：其中包含数据集角色、前沿研究方向、领域难点、现有方法问题、至少三个带公式的方法模块、总损失和消融计划。`build-main-tex` 会先校验这个设计稿；如果缺少合格设计稿，它会失败，不再生成泛泛 scaffold。如果你提供了模板，例如 `D:/DreamweaverAI/test/main.tex`，插件只参考模板的结构、章节组织和写作风格，不复制模板论文的内容、方法、数据集、引用或结果。

可用命令：

```bash
python scripts/research_autopilot.py validate-research-design
python scripts/research_autopilot.py build-main-tex --design-file research_design.json --template "D:/DreamweaverAI/test/main.tex" --topic "confirmed research topic"
```

### 安装和启用

在本地源码目录安装到个人插件目录：

```powershell
cd D:\DreamweaverAI\juzhen\paperExperiment\dreamweaverai-autolab
node .\bin\matrix-autolab.js install --force
```

默认安装位置：

```text
C:\Users\10766\plugins\dreamweaverai-autolab
```

注册个人 marketplace：

```powershell
codex plugin marketplace add %USERPROFILE%
```

如果 Codex 插件 UI 里没有自动启用，可以在 `C:\Users\10766\.codex\config.toml` 中确认：

```toml
[plugins."dreamweaverai-autolab@personal"]
enabled = true
```

启用后新开一个 Codex 线程，让新插件和 skills 被重新加载。

`Add Marketplace` 的作用是把一个本地 marketplace 注册给 Codex。它不是 npm install，也不会自动克隆项目；它只是告诉 Codex 去哪里发现个人插件。

### 推荐提示词

从研究 idea 开始：

```text
请使用 matrix-research-autopilot，围绕我的研究 idea 完成文献、代码、数据集和 baseline 搜索，生成 research_brief.md 和 search_evidence.json。请先给出候选研究路线，等我确认后再生成 main.tex 和实验计划。
```

使用模板生成 `main.tex`：

```text
请参考 D:/DreamweaverAI/test/main.tex 的结构生成新的 main.tex。只参考模板格式和章节组织，不复制模板论文内容。请让研究内容来自已确认的 research_brief.md 和 search_evidence.json。
```

从已有论文进入实验：

```text
请使用 matrix-autolab，根据 main.tex 完成方法实现、训练、消融和 baseline 对比。每个阶段生成报告并等待我确认。
```

实验完成后进入写作：

```text
请基于 experiment_matrix.json、结果 CSV、phase reports 和 manuscript_claims.json 生成 writing_packet.md，然后使用 nature-writing、nature-figure、nature-citation 和 nature-data 准备英文稿件、图注、引用和数据声明。unsupported claims 不要进入正式写作。
```

### 开发验证

```bash
npm run doctor
npm run pack:dry-run
```

`doctor` 会检查插件 manifest、核心 scripts、Matrix skills，以及内置的 9 个 `nature-*` skills。`pack:dry-run` 用于确认发布包包含 `skills/`、`docs/`、`scripts/research_autopilot.py` 和 Nature Skills 资源。

### 第三方说明

内置 Nature Skills 来源于 `Yuan1z0825/nature-skills`，按 MIT 许可证集成和再分发。许可证文本保存在 `docs/third-party-nature-skills-LICENSE.md`。

## English Guide

DreamweaverAI AutoLab is a Codex plugin for graduate students and researchers who want a practical idea-to-paper and paper-to-experiment workflow. It connects research discovery, experiment planning, gated server execution, ablations, baseline comparison, evidence tracking, and Nature-style manuscript writing.

The first version is intentionally plugin-first. `matrix-research-autopilot` starts from a research idea, `matrix-autolab` runs the experiment workflow, and the built-in `nature-*` skills produce writing, figures, citations, and data statements from verified evidence.

### When To Use It

- You have a rough research idea, hypothesis, direction, or dataset and need to decide whether it is worth pursuing.
- You already have a `main.tex` and want to implement the method, train models, run ablations, and compare baselines.
- You have experiment results and want to turn them into supported claims, English Results/Discussion text, figure captions, and references.
- You want the agent to preserve an auditable evidence chain instead of drafting unsupported manuscript claims.

### Included Skills

- `matrix-research-autopilot`: idea-to-paper discovery, evidence, research route, experiment plan, and writing packet.
- `matrix-autolab`: unified PaperBanana -> AutoLab -> AutoBaseline entry point.
- `paperbanana`: framework and methodology figure generation from paper text.
- `autolab`: method implementation, training, evaluation, ablations, and phase reports.
- `autobaseline`: baseline discovery, adaptation, execution, and comparison.
- `nature-writing`: Results, Discussion, manuscript sections, and claim-evidence maps from `writing_packet.md`.
- `nature-figure`: figures and captions from `experiment_matrix.json`, result CSV files, phase reports, and figure contracts.
- `nature-citation`: references for background, related work, discussion, and method context; it must not fabricate support for experimental results.
- `nature-data`: Data Availability, FAIR checks, dataset citation, and repository statements.
- `nature-polishing`, `nature-reader`, `nature-response`, `nature-paper2ppt`, `nature-academic-search`: polishing, paper reading, reviewer response, slide conversion, and academic search support.
- `apps/dashboard`: local read-only dashboard for workflows, runs, metrics, failures, reports, artifacts, and sync readiness.

### Recommended Workflow

```text
research idea
-> Research Discovery Layer searches papers, code, datasets, and baselines
-> research_brief.md + search_evidence.json
-> user-confirmed research route
-> main.tex or experiment-first manuscript scaffold
-> matrix-autolab server execution, ablations, and baselines
-> experiment_matrix.json + result CSV files + phase reports
-> manuscript_claims.json
-> writing_packet.md
-> nature-writing / nature-figure / nature-citation / nature-data
```

The central rule is evidence-gated writing. Only `supported` claims may enter manuscript prose. Claims without evidence must be marked `needs_evidence` and excluded from the formal writing section of `writing_packet.md`.

### When main.tex Is Generated

`main.tex` is generated after the research route is confirmed.

When starting from an idea, `matrix-research-autopilot` first creates `research_brief.md` and `search_evidence.json`. After you confirm the route, it must create `research_design.json` with dataset roles, frontier directions, domain difficulties, current-method gaps, at least three formula-bearing method modules, an overall objective, and ablations. `build-main-tex` validates that design first; without a valid design, it fails instead of producing a generic scaffold. If you provide a template such as `D:/DreamweaverAI/test/main.tex`, the plugin uses it only for structure, section organization, and style. It must not copy the template paper's content, methods, datasets, citations, claims, or results.

Command example:

```bash
python scripts/research_autopilot.py validate-research-design
python scripts/research_autopilot.py build-main-tex --design-file research_design.json --template "D:/DreamweaverAI/test/main.tex" --topic "confirmed research topic"
```

### Install And Enable

Install from the local source tree:

```powershell
cd D:\DreamweaverAI\juzhen\paperExperiment\dreamweaverai-autolab
node .\bin\matrix-autolab.js install --force
```

Default installed plugin path:

```text
C:\Users\10766\plugins\dreamweaverai-autolab
```

Register the personal marketplace:

```powershell
codex plugin marketplace add %USERPROFILE%
```

If the plugin UI does not enable it automatically, confirm this block in `C:\Users\10766\.codex\config.toml`:

```toml
[plugins."dreamweaverai-autolab@personal"]
enabled = true
```

Open a new Codex thread after enabling the plugin so the new skills are loaded.

`Add Marketplace` registers a local marketplace with Codex. It does not install an npm package or clone a repository by itself; it only tells Codex where to discover personal plugins.

### Prompt Examples

Start from a research idea:

```text
Use matrix-research-autopilot to search papers, code, datasets, and baselines for my research idea. Generate research_brief.md and search_evidence.json first, recommend candidate research routes, and wait for my confirmation before generating main.tex and the experiment plan.
```

Generate `main.tex` from a template:

```text
Use D:/DreamweaverAI/test/main.tex as a structural template for a new main.tex. Only follow the organization and style; do not copy its research content. Use the confirmed research_brief.md and search_evidence.json as the source of the new manuscript scaffold.
```

Run experiments from an existing paper:

```text
Use matrix-autolab with main.tex to implement the method, train models, run ablations, and compare baselines. Produce a phase report for each stage and wait for my confirmation.
```

Move from results to writing:

```text
Build writing_packet.md from experiment_matrix.json, result CSV files, phase reports, and manuscript_claims.json. Then use nature-writing, nature-figure, nature-citation, and nature-data to prepare English manuscript text, captions, citations, and data statements. Do not include unsupported claims in final prose.
```

### Development Checks

```bash
npm run doctor
npm run pack:dry-run
```

`doctor` checks the manifest, core scripts, Matrix skills, and all nine built-in `nature-*` skills. `pack:dry-run` confirms the publishable package includes `skills/`, `docs/`, `scripts/research_autopilot.py`, and Nature Skills resources.

### Third-Party Notice

The built-in Nature Skills are integrated from `Yuan1z0825/nature-skills` and redistributed under the MIT license. The license text is kept in `docs/third-party-nature-skills-LICENSE.md`.
