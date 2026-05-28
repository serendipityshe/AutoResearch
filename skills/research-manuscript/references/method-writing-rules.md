# Method Writing Rules

Method is the core of the manuscript.

## Per-Module Requirements

Each module must include:

- motivation
- input
- output
- forward equation
- loss or regularizer
- ablation

## Global Requirements

- Define the task mathematically before modules.
- Use formulas from `research_design.json`.
- Include the total objective `\mathcal{L}_{total}`.
- Keep symbol definitions consistent with the design contract.
- Do not introduce a new module that is not in `research_design.json`.

## Common Failure

Do not write a prose-only Method. If a module cannot be expressed by equations and a loss or ablation, keep it out of the paper draft.
