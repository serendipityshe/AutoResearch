import json
import math
import pathlib
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "plugins" / "matrix-autolab" / "scripts"


def run_script(project_dir, script_name, *args):
    script = SCRIPTS_DIR / script_name
    result = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=project_dir,
        text=True,
        capture_output=True,
        timeout=10,
    )
    return result


class AutolabRecordingTests(unittest.TestCase):
    def start_run(self, project):
        start = run_script(
            project,
            "autolab_run.py",
            "start-run",
            "--kind",
            "ablation",
            "--entry-skill",
            "autolab",
        )
        self.assertEqual(start.returncode, 0, start.stderr)
        return json.loads(start.stdout)["run_id"]

    def test_init_project_creates_project_and_status_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            result = run_script(project, "autolab_run.py", "init-project", "--name", "Demo")
            self.assertEqual(result.returncode, 0, result.stderr)

            project_json = json.loads((project / ".autolab" / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(project_json["schema_version"], "0.1.0")
            self.assertEqual(project_json["name"], "Demo")
            self.assertEqual(project_json["paper_source"], "main.tex")

            status_json = json.loads((project / ".autolab" / "workflow_status.json").read_text(encoding="utf-8"))
            self.assertEqual(status_json["schema_version"], "0.1.0")
            self.assertIn("matrix-autolab", status_json["skills"])
            self.assertIn("paperbanana", status_json["skills"])
            self.assertIn("autolab", status_json["skills"])
            self.assertIn("autobaseline", status_json["skills"])

    def test_start_and_finish_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            start = run_script(
                project,
                "autolab_run.py",
                "start-run",
                "--kind",
                "ablation",
                "--entry-skill",
                "autolab",
            )
            self.assertEqual(start.returncode, 0, start.stderr)
            payload = json.loads(start.stdout)
            run_id = payload["run_id"]

            run_dir = project / ".autolab" / "runs" / run_id
            run_json = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(run_json["kind"], "ablation")
            self.assertEqual(run_json["status"], "in_progress")
            self.assertEqual(run_json["entry_skill"], "autolab")

            status_json = json.loads((project / ".autolab" / "workflow_status.json").read_text(encoding="utf-8"))
            self.assertEqual(status_json["active_run_id"], run_id)

            finish = run_script(
                project,
                "autolab_run.py",
                "finish-run",
                "--run-id",
                run_id,
                "--status",
                "completed",
                "--summary",
                "Smoke run complete",
            )
            self.assertEqual(finish.returncode, 0, finish.stderr)
            updated = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(updated["status"], "completed")
            self.assertEqual(updated["summary"], "Smoke run complete")
            self.assertTrue(updated["ended_at"])

    def test_invalid_run_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            start = run_script(
                project,
                "autolab_run.py",
                "start-run",
                "--kind",
                "ablation",
                "--entry-skill",
                "autolab",
                "--run-id",
                "../outside",
            )
            self.assertNotEqual(start.returncode, 0)
            self.assertIn("Invalid run id", start.stderr)
            self.assertFalse((project.parent / "outside").exists())

            finish = run_script(
                project,
                "autolab_run.py",
                "finish-run",
                "--run-id",
                "../outside",
                "--status",
                "completed",
            )
            self.assertNotEqual(finish.returncode, 0)
            self.assertIn("Invalid run id", finish.stderr)

    def test_duplicate_start_run_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = "20260425T120000Z-abcdef"
            first = run_script(
                project,
                "autolab_run.py",
                "start-run",
                "--kind",
                "ablation",
                "--entry-skill",
                "autolab",
                "--run-id",
                run_id,
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            duplicate = run_script(
                project,
                "autolab_run.py",
                "start-run",
                "--kind",
                "inspection",
                "--entry-skill",
                "autolab",
                "--run-id",
                run_id,
            )
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertIn("Run already exists", duplicate.stderr)

            run_dir = project / ".autolab" / "runs" / run_id
            run_json = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(run_json["kind"], "ablation")
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(events), 1)

    def test_repeated_finish_run_same_status_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = "20260425T120001Z-abcdef"
            start = run_script(
                project,
                "autolab_run.py",
                "start-run",
                "--kind",
                "ablation",
                "--entry-skill",
                "autolab",
                "--run-id",
                run_id,
            )
            self.assertEqual(start.returncode, 0, start.stderr)

            first_finish = run_script(
                project,
                "autolab_run.py",
                "finish-run",
                "--run-id",
                run_id,
                "--status",
                "completed",
                "--summary",
                "first summary",
            )
            self.assertEqual(first_finish.returncode, 0, first_finish.stderr)

            run_dir = project / ".autolab" / "runs" / run_id
            first_run_json = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            first_events = (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()

            second_finish = run_script(
                project,
                "autolab_run.py",
                "finish-run",
                "--run-id",
                run_id,
                "--status",
                "completed",
                "--summary",
                "second summary",
            )
            self.assertEqual(second_finish.returncode, 0, second_finish.stderr)
            payload = json.loads(second_finish.stdout)
            self.assertTrue(payload["unchanged"])

            second_run_json = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            second_events = (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(second_run_json["ended_at"], first_run_json["ended_at"])
            self.assertEqual(second_run_json["summary"], "first summary")
            self.assertEqual(second_events, first_events)

    def test_generated_run_files_are_parseable_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            start = run_script(
                project,
                "autolab_run.py",
                "start-run",
                "--kind",
                "ablation",
                "--entry-skill",
                "autolab",
            )
            self.assertEqual(start.returncode, 0, start.stderr)
            run_id = json.loads(start.stdout)["run_id"]

            finish = run_script(
                project,
                "autolab_run.py",
                "finish-run",
                "--run-id",
                run_id,
                "--status",
                "completed",
                "--summary",
                "parseable",
            )
            self.assertEqual(finish.returncode, 0, finish.stderr)

            run_dir = project / ".autolab" / "runs" / run_id
            json_paths = [
                project / ".autolab" / "project.json",
                project / ".autolab" / "workflow_status.json",
                run_dir / "run.json",
                run_dir / "config.json",
                run_dir / "artifacts.json",
                run_dir / "changed_files.json",
                run_dir / "reports" / "reports_index.json",
            ]
            for path in json_paths:
                with self.subTest(path=path):
                    json.loads(path.read_text(encoding="utf-8"))

            events = (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(events), 2)
            for line in events:
                with self.subTest(line=line):
                    json.loads(line)

    def test_event_metric_and_error_append_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = self.start_run(project)

            event = run_script(
                project,
                "autolab_event.py",
                "event",
                "--run-id",
                run_id,
                "--type",
                "phase_started",
                "--skill",
                "autolab",
                "--phase",
                "phase_4_modules",
                "--message",
                "Phase 4 started",
                "--level",
                "info",
                "--data",
                '{"phase_index": 4}',
            )
            self.assertEqual(event.returncode, 0, event.stderr)

            metric = run_script(
                project,
                "autolab_event.py",
                "metric",
                "--run-id",
                run_id,
                "--name",
                "mIoU",
                "--value",
                "0.734",
                "--source",
                "eval.py",
                "--phase",
                "phase_4_modules",
                "--step",
                "12",
                "--epoch",
                "3",
                "--split",
                "val",
                "--unit",
                "ratio",
                "--context",
                '{"dataset": "demo"}',
            )
            self.assertEqual(metric.returncode, 0, metric.stderr)

            error = run_script(
                project,
                "autolab_event.py",
                "error",
                "--run-id",
                run_id,
                "--category",
                "oom",
                "--message",
                "CUDA out of memory",
                "--skill",
                "autolab",
                "--phase",
                "phase_4_modules",
                "--severity",
                "error",
                "--command-text",
                "python train.py",
                "--log-excerpt",
                "CUDA out of memory",
                "--suggested-next-step",
                "Reduce batch size",
            )
            self.assertEqual(error.returncode, 0, error.stderr)

            run_dir = project / ".autolab" / "runs" / run_id
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            metrics = [
                json.loads(line)
                for line in (run_dir / "metrics.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            errors = [
                json.loads(line)
                for line in (run_dir / "errors.jsonl").read_text(encoding="utf-8").splitlines()
            ]

            self.assertEqual(events[-3]["event_type"], "phase_started")
            self.assertEqual(events[-3]["skill"], "autolab")
            self.assertEqual(events[-3]["phase"], "phase_4_modules")
            self.assertEqual(events[-3]["message"], "Phase 4 started")
            self.assertEqual(events[-3]["level"], "info")
            self.assertEqual(events[-3]["data"], {"phase_index": 4})
            self.assertEqual(events[-2]["event_type"], "metric_recorded")
            self.assertEqual(events[-2]["data"], {"name": "mIoU", "value": 0.734})
            self.assertEqual(events[-1]["event_type"], "phase_failed")
            self.assertEqual(events[-1]["data"], {"category": "oom"})

            self.assertEqual(metrics[0]["name"], "mIoU")
            self.assertEqual(metrics[0]["value"], 0.734)
            self.assertEqual(metrics[0]["source"], "eval.py")
            self.assertEqual(metrics[0]["phase"], "phase_4_modules")
            self.assertEqual(metrics[0]["step"], 12)
            self.assertEqual(metrics[0]["epoch"], 3)
            self.assertEqual(metrics[0]["split"], "val")
            self.assertEqual(metrics[0]["unit"], "ratio")
            self.assertEqual(metrics[0]["context"], {"dataset": "demo"})

            self.assertEqual(errors[0]["category"], "oom")
            self.assertEqual(errors[0]["message"], "CUDA out of memory")
            self.assertEqual(errors[0]["skill"], "autolab")
            self.assertEqual(errors[0]["phase"], "phase_4_modules")
            self.assertEqual(errors[0]["severity"], "error")
            self.assertEqual(errors[0]["command"], "python train.py")
            self.assertEqual(errors[0]["log_excerpt"], "CUDA out of memory")
            self.assertEqual(errors[0]["suggested_next_step"], "Reduce batch size")

    def test_metric_rejects_non_finite_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = self.start_run(project)
            run_dir = project / ".autolab" / "runs" / run_id

            for value in ("nan", "inf", "-inf"):
                with self.subTest(value=value):
                    result = run_script(
                        project,
                        "autolab_event.py",
                        "metric",
                        "--run-id",
                        run_id,
                        "--name",
                        "loss",
                        f"--value={value}",
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("Metric value must be finite", result.stderr)

            self.assertFalse((run_dir / "metrics.jsonl").exists())

    def test_event_rejects_malformed_json_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = self.start_run(project)

            result = run_script(
                project,
                "autolab_event.py",
                "event",
                "--run-id",
                run_id,
                "--type",
                "phase_started",
                "--message",
                "Phase started",
                "--data",
                "{bad-json",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Invalid JSON for --data", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_event_rejects_json_array_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = self.start_run(project)

            result = run_script(
                project,
                "autolab_event.py",
                "event",
                "--run-id",
                run_id,
                "--type",
                "phase_started",
                "--message",
                "Phase started",
                "--data",
                '["not", "object"]',
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("expected an object", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_event_rejects_invalid_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)

            result = run_script(
                project,
                "autolab_event.py",
                "event",
                "--run-id",
                "../outside",
                "--type",
                "phase_started",
                "--message",
                "Phase started",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Invalid run id", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_event_jsonl_remains_parseable_after_normal_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = self.start_run(project)

            metric = run_script(
                project,
                "autolab_event.py",
                "metric",
                "--run-id",
                run_id,
                "--name",
                "accuracy",
                "--value",
                "1.0",
            )
            self.assertEqual(metric.returncode, 0, metric.stderr)

            event = run_script(
                project,
                "autolab_event.py",
                "event",
                "--run-id",
                run_id,
                "--type",
                "phase_completed",
                "--message",
                "Phase completed",
                "--level",
                "warning",
            )
            self.assertEqual(event.returncode, 0, event.stderr)

            run_dir = project / ".autolab" / "runs" / run_id
            for path in (run_dir / "events.jsonl", run_dir / "metrics.jsonl"):
                with self.subTest(path=path):
                    lines = path.read_text(encoding="utf-8").splitlines()
                    self.assertTrue(lines)
                    for line in lines:
                        json.loads(line)

            metric_record = json.loads((run_dir / "metrics.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertIsNone(metric_record["step"])
            self.assertIsNone(metric_record["epoch"])

    def test_collect_artifact_report_and_changed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "config", "user.email", "autolab@example.test"],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "AutoLab Test"],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )
            tracked = project / "model.py"
            tracked.write_text("print('v1')\n", encoding="utf-8")
            subprocess.run(["git", "add", "model.py"], cwd=project, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "commit", "-m", "init"],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )
            tracked.write_text("print('v2')\n", encoding="utf-8")

            run_id = self.start_run(project)

            artifact_file = project / "outputs" / "best.pth"
            artifact_file.parent.mkdir()
            artifact_file.write_bytes(b"checkpoint")
            artifact = run_script(
                project,
                "autolab_collect.py",
                "artifact",
                "--run-id",
                run_id,
                "--type",
                "checkpoint",
                "--path",
                "outputs/best.pth",
                "--id",
                "best_checkpoint",
                "--phase",
                "phase_4_modules",
                "--description",
                "Best checkpoint",
            )
            self.assertEqual(artifact.returncode, 0, artifact.stderr)

            duplicate = run_script(
                project,
                "autolab_collect.py",
                "artifact",
                "--run-id",
                run_id,
                "--type",
                "checkpoint",
                "--path",
                "outputs/best.pth",
                "--id",
                "best_checkpoint",
                "--description",
                "Updated checkpoint description",
            )
            self.assertEqual(duplicate.returncode, 0, duplicate.stderr)

            report_file = project / "experiment_docs" / "reports" / "phase.md"
            report_file.parent.mkdir(parents=True)
            report_file.write_text("# Phase\n", encoding="utf-8")
            report = run_script(
                project,
                "autolab_collect.py",
                "report",
                "--run-id",
                run_id,
                "--type",
                "phase_report",
                "--phase",
                "phase_3_baseline_audit",
                "--path",
                "experiment_docs/reports/phase.md",
                "--title",
                "Baseline Audit",
            )
            self.assertEqual(report.returncode, 0, report.stderr)

            changed = run_script(project, "autolab_collect.py", "changed-files", "--run-id", run_id)
            self.assertEqual(changed.returncode, 0, changed.stderr)

            run_dir = project / ".autolab" / "runs" / run_id
            artifacts = json.loads((run_dir / "artifacts.json").read_text(encoding="utf-8"))["artifacts"]
            reports = json.loads((run_dir / "reports" / "reports_index.json").read_text(encoding="utf-8"))[
                "reports"
            ]
            changed_payload = json.loads((run_dir / "changed_files.json").read_text(encoding="utf-8"))
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]

            self.assertEqual(len(artifacts), 1)
            self.assertEqual(artifacts[0]["id"], "best_checkpoint")
            self.assertEqual(artifacts[0]["type"], "checkpoint")
            self.assertEqual(artifacts[0]["path"], "outputs/best.pth")
            self.assertTrue(artifacts[0]["exists"])
            self.assertEqual(artifacts[0]["size_bytes"], len(b"checkpoint"))
            self.assertEqual(
                artifacts[0]["sha256"],
                "47320987f9a49d5b00119b960f247a956773f57543982b8bfcb6da5bb3afd9ef",
            )
            self.assertEqual(artifacts[0]["description"], "Updated checkpoint description")

            self.assertEqual(len(reports), 1)
            self.assertEqual(reports[0]["title"], "Baseline Audit")
            self.assertEqual(reports[0]["type"], "phase_report")
            self.assertEqual(reports[0]["phase"], "phase_3_baseline_audit")
            self.assertEqual(reports[0]["path"], "experiment_docs/reports/phase.md")

            self.assertTrue(changed_payload["captured_at"])
            self.assertTrue(changed_payload["git"]["commit"])
            self.assertTrue(changed_payload["git"]["dirty"])
            self.assertTrue(any(item["path"] == "model.py" and item["status"] == "M" for item in changed_payload["files"]))
            self.assertTrue(any(event["event_type"] == "artifact_recorded" for event in events))
            self.assertTrue(any(event["event_type"] == "report_recorded" for event in events))

    def test_collect_rejects_artifact_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = self.start_run(project)

            result = run_script(
                project,
                "autolab_collect.py",
                "artifact",
                "--run-id",
                run_id,
                "--type",
                "checkpoint",
                "--path",
                "../outside.pth",
                "--id",
                "outside",
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("Invalid artifact path", result.stderr)
            run_dir = project / ".autolab" / "runs" / run_id
            artifacts = json.loads((run_dir / "artifacts.json").read_text(encoding="utf-8"))["artifacts"]
            self.assertEqual(artifacts, [])

    def test_collect_rejects_absolute_artifact_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = self.start_run(project)
            outside = pathlib.Path(tmp).parent / "outside.pth"

            result = run_script(
                project,
                "autolab_collect.py",
                "artifact",
                "--run-id",
                run_id,
                "--type",
                "checkpoint",
                "--path",
                str(outside),
                "--id",
                "outside",
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("Invalid artifact path", result.stderr)

    def test_collect_rejects_report_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = self.start_run(project)

            result = run_script(
                project,
                "autolab_collect.py",
                "report",
                "--run-id",
                run_id,
                "--type",
                "phase_report",
                "--phase",
                "phase_1",
                "--path",
                "../outside.md",
                "--title",
                "Outside",
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("Invalid report path", result.stderr)
            run_dir = project / ".autolab" / "runs" / run_id
            reports = json.loads((run_dir / "reports" / "reports_index.json").read_text(encoding="utf-8"))[
                "reports"
            ]
            self.assertEqual(reports, [])

    def test_collect_report_duplicate_upserts_one_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = self.start_run(project)
            report_path = project / "reports" / "phase.md"
            report_path.parent.mkdir()
            report_path.write_text("# Phase\n", encoding="utf-8")

            first = run_script(
                project,
                "autolab_collect.py",
                "report",
                "--run-id",
                run_id,
                "--type",
                "phase_report",
                "--phase",
                "phase_1",
                "--path",
                "reports/phase.md",
                "--title",
                "First Title",
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            second = run_script(
                project,
                "autolab_collect.py",
                "report",
                "--run-id",
                run_id,
                "--type",
                "phase_report",
                "--phase",
                "phase_1",
                "--path",
                "reports/phase.md",
                "--title",
                "Second Title",
            )
            self.assertEqual(second.returncode, 0, second.stderr)

            run_dir = project / ".autolab" / "runs" / run_id
            reports = json.loads((run_dir / "reports" / "reports_index.json").read_text(encoding="utf-8"))[
                "reports"
            ]
            self.assertEqual(len(reports), 1)
            self.assertEqual(reports[0]["title"], "Second Title")
            self.assertTrue(reports[0]["created_at"])
            self.assertTrue(reports[0]["updated_at"])

    def test_collect_changed_files_captures_git_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "config", "user.email", "autolab@example.test"],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "AutoLab Test"],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )
            original = project / "old_name.py"
            original.write_text("print('v1')\n", encoding="utf-8")
            subprocess.run(["git", "add", "old_name.py"], cwd=project, check=True, capture_output=True, text=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=project, check=True, capture_output=True, text=True)
            subprocess.run(["git", "mv", "old_name.py", "new_name.py"], cwd=project, check=True, capture_output=True, text=True)

            run_id = self.start_run(project)
            changed = run_script(project, "autolab_collect.py", "changed-files", "--run-id", run_id)
            self.assertEqual(changed.returncode, 0, changed.stderr)

            run_dir = project / ".autolab" / "runs" / run_id
            files = json.loads((run_dir / "changed_files.json").read_text(encoding="utf-8"))["files"]
            self.assertTrue(
                any(
                    item["status"] == "R" and item["old_path"] == "old_name.py" and item["path"] == "new_name.py"
                    for item in files
                )
            )

    def test_write_json_rejects_non_finite_values(self):
        import importlib.util

        module_path = SCRIPTS_DIR / "autolab_common.py"
        spec = importlib.util.spec_from_file_location("autolab_common_for_test", module_path)
        autolab_common = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(autolab_common)

        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "strict.json"
            with self.assertRaises(ValueError):
                autolab_common.write_json(path, {"value": math.nan})
            self.assertFalse(path.exists())

    def test_collect_artifact_duplicate_preserves_phase_when_omitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = self.start_run(project)
            artifact_file = project / "outputs" / "best.pth"
            artifact_file.parent.mkdir()
            artifact_file.write_bytes(b"checkpoint")

            first = run_script(
                project,
                "autolab_collect.py",
                "artifact",
                "--run-id",
                run_id,
                "--type",
                "checkpoint",
                "--path",
                "outputs/best.pth",
                "--id",
                "best_checkpoint",
                "--phase",
                "phase_4_modules",
                "--description",
                "Best checkpoint",
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            second = run_script(
                project,
                "autolab_collect.py",
                "artifact",
                "--run-id",
                run_id,
                "--type",
                "checkpoint",
                "--path",
                "outputs/best.pth",
                "--id",
                "best_checkpoint",
            )
            self.assertEqual(second.returncode, 0, second.stderr)

            run_dir = project / ".autolab" / "runs" / run_id
            artifacts = json.loads((run_dir / "artifacts.json").read_text(encoding="utf-8"))["artifacts"]
            self.assertEqual(len(artifacts), 1)
            self.assertEqual(artifacts[0]["phase"], "phase_4_modules")
            self.assertEqual(artifacts[0]["description"], "Best checkpoint")


if __name__ == "__main__":
    unittest.main()
