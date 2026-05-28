# Method Module Patterns

Each module must be a testable mechanism.

## Required Module Fields

- `name`
- `purpose`
- `inputs`
- `outputs`
- `formulas`
- `loss_terms`
- `ablation`
- `evidence_ids`

## Good Module Shape

Use this logic:

1. Motivation: which domain difficulty or frontier gap motivates the module.
2. Representation: what tensor, graph, field, probability, or set the module operates on.
3. Forward process: input to output in equations.
4. Training signal: loss term or regularizer.
5. Test: ablation and metric that would falsify the module's usefulness.

## Bad Module Shape

Reject modules that are:

- Merely named architectures with no task-specific role.
- Pure text descriptions with no equations.
- Not removable by ablation.
- Not tied to evidence ids.
