---
name: autolab
description: Use this skill when a user provides a paper source file (e.g., main.tex) and wants to implement the method, run experiments, or perform ablations. Guides phased execution from paper reading to final evaluation with mandatory user confirmation at each phase.
---
# AutoLab v0.3.0

Paper-driven deep learning experiment workflow with phase-gated execution and mandatory user confirmation.

## When To Use

Use when the user:

- provides `main.tex` or another LaTeX paper source
- asks to implement a paper, reproduce experiments, or run ablations
- needs a structured experiment plan tied to an existing codebase

Do NOT use for single-file scripts, literature review only, or papers without an implementation target.

## Pipeline Position

autolab is part of a three-skill pipeline driven by `main.tex`:

1. **paperbanana** (first) → generates the main framework figure from abstract + method. Runs early as Phase 1 because it requires no implementation context and can work in parallel with setup.
2. **autolab** (this skill) → implements the method, runs experiments and ablations (Phase 2-9).
3. **autobaseline** → trains SOTA baselines for comparison (optional, after autolab completes).

**IMPORTANT**: paperbanana runs as Phase 1 with user confirmation before proceeding to implementation phases.

## Core Principles

### 1. Phase-Gated Execution

- Each phase has three mandatory steps: Execute → Document → User Confirm
- No phase can start until the previous phase's user confirmation is received
- AI cannot skip ahead or work in parallel across phases

### 2. Documentation-Driven

- Every phase produces a `phase_X_{name}_report.md` file
- Reports contain concrete evidence (file paths, line numbers, code snippets, output logs)
- Reports are the source of truth, not AI memory

### 3. User Confirmation Gates

- After each phase, AI MUST present the report and ask: "Phase X complete. Please review `phase_X_{name}_report.md`. Confirm to proceed or request changes."
- AI MUST wait for explicit user response ("confirm", "ok", "proceed", or specific feedback)
- If user requests changes, return to that phase's execution step

### 4. Two-Tier Gates (Machine + Human)

Every phase below has **two gates**:

1. **User Gate** — the user types `confirm` in chat after reading the phase report.
2. **Machine Gate** — a JSON artifact in `.autolab/runs/<run_id>/` that proves the phase actually ran. The next phase's first action is to validate it via the matrix-autolab CLI; if the artifact is missing or fails validation, the next phase MUST refuse to proceed.

The machine gate is what stops "I claimed I did X" drift. AI MUST NOT skip producing the artifact, and MUST run the validating CLI command before each downstream phase. If a model has no `.autolab/` workspace yet (the user hasn't initialised the project), Phase 2 includes the `init-project` + `start-run` calls that create it.

CLI invocation pattern (run from the autolab project root):

```bash
python plugins/matrix-autolab/scripts/autolab_run.py <subcommand> --run-id <id> ...
```

Throughout this skill, where you see "Machine Gate:" the listed artifact and CLI exit code are mandatory.

## Workflow

### Step 1: Read and analyze the paper

Read the LaTeX source directly. If the paper uses `\input` or `\include`, read those files too. Expand `\newcommand` / `\def` macros mentally when interpreting equations.

Extract:

**Metadata:** title, abstract, research goal, task type, backbone, dataset(s), evaluation metrics

**Structure:** section titles with one-line scope each

**Innovation modules:** for each Method subsection (skip generic ones like Overview, Preliminaries, Background, Implementation Details, Training Objective):

- Name, purpose, level (input / feature / loss)
- Key equations (verbatim LaTeX)
- Where it connects to the baseline
- Pitfalls or ambiguities

**Losses:** each component's name, formula, purpose, total loss composition

**Training details:** hyperparameters, optimizer, scheduler, augmentation, etc.

### Step 2: Confirm with the user

Before generating docs, confirm:

1. Baseline codebase path
2. Dataset path
3. Runtime environment (conda env, etc.)
4. Pretrained weights path (if needed)
5. Scope preferences (which modules, training budget)

### Step 3: Generate experiment docs

Create `experiment_docs/` with three files, written directly from your paper analysis.

#### `experiment_docs/CLAUDE.md`

Project context document. Write with specificity — every section should reflect THIS paper's content, not generic placeholders.

```
# {Paper Title}

## Summary
- Goal: {from abstract}
- Task: {segmentation / classification / detection / ...}
- Backbone: {model name}
- Dataset: {name}, path: {confirmed path}
- Metrics: {evaluation metrics}
- Progress: `experiment_docs/progress.json`

## Paper Map
- {Section}: {one-line scope}
- ...

## Innovation Modules

### 1. {Module Name}
- Section: {paper section}
- Level: {input / feature / loss}
- Purpose: {what and why}
- Insertion point: {where in baseline}
- Target file: {implementation path}
- Risks: {issues}

Equations:
{verbatim math}

Implementation notes:
{specific analysis: tensor shapes, edge cases, design decisions}

### 2. ...

## Losses
- {name}: {purpose}, formula: {formula}, file: {path}

## Baseline Map
- Path: {path}
- Train: {entrypoint}
- Model: {definition file}
- Config: {config file}

## Commands
{filled after baseline audit}

## Known Gaps
{ambiguities, missing info, mismatches}
```

#### `experiment_docs/TODO.md`

Phased checklist with user confirmation gates:

```
# TODO: {Paper Title}

## Rules
- Each phase has three steps: Execute → Document → User Confirm
- No phase starts until previous phase is user-confirmed
- All reports saved to experiment_docs/reports/

## Phase 1: Generate Framework Figure (paperbanana)

### 1.1 Execute

- [ ] Check if `workflow_status.json` exists and read paperbanana status
- [ ] If paperbanana status is "completed" and user_confirmed is true:
  - Skip to 1.2 with note: "PaperBanana already completed"
- [ ] Otherwise:
  - [ ] Read `main.tex` and extract:
    - `\begin{abstract}...\end{abstract}` → abstract text
    - `\section{Method}` through next `\section` → methodology text
  - [ ] Concatenate into content: `"Abstract:\n{abstract}\n\nMethodology:\n{method}"`
  - [ ] Write to `paper_figures/method_content.txt`
  - [ ] Ask user: "Do you need to generate the framework figure? (yes/no)"
    - If **no**: Update workflow_status.json with paperbanana status="skipped", skip to 1.2
    - If **yes**: Invoke `paperbanana-0.1.0` skill using Skill tool

### 1.2 Document

- [ ] Create `experiment_docs/reports/phase_1_paperbanana_report.md` with:
  - If paperbanana was already completed: reference to existing `paperbanana_completion_report.md`
  - If user skipped: "User confirmed framework figure not needed"
  - If paperbanana just executed: Summary of execution result

### 1.3 User Confirm (BLOCKING)

- [ ] Present the report to user
- [ ] Ask: "Phase 1 complete. Reply 'confirm' to proceed to implementation."
- [ ] Wait for explicit confirmation
- [ ] Update `workflow_status.json`:
  ```json
  "autolab": {
    "status": "in_progress",
    "current_phase": "phase_2_setup",
    "report": "experiment_docs/reports/phase_1_paperbanana_report.md",
    "timestamp": "<ISO8601>"
  }
  ```

Checkpoint: User confirmed, proceed to Phase 2

## Phase 2: Setup

### 2.1 Execute

- [ ] Initialise project tracking and start a run (skip if `.autolab/` already has an active run):
  ```bash
  python plugins/matrix-autolab/scripts/autolab_run.py init-project --name "<paper title>" --paper-source main.tex
  python plugins/matrix-autolab/scripts/autolab_run.py start-run --kind paper_reproduction --entry-skill autolab
  ```
  Capture the `run_id` from start-run's stdout — every later command needs it.
- [ ] Confirm baseline path
- [ ] Confirm dataset path
- [ ] Confirm environment and weights

### 2.2 Document

- [ ] Create `phase_2_setup_report.md` with:
  - Baseline path and key files identified
  - Dataset path and sample count
  - Environment details (conda env, GPU, CUDA version)
  - Pretrained weights path (if applicable)
  - Active `run_id`
  - Any blockers or missing dependencies

### 2.3 User Confirm (BLOCKING)

- [ ] Present report to user
- [ ] Wait for explicit confirmation
- [ ] If changes requested, return to 2.1

Machine Gate: `.autolab/runs/<run_id>/run.json` exists with `status: in_progress`. Verify with `autolab_run.py status`.

Checkpoint: User confirmed, proceed to Phase 2.5

## Phase 2.5: Environment Sanity Scan

### 2.5.1 Execute

- [ ] Scan the baseline working directory for stale checkpoints, caches, and outputs left by prior workflows. The scanner detects:
  - checkpoint files (`*.pth`, `*.ckpt`, `*.bin`, `*.safetensors`, `*.pt`)
  - output dirs (`outputs/`, `runs/`, `wandb/`, `lightning_logs/`, `tensorboard/`, `mlruns/`)
  - cache dirs (`*/cache`, `data/cache`, `processed/`)
  - large untracked binaries (>1 MiB) that are not git-managed
- [ ] Run the scan:
  ```bash
  python plugins/matrix-autolab/scripts/autolab_run.py scan-environment \
      --run-id <id> --workdir <baseline_root>
  ```
  Outputs:
    * `.autolab/runs/<id>/environment_snapshot.json` — machine-readable list with paths, sizes, mtimes, sha256, git-tracked status
    * `.autolab/runs/<id>/environment_decisions.json` — initialised with `decision: "pending"` for each item
    * `.autolab/runs/<id>/reports/phase_2.5_environment_report.md` — human-readable report

### 2.5.2 Document

- [ ] Open the report and walk the user through every detected item.
- [ ] For each entry in `environment_decisions.json`, the user must replace `"pending"` with one of:
    * `"keep"` — acknowledged as a known input (e.g., a pretrained weight intentionally placed there). Record the rationale.
    * `"move-aside"` — rename it to `*.bak` so the skill ignores it. Document the new path.
    * `"delete"` — remove it. ONLY do so on the user's explicit instruction.
- [ ] Update `phase_2.5_environment_report.md` with the user's decision per item and a one-line rationale.

### 2.5.3 User Confirm (BLOCKING)

- [ ] Present the report and the updated `environment_decisions.json` to the user.
- [ ] Wait for explicit confirmation that the working directory is clean.
- [ ] **GATE**: Every item must have a non-`pending` decision. If any pending remain, AI MUST refuse to proceed and ask the user to decide.

Machine Gate: `environment_snapshot.json` exists AND `environment_decisions.json` has zero items with `decision == "pending"`. Before later phases that touch training, AI MUST re-scan with `--against .autolab/runs/<id>/environment_snapshot.json` and verify exit code 0; exit code 3 means new untracked artifacts appeared and the workflow MUST stop until the user adjudicates.

Checkpoint: User confirmed clean environment, proceed to Phase 3

## Phase 3: Baseline Audit

### 3.1 Execute

- [ ] Find real train/eval entrypoints (use rg, not assumptions)
- [ ] Find config mechanism (argparse/hydra/yaml)
- [ ] Find data loading code
- [ ] Find model definition
- [ ] Identify how to toggle modules (config flags, command args)
- [ ] Run baseline smoke test (1 iteration)

### 3.2 Document

- [ ] Create `phase_3_baseline_audit_report.md` with:
  - Train entrypoint: file path, command example
  - Eval entrypoint: file path, command example
  - Config mechanism: how to override settings
  - Data format: expected input structure
  - Model architecture: key files and classes
  - Smoke test result: command run, output log snippet
  - Architecture notes:
    * Decoder/head structure (if segmentation/detection)
    * Multi-scale feature usage
    * Upsampling strategy
  - Data augmentation: current transforms, suitability for task domain
  - Identified risks or mismatches with paper

### 3.3 User Confirm (BLOCKING)

- [ ] Present report to user
- [ ] Wait for explicit confirmation
- [ ] If changes requested, return to 3.1

Checkpoint: User confirmed, proceed to Phase 4

## Phase 4: Module Implementation

### 4.1 Execute

For each innovation module:

- [ ] Implement in target file
- [ ] Smoke test on synthetic tensors (print shapes, check gradients)
- [ ] Add config flag to enable/disable
- [ ] Document any deviations from paper

### 4.2 Document

- [ ] Create `phase_4_modules_report.md` with:
  - For each module:
    * Implementation file: path and line numbers
    * Key code snippet (10-20 lines showing core logic)
    * Smoke test result: input/output shapes, gradient check
    * Config flag: name and how to toggle
    * Deviations from paper: what and why
  - Modules not yet implemented: reason (ambiguous, out of scope, etc.)

### 4.3 User Confirm (BLOCKING)

- [ ] Present report to user
- [ ] Wait for explicit confirmation
- [ ] If changes requested, return to 4.1

Checkpoint: User confirmed, proceed to Phase 4.5

## Phase 4.5: Loss Consistency Check

### 4.5.1 Execute

- [ ] List every loss component from paper's total loss formula
- [ ] For each component:
  - [ ] Verify function is defined
  - [ ] Verify function is CALLED in training loop
  - [ ] Verify it participates in backward pass
- [ ] Run 1-batch forward+backward pass
- [ ] Print each loss component's value
- [ ] Check for task-specific loss requirements:
  - [ ] If extreme class imbalance (any class < 5% of data): verify Dice Loss or class-weighted CE is used
  - [ ] If paper mentions specific loss weights: verify they match implementation

### 4.5.2 Document

- [ ] Create `phase_4.5_loss_check_report.md` with:
  - Paper's total loss formula (LaTeX)
  - Implementation breakdown:
    * Component 1: function name, file:line, called in training loop (yes/no), value from test batch
    * Component 2: ...
  - Test batch loss output (full log)
  - Class distribution statistics (if applicable)
  - Loss configuration: weights, reduction method
  - **PASS/FAIL**: All components active and non-zero?

### 4.5.3 User Confirm (BLOCKING)

- [ ] Present report to user
- [ ] If FAIL: explain issue, return to 4.5.1 to fix
- [ ] Wait for explicit confirmation
- [ ] **GATE**: Must be PASS to proceed

Machine Gate: `phase_4.5_loss_check_report.md` exists AND its closing line reads `PASS`.

Checkpoint: User confirmed PASS, proceed to Phase 4.7

## Phase 4.7: Data Pipeline Freeze

### 4.7.1 Execute

- [ ] Serialise the **deterministic** preprocess pipeline (Resize, CenterCrop, Normalize, ToTensor, etc.) as a JSON object to `experiment_docs/preprocess.json`. Include every transform's class name and parameters in their applied order. Example:
    ```json
    {
      "transforms": [
        {"name": "Resize", "size": [512, 1024], "interpolation": "bilinear"},
        {"name": "Normalize", "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]},
        {"name": "ToTensor"}
      ],
      "input_resolution": [512, 1024]
    }
    ```
- [ ] Serialise the **stochastic** augmentation pipeline as a JSON object to `experiment_docs/augment.json`. Include train/val splits separately:
    ```json
    {
      "train": [
        {"name": "RandomFlip", "p": 0.5, "axis": "horizontal"},
        {"name": "ColorJitter", "brightness": 0.2, "contrast": 0.2}
      ],
      "val": []
    }
    ```
- [ ] Compute and persist hashes:
  ```bash
  python plugins/matrix-autolab/scripts/autolab_run.py freeze-pipeline \
      --run-id <id> \
      --pre @experiment_docs/preprocess.json \
      --aug @experiment_docs/augment.json
  ```
  Stdout returns `{"preprocess_hash": "...", "augment_hash": "..."}`. The hashes are also written into `.autolab/runs/<id>/contract.json` under `data.preprocess_hash` and `data.augment_hash`.

### 4.7.2 Document

- [ ] Create `phase_4.7_pipeline_report.md` with:
  - Full preprocess transform list (code snippets + JSON)
  - Full train and val augmentation lists (code snippets + JSON)
  - `preprocess_hash` and `augment_hash` from the CLI output
  - Class mapping, splits, normalization statistics, target resolution
  - Any deviations from paper's described preprocessing/augmentation, with rationale

### 4.7.3 User Confirm (BLOCKING)

- [ ] Present the report to user.
- [ ] Confirm: "These two hashes lock the data pipeline. No phase from 6 onwards may change preprocess or augment without explicit re-freeze."
- [ ] Wait for explicit confirmation.

Machine Gate: `.autolab/runs/<id>/contract.json` has non-empty `data.preprocess_hash` AND non-empty `data.augment_hash`. Before Phase 6, 7, 8 launches the skill MUST run:
```bash
python plugins/matrix-autolab/scripts/autolab_run.py validate-contract \
    --run-id <id> \
    --pre @experiment_docs/preprocess.json \
    --aug @experiment_docs/augment.json
```
and verify exit code 0. Exit code 3 means the on-disk pipeline drifted from the frozen contract — STOP and notify the user.

Checkpoint: User confirmed pipeline frozen, proceed to Phase 5

## Phase 5: Integration

### 5.1 Execute

- [ ] Integrate modules into baseline behind config flags
- [ ] Test forward/backward pass with all modules enabled
- [ ] Test baseline recovery with all flags off
- [ ] Collect data statistics:
  - [ ] Class distribution (samples per class, pixels per class if segmentation)
  - [ ] Input resolution vs original data resolution
  - [ ] Samples per split (train/val/test)
  - [ ] Domain distribution (if multi-domain)

### 5.2 Document

- [ ] Create `phase_5_integration_report.md` with:
  - Integration points: where each module connects to baseline (file:line)
  - Config flags: how to enable/disable each module
  - Test results:
    * Forward pass with all modules: output shape, memory usage
    * Backward pass: gradient flow check
    * Baseline recovery test: command and result
  - Data statistics:
    * Class distribution table
    * Resolution: input vs original
    * Split sizes
  - Data imbalance handling:
    * If any class < 5%: what loss mechanism addresses this?
    * If input resolution > 2x original: justification
  - Identified risks

### 5.3 User Confirm (BLOCKING)

- [ ] Present report to user
- [ ] Wait for explicit confirmation
- [ ] If data statistics reveal issues, discuss with user before proceeding

Checkpoint: User confirmed, proceed to Phase 6

## Phase 6: Short Training (Smoke Test)

### 6.1 Execute

- [ ] Run 1-3 epochs with reduced budget (small subset or fewer iterations)
- [ ] Monitor training loss (all components)
- [ ] Run validation after each epoch
- [ ] Collect predictions from first validation
- [ ] Check prediction distribution (class counts, not all one class)
- [ ] Check metric trends

### 6.2 Document

- [ ] Create `phase_6_short_train_report.md` with:
  - Training command used
  - Training loss log (all components, first and last batch of each epoch)
  - Validation results per epoch:
    * Epoch 1: metric value, prediction distribution (pred.unique() output)
    * Epoch 2: metric value, improvement vs epoch 1
    * Epoch 3: metric value, trend
  - Sanity checks:
    * Predictions contain all expected classes? (yes/no)
    * Primary metric > random baseline? (yes/no, with baseline value)
    * Metric shows improvement trend? (yes/no)
    * Loss components all > 0 and decreasing? (yes/no)
  - **PASS/FAIL**: All sanity checks pass?
  - If FAIL: diagnosis and proposed fix

### 6.3 User Confirm (BLOCKING)

- [ ] Present report to user
- [ ] If FAIL: explain issue, return to earlier phase to fix
- [ ] Wait for explicit confirmation
- [ ] **GATE**: Must be PASS to proceed to full training

Machine Gate: Before launching short training, run `validate-contract --pre @... --aug @...` and confirm exit code 0. The pipeline used for short training must match the frozen Phase 4.7 hashes.

Checkpoint: User confirmed PASS, proceed to Phase 7

## Phase 7: Full Training

### 7.1 Execute

- [ ] Confirm training budget with user (epochs, batch size, etc.)
- [ ] Populate the remaining contract fields (hyperparams, modules, environment) by editing `.autolab/runs/<id>/contract.json` directly, then **lock** the contract:
  ```bash
  python plugins/matrix-autolab/scripts/autolab_run.py lock-contract --run-id <id>
  ```
  Lock fails (exit 5) if any required field is empty — fill those in and retry. Once locked, hyperparams / modules / data hashes / environment cannot be modified for this run.
- [ ] Re-validate the pipeline one last time:
  ```bash
  python plugins/matrix-autolab/scripts/autolab_run.py validate-contract \
      --run-id <id> --pre @experiment_docs/preprocess.json --aug @experiment_docs/augment.json --strict
  ```
  Must exit 0 before launching training.
- [ ] Launch full training (nohup or tmux)
- [ ] Record PID, log paths, checkpoint dir
- [ ] Set up automatic monitoring using CronCreate:
  ```python
  # Create hourly monitoring task
  CronCreate(
    cron="7 * * * *",  # Every hour at :07 (avoid :00 and :30)
    prompt=f"""Check training status for {experiment_name}:
    1. Read log file: {log_path}
    2. Check for errors: OOM, CUDA errors, NaN loss, process crash
    3. Check progress: current epoch, loss trend, ETA
    4. If training failed or stuck: notify user with error details and last 50 lines of log
    5. If training completed: notify user and proceed to Phase 8
    6. If training running normally: report current status (epoch, loss, ETA)""",
    recurring=True
  )
```

- [ ] Record cron job ID for later cleanup

### 7.2 Document

- [ ] Create `phase_7_full_train_report.md` with:
  - Training command (full, reproducible)
  - Process info: PID, tmux session name, log path
  - Checkpoint directory
  - Estimated completion time
  - Monitoring cron job ID
  - Monitoring instructions (manual check if needed)

### 7.3 User Confirm (BLOCKING)

- [ ] Present report to user
- [ ] Confirm training is running
- [ ] Confirm monitoring cron job is active
- [ ] Wait for explicit confirmation

Machine Gate: `.autolab/runs/<id>/contract.json` has a non-empty `locked_at`. AI MUST NOT launch training until this is true.

Checkpoint: User confirmed, training in progress with automatic monitoring

## Phase 8: Evaluation

### 8.1 Execute

- [ ] Wait for training to complete (or user signals early stop)
- [ ] Stop monitoring cron job: `CronDelete(job_id)`
- [ ] Identify best checkpoint (by validation metric)
- [ ] Run evaluation script on test set
- [ ] Collect all metrics
- [ ] **If ablations requested**: AI MUST create each ablation child run via `derive-ablation`, NOT via `start-run`. The CLI refuses any change other than the toggled module flag, guaranteeing all ablations share identical hyperparams/data/environment with the parent:
  ```bash
  python plugins/matrix-autolab/scripts/autolab_run.py derive-ablation \
      --parent <parent_run_id> --toggle <module_name>=false
  ```
  Repeat for each module to ablate. After each ablation completes, run the same training entrypoint (the modules dict in the child contract controls the flags) and finish the run with `finish-run`. Compare results across ablations with:
  ```bash
  python plugins/matrix-autolab/scripts/autolab_run.py compare-runs --run-a <parent> --run-b <child>
  ```
  to confirm the only contract diff is the toggled module(s).

### 8.2 Document

- [ ] Create `phase_8_eval_report.md` with:
  - Training completion status
  - Best checkpoint: path, epoch, validation metric
  - Test set results: all metrics, comparison to paper's reported numbers
  - Ablation results (if applicable): table showing metric per configuration
  - Prediction samples: paths to saved outputs (if applicable)

### 8.3 User Confirm (BLOCKING)

- [ ] Present report to user
- [ ] Wait for explicit confirmation
- [ ] If results unsatisfactory, discuss next steps

Machine Gate: For every ablation run, `.autolab/runs/<child_id>/contract.json` has a non-null `parent_run_id` and `ablation_diff` whose only entries are `modules.*`. If a manually-created run lacks lineage, AI MUST refuse to include its results in the comparison table.

Checkpoint: User confirmed, proceed to Phase 9

## Phase 9: Final Summary

### 9.1 Execute

- [ ] Consolidate all phase reports
- [ ] Create final implementation summary
- [ ] Archive artifacts (checkpoints, logs, configs)

### 9.2 Document

- [ ] Create `IMPLEMENTATION_SUMMARY.md` with:
  - Paper title and goal
  - Implementation status: what was implemented, what was skipped
  - Key deviations from paper and rationale
  - Final results: test metrics, comparison to paper
  - Artifacts: paths to checkpoints, logs, configs, predictions
  - Reproducibility: exact commands to reproduce results
  - Known issues or limitations
  - Recommendations for future work

### 9.3 User Confirm (BLOCKING)

- [ ] Present summary to user
- [ ] Wait for explicit confirmation
- [ ] **GATE**: User confirms autolab is complete
- [ ] Update `workflow_status.json`:
  ```json
  "autolab": {
    "status": "completed",
    "user_confirmed": true,
    "current_phase": "phase_9_final",
    "report": "experiment_docs/IMPLEMENTATION_SUMMARY.md",
    "timestamp": "<ISO8601>"
  }
  ```

- [ ] Ask user: "AutoLab complete. Do you need to train SOTA baselines for comparison? (yes/no)"
  - If **yes**: Invoke `autobaseline-0.1.0` skill using Skill tool
  - If **no**: End workflow

Checkpoint: autolab complete

```

#### `experiment_docs/progress.json`

```json
{
  "project": "{title}",
  "current_phase": "phase_1_paperbanana",
  "phases": {
    "phase_1_paperbanana": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_2_setup": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_2.5_environment": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_3_baseline_audit": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_4_modules": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_4.5_loss_check": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_4.7_pipeline_freeze": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_5_integration": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_6_short_train": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_7_full_train": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_8_eval": {"status": "pending", "report": "", "user_confirmed": false},
    "phase_9_final": {"status": "pending", "report": "", "user_confirmed": false}
  },
  "last_updated": "",
  "blocked": null
}
```

Update at every phase transition. Status: `pending` / `in_progress` / `completed` / `blocked`.

### Step 4: Execute in phases

Work through TODO.md sequentially. **CRITICAL**: After completing each phase's execution and documentation steps, you MUST:

1. Present the phase report to the user
2. Explicitly ask: "Phase X complete. Please review `experiment_docs/reports/phase_X_{name}_report.md`. Reply 'confirm' to proceed to Phase X+1, or provide feedback for changes."
3. WAIT for user response. Do NOT proceed to the next phase until user confirms.
4. If user requests changes, return to that phase's execution step and iterate.

**Baseline audit tips:**

- Search with `rg`, don't assume filenames. Look for `argparse`, `hydra`, `Trainer`, `fit(`, `train(` to find entrypoints
- Check `Dataset`, `DataLoader`, `build_dataset` for data loading
- Check `load_state_dict`, `from_pretrained`, `ckpt` for weight requirements
- Produce a short factual audit: project root, entrypoints, config mechanism, dataset format, weights, blockers

**Module implementation:**

- Smallest isolated version first
- Smoke test on synthetic tensors before touching the baseline
- One module at a time, behind config flags

**Execution rules:**

- One phase at a time, no skipping ahead
- Every phase produces a report in `experiment_docs/reports/`
- Every phase requires user confirmation before proceeding
- Update progress.json at every phase transition
- If a phase fails its checks, STOP and report to user — do not continue
- **Anti-shortcut rule**:
  - Never skip a user confirmation gate
  - Never assume user approval without explicit response
  - Never proceed to next phase "to save time"
  - Reports must contain concrete evidence (file:line, code snippets, log outputs), not summaries
  - Never bypass a Machine Gate by declaring success in prose; the JSON artifact MUST exist and the validating CLI subcommand MUST exit 0
  - Never modify or delete contract.json / environment_snapshot.json after they're locked; if the run state is genuinely wrong, abort the run with `finish-run --status aborted` and start a fresh one

### Step 5: Recover after interruption

1. Read `experiment_docs/progress.json`
2. Find last user-confirmed phase
3. Read that phase's report to understand what was done
4. Resume from first unconfirmed phase — not from memory

## Guidance

**Paper reading:**

- Check preamble for custom notation before interpreting formulas
- Subsection boundaries > prose paragraphs for module identification
- Separate architecture modules from losses from eval protocol

**Paper/code gaps:**

- Verify baseline API and tensor shapes first
- Smallest adapter that preserves paper intent
- Document deviation + rationale in phase reports
- Escalate to user when 2+ plausible implementations would materially change results

**Report writing:**

- Be specific: file paths with line numbers, not "in the model file"
- Include code snippets: 10-20 lines showing the actual implementation
- Include command outputs: actual logs, not "it worked"
- Include numbers: metric values, class counts, not "looks good"
- Reports are for user review AND for AI recovery after context loss

**User confirmation:**

- Always present the report file path
- Always ask explicitly for confirmation
- Always wait for response before proceeding
- If user is silent, remind them: "Waiting for your confirmation to proceed to Phase X+1"

**Automatic training monitoring:**

- Use CronCreate to set up hourly monitoring during Phase 7 (Full Training)
- Cron schedule: avoid :00 and :30 minutes (use :07 or other off-peak times)
- Monitor checks: errors (OOM, CUDA, NaN), progress (epoch, loss), completion status
- If training fails: immediately notify user with error details and last 50 lines of log
- If training completes: notify user and proceed to next phase
- Always record cron job ID in phase report for later cleanup
- Always stop cron job with CronDelete when training completes or Phase 8 starts

**Contract & rigor commands (quick reference):**

All commands run from the autolab project root and expect `--run-id <id>` unless noted.

| When | Command | Purpose |
|---|---|---|
| Phase 2.5 | `scan-environment --workdir <baseline>` | Detect stale checkpoints / caches / outputs |
| Phase 2.5 (re-check) | `scan-environment --workdir <baseline> --against <prior_snapshot>` | Exit 3 if new untracked artifacts appeared |
| Phase 4.7 | `freeze-pipeline --pre @pre.json --aug @aug.json` | Hash and persist preprocess + augment specs |
| Phase 6 / 7 pre-launch | `validate-contract --pre @pre.json --aug @aug.json` | Confirm pipeline matches frozen hashes (exit 3 on drift) |
| Phase 7 launch | `lock-contract` | Stamp `locked_at`; refuses if any required field is empty (exit 5) |
| Phase 8 ablation | `derive-ablation --parent <id> --toggle name=false` | Create child run sharing all parent contract fields except toggled module(s) |
| Phase 8 review | `compare-runs --run-a <id> --run-b <id>` | Show field-level diff between two contracts |

Exit codes used by these commands:

- `0` — success
- `1` — run / contract / file not found
- `2` — invalid args / malformed JSON
- `3` — hash mismatch or new environment artifact detected
- `4` — contract is locked, cannot modify
- `5` — required fields missing or contract not locked while required
- `6` — derive-ablation rejected (unknown module, no-op toggle, or non-toggle change attempted)
