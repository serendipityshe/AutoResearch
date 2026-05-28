from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "skills" / "research-design" / "scripts" / "validate_research_design_artifacts.py"
SUMMARIZER = REPO_ROOT / "skills" / "research-design" / "scripts" / "summarize_design_status.py"


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


def valid_design() -> dict:
    return {
        "topic": "thyroid nodule ultrasound segmentation",
        "confirmed_route": {
            "route_id": "R1",
            "description": "Anatomy-aware topology-consistent boundary segmentation",
            "user_confirmed": True,
        },
        "title_candidate": "ThyroTopoNet: Anatomy-Aware Boundary Graph Learning for Thyroid Nodule Ultrasound Segmentation",
        "dataset_strategy": {
            "primary": [{"name": "TN3K", "role": "primary benchmark", "evidence_ids": ["D-TN3K"]}],
            "validation": [{"name": "Stanford cine clips", "role": "temporal validation", "evidence_ids": ["D-CINE"]}],
            "external_test": [{"name": "DDTI", "role": "external robustness", "evidence_ids": ["D-DDTI"]}],
            "supplementary": [{"name": "in-house multi-center cohort", "role": "supplementary stress test"}],
        },
        "frontier_landscape": [
            {"direction": "anatomy-aware segmentation", "insight": "thyroid region context helps reduce false contours", "evidence_ids": ["P-ANATOMY"]},
            {"direction": "topology-aware graph decoding", "insight": "ordered contours expose boundary stability errors", "evidence_ids": ["P-GRAPH"]},
        ],
        "domain_difficulties": [
            {"name": "low boundary contrast", "experiment_impact": "requires contour-sensitive metrics", "evidence_ids": ["P-DIFF"]},
            {"name": "cross-center shift", "experiment_impact": "requires external testing", "evidence_ids": ["D-DDTI"]},
        ],
        "method_rationale": {
            "existing_method_problems": [
                "Pixel-overlap objectives hide boundary fragmentation.",
                "Single-frame segmentation underuses cine context.",
            ],
            "design_direction": "Decode an ordered boundary graph from anatomy-conditioned ultrasound features.",
            "bridge_logic": "Map boundary uncertainty to topology-constrained contour supervision.",
        },
        "proposed_method": {
            "name": "ThyroTopoNet",
            "modules": [
                {
                    "name": "Anatomy-Conditioned Context Encoder",
                    "purpose": "Represent thyroid-region context before nodule decoding.",
                    "inputs": ["image", "thyroid region prior"],
                    "outputs": ["context feature map"],
                    "formulas": ["F_c = E_\\theta(x, r)"],
                    "loss_terms": ["\\mathcal{L}_{ctx}"],
                    "ablation": "remove anatomy-conditioned context encoder",
                    "evidence_ids": ["P-ANATOMY"],
                },
                {
                    "name": "Fixed-Topology Boundary Graph Decoder",
                    "purpose": "Decode a closed ordered contour instead of an unconstrained mask.",
                    "inputs": ["context feature map"],
                    "outputs": ["ordered contour nodes", "rasterized mask"],
                    "formulas": ["P = G_\\phi(F_c, A)", "\\hat{M}=\\mathcal{R}(P)"],
                    "loss_terms": ["\\mathcal{L}_{cd}", "\\mathcal{L}_{pix}"],
                    "ablation": "replace graph decoder with pixel decoder",
                    "evidence_ids": ["P-GRAPH"],
                },
                {
                    "name": "Anchor-Aligned Cyclic Normalization",
                    "purpose": "Resolve ambiguous node ordering around the closed contour.",
                    "inputs": ["ordered contour nodes", "boundary anchor"],
                    "outputs": ["normalized contour sequence"],
                    "formulas": ["a^*=\\arg\\min_{p\\in C} p_y", "\\tilde{P}=\\operatorname{shift}(P,a^*)"],
                    "loss_terms": ["\\mathcal{L}_{cyc}"],
                    "ablation": "remove anchor-aligned cyclic normalization",
                    "evidence_ids": ["P-GRAPH", "P-DIFF"],
                },
            ],
            "total_objective": "\\mathcal{L}_{total}=\\lambda_{ctx}\\mathcal{L}_{ctx}+\\lambda_{cd}\\mathcal{L}_{cd}+\\lambda_{pix}\\mathcal{L}_{pix}+\\lambda_{cyc}\\mathcal{L}_{cyc}",
        },
        "experiment_alignment": [
            {
                "claim": "Boundary graph decoding improves contour topology.",
                "module": "Fixed-Topology Boundary Graph Decoder",
                "datasets": ["TN3K", "DDTI"],
                "baselines": ["U-Net", "TRFE-Net"],
                "metrics": ["Dice", "IoU", "HD95", "boundary F-score", "component count"],
                "ablation": "replace graph decoder with pixel decoder",
            },
            {
                "claim": "Anatomy-conditioned context should reduce thyroid-region false positives.",
                "module": "Anatomy-Conditioned Context Encoder",
                "datasets": ["TN3K", "DDTI"],
                "baselines": ["U-Net", "TRFE-Net"],
                "metrics": ["Dice", "IoU", "false positive area"],
                "ablation": "remove anatomy-conditioned context encoder",
            },
            {
                "claim": "Anchor alignment should stabilize cyclic contour ordering.",
                "module": "Anchor-Aligned Cyclic Normalization",
                "datasets": ["TN3K", "Stanford cine clips"],
                "baselines": ["ThyroTopoNet without anchor alignment"],
                "metrics": ["node jitter", "HD95", "boundary F-score"],
                "ablation": "remove anchor-aligned cyclic normalization",
            },
        ],
        "expected_results": [
            {
                "status": "hypothesis",
                "claim": "The proposed contour representation should reduce fragmented boundaries without sacrificing overlap accuracy.",
                "evidence_needed": "main comparison and ablation tables",
            }
        ],
        "risk_review": [
            {"risk": "External datasets may have incompatible annotations.", "mitigation": "report dataset-specific preprocessing and sensitivity analysis."}
        ],
    }


def valid_blueprint() -> dict:
    return {
        "title": "ThyroTopoNet: Anatomy-Aware Boundary Graph Learning for Thyroid Nodule Ultrasound Segmentation",
        "central_argument": "Topology-constrained contour decoding can better match ultrasound nodule boundary ambiguity than pixel-only masks.",
        "section_plan": [
            {"section": "Abstract", "purpose": "State problem, method, planned validation, and expected contribution without measured numbers."},
            {"section": "Method", "purpose": "Define data, modules, formulas, losses, and ablations."},
            {"section": "Planned Study Design", "purpose": "Map datasets, baselines, metrics, and risks."},
        ],
        "claim_to_experiment_map": [
            {
                "claim": "Boundary graph decoding improves contour topology.",
                "experiment": "main comparison plus graph decoder ablation",
                "evidence_status": "planned",
            }
        ],
    }


def write_valid_artifacts(root: Path) -> None:
    write_json(root / "research_design.json", valid_design())
    write_json(root / "manuscript_blueprint.json", valid_blueprint())


class ResearchDesignSkillTests(unittest.TestCase):
    def test_validator_fails_when_design_artifacts_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_script(VALIDATOR, cwd, "--root", "research_autopilot")
            self.assertEqual(result.returncode, 3)
            self.assertIn("research_design.json", result.stderr)

    def test_validator_rejects_unconfirmed_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            root = cwd / "research_autopilot"
            write_valid_artifacts(root)
            design = valid_design()
            design["confirmed_route"]["user_confirmed"] = False
            write_json(root / "research_design.json", design)
            result = run_script(VALIDATOR, cwd, "--root", str(root))
            self.assertEqual(result.returncode, 3)
            self.assertIn("route is not confirmed", result.stderr)

    def test_validator_rejects_modules_without_evidence_and_ablation_alignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            root = cwd / "research_autopilot"
            write_valid_artifacts(root)
            design = valid_design()
            del design["proposed_method"]["modules"][0]["evidence_ids"]
            design["experiment_alignment"] = []
            write_json(root / "research_design.json", design)
            result = run_script(VALIDATOR, cwd, "--root", str(root))
            self.assertEqual(result.returncode, 3)
            self.assertIn("lacks evidence_ids", result.stderr)
            self.assertIn("experiment_alignment", result.stderr)

    def test_validator_accepts_complete_design_package_and_summarizer_counts_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            root = cwd / "research_autopilot"
            write_valid_artifacts(root)
            result = run_script(VALIDATOR, cwd, "--root", str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])

            summary = run_script(SUMMARIZER, cwd, "--root", str(root))
            self.assertEqual(summary.returncode, 0, summary.stderr)
            summary_payload = json.loads(summary.stdout)
            self.assertEqual(summary_payload["method_modules"], 3)
            self.assertEqual(summary_payload["dataset_roles"], ["external_test", "primary", "supplementary", "validation"])


if __name__ == "__main__":
    unittest.main()
