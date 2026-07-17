from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter_prf004_race", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = exporter
spec.loader.exec_module(exporter)


def git():
    return exporter.GitProvenance(exporter.REPOSITORY, "main", "a" * 40)


def provider(root, payload_path, output_path, allowed_paths):
    return git()


def fake_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(exporter, "validate_payload", lambda root, value: {"status": "valid"})
    monkeypatch.setattr(
        exporter,
        "build_export",
        lambda value, provenance, run_id, input_ref: (
            {
                "handoff": {"status": "successful", "allowed": True},
                "export_id": "unit-export-open-race",
                "producer": {"commit_sha": provenance.commit_sha},
            },
            {"payload_hash": "payload", "bundle_hash": "bundle", "export_hash": "open-race"},
        ),
    )
    monkeypatch.setattr(exporter, "validate_contracts", lambda root, value: None)
    monkeypatch.setattr(exporter, "verify_hashes", lambda value, hashes: None)


def test_link_to_descriptor_open_race_blocks_handoff_and_preserves_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    external = tmp_path / "external.json"
    external.write_text('{"external":true}\n', encoding="utf-8")
    real_open = exporter.os.open
    raced = False

    def racing_open(path, flags, *args, **kwargs):
        nonlocal raced
        if (
            path == output.name
            and kwargs.get("dir_fd") is not None
            and flags & os.O_RDONLY == os.O_RDONLY
            and not raced
        ):
            raced = True
            os.replace(external, output)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(exporter.os, "open", racing_open)
    result = exporter.run_export(
        tmp_path,
        payload,
        output,
        "open-race",
        provenance_provider=provider,
    )
    assert result.artifact_committed is True
    assert result.output_committed is True
    assert result.handoff_allowed is False
    assert result.current_revision_accepted is False
    assert result.canonical_destination_present is False
    assert result.current_destination_claim is False
    assert result.output_path == ""
    assert result.result_status == "COMMITTED_HANDOFF_BLOCKED_WITH_WARNINGS"
    assert (
        "ARCH_EXPORT_POST_COMMIT_OBSERVATION_WARNING:ARCH_EXPORT_PUBLICATION_IDENTITY_MISMATCH"
        in result.cleanup_warnings
    )
    assert any(
        item.startswith("ARCH_EXPORT_POST_COMMIT_PUBLICATION_BLOCKED:")
        for item in result.acceptance_blockers
    )
    assert output.read_text(encoding="utf-8") == '{"external":true}\n'


def test_parent_rename_and_symlink_before_operational_commit_emits_no_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    repo = tmp_path / "repo"
    repo.mkdir()
    parent = repo / "run"
    parent.mkdir()
    outside = tmp_path / "outside"
    payload = repo / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
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
        exporter.run_export(
            repo,
            payload,
            output,
            "ancestry-race",
            provenance_provider=drifting_provider,
            receipt_emitter=receipts.append,
        )
    assert exc.value.code == "ARCH_EXPORT_OUTPUT_ANCESTRY_DRIFT"
    assert exc.value.output_committed is False
    assert receipts == []
    assert not (outside / "out.json").exists()
