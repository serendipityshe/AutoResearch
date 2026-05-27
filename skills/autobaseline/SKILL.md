---
name: autobaseline
description: Use this skill when a user provides a paper (e.g., main.tex) and wants to run SOTA baseline comparisons. Guides the full workflow from identifying baselines in the paper, cloning repos, adapting data pipelines, writing unified training scripts, launching nohup training, and collecting final metrics into a comparison report. Distinct from ablation (autolab) — this skill handles multiple independent third-party models, each with its own codebase, preprocessing, and training logic. Includes mandatory user confirmation at each phase.
---

# AutoBaseline v0.2.0

Automated SOTA baseline comparison workflow with phase-gated execution and mandatory user confirmation.

## Prerequisites Check

Before starting:

- [ ] Check `workflow_status.json` exists in project root
- [ ] Verify autolab status is "completed" and user_confirmed is true
- [ ] If not completed, inform user: "AutoLab must be completed first. Please run autolab skill."
- [ ] Read autolab's `experiment_docs/IMPLEMENTATION_SUMMARY.md` for context

## When To Use

Use when the user:
- provides `main.tex` or another LaTeX paper source and wants to compare against SOTA baselines
- explicitly names baseline models to benchmark against
- asks to reproduce or run comparison experiments from a paper's experiment table
- needs a structured pipeline to train multiple third-party models on the same dataset

Do NOT use for:
- ablation studies of a single method (use autolab instead)
- single-model training or debugging
- literature review without implementation

## Pipeline Position

autobaseline is part of a three-skill pipeline driven by `main.tex`:

1. **paperbanana** → generates the main framework figure (completed in autolab Phase 1)
2. **autolab** → implements the method, runs experiments and ablations
3. **autobaseline** (this skill) → trains SOTA baselines for comparison

**IMPORTANT**: autobaseline runs AFTER autolab completes. It assumes paperbanana has already generated the framework figure in autolab Phase 1.

## Core Differences from Ablation (autolab)

- **autolab**: one codebase, toggle modules on/off, same data pipeline throughout
- **autobaseline**: multiple independent codebases, each with its own data format, preprocessing, model architecture, training script, and potentially pretrained weights
- Key challenge: unifying heterogeneous repos to run on the same dataset with comparable evaluation

## Core Principles

### 0. Machine Gate First
- Before each phase or baseline-specific substep, declare the current work with `python plugins/matrix-autolab/scripts/autolab_gate.py start-step --run-id <run_id> ...`
- Every selected baseline, repo audit finding, data adapter, smoke test, metric, and report must be tied to a requirement or evidence record
- A phase or substep is not complete until `autolab_gate.py check-step --run-id <run_id>` returns `ok: true`
- If the gate reports blockers, STOP and resolve them before continuing
- `gate_status.json` is the source of truth for the next executable step; chat memory and summaries are secondary

### 1. Phase-Gated Execution
- Each phase has three mandatory steps: Execute → Document → User Confirm
- No phase can start until the previous phase's user confirmation is received
- AI cannot skip ahead or work in parallel across phases

### 2. Documentation-Driven
- Every phase produces a `phase_X_{name}_report.md` file
- Reports contain concrete evidence (file paths, commands, outputs, metrics)
- Reports are the source of truth, not AI memory

### 3. User Confirmation Gates
- After each phase, AI MUST present the report and ask: "Phase X complete. Please review `phase_X_{name}_report.md`. Confirm to proceed or request changes."
- AI MUST wait for explicit user response ("confirm", "ok", "proceed", or specific feedback)
- If user requests changes, return to that phase's execution step

## Workflow

### Step 1: Read the paper and extract baselines

Read the LaTeX source. If the paper uses `\input` or `\include`, read those files too.

Extract:
- **Comparison table**: locate the main results table (usually in Experiments section)
- **Baseline list**: model names, citations, and any noted implementation details
- **Evaluation protocol**: metrics, dataset splits, preprocessing described in the paper
- **Task type**: segmentation, classification, detection, etc.
- **Dataset info**: name, modality, number of classes, input format

### Step 2: Generate baseline tracking document

Create `baselines/` directory with tracking files.

#### `baselines/BASELINE_PLAN.md`

```markdown
# Baseline Comparison Plan: {Paper Title}

## Paper Info
- Task: {segmentation / classification / detection}
- Dataset: {name}
- Metrics: {list from paper}
- Our method's reported results: {from paper table}

## Baselines to Implement

### 1. {Baseline Name}
- Paper: {citation}
- GitHub: {to be confirmed}
- Key features: {what makes this baseline relevant}
- Expected difficulty: {easy / medium / hard}

### 2. {Baseline Name}
...

## Evaluation Protocol
- Train/val/test split: {from paper}
- Preprocessing: {from paper}
- Augmentation: {from paper}
- Metrics: {exact definitions}

## Environment Requirements
- Dataset path: {to be confirmed}
- Conda env: {to be confirmed}
- GPU requirements: {estimate}
```

#### `baselines/progress.json`

```json
{
  "project": "{title}",
  "current_phase": "phase_1_planning",
  "phases": {
    "phase_1_planning": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_2_repo_audit": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_3_data_adaptation": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_4_training_setup": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_5_smoke_tests": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_6_full_training": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_7_evaluation": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_8_comparison": {"status": "pending", "report": "", "user_confirmed": false}
  },
  "baselines": {},
  "last_updated": ""
}
```

### Step 3: Execute in phases

Work through phases sequentially. **CRITICAL**: After completing each phase's execution and documentation steps, you MUST:

1. Start the current phase or baseline-specific substep with `autolab_gate.py start-step`
2. Record selected baseline and evaluation-protocol requirements with `autolab_gate.py define-requirement`
3. Execute only the active gate step
4. Record repo audit, adapter, smoke-test, metric, command, and report evidence with `autolab_gate.py add-evidence`
5. Run `autolab_gate.py check-step --run-id <run_id>` and stop if blockers remain
6. Present the phase report to the user
7. Explicitly ask: "Phase X complete. Please review `baselines/reports/phase_X_{name}_report.md`. Reply 'confirm' to proceed to Phase X+1, or provide feedback for changes."
8. WAIT for user response. Do NOT proceed to the next phase until user confirms.
9. After explicit user confirmation, run `autolab_gate.py confirm-step --run-id <run_id>` and then `autolab_gate.py complete-step --run-id <run_id>`
10. If user requests changes, return to that phase's execution step and iterate.

## Phase Breakdown

### Phase 1: Planning and Confirmation
#### 1.1 Execute
- [ ] Extract baselines from paper
- [ ] Search for official GitHub repos for each baseline
- [ ] Identify dataset requirements
- [ ] Estimate compute requirements

#### 1.2 Document
- [ ] Create `phase_1_planning_report.md` with:
  - Extracted baseline list with citations
  - Found GitHub repo URLs (one per baseline)
  - Dataset requirements: format, size, splits
  - Compute estimate: GPU memory, training time per baseline
  - Proposed baseline subset (if too many to run all)

#### 1.3 User Confirm (BLOCKING)
- [ ] Present report to user
- [ ] Ask user to confirm:
  - Which baselines to run (may want subset)
  - Repo URLs are correct (or provide correct ones)
  - Dataset path on local filesystem
  - Runtime environment (conda env, GPU allocation)
  - Training budget (epochs, batch size)
- [ ] Wait for explicit confirmation
- [ ] Update BASELINE_PLAN.md with confirmed info

Checkpoint: User confirmed baseline list and environment, proceed to Phase 2

### Phase 2: Repository Audit
#### 2.1 Execute
For each confirmed baseline:
- [ ] Clone repo to `baselines/{model_name}/`
- [ ] Audit codebase:
  - Find train entrypoint (search for `argparse`, `Trainer`, `main(`)
  - Find data loading (search for `Dataset`, `DataLoader`)
  - Find config mechanism (`.yaml`, `argparse`, `hydra`)
  - Find weight loading (search for `load_state_dict`, `from_pretrained`)
  - Check dependencies (`requirements.txt`, `environment.yml`)
- [ ] Identify adaptation needs:
  - Data format conversion required?
  - Config overrides needed?
  - Pretrained weights available?
  - Framework version conflicts?

#### 2.2 Document
- [ ] Create `phase_2_repo_audit_report.md` with:
  - For each baseline:
    * Repo path: `baselines/{model_name}/`
    * Train entrypoint: file path, example command
    * Data format expected: directory structure, file types
    * Config mechanism: how to override settings
    * Dependencies: key packages and versions
    * Pretrained weights: URL or path (if needed)
    * Adaptation strategy: what needs to change
    * Blockers: missing dependencies, incompatible versions, etc.

#### 2.3 User Confirm (BLOCKING)
- [ ] Present report to user
- [ ] Highlight any blockers or conflicts
- [ ] Wait for explicit confirmation
- [ ] If blockers exist, discuss solutions before proceeding

Checkpoint: User confirmed audit, proceed to Phase 3

### Phase 3: Data Adaptation
#### 3.1 Execute
For each baseline:
- [ ] Analyze expected data format
- [ ] Write data adapter or conversion script
- [ ] Options (prefer minimal changes):
  - Symlink: if model expects specific directory layout
  - Adapter dataset: thin wrapper that reads user's data
  - Conversion script: one-time format conversion
- [ ] Test adapter on a few samples
- [ ] Verify data loading works

#### 3.2 Document
- [ ] Create `phase_3_data_adaptation_report.md` with:
  - For each baseline:
    * Data adapter: file path and approach (symlink/wrapper/conversion)
    * Adapter code snippet (10-20 lines)
    * Test results: loaded sample shapes, visual check
    * Data path configuration: how to point model to data
    * Any issues encountered and solutions

#### 3.3 User Confirm (BLOCKING)
- [ ] Present report to user
- [ ] Show sample loading results
- [ ] Wait for explicit confirmation

Checkpoint: User confirmed data adaptation, proceed to Phase 4

### Phase 4: Training Setup
#### 4.1 Execute
For each baseline:
- [ ] Create training wrapper scripts:
  - `baselines/{model_name}/train_wrapper.sh`
  - `baselines/{model_name}/eval_wrapper.sh`
- [ ] Create config overrides:
  - `baselines/{model_name}/config_override.yaml`
- [ ] Set up logging and checkpointing:
  - Logs to `baselines/{model_name}/logs/`
  - Checkpoints to `baselines/{model_name}/checkpoints/`
- [ ] Ensure reproducibility:
  - Set random seeds
  - Document exact commands
  - Pin dependency versions

#### 4.2 Document
- [ ] Create `phase_4_training_setup_report.md` with:
  - For each baseline:
    * Training command: full reproducible command
    * Config overrides: what was changed from defaults
    * Log paths: where to find training logs
    * Checkpoint paths: where models are saved
    * Environment: conda env name, key package versions
    * Estimated training time

#### 4.3 User Confirm (BLOCKING)
- [ ] Present report to user
- [ ] Confirm training budget is acceptable
- [ ] Wait for explicit confirmation

Checkpoint: User confirmed training setup, proceed to Phase 5

### Phase 5: Smoke Tests
#### 5.1 Execute
For each baseline:
- [ ] Run smoke test: 2-3 iterations
- [ ] Verify loss is finite and decreasing
- [ ] Verify predictions contain all expected classes (pred.unique() check)
- [ ] If segmentation with class imbalance > 20:1, verify loss includes Dice or class weights
- [ ] Print loss breakdown — every component active and > 0
- [ ] Verify data loading is correct (spot-check samples)
- [ ] Confirm checkpoint saving works
- [ ] Confirm evaluation script runs

#### 5.2 Document
- [ ] Create `phase_5_smoke_tests_report.md` with:
  - For each baseline:
    * Smoke test command
    * Loss values: initial and after 2-3 iterations
    * Prediction distribution: pred.unique() output
    * Data loading check: sample shapes, visual inspection
    * Checkpoint test: saved file exists and loadable
    * **PASS/FAIL**: All checks pass?
    * If FAIL: diagnosis and proposed fix

#### 5.3 User Confirm (BLOCKING)
- [ ] Present report to user with actual numbers (not just "passed")
- [ ] For each baseline: show PASS/FAIL status
- [ ] If any FAIL: explain issue, return to earlier phase to fix
- [ ] Wait for explicit confirmation
- [ ] **GATE**: All baselines must PASS to proceed

Checkpoint: User confirmed all smoke tests PASS, proceed to Phase 6

### Phase 6: Full Training
#### 6.1 Execute
For each baseline:
- [ ] Launch full training (nohup or tmux)
- [ ] Record PID, log paths, checkpoint dir
- [ ] Set up automatic monitoring using CronCreate:
  ```python
  # Create hourly monitoring task for each baseline
  for baseline_name, log_path in baselines.items():
    CronCreate(
      cron=f"{baseline_idx * 5 + 7} * * * *",  # Stagger checks: :07, :12, :17, etc.
      prompt=f"""Check training status for baseline {baseline_name}:
      1. Read log file: {log_path}
      2. Check for errors: OOM, CUDA errors, NaN loss, process crash
      3. Check progress: current epoch, loss trend, ETA
      4. If training failed or stuck: notify user with error details and last 50 lines of log
      5. If training completed: notify user
      6. If training running normally: report current status (epoch, loss, ETA)""",
      recurring=True
    )
  ```
- [ ] Record cron job IDs for later cleanup

#### 6.2 Document
- [ ] Create `phase_6_full_training_report.md` with:
  - For each baseline:
    * Training command (full, reproducible)
    * Process info: PID, tmux session name, log path
    * Checkpoint directory
    * Estimated completion time
    * Monitoring cron job ID
    * Monitoring instructions (manual check if needed)
    * Current status: running / completed / failed

#### 6.3 User Confirm (BLOCKING)
- [ ] Present report to user
- [ ] Confirm all trainings are running
- [ ] Confirm monitoring cron jobs are active
- [ ] Provide monitoring instructions
- [ ] Wait for explicit confirmation

Checkpoint: User confirmed trainings launched with automatic monitoring, proceed to Phase 7 when complete

### Phase 7: Evaluation
#### 7.1 Execute
For each baseline:
- [ ] Wait for training to complete (or user signals early stop)
- [ ] Stop monitoring cron job: `CronDelete(job_id)`
- [ ] Identify best checkpoint (by validation metric)
- [ ] Run evaluation script on test set
- [ ] Collect all metrics (match paper's evaluation protocol)
- [ ] Save predictions if needed

#### 7.2 Document
- [ ] Create `phase_7_evaluation_report.md` with:
  - For each baseline:
    * Training completion status
    * Best checkpoint: path, epoch, validation metric
    * Test set results: all metrics
    * Comparison to paper's reported numbers (if available)
    * Training time: total hours
    * Any issues or failures

#### 7.3 User Confirm (BLOCKING)
- [ ] Present report to user
- [ ] Show metrics for each baseline
- [ ] Wait for explicit confirmation
- [ ] If results unsatisfactory, discuss next steps

Checkpoint: User confirmed evaluation results, proceed to Phase 8

### Phase 8: Comparison Report
#### 8.1 Execute
- [ ] Consolidate all baseline results
- [ ] Create comparison table (baselines vs our method)
- [ ] Generate visualizations if applicable
- [ ] Archive all artifacts

#### 8.2 Document
- [ ] Create `BASELINE_COMPARISON_SUMMARY.md` with:
  - Comparison table:
    | Method | Metric1 | Metric2 | ... | Training Time |
    |--------|---------|---------|-----|---------------|
    | Ours   | X.XX    | X.XX    | ... | X hours       |
    | Baseline1 | X.XX | X.XX    | ... | X hours       |
    | ...    | ...     | ...     | ... | ...           |
  - Analysis:
    * Which baselines our method outperforms
    * Which baselines are competitive
    * Possible reasons for differences
  - Artifacts:
    * Checkpoint paths for each baseline
    * Log paths
    * Prediction paths (if saved)
  - Reproducibility:
    * Exact commands to reproduce each baseline
    * Environment details
  - Known issues or limitations

#### 8.3 User Confirm (BLOCKING)
- [ ] Present comparison report to user
- [ ] Wait for explicit confirmation
- [ ] **GATE**: User confirms autobaseline is complete
- [ ] Update `workflow_status.json`:
  ```json
  "autobaseline": {
    "status": "completed",
    "user_confirmed": true,
    "report": "baselines/BASELINE_COMPARISON_REPORT.md",
    "timestamp": "<ISO8601>"
  }
  ```

Checkpoint: autobaseline complete

## Execution Rules

- One phase at a time, no skipping ahead
- Every phase produces a report in `baselines/reports/`
- Every phase requires user confirmation before proceeding
- Update progress.json at every phase transition
- If a phase fails its checks, STOP and report to user — do not continue
- **Anti-shortcut rule**:
  - Never skip a user confirmation gate
  - Never assume user approval without explicit response
  - Never proceed to next phase "to save time"
  - Reports must contain concrete evidence (file paths, commands, outputs), not summaries

## Recovery After Interruption

1. Read `baselines/progress.json`
2. Find last user-confirmed phase
3. Read that phase's report to understand what was done
4. Resume from first unconfirmed phase — not from memory

## Guidance

**Repo auditing:**
- Search with `rg`, never assume filenames or project structure
- Many repos have outdated READMEs — trust the code over documentation
- Check git tags/branches for stable releases vs development code

**Data adaptation:**
- Prefer symlinks over copying large datasets
- Validate a few samples visually after conversion
- Keep original data untouched — all conversions go to a separate directory

**Training configuration:**
- Match the paper's hyperparameters when possible
- If the paper doesn't specify, use the repo's default config
- Document any deviations from paper settings in phase reports
- Confirm training details (epochs, lr, batch size) with user before launching

**Common pitfalls:**
- Different repos may need different PyTorch/CUDA versions — use separate conda envs if needed
- Some repos hardcode dataset paths — search for these and override
- Watch for repos that expect specific directory names (e.g., `imagesTr`, `labelsTr`)
- OOM errors: reduce batch size first, then try gradient accumulation, then mixed precision

**Report writing:**
- Be specific: file paths with line numbers, not "in the baseline repo"
- Include command examples: actual commands that were run
- Include outputs: actual logs, not "it worked"
- Include numbers: metric values, not "looks good"
- Reports are for user review AND for AI recovery after context loss

**User confirmation:**
- Always present the report file path
- Always ask explicitly for confirmation
- Always wait for response before proceeding
- If user is silent, remind them: "Waiting for your confirmation to proceed to Phase X+1"
