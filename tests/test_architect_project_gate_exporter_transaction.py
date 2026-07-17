from __future__ import annotations

import importlib.util
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location(
    "architect_project_gate_exporter_transaction", SCRIPT
)
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
            {"payload_hash": "payload", "bundle_hash": "bundle", "export_hash": run_id},
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


def run_unit_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    run_id: str,
    *,
    output: Path | None = None,
    receipt_emitter=None,
):
    fake_pipeline(monkeypatch)
    payload = tmp_path / f"payload-{run_id}.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = output or tmp_path / "out.json"
    return exporter.run_export(
        tmp_path,
        payload,
        output,
        run_id,
        provenance_provider=provider,
        receipt_emitter=receipt_emitter,
    )


def test_overwrite_fails_closed_before_any_destructive_namespace_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    output = tmp_path / "out.json"
    output.write_bytes(b"original\n")
    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(b"concurrent\n")
    real_lstat = exporter.os.lstat
    real_replace = os.replace
    calls = 0

    def racing_lstat(path):
        nonlocal calls
        observed = real_lstat(path)
        if Path(path) == output:
            calls += 1
            if calls == 2:
                real_replace(replacement, output)
        return observed

    monkeypatch.setattr(exporter.os, "lstat", racing_lstat)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"candidate": 1}, overwrite=True)

    assert exc.value.code == "ARCH_EXPORT_ATOMIC_OVERWRITE_UNSUPPORTED"
    assert exc.value.output_written is False
    assert exc.value.destination_present is True
    assert output.read_bytes() == b"concurrent\n"
    assert backups(tmp_path) == []
    assert temps(tmp_path) == []


def test_destination_created_before_nondestructive_rollback_is_preserved(tmp_path: Path):
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(output, {"candidate": 1}, overwrite=False)
    try:
        output.write_bytes(b"external\n")
        transaction.rollback()
        assert output.read_bytes() == b"external\n"
        assert backups(tmp_path) == []
    finally:
        transaction.close()


def test_destination_replaced_before_nondestructive_rollback_is_preserved(tmp_path: Path):
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(output, {"candidate": 1}, overwrite=False)
    try:
        transaction.publish()
        replacement = tmp_path / "replacement.json"
        replacement.write_bytes(b"external-replacement\n")
        os.replace(replacement, output)
        transaction.rollback()
        assert output.read_bytes() == b"external-replacement\n"
        assert transaction.cleanup_warnings == [
            "ARCH_EXPORT_FAILED_OUTPUT_RETAINED:out.json"
        ]
    finally:
        transaction.close()


def test_overwrite_exporter_racing_no_overwrite_exporter_has_one_success(
    tmp_path: Path,
):
    output = tmp_path / "out.json"
    barrier = threading.Barrier(2)

    def run(overwrite: bool) -> str:
        barrier.wait()
        try:
            exporter.atomic_write(output, {"overwrite": overwrite}, overwrite=overwrite)
            return "ok"
        except exporter.ExportError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, [True, False]))

    assert sorted(results) == ["ARCH_EXPORT_ATOMIC_OVERWRITE_UNSUPPORTED", "ok"]
    assert json.loads(output.read_text(encoding="utf-8")) == {"overwrite": False}
    assert backups(tmp_path) == []


def test_external_writer_racing_quarantine_cannot_be_moved(tmp_path: Path):
    output = tmp_path / "out.json"
    output.write_bytes(b"external-current\n")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"candidate": 1}, overwrite=True)
    assert exc.value.code == "ARCH_EXPORT_ATOMIC_OVERWRITE_UNSUPPORTED"
    assert output.read_bytes() == b"external-current\n"
    assert backups(tmp_path) == []


def test_external_writer_racing_rollback_restoration_cannot_be_clobbered(tmp_path: Path):
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(output, {"candidate": 1}, overwrite=False)
    try:
        transaction.publish()
        replacement = tmp_path / "replacement.json"
        replacement.write_bytes(b"external-current\n")
        os.replace(replacement, output)
        transaction.rollback()
        assert output.read_bytes() == b"external-current\n"
        assert backups(tmp_path) == []
    finally:
        transaction.close()


def test_prior_artifact_remains_recoverable_at_original_path_when_overwrite_rejected(
    tmp_path: Path,
):
    output = tmp_path / "out.json"
    output.write_bytes(b"prior-artifact\n")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"candidate": 1}, overwrite=True)
    report = exc.value.report()
    assert output.read_bytes() == b"prior-artifact\n"
    assert report["backup_retained"] is False
    assert report["backup_path"] is None
    assert report["destination_present"] is True


def test_identity_drift_never_reports_concurrent_bytes_as_output_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    validations = 0

    def validate(root, value):
        nonlocal validations
        validations += 1
        if validations == 3:
            replacement = tmp_path / "replacement.json"
            replacement.write_text('{"external":true}\n', encoding="utf-8")
            os.replace(replacement, output)

    monkeypatch.setattr(exporter, "validate_contracts", validate)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(
            tmp_path,
            payload,
            output,
            "identity-drift",
            provenance_provider=provider,
        )

    assert exc.value.code == "ARCH_EXPORT_OUTPUT_IDENTITY_DRIFT"
    assert exc.value.output_written is False
    assert exc.value.destination_present is True
    assert exc.value.concurrent_destination_preserved is True
    assert output.read_text(encoding="utf-8") == '{"external":true}\n'


def test_second_exporter_waits_through_first_historical_receipt_emission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    output = tmp_path / "out.json"
    first_payload = tmp_path / "payload-first.json"
    second_payload = tmp_path / "payload-second.json"
    first_payload.write_text("{}\n", encoding="utf-8")
    second_payload.write_text("{}\n", encoding="utf-8")
    receipt_entered = threading.Event()
    release_receipt = threading.Event()
    second_done = threading.Event()
    receipts: list[exporter.ExportResult] = []
    outcomes: dict[str, str] = {}

    def emitter(result):
        receipts.append(result)
        receipt_entered.set()
        assert release_receipt.wait(timeout=5)

    def first():
        result = exporter.run_export(
            tmp_path,
            first_payload,
            output,
            "first",
            provenance_provider=provider,
            receipt_emitter=emitter,
        )
        outcomes["first"] = result.export_hash

    def second():
        try:
            exporter.run_export(
                tmp_path,
                second_payload,
                output,
                "second",
                provenance_provider=provider,
            )
            outcomes["second"] = "ok"
        except exporter.ExportError as exc:
            outcomes["second"] = exc.code
        finally:
            second_done.set()

    first_thread = threading.Thread(target=first)
    first_thread.start()
    assert receipt_entered.wait(timeout=5)
    second_thread = threading.Thread(target=second)
    second_thread.start()
    time.sleep(0.1)
    assert not second_done.is_set()
    release_receipt.set()
    first_thread.join(timeout=5)
    second_thread.join(timeout=5)

    assert outcomes["second"] == "ARCH_EXPORT_OUTPUT_EXISTS"
    assert len(receipts) == 1
    assert receipts[0].receipt_scope == "historical_commit"
    assert receipts[0].current_destination_claim is False
    assert receipts[0].output_written is False
    assert receipts[0].output_committed is True


def test_two_hashes_cannot_both_be_reported_as_current_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    output = tmp_path / "out.json"
    claims: list[tuple[str, bool]] = []

    def emitter(result):
        claims.append((result.export_hash, result.current_destination_claim))

    first_payload = tmp_path / "payload-first.json"
    first_payload.write_text("{}\n", encoding="utf-8")
    exporter.run_export(
        tmp_path,
        first_payload,
        output,
        "hash-a",
        provenance_provider=provider,
        receipt_emitter=emitter,
    )
    second_payload = tmp_path / "payload-second.json"
    second_payload.write_text("{}\n", encoding="utf-8")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(
            tmp_path,
            second_payload,
            output,
            "hash-b",
            provenance_provider=provider,
            receipt_emitter=emitter,
        )

    assert exc.value.code == "ARCH_EXPORT_OUTPUT_EXISTS"
    assert claims == [("hash-a", False)]


def test_unsupported_atomic_overwrite_platform_fails_closed(tmp_path: Path):
    output = tmp_path / "out.json"
    output.write_bytes(b"existing\n")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"candidate": 1}, overwrite=True)
    assert exc.value.code == "ARCH_EXPORT_ATOMIC_OVERWRITE_UNSUPPORTED"
    assert output.read_bytes() == b"existing\n"


def test_missing_platform_lock_support_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(exporter, "fcntl", None)
    monkeypatch.setattr(exporter, "msvcrt", None)
    output = tmp_path / "out.json"
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"candidate": 1}, overwrite=False)
    assert exc.value.code == "ARCH_EXPORT_OUTPUT_LOCK_UNAVAILABLE"
    assert not output.exists()


def test_two_no_overwrite_publishers_remain_one_success_one_output_exists(
    tmp_path: Path,
):
    for index in range(10):
        output = tmp_path / f"out-{index}.json"
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


def test_same_lock_coordinates_no_overwrite_transactions(tmp_path: Path):
    output = tmp_path / "out.json"
    held = exporter.OutputLock(exporter._output_lock_path(output))
    held.acquire()
    finished = threading.Event()

    def writer():
        exporter.atomic_write(output, {"writer": True}, overwrite=False)
        finished.set()

    thread = threading.Thread(target=writer)
    thread.start()
    time.sleep(0.1)
    assert not finished.is_set()
    held.release()
    thread.join(timeout=5)
    assert finished.is_set()
    assert json.loads(output.read_text(encoding="utf-8")) == {"writer": True}


def test_final_destination_identity_drift_is_detected_without_clobber(tmp_path: Path):
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(output, {"candidate": 1}, overwrite=False)
    try:
        transaction.publish()
        replacement = tmp_path / "replacement.json"
        replacement.write_bytes(b"external\n")
        os.replace(replacement, output)
        with pytest.raises(exporter.ExportError) as exc:
            transaction.verify_owned("identity-test")
        assert exc.value.code == "ARCH_EXPORT_OUTPUT_IDENTITY_DRIFT"
        assert exc.value.concurrent_destination_preserved is True
        transaction.rollback()
        assert output.read_bytes() == b"external\n"
    finally:
        transaction.close()


def test_final_destination_byte_drift_is_detected_without_deletion(tmp_path: Path):
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(output, {"candidate": 1}, overwrite=False)
    try:
        transaction.publish()
        output.write_bytes(b'{"tampered":true}\n')
        with pytest.raises(exporter.ExportError) as exc:
            transaction.verify_owned("byte-test")
        assert exc.value.code == "ARCH_EXPORT_OUTPUT_BYTE_DRIFT"
        transaction.rollback()
        assert output.read_bytes() == b'{"tampered":true}\n'
    finally:
        transaction.close()


def test_overwrite_fail_closed_never_enters_backup_cleanup(tmp_path: Path):
    output = tmp_path / "out.json"
    output.write_bytes(b"existing\n")
    with pytest.raises(exporter.ExportError):
        exporter.atomic_write(output, {"candidate": 1}, overwrite=True)
    assert backups(tmp_path) == []
    assert temps(tmp_path) == []


def test_lock_release_cleanup_warning_is_operator_visible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    real_release = exporter.OutputLock.release

    def warning_release(self):
        real_release(self)
        return "ARCH_EXPORT_OUTPUT_LOCK_RELEASE_FAILED:Injected"

    monkeypatch.setattr(exporter.OutputLock, "release", warning_release)
    result = exporter.run_export(
        tmp_path,
        payload,
        output,
        "cleanup-warning",
        provenance_provider=provider,
    )
    assert result.cleanup_warnings == [
        "ARCH_EXPORT_OUTPUT_LOCK_RELEASE_FAILED:Injected"
    ]


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
        exporter.run_export(
            tmp_path,
            payload,
            output,
            "run",
            provenance_provider=drifting_provider,
        )
    assert exc.value.code == "ARCH_EXPORT_PROVENANCE_DRIFT"
    assert changed_field in exc.value.reason
    assert not output.exists()
    assert temps(tmp_path) == []


def test_tracked_contract_drift_before_publication_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
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
        exporter.run_export(
            tmp_path,
            payload,
            output,
            "run",
            provenance_provider=dirty_provider,
        )
    assert exc.value.code == "ARCH_EXPORT_DIRTY_WORKTREE"
    assert not output.exists()


def test_final_provenance_drift_retains_unclaimed_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    states = iter([git(), git(), git(sha="b" * 40)])

    def drifting_provider(root, payload_path, output_path, allowed_paths):
        return next(states)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(
            tmp_path,
            payload,
            output,
            "run",
            provenance_provider=drifting_provider,
        )
    assert exc.value.code == "ARCH_EXPORT_PROVENANCE_DRIFT"
    assert exc.value.output_written is False
    assert exc.value.destination_present is True
    assert output.exists()


def test_unicode_output_path_remains_supported(tmp_path: Path):
    output = tmp_path / "معماری-خروجی.json"
    exporter.atomic_write(output, {"value": "معماری"}, overwrite=False)
    assert json.loads(output.read_text(encoding="utf-8")) == {"value": "معماری"}


def test_existing_symlink_is_rejected(tmp_path: Path):
    target = tmp_path / "target.json"
    target.write_text("target\n", encoding="utf-8")
    link = tmp_path / "out.json"
    link.symlink_to(target)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(link, {"candidate": 1}, overwrite=False)
    assert exc.value.code == "ARCH_EXPORT_UNSAFE_OUTPUT_PATH"
    assert target.read_text(encoding="utf-8") == "target\n"


def test_existing_non_regular_output_is_rejected(tmp_path: Path):
    output = tmp_path / "out.json"
    output.mkdir()
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"candidate": 1}, overwrite=False)
    assert exc.value.code == "ARCH_EXPORT_OUTPUT_PATH_TYPE_INVALID"


def test_exact_canonical_bytes_and_hash_verification_remain_stable(tmp_path: Path):
    output = tmp_path / "out.json"
    value = {"z": "معماری", "a": 1}
    exporter.atomic_write(output, value, overwrite=False)
    assert output.read_bytes() == exporter.canonical_bytes(value) + b"\n"
    assert exporter.digest(value) == exporter.digest(json.loads(output.read_text()))
