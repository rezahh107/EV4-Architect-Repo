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

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export-architect-project-gate.py"
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
            {"payload_hash": "payload", "bundle_hash": "bundle", "export_hash": run_id},
        ),
    )
    monkeypatch.setattr(exporter, "validate_contracts", lambda root, value: None)
    monkeypatch.setattr(exporter, "verify_hashes", lambda value, hashes: None)


def git(ref: str = "main", sha: str = "a" * 40):
    return exporter.GitProvenance(exporter.REPOSITORY, ref, sha)


def provider(root, payload_path, output_path, allowed_paths):
    return git()


def run_unit_export(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    run_id: str,
    output: Path,
    *,
    receipt_emitter=None,
    provenance_provider=provider,
):
    fake_pipeline(monkeypatch)
    payload = root / f"payload-{run_id}.json"
    payload.write_text("{}\n", encoding="utf-8")
    return exporter.run_export(
        root,
        payload,
        output,
        run_id,
        provenance_provider=provenance_provider,
        receipt_emitter=receipt_emitter,
    )


def test_overwrite_remains_fail_closed(tmp_path: Path):
    output = tmp_path / "out.json"
    output.write_bytes(b"existing\n")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"candidate": 1}, overwrite=True)
    assert exc.value.code == "ARCH_EXPORT_ATOMIC_OVERWRITE_UNSUPPORTED"
    assert output.read_bytes() == b"existing\n"


def test_two_no_overwrite_publishers_one_success(tmp_path: Path):
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


def test_overwrite_and_no_overwrite_share_lock(tmp_path: Path):
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


def test_external_destination_replacement_is_preserved(tmp_path: Path):
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(output, {"candidate": 1}, False)
    try:
        transaction.publish()
        replacement = tmp_path / "replacement.json"
        replacement.write_bytes(b"external\n")
        os.replace(replacement, output)
        with pytest.raises(exporter.ExportError) as exc:
            transaction.verify_owned("external-replacement")
        assert exc.value.code == "ARCH_EXPORT_OUTPUT_IDENTITY_DRIFT"
        transaction.rollback()
        assert output.read_bytes() == b"external\n"
    finally:
        transaction.close()


def test_exact_byte_drift_is_detected_without_deletion(tmp_path: Path):
    output = tmp_path / "out.json"
    transaction = exporter.OutputTransaction.stage(output, {"candidate": 1}, False)
    try:
        transaction.publish()
        output.write_bytes(b'{"tampered":true}\n')
        with pytest.raises(exporter.ExportError) as exc:
            transaction.verify_owned("byte-drift")
        assert exc.value.code == "ARCH_EXPORT_OUTPUT_BYTE_DRIFT"
        transaction.rollback()
        assert output.read_bytes() == b'{"tampered":true}\n'
    finally:
        transaction.close()


def test_parent_renamed_outside_after_final_provenance_blocks_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    repo = tmp_path / "repo"
    repo.mkdir()
    parent = repo / "run"
    parent.mkdir()
    outside = tmp_path / "outside-run"
    output = parent / "out.json"
    receipts = []
    calls = 0

    def drifting_provider(root, payload_path, output_path, allowed_paths):
        nonlocal calls
        calls += 1
        if calls == 3:
            os.rename(parent, outside)
            parent.symlink_to(outside, target_is_directory=True)
        return git()

    with pytest.raises(exporter.ExportError) as exc:
        run_unit_export(
            repo,
            monkeypatch,
            "ancestry-after-final-git",
            output,
            provenance_provider=drifting_provider,
            receipt_emitter=receipts.append,
        )
    assert exc.value.code == "ARCH_EXPORT_OUTPUT_ANCESTRY_DRIFT"
    assert receipts == []
    assert (outside / "out.json").exists()


def test_unchanged_output_inode_does_not_hide_ancestry_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    repo = tmp_path / "repo"
    repo.mkdir()
    parent = repo / "run"
    parent.mkdir()
    outside = tmp_path / "outside-run"
    output = parent / "out.json"
    captured_identity = None
    calls = 0

    def drifting_provider(root, payload_path, output_path, allowed_paths):
        nonlocal calls, captured_identity
        calls += 1
        if calls == 3:
            captured_identity = exporter._identity(output)
            os.rename(parent, outside)
            parent.symlink_to(outside, target_is_directory=True)
            assert exporter._identity(outside / "out.json") == captured_identity
        return git()

    with pytest.raises(exporter.ExportError) as exc:
        run_unit_export(repo, monkeypatch, "same-inode", output, provenance_provider=drifting_provider)
    assert exc.value.code == "ARCH_EXPORT_OUTPUT_ANCESTRY_DRIFT"


def test_parent_drift_before_publication_leaves_no_authoritative_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    repo = tmp_path / "repo"
    repo.mkdir()
    parent = repo / "run"
    parent.mkdir()
    outside = tmp_path / "outside-run"
    output = parent / "out.json"
    calls = 0

    def drifting_provider(root, payload_path, output_path, allowed_paths):
        nonlocal calls
        calls += 1
        if calls == 2:
            os.rename(parent, outside)
            parent.symlink_to(outside, target_is_directory=True)
        return git()

    with pytest.raises(exporter.ExportError) as exc:
        run_unit_export(repo, monkeypatch, "before-publication", output, provenance_provider=drifting_provider)
    assert exc.value.code == "ARCH_EXPORT_OUTPUT_ANCESTRY_DRIFT"
    assert not (outside / "out.json").exists()


def test_intermediate_component_symlink_is_rejected(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / "run").symlink_to(outside, target_is_directory=True)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(repo / "run" / "out.json", {"value": 1}, False, root=repo)
    assert exc.value.code in {
        "ARCH_EXPORT_OUTPUT_ANCESTRY_UNSAFE",
        "ARCH_EXPORT_OUTPUT_ANCESTRY_INSPECTION_FAILED",
    }
    assert not (outside / "out.json").exists()


def test_root_identity_drift_is_detected(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    output = root / "out.json"
    transaction = exporter.OutputTransaction.stage(output, {"value": 1}, False, root=root)
    moved = tmp_path / "moved-repo"
    try:
        transaction.publish()
        os.rename(root, moved)
        root.symlink_to(moved, target_is_directory=True)
        with pytest.raises(exporter.ExportError) as exc:
            transaction.verify_owned("root-drift")
        assert exc.value.code == "ARCH_EXPORT_OUTPUT_ANCESTRY_DRIFT"
    finally:
        transaction.close()


def test_destination_file_not_found_during_single_stat_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    output = tmp_path / "out.json"
    real_stat = exporter.os.stat
    injected = False

    def racing_stat(path, *args, **kwargs):
        nonlocal injected
        if path == output.name and kwargs.get("dir_fd") is not None and not injected:
            injected = True
            raise FileNotFoundError(path)
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(exporter.os, "stat", racing_stat)
    exporter.atomic_write(output, {"value": 1}, False)
    assert json.loads(output.read_text(encoding="utf-8")) == {"value": 1}


def test_destination_inspection_oserror_is_stable_export_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    output = tmp_path / "out.json"
    real_stat = exporter.os.stat

    def failing_stat(path, *args, **kwargs):
        if path == output.name and kwargs.get("dir_fd") is not None:
            raise PermissionError("injected")
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(exporter.os, "stat", failing_stat)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"value": 1}, False)
    assert exc.value.code == "ARCH_EXPORT_OUTPUT_INSPECTION_FAILED"


def test_cli_preflight_race_emits_no_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(exporter, "run_export", lambda *args, **kwargs: (_ for _ in ()).throw(
        exporter.ExportError(
            "ARCH_EXPORT_OUTPUT_INSPECTION_FAILED",
            "output_preflight",
            "stable failure",
            "operator",
        )
    ))
    code = exporter.main([
        "--repo-root", str(tmp_path),
        "--payload", str(payload),
        "--run-id", "race",
        "--format", "json",
    ])
    captured = capsys.readouterr()
    assert code == 1
    assert "ARCH_EXPORT_OUTPUT_INSPECTION_FAILED" in captured.err
    assert "Traceback" not in captured.err


def test_receipt_is_emitted_while_lock_and_ancestry_are_held(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    output = tmp_path / "out.json"
    observed = []

    def emitter(result):
        observed.append(result)
        assert result.receipt_scope == "historical_commit"
        assert result.current_destination_claim is False

    result = run_unit_export(tmp_path, monkeypatch, "receipt", output, receipt_emitter=emitter)
    assert observed == [result]


def test_second_exporter_waits_until_receipt_emission_finishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    output = tmp_path / "out.json"
    first_payload = tmp_path / "first.json"
    second_payload = tmp_path / "second.json"
    first_payload.write_text("{}\n", encoding="utf-8")
    second_payload.write_text("{}\n", encoding="utf-8")
    entered = threading.Event()
    release = threading.Event()
    second_done = threading.Event()
    outcomes = {}

    def emitter(result):
        entered.set()
        assert release.wait(timeout=5)

    def first():
        exporter.run_export(
            tmp_path,
            first_payload,
            output,
            "first",
            provenance_provider=provider,
            receipt_emitter=emitter,
        )

    def second():
        try:
            exporter.run_export(
                tmp_path, second_payload, output, "second", provenance_provider=provider
            )
            outcomes["second"] = "ok"
        except exporter.ExportError as exc:
            outcomes["second"] = exc.code
        finally:
            second_done.set()

    first_thread = threading.Thread(target=first)
    first_thread.start()
    assert entered.wait(timeout=5)
    second_thread = threading.Thread(target=second)
    second_thread.start()
    time.sleep(0.1)
    assert not second_done.is_set()
    release.set()
    first_thread.join(timeout=5)
    second_thread.join(timeout=5)
    assert outcomes["second"] == "ARCH_EXPORT_OUTPUT_EXISTS"


def test_head_and_ref_drift_remain_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    for changed in (git(sha="b" * 40), git(ref="other")):
        output = tmp_path / f"{changed.ref}-{changed.commit_sha[:1]}.json"
        states = iter([git(), changed])

        def drifting_provider(root, payload_path, output_path, allowed_paths):
            return next(states)

        with pytest.raises(exporter.ExportError) as exc:
            run_unit_export(
                tmp_path,
                monkeypatch,
                f"drift-{changed.ref}-{changed.commit_sha[:1]}",
                output,
                provenance_provider=drifting_provider,
            )
        assert exc.value.code == "ARCH_EXPORT_PROVENANCE_DRIFT"
        assert not output.exists()


def test_unicode_path_and_canonical_bytes(tmp_path: Path):
    output = tmp_path / "مسیر" / "معماری.json"
    value = {"z": "معماری", "a": 1}
    exporter.atomic_write(output, value, False, root=tmp_path)
    assert output.read_bytes() == exporter.canonical_bytes(value) + b"\n"


def test_final_component_symlink_and_nonregular_rejected(tmp_path: Path):
    target = tmp_path / "target.json"
    target.write_text("target\n", encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(target)
    with pytest.raises(exporter.ExportError) as symlink_exc:
        exporter.atomic_write(link, {"value": 1}, False)
    assert symlink_exc.value.code == "ARCH_EXPORT_UNSAFE_OUTPUT_PATH"
    directory = tmp_path / "directory.json"
    directory.mkdir()
    with pytest.raises(exporter.ExportError) as directory_exc:
        exporter.atomic_write(directory, {"value": 1}, False)
    assert directory_exc.value.code == "ARCH_EXPORT_OUTPUT_PATH_TYPE_INVALID"


def test_missing_ancestry_primitives_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(exporter, "_ancestry_primitives_available", lambda: False)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(tmp_path / "out.json", {"value": 1}, False)
    assert exc.value.code == "ARCH_EXPORT_ANCESTRY_BINDING_UNSUPPORTED"
