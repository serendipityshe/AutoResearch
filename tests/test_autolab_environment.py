import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "plugins" / "matrix-autolab" / "scripts"


def run_script(project_dir, script_name, *args):
    script = SCRIPTS_DIR / script_name
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=project_dir,
        text=True,
        capture_output=True,
        timeout=15,
    )


def start_run(project):
    result = run_script(
        project, "autolab_run.py",
        "start-run", "--kind", "paper_reproduction", "--entry-skill", "autolab",
    )
    if result.returncode != 0:
        raise RuntimeError(f"start-run failed: {result.stderr}")
    return json.loads(result.stdout)["run_id"]


def make_baseline(workdir, *, with_checkpoint=True, with_outputs=True, with_cache=True, with_clean_files=True):
    """Construct a fake baseline directory with optional stale artifacts."""
    workdir.mkdir(parents=True, exist_ok=True)
    if with_clean_files:
        (workdir / "train.py").write_text("# training entrypoint\n", encoding="utf-8")
        (workdir / "model.py").write_text("# model definition\n", encoding="utf-8")
    if with_checkpoint:
        (workdir / "checkpoints").mkdir(exist_ok=True)
        (workdir / "checkpoints" / "best.pth").write_bytes(b"\x00" * 2048)
        (workdir / "last_epoch.ckpt").write_bytes(b"\x00" * 1024)
    if with_outputs:
        (workdir / "outputs").mkdir(exist_ok=True)
        (workdir / "outputs" / "metrics.json").write_text("{}", encoding="utf-8")
        (workdir / "wandb").mkdir(exist_ok=True)
        (workdir / "wandb" / "run-old").mkdir(exist_ok=True)
        (workdir / "wandb" / "run-old" / "log.txt").write_text("...", encoding="utf-8")
    if with_cache:
        (workdir / "data" / "cache").mkdir(parents=True, exist_ok=True)
        (workdir / "data" / "cache" / "preprocessed.bin").write_bytes(b"\x01" * 4096)


class ScannerTests(unittest.TestCase):
    def test_scanner_detects_checkpoints_outputs_and_caches(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            baseline = project / "baseline"
            make_baseline(baseline)

            result = run_script(
                project, "autolab_run.py",
                "scan-environment", "--run-id", run_id, "--workdir", str(baseline),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertGreaterEqual(payload["items"], 4)

            snapshot = json.loads(
                (project / ".autolab" / "runs" / run_id / "environment_snapshot.json").read_text(encoding="utf-8")
            )
            kinds = {item["kind"] for item in snapshot["items"]}
            self.assertIn("checkpoint", kinds)
            self.assertIn("output", kinds)
            self.assertIn("cache", kinds)

            # Each .pth/.ckpt file gets sha256 since it's small
            for item in snapshot["items"]:
                if item["kind"] == "checkpoint":
                    self.assertEqual(len(item["sha256"]), 64)

    def test_scanner_writes_initial_decisions_with_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            baseline = project / "baseline"
            make_baseline(baseline, with_outputs=False, with_cache=False)

            result = run_script(
                project, "autolab_run.py",
                "scan-environment", "--run-id", run_id, "--workdir", str(baseline),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            decisions = json.loads(
                (project / ".autolab" / "runs" / run_id / "environment_decisions.json").read_text(encoding="utf-8")
            )
            self.assertGreater(len(decisions["decisions"]), 0)
            for entry in decisions["decisions"]:
                self.assertEqual(entry["decision"], "pending")

    def test_scanner_writes_markdown_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            baseline = project / "baseline"
            make_baseline(baseline, with_cache=False, with_outputs=False)

            result = run_script(
                project, "autolab_run.py",
                "scan-environment", "--run-id", run_id, "--workdir", str(baseline),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = (
                project / ".autolab" / "runs" / run_id / "reports" / "phase_2.5_environment_report.md"
            ).read_text(encoding="utf-8")
            self.assertIn("Phase 2.5", report)
            self.assertIn("checkpoint", report)
            self.assertIn("Required action", report)

    def test_scanner_clean_baseline_returns_no_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            baseline = project / "baseline"
            make_baseline(
                baseline,
                with_checkpoint=False, with_outputs=False, with_cache=False, with_clean_files=True,
            )

            result = run_script(
                project, "autolab_run.py",
                "scan-environment", "--run-id", run_id, "--workdir", str(baseline),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["items"], 0)

    def test_scanner_skips_dot_git_and_pycache(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            baseline = project / "baseline"
            baseline.mkdir()
            (baseline / ".git").mkdir()
            (baseline / ".git" / "ckpt.pth").write_bytes(b"\x00" * 1024)
            (baseline / "__pycache__").mkdir()
            (baseline / "__pycache__" / "x.cpython-310.pyc").write_bytes(b"\x00" * 1024)
            (baseline / "model.py").write_text("ok\n", encoding="utf-8")

            result = run_script(
                project, "autolab_run.py",
                "scan-environment", "--run-id", run_id, "--workdir", str(baseline),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["items"], 0)

    def test_scanner_diff_returns_exit_3_for_new_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            baseline = project / "baseline"
            baseline.mkdir()
            (baseline / "old.pth").write_bytes(b"\x00" * 512)

            first = run_script(
                project, "autolab_run.py",
                "scan-environment", "--run-id", run_id, "--workdir", str(baseline),
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            snapshot_path = project / ".autolab" / "runs" / run_id / "environment_snapshot.json"

            # New item appears later
            (baseline / "new.ckpt").write_bytes(b"\x01" * 512)
            second = run_script(
                project, "autolab_run.py",
                "scan-environment", "--run-id", run_id, "--workdir", str(baseline),
                "--against", str(snapshot_path.with_name("environment_snapshot_prior.json")),
            )
            # Wrong path -> not found
            self.assertEqual(second.returncode, 1)

            # Save the prior snapshot to a stable name and re-run
            prior_path = project / ".autolab" / "runs" / run_id / "prior_snapshot.json"
            prior_path.write_text(snapshot_path.read_text(encoding="utf-8"), encoding="utf-8")
            third = run_script(
                project, "autolab_run.py",
                "scan-environment", "--run-id", run_id, "--workdir", str(baseline),
                "--against", str(prior_path),
            )
            self.assertEqual(third.returncode, 3, third.stderr)
            payload = json.loads(third.stdout)
            self.assertEqual(payload["new_items"], 1)

    def test_scan_rejects_invalid_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            baseline = project / "baseline"
            baseline.mkdir()
            result = run_script(
                project, "autolab_run.py",
                "scan-environment", "--run-id", "../escape", "--workdir", str(baseline),
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Invalid run id", result.stderr)
            self.assertFalse((project.parent / "escape").exists())

    def test_scan_rejects_missing_workdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            result = run_script(
                project, "autolab_run.py",
                "scan-environment", "--run-id", run_id, "--workdir", str(project / "does_not_exist"),
            )
            self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
