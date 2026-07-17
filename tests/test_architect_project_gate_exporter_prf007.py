from __future__ import annotations

import importlib.util
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter_prf007", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = exporter
spec.loader.exec_module(exporter)


def transaction_module():
    return exporter._transaction_module


def force_named_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        transaction_module(),
        "_open_unnamed_candidate",
        lambda parent_descriptor: None,
    )


def residue_path(root: Path, output: Path, token: str) -> Path:
    module = transaction_module()
    return module._candidate_residue_directory_path(root) / module._candidate_name(
        output.name, token
    )


def test_repeated_candidate_collisions_and_exhaustion_preserve_all_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = transaction_module()
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    tokens = [f"collision-{index}" for index in range(4)]
    directory = module._candidate_residue_directory_path(tmp_path)
    directory.mkdir(mode=0o700)
    colliders = []
    for index, token in enumerate(tokens):
        path = directory / module._candidate_name(output.name, token)
        path.write_bytes(f"external-{index}\n".encode())
        colliders.append(path)
    values = iter(tokens)
    monkeypatch.setattr(module, "_CANDIDATE_ALLOCATION_ATTEMPTS", len(tokens))
    monkeypatch.setattr(module.secrets, "token_hex", lambda count: next(values))

    with pytest.raises(exporter.ExportError) as exc:
        exporter.OutputTransaction.stage(output, {"value": 1}, False, root=tmp_path)

    assert exc.value.code == "ARCH_EXPORT_STAGED_CANDIDATE_CREATE_FAILED"
    for index, path in enumerate(colliders):
        assert path.read_bytes() == f"external-{index}\n".encode()


def test_creation_error_before_ownership_does_not_unlink_generated_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = transaction_module()
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    token = "creation-error"
    candidate = residue_path(tmp_path, output, token)
    real_open = module.os.open
    real_close = module.os.close
    monkeypatch.setattr(module.secrets, "token_hex", lambda count: token)

    def failing_open(path, flags, mode=0o777, *, dir_fd=None):
        if path == candidate.name and flags & os.O_EXCL:
            descriptor = real_open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=dir_fd,
            )
            os.write(descriptor, b"external\n")
            real_close(descriptor)
            raise PermissionError("injected before ownership return")
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(module.os, "open", failing_open)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.OutputTransaction.stage(output, {"value": 1}, False, root=tmp_path)

    assert exc.value.code == "ARCH_EXPORT_STAGED_CANDIDATE_CREATE_FAILED"
    assert candidate.read_bytes() == b"external\n"


def test_candidate_replacement_before_stage_error_cleanup_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = transaction_module()
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    token = "stage-replacement"
    candidate = residue_path(tmp_path, output, token)
    real_unlink = os.unlink
    monkeypatch.setattr(module.secrets, "token_hex", lambda count: token)

    def failing_write(descriptor: int, data: bytes) -> None:
        real_unlink(candidate)
        candidate.write_bytes(b"replacement\n")
        raise OSError("injected write failure")

    monkeypatch.setattr(module, "_write_all", failing_write)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.OutputTransaction.stage(output, {"value": 1}, False, root=tmp_path)

    assert exc.value.code == "ARCH_EXPORT_STAGED_CANDIDATE_WRITE_FAILED"
    assert candidate.read_bytes() == b"replacement\n"
    assert "ARCH_EXPORT_CANDIDATE_CLEANUP_CONFLICT" in exc.value.cleanup_warnings


def test_candidate_replacement_before_rollback_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(
        output, {"value": 1}, False, root=tmp_path
    )
    candidate = transaction.candidate.residue_path
    assert candidate is not None
    replacement = tmp_path / "replacement.tmp"
    replacement.write_bytes(b"replacement\n")
    os.replace(replacement, candidate)
    try:
        transaction.rollback()
        assert candidate.read_bytes() == b"replacement\n"
        assert "ARCH_EXPORT_CANDIDATE_CLEANUP_CONFLICT" in transaction.cleanup_warnings
    finally:
        transaction.close()


def test_candidate_name_reuse_after_publication_is_not_removed_by_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(
        output, {"value": 1}, False, root=tmp_path
    )
    candidate = transaction.candidate.residue_path
    assert candidate is not None
    transaction.publish()
    candidate.unlink()
    candidate.write_bytes(b"reused\n")
    transaction.close()

    assert output.exists()
    assert candidate.read_bytes() == b"reused\n"


def test_release_failure_then_name_reuse_is_preserved_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = transaction_module()
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(
        output, {"value": 1}, False, root=tmp_path
    )
    candidate = transaction.candidate.residue_path
    descriptor = transaction.candidate.descriptor
    assert candidate is not None and descriptor is not None
    replacement = tmp_path / "replacement.tmp"
    replacement.write_bytes(b"replacement\n")
    os.replace(replacement, candidate)
    real_close = module.os.close
    close_attempts = 0

    def failing_close(value: int) -> None:
        nonlocal close_attempts
        if value == descriptor:
            close_attempts += 1
            raise OSError("injected close failure")
        real_close(value)

    monkeypatch.setattr(module.os, "close", failing_close)
    try:
        transaction.rollback()
        transaction.close()
        assert close_attempts == 1
        assert candidate.read_bytes() == b"replacement\n"
        assert any(
            warning.startswith("ARCH_EXPORT_CANDIDATE_RELEASE_FAILED:")
            for warning in transaction.cleanup_warnings
        )
        assert "ARCH_EXPORT_CANDIDATE_CLEANUP_CONFLICT" in transaction.cleanup_warnings
    finally:
        real_close(descriptor)


def test_no_identity_check_then_unlink_sequence_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = transaction_module()
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(
        output, {"value": 1}, False, root=tmp_path
    )
    candidate = transaction.candidate.residue_path
    assert candidate is not None
    unlink_calls = []

    def forbidden_unlink(*args, **kwargs):
        unlink_calls.append((args, kwargs))
        raise AssertionError("transaction cleanup must not unlink by pathname")

    monkeypatch.setattr(module.os, "unlink", forbidden_unlink)
    transaction.rollback()
    transaction.close()

    assert unlink_calls == []
    assert candidate.exists()
    assert "ARCH_EXPORT_CANDIDATE_RESIDUE_RETAINED" in transaction.cleanup_warnings


def test_cleanup_conflict_is_reported_as_stable_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(
        output, {"value": 1}, False, root=tmp_path
    )
    candidate = transaction.candidate.residue_path
    assert candidate is not None
    candidate.unlink()
    candidate.write_bytes(b"external\n")
    transaction.rollback()
    warnings = transaction.close()

    assert "ARCH_EXPORT_CANDIDATE_CLEANUP_CONFLICT" in warnings
    assert candidate.read_bytes() == b"external\n"


def test_two_no_overwrite_exporters_still_have_exactly_one_winner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    barrier = threading.Barrier(2)

    def run(value: int) -> str:
        barrier.wait()
        try:
            exporter.atomic_write(output, {"winner": value}, False, root=tmp_path)
            return "ok"
        except exporter.ExportError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(run, (1, 2)))

    assert sorted(outcomes) == ["ARCH_EXPORT_OUTPUT_EXISTS", "ok"]
    assert json.loads(output.read_text(encoding="utf-8"))["winner"] in {1, 2}


def test_concurrent_destination_creation_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    output = tmp_path / "out.json"
    real_link = exporter.os.link

    def concurrent_create(source, destination, **kwargs):
        descriptor = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
            dir_fd=kwargs["dst_dir_fd"],
        )
        os.write(descriptor, b"external\n")
        os.close(descriptor)
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(exporter.os, "link", concurrent_create)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"value": 1}, False, root=tmp_path)

    assert exc.value.code == "ARCH_EXPORT_OUTPUT_EXISTS"
    assert output.read_bytes() == b"external\n"
