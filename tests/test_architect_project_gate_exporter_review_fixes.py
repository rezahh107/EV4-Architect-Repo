from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter_review_fixes", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = exporter
spec.loader.exec_module(exporter)


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "ARCH-01 Tests"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "arch01@example.invalid"], check=True)
    (path / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "test fixture"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "remote", "add", "origin", "https://github.com/rezahh107/EV4-Architect-Repo.git"],
        check=True,
    )


def test_canonicalization_rejects_mixed_key_types_without_crashing():
    with pytest.raises(exporter.ExportError) as exc:
        exporter.canonical_bytes({"valid": 1, 2: "invalid"})
    assert exc.value.code == "ARCH_EXPORT_NON_STRING_KEY"


def test_non_object_payload_is_rejected_before_official_validator(tmp_path: Path):
    payload = tmp_path / "payload.json"
    payload.write_text("[]\n", encoding="utf-8")

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(tmp_path, payload, tmp_path / "output.json", "run-non-object")

    assert exc.value.code == "ARCH_EXPORT_PAYLOAD_NOT_OBJECT"


def test_unicode_run_paths_are_allowed_in_clean_repository(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    payload = repo / "معماری-ورودی.json"
    output = repo / "معماری-خروجی.json"
    payload.write_text("{}\n", encoding="utf-8")

    observed = exporter.inspect_repository(repo, payload, output)

    assert observed.repository == exporter.REPOSITORY
    assert observed.ref == "main"


def test_concurrently_created_output_is_not_deleted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    output = tmp_path / "architect-project-gate.json"
    real_link = exporter.os.link

    def concurrent_create(source, destination, **kwargs):
        Path(destination).write_text("operator-created artifact\n", encoding="utf-8")
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(exporter.os, "link", concurrent_create)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"unit": True}, overwrite=False)

    assert exc.value.code == "ARCH_EXPORT_OUTPUT_EXISTS"
    assert output.read_text(encoding="utf-8") == "operator-created artifact\n"
    assert not list(tmp_path.glob(".architect-project-gate.json.*.tmp"))
