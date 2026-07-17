from __future__ import annotations

import importlib.util
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter_transaction", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = exporter
spec.loader.exec_module(exporter)


def fake_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(exporter, "validate_payload", lambda root, value: {"status": "valid"})
    monkeypatch.setattr(
        exporter,
        "build_export",
        lambda value, provenance, run_id, input_ref: (
            {
                "handoff": {"status": "successful", "allowed": True},
                "export_id": f"unit-export-{run_id}",
                "producer": {"commit_sha": provenance.commit_sha},
            },
            {"payload_hash": "payload", "bundle_hash": "bundle", "export_hash": "export"},
        ),
    )
    monkeypatch.setattr(exporter, "validate_contracts", lambda root, value: None)
    monkeypatch.setattr(exporter, "verify_hashes", lambda value, hashes: None)


def git(ref: str = "main", sha: str = "a" * 40):
    return exporter.GitProvenance(exporter.REPOSITORY, ref, sha)


def provider(root, payload_path, output_path, allowed_paths):
    return git()


def backups(path: Path) -> list[Path]:
    return [item for item in path.iterdir() if item.name.endswith(".bak")]


def temps(path: Path) -> list[Path]:
    return [item for item in path.iterdir() if item.name.endswith(".tmp")]


def test_overwrite_quarantine_concurrent_destination_preserved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    output = tmp_path / "out.json"
    output.write_bytes(b"original\n")
    real_link = exporter.os.link

    def racing_link(source, destination, **kwargs):
        Path(destination).write_bytes(b"concurrent\n")
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(exporter.os, "link", racing_link)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"candidate": 1}, overwrite=True)

    assert exc.value.code == "ARCH_EXPORT_ROLLBACK_CONFLICT"
    assert output.read_bytes() == b"concurrent\n"
    assert len(backups(tmp_path)) == 1
    assert backups(tmp_path)[0].read_bytes() == b"original\n"
    assert temps(tmp_path) == []


def test_published_candidate_replaced_before_rollback_is_not_clobbered(tmp_path: Path):
    output = tmp_path / "out.json"
    output.write_bytes(b"original\n")
    transaction = exporter.OutputTransaction.stage(output, {"candidate": 1}, overwrite=True)
    try:
        transaction.publish()
        replacement = tmp_path / "replacement.json"
        replacement.write_bytes(b"concurrent-replacement\n")
        os.replace(replacement, output)

        with pytest.raises(exporter.ExportError) as exc:
            transaction.rollback()

        assert exc.value.code == "ARCH_EXPORT_ROLLBACK_CONFLICT"
        assert output.read_bytes() == b"concurrent-replacement\n"
        assert transaction.backup is not None
        assert transaction.backup.read_bytes() == b"original\n"
    finally:
        transaction.close()


def test_two_concurrent_overwrite_exporters_at_most_one_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    output = tmp_path / "out.json"
    output.write_text('{"old":true}\n', encoding="utf-8")
    first_in_link = threading.Event()
    release_first = threading.Event()
    real_link = exporter.os.link

    def delayed_link(source, destination, **kwargs):
        if threading.current_thread().name == "first-exporter":
            first_in_link.set()
            assert release_first.wait(timeout=5)
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(exporter.os, "link", delayed_link)

    def run(value: int) -> str:
        try:
            exporter.atomic_write(output, {"winner": value}, overwrite=True)
            return "ok"
        except exporter.ExportError as exc:
            return exc.code

    results: dict[str, str] = {}

    def first_call():
        threading.current_thread().name = "first-exporter"
        results["first"] = run(1)

    def second_call():
        threading.current_thread().name = "second-exporter"
        results["second"] = run(2)

    t1 = threading.Thread(target=first_call)
    t1.start()
    assert first_in_link.wait(timeout=5)
    t2 = threading.Thread(target=second_call)
    t2.start()
    t2.join(timeout=5)
    release_first.set()
    t1.join(timeout=5)

    assert list(results.values()).count("ok") == 1
    assert set(results.values()) <= {
        "ok",
        "ARCH_EXPORT_OUTPUT_LOCKED",
        "ARCH_EXPORT_OUTPUT_CHANGED_BEFORE_LOCK",
    }
    assert json.loads(output.read_text(encoding="utf-8"))["winner"] == 1


def test_final_destination_identity_drift_never_reports_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    output.write_bytes(b"original\n")
    validations = 0

    def validate(root, value):
        nonlocal validations
        validations += 1
        if validations == 3:
            replacement = tmp_path / "replacement.json"
            replacement.write_text('{"concurrent":true}\n', encoding="utf-8")
            os.replace(replacement, output)

    monkeypatch.setattr(exporter, "validate_contracts", validate)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(
            tmp_path,
            payload,
            output,
            "identity-drift",
            overwrite=True,
            provenance_provider=provider,
        )

    assert exc.value.code == "ARCH_EXPORT_ROLLBACK_CONFLICT"
    assert output.read_text(encoding="utf-8") == '{"concurrent":true}\n'
    assert len(backups(tmp_path)) == 1
    assert backups(tmp_path)[0].read_bytes() == b"original\n"


def test_final_destination_byte_drift_never_reports_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    output.write_bytes(b"original\n")
    verifications = 0

    def verify(value, hashes):
        nonlocal verifications
        verifications += 1
        expected = "unit-export-byte-drift"
        if value.get("export_id") != expected:
            raise exporter.ExportError(
                "ARCH_EXPORT_HASH_SELF_VERIFICATION_FAILED",
                "hash_self_verification",
                "final bytes changed",
                "repository_owner",
            )
        if verifications == 3:
            output.write_text('{"export_id":"tampered"}\n', encoding="utf-8")

    monkeypatch.setattr(exporter, "verify_hashes", verify)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(
            tmp_path,
            payload,
            output,
            "byte-drift",
            overwrite=True,
            provenance_provider=provider,
        )

    assert exc.value.code == "ARCH_EXPORT_HASH_SELF_VERIFICATION_FAILED"
    assert output.read_bytes() == b"original\n"
    assert backups(tmp_path) == []


def test_backup_cleanup_first_failure_then_retry_succeeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    output.write_bytes(b"original\n")
    original_unlink = Path.unlink
    attempts = 0

    def flaky_unlink(self, *args, **kwargs):
        nonlocal attempts
        if self.name.endswith(".bak") and self.exists() and self.stat().st_size > 0:
            attempts += 1
            if attempts == 1:
                raise OSError("first cleanup failure")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", flaky_unlink)
    result = exporter.run_export(
        tmp_path,
        payload,
        output,
        "cleanup-retry",
        overwrite=True,
        provenance_provider=provider,
    )

    assert result.output_written is True
    assert result.cleanup_warnings == ["ARCH_EXPORT_BACKUP_CLEANUP_RETRY:1:OSError"]
    assert backups(tmp_path) == []


def test_all_backup_cleanup_attempts_report_retained_residue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    output.write_bytes(b"original\n")
    original_unlink = Path.unlink

    def failing_unlink(self, *args, **kwargs):
        if self.name.endswith(".bak") and self.exists() and self.stat().st_size > 0:
            raise OSError("persistent cleanup failure")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failing_unlink)
    result = exporter.run_export(
        tmp_path,
        payload,
        output,
        "cleanup-retained",
        overwrite=True,
        provenance_provider=provider,
    )

    assert result.output_written is True
    assert result.cleanup_warnings[:2] == [
        "ARCH_EXPORT_BACKUP_CLEANUP_RETRY:1:OSError",
        "ARCH_EXPORT_BACKUP_CLEANUP_RETRY:2:OSError",
    ]
    assert result.cleanup_warnings[2].startswith("ARCH_EXPORT_BACKUP_RETAINED:")
    assert len(backups(tmp_path)) == 1
    assert backups(tmp_path)[0].read_bytes() == b"original\n"


def test_two_no_overwrite_publishers_remain_one_success_one_output_exists(tmp_path: Path):
    output = tmp_path / "out.json"
    barrier = threading.Barrier(2)

    def run(value: int) -> str:
        barrier.wait()
        try:
            exporter.atomic_write(output, {"winner": value}, overwrite=False)
            return "ok"
        except exporter.ExportError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, [1, 2]))

    assert sorted(results) == ["ARCH_EXPORT_OUTPUT_EXISTS", "ok"]
    assert json.loads(output.read_text(encoding="utf-8"))["winner"] in {1, 2}
    assert backups(tmp_path) == []
    assert temps(tmp_path) == []


@pytest.mark.parametrize(
    ("second", "changed_field"),
    [(git(sha="b" * 40), "HEAD"), (git(ref="other"), "ref")],
)
def test_provenance_drift_before_publication_writes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    second,
    changed_field: str,
):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    states = iter([git(), second])

    def drifting_provider(root, payload_path, output_path, allowed_paths):
        return next(states)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(tmp_path, payload, output, "run", provenance_provider=drifting_provider)

    assert exc.value.code == "ARCH_EXPORT_PROVENANCE_DRIFT"
    assert changed_field in exc.value.reason
    assert not output.exists()
    assert backups(tmp_path) == []
    assert temps(tmp_path) == []


def test_tracked_contract_drift_before_publication_writes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    calls = 0

    def dirty_provider(root, payload_path, output_path, allowed_paths):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise exporter.ExportError(
                "ARCH_EXPORT_DIRTY_WORKTREE",
                "git_provenance",
                "tracked contract changed",
                "operator",
            )
        return git()

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(tmp_path, payload, output, "run", provenance_provider=dirty_provider)

    assert exc.value.code == "ARCH_EXPORT_DIRTY_WORKTREE"
    assert not output.exists()
    assert backups(tmp_path) == []
    assert temps(tmp_path) == []


def test_final_provenance_drift_removes_new_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    states = iter([git(), git(), git(sha="b" * 40)])

    def drifting_provider(root, payload_path, output_path, allowed_paths):
        return next(states)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(tmp_path, payload, output, "run", provenance_provider=drifting_provider)

    assert exc.value.code == "ARCH_EXPORT_PROVENANCE_DRIFT"
    assert not output.exists()
    assert backups(tmp_path) == []
    assert temps(tmp_path) == []


def test_overwrite_restores_previous_output_on_final_provenance_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    output.write_bytes(b"previous-output\n")
    states = iter([git(), git(), git(ref="other")])

    def drifting_provider(root, payload_path, output_path, allowed_paths):
        return next(states)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(
            tmp_path,
            payload,
            output,
            "run",
            overwrite=True,
            provenance_provider=drifting_provider,
        )

    assert exc.value.code == "ARCH_EXPORT_PROVENANCE_DRIFT"
    assert output.read_bytes() == b"previous-output\n"
    assert backups(tmp_path) == []
    assert temps(tmp_path) == []


def test_postwrite_validation_failure_restores_previous_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    output.write_bytes(b"previous-output\n")
    validations = 0

    def validate(root, value):
        nonlocal validations
        validations += 1
        if validations == 3:
            raise exporter.ExportError(
                "TEST_POSTWRITE_FAILURE",
                "post_write_validation",
                "fail",
                "repository_owner",
            )

    monkeypatch.setattr(exporter, "validate_contracts", validate)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(
            tmp_path,
            payload,
            output,
            "run",
            overwrite=True,
            provenance_provider=provider,
        )

    assert exc.value.code == "TEST_POSTWRITE_FAILURE"
    assert output.read_bytes() == b"previous-output\n"
    assert backups(tmp_path) == []
    assert temps(tmp_path) == []


def test_existing_symlink_is_rejected(tmp_path: Path):
    target = tmp_path / "target.json"
    target.write_text("target\n", encoding="utf-8")
    link = tmp_path / "out.json"
    link.symlink_to(target)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.inside(tmp_path, link)

    assert exc.value.code == "ARCH_EXPORT_UNSAFE_OUTPUT_PATH"
