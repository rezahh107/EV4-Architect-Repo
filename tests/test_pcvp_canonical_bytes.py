from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Callable

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate-pcvp-canonical-bytes.py"
SPEC = importlib.util.spec_from_file_location(
    "_architect_pcvp_canonical_bytes_validator", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

LockMutation = Callable[[dict], None]


def _canonical_checkout() -> Path:
    value = os.environ.get("EV4_DECISION_KERNEL_CHECKOUT")
    if not value:
        pytest.skip("exact Decision Kernel checkout is a CI-only dependency")
    return Path(value)


def _local_inventory_copy(tmp_path: Path) -> Path:
    root = tmp_path / "architect"
    paths = {
        validator.LOCK_PATH,
        *(local for local, _canonical in validator.EXPECTED_RESOURCE_PAIRS),
    }
    for relative in paths:
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return root


def _read_lock(root: Path) -> dict:
    return json.loads((root / validator.LOCK_PATH).read_text(encoding="utf-8"))


def _write_lock(root: Path, lock: dict) -> None:
    (root / validator.LOCK_PATH).write_text(
        json.dumps(lock, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _duplicate_local_path(lock: dict) -> None:
    lock["resources"][1]["path"] = lock["resources"][0]["path"]


def _duplicate_canonical_path(lock: dict) -> None:
    lock["resources"][1]["canonical_path"] = lock["resources"][0][
        "canonical_path"
    ]


def _remove_resource(lock: dict) -> None:
    lock["resources"].pop()


def _add_undeclared_resource(lock: dict) -> None:
    entry = copy.deepcopy(lock["resources"][-1])
    entry["path"] = "contracts/pcvp/undeclared-resource.json"
    entry["canonical_path"] = "04-SCHEMAS/undeclared-resource.json"
    lock["resources"].append(entry)


def _escape_local_path(lock: dict) -> None:
    lock["resources"][0]["path"] = "../escaped-policy.md"


def _escape_canonical_path(lock: dict) -> None:
    lock["resources"][0]["canonical_path"] = "../escaped-policy.md"


def _incorrect_canonical_path(lock: dict) -> None:
    lock["resources"][0][
        "canonical_path"
    ] = "02-MODEL_POLICY/not-the-architect-policy.md"


def test_exact_six_resource_inventory_matches_immutable_canonical_bytes() -> None:
    result = validator.validate_canonical_bytes(ROOT, _canonical_checkout())
    assert result["resource_count"] == 6
    assert {
        (item["path"], item["canonical_path"]) for item in result["matches"]
    } == set(validator.EXPECTED_RESOURCE_PAIRS)


def test_coordinated_local_resource_and_lock_drift_still_fails(
    tmp_path: Path,
) -> None:
    root = _local_inventory_copy(tmp_path)
    lock = _read_lock(root)
    entry = lock["resources"][0]
    resource = root / entry["path"]
    drifted = resource.read_bytes() + b"\ncoordinated-local-drift\n"
    resource.write_bytes(drifted)
    entry["sha256"] = hashlib.sha256(drifted).hexdigest()
    _write_lock(root, lock)

    with pytest.raises(
        validator.CanonicalParityError, match="Canonical PCVP byte mismatch"
    ):
        validator.validate_canonical_bytes(root, _canonical_checkout())


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (_duplicate_local_path, "duplicate local paths"),
        (_duplicate_canonical_path, "duplicate canonical paths"),
        (_remove_resource, "exactly six resources"),
        (_add_undeclared_resource, "exactly six resources"),
        (_escape_local_path, "Unsafe local path"),
        (_escape_canonical_path, "Unsafe canonical path"),
        (_incorrect_canonical_path, "incorrect canonical path mapping"),
    ],
)
def test_invalid_resource_inventory_fails_closed(
    tmp_path: Path,
    mutation: LockMutation,
    message: str,
) -> None:
    root = _local_inventory_copy(tmp_path)
    lock = _read_lock(root)
    mutation(lock)
    _write_lock(root, lock)

    with pytest.raises(validator.CanonicalParityError, match=message):
        validator.validate_canonical_bytes(root, _canonical_checkout())


def test_missing_local_resource_fails_closed(tmp_path: Path) -> None:
    root = _local_inventory_copy(tmp_path)
    lock = _read_lock(root)
    (root / lock["resources"][0]["path"]).unlink()

    with pytest.raises(
        validator.CanonicalParityError, match="Local PCVP resource is unavailable"
    ):
        validator.validate_canonical_bytes(root, _canonical_checkout())


def test_dependency_checkout_head_must_match_lock_snapshot(tmp_path: Path) -> None:
    root = _local_inventory_copy(tmp_path)
    lock = _read_lock(root)
    lock["canonical"]["commit_sha"] = "0" * 40
    _write_lock(root, lock)

    with pytest.raises(
        validator.CanonicalParityError,
        match="Decision Kernel checkout Head mismatch",
    ):
        validator.validate_canonical_bytes(root, _canonical_checkout())


def test_cli_requires_decision_kernel_checkout(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("EV4_DECISION_KERNEL_CHECKOUT", raising=False)
    assert validator.main([]) == 1
    assert "EV4_DECISION_KERNEL_CHECKOUT is required" in capsys.readouterr().err
