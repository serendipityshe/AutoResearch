---
name: paperbanana
description: Generate publication-quality academic diagrams from paper methodology text. Supports direct LaTeX source input (e.g., main.tex) — automatically extracts abstract and method sections as content.
license: MIT-0
dependencies:
  env:
    - OPENROUTER_API_KEY (recommended)
    - GOOGLE_API_KEY (alternative)
    - OPENAI_COMPATIBLE_API_KEY + OPENAI_COMPATIBLE_BASE_URL (third-party)
  runtime:
    - python3
    - uv
---

# PaperBanana

Generate publication-quality academic diagrams and pipeline figures from a paper's methodology section and figure caption. PaperBanana orchestrates a multi-agent pipeline (Retriever, Planner, Stylist, Visualizer, Critic) to produce camera-ready figures suitable for venues like NeurIPS, ICML, and ACL.

## Integration with autolab / autobaseline

PaperBanana is the visualization backend for the full paper workflow:

1. **autolab** → implements the method, runs ablations → calls paperbanana to generate the main framework figure
2. **autobaseline** → trains SOTA baselines, collects metrics → calls paperbanana to generate comparison diagrams
3. **paperbanana** (standalone) → generates figures from any method text or LaTeX source

When called from autolab or autobaseline, content is automatically extracted from `main.tex` (abstract + method sections). No manual `--content` input needed.

## LaTeX Source Integration

When a `main.tex` (or any `.tex` file) is available, extract content automatically instead of requiring raw text:

1. Read the `.tex` file
2. Extract the `\begin{abstract}...\end{abstract}` block as the paper summary
3. Extract the `\section{Method}` (or `\section{Methodology}`) through the next `\section` as the methodology text
4. Concatenate: `"Abstract:\n{abstract}\n\nMethodology:\n{method}"` → pass as `--content`
5. Generate a caption from the paper title: `"Figure 1: Overview of the proposed {title} framework"`

This is the recommended approach when integrating with autolab/autobaseline — the caller reads main.tex, extracts the relevant sections, and passes them to paperbanana.

## Prerequisites

Clone the PaperBanana repository first:

```bash
git clone https://github.com/serendipityshe/PaperBanana-meng.git
cd PaperBanana-meng
```

## Environment Setup

```bash
uv pip install -r requirements.txt
```

Set your API key via environment variable or in `configs/model_config.yaml`.

**Option 1 (Recommended): OpenRouter API key** — one key for both text reasoning and image generation:
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

**Option 2: Google API key** — direct access to Gemini API:
```bash
export GOOGLE_API_KEY="your-key-here"
```

**Option 3: OpenAI-compatible third-party API** — any provider with OpenAI-compatible endpoint:
```bash
export OPENAI_COMPATIBLE_API_KEY="your-key-here"
export OPENAI_COMPATIBLE_BASE_URL="https://your-provider.com/v1"
```

If multiple keys are configured, priority: OpenAI-compatible > OpenRouter > Google.

## Usage

**Original pipeline** (requires full PaperVizAgent framework):
```bash
python skill/run.py \
  --content "METHOD_TEXT" \
  --caption "FIGURE_CAPTION" \
  --task diagram \
  --output output.png
```

**Standalone mode** (uses OpenAI-compatible API, no extra dependencies):
```bash
pip install openai Pillow
python paperbanana_standalone.py \
  --content "METHOD_TEXT" \
  --caption "FIGURE_CAPTION" \
  --output output.png
```

API credentials are configured directly in `paperbanana_standalone.py` (API_KEY, BASE_URL, TEXT_MODEL, IMAGE_MODEL).

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--content` | Yes* | | Method section text to visualize |
| `--content-file` | Yes* | | Path to a file containing the method text (alternative to `--content`) |
| `--caption` | Yes | | Figure caption or visual intent |
| `--task` | No | `diagram` | Task type: `diagram` |
| `--output` | No | `output.png` | Output image file path |
| `--aspect-ratio` | No | `21:9` | Aspect ratio: `21:9`, `16:9`, or `3:2` |
| `--max-critic-rounds` | No | `3` | Maximum critic refinement iterations |
| `--num-candidates` | No | `10` | Number of parallel candidates to generate |
| `--retrieval-setting` | No | `auto` | Retrieval mode: `auto`, `manual`, `random`, or `none` |
| `--main-model-name` | No | `gemini-3.1-pro-preview` | Main model for VLM agents. Provider auto-detected from configured API key |
| `--image-gen-model-name` | No | `gemini-3.1-flash-image-preview` | Model for image generation. Also supports `gemini-3-pro-image-preview` |
| `--exp-mode` | No | `demo_full` | Pipeline: `demo_full` (with Stylist) or `demo_planner_critic` (without Stylist) |

*One of `--content` or `--content-file` is required.

When `--num-candidates` > 1, output files are named `<stem>_0.png`, `<stem>_1.png`, etc.

## Output

The absolute path of each saved image is printed to stdout, one per line.

## Examples

### Diagram (Standalone with third-party API)

```bash
python paperbanana_standalone.py \
  --content "We propose a transformer-based encoder-decoder architecture. The encoder consists of 12 self-attention layers with residual connections. The decoder uses cross-attention to attend to encoder outputs and generates the target sequence autoregressively." \
  --caption "Figure 1: Overview of the proposed transformer architecture" \
  --output architecture.png \
  --num-candidates 1
```

### Diagram (Original pipeline)

```bash
python skill/run.py \
  --content "We propose a transformer-based encoder-decoder architecture. The encoder consists of 12 self-attention layers with residual connections. The decoder uses cross-attention to attend to encoder outputs and generates the target sequence autoregressively." \
  --caption "Figure 1: Overview of the proposed transformer architecture" \
  --task diagram \
  --output architecture.png
```


## Illustration Prompt Template

When generating the main framework figure for a paper, use this prompt structure as the `--caption` to guide the Visualizer toward publication-quality output:

```
You are an expert Scientific Illustrator for top-tier AI conferences (NeurIPS/CVPR/ICML).
Generate a professional illustration (main figure) for this paper.

Visual Style Requirements:
1. Style: Flat vector illustration, clean lines, academic aesthetic. Similar to figures in DeepMind or OpenAI papers.
2. Layout: Organized flow (Left-to-Right or Top-to-Bottom). Group related components logically.
3. Color Palette: Professional pastel tones. White background.
4. Text Rendering: Include legible text labels for key modules or equations (e.g., "Encoder", "Loss", "Transformer").
5. Negative Constraints: NO photorealistic photos, NO messy sketches, NO unreadable text, NO 3D shading artifacts.

Highlight the core novelty. Ensure the connection logic makes sense.
Figure caption: {caption}
```

Replace `{caption}` with the actual figure caption (e.g., "Figure 1: Overview of the proposed frequency-disentangled domain generalization framework").

### Example: From LaTeX source

```bash
# Step 1: Extract abstract + method from main.tex (done by the caller, e.g., autolab)
# Step 2: Write extracted content to a temp file
# Step 3: Call paperbanana

python skill/run.py \
  --content-file /tmp/extracted_method.txt \
  --caption "You are an expert Scientific Illustrator for top-tier AI conferences. Generate a professional illustration for this paper. Style: Flat vector, clean lines, academic aesthetic. Layout: Left-to-Right organized flow. Color: Professional pastel tones, white background. Include legible text labels for key modules. NO photorealistic photos, NO messy sketches. Highlight the core novelty. Figure caption: Figure 1: Overview of the proposed framework" \
  --task diagram \
  --output paper_figures/framework.png \
  --num-candidates 3 \
  --aspect-ratio 21:9
```

## Important Notes

- **Runtime**: A single candidate typically takes 3-10 minutes depending on model and network conditions. With the default 10 candidates running in parallel, expect ~10-30 minutes total. Plan accordingly.
- **API calls**: Each candidate involves multiple LLM calls (Retriever + Planner + Stylist + Visualizer + up to 3 Critic rounds). Candidates run in parallel for efficiency.
- **Image generation**: The Visualizer agent calls an image generation model (Gemini Image) to render diagrams.

## About

PaperBanana is based on the **PaperVizAgent** framework, a reference-driven multi-agent system for automated academic illustration. It was developed as part of the research paper:

> **PaperBanana: Automating Academic Illustration for AI Scientists**
> Dawei Zhu, Rui Meng, Yale Song, Xiyu Wei, Sujian Li, Tomas Pfister, Jinsung Yoon
> arXiv:2601.23265

The framework introduces a collaborative team of five specialized agents — Retriever, Planner, Stylist, Visualizer, and Critic — to transform raw scientific content into publication-quality diagrams. Evaluation is conducted on the **PaperBananaBench** benchmark.

