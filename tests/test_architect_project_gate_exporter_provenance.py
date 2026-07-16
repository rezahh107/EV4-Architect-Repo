from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter_provenance", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = exporter
spec.loader.exec_module(exporter)


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "ARCH-01 Tests"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "arch01@example.invalid"], check=True)
    (path / "architect-stage-payload.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "architect-stage-payload.json"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "test fixture"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "remote", "add", "origin", "https://github.com/rezahh107/EV4-Architect-Repo.git"],
        check=True,
    )


def test_tracked_payload_modified_in_place_is_dirty_provenance(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    payload = repo / "architect-stage-payload.json"
    payload.write_text('{"changed":true}\n', encoding="utf-8")

    with pytest.raises(exporter.ExportError) as exc:
        exporter.inspect_repository(repo, payload, repo / "architect-project-gate.json")

    assert exc.value.code == "ARCH_EXPORT_DIRTY_WORKTREE"


def test_error_report_preserves_output_written_state():
    error = exporter.ExportError(
        "ARCH_EXPORT_POSTWRITE_CLEANUP_FAILED",
        "post_write_validation",
        "invalid output could not be removed",
        "operator",
        output_written=True,
    )
    assert error.report()["output_written"] is True
