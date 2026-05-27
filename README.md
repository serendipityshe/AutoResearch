# DreamweaverAI AutoLab

<p align="center">
  <strong>从研究想法到可审计实验，再到论文写作资产的一体化 Codex 插件</strong>
</p>

<p align="center">
  <code>matrix-research-autopilot</code>
  ·
  <code>matrix-autolab</code>
  ·
  <code>paperbanana</code>
  ·
  <code>autolab</code>
  ·
  <code>autobaseline</code>
</p>

DreamweaverAI AutoLab 是一个面向科研工作流的 Codex 插件包。它把研究方向探索、论文复现实验、框架图生成、方法实现、消融实验、SOTA baseline 对比、本地实验记录和只读看板收束到同一个插件中。

它的核心目标很直接：让每一步研究动作都有证据、有产物、有阶段门控，而不是只停留在聊天记录里。

```text
粗糙研究想法
  -> 文献 / 代码 / 数据集 / baseline 搜索
  -> 可审计证据与研究路线
  -> 实验计划和 main.tex 或论文脚手架
  -> Matrix-AutoLab 服务器实验
  -> 消融与 baseline 对比
  -> claim-to-evidence 写作包
  -> 论文、图表、引用与数据声明
```

## 项目信息

| 项目 | 内容 |
|---|---|
| 包名 | `@dreamweaverai/matrix-autolab` |
| 插件名 | `dreamweaverai-autolab` |
| 版本 | `0.1.0` |
| 运行环境 | Node.js `>=18`，Python 3 |
| 主要场景 | idea-to-paper、paper-to-experiment、论文复现、消融实验、baseline 对比 |
| 数据策略 | local-first，本地记录优先，默认不上传实验数据 |

## 核心能力

| 入口 | 适合做什么 | 典型输入 |
|---|---|---|
| `matrix-research-autopilot` | 从研究想法出发，完成文献、代码、数据集、baseline 搜索，并生成实验路线与写作资产 | 研究想法、方向、假设、数据集线索 |
| `matrix-autolab` | 统一调度论文复现到实验验证的完整流程 | `main.tex`、论文源码、实验计划 |
| `paperbanana` | 根据论文方法生成框架图与方法图 | 方法描述、论文源码 |
| `autolab` | 方法实现、训练、评估和消融实验 | 论文方法、代码仓库、数据集路径 |
| `autobaseline` | SOTA baseline 训练、适配与对比 | baseline repo、训练脚本、指标表 |
| `apps/dashboard` | 本地只读看板，查看运行记录、指标、报告、失败和同步准备状态 | `.autolab/` 记录 |

## 工作流总览

### 从研究想法到论文

`matrix-research-autopilot` 适合还没有 `main.tex` 的早期研究阶段。它使用 Research Discovery Layer 收集证据，而不是强绑定某个单一外部 agent。

```text
research idea
  -> Research Discovery Layer
  -> research_brief.md
  -> search_evidence.json
  -> 用户确认研究路线
  -> main.tex 或 experiment-first 论文脚手架
  -> paper_requirements.json
  -> experiment_matrix.json
  -> Matrix-AutoLab 执行
  -> manuscript_claims.json
  -> writing_packet.md
```

Research Discovery Layer 默认包含六类适配器：

| 适配器 | 证据来源 |
|---|---|
| `web` | 项目页面、benchmark 页面、官方文档、release 页面、网页资料 |
| `github` | 官方仓库、baseline 仓库、训练入口、许可证、活跃度、示例 |
| `huggingface` | HF papers、datasets、models、Spaces、dataset card、model card |
| `scholarly` | arXiv、Semantic Scholar、引用图谱、相关工作、方法谱系 |
| `pubmed` | 医学、生物、临床相关文献 |
| `zotero` | 用户本地 Zotero 文献库、笔记、PDF、citation key |

所有搜索结果最终都会归一化到 `search_evidence.json`。每条证据都需要有稳定定位信息，例如 `url`、`doi`、`pmid`、`citation_key`、`local_path` 或 `paper_or_repo_url`。

### 从论文到实验

`matrix-autolab` 适合已经有论文源码、`main.tex` 或明确实验计划的阶段。它会协调：

```text
main.tex / paper source
  -> paperbanana 生成方法图
  -> autolab 实现方法、训练、评估、消融
  -> autobaseline 运行 SOTA baseline
  -> 本地报告、指标、失败记录和变更清单
```

长实验必须由 `.autolab/runs/<run_id>/gate_status.json` 驱动。当前 gate 状态优先级高于聊天记忆，避免跳过阶段、漏掉实验要求或提前宣布完成。

## 推荐提示词

从一个研究想法开始：

```text
我有一个医学 AI 研究想法，请使用 matrix-research-autopilot 帮我完成文献、代码、数据集和 baseline 搜索，推荐 2-3 条研究路线，制定实验计划，并准备 Nature 风格写作资产。请每个阶段生成可审计证据，并在关键节点等待我确认。
```

从已有论文源码开始：

```text
根据 main.tex 帮我完成论文方法实现、训练、评估和相关消融实验。请使用 matrix-autolab 按阶段推进，每个阶段生成报告、指标和证据，并等待我确认后再继续。
```

继续一个已有实验：

```text
使用 matrix-autolab 从上次确认的阶段继续我的 AutoLab 实验。请先读取 .autolab 当前 gate 状态、requirements 和 phase plan，再告诉我下一步允许执行什么。
```

## 安装

全局安装 npm 包：

```bash
npm install -g @dreamweaverai/matrix-autolab
matrix-autolab install
```

安装到自定义插件目录：

```bash
matrix-autolab install --target /path/to/codex/plugins/dreamweaverai-autolab
```

默认本地开发安装位置：

```text
~/plugins/dreamweaverai-autolab
```

默认个人 marketplace 文件：

```text
~/.agents/plugins/marketplace.json
```

在当前 Codex CLI 注册个人 marketplace：

```bash
codex plugin marketplace add %USERPROFILE%
```

随后在 Codex App 的插件界面启用 `dreamweaverai-autolab@personal`。如果当前版本没有插件界面，可以手动写入 `~/.codex/config.toml`：

```toml
[plugins."dreamweaverai-autolab@personal"]
enabled = true
```

启用后请开启新的 Codex 线程，以便加载新增技能。

如果希望安装插件时同时安装 dashboard 依赖：

```bash
matrix-autolab install --install-dashboard
```

## 常用命令

### Research Autopilot 协议命令

```bash
python scripts/research_autopilot.py list-adapters
python scripts/research_autopilot.py init-artifacts --query "my research idea"
python scripts/research_autopilot.py validate-search-evidence
python scripts/research_autopilot.py build-main-tex --template "D:/DreamweaverAI/test/main.tex" --topic "my confirmed research topic"
python scripts/research_autopilot.py build-writing-packet --argument "confirmed research argument"
python scripts/research_autopilot.py validate-claims
```

### 本地记录命令

初始化项目记录：

```bash
python scripts/autolab_run.py init-project
```

启动论文复现实验：

```bash
python scripts/autolab_run.py start-run --kind paper_reproduction --entry-skill matrix-autolab
```

启动 idea-to-paper 实验：

```bash
python scripts/autolab_run.py start-run --kind idea_to_paper --entry-skill matrix-research-autopilot
```

### 阶段门控命令

声明当前允许执行的步骤：

```bash
python scripts/autolab_gate.py start-step --run-id <run_id> --phase phase_4_modules --step module_name --requirement method.module_name --required-artifact experiment_docs/reports/phase_4_modules_report.md --check "implementation, smoke test, and report evidence are present" --user-confirmation-required
```

检查当前步骤是否满足完成条件：

```bash
python scripts/autolab_gate.py check-step --run-id <run_id>
```

如果 `check-step` 返回 blocker，必须先解决 blocker，不能直接进入后续阶段。

## 协议产物

| 文件 | 用途 |
|---|---|
| `research_brief.md` | 用中文解释研究方向、问题定义、候选创新点、风险和推荐路线 |
| `search_evidence.json` | 记录来自文献、GitHub、HF、PubMed、Zotero 和网页的结构化证据 |
| `paper_requirements.json` | 从论文或脚手架中提取方法模块、loss、数据集、指标、baseline 和实现要求 |
| `experiment_matrix.json` | 记录主实验、消融、baseline、指标、预算、服务器目标和 handoff 状态 |
| `manuscript_claims.json` | 建立 claim-to-evidence 映射，阻止无证据结论进入论文正文 |
| `writing_packet.md` | 提供给论文写作、图表、caption、引用和数据声明的证据包 |
| `.autolab/runs/<run_id>/gate_status.json` | 当前唯一允许执行的步骤和 blocker |
| `.autolab/runs/<run_id>/phase_plan.json` | 严格顺序阶段计划 |
| `.autolab/runs/<run_id>/requirements.json` | 论文要求和实验证据映射 |

## 本地 Dashboard

Dashboard 位于 `apps/dashboard`，第一版是只读、本地优先的看板。它可以查看 workflow 状态、run 历史、指标、失败记录、报告、artifact 和同步准备状态。

```bash
cd apps/dashboard
npm install
npm run dev
```

打开：

```text
http://127.0.0.1:3217
```

Dashboard 默认不会上传数据，也不会修改 `.autolab/` 记录。

## 项目结构

```text
dreamweaverai-autolab/
  .codex-plugin/
    plugin.json
  .app.json
  apps/
    dashboard/
  bin/
    matrix-autolab.js
  docs/
    matrix-research-autopilot-architecture.md
  scripts/
    autolab_*.py
    research_autopilot.py
  skills/
    matrix-research-autopilot/
    matrix-autolab/
    paperbanana/
    autolab/
    autobaseline/
  package.json
  PUBLISHING.md
  README.md
```

## 开发与检查

运行插件健康检查：

```bash
npm run doctor
```

发布前检查 npm 包内容：

```bash
npm run pack:dry-run
```

本仓库使用 `files` 白名单和 `.npmignore` 黑名单控制发布内容，避免把本地实验记录、日志、依赖、构建产物、凭据、checkpoint 和模型权重发布出去。

## 版本控制与安全边界

仓库只应该跟踪插件源码、技能、脚本、文档和 dashboard 源码。以下内容不要提交：

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

写作和实验阶段遵守同一条规则：没有证据的结论只能标记为 `needs_evidence`，不能进入最终论文正文。每个 claim、结果图、baseline 对比和指标结论都必须能追溯到真实的报告、日志、代码路径、指标文件、来源链接或引用。

## License

MIT-0