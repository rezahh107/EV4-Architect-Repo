from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SPEC = importlib.util.spec_from_file_location(
    "_architect_quality_runtime_public_failure_test",
    SCRIPTS / "architect_quality_runtime.py",
)
assert SPEC is not None and SPEC.loader is not None
runtime = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runtime
SPEC.loader.exec_module(runtime)
legacy = importlib.import_module("_legacy_architect_runtime_truth_spine")
finalization = importlib.import_module("architect_project_gate_finalization")
contracts = importlib.import_module("architect_project_gate_exporter.contracts")


def finalize(directory: Path):
    return runtime.finalize_project_gate(
        legacy.full_outputs(),
        run_context=legacy.context("fixture"),
        repository_root=ROOT,
        output_directory=directory,
        git_provider=legacy.FixtureGitProvider(),
    )


def assert_not_published(result, directory: Path) -> None:
    assert result.finalization_succeeded is False
    assert result.publication_status == "not_published"
    assert not (directory / "architect-project-gate.json").exists()
    assert not (directory / "architect-project-gate-receipt.json").exists()


def test_publication_inside_architect_repository_is_forbidden(tmp_path: Path) -> None:
    directory = ROOT / ".test-project-gate-publication"
    try:
        assert_not_published(finalize(directory), directory)
    finally:
        for path in (
            directory / "architect-project-gate.json",
            directory / "architect-project-gate-receipt.json",
        ):
            path.unlink(missing_ok=True)
        directory.rmdir() if directory.exists() else None


def test_contract_or_hash_failure_prevents_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args, **kwargs):
        raise contracts.ExportError(
            "ARCH_EXPORT_TEST_HASH_FAILURE", "hash_self_verification",
            "Injected hash failure.", "repository_owner"
        )

    monkeypatch.setattr(contracts, "verify_hashes", fail)
    assert_not_published(finalize(tmp_path), tmp_path)


def test_artifact_write_failure_does_not_publish_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        finalization,
        "_publish_no_replace",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("artifact failed")),
    )
    assert_not_published(finalize(tmp_path), tmp_path)


def test_receipt_write_failure_removes_owned_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = finalization._publish_no_replace
    calls = 0

    def fail_second(staged: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("receipt failed")
        original(staged, destination)

    monkeypatch.setattr(finalization, "_publish_no_replace", fail_second)
    assert_not_published(finalize(tmp_path), tmp_path)


def test_existing_destination_fails_closed(tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    artifact = tmp_path / "architect-project-gate.json"
    artifact.write_text("caller-owned", encoding="utf-8")
    result = finalize(tmp_path)
    assert result.finalization_succeeded is False
    assert artifact.read_text(encoding="utf-8") == "caller-owned"
    assert not (tmp_path / "architect-project-gate-receipt.json").exists()
