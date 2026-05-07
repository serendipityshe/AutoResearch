# AutoLab Skill Rigor Enhancement

Date: 2026-05-06
Status: Implemented

## Goal

Tighten the autolab skill so model drift, environment contamination, and silent pipeline mutations cannot break ablation rigor. After this enhancement the skill enforces every "must be identical across runs" claim through machine-checkable artifacts, not prose alone.

## Background

Real-world testing of the v0.2.0 skill exposed three failure modes:

1. **Model drift**: even with `MUST` / `BLOCKING` language in SKILL.md, models occasionally skip phases, claim work was done without producing artifacts, or vary hyperparameters between ablation runs.
2. **Environment contamination**: working directories regularly contain stale checkpoints, `outputs/`, `wandb/`, and cached datasets from prior workflows. The recording layer is append-only and declaration-based; it had no detection for these.
3. **Pipeline drift across phases**: data preprocessing and augmentation are audited in Phase 3 and statistics are collected in Phase 5, but no phase explicitly froze the pipeline. Short training, full training, and ablation runs could silently use different transforms.

## Non-Goals

- No automatic deletion or modification of detected stale artifacts. Decisions remain user-driven and recorded.
- No remote sync, no dashboard surface for the new contract data (those belong to dashboard scope).
- No mandatory inspection of contract / pipeline contents inside training code; the contract is a control-plane artifact, not runtime config.
- No retroactive migration of pre-0.3.0 runs (their `config.json` stays as-is; new runs additionally produce `contract.json`).

## Two-Tier Gates

Every phase gains a Machine Gate alongside the existing User Gate:

- **User Gate**: user types `confirm` in chat after reviewing the report.
- **Machine Gate**: a JSON artifact under `.autolab/runs/<run_id>/` whose presence and validity is checked by a CLI subcommand. The next phase MUST run that check and refuse to proceed on non-zero exit.

The combination defeats both impatient humans and impatient models: the user can't accidentally accept a phase that didn't actually run, and the model can't fake completion because the validating CLI runs against real files.

## New Phases

### Phase 2.5 — Environment Sanity Scan

Inserted between Phase 2 (Setup) and Phase 3 (Baseline Audit).

The skill scans the baseline working directory for:

- checkpoint files: `*.pth`, `*.ckpt`, `*.bin`, `*.safetensors`, `*.pt`
- output directories: `outputs/`, `runs/`, `wandb/`, `lightning_logs/`, `tensorboard/`, `tb_logs/`, `mlruns/`
- cache directories: `*/cache`, `data/cache`, `processed/`
- large untracked binaries (>1 MiB) that aren't in git

Outputs (under `.autolab/runs/<id>/`):

- `environment_snapshot.json` — full list with path, kind, size, mtime, sha256 (≤100 MiB), `git_tracked`
- `environment_decisions.json` — initialised with `decision: "pending"` per item; user must replace with `keep` / `move-aside` / `delete`
- `reports/phase_2.5_environment_report.md` — Markdown table for human review

The gate blocks Phase 3 until every decision is non-pending. Subsequent phases MAY re-run the scan with `--against <prior_snapshot>`; exit code 3 means new untracked artifacts appeared and the workflow halts.

### Phase 4.7 — Data Pipeline Freeze

Inserted between Phase 4.5 (Loss Check) and Phase 5 (Integration).

The skill serialises preprocessing and augmentation pipelines into JSON specs and computes two independent SHA-256 hashes via canonicalised JSON (sorted keys, no extra whitespace):

- `preprocess_hash` — covers deterministic transforms (Resize, Normalize, ToTensor, …)
- `augment_hash` — covers stochastic transforms (RandomFlip, ColorJitter, …) for both train and val splits

Splitting the hash lets ablation studies that specifically target augmentation toggle `augment_hash` while keeping `preprocess_hash` invariant.

Outputs:

- `data_pipeline.json` — canonicalised preprocess + augment JSON plus both hashes
- `contract.json` updated: `data.preprocess_hash`, `data.augment_hash`
- `reports/phase_4.7_pipeline_report.md` — code snippets, hashes, deviations from paper

After this phase, every training launch (Phase 6, 7, 8) MUST run `validate-contract --pre … --aug …` and confirm exit code 0 before launching.

## Experiment Contract

`.autolab/runs/<run_id>/contract.json` is the new authoritative experiment description (schema version 0.2.0). The legacy `config.json` stub is still written for backwards compatibility with the recording-system tests, but no new logic depends on it.

```json
{
  "schema_version": "0.2.0",
  "captured_at": "...",
  "locked_at": "",
  "hyperparams": {
    "seed": null, "optimizer": "", "lr": null, "scheduler": "",
    "batch_size": null, "epochs": null, "loss_components": {}
  },
  "data": {
    "dataset_path": "", "splits": {},
    "preprocess_hash": "", "augment_hash": "",
    "input_resolution": [], "class_distribution": {}
  },
  "modules": {},
  "environment": {
    "git_commit": "", "python": "", "torch": "", "cuda": "",
    "pretrained_weights": [], "environment_decisions_ref": ""
  },
  "parent_run_id": null,
  "ablation_diff": null
}
```

Required fields for `lock-contract`: every `hyperparams` field except `scheduler` and `loss_components`; `data.dataset_path` / `preprocess_hash` / `augment_hash`; `environment.git_commit` / `python` / `torch`; non-empty `modules`.

Once locked, `freeze-pipeline` returns exit 4 (cannot modify locked contract). Edits to `hyperparams.*`, `modules.*`, `data.*`, or `environment.*` should be considered append-only at this point — if they're genuinely wrong, abort the run and start fresh.

## Ablation Derivation

Phase 8 ablations now require the new `derive-ablation` subcommand. Manually running `start-run --kind ablation` is permitted but produces a child run without `parent_run_id` / `ablation_diff`, and the SKILL.md instructs AI to refuse such runs in the comparison table.

`derive-ablation` enforces:

- parent contract MUST be locked
- toggles MUST reference modules that exist in the parent
- at least one toggle MUST produce a real change
- by default, only `modules.*` may differ from parent. `--allow-pipeline-change` is reserved for studying augmentation effects and writes a non-empty diff event for visibility.

The child contract starts unlocked so the child run can lock once it has its own `git_commit` and (optionally) different `loss_components` overrides. The `parent_run_id` and `ablation_diff` fields are immutable once written.

## CLI Surface

All commands live in `plugins/matrix-autolab/scripts/autolab_run.py`:

| Subcommand | Phase | Purpose |
|---|---|---|
| `scan-environment` | 2.5 | Detect stale artifacts; optional `--against` for re-scan with drift detection |
| `freeze-pipeline` | 4.7 | Hash and persist preprocess + augment specs into contract |
| `lock-contract` | 7 | Stamp `locked_at`; refuses on missing required fields |
| `validate-contract` | 6 / 7 / 8 (pre-launch) | Recompute hashes and compare to locked contract |
| `derive-ablation` | 8 | Create child run from locked parent + module toggles |
| `compare-runs` | 8 (review) | Field-level diff between two contracts |

Heavy logic lives in two new helper modules:

- `autolab_contract.py` — empty-contract factory, canonical JSON / hash, lock / validate / derive helpers
- `autolab_environment.py` — directory walker, kind classifier, snapshot diff

`autolab_common.py` gained `parse_json_object(value, option)` which accepts inline JSON or a leading `@` for file-based input.

## Exit Code Convention

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | run / contract / file not found |
| 2 | invalid args / malformed JSON |
| 3 | hash mismatch or new environment artifact detected |
| 4 | contract is locked, cannot modify |
| 5 | required fields missing, or contract not locked while required |
| 6 | derive-ablation rejected (unknown module, no-op toggle, or non-toggle change) |

## Tests

- `tests/test_autolab_contract.py` — 18 tests covering empty contract creation, freeze (deterministic, file-based input, post-lock refusal), lock (refusal on missing fields, success path), validate (pass / drift / strict-not-locked), derive-ablation (success, unknown module, no-op, unlocked parent, malformed toggle), compare-runs.
- `tests/test_autolab_environment.py` — 8 tests covering checkpoint/output/cache detection, hidden-dir skipping, decisions stub, Markdown report, drift exit code 3, invalid run id and missing workdir.
- `tests/test_autolab_recording.py` — unchanged, all 20 still pass (verified post-implementation).

## Migration

- v0.2.0 runs continue to function read-only; their `config.json` is unchanged.
- v0.3.0 runs additionally write `contract.json` on `start-run`. No migration script is needed.
- The dashboard (separate scope) MAY surface the new fields when read; existing fields remain backwards-compatible.
