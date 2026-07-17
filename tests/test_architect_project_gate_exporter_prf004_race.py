from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter_prf004_race", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = exporter
spec.loader.exec_module(exporter)


def git():
    return exporter.GitProvenance(exporter.REPOSITORY, "main", "a" * 40)


def provider(root, payload_path, output_path, allowed_paths):
    return git()


def test_link_to_descriptor_open_race_preserves_concurrent_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
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

    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    external = tmp_path / "external.json"
    external.write_text('{"external":true}\n', encoding="utf-8")
    real_open = exporter.os.open
    raced = False

    def racing_open(path, flags, *args, **kwargs):
        nonlocal raced
        if Path(path) == output and not raced:
            raced = True
            os.replace(external, output)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(exporter.os, "open", racing_open)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(
            tmp_path,
            payload,
            output,
            "open-race",
            provenance_provider=provider,
        )

    assert exc.value.code == "ARCH_EXPORT_PUBLICATION_IDENTITY_MISMATCH"
    assert exc.value.output_written is False
    assert exc.value.concurrent_destination_preserved is True
    assert output.read_text(encoding="utf-8") == '{"external":true}\n'
