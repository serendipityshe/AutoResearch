import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "plugins" / "matrix-autolab" / "scripts"


def run_script(project_dir, script_name, *args, env_extra=None):
    script = SCRIPTS_DIR / script_name
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=project_dir,
        text=True,
        capture_output=True,
        timeout=15,
    )


def start_run(project, kind="paper_reproduction", run_id=""):
    args = [
        "start-run",
        "--kind",
        kind,
        "--entry-skill",
        "autolab",
    ]
    if run_id:
        args.extend(["--run-id", run_id])
    result = run_script(project, "autolab_run.py", *args)
    if result.returncode != 0:
        raise RuntimeError(f"start-run failed: {result.stderr}")
    return json.loads(result.stdout)["run_id"]


def populate_contract(project, run_id, modules):
    contract_path = project / ".autolab" / "runs" / run_id / "contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["hyperparams"].update(
        {
            "seed": 42,
            "optimizer": "AdamW",
            "lr": 0.001,
            "batch_size": 16,
            "epochs": 50,
        }
    )
    contract["data"].update(
        {
            "dataset_path": "data/cityscapes",
            "preprocess_hash": contract["data"].get("preprocess_hash") or "x" * 64,
            "augment_hash": contract["data"].get("augment_hash") or "y" * 64,
        }
    )
    contract["environment"].update(
        {
            "git_commit": "abc1234",
            "python": "3.10.13",
            "torch": "2.1.0",
        }
    )
    contract["modules"] = dict(modules)
    contract_path.write_text(json.dumps(contract, indent=2), encoding="utf-8")


class ContractStartRunTests(unittest.TestCase):
    def test_start_run_writes_empty_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            contract_path = project / ".autolab" / "runs" / run_id / "contract.json"
            self.assertTrue(contract_path.exists(), "contract.json must be created on start-run")
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            self.assertEqual(contract["schema_version"], "0.2.0")
            self.assertEqual(contract["locked_at"], "")
            self.assertEqual(contract["modules"], {})
            self.assertIsNone(contract["parent_run_id"])

    def test_legacy_config_json_still_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            config_path = project / ".autolab" / "runs" / run_id / "config.json"
            self.assertTrue(config_path.exists(), "back-compat config.json must still be written")
            data = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "0.1.0")


class FreezePipelineTests(unittest.TestCase):
    def test_freeze_writes_hashes_into_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)

            pre_spec = '{"transforms":[{"name":"Resize","size":[256,256]},{"name":"ToTensor"}]}'
            aug_spec = '{"train":[{"name":"RandomFlip","p":0.5}]}'
            result = run_script(
                project,
                "autolab_run.py",
                "freeze-pipeline",
                "--run-id",
                run_id,
                "--pre",
                pre_spec,
                "--aug",
                aug_spec,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload["preprocess_hash"]), 64)
            self.assertEqual(len(payload["augment_hash"]), 64)
            self.assertNotEqual(payload["preprocess_hash"], payload["augment_hash"])

            contract = json.loads(
                (project / ".autolab" / "runs" / run_id / "contract.json").read_text(encoding="utf-8")
            )
            self.assertEqual(contract["data"]["preprocess_hash"], payload["preprocess_hash"])
            self.assertEqual(contract["data"]["augment_hash"], payload["augment_hash"])

            pipeline = json.loads(
                (project / ".autolab" / "runs" / run_id / "data_pipeline.json").read_text(encoding="utf-8")
            )
            self.assertEqual(pipeline["preprocess_hash"], payload["preprocess_hash"])
            self.assertEqual(pipeline["augment_hash"], payload["augment_hash"])

    def test_freeze_is_deterministic_across_key_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id_a = start_run(project)
            run_id_b = start_run(project)
            spec_a = '{"transforms":[{"name":"Resize","size":[256,256]}]}'
            spec_b = '{"transforms":[{"size":[256,256],"name":"Resize"}]}'
            other = '{"x":1}'

            result_a = run_script(
                project, "autolab_run.py", "freeze-pipeline",
                "--run-id", run_id_a, "--pre", spec_a, "--aug", other,
            )
            result_b = run_script(
                project, "autolab_run.py", "freeze-pipeline",
                "--run-id", run_id_b, "--pre", spec_b, "--aug", other,
            )
            self.assertEqual(result_a.returncode, 0, result_a.stderr)
            self.assertEqual(result_b.returncode, 0, result_b.stderr)
            self.assertEqual(
                json.loads(result_a.stdout)["preprocess_hash"],
                json.loads(result_b.stdout)["preprocess_hash"],
            )

    def test_freeze_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            result = run_script(
                project, "autolab_run.py", "freeze-pipeline",
                "--run-id", run_id, "--pre", "not-json", "--aug", "{}",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid JSON", result.stderr)

    def test_freeze_accepts_at_file_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            pre_path = project / "pre.json"
            aug_path = project / "aug.json"
            pre_path.write_text('{"transforms":[{"name":"Resize","size":[224,224]}]}', encoding="utf-8")
            aug_path.write_text('{"train":[]}', encoding="utf-8")
            result = run_script(
                project, "autolab_run.py", "freeze-pipeline",
                "--run-id", run_id, "--pre", f"@{pre_path}", "--aug", f"@{aug_path}",
            )
            self.assertEqual(result.returncode, 0, result.stderr)


class LockContractTests(unittest.TestCase):
    def test_lock_refuses_when_required_fields_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            result = run_script(
                project, "autolab_run.py", "lock-contract", "--run-id", run_id,
            )
            self.assertEqual(result.returncode, 5)
            self.assertIn("hyperparams.seed", result.stderr)

    def test_lock_succeeds_with_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            populate_contract(project, run_id, modules={"alpha": True, "beta": True})
            result = run_script(
                project, "autolab_run.py", "lock-contract", "--run-id", run_id,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["locked"])
            contract = json.loads(
                (project / ".autolab" / "runs" / run_id / "contract.json").read_text(encoding="utf-8")
            )
            self.assertTrue(contract["locked_at"])

    def test_freeze_after_lock_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            populate_contract(project, run_id, modules={"alpha": True})
            lock = run_script(project, "autolab_run.py", "lock-contract", "--run-id", run_id)
            self.assertEqual(lock.returncode, 0, lock.stderr)
            freeze = run_script(
                project, "autolab_run.py", "freeze-pipeline",
                "--run-id", run_id, "--pre", "{}", "--aug", "{}",
            )
            self.assertEqual(freeze.returncode, 4)
            self.assertIn("locked", freeze.stderr.lower())


class ValidateContractTests(unittest.TestCase):
    def test_validate_passes_when_pipeline_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            pre = '{"transforms":[{"name":"Resize","size":[256,256]}]}'
            aug = '{"train":[]}'
            run_script(
                project, "autolab_run.py", "freeze-pipeline",
                "--run-id", run_id, "--pre", pre, "--aug", aug,
            )
            populate_contract(project, run_id, modules={"alpha": True})
            run_script(project, "autolab_run.py", "lock-contract", "--run-id", run_id)
            result = run_script(
                project, "autolab_run.py", "validate-contract",
                "--run-id", run_id, "--pre", pre, "--aug", aug, "--strict",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["ok"])

    def test_validate_detects_pipeline_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            pre = '{"transforms":[{"name":"Resize","size":[256,256]}]}'
            aug = '{"train":[]}'
            run_script(
                project, "autolab_run.py", "freeze-pipeline",
                "--run-id", run_id, "--pre", pre, "--aug", aug,
            )
            populate_contract(project, run_id, modules={"alpha": True})
            run_script(project, "autolab_run.py", "lock-contract", "--run-id", run_id)
            tampered_pre = '{"transforms":[{"name":"Resize","size":[512,512]}]}'
            result = run_script(
                project, "autolab_run.py", "validate-contract",
                "--run-id", run_id, "--pre", tampered_pre, "--aug", aug,
            )
            self.assertEqual(result.returncode, 3, result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(len(payload["mismatches"]), 1)
            self.assertEqual(payload["mismatches"][0]["field"], "preprocess_hash")

    def test_strict_validate_fails_when_not_locked(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            run_id = start_run(project)
            result = run_script(
                project, "autolab_run.py", "validate-contract",
                "--run-id", run_id, "--strict",
            )
            self.assertEqual(result.returncode, 5)
            self.assertEqual(json.loads(result.stdout)["reason"], "contract_not_locked")


class DeriveAblationTests(unittest.TestCase):
    def setup_locked_parent(self, project, modules):
        run_id = start_run(project)
        run_script(
            project, "autolab_run.py", "freeze-pipeline",
            "--run-id", run_id, "--pre", '{"x":1}', "--aug", '{"y":2}',
        )
        populate_contract(project, run_id, modules=modules)
        run_script(project, "autolab_run.py", "lock-contract", "--run-id", run_id)
        return run_id

    def test_derive_creates_child_with_correct_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            parent = self.setup_locked_parent(project, {"alpha": True, "beta": True, "gamma": True})
            result = run_script(
                project, "autolab_run.py", "derive-ablation",
                "--parent", parent, "--toggle", "alpha=false",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            child_id = payload["run_id"]
            self.assertEqual(payload["parent_run_id"], parent)
            self.assertEqual(len(payload["ablation_diff"]), 1)
            self.assertEqual(payload["ablation_diff"][0]["field"], "modules.alpha")
            self.assertFalse(payload["ablation_diff"][0]["after"])

            child_contract = json.loads(
                (project / ".autolab" / "runs" / child_id / "contract.json").read_text(encoding="utf-8")
            )
            self.assertEqual(child_contract["modules"]["alpha"], False)
            self.assertEqual(child_contract["modules"]["beta"], True)
            self.assertEqual(child_contract["modules"]["gamma"], True)
            self.assertEqual(child_contract["parent_run_id"], parent)
            self.assertEqual(child_contract["locked_at"], "")

    def test_derive_rejects_unlocked_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            parent = start_run(project)
            populate_contract(project, parent, modules={"alpha": True})
            # NOT locked
            result = run_script(
                project, "autolab_run.py", "derive-ablation",
                "--parent", parent, "--toggle", "alpha=false",
            )
            self.assertEqual(result.returncode, 5)
            self.assertIn("locked", result.stderr.lower())

    def test_derive_rejects_unknown_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            parent = self.setup_locked_parent(project, {"alpha": True})
            result = run_script(
                project, "autolab_run.py", "derive-ablation",
                "--parent", parent, "--toggle", "ghost=false",
            )
            self.assertEqual(result.returncode, 6)
            self.assertIn("unknown modules", result.stderr.lower())

    def test_derive_rejects_no_op_toggle(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            parent = self.setup_locked_parent(project, {"alpha": True})
            result = run_script(
                project, "autolab_run.py", "derive-ablation",
                "--parent", parent, "--toggle", "alpha=true",
            )
            self.assertEqual(result.returncode, 6)
            self.assertIn("no effective toggle change", result.stderr.lower())

    def test_derive_rejects_invalid_toggle_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            parent = self.setup_locked_parent(project, {"alpha": True})
            result = run_script(
                project, "autolab_run.py", "derive-ablation",
                "--parent", parent, "--toggle", "alpha",
            )
            self.assertEqual(result.returncode, 2)


class CompareRunsTests(unittest.TestCase):
    def test_compare_shows_module_diffs(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            parent = start_run(project)
            run_script(
                project, "autolab_run.py", "freeze-pipeline",
                "--run-id", parent, "--pre", '{"x":1}', "--aug", '{"y":2}',
            )
            populate_contract(project, parent, modules={"alpha": True, "beta": True})
            run_script(project, "autolab_run.py", "lock-contract", "--run-id", parent)
            child_result = run_script(
                project, "autolab_run.py", "derive-ablation",
                "--parent", parent, "--toggle", "alpha=false",
            )
            child_id = json.loads(child_result.stdout)["run_id"]

            result = run_script(
                project, "autolab_run.py", "compare-runs",
                "--run-a", parent, "--run-b", child_id,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            diffs = json.loads(result.stdout)["diffs"]
            module_diffs = [d for d in diffs if d["field"].startswith("modules.")]
            self.assertEqual(len(module_diffs), 1)
            self.assertEqual(module_diffs[0]["field"], "modules.alpha")
            self.assertTrue(module_diffs[0]["before"])
            self.assertFalse(module_diffs[0]["after"])
            # parent_run_id should also differ
            lineage_diffs = [d for d in diffs if d["field"] == "parent_run_id"]
            self.assertEqual(len(lineage_diffs), 1)


if __name__ == "__main__":
    unittest.main()
