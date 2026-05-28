# Experiment Alignment

Every contribution must have a planned test.

## Required Alignment Fields

- `claim`
- `module`
- `datasets`
- `baselines`
- `metrics`
- `ablation`

## Alignment Rules

- Each method module must appear in `experiment_alignment`.
- Each module's ablation must appear in `experiment_alignment`.
- The primary dataset tests core performance.
- Validation data tunes or selects design choices.
- External test data checks shift and robustness.
- Supplementary data tests sensitivity or publication-grade extensions.

## Baseline Rules

Include:

- One classical baseline for interpretability.
- One strong recent baseline.
- One task- or dataset-specific baseline when available.
- One ablation per proposed module.
