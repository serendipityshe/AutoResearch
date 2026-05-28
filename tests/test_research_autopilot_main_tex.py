from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "research_autopilot.py"


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def extract_abstract(tex: str) -> str:
    start = tex.index("\\begin{abstract}") + len("\\begin{abstract}")
    end = tex.index("\\end{abstract}")
    return tex[start:end]


def rich_design() -> dict:
    return {
        "topic": "thyroid nodule ultrasound segmentation",
        "confirmed_route": {
            "route_id": "R1",
            "description": "Study predictive ultrasound field modeling plus mask-supervised boundary graph learning.",
            "user_confirmed": True,
        },
        "title_candidate": "ThyroFieldGNet: Predictive Ultrasound Field Modeling and Boundary Graph Learning for Thyroid Nodule Segmentation",
        "dataset_strategy": {
            "primary": [
                {
                    "name": "TN3K",
                    "role": "main static segmentation benchmark",
                    "rationale": "large public thyroid nodule segmentation set",
                    "risk": "label provenance needs verification",
                    "evidence_ids": ["D-TN3K"],
                }
            ],
            "validation": [
                {
                    "name": "Stanford Thyroid Ultrasound Cine-clip",
                    "role": "clip-aware validation",
                    "rationale": "supports temporal stability evaluation",
                    "risk": "small pathology-confirmed subset",
                    "evidence_ids": ["D-STANFORD-CINE"],
                }
            ],
            "external_test": [
                {
                    "name": "DDTI",
                    "role": "external static robustness set",
                    "rationale": "device and dataset shift stress test",
                    "risk": "version conflicts must be fixed",
                    "evidence_ids": ["D-DDTI"],
                }
            ],
            "supplementary": [
                {
                    "name": "Optional in-house multi-center cohort",
                    "role": "publication-grade external cohort",
                    "rationale": "tests true center shift",
                    "risk": "requires ethics and data access",
                    "evidence_ids": [],
                }
            ],
        },
        "frontier_landscape": [
            {
                "direction": "thyroid ultrasound cine learning",
                "insight": "neighboring frames provide lesion continuity that static masks ignore",
                "evidence_ids": ["P-WEBB-2021"],
            },
            {
                "direction": "graph-based medical segmentation from masks",
                "insight": "closed contours can be trained from standard pixel supervision",
                "evidence_ids": ["P-MASK-GNET"],
            },
        ],
        "domain_difficulties": [
            {
                "name": "speckle noise and low boundary contrast",
                "impact": "pixel overlap can hide fragmented or noisy contour failures",
                "evidence_ids": ["P-THYROID-SEG"],
            },
            {
                "name": "cross-dataset acquisition shift",
                "impact": "external testing is required before robustness claims",
                "evidence_ids": ["D-DDTI"],
            },
        ],
        "method_rationale": {
            "existing_method_problems": [
                "Static pixel-only methods optimize Dice while ignoring contour ordering and topology.",
                "Single-frame models underuse cine sweeps and nearby views available in routine ultrasound.",
                "Unstructured masks are unstable for TI-RADS shape and margin descriptors.",
            ],
            "design_direction": "learn a compact ultrasound field latent and decode it into an ordered closed contour graph supervised by masks",
        },
        "proposed_method": {
            "name": "ThyroFieldGNet",
            "overview": "A two-stage framework that learns a view-aware nodule latent and decodes a fixed-topology boundary graph.",
            "modules": [
                {
                    "name": "Predictive Ultrasound Field Modeling",
                    "purpose": "learn a compact latent from context frames by reconstructing held-out target-frame features",
                    "inputs": ["context frames", "view-position tokens"],
                    "outputs": ["nodule field latent", "target feature field"],
                    "formulas": [
                        "z = E_{\\phi}\\left(\\{B_{\\phi}(x_t)+e(\\pi_t)\\}_{t\\in\\mathcal{C}}\\right)",
                        "\\hat{F}_{\\tau}=D_{\\psi}(z,e(\\pi_{\\tau}))",
                    ],
                    "loss_terms": ["\\mathcal{L}_{\\text{field}}"],
                    "ablation": "without predictive field modeling",
                },
                {
                    "name": "Fixed-topology Boundary Graph Decoder",
                    "purpose": "decode a closed ordered contour from latent and target-frame features",
                    "inputs": ["target feature field", "nodule latent"],
                    "outputs": ["ordered node coordinates", "rasterized mask"],
                    "formulas": [
                        "P_{\\tau}=G_{\\omega}(\\hat{F}_{\\tau}, z, A)",
                        "\\hat{M}_{\\tau}=\\mathcal{R}(P_{\\tau})",
                    ],
                    "loss_terms": ["\\mathcal{L}_{\\text{CD}}", "\\mathcal{L}_{\\text{pix}}"],
                    "ablation": "replace graph decoder with pixel decoder",
                },
                {
                    "name": "Anchor-aligned Cyclic Graph Normalization",
                    "purpose": "stabilize contour node ordering using a lesion-relative superficial anchor",
                    "inputs": ["contour pixels", "predicted circular node sequence"],
                    "outputs": ["anchor-normalized contour graph"],
                    "formulas": [
                        "a_{\\tau}^{\\star}=\\arg\\min_{p\\in C_{\\tau}} p_y",
                        "\\tilde{P}_{\\tau}=\\operatorname{shift}(P_{\\tau}, a_{\\tau}^{\\star})",
                    ],
                    "loss_terms": ["\\mathcal{L}_{\\text{temp}}"],
                    "ablation": "without anchor-aligned cyclic normalization",
                },
            ],
            "total_objective": "\\mathcal{L}_{\\text{total}}=\\lambda_{\\text{field}}\\mathcal{L}_{\\text{field}}+\\lambda_{\\text{CD}}\\mathcal{L}_{\\text{CD}}+\\lambda_{\\text{pix}}\\mathcal{L}_{\\text{pix}}+\\lambda_{\\text{temp}}\\mathcal{L}_{\\text{temp}}",
        },
        "expected_results": [
            {
                "status": "hypothesis",
                "claim": "The graph representation should reduce topological defects while preserving Dice and IoU.",
                "evidence_needed": "main comparison and topology metrics",
            },
            {
                "status": "expected",
                "claim": "Clip-aware field modeling should improve temporal contour stability.",
                "evidence_needed": "node jitter and descriptor coefficient of variation",
            },
        ],
    }


def evidence() -> dict:
    return {
        "schema_version": "0.1.0",
        "artifact": "search_evidence",
        "query": "thyroid nodule ultrasound segmentation",
        "adapter_runs": [],
        "papers": [
            {
                "id": "P-WEBB-2021",
                "title": "Automatic deep learning semantic segmentation of ultrasound thyroid cineclips using recurrent fully convolutional networks",
                "venue_or_source": "IEEE Access",
                "year": "2021",
                "url": "https://doi.org/10.1109/ACCESS.2020.3048163",
                "source_adapter": "scholarly",
            },
            {
                "id": "P-MASK-GNET",
                "title": "Mask-HybridGNet: Graph-based segmentation with emergent anatomical correspondence from pixel-level supervision",
                "venue_or_source": "arXiv",
                "year": "2026",
                "url": "https://arxiv.org/abs/2602.21179",
                "source_adapter": "scholarly",
            },
        ],
        "datasets": [
            {
                "id": "D-TN3K",
                "name": "TN3K",
                "url": "https://github.com/haifangong/TRFE-Net-for-thyroid-nodule-segmentation",
                "source_adapter": "github",
            },
            {
                "id": "D-DDTI",
                "name": "DDTI",
                "url": "https://doi.org/10.1117/12.2073532",
                "source_adapter": "scholarly",
            },
        ],
        "code_repositories": [],
        "baseline_candidates": [],
        "web_sources": [],
        "pubmed_records": [],
        "zotero_items": [],
        "user_sources": [],
    }


class ResearchAutopilotMainTexTests(unittest.TestCase):
    def test_build_main_tex_fails_without_research_design(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_cli(cwd, "build-main-tex")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("research_design.json", result.stderr)

    def test_validate_research_design_rejects_underdeveloped_method(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            root = cwd / "research_autopilot"
            design = rich_design()
            design["proposed_method"]["modules"] = design["proposed_method"]["modules"][:2]
            write_json(root / "research_design.json", design)
            result = run_cli(cwd, "validate-research-design")
            self.assertEqual(result.returncode, 3)
            self.assertIn("at least 3 method modules", result.stdout)

    def test_validate_research_design_rejects_missing_dataset_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            root = cwd / "research_autopilot"
            design = rich_design()
            del design["dataset_strategy"]["external_test"]
            write_json(root / "research_design.json", design)
            result = run_cli(cwd, "validate-research-design")
            self.assertEqual(result.returncode, 3)
            self.assertIn("dataset_strategy missing roles", result.stdout)

    def test_validate_research_design_rejects_unconfirmed_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            root = cwd / "research_autopilot"
            design = rich_design()
            del design["confirmed_route"]["user_confirmed"]
            write_json(root / "research_design.json", design)
            result = run_cli(cwd, "validate-research-design")
            self.assertEqual(result.returncode, 3)
            self.assertIn("user_confirmed", result.stdout)

    def test_build_main_tex_renders_formula_rich_english_manuscript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            root = cwd / "research_autopilot"
            write_json(root / "research_design.json", rich_design())
            write_json(root / "search_evidence.json", evidence())
            result = run_cli(cwd, "build-main-tex", "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            output = root / "main.tex"
            text = output.read_text(encoding="utf-8")
            self.assertIn("\\section{Method}", text)
            self.assertIn("Predictive Ultrasound Field Modeling", text)
            self.assertIn("\\mathcal{L}_{\\text{total}}", text)
            self.assertIn("Datasets and their role", text)
            self.assertIn("without predictive field modeling", text)
            self.assertIn("TBD", text)
            self.assertNotIn("manuscript generation", text)
            self.assertNotIn("The draft treats", text)
            self.assertNotIn("evidence-gated writing", text)
            self.assertNotIn("focuses on Study", text)
            self.assertNotIn("..", text)
            abstract = extract_abstract(text)
            self.assertIn("We propose", abstract)
            for banned in [
                "scaffold",
                "manuscript-ready",
                "planned study",
                "planned hypotheses",
                "Matrix-AutoLab",
                "needs\\_evidence",
                "TBD",
                "logs",
                "figures",
            ]:
                self.assertNotIn(banned, abstract)
            raw = output.read_bytes()
            self.assertIn(b"\r\n", raw)
            self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))

    def test_template_scientific_content_is_not_reused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            root = cwd / "research_autopilot"
            template = cwd / "template.tex"
            template.write_text(
                "\\documentclass[12pt]{article}\n"
                "\\usepackage{amsmath}\n"
                "\\begin{document}\n"
                "DO_NOT_COPY_THIS_SCIENTIFIC_CLAIM\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            write_json(root / "research_design.json", rich_design())
            write_json(root / "search_evidence.json", evidence())
            result = run_cli(cwd, "build-main-tex", "--template", str(template), "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (root / "main.tex").read_text(encoding="utf-8")
            self.assertIn("\\documentclass[12pt]{article}", text)
            self.assertIn("\\usepackage{amsmath}", text)
            self.assertNotIn("DO_NOT_COPY_THIS_SCIENTIFIC_CLAIM", text)


if __name__ == "__main__":
    unittest.main()
