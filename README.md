# AutoLab - Paper-Driven Deep Learning Experiment Workflow

[中文版](README_zh.md) | English

A three-skill pipeline for automating the complete workflow from paper to experiments: framework figure generation → method implementation → baseline comparison.

## Overview

AutoLab provides an automated, phase-gated workflow for implementing deep learning papers with mandatory user confirmation at each stage. It consists of three coordinated skills:

1. **PaperBanana** - Generate publication-quality framework figures from paper methodology
2. **AutoLab** - Implement the method, run experiments and ablations
3. **AutoBaseline** - Train SOTA baselines for comparison

## Key Features

- **Phase-Gated Execution**: Each phase requires user confirmation before proceeding
- **Documentation-Driven**: Every phase produces detailed `.md` reports for human review
- **State Management**: Shared `workflow_status.json` tracks progress across all skills
- **Flexible Workflow**: Skip steps you've already completed (e.g., existing framework figures)
- **Recoverable**: Resume from any checkpoint after interruption

## Installation

### 1. Create Skills Directory

```bash
mkdir -p .claude/skills
```

### 2. Move Skills to Directory

```bash
mv paperbanana-0.1.0 .claude/skills/
mv autolab-0.1.0 .claude/skills/
mv autobaseline-0.1.0 .claude/skills/
```

### 3. Verify Installation

```bash
ls .claude/skills/
# Should show: paperbanana-0.1.0  autolab-0.1.0  autobaseline-0.1.0
```

## Usage

### Quick Start

1. **Prepare your paper source**

   - Place `main.tex` in your project directory
   - Ensure it contains `\begin{abstract}...\end{abstract}` and `\section{Method}` sections
2. **Start the workflow**

   ```bash
   # In Claude Code, invoke the first skill
   /paperbanana-0.1.0
   ```
3. **Follow the guided workflow**

   - Each skill will ask for confirmation before proceeding
   - Review generated reports in `experiment_docs/reports/`
   - Check workflow status in `workflow_status.json`

### Workflow Sequence

```
┌─────────────────┐
│  PaperBanana    │  Generate framework figure
│  (Optional)     │  → paperbanana_completion_report.md
└────────┬────────┘
         │ User confirms
         ↓
┌─────────────────┐
│    AutoLab      │  Implement method & run experiments
│  (Phase 1-9)    │  → experiment_docs/reports/phase_*.md
└────────┬────────┘  → experiment_docs/IMPLEMENTATION_SUMMARY.md
         │ User confirms
         ↓
┌─────────────────┐
│  AutoBaseline   │  Train SOTA baselines
│  (Optional)     │  → baselines/BASELINE_COMPARISON_REPORT.md
└─────────────────┘
```

### Workflow Status File

The `workflow_status.json` file tracks the state of all three skills:

```json
{
  "project": "Your Paper Title",
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

**Status values**: `pending` | `in_progress` | `completed` | `skipped`

## Skill Details

### 1. PaperBanana (paperbanana-0.1.0)

**Purpose**: Generate publication-quality framework figures from paper abstract and methodology.

**When to use**:

- You need a framework diagram for your paper
- You want to visualize the method architecture

**Workflow**:

1. Extracts abstract and method sections from `main.tex`
2. Launches interactive web UI for figure generation
3. Generates completion report
4. Asks if you want to proceed to AutoLab

**Output**:

- `paperbanana_completion_report.md` - Execution details and parameters
- Generated framework figures (saved by user through UI)
- Updated `workflow_status.json`

**Skip condition**: If you already have a framework figure, AutoLab will ask if you need PaperBanana.

---

### 2. AutoLab (autolab-0.1.0)

**Purpose**: Implement the paper's method, run experiments, and perform ablations.

**When to use**:

- You have a paper source (`main.tex`) and want to implement it
- You need structured experiment tracking with phase gates

**Phases**:

1. **Phase 1**: Generate framework figure (via PaperBanana)
2. **Phase 2**: Setup baseline, dataset, environment
3. **Phase 3**: Baseline audit (find entrypoints, configs, data loading)
4. **Phase 4**: Module implementation
5. **Phase 4.5**: Loss consistency check
6. **Phase 5**: Integration test
7. **Phase 6**: Short training run (sanity check)
8. **Phase 7**: Full training with automatic monitoring
9. **Phase 8**: Evaluation on test set
10. **Phase 9**: Final summary and comparison

**Output**:

- `experiment_docs/CLAUDE.md` - Project context and module map
- `experiment_docs/TODO.md` - Phase checklist
- `experiment_docs/progress.json` - Internal phase tracking
- `experiment_docs/reports/phase_*.md` - Detailed phase reports
- `experiment_docs/IMPLEMENTATION_SUMMARY.md` - Final summary
- Updated `workflow_status.json`

**Key features**:

- Checks if PaperBanana already completed (reads `workflow_status.json`)
- Automatic training monitoring with cron jobs
- Mandatory user confirmation at each phase
- Asks if you want to proceed to AutoBaseline after completion

---

### 3. AutoBaseline (autobaseline-0.1.0)

**Purpose**: Train SOTA baseline models for comparison with your method.

**When to use**:

- AutoLab has completed implementation
- You need to compare against SOTA baselines from the paper

**Prerequisites**:

- AutoLab must be completed (checks `workflow_status.json`)
- Reads `experiment_docs/IMPLEMENTATION_SUMMARY.md` for context

**Phases**:

1. **Phase 1**: Identify baselines from paper
2. **Phase 2**: Clone baseline repositories
3. **Phase 3**: Audit baseline codebases
4. **Phase 4**: Adapt data pipelines
5. **Phase 5**: Write unified training scripts
6. **Phase 6**: Launch training with monitoring
7. **Phase 7**: Wait for completion
8. **Phase 8**: Collect metrics and generate comparison report

**Output**:

- `baselines/reports/phase_*.md` - Phase reports
- `baselines/BASELINE_COMPARISON_REPORT.md` - Final comparison
- Updated `workflow_status.json`

**Key features**:

- Handles multiple independent codebases
- Unified evaluation on the same dataset
- Automatic training monitoring
- Side-by-side metric comparison

## Advanced Usage

### Resume from Checkpoint

If interrupted, simply re-invoke the skill. It will check `workflow_status.json` and resume from the last confirmed phase.

```bash
# AutoLab will detect Phase 3 was completed and start from Phase 4
/autolab-0.1.0
```

### Skip PaperBanana

If you already have a framework figure:

```bash
# Start directly with AutoLab
/autolab-0.1.0
# When asked "Do you need to generate the framework figure?", answer "no"
```

### Run Only Baselines

If you've already implemented the method manually:

```bash
# Ensure workflow_status.json shows autolab as "completed"
/autobaseline-0.1.0
```

## File Structure

After running the complete workflow, your project will have:

```
your-project/
├── main.tex                              # Your paper source
├── workflow_status.json                  # Shared workflow state
├── paperbanana_completion_report.md      # PaperBanana report
├── paper_figures/
│   ├── method_content.txt                # Extracted abstract + method
│   └── framework_figure.png              # Generated figure (if saved)
├── experiment_docs/
│   ├── CLAUDE.md                         # Project context
│   ├── TODO.md                           # Phase checklist
│   ├── progress.json                     # Internal phase tracking
│   ├── IMPLEMENTATION_SUMMARY.md         # Final summary
│   └── reports/
│       ├── phase_1_paperbanana_report.md
│       ├── phase_2_setup_report.md
│       ├── ...
│       └── phase_9_final_report.md
└── baselines/
    ├── BASELINE_COMPARISON_REPORT.md     # Final comparison
    └── reports/
        ├── phase_1_identify_report.md
        ├── ...
        └── phase_8_comparison_report.md
```

## Design Philosophy

### 1. Human-in-the-Loop

Every phase requires explicit user confirmation. The AI cannot skip ahead or make assumptions about your intent.

### 2. Documentation-Driven

All decisions, implementations, and results are documented in `.md` files. These serve as:

- Audit trail for reproducibility
- Context for future sessions
- Evidence for paper writing

### 3. State Coordination

The shared `workflow_status.json` enables:

- Cross-skill state checking
- Workflow resumption after interruption
- Flexible execution order (skip completed steps)

### 4. Fail-Safe Execution

- One phase at a time, no parallel execution across phases
- Concrete evidence required (file paths, line numbers, command outputs)
- Smoke tests before full training
- Automatic monitoring for long-running tasks

## Troubleshooting

### "AutoLab must be completed first"

- AutoBaseline requires AutoLab to finish Phase 9
- Check `workflow_status.json` to see AutoLab's status
- Complete AutoLab before running AutoBaseline

### "PaperBanana already completed"

- AutoLab detected existing PaperBanana completion in `workflow_status.json`
- If you want to regenerate, manually edit the JSON or delete it

### Workflow state is corrupted

```bash
# Reset workflow state
rm workflow_status.json
# Start fresh from PaperBanana or AutoLab
```

### Phase reports are missing

- Each phase generates a report before asking for confirmation
- If missing, the phase was not completed
- Re-run the skill to regenerate

## Requirements

- **Claude Code** or compatible AI coding environment
- **LaTeX paper source** with `main.tex`
- **Python environment** for deep learning experiments
- **Git** for cloning baseline repositories (AutoBaseline)
- **Baseline codebase** for your method (AutoLab)
- **Dataset** prepared and accessible

## Version

- **Workflow Version**: 0.1.0
- **PaperBanana**: 0.1.0
- **AutoLab**: 0.2.0
- **AutoBaseline**: 0.2.0

## License

See individual skill directories for license information.

## Contributing

This is a research workflow automation tool. Contributions welcome for:

- Additional phase checks and validations
- Better error handling and recovery
- Support for more paper formats
- Integration with experiment tracking tools (W&B, MLflow)

## Citation

If you use AutoLab in your research, please cite:

```bibtex
@software{autolab2026,
  title={AutoLab: Paper-Driven Deep Learning Experiment Workflow},
  author={serendipityshe},
  year={2026},
  url={https://github.com/serendipityshe/JUZHEN_ABLATION.git}
}
```
