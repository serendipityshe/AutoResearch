---
name: paperbanana-0.1.0
description: Generate publication-quality academic diagrams from paper methodology text using an interactive web UI. Supports direct LaTeX source input (e.g., main.tex) — automatically extracts abstract and method sections as content.
license: MIT-0
---

# PaperBanana

Generate publication-quality academic diagrams and pipeline figures from a paper's methodology section and figure caption. PaperBanana orchestrates a multi-agent pipeline (Retriever, Planner, Stylist, Visualizer, Critic) to produce camera-ready figures suitable for venues like NeurIPS, ICML, and ACL.

## Integration with autolab / autobaseline

PaperBanana is the visualization backend for the full paper workflow:

1. **autolab** → implements the method, runs ablations → calls paperbanana to generate the main framework figure
2. **autobaseline** → trains SOTA baselines, collects metrics → calls paperbanana to generate comparison diagrams
3. **paperbanana** (standalone) → generates figures from any method text or LaTeX source

When called from autolab or autobaseline, content is automatically extracted from `main.tex` (abstract + method sections). No manual `--content` input needed.

## Prerequisites

Clone the PaperBanana repository:

```bash
git clone https://github.com/serendipityshe/PaperBanana-meng.git
cd PaperBanana-meng
```

## Usage Workflow

**Primary workflow: Launch Web UI for user to operate interactively.**

When a user requests diagram generation:

1. **Collect API Configuration** (use AskUserQuestion):
   - Which API provider? (OpenAI Official / Google Gemini / Custom Third-Party)
   - API Key
   - Text model name
   - Image generation model name
   - Base URL (if Custom provider)

2. **Configure the environment**:
   - Set environment variables or update `configs/model_config.yaml`

3. **Check data availability**:
   - If HuggingFace download fails, provide the dataset URL and ask user to download manually

4. **Launch the web UI** (preferred method):
   ```bash
   cd PaperBanana-meng
   bash scripts/run_demo.sh
   ```

5. **Provide SSH forwarding instructions** if on remote server:
   ```bash
   ssh -L 8501:localhost:8501 user@remote-server
   ```

6. **Inform user about cost parameters**:
   - Explain `num_candidates` and `max_critic_rounds` impact on token usage
   - Suggest starting with low values for testing

7. **Let user operate the web UI** to generate diagrams interactively

**Do NOT write Python scripts to automate diagram generation unless explicitly requested by the user.**
   - Suggest starting with low values for testing
7. **Let user operate the web UI** to generate diagrams interactively

## API Configuration

Before running, configure your API credentials. You will be prompted to choose:

**Option 1: OpenAI Official API**

- API Key: Your OpenAI API key
- Text Model: e.g., `gpt-4o`, `gpt-4-turbo`
- Image Model: e.g., `dall-e-3`

**Option 2: Google Gemini Official API**

- API Key: Your Google API key
- Text Model: e.g., `gemini-2.0-flash-exp`, `gemini-1.5-pro`
- Image Model: e.g., `gemini-3.1-flash-image-preview`

**Option 3: Custom Third-Party Provider**

- API Key: Your provider's API key
- Base URL: e.g., `https://api.openrouter.ai/v1`
- Text Model: Provider-specific model name
- Image Model: Provider-specific image generation model

Set these in `configs/model_config.yaml` or as environment variables:

```bash
export OPENAI_API_KEY="your-key"  # Option 1
export GOOGLE_API_KEY="your-key"  # Option 2
export OPENAI_COMPATIBLE_API_KEY="your-key"  # Option 3
export OPENAI_COMPATIBLE_BASE_URL="https://..."  # Option 3
```

## Data Setup

The benchmark data will be automatically created as empty placeholders. If you need the full PaperBananaBench dataset:

1. Download from: https://huggingface.co/datasets/google/PaperBananaBench
2. If HuggingFace is inaccessible, request manual download instructions
3. Extract to `data/PaperBananaBench/`

For basic usage, the auto-generated empty data structure is sufficient.

## Running PaperBanana

### Recommended: Interactive Web UI

Start the Streamlit web interface:

```bash
bash scripts/run_demo.sh
```

This will:

- Create a virtual environment if needed
- Install dependencies
- Start Streamlit on `http://0.0.0.0:8501`

**Important Cost Considerations:**

- `num_candidates`: Number of parallel diagram generations (default: 10) — directly multiplies API costs
- `max_critic_rounds`: Refinement iterations (default: 3) — each round costs additional tokens
- Recommended for testing: `num_candidates=1-3`, `max_critic_rounds=1-2`

**For Remote Servers (SSH Port Forwarding):**

If running on a remote server without a browser, forward the port to your local machine:

```bash
# On your local machine:
ssh -L 8501:localhost:8501 user@remote-server

# Then open in your local browser:
http://localhost:8501
```

### Alternative: Command-Line Mode

For automated workflows or integration with other tools:

```bash
python skill/run.py \
  --content "METHOD_TEXT" \
  --caption "FIGURE_CAPTION" \
  --task diagram \
  --output output.png \
  --num-candidates 3 \
  --max-critic-rounds 2
```

Or use the batch processing script:

```bash
bash scripts/run_main.sh
```

## LaTeX Source Integration (For Automated Workflows)

When integrating with autolab/autobaseline or using command-line mode, extract content from LaTeX files:

1. Read the `.tex` file
2. Extract the `\begin{abstract}...\end{abstract}` block as the paper summary
3. Extract the `\section{Method}` (or `\section{Methodology}`) through the next `\section` as the methodology text
4. Concatenate: `"Abstract:\n{abstract}\n\nMethodology:\n{method}"` → pass as `--content`
5. Generate a caption from the paper title: `"Figure 1: Overview of the proposed {title} framework"`

This is the recommended approach when integrating with autolab/autobaseline — the caller reads main.tex, extracts the relevant sections, and passes them to paperbanana.

## Integration with autolab / autobaseline

PaperBanana is the visualization backend for the full paper workflow:

1. **autolab** → implements the method, runs ablations → calls paperbanana to generate the main framework figure
2. **autobaseline** → trains SOTA baselines, collects metrics → calls paperbanana to generate comparison diagrams
3. **paperbanana** (standalone) → generates figures from any method text or LaTeX source

When called from autolab or autobaseline, content is automatically extracted from `main.tex` (abstract + method sections). No manual `--content` input needed.

## Command-Line Parameters

| Parameter                  | Required | Default                            | Description                                                                        |
| -------------------------- | -------- | ---------------------------------- | ---------------------------------------------------------------------------------- |
| `--content`              | Yes*     |                                    | Method section text to visualize                                                   |
| `--content-file`         | Yes*     |                                    | Path to a file containing the method text (alternative to `--content`)           |
| `--caption`              | Yes      |                                    | Figure caption or visual intent                                                    |
| `--task`                 | No       | `diagram`                        | Task type:`diagram`                                                              |
| `--output`               | No       | `output.png`                     | Output image file path                                                             |
| `--aspect-ratio`         | No       | `21:9`                           | Aspect ratio:`21:9`, `16:9`, or `3:2`                                        |
| `--max-critic-rounds`    | No       | `3`                              | Maximum critic refinement iterations                                               |
| `--num-candidates`       | No       | `10`                             | Number of parallel candidates to generate                                          |
| `--retrieval-setting`    | No       | `auto`                           | Retrieval mode:`auto`, `manual`, `random`, or `none`                       |
| `--main-model-name`      | No       | `gemini-3.1-pro-preview`         | Main model for VLM agents                                                          |
| `--image-gen-model-name` | No       | `gemini-3.1-flash-image-preview` | Model for image generation                                                         |
| `--exp-mode`             | No       | `demo_full`                      | Pipeline:`demo_full` (with Stylist) or `demo_planner_critic` (without Stylist) |

*One of `--content` or `--content-file` is required.

When `--num-candidates` > 1, output files are named `<stem>_0.png`, `<stem>_1.png`, etc.

## Output

The absolute path of each saved image is printed to stdout, one per line.

---
