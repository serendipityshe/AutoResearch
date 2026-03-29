# Dataset Setup

When the launcher cannot download PaperBananaBench from Hugging Face, it tries only once and then starts the UI in a safe mode.

In that state:

- The UI still launches normally.
- Retrieval-based modes should stay on `none`.
- You must manually provide the reference dataset to re-enable retrieval.

Provide the dataset under:

```text
/home/hz/AutoLab/PaperBanana/data/PaperBananaBench
```

Expected structure:

```text
data/PaperBananaBench/
  diagram/
    ref.json
    images/
  plot/
    ref.json
    images/
```

Recommended method:

1. Download `dwzhu/PaperBananaBench` on a machine that can access Hugging Face.
2. Copy the dataset into `/home/hz/AutoLab/PaperBanana/data/PaperBananaBench`.
3. Restart the UI.

If the project runs on a remote server without local graphics, start the UI on the server and access it through SSH port forwarding as described in `references/remote-access.md`.
