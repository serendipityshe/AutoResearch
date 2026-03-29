# UI Parameters

Recommended first-pass settings:

```text
Method Content = abstract + method section text
Caption = clear overview-figure intent
exp_mode = demo_full
retrieval_setting = auto
num_candidates = 3
aspect_ratio = 21:9
max_critic_rounds = 3
```

Field guidance:

- `Method Content`: paste the abstract plus method text, not only a title.
- `Caption`: describe the intended figure, for example `Figure 1: Overview of the proposed framework`.
- `exp_mode=demo_full`: full multi-agent collaboration path.
- `retrieval_setting=auto`: default Retriever behavior.
- `num_candidates=3`: good balance for a first pass.
- `aspect_ratio=21:9`: best default for wide pipeline figures.
- `max_critic_rounds=3`: good default for iterative refinement.
