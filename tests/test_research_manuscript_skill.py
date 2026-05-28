from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "skills" / "research-manuscript" / "scripts" / "validate_manuscript_inputs.py"
AUDITOR = REPO_ROOT / "skills" / "research-manuscript" / "scripts" / "audit_main_tex.py"
SUMMARIZER = REPO_ROOT / "skills" / "research-manuscript" / "scripts" / "summarize_manuscript_status.py"


def run_script(script: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def valid_design() -> dict:
    return {
        "topic": "thyroid nodule ultrasound segmentation",
        "confirmed_route": {"route_id": "R1", "description": "anatomy-aware topology segmentation", "user_confirmed": True},
        "title_candidate": "ThyroTopoGNet: Thyroid-Context Guided Ordered Boundary Graph Learning",
        "dataset_strategy": {
            "primary": [{"name": "TN3K", "role": "primary benchmark", "rationale": "common public benchmark", "risk": "saturation", "evidence_ids": ["D-TN3K"]}],
            "validation": [{"name": "TN3K validation", "role": "model selection", "rationale": "tuning", "risk": "split leakage", "evidence_ids": ["D-TN3K"]}],
            "external_test": [{"name": "DDTI", "role": "external test", "rationale": "shift test", "risk": "version ambiguity", "evidence_ids": ["D-DDTI"]}],
            "supplementary": [{"name": "ThyroidXL", "role": "supplementary", "rationale": "large new benchmark", "risk": "access verification", "evidence_ids": ["D-XL"]}],
        },
        "frontier_landscape": [{"direction": "graph segmentation", "insight": "boundary reliability", "evidence_ids": ["P-GRAPH"]}],
        "domain_difficulties": [{"name": "blurred boundaries", "experiment_impact": "needs boundary metrics", "evidence_ids": ["P-DIFF"]}],
        "method_rationale": {
            "existing_method_problems": ["pixel losses hide fragmented contours"],
            "design_direction": "context plus ordered topology-constrained contour graph",
            "bridge_logic": "use context to localize and graph topology to regularize contours",
        },
        "proposed_method": {
            "name": "ThyroTopoGNet",
            "modules": [
                {
                    "name": "Thyroid-Region Context Encoder",
                    "purpose": "suppress extra-thyroid false positives",
                    "inputs": ["x"],
                    "outputs": ["R_g", "F_c"],
                    "formulas": ["R_g=\\sigma(H_g(E_\\theta(x)))", "F_c=F\\odot(1+R_g)"],
                    "loss_terms": ["\\mathcal{L}_{gland}"],
                    "ablation": "remove thyroid-region context branch",
                    "evidence_ids": ["P-CTX"],
                },
                {
                    "name": "Ordered Boundary Graph Decoder",
                    "purpose": "decode a closed ordered contour",
                    "inputs": ["F_c"],
                    "outputs": ["P", "\\hat{M}"],
                    "formulas": ["P=G_\\phi(F_c,A)", "\\hat{M}=\\mathcal{R}(P)"],
                    "loss_terms": ["\\mathcal{L}_{pix}", "\\mathcal{L}_{cd}"],
                    "ablation": "replace ordered graph decoder with pixel decoder",
                    "evidence_ids": ["P-GRAPH"],
                },
                {
                    "name": "Mask-Supervised Topology Optimization",
                    "purpose": "reduce fragmented contours",
                    "inputs": ["P", "M"],
                    "outputs": ["topology-regularized mask"],
                    "formulas": ["\\mathcal{L}_{topo}=|\\chi(\\hat{M})-\\chi(M)|"],
                    "loss_terms": ["\\mathcal{L}_{topo}"],
                    "ablation": "remove topology regularization",
                    "evidence_ids": ["P-DIFF"],
                },
            ],
            "total_objective": "\\mathcal{L}_{total}=\\lambda_1\\mathcal{L}_{gland}+\\lambda_2\\mathcal{L}_{pix}+\\lambda_3\\mathcal{L}_{topo}",
        },
        "experiment_alignment": [
            {
                "claim": "Context reduces false positives.",
                "module": "Thyroid-Region Context Encoder",
                "datasets": ["TN3K", "DDTI"],
                "baselines": ["U-Net", "TRFE+"],
                "metrics": ["Dice", "IoU", "outside-region false positives"],
                "ablation": "remove thyroid-region context branch",
            }
        ],
        "expected_results": [{"status": "hypothesis", "claim": "Boundary quality should improve.", "evidence_needed": "main and ablation tables"}],
        "risk_review": [{"risk": "topology loss may oversmooth malignant margins", "mitigation": "report margin sensitivity"}],
    }


def valid_blueprint() -> dict:
    return {
        "title": "ThyroTopoGNet: Thyroid-Context Guided Ordered Boundary Graph Learning",
        "central_argument": "Context and ordered topology constraints address thyroid ultrasound boundary ambiguity.",
        "section_plan": [
            {"section": "Abstract", "purpose": "formal paper abstract"},
            {"section": "Introduction", "purpose": "clinical motivation"},
            {"section": "Related Work and Design Rationale", "purpose": "grouped literature"},
            {"section": "Problem Statement", "purpose": "mathematical definitions"},
            {"section": "Method", "purpose": "modules and formulas"},
            {"section": "Planned Study Design", "purpose": "real experiment plan"},
            {"section": "Planned Results Presentation", "purpose": "TBD tables"},
            {"section": "Risks", "purpose": "limitations"},
            {"section": "Discussion", "purpose": "restrained interpretation"},
        ],
        "claim_to_experiment_map": [{"claim": "Context reduces false positives.", "experiment": "ablation", "evidence_status": "planned"}],
    }


def valid_evidence() -> dict:
    return {
        "papers": [{"id": "P-GRAPH", "title": "Graph segmentation", "year": 2026, "url": "https://example.org/graph"}],
        "datasets": [{"id": "D-TN3K", "name": "TN3K", "url": "https://example.org/tn3k"}],
        "code_repositories": [],
        "baseline_candidates": [{"id": "B-UNET", "name": "U-Net", "url": "https://arxiv.org/abs/1505.04597"}],
        "web_sources": [],
        "pubmed_records": [],
        "zotero_items": [],
        "user_sources": [],
    }


def write_valid_inputs(root: Path) -> None:
    write_json(root / "research_design.json", valid_design())
    write_json(root / "manuscript_blueprint.json", valid_blueprint())
    write_json(root / "search_evidence.json", valid_evidence())


def valid_main_tex() -> str:
    return r"""
\documentclass{article}
\usepackage{amsmath}
\begin{document}
\title{ThyroTopoGNet}
\maketitle
\begin{abstract}
Thyroid ultrasound segmentation is limited by low contrast, speckle noise, and ambiguous lesion margins. Existing pixel-mask AI methods may produce fragmented contours and extra-thyroid false positives even when overlap metrics appear acceptable. We propose ThyroTopoGNet, a thyroid-context guided ordered boundary graph framework for mask-supervised nodule segmentation. The method combines thyroid-region context encoding, fixed-topology graph decoding, differentiable rasterization, and topology-aware mask losses. Planned evaluation on TN3K, DDTI, and supplementary thyroid ultrasound datasets will test overlap, boundary, topology, and external-validation endpoints; no measured numerical results are reported before experiments are completed.
\end{abstract}
\section{Introduction}
Clinical importance motivates robust thyroid ultrasound segmentation. Low contrast and boundary ambiguity expose the limits of pixel-mask objectives. Context and topology are therefore needed. The contributions are context encoding, ordered graph decoding, and topology-aware evaluation.
\section{Related Work and Design Rationale}
\subsection{Static thyroid ultrasound segmentation}
Prior methods optimize pixel overlap.
\subsection{Thyroid-region context and anatomy priors}
Gland context can suppress non-thyroid false positives.
\subsection{Boundary graph and topology-aware segmentation}
Graph decoders expose contour continuity.
\subsection{Uncertain-region and robustness-aware segmentation}
Uncertain boundaries require dedicated metrics.
\subsection{Cross-dataset generalization}
External validation tests acquisition shift.
\subsection{Why direct transfer is insufficient}
Existing components cannot be copied directly because nodules lack a universal atlas and ultrasound datasets vary in annotation and acquisition.
\section{Problem Statement}
Let $\mathcal{D}=\{(x_i,M_i)\}_{i=1}^{N}$, where $x$ is an ultrasound image and $M$ is a mask. The model predicts thyroid context $R_g$, graph nodes $P$, and $\hat{M}=\mathcal{R}(P)$. The objective is to optimize boundary, topology, and pixel consistency under dataset constraints.
\section{Method}
\subsection{Thyroid-Region Context Encoder}
Motivation: reduce false positives. Input: $x$. Output: $R_g$ and $F_c$.
\begin{equation}R_g=\sigma(H_g(E_\theta(x))),\quad F_c=F\odot(1+R_g)\end{equation}
Loss: $\mathcal{L}_{gland}$. Ablation: remove thyroid-region context branch.
\subsection{Ordered Boundary Graph Decoder}
Motivation: produce a closed ordered contour. Input: $F_c$. Output: $P$ and $\hat{M}$.
\begin{equation}P=G_\phi(F_c,A),\quad \hat{M}=\mathcal{R}(P)\end{equation}
Loss: $\mathcal{L}_{pix}$ and $\mathcal{L}_{cd}$. Ablation: replace ordered graph decoder with pixel decoder.
\subsection{Mask-Supervised Topology Optimization}
Motivation: reduce contour fragmentation. Input: $P$ and $M$. Output: topology-regularized prediction.
\begin{equation}\mathcal{L}_{topo}=|\chi(\hat{M})-\chi(M)|\end{equation}
Loss: $\mathcal{L}_{topo}$. Ablation: remove topology regularization.
\begin{equation}\mathcal{L}_{total}=\lambda_1\mathcal{L}_{gland}+\lambda_2\mathcal{L}_{pix}+\lambda_3\mathcal{L}_{topo}\end{equation}
\section{Planned Study Design}
Datasets and their role include primary TN3K, validation split, external test DDTI, and supplementary ThyroidXL. Inclusion/exclusion criteria, preprocessing, implementation preset, baselines, metrics, ablation, and statistics will be reported.
\section{Planned Results Presentation}
\begin{tabular}{llll}
Method & Dice & IoU & HD95 \\
U-Net & TBD & TBD & TBD \\
ThyroTopoGNet & TBD & TBD & TBD \\
\end{tabular}
\section{Risks}
Dataset access, external validation, topology regularization oversmoothing, and baseline reproducibility remain risks.
\section{Discussion}
The interpretation is restrained until experiments are complete.
\begin{thebibliography}{9}
\bibitem{graph} Graph segmentation. Available at: \url{https://example.org/graph}.
\end{thebibliography}
\end{document}
"""


class ResearchManuscriptSkillTests(unittest.TestCase):
    def test_input_validator_fails_without_design_and_blueprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(VALIDATOR, Path(tmp), "--root", "research_autopilot")
            self.assertEqual(result.returncode, 3)
            self.assertIn("research_design.json", result.stderr)
            self.assertIn("manuscript_blueprint.json", result.stderr)

    def test_input_validator_accepts_complete_manuscript_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "research_autopilot"
            write_valid_inputs(root)
            result = run_script(VALIDATOR, Path(tmp), "--root", str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["method_modules"], 3)
            self.assertTrue((root / "citation_plan.json").exists())
            self.assertTrue((root / "manuscript_source_map.json").exists())

    def test_auditor_rejects_internal_abstract_language_and_fake_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "research_autopilot"
            write_valid_inputs(root)
            bad_tex = valid_main_tex().replace("We propose", "This document presents a manuscript-ready study design for")
            bad_tex = bad_tex.replace("TBD & TBD & TBD", "0.91 & 0.84 & 3.2")
            write_text(root / "main.tex", bad_tex)
            result = run_script(AUDITOR, Path(tmp), "--root", str(root))
            self.assertEqual(result.returncode, 3)
            self.assertIn("banned abstract phrase", result.stderr)
            self.assertIn("non-TBD numeric result", result.stderr)

    def test_auditor_accepts_template_style_manuscript_with_tbd_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "research_autopilot"
            write_valid_inputs(root)
            write_text(root / "main.tex", valid_main_tex())
            result = run_script(AUDITOR, Path(tmp), "--root", str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertGreaterEqual(payload["method_modules_detected"], 3)

            summary = run_script(SUMMARIZER, Path(tmp), "--root", str(root))
            self.assertEqual(summary.returncode, 0, summary.stderr)
            summary_payload = json.loads(summary.stdout)
            self.assertTrue(summary_payload["artifacts"]["main_tex"])
            self.assertEqual(summary_payload["audit"]["errors"], 0)


if __name__ == "__main__":
    unittest.main()
