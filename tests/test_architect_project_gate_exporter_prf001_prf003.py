from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location(
    "architect_project_gate_exporter_prf001_prf003", SCRIPT
)
exporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = exporter
spec.loader.exec_module(exporter)


def git(ref: str = "main", sha: str = "a" * 40):
    return exporter.GitProvenance(exporter.REPOSITORY, ref, sha)


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
            {
                "payload_hash": "payload",
                "bundle_hash": "bundle",
                "export_hash": run_id,
            },
        ),
    )
    monkeypatch.setattr(exporter, "validate_contracts", lambda root, value: None)
    monkeypatch.setattr(exporter, "verify_hashes", lambda value, hashes: None)


def test_detached_bound_parent_after_final_check_blocks_handoff_and_canonical_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    repo = tmp_path / "repo"
    repo.mkdir()
    parent = repo / "run"
    parent.mkdir()
    outside = tmp_path / "detached-run"
    payload = repo / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = parent / "architect-project-gate.json"
    real_link = exporter.os.link
    raced = False

    def racing_link(source, destination, *args, **kwargs):
        nonlocal raced
        if (
            destination == output.name
            and kwargs.get("dst_dir_fd") is not None
            and not raced
        ):
            raced = True
            os.rename(parent, outside)
            parent.mkdir()
        return real_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(exporter.os, "link", racing_link)
    result = exporter.run_export(
        repo,
        payload,
        output,
        "detached-parent",
        provenance_provider=lambda *args: git(),
    )

    assert result.artifact_committed is True
    assert result.handoff_allowed is False
    assert result.current_revision_accepted is False
    assert result.canonical_destination_present is False
    assert result.output_path != "run/architect-project-gate.json"
    assert result.committed_output_location == "bound_parent_outside_canonical_ancestry"
    assert (outside / output.name).exists()
    assert not (parent / output.name).exists()


def test_post_link_git_drift_blocks_exact_revision_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "architect-project-gate.json"
    drifted = False
    real_link = exporter.os.link

    def provider(root, payload_path, output_path, allowed_paths):
        return git(sha=("b" * 40 if drifted else "a" * 40))

    def racing_link(source, destination, *args, **kwargs):
        nonlocal drifted
        drifted = True
        return real_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(exporter.os, "link", racing_link)
    result = exporter.run_export(
        tmp_path,
        payload,
        output,
        "post-link-git-drift",
        provenance_provider=provider,
    )

    assert result.artifact_committed is True
    assert result.handoff_allowed is False
    assert result.current_revision_accepted is False
    assert result.canonical_destination_present is True
    assert result.output_path == output.name
    assert result.committed_output_location == "canonical_repository_destination"
    assert any(
        item.startswith("ARCH_EXPORT_POST_COMMIT_PROVENANCE_BLOCKED:")
        for item in result.acceptance_blockers
    )
    assert output.exists()


def test_output_lock_release_failure_marks_cleanup_incomplete_without_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "architect-project-gate.json"
    real_release = exporter.OutputLock.release

    def release_with_warning(self):
        real_release(self)
        return "ARCH_EXPORT_OUTPUT_LOCK_RELEASE_FAILED:Injected"

    monkeypatch.setattr(exporter.OutputLock, "release", release_with_warning)
    result = exporter.run_export(
        tmp_path,
        payload,
        output,
        "lock-release-warning",
        provenance_provider=lambda *args: git(),
    )

    assert result.artifact_committed is True
    assert result.cleanup_complete is False
    assert result.result_status == "SUCCESS_WITH_CLEANUP_WARNING"
    assert "ARCH_EXPORT_OUTPUT_LOCK_RELEASE_FAILED:Injected" in result.cleanup_warnings
    assert output.exists()
