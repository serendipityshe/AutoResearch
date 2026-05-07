from __future__ import annotations

import argparse
import os
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "plugins" / "matrix-autolab" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import autolab_gate  # noqa: E402
import autolab_run  # noqa: E402
from autolab_common import ensure_project, read_json, run_root  # noqa: E402


RUN_ID = "20260101T000000Z-abcdef"


class AutoLabGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.tempdir.name)

    def tearDown(self) -> None:
        os.chdir(self.old_cwd)
        self.tempdir.cleanup()

    def create_run(self) -> Path:
        root = Path.cwd()
        project = ensure_project(root)
        directory, _ = autolab_run._create_run_skeleton(
            run_id=RUN_ID,
            project=project,
            kind="paper_reproduction",
            entry_skill="matrix-autolab",
            paper_source="main.tex",
            root=root,
        )
        return directory

    def test_start_run_creates_gate_files(self) -> None:
        directory = self.create_run()

        self.assertTrue((directory / "phase_plan.json").exists())
        self.assertTrue((directory / "requirements.json").exists())
        self.assertTrue((directory / "gate_status.json").exists())
        gate_status = read_json(directory / "gate_status.json", {})
        self.assertIsNone(gate_status["current_step"])
        self.assertEqual(gate_status["completed_steps"], [])

    def test_gate_blocks_until_artifact_evidence_and_confirmation_exist(self) -> None:
        self.create_run()
        start_args = argparse.Namespace(
            run_id=RUN_ID,
            phase="phase_4_modules",
            step="module_a",
            summary="Implement module A",
            required_artifact=["experiment_docs/reports/phase_4_modules_report.md"],
            requirement=["method.module_a"],
            check=["implementation, smoke test, and report evidence are present"],
            report="experiment_docs/reports/phase_4_modules_report.md",
            user_confirmation_required=True,
            replace=False,
        )

        self.assertEqual(autolab_gate.cmd_start_step(start_args), 0)
        self.assertEqual(autolab_gate.cmd_check_step(argparse.Namespace(run_id=RUN_ID)), 3)
        gate_status = read_json(run_root(RUN_ID) / "gate_status.json", {})
        blocker_kinds = {item["kind"] for item in gate_status["blocked"]}
        self.assertIn("missing_artifact", blocker_kinds)
        self.assertIn("missing_requirement", blocker_kinds)
        self.assertIn("user_confirmation", blocker_kinds)

        report_path = Path("experiment_docs/reports/phase_4_modules_report.md")
        report_path.parent.mkdir(parents=True)
        report_path.write_text("# Phase 4\n\nEvidence.\n", encoding="utf-8")
        define_args = argparse.Namespace(
            run_id=RUN_ID,
            id="method.module_a",
            phase="phase_4_modules",
            kind="paper",
            source="paper:method-module-a",
            text="Module A must match the paper method details.",
            implementation_target="src/module_a.py",
            test_target="tests/test_module_a.py",
        )
        self.assertEqual(autolab_gate.cmd_define_requirement(define_args), 0)
        evidence_args = argparse.Namespace(
            run_id=RUN_ID,
            id="method.module_a",
            type="report",
            path=str(report_path),
            command_text="",
            notes="Report records implementation and smoke-test evidence.",
        )
        self.assertEqual(autolab_gate.cmd_add_evidence(evidence_args), 0)
        self.assertEqual(autolab_gate.cmd_confirm_step(argparse.Namespace(run_id=RUN_ID, phase="", step="")), 0)

        self.assertEqual(autolab_gate.cmd_check_step(argparse.Namespace(run_id=RUN_ID)), 0)
        self.assertEqual(autolab_gate.cmd_complete_step(argparse.Namespace(run_id=RUN_ID)), 0)
        gate_status = read_json(run_root(RUN_ID) / "gate_status.json", {})
        self.assertIsNone(gate_status["current_step"])
        self.assertEqual(len(gate_status["completed_steps"]), 1)


if __name__ == "__main__":
    unittest.main()
