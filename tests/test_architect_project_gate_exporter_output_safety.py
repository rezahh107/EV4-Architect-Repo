from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter_output_safety", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = exporter
spec.loader.exec_module(exporter)


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "ARCH-01 Tests"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "arch01@example.invalid"], check=True)
    (path / "tracked-output.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "tracked-output.json"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "test fixture"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "remote", "add", "origin", "https://github.com/rezahh107/EV4-Architect-Repo.git"],
        check=True,
    )


def test_output_cannot_target_git_metadata(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    with pytest.raises(exporter.ExportError) as exc:
        exporter.inside(repo, repo / ".git/config")
    assert exc.value.code == "ARCH_EXPORT_UNSAFE_OUTPUT_PATH"


def test_output_cannot_escape_repository_lexically(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(exporter.ExportError) as exc:
        exporter.inside(repo, repo / ".." / "outside.json")
    assert exc.value.code == "ARCH_EXPORT_UNSAFE_OUTPUT_PATH"


def test_output_cannot_replace_source_payload(tmp_path: Path):
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(tmp_path, payload, payload, "run-collision")
    assert exc.value.code == "ARCH_EXPORT_INPUT_OUTPUT_COLLISION"


def test_output_cannot_replace_tracked_repository_file(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    payload = repo / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.inspect_repository(repo, payload, repo / "tracked-output.json")
    assert exc.value.code == "ARCH_EXPORT_TRACKED_OUTPUT_FORBIDDEN"


def test_intermediate_symlink_cannot_redirect_output_outside_repository(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / "nested").symlink_to(outside, target_is_directory=True)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(repo / "nested" / "out.json", {"value": 1}, False, root=repo)
    assert exc.value.code in {
        "ARCH_EXPORT_OUTPUT_ANCESTRY_UNSAFE",
        "ARCH_EXPORT_OUTPUT_ANCESTRY_INSPECTION_FAILED",
    }
    assert not (outside / "out.json").exists()


def test_parent_descriptor_is_bound_to_repository_chain(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    parent = repo / "nested"
    parent.mkdir()
    transaction = exporter.OutputTransaction.stage(
        parent / "out.json", {"value": 1}, False, root=repo
    )
    moved = tmp_path / "moved"
    try:
        os.rename(parent, moved)
        parent.symlink_to(moved, target_is_directory=True)
        with pytest.raises(exporter.ExportError) as exc:
            transaction.ancestry.verify("test_parent_binding")
        assert exc.value.code == "ARCH_EXPORT_OUTPUT_ANCESTRY_DRIFT"
    finally:
        transaction.close()
