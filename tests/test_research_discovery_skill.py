from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "skills" / "research-discovery" / "scripts" / "validate_discovery_artifacts.py"
SUMMARIZER = REPO_ROOT / "skills" / "research-discovery" / "scripts" / "summarize_discovery_status.py"


def run_script(script: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_valid_discovery(root: Path) -> None:
    write_json(
        root / "discovery_plan.json",
        {
            "topic": "thyroid nodule ultrasound segmentation",
            "created_at": "2026-05-28",
            "time_policy": {
                "frontier_hotspots": "latest_12_months",
                "domain_difficulties": "last_3_to_5_years",
            },
            "concepts": ["thyroid nodule", "ultrasound", "segmentation"],
            "source_plan": ["PubMed", "Semantic Scholar", "GitHub", "Hugging Face"],
            "queries": ["thyroid nodule ultrasound segmentation dataset"],
            "screening_rules": ["stable locator required"],
        },
    )
    write_json(
        root / "search_evidence.json",
        {
            "papers": [
                {
                    "id": "paper_recent_dataset",
                    "title": "Recent thyroid ultrasound benchmark",
                    "year": 2026,
                    "doi": "10.0000/example",
                    "source_adapter": "scholarly",
                    "why_relevant": "latest benchmark evidence",
                    "limitations": "sample counts require local verification",
                },
                {
                    "id": "paper_domain_shift",
                    "title": "Domain shift in thyroid ultrasound",
                    "year": 2024,
                    "url": "https://example.org/domain-shift",
                    "source_adapter": "pubmed",
                    "why_relevant": "domain difficulty evidence",
                    "limitations": "private data",
                },
            ],
            "datasets": [
                {
                    "id": "dataset_tn3k",
                    "name": "TN3K",
                    "url": "https://github.com/example/tn3k",
                    "task": ["segmentation"],
                    "reported_size": "3493 images",
                    "label_type": "mask",
                    "access_status": "public",
                    "license": "MIT",
                    "candidate_roles": ["primary"],
                    "recent_usage": "used by recent thyroid ultrasound papers",
                    "risk_notes": "patient identifiers need verification",
                    "source_adapter": "github",
                    "why_relevant": "primary benchmark candidate",
                    "limitations": "split verification needed",
                }
            ],
            "code_repositories": [
                {
                    "id": "repo_baseline",
                    "name": "TRFE-Net",
                    "url": "https://github.com/example/trfe",
                    "repo_role": "baseline",
                    "official_status": "official",
                    "license": "MIT",
                    "train_entrypoints": ["train.py"],
                    "eval_entrypoints": ["test.py"],
                    "dataset_support": ["TN3K"],
                    "maintenance_status": "stable",
                    "reproducibility_risk": "dependency pinning needed",
                    "source_adapter": "github",
                    "why_relevant": "baseline implementation",
                    "limitations": "environment needs verification",
                }
            ],
            "baseline_candidates": [
                {
                    "id": "baseline_unet",
                    "name": "U-Net",
                    "url": "https://arxiv.org/abs/1505.04597",
                    "baseline_type": "segmentation",
                    "why_required": "classic segmentation control",
                    "expected_comparison_role": "generic baseline",
                    "source_ids": ["repo_baseline"],
                    "source_adapter": "scholarly",
                    "why_relevant": "minimum comparison",
                    "limitations": "not thyroid-specific",
                }
            ],
            "web_sources": [],
            "pubmed_records": [],
            "zotero_items": [],
            "user_sources": [],
            "adapter_runs": [],
        },
    )
    write_json(
        root / "research_landscape.json",
        {
            "dataset_candidates": [
                {
                    "dataset_id": "dataset_tn3k",
                    "name": "TN3K",
                    "candidate_roles": ["primary"],
                    "evidence_ids": ["dataset_tn3k"],
                }
            ],
            "frontier_hotspots": [
                {
                    "time_window": "latest_12_months",
                    "hotspot": "open thyroid ultrasound benchmarks",
                    "why_now": "new benchmark papers and repos appeared recently",
                    "evidence_ids": ["paper_recent_dataset", "dataset_tn3k"],
                    "signal_strength": "supported",
                }
            ],
            "domain_difficulties": [
                {
                    "time_window": "last_3_to_5_years",
                    "difficulty": "domain shift",
                    "experiment_impact": "requires external testing",
                    "evidence_ids": ["paper_domain_shift", "dataset_tn3k"],
                }
            ],
            "baseline_candidates": [
                {
                    "name": "U-Net",
                    "baseline_type": "segmentation",
                    "why_required": "classic baseline",
                    "source_ids": ["baseline_unet"],
                }
            ],
            "method_gap_matrix": [
                {
                    "gap": "pixel overlap ignores contour topology",
                    "evidence_ids": ["paper_recent_dataset"],
                }
            ],
            "route_candidates": [
                {
                    "route_id": "R1",
                    "name": "Topology-aware segmentation",
                    "core_claim": "improve contour stability",
                    "dataset_requirements": ["TN3K primary"],
                    "method_direction": "graph-based boundary decoding",
                    "baseline_requirements": ["U-Net"],
                    "evidence_ids": ["paper_recent_dataset", "dataset_tn3k", "baseline_unet"],
                    "failure_risks": ["external data may be too small"],
                    "recommendation": "recommended",
                }
            ],
        },
    )
    (root / "research_brief.md").write_text(
        "# 研究发现简报\n\n候选路线：Topology-aware segmentation。\n",
        encoding="utf-8",
    )


class ResearchDiscoverySkillTests(unittest.TestCase):
    def test_validator_fails_when_required_artifacts_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_script(VALIDATOR, cwd, "--root", "research_autopilot")
            self.assertEqual(result.returncode, 3)
            self.assertIn("discovery_plan.json", result.stderr)

    def test_validator_accepts_complete_discovery_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            root = cwd / "research_autopilot"
            write_valid_discovery(root)
            result = run_script(VALIDATOR, cwd, "--root", str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["errors"], [])

    def test_summarizer_reports_discovery_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            root = cwd / "research_autopilot"
            write_valid_discovery(root)
            result = run_script(SUMMARIZER, cwd, "--root", str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["evidence_counts"]["papers"], 2)
            self.assertEqual(payload["landscape_counts"]["route_candidates"], 1)


if __name__ == "__main__":
    unittest.main()
