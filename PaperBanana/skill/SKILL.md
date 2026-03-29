---
name: paperbanana
description: Launch the PaperBanana multi-agent web UI, configure figure-generation parameters, handle local or remote Streamlit access, and complete the figure stage before continuing into autolab or autobaseline.
---

# PaperBanana

Use the real PaperBanana project at `/home/hz/AutoLab/PaperBanana` through a skill wrapper that defaults to the Streamlit UI and the full multi-agent pipeline.

Canonical source lives in `/home/hz/AutoLab/PaperBanana/skill`.
`/home/hz/AutoLab/paperbanana-0.1.0` is a generated release artifact, not the primary edit location.

## Contract

- Default to the UI in `demo.py`.
- Default to the multi-agent path, not a single direct image API shortcut.
- Recommend `exp_mode=demo_full` unless the user explicitly wants a faster degraded mode.
- Use this as the figure-generation stage before `autolab`.

`demo_full` runs:
- Retriever
- Planner
- Stylist
- Visualizer
- Critic

`demo_planner_critic` is a fallback, not the default.

## Environment

Run in `/home/hz/AutoLab/PaperBanana`:

```bash
uv venv
source .venv/bin/activate
uv python install 3.12
uv pip install -r requirements.txt
cd skill
python run.py
```

If `configs/model_config.yaml` is missing, the launcher creates it from the template.

## API Keys

Set at least one:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

or:

```bash
export GOOGLE_API_KEY="..."
```

or:

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://your-provider.com/v1"
```

These keys supply model access only. The workflow still goes through the multi-agent pipeline in `demo.py`.

## Launch

Default launch:

```bash
python run.py
```

Variants:

```bash
python run.py --host 127.0.0.1 --port 8501
python run.py --host 0.0.0.0 --port 8501
```

This starts:

```bash
streamlit run /home/hz/AutoLab/PaperBanana/demo.py
```

## References

- For parameter guidance, read `references/ui-params.md`.
- For local vs remote access, read `references/remote-access.md`.

## Pipeline Position

1. Use `paperbanana` first to launch the UI and complete the figure stage.
2. Continue with `autolab` for implementation and experiments.
3. Use `autobaseline` after autolab if baseline comparisons are needed.

## Fallback CLI

The launcher also supports a non-default CLI path:

```bash
python run.py generate --content-file method.txt --caption "Figure 1: Overview of the proposed framework"
```

Use the fallback only when the UI is not appropriate for the task.
