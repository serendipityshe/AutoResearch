# Novelty And Risk Review

Before handoff, review the design as a skeptical reviewer.

## Novelty Checks

- What is the nearest existing method?
- What exactly changes in representation, training, supervision, or evaluation?
- Why does this change matter for the domain difficulty?
- Which evidence id supports the gap?

## Risk Checks

Record risks in `risk_review` when:

- Dataset access is uncertain.
- Labels are incompatible.
- Baseline code may not reproduce.
- The module may improve a proxy metric but not the clinical or domain-relevant endpoint.
- The idea needs private data to be publication-grade.

## Language Discipline

Use hypothesis, expected, planned, or needs_evidence for untested results. Do not write measured values.
