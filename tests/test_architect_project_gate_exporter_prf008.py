from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter_prf008", SCRIPT)
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


def capture_named_descriptor(
    monkeypatch: pytest.MonkeyPatch,
    candidate_name: str,
) -> tuple[dict[str, int], object]:
    module = transaction_module()
    real_open = module.os.open
    holder: dict[str, int] = {}

    def opening(path, flags, mode=0o777, *, dir_fd=None):
        descriptor = real_open(path, flags, mode, dir_fd=dir_fd)
        if path == candidate_name and flags & os.O_EXCL:
            holder["descriptor"] = descriptor
        return descriptor

    monkeypatch.setattr(module.os, "open", opening)
    return holder, real_open


def test_named_fstat_failure_reports_retained_residue_without_unlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = transaction_module()
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    token = "identity-fstat-failure"
    candidate = residue_path(tmp_path, output, token)
    monkeypatch.setattr(module.secrets, "token_hex", lambda count: token)
    holder, _ = capture_named_descriptor(monkeypatch, candidate.name)
    real_fstat = module.os.fstat
    capture_attempts = 0

    def failing_once(descriptor: int):
        nonlocal capture_attempts
        if descriptor == holder.get("descriptor"):
            capture_attempts += 1
            if capture_attempts == 1:
                raise OSError("injected identity capture failure")
        return real_fstat(descriptor)

    unlink_calls = []
    monkeypatch.setattr(module.os, "fstat", failing_once)
    monkeypatch.setattr(
        module.os,
        "unlink",
        lambda *args, **kwargs: unlink_calls.append((args, kwargs)),
    )

    with pytest.raises(exporter.ExportError) as exc:
        exporter.OutputTransaction.stage(output, {"value": 1}, False, root=tmp_path)

    assert exc.value.code == "ARCH_EXPORT_CANDIDATE_IDENTITY_CAPTURE_FAILED"
    assert "ARCH_EXPORT_CANDIDATE_RESIDUE_RETAINED" in exc.value.cleanup_warnings
    assert candidate.exists()
    assert unlink_calls == []


def test_replacement_before_residue_reporting_is_preserved_as_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = transaction_module()
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    token = "identity-replacement"
    candidate = residue_path(tmp_path, output, token)
    monkeypatch.setattr(module.secrets, "token_hex", lambda count: token)
    holder, _ = capture_named_descriptor(monkeypatch, candidate.name)
    real_identity = module._identity_from_stat
    replaced = False

    def failing_identity(observed):
        nonlocal replaced
        descriptor = holder.get("descriptor")
        if descriptor is not None:
            owned = module.os.fstat(descriptor)
            if (
                observed.st_dev,
                observed.st_ino,
            ) == (owned.st_dev, owned.st_ino) and not replaced:
                replaced = True
                replacement = tmp_path / "replacement.tmp"
                replacement.write_bytes(b"external replacement\n")
                os.replace(replacement, candidate)
                raise ValueError("injected identity conversion failure")
        return real_identity(observed)

    monkeypatch.setattr(module, "_identity_from_stat", failing_identity)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.OutputTransaction.stage(output, {"value": 1}, False, root=tmp_path)

    assert exc.value.code == "ARCH_EXPORT_CANDIDATE_IDENTITY_CAPTURE_FAILED"
    assert "ARCH_EXPORT_CANDIDATE_CLEANUP_CONFLICT" in exc.value.cleanup_warnings
    assert candidate.read_bytes() == b"external replacement\n"


def test_provisional_close_failure_is_attempted_once_and_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = transaction_module()
    force_named_candidate(monkeypatch)
    output = tmp_path / "out.json"
    token = "identity-close-failure"
    candidate = residue_path(tmp_path, output, token)
    monkeypatch.setattr(module.secrets, "token_hex", lambda count: token)
    holder, _ = capture_named_descriptor(monkeypatch, candidate.name)
    real_fstat = module.os.fstat
    real_close = module.os.close
    close_attempts = 0

    def failing_fstat(descriptor: int):
        if descriptor == holder.get("descriptor"):
            raise OSError("injected identity capture failure")
        return real_fstat(descriptor)

    def failing_close(descriptor: int) -> None:
        nonlocal close_attempts
        if descriptor == holder.get("descriptor"):
            close_attempts += 1
            raise OSError("injected provisional release failure")
        real_close(descriptor)

    unlink_calls = []
    monkeypatch.setattr(module.os, "fstat", failing_fstat)
    monkeypatch.setattr(module.os, "close", failing_close)
    monkeypatch.setattr(
        module.os,
        "unlink",
        lambda *args, **kwargs: unlink_calls.append((args, kwargs)),
    )

    try:
        with pytest.raises(exporter.ExportError) as exc:
            exporter.OutputTransaction.stage(output, {"value": 1}, False, root=tmp_path)

        assert exc.value.code == "ARCH_EXPORT_CANDIDATE_IDENTITY_CAPTURE_FAILED"
        assert close_attempts == 1
        assert any(
            warning.startswith("ARCH_EXPORT_CANDIDATE_RELEASE_FAILED:")
            for warning in exc.value.cleanup_warnings
        )
        assert candidate.exists()
        assert unlink_calls == []
    finally:
        descriptor = holder.get("descriptor")
        if descriptor is not None:
            real_close(descriptor)


@pytest.mark.parametrize("failure_kind", ["identity_conversion", "ownership_construction"])
def test_post_create_failures_keep_candidate_specific_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_kind: str,
):
    module = transaction_module()
    force_named_candidate(monkeypatch)
    output = tmp_path / f"{failure_kind}.json"
    token = failure_kind
    candidate = residue_path(tmp_path, output, token)
    monkeypatch.setattr(module.secrets, "token_hex", lambda count: token)
    holder, _ = capture_named_descriptor(monkeypatch, candidate.name)

    if failure_kind == "identity_conversion":
        real_identity = module._identity_from_stat

        def failing_candidate_identity(observed):
            descriptor = holder.get("descriptor")
            if descriptor is not None:
                owned = module.os.fstat(descriptor)
                if (observed.st_dev, observed.st_ino) == (owned.st_dev, owned.st_ino):
                    raise RuntimeError("injected identity conversion failure")
            return real_identity(observed)

        monkeypatch.setattr(module, "_identity_from_stat", failing_candidate_identity)
    else:
        monkeypatch.setattr(
            module,
            "CandidateOwnership",
            lambda **kwargs: (_ for _ in ()).throw(
                RuntimeError("injected ownership construction failure")
            ),
        )

    with pytest.raises(exporter.ExportError) as exc:
        exporter.OutputTransaction.stage(output, {"value": 1}, False, root=tmp_path)

    assert exc.value.code == "ARCH_EXPORT_CANDIDATE_IDENTITY_CAPTURE_FAILED"
    assert "ARCH_EXPORT_CANDIDATE_RESIDUE_RETAINED" in exc.value.cleanup_warnings
    assert candidate.exists()
    assert "ARCH_EXPORT_OUTPUT_PREFLIGHT_FAILED" not in exc.value.code


def test_unnamed_identity_capture_failure_has_no_named_residue_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = transaction_module()
    if not hasattr(os, "memfd_create"):
        pytest.skip("memfd_create is required for deterministic unnamed-inode simulation")
    descriptor = os.memfd_create("architect-prf008")
    real_fstat = module.os.fstat

    monkeypatch.setattr(
        module,
        "_open_unnamed_candidate",
        lambda parent_descriptor: descriptor,
    )

    def failing_fstat(value: int):
        if value == descriptor:
            raise OSError("injected unnamed identity capture failure")
        return real_fstat(value)

    monkeypatch.setattr(module.os, "fstat", failing_fstat)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.OutputTransaction.stage(
            tmp_path / "out.json", {"value": 1}, False, root=tmp_path
        )

    assert exc.value.code == "ARCH_EXPORT_CANDIDATE_IDENTITY_CAPTURE_FAILED"
    assert not any(
        "RESIDUE" in warning or "CLEANUP_CONFLICT" in warning
        for warning in exc.value.cleanup_warnings
    )


def test_residue_inspection_failure_is_bounded_and_preserves_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = transaction_module()
    force_named_candidate(monkeypatch)
    output = tmp_path / "inspection-failure.json"
    token = "inspection-failure"
    candidate = residue_path(tmp_path, output, token)
    monkeypatch.setattr(module.secrets, "token_hex", lambda count: token)
    holder, _ = capture_named_descriptor(monkeypatch, candidate.name)
    real_fstat = module.os.fstat
    real_lstat = module.os.lstat

    def failing_fstat(descriptor: int):
        if descriptor == holder.get("descriptor"):
            raise OSError("injected identity capture failure")
        return real_fstat(descriptor)

    def failing_lstat(path):
        if Path(path) == candidate:
            raise PermissionError("injected residue inspection failure")
        return real_lstat(path)

    monkeypatch.setattr(module.os, "fstat", failing_fstat)
    monkeypatch.setattr(module.os, "lstat", failing_lstat)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.OutputTransaction.stage(output, {"value": 1}, False, root=tmp_path)

    assert exc.value.code == "ARCH_EXPORT_CANDIDATE_IDENTITY_CAPTURE_FAILED"
    assert any(
        warning.startswith("ARCH_EXPORT_CANDIDATE_RESIDUE_STATUS_UNKNOWN:")
        for warning in exc.value.cleanup_warnings
    )
    assert candidate.exists()
