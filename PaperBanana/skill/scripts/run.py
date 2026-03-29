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

"""Unified entry point for the PaperBanana in-repo skill wrapper."""

from __future__ import annotations

import argparse
import asyncio
import base64
import importlib.util
import os
import shutil
import subprocess
import sys
from io import BytesIO
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
    if not DEMO_PATH.exists():
        print(f"ERROR: PaperBanana UI entrypoint not found: {DEMO_PATH}", file=sys.stderr)
        return 1

    print_access_instructions(args.host, args.port)
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
    return subprocess.call(command, cwd=str(PROJECT_ROOT))


def ensure_dataset(task_name: str) -> None:
    data_dir = PROJECT_ROOT / "data" / "PaperBananaBench" / task_name
    ref_path = data_dir / "ref.json"
    images_dir = data_dir / "images"
    if ref_path.exists() and images_dir.exists():
        return
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print(
            "ERROR: huggingface_hub is required for automatic dataset download.\n"
            "Install it with: pip install huggingface_hub",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Downloading PaperBananaBench/{task_name} from HuggingFace...")
    snapshot_download(
        "dwzhu/PaperBananaBench",
        repo_type="dataset",
        allow_patterns=[f"{task_name}/*"],
        local_dir=str(PROJECT_ROOT / "data" / "PaperBananaBench"),
    )


def extract_final_image_b64(result: dict, exp_mode: str) -> str | None:
    task_name = "diagram"
    for round_idx in range(3, -1, -1):
        key = f"target_{task_name}_critic_desc{round_idx}_base64_jpg"
        if key in result and result[key]:
            return result[key]

    if exp_mode == "demo_full":
        key = f"target_{task_name}_stylist_desc0_base64_jpg"
    else:
        key = f"target_{task_name}_desc0_base64_jpg"
    return result.get(key)


async def run_generate(args: argparse.Namespace) -> None:
    ensure_model_config()
    ensure_dataset(args.task)

    from agents.critic_agent import CriticAgent
    from agents.planner_agent import PlannerAgent
    from agents.polish_agent import PolishAgent
    from agents.retriever_agent import RetrieverAgent
    from agents.stylist_agent import StylistAgent
    from agents.vanilla_agent import VanillaAgent
    from agents.visualizer_agent import VisualizerAgent
    from utils import config
    from utils.paperviz_processor import PaperVizProcessor

    content = args.content
    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")
    if not content:
        print("ERROR: --content or --content-file is required.", file=sys.stderr)
        sys.exit(1)

    exp_config = config.ExpConfig(
        dataset_name="Demo",
        split_name="demo",
        exp_mode=args.exp_mode,
        retrieval_setting=args.retrieval_setting,
        main_model_name=args.main_model_name,
        image_gen_model_name=args.image_gen_model_name,
        work_dir=PROJECT_ROOT,
    )

    processor = PaperVizProcessor(
        exp_config=exp_config,
        vanilla_agent=VanillaAgent(exp_config=exp_config),
        planner_agent=PlannerAgent(exp_config=exp_config),
        visualizer_agent=VisualizerAgent(exp_config=exp_config),
        stylist_agent=StylistAgent(exp_config=exp_config),
        critic_agent=CriticAgent(exp_config=exp_config),
        retriever_agent=RetrieverAgent(exp_config=exp_config),
        polish_agent=PolishAgent(exp_config=exp_config),
    )

    data_list = []
    for i in range(args.num_candidates):
        data_list.append(
            {
                "filename": f"skill_candidate_{i}",
                "caption": args.caption,
                "content": content,
                "visual_intent": args.caption,
                "additional_info": {"rounded_ratio": args.aspect_ratio},
                "max_critic_rounds": args.max_critic_rounds,
            }
        )

    results = []
    async for result_data in processor.process_queries_batch(
        data_list, max_concurrent=args.num_candidates, do_eval=False
    ):
        results.append(result_data)

    if not results:
        print("ERROR: Pipeline returned no results.", file=sys.stderr)
        sys.exit(1)

    from PIL import Image

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for idx, result in enumerate(results):
        b64 = extract_final_image_b64(result, args.exp_mode)
        if not b64:
            print(f"WARNING: No image produced for candidate {idx}.", file=sys.stderr)
            continue

        if "," in b64:
            b64 = b64.split(",")[1]
        image_data = base64.b64decode(b64)
        img = Image.open(BytesIO(image_data))

        if args.num_candidates == 1:
            save_path = output_path
        else:
            stem = output_path.stem
            suffix = output_path.suffix or ".png"
            save_path = output_path.parent / f"{stem}_{idx}{suffix}"

        img.save(str(save_path), format="PNG")
        saved_paths.append(str(save_path))

    for path in saved_paths:
        print(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PaperBanana launcher: multi-agent Streamlit UI by default, CLI generate as fallback."
    )
    subparsers = parser.add_subparsers(dest="command")

    ui_parser = subparsers.add_parser("ui", help="Launch the PaperBanana Streamlit UI backed by demo.py.")
    ui_parser.add_argument("--host", default="127.0.0.1", help="Bind address for Streamlit.")
    ui_parser.add_argument("--port", type=int, default=8501, help="Port for Streamlit.")

    generate_parser = subparsers.add_parser("generate", help="Fallback direct CLI generation path.")
    generate_parser.add_argument("--content", type=str, default="", help="Method section text to visualize.")
    generate_parser.add_argument("--content-file", type=str, default="", help="Path to a file containing the method section text.")
    generate_parser.add_argument("--caption", type=str, required=True, help="Figure caption / visual intent.")
    generate_parser.add_argument("--task", type=str, default="diagram", choices=["diagram", "plot"], help="Task type: diagram or plot.")
    generate_parser.add_argument("--output", type=str, default="output.png", help="Output image path.")
    generate_parser.add_argument("--aspect-ratio", type=str, default="21:9", choices=["21:9", "16:9", "3:2"], help="Aspect ratio.")
    generate_parser.add_argument("--max-critic-rounds", type=int, default=3, help="Max critic refinement rounds.")
    generate_parser.add_argument("--num-candidates", type=int, default=10, help="Number of parallel candidates to generate.")
    generate_parser.add_argument("--retrieval-setting", type=str, default="auto", choices=["auto", "manual", "random", "none"], help="Retrieval mode.")
    generate_parser.add_argument("--main-model-name", type=str, default="", help="Main model name for VLM agents.")
    generate_parser.add_argument("--image-gen-model-name", type=str, default="", help="Model name for image generation.")
    generate_parser.add_argument("--exp-mode", type=str, default="demo_full", choices=["demo_full", "demo_planner_critic"], help="Pipeline mode.")
    return parser


def main() -> None:
    parser = build_parser()
    argv = sys.argv[1:]
    if not argv or argv[0].startswith("-"):
        args = parser.parse_args(["ui", *argv])
    else:
        args = parser.parse_args(argv)

    if args.command == "generate":
        asyncio.run(run_generate(args))
        return

    sys.exit(launch_ui(args))


if __name__ == "__main__":
    main()
