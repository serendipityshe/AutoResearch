"""Experiment contract: hyperparameters, pipeline hashes, ablation diff.

The contract lives at `.autolab/runs/<run_id>/contract.json` and is the
machine-checkable counterpart of the human-facing phase reports. Once locked,
its hyperparams / data hashes / module flags / environment fingerprints cannot
be silently changed; subsequent phases re-validate against it.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from autolab_common import (
    read_json,
    run_root,
    utc_now,
    write_json,
)


CONTRACT_SCHEMA_VERSION = "0.2.0"
CONTRACT_FILENAME = "contract.json"
DATA_PIPELINE_FILENAME = "data_pipeline.json"

REQUIRED_HYPERPARAM_FIELDS = ("seed", "optimizer", "lr", "batch_size", "epochs")
REQUIRED_DATA_FIELDS = ("dataset_path", "preprocess_hash", "augment_hash")
REQUIRED_ENVIRONMENT_FIELDS = ("git_commit", "python", "torch")


def empty_contract() -> dict[str, Any]:
    return {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "captured_at": utc_now(),
        "locked_at": "",
        "hyperparams": {
            "seed": None,
            "optimizer": "",
            "lr": None,
            "scheduler": "",
            "batch_size": None,
            "epochs": None,
            "loss_components": {},
        },
        "data": {
            "dataset_path": "",
            "splits": {},
            "preprocess_hash": "",
            "augment_hash": "",
            "input_resolution": [],
            "class_distribution": {},
        },
        "modules": {},
        "environment": {
            "git_commit": "",
            "python": "",
            "torch": "",
            "cuda": "",
            "pretrained_weights": [],
            "environment_decisions_ref": "",
        },
        "parent_run_id": None,
        "ablation_diff": None,
    }


def canonicalize(value: Any) -> str:
    """Stable JSON serialization with sorted keys, used as hash input."""
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def pipeline_hash(spec: Any) -> str:
    return hashlib.sha256(canonicalize(spec).encode("utf-8")).hexdigest()


def contract_path(run_id: str, root: Path | None = None) -> Path:
    return run_root(run_id, root) / CONTRACT_FILENAME


def data_pipeline_path(run_id: str, root: Path | None = None) -> Path:
    return run_root(run_id, root) / DATA_PIPELINE_FILENAME


def load_contract(run_id: str, root: Path | None = None) -> dict[str, Any] | None:
    return read_json(contract_path(run_id, root), None)


def save_contract(run_id: str, contract: dict[str, Any], root: Path | None = None) -> None:
    write_json(contract_path(run_id, root), contract)


def is_locked(contract: dict[str, Any]) -> bool:
    return bool(contract.get("locked_at"))


def missing_required_fields(contract: dict[str, Any]) -> list[str]:
    """Return dotted-path names for fields that must be set before locking."""
    missing: list[str] = []
    hyperparams = contract.get("hyperparams") or {}
    for field in REQUIRED_HYPERPARAM_FIELDS:
        value = hyperparams.get(field)
        if value is None or value == "":
            missing.append(f"hyperparams.{field}")
    data = contract.get("data") or {}
    for field in REQUIRED_DATA_FIELDS:
        if not data.get(field):
            missing.append(f"data.{field}")
    environment = contract.get("environment") or {}
    for field in REQUIRED_ENVIRONMENT_FIELDS:
        if not environment.get(field):
            missing.append(f"environment.{field}")
    if not contract.get("modules"):
        missing.append("modules")
    return missing


def freeze_pipeline(
    run_id: str,
    preprocess: dict[str, Any],
    augment: dict[str, Any],
    root: Path | None = None,
) -> dict[str, str]:
    """Compute and persist preprocess/augment hashes; update contract.

    Returns the two hashes. Raises FileNotFoundError if the run doesn't exist,
    PermissionError if the contract is already locked, ValueError if a spec
    is not a JSON object.
    """
    if not isinstance(preprocess, dict):
        raise ValueError("preprocess spec must be a JSON object")
    if not isinstance(augment, dict):
        raise ValueError("augment spec must be a JSON object")

    directory = run_root(run_id, root)
    if not (directory / "run.json").exists():
        raise FileNotFoundError(f"Run not found: {run_id}")

    pre_hash = pipeline_hash(preprocess)
    aug_hash = pipeline_hash(augment)

    write_json(
        data_pipeline_path(run_id, root),
        {
            "captured_at": utc_now(),
            "preprocess": preprocess,
            "augment": augment,
            "preprocess_hash": pre_hash,
            "augment_hash": aug_hash,
        },
    )

    contract = load_contract(run_id, root) or empty_contract()
    if is_locked(contract):
        raise PermissionError(f"Contract is locked for run {run_id}; cannot modify pipeline")

    contract["data"]["preprocess_hash"] = pre_hash
    contract["data"]["augment_hash"] = aug_hash
    save_contract(run_id, contract, root)

    return {"preprocess_hash": pre_hash, "augment_hash": aug_hash}


def lock_contract(run_id: str, root: Path | None = None) -> dict[str, Any]:
    """Lock the contract by stamping locked_at; refuses if required fields are missing.

    Returns a status dict. Raises FileNotFoundError if the contract doesn't exist,
    ValueError if required fields are missing.
    """
    contract = load_contract(run_id, root)
    if contract is None:
        raise FileNotFoundError(f"Contract not found: {run_id}")
    if is_locked(contract):
        return {"run_id": run_id, "locked": True, "unchanged": True, "locked_at": contract["locked_at"]}
    missing = missing_required_fields(contract)
    if missing:
        raise ValueError(f"Cannot lock; missing required fields: {missing}")
    contract["locked_at"] = utc_now()
    save_contract(run_id, contract, root)
    return {"run_id": run_id, "locked": True, "unchanged": False, "locked_at": contract["locked_at"]}


def validate_against_contract(
    run_id: str,
    preprocess: dict[str, Any] | None = None,
    augment: dict[str, Any] | None = None,
    root: Path | None = None,
    require_locked: bool = False,
) -> dict[str, Any]:
    """Compare current pipeline specs to the locked contract.

    Returns {"ok": bool, "mismatches": [...], "locked": bool}. Raises
    FileNotFoundError if the contract doesn't exist.
    """
    contract = load_contract(run_id, root)
    if contract is None:
        raise FileNotFoundError(f"Contract not found: {run_id}")
    locked = is_locked(contract)
    mismatches: list[dict[str, str]] = []
    if require_locked and not locked:
        return {"ok": False, "locked": False, "mismatches": [], "reason": "contract_not_locked"}

    expected_pre = (contract.get("data") or {}).get("preprocess_hash", "")
    expected_aug = (contract.get("data") or {}).get("augment_hash", "")

    if preprocess is not None and expected_pre:
        actual = pipeline_hash(preprocess)
        if actual != expected_pre:
            mismatches.append({"field": "preprocess_hash", "expected": expected_pre, "actual": actual})
    if augment is not None and expected_aug:
        actual = pipeline_hash(augment)
        if actual != expected_aug:
            mismatches.append({"field": "augment_hash", "expected": expected_aug, "actual": actual})

    return {"ok": not mismatches, "locked": locked, "mismatches": mismatches}


def derive_ablation_contract(
    parent_contract: dict[str, Any],
    toggles: dict[str, bool],
    *,
    allow_pipeline_change: bool = False,
) -> dict[str, Any]:
    """Build a child contract from parent + toggle dict.

    Raises ValueError if a toggle references an unknown module, or if the
    parent contract is not locked, or if non-toggle fields would change.
    The child contract is unlocked (locked_at='') so the child run must
    re-lock after deriving.
    """
    if not is_locked(parent_contract):
        raise ValueError("Parent contract must be locked before deriving ablation")
    parent_modules = parent_contract.get("modules") or {}
    unknown = sorted(name for name in toggles if name not in parent_modules)
    if unknown:
        raise ValueError(f"Toggle references unknown modules: {unknown}")

    child = copy.deepcopy(parent_contract)
    child["captured_at"] = utc_now()
    child["locked_at"] = ""
    child["parent_run_id"] = None  # set by caller (CLI) once child run_id is known
    diff: list[dict[str, Any]] = []
    for name, new_value in toggles.items():
        old_value = child["modules"].get(name)
        if old_value == new_value:
            continue
        child["modules"][name] = new_value
        diff.append({"field": f"modules.{name}", "before": old_value, "after": new_value})
    if not diff and not allow_pipeline_change:
        raise ValueError("No effective toggle change; ablation must differ from parent")
    child["ablation_diff"] = diff
    return child


def diff_contracts(
    a: dict[str, Any],
    b: dict[str, Any],
    *,
    prefix: str = "",
    skip_fields: tuple[str, ...] = ("captured_at", "locked_at"),
) -> list[dict[str, Any]]:
    """Return a list of field-level diffs between two contract dicts."""
    diffs: list[dict[str, Any]] = []
    keys = sorted(set(a.keys()) | set(b.keys()))
    for key in keys:
        if not prefix and key in skip_fields:
            continue
        path = f"{prefix}.{key}" if prefix else key
        if key not in a:
            diffs.append({"field": path, "before": None, "after": b[key], "kind": "added"})
        elif key not in b:
            diffs.append({"field": path, "before": a[key], "after": None, "kind": "removed"})
        else:
            va, vb = a[key], b[key]
            if isinstance(va, dict) and isinstance(vb, dict):
                diffs.extend(diff_contracts(va, vb, prefix=path, skip_fields=skip_fields))
            elif va != vb:
                diffs.append({"field": path, "before": va, "after": vb, "kind": "changed"})
    return diffs
