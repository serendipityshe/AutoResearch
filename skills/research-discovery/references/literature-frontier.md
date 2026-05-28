# Literature Frontier

## Time Policy

- Frontier hotspots use the latest 12 months.
- Domain difficulties use the latest 3-5 years.
- Older papers can be classical background or baselines, but not "current hotspot" evidence.

## Frontier Hotspots

A hotspot should answer why the topic is timely now. Prefer evidence from:

- New datasets or benchmarks.
- Recent high-quality journal or conference papers.
- Recent official code releases.
- Recent reporting guidelines or clinical workflow shifts.

Each hotspot should include at least two evidence ids. If only one evidence item exists, mark `signal_strength` as `weak_signal`.

## Domain Difficulties

Domain difficulties are stable obstacles that affect experimental design. Examples:

- Cross-center or device domain shift.
- Label inconsistency or noisy labels.
- Low contrast, speckle noise, small lesions, class imbalance.
- Patient-level leakage.
- Calibration or decision-threshold instability.
- Missing descriptors or annotation ambiguity.

Each difficulty must include its experiment impact, not just a description.

## Synthesis Rules

- Do not call a topic "hot" just because one paper exists.
- Separate method trends from clinical needs.
- Separate dataset availability from dataset suitability.
- Record negative evidence when a route appears attractive but lacks public data or baseline code.
