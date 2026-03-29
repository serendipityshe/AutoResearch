# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""UI-only entry point for the PaperBanana skill wrapper."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent


def resolve_project_root() -> Path:
    candidates = [
        SKILL_ROOT.parent,
        SKILL_ROOT.parent / "PaperBanana",
    ]
    env_root = Path(os.environ["PAPERBANANA_PROJECT_ROOT"]) if "PAPERBANANA_PROJECT_ROOT" in os.environ else None
    if env_root is not None:
        candidates.insert(0, env_root)

    for candidate in candidates:
        if (candidate / "demo.py").exists():
            return candidate
    raise FileNotFoundError("Could not locate the PaperBanana project root.")


PROJECT_ROOT = resolve_project_root()
DEMO_PATH = PROJECT_ROOT / "demo.py"
sys.path.insert(0, str(PROJECT_ROOT))
DATA_ROOT = PROJECT_ROOT / "data" / "PaperBananaBench"
DATASET_FAILURE_MARKER = DATA_ROOT / ".dataset_download_failed"


def ensure_model_config() -> None:
    configs_dir = PROJECT_ROOT / "configs"
    config_path = configs_dir / "model_config.yaml"
    template_path = configs_dir / "model_config.template.yaml"
    if not config_path.exists() and template_path.exists():
        shutil.copy2(template_path, config_path)


def ensure_streamlit_available() -> None:
    if importlib.util.find_spec("streamlit") is not None:
        return
    print(
        "ERROR: streamlit is not installed in the current Python environment.\n"
        "Set up PaperBanana with uv first:\n"
        "  cd /home/hz/AutoLab/PaperBanana\n"
        "  uv venv\n"
        "  source .venv/bin/activate\n"
        "  uv python install 3.12\n"
        "  uv pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)


def write_placeholder_reference_files() -> None:
    for task_name in ("diagram", "plot"):
        task_dir = DATA_ROOT / task_name
        images_dir = task_dir / "images"
        task_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        ref_path = task_dir / "ref.json"
        if not ref_path.exists():
            ref_path.write_text("[]\n", encoding="utf-8")


def dataset_is_ready() -> bool:
    required_paths = [
        DATA_ROOT / "diagram" / "ref.json",
        DATA_ROOT / "diagram" / "images",
        DATA_ROOT / "plot" / "ref.json",
        DATA_ROOT / "plot" / "images",
    ]
    return all(path.exists() for path in required_paths)


def print_manual_dataset_instructions(reason: str) -> None:
    print("Reference dataset is not available for retrieval-based generation.")
    print(f"Reason: {reason}")
    print("PaperBanana UI will still start, but retrieval defaults should stay on 'none' until the dataset is provided.")
    print("Provide the dataset by placing PaperBananaBench under:")
    print(f"  {DATA_ROOT}")
    print("Expected structure:")
    print(f"  {DATA_ROOT / 'diagram' / 'ref.json'}")
    print(f"  {DATA_ROOT / 'diagram' / 'images'}")
    print(f"  {DATA_ROOT / 'plot' / 'ref.json'}")
    print(f"  {DATA_ROOT / 'plot' / 'images'}")
    print("Recommended method:")
    print("  1. Download the PaperBananaBench dataset on a machine that can access Hugging Face.")
    print("  2. Copy the dataset directory to the server under the path above.")
    print("  3. Restart the UI after the files are in place.")


def ensure_ui_reference_dataset() -> None:
    if dataset_is_ready():
        if DATASET_FAILURE_MARKER.exists():
            DATASET_FAILURE_MARKER.unlink()
        return

    if DATASET_FAILURE_MARKER.exists():
        write_placeholder_reference_files()
        print_manual_dataset_instructions(DATASET_FAILURE_MARKER.read_text(encoding="utf-8").strip())
        return

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        reason = "huggingface_hub is not installed in the active environment."
        write_placeholder_reference_files()
        DATASET_FAILURE_MARKER.parent.mkdir(parents=True, exist_ok=True)
        DATASET_FAILURE_MARKER.write_text(reason, encoding="utf-8")
        print_manual_dataset_instructions(reason)
        return

    try:
        print("Attempting to download PaperBananaBench once for UI retrieval support...")
        snapshot_download(
            "dwzhu/PaperBananaBench",
            repo_type="dataset",
            allow_patterns=["diagram/*", "plot/*"],
            local_dir=str(DATA_ROOT),
        )
    except Exception as exc:
        reason = f"Hugging Face download failed: {exc}"
        write_placeholder_reference_files()
        DATASET_FAILURE_MARKER.parent.mkdir(parents=True, exist_ok=True)
        DATASET_FAILURE_MARKER.write_text(reason, encoding="utf-8")
        print_manual_dataset_instructions(reason)
        return

    if dataset_is_ready():
        if DATASET_FAILURE_MARKER.exists():
            DATASET_FAILURE_MARKER.unlink()
        return

    reason = "The download completed but the expected PaperBananaBench reference files are still incomplete."
    write_placeholder_reference_files()
    DATASET_FAILURE_MARKER.parent.mkdir(parents=True, exist_ok=True)
    DATASET_FAILURE_MARKER.write_text(reason, encoding="utf-8")
    print_manual_dataset_instructions(reason)


def print_access_instructions(host: str, port: int) -> None:
    print(f"Starting PaperBanana multi-agent UI on {host}:{port}")
    if host in {"127.0.0.1", "localhost"}:
        print(f"Open this URL on the same machine: http://127.0.0.1:{port}")
        print(
            "For a remote server, create an SSH tunnel from your local machine:\n"
            f"  ssh -L {port}:127.0.0.1:{port} <user>@<server>\n"
            f"Then open http://127.0.0.1:{port} locally."
        )
    else:
        print(
            f"Local access URL if the port is exposed: http://<server-ip>:{port}\n"
            "If this is a remote machine, SSH port forwarding is usually safer."
        )


def launch_ui(args: argparse.Namespace) -> int:
    ensure_model_config()
    ensure_streamlit_available()
    ensure_ui_reference_dataset()
    if not DEMO_PATH.exists():
        print(f"ERROR: PaperBanana UI entrypoint not found: {DEMO_PATH}", file=sys.stderr)
        return 1

    print_access_instructions(args.host, args.port)
    env = os.environ.copy()
    env["PAPERBANANA_DATA_ROOT"] = str(DATA_ROOT)
    env["PAPERBANANA_REFERENCE_DATASET_READY"] = "1" if dataset_is_ready() else "0"
    env["PAPERBANANA_REFERENCE_DATASET_MARKER"] = str(DATASET_FAILURE_MARKER)
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(DEMO_PATH),
        f"--server.address={args.host}",
        f"--server.port={args.port}",
        "--browser.gatherUsageStats=false",
        "--server.headless=true",
    ]
    return subprocess.call(command, cwd=str(PROJECT_ROOT), env=env)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PaperBanana launcher: multi-agent Streamlit UI only.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address for Streamlit.")
    parser.add_argument("--port", type=int, default=8501, help="Port for Streamlit.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:])
    sys.exit(launch_ui(args))


if __name__ == "__main__":
    main()
