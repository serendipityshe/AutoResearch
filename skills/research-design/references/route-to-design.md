# Route To Design

Use the confirmed route as a constraint, not as prose to copy.

## Route Clarification Pass

Produce:

- Problem statement: one task-specific sentence.
- Novelty hypothesis: what current methods fail to model.
- Dataset feasibility: which dataset roles can test the hypothesis.
- Reviewer risk: why the idea may be rejected.
- Design bridge: how the method directly addresses the difficulty.

## Evidence Binding

Every design decision should cite evidence ids from discovery artifacts. If a decision has no evidence id, mark it as an assumption and put it in `risk_review`.

## Route Smell Checks

Fail or revise when:

- The route is just a broad task name.
- The method is a loose combination of recent modules.
- The claimed novelty is not linked to a domain difficulty.
- No external or stress-test dataset can test the main claim.
