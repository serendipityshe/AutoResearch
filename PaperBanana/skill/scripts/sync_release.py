#!/usr/bin/env python3
"""Sync the canonical PaperBanana skill into the release directory."""

from __future__ import annotations

import shutil
from pathlib import Path


SOURCE_ROOT = Path("/home/hz/AutoLab/PaperBanana/skill")
RELEASE_ROOT = Path("/home/hz/AutoLab/paperbanana-0.1.0")
COPY_ITEMS = [
    "SKILL.md",
    "clawhub.json",
    "agents",
    "references",
    "scripts",
]


def main() -> None:
    RELEASE_ROOT.mkdir(parents=True, exist_ok=True)
    for relative in COPY_ITEMS:
        src = SOURCE_ROOT / relative
        dst = RELEASE_ROOT / relative
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    wrapper_path = RELEASE_ROOT / "run.py"
    wrapper_path.write_text(
        "# Generated from /home/hz/AutoLab/PaperBanana/skill\n"
        "from scripts.run import main\n\n"
        "if __name__ == \"__main__\":\n"
        "    main()\n",
        encoding="utf-8",
    )
    copied_sync = RELEASE_ROOT / "scripts" / "sync_release.py"
    if copied_sync.exists():
        copied_sync.unlink()


if __name__ == "__main__":
    main()
