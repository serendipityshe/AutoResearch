---
name: matrix-autolab
description: Unified entry point for the Matrix-AutoLab paper-to-experiment workflow. Use when the user wants to run, resume, or inspect the full PaperBanana -> AutoLab -> AutoBaseline pipeline from a single plugin entry.
---

# Matrix-AutoLab

Matrix-AutoLab is the unified coordinator for the AutoLab plugin. It keeps the three specialized skills available as separate entries while giving users one guided starting point for the full workflow.

## Pipeline

The plugin exposes four skill entries:

1. `matrix-autolab` - unified coordinator and recommended starting point
2. `paperbanana` - framework figure generation from paper methodology
3. `autolab` - method implementation, experiments, and ablations
4. `autobaseline` - SOTA baseline training and comparison

## When To Use

Use this skill when the user:

- wants to start from a paper source such as `main.tex`
- asks in Chinese or English to complete implementation, training, ablation, or baseline work from `main.tex`
- asks to run or resume the whole AutoLab workflow
- is unsure whether to start with figure generation, method implementation, or baseline comparison
- wants a single entry point for the plugin

Common trigger examples:

- `根据 main.tex 帮我完成相关消融实验`
- `根据 main.tex 帮我完成论文方法实现、训练和消融实验`
- `Use matrix-autolab to reproduce this paper and run ablations`

Use the specialized skills directly when the user explicitly asks only for that part:

- framework figure only -> `paperbanana`
- method implementation or ablations only -> `autolab`
- SOTA baseline comparison only -> `autobaseline`

## Current Packaging Scope

This first plugin version packages the existing workflow without changing its execution behavior.

- Existing status files such as `workflow_status.json`, `experiment_docs/progress.json`, and `baselines/progress.json` remain supported.
- The `.autolab/` run archive now includes gate files used to prevent skipped phases and undocumented implementation details.
- Do not move existing outputs into `.autolab/` unless the user explicitly asks for that migration in a later task.

## Anti-Skip Gate Protocol

This plugin must treat `.autolab/runs/<run_id>/gate_status.json` as the current source of truth for what may be executed next. Chat history and narrative summaries are not enough for long tasks.

For every phase or meaningful substep:

1. Define paper or experiment requirements with `autolab_gate.py define-requirement`.
2. Start exactly one active step with `autolab_gate.py start-step`.
3. Execute only that active step.
4. Record evidence with `autolab_gate.py add-evidence`.
5. Run `autolab_gate.py check-step`.
6. If the step requires user confirmation, present the report and wait; after explicit confirmation, record it with `autolab_gate.py confirm-step`.
7. Complete the step only after `check-step` returns `ok: true`.

The agent must stop when `check-step` reports blockers. Do not proceed to a later phase to "save time" or because the intended work seems obvious.

## Startup Procedure

When invoked:

1. Inspect the current project root.
2. Check for `main.tex` or another paper source file.
3. Check for local recording state:
   - If `.autolab/project.json` and `.autolab/workflow_status.json` exist, read them and summarize the active run plus the latest known status for each recorded skill.
   - If an active run exists, read `.autolab/runs/<active_run_id>/gate_status.json`, `.autolab/runs/<active_run_id>/requirements.json`, and `.autolab/runs/<active_run_id>/phase_plan.json`. Summarize the current allowed step and any blockers before recommending work.
   - If `.autolab/` does not exist, tell the user local recording is not initialized and recommend:
     ```bash
     python3 plugins/matrix-autolab/scripts/autolab_run.py init-project
     ```
   - If legacy workflow files exist but `.autolab/` does not, explain that the project is readable in compatibility mode.
   - Local recording utilities are optional in this phase. Do not block legacy workflow execution when `.autolab/` is absent.
4. Check for existing legacy workflow state:
   - `workflow_status.json`
   - `experiment_docs/progress.json`
   - `baselines/progress.json`
- `paperbanana_completion_report.md`
- `experiment_docs/IMPLEMENTATION_SUMMARY.md`
- `baselines/BASELINE_COMPARISON_REPORT.md`

5. Summarize the detected state to the user.
6. Recommend the next skill:
   - no framework figure and no implementation state -&gt; `paperbanana` or `autolab` Phase 1
   - implementation not complete -&gt; `autolab`
   - implementation complete and baseline comparison not complete -&gt; `autobaseline`
   - all complete -&gt; summarize available reports and ask what the user wants to inspect or rerun

## Dashboard

The plugin includes a local-first dashboard app at `apps/dashboard` and registers it through `.app.json`. The dashboard visualizes workflow status, run history, metrics, failures, reports, artifacts, and sync readiness. It is read-only in the first version and must not upload data or mutate `.autolab/` records.

Run locally from `plugins/matrix-autolab/apps/dashboard`:

```bash
npm install
npm run dev
```

Then open `http://127.0.0.1:3217`.

## Local Recording Utilities

The local recording utilities write optional project/run metadata under `.autolab/`. They are available for projects that want structured local run records, but legacy workflow execution must continue to work when `.autolab/` is absent.

Initialize local recording for a project:

```bash
python3 plugins/matrix-autolab/scripts/autolab_run.py init-project
```

Start a paper reproduction run from this unified entry point:

```bash
```
python3 plugins/matrix-autolab/scripts/autolab_run.py start-run --kind paper_reproduction --entry-skill matrix-autolab
```

Record an event:

```bash
python3 plugins/matrix-autolab/scripts/autolab_event.py event --run-id <run_id> --skill matrix-autolab --type phase_started --message "Started Matrix-AutoLab coordination"
```

Record a metric:

```bash
python3 plugins/matrix-autolab/scripts/autolab_event.py metric --run-id <run_id> --source autolab --name validation_accuracy --value 0.87
```

Collect changed files:

```bash
python3 plugins/matrix-autolab/scripts/autolab_collect.py changed-files --run-id <run_id>
```

## Coordination Rules

- Current gate status beats chat memory. If `gate_status.json` has an active step, resume that step first.
- Do not start a phase or substep without first declaring it through `autolab_gate.py start-step`.
- Do not mark a phase done until `autolab_gate.py check-step --run-id <run_id>` returns `ok: true`.
- Every paper-derived implementation detail must appear in `requirements.json` and have evidence before the related implementation step can complete.
- Do not bypass the phase gates defined in `autolab` or `autobaseline`.
- Do not assume user confirmation from existing files alone. Report the detected status and ask before continuing.
- Prefer resuming from the last confirmed phase rather than restarting.
- If a specialized skill has stricter rules, follow the specialized skill.
- Keep generated reports factual and path-specific.

## Delegation

After recommending the next step, invoke or instruct the user to invoke the appropriate specialized skill:

- `paperbanana` for diagram generation
- `autolab` for method implementation and ablation workflow
- `autobaseline` for SOTA baseline comparison

If the environment supports automatic skill invocation, use it. Otherwise, tell the user the exact skill entry to run next.

## Future Extension Points

The following capabilities are planned for later iterations and should be treated as design targets, not current requirements:

- `.autolab/` project-local run archive
- event and metric JSONL capture
- changed file manifest
- local-first server synchronization
- Matrix-AutoLab web dashboard with login, project list, run history, phase reports, metrics, and failure records
