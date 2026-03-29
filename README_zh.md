# AutoLab - 论文驱动的深度学习实验工作流

[English](README.md) | 中文版

一个三技能流水线，自动化从论文到实验的完整工作流：框架图生成 → 方法实现 → 基线对比。

## 概述

AutoLab 提供了一个自动化、阶段门控的工作流，用于实现深度学习论文，每个阶段都需要用户确认。它由三个协调的技能组成：

1. **PaperBanana** - 从论文方法生成出版级框架图
2. **AutoLab** - 实现方法、运行实验和消融研究
3. **AutoBaseline** - 训练 SOTA 基线进行对比

## 核心特性

- **阶段门控执行**：每个阶段需要用户确认后才能继续
- **文档驱动**：每个阶段生成详细的 `.md` 报告供人类审查
- **状态管理**：共享的 `workflow_status.json` 跟踪所有技能的进度
- **灵活工作流**：跳过已完成的步骤（如已有框架图）
- **可恢复**：中断后可从任何检查点恢复

## 安装

### 1. 创建技能目录

```bash
mkdir -p .claude/skills
```

### 2. 移动技能到目录

```bash
mv paperbanana-0.1.0 .claude/skills/
mv autolab-0.1.0 .claude/skills/
mv autobaseline-0.1.0 .claude/skills/
```

### 3. 验证安装

```bash
ls .claude/skills/
# 应显示: paperbanana-0.1.0  autolab-0.1.0  autobaseline-0.1.0
```

## 使用方法

### 快速开始

1. **准备论文源文件**
   - 将 `main.tex` 放在项目目录中
   - 确保包含 `\begin{abstract}...\end{abstract}` 和 `\section{Method}` 部分

2. **启动工作流**
   ```bash
   # 在 Claude Code 中，调用第一个技能
   /paperbanana-0.1.0
   ```

3. **按照引导工作流操作**
   - 每个技能在继续前会要求确认
   - 在 `experiment_docs/reports/` 中查看生成的报告
   - 在 `workflow_status.json` 中检查工作流状态

### 工作流程序列

```
┌─────────────────┐
│  PaperBanana    │  生成框架图
│  (可选)         │  → paperbanana_completion_report.md
└────────┬────────┘
         │ 用户确认
         ↓
┌─────────────────┐
│    AutoLab      │  实现方法并运行实验
│  (阶段 1-9)     │  → experiment_docs/reports/phase_*.md
└────────┬────────┘  → experiment_docs/IMPLEMENTATION_SUMMARY.md
         │ 用户确认
         ↓
┌─────────────────┐
│  AutoBaseline   │  训练 SOTA 基线
│  (可选)         │  → baselines/BASELINE_COMPARISON_REPORT.md
└─────────────────┘
```

### 工作流状态文件

`workflow_status.json` 文件跟踪所有三个技能的状态：

```json
{
  "project": "你的论文标题",
  "workflow_version": "0.1.0",
  "skills": {
    "paperbanana": {
      "status": "completed",
      "user_confirmed": true,
      "report": "paperbanana_completion_report.md",
      "timestamp": "2026-03-29T21:00:00Z"
    },
    "autolab": {
      "status": "in_progress",
      "user_confirmed": false,
      "current_phase": "phase_3_baseline_audit",
      "report": "experiment_docs/reports/phase_3_baseline_audit_report.md",
      "timestamp": "2026-03-29T22:30:00Z"
    },
    "autobaseline": {
      "status": "pending",
      "user_confirmed": false,
      "report": "",
      "timestamp": ""
    }
  }
}
```

**状态值**: `pending`（待处理）| `in_progress`（进行中）| `completed`（已完成）| `skipped`（已跳过）

## 技能详情

### 1. PaperBanana (paperbanana-0.1.0)

**用途**：从论文摘要和方法生成出版级框架图。

**使用场景**：
- 需要为论文生成框架图
- 想要可视化方法架构

**工作流**：
1. 从 `main.tex` 提取摘要和方法部分
2. 启动交互式 Web UI 进行图形生成
3. 生成完成报告
4. 询问是否继续到 AutoLab

**输出**：
- `paperbanana_completion_report.md` - 执行详情和参数
- 生成的框架图（用户通过 UI 保存）
- 更新的 `workflow_status.json`

**跳过条件**：如果已有框架图，AutoLab 会询问是否需要 PaperBanana。

---

### 2. AutoLab (autolab-0.1.0)

**用途**：实现论文方法、运行实验和消融研究。

**使用场景**：
- 有论文源文件（`main.tex`）并想实现它
- 需要带阶段门控的结构化实验跟踪

**阶段**：
1. **阶段 1**：生成框架图（通过 PaperBanana）
2. **阶段 2**：设置基线、数据集、环境
3. **阶段 3**：基线审计（查找入口点、配置、数据加载）
4. **阶段 4**：模块实现
5. **阶段 4.5**：损失一致性检查
6. **阶段 5**：集成测试
7. **阶段 6**：短训练运行（完整性检查）
8. **阶段 7**：完整训练（自动监控）
9. **阶段 8**：测试集评估
10. **阶段 9**：最终总结和对比

**输出**：
- `experiment_docs/CLAUDE.md` - 项目上下文和模块映射
- `experiment_docs/TODO.md` - 阶段检查清单
- `experiment_docs/progress.json` - 内部阶段跟踪
- `experiment_docs/reports/phase_*.md` - 详细阶段报告
- `experiment_docs/IMPLEMENTATION_SUMMARY.md` - 最终总结
- 更新的 `workflow_status.json`

**关键特性**：
- 检查 PaperBanana 是否已完成（读取 `workflow_status.json`）
- 使用 cron 作业自动监控训练
- 每个阶段强制用户确认
- 完成后询问是否继续到 AutoBaseline

---

### 3. AutoBaseline (autobaseline-0.1.0)

**用途**：训练 SOTA 基线模型与你的方法进行对比。

**使用场景**：
- AutoLab 已完成实现
- 需要与论文中的 SOTA 基线进行对比

**前置条件**：
- AutoLab 必须已完成（检查 `workflow_status.json`）
- 读取 `experiment_docs/IMPLEMENTATION_SUMMARY.md` 获取上下文

**阶段**：
1. **阶段 1**：从论文中识别基线
2. **阶段 2**：克隆基线仓库
3. **阶段 3**：审计基线代码库
4. **阶段 4**：适配数据流水线
5. **阶段 5**：编写统一训练脚本
6. **阶段 6**：启动训练并监控
7. **阶段 7**：等待完成
8. **阶段 8**：收集指标并生成对比报告

**输出**：
- `baselines/reports/phase_*.md` - 阶段报告
- `baselines/BASELINE_COMPARISON_REPORT.md` - 最终对比
- 更新的 `workflow_status.json`

**关键特性**：
- 处理多个独立代码库
- 在同一数据集上统一评估
- 自动训练监控
- 并排指标对比

## 高级用法

### 从检查点恢复

如果中断，只需重新调用技能。它会检查 `workflow_status.json` 并从最后确认的阶段恢复。

```bash
# AutoLab 会检测到阶段 3 已完成，从阶段 4 开始
/autolab-0.1.0
```

### 跳过 PaperBanana

如果已有框架图：

```bash
# 直接从 AutoLab 开始
/autolab-0.1.0
# 当询问"是否需要生成框架图？"时，回答"no"
```

### 仅运行基线

如果已手动实现方法：

```bash
# 确保 workflow_status.json 显示 autolab 为"completed"
/autobaseline-0.1.0
```

## 文件结构

运行完整工作流后，项目将包含：

```
your-project/
├── main.tex                              # 论文源文件
├── workflow_status.json                  # 共享工作流状态
├── paperbanana_completion_report.md      # PaperBanana 报告
├── paper_figures/
│   ├── method_content.txt                # 提取的摘要 + 方法
│   └── framework_figure.png              # 生成的图（如果保存）
├── experiment_docs/
│   ├── CLAUDE.md                         # 项目上下文
│   ├── TODO.md                           # 阶段检查清单
│   ├── progress.json                     # 内部阶段跟踪
│   ├── IMPLEMENTATION_SUMMARY.md         # 最终总结
│   └── reports/
│       ├── phase_1_paperbanana_report.md
│       ├── phase_2_setup_report.md
│       ├── ...
│       └── phase_9_final_report.md
└── baselines/
    ├── BASELINE_COMPARISON_REPORT.md     # 最终对比
    └── reports/
        ├── phase_1_identify_report.md
        ├── ...
        └── phase_8_comparison_report.md
```

## 设计理念

### 1. 人在回路中
每个阶段都需要明确的用户确认。AI 不能跳过或对你的意图做假设。

### 2. 文档驱动
所有决策、实现和结果都记录在 `.md` 文件中。这些文件用作：
- 可重现性的审计跟踪
- 未来会话的上下文
- 论文写作的证据

### 3. 状态协调
共享的 `workflow_status.json` 实现：
- 跨技能状态检查
- 中断后工作流恢复
- 灵活的执行顺序（跳过已完成步骤）

### 4. 故障安全执行
- 一次一个阶段，阶段间无并行执行
- 需要具体证据（文件路径、行号、命令输出）
- 完整训练前进行冒烟测试
- 长时间运行任务的自动监控

## 故障排查

### "AutoLab must be completed first"（必须先完成 AutoLab）
- AutoBaseline 需要 AutoLab 完成阶段 9
- 检查 `workflow_status.json` 查看 AutoLab 状态
- 在运行 AutoBaseline 前完成 AutoLab

### "PaperBanana already completed"（PaperBanana 已完成）
- AutoLab 在 `workflow_status.json` 中检测到现有的 PaperBanana 完成记录
- 如果想重新生成，手动编辑 JSON 或删除它

### 工作流状态损坏
```bash
# 重置工作流状态
rm workflow_status.json
# 从 PaperBanana 或 AutoLab 重新开始
```

### 阶段报告缺失
- 每个阶段在要求确认前生成报告
- 如果缺失，说明阶段未完成
- 重新运行技能以重新生成

## 系统要求

- **Claude Code** 或兼容的 AI 编码环境
- **LaTeX 论文源文件**（包含 `main.tex`）
- **Python 环境**（用于深度学习实验）
- **Git**（用于克隆基线仓库，AutoBaseline 需要）
- **基线代码库**（用于你的方法，AutoLab 需要）
- **数据集**（已准备并可访问）

## 版本

- **工作流版本**: 0.1.0
- **PaperBanana**: 0.1.0
- **AutoLab**: 0.2.0
- **AutoBaseline**: 0.2.0

## 许可证

各技能目录中的许可证信息请参见各自目录。

## 贡献

这是一个研究工作流自动化工具。欢迎贡献：
- 额外的阶段检查和验证
- 更好的错误处理和恢复
- 支持更多论文格式
- 与实验跟踪工具集成（W&B、MLflow）

## 引用

如果在研究中使用 AutoLab，请引用：

```bibtex
@software{autolab2026,
  title={AutoLab: Paper-Driven Deep Learning Experiment Workflow},
  author={Your Name},
  year={2026},
  url={https://github.com/yourusername/autolab}
}
```
