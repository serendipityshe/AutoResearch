"""Working-directory scanner for stale checkpoints, caches, and outputs.

Used by the Phase 2.5 environment sanity gate. Detects artifacts that the
autolab skill did not create itself (prior failed runs, manual training,
other workflows) so the user can explicitly accept / move-aside / delete each
one before implementation begins.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any

from autolab_common import utc_now


CHECKPOINT_SUFFIXES = (".pth", ".ckpt", ".bin", ".safetensors", ".pt")
OUTPUT_DIR_NAMES = (
    "outputs",
    "runs",
    "wandb",
    "lightning_logs",
    "tensorboard",
    "tb_logs",
    "mlruns",
)
CACHE_DIR_NAMES = ("cache", ".cache", "processed")
SKIP_DIRS = (".git", ".autolab", "node_modules", "__pycache__", ".venv", "venv", ".tox", "dist", "build")
LARGE_BINARY_THRESHOLD = 1 * 1024 * 1024  # 1 MiB
MAX_HASH_BYTES = 100 * 1024 * 1024


def _file_sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        if path.stat().st_size > MAX_HASH_BYTES:
            return ""
    except OSError:
        return ""
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _git_tracked_set(workdir: Path) -> set[str]:
    """Return relative paths tracked by git in workdir, or empty set if not a repo."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=workdir,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return set()
    if result.returncode != 0:
        return set()
    paths = result.stdout.split(b"\x00")
    return {
        p.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        for p in paths
        if p
    }


def _looks_like_text(path: Path, sniff_bytes: int = 4096) -> bool:
    try:
        with path.open("rb") as handle:
            chunk = handle.read(sniff_bytes)
    except OSError:
        return True
    if not chunk:
        return True
    if b"\x00" in chunk:
        return False
    try:
        chunk.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def _classify(rel_path: str, suffix: str, is_dir: bool) -> str | None:
    parts = rel_path.replace("\\", "/").split("/")
    if is_dir:
        name = parts[-1]
        if name in OUTPUT_DIR_NAMES:
            return "output"
        if name in CACHE_DIR_NAMES:
            return "cache"
        if "data" in parts and name in ("cache", "processed"):
            return "cache"
        return None
    if suffix.lower() in CHECKPOINT_SUFFIXES:
        return "checkpoint"
    return None


def _stat_safe(path: Path) -> tuple[int, str]:
    try:
        st = path.stat()
    except OSError:
        return 0, ""
    mtime = ""
    try:
        from datetime import datetime, timezone

        mtime = (
            datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except (OSError, ValueError, OverflowError):
        mtime = ""
    return st.st_size, mtime


def _dir_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for fname in files:
            try:
                total += (Path(root) / fname).stat().st_size
            except OSError:
                continue
    return total


def scan(workdir: Path) -> dict[str, Any]:
    """Walk workdir and return a snapshot dict of detected stale artifacts."""
    workdir = workdir.resolve()
    if not workdir.exists() or not workdir.is_dir():
        raise FileNotFoundError(f"Working directory not found: {workdir}")

    tracked = _git_tracked_set(workdir)
    items: list[dict[str, Any]] = []
    seen_dirs: set[str] = set()

    for root, dirnames, filenames in os.walk(workdir):
        root_path = Path(root)
        # Skip noisy directories in-place
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        # Detect cache/output directories themselves
        for dname in list(dirnames):
            full = root_path / dname
            try:
                rel = full.relative_to(workdir).as_posix()
            except ValueError:
                continue
            kind = _classify(rel, "", is_dir=True)
            if kind is None:
                continue
            if rel in seen_dirs:
                continue
            seen_dirs.add(rel)
            size = _dir_size(full)
            _, mtime = _stat_safe(full)
            items.append(
                {
                    "path": rel,
                    "kind": kind,
                    "is_dir": True,
                    "size_bytes": size,
                    "mtime": mtime,
                    "sha256": "",
                    "git_tracked": rel in tracked,
                }
            )
            # Don't descend into output/cache dirs after capturing them
            dirnames.remove(dname)

        for fname in filenames:
            full = root_path / fname
            try:
                rel = full.relative_to(workdir).as_posix()
            except ValueError:
                continue
            suffix = full.suffix
            kind = _classify(rel, suffix, is_dir=False)
            size, mtime = _stat_safe(full)

            if kind is None:
                # Catch large unclassified binaries that aren't git-tracked
                if size < LARGE_BINARY_THRESHOLD or rel in tracked:
                    continue
                if _looks_like_text(full):
                    continue
                kind = "binary"

            items.append(
                {
                    "path": rel,
                    "kind": kind,
                    "is_dir": False,
                    "size_bytes": size,
                    "mtime": mtime,
                    "sha256": _file_sha256(full),
                    "git_tracked": rel in tracked,
                }
            )

    items.sort(key=lambda x: (x["kind"], x["path"]))
    return {
        "captured_at": utc_now(),
        "workdir": str(workdir),
        "items": items,
    }


def render_report(snapshot: dict[str, Any]) -> str:
    """Render a Markdown report from a scan snapshot."""
    lines: list[str] = []
    lines.append("# Phase 2.5 — Environment Sanity Scan")
    lines.append("")
    lines.append(f"- Workdir: `{snapshot['workdir']}`")
    lines.append(f"- Captured at: {snapshot['captured_at']}")
    lines.append(f"- Items found: {len(snapshot['items'])}")
    lines.append("")
    if not snapshot["items"]:
        lines.append("**No stale artifacts detected.** Working directory is clean.")
        lines.append("")
        return "\n".join(lines)

    lines.append("## Detected artifacts")
    lines.append("")
    lines.append("| Kind | Path | Size | Tracked | SHA256 (prefix) |")
    lines.append("|---|---|---:|---|---|")
    for item in snapshot["items"]:
        size_mb = item["size_bytes"] / (1024 * 1024) if item["size_bytes"] else 0
        size_str = f"{size_mb:.2f} MiB" if size_mb else "0"
        sha = item["sha256"][:12] if item["sha256"] else "—"
        tracked = "yes" if item["git_tracked"] else "no"
        suffix = "/" if item["is_dir"] else ""
        lines.append(
            f"| {item['kind']} | `{item['path']}{suffix}` | {size_str} | {tracked} | `{sha}` |"
        )
    lines.append("")
    lines.append("## Required action")
    lines.append("")
    lines.append(
        "For each item above, decide one of: **keep** (acknowledge it as input), "
        "**move-aside** (rename to `*.bak/` so the skill ignores it), or **delete**. "
        "Record decisions in `environment_decisions.json` before proceeding to Phase 3."
    )
    lines.append("")
    return "\n".join(lines)


def initial_decisions(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return a stub decisions file with all entries marked 'pending'."""
    return {
        "captured_at": snapshot["captured_at"],
        "workdir": snapshot["workdir"],
        "decisions": [
            {
                "path": item["path"],
                "kind": item["kind"],
                "sha256": item["sha256"],
                "decision": "pending",
                "rationale": "",
            }
            for item in snapshot["items"]
        ],
    }


def diff_against(prior: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Compare two snapshots; return new items that appeared in current but not prior."""
    prior_keys = {(item["path"], item["sha256"]) for item in prior.get("items", [])}
    new_items = [
        item
        for item in current.get("items", [])
        if (item["path"], item["sha256"]) not in prior_keys
    ]
    return {
        "captured_at": current.get("captured_at", ""),
        "new_items": new_items,
    }
