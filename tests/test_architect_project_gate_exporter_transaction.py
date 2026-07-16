from __future__ import annotations

import importlib.util
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter_transaction", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
import sys
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
                "export_id": "unit-export",
                "producer": {"commit_sha": provenance.commit_sha},
            },
            {"payload_hash": "payload", "bundle_hash": "bundle", "export_hash": "export"},
        ),
    )
    monkeypatch.setattr(exporter, "validate_contracts", lambda root, value: None)
    monkeypatch.setattr(exporter, "verify_hashes", lambda value, hashes: None)


def git(ref: str = "main", sha: str = "a" * 40):
    return exporter.GitProvenance(exporter.REPOSITORY, ref, sha)


def leftovers(path: Path) -> list[str]:
    return [item.name for item in path.iterdir() if item.name.endswith((".tmp", ".bak"))]


def test_atomic_no_clobber_race_preserves_operator_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    output = tmp_path / "out.json"
    real_link = exporter.os.link

    def racing_link(source, destination, **kwargs):
        Path(destination).write_bytes(b"operator-created\n")
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(exporter.os, "link", racing_link)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.atomic_write(output, {"a": 1}, overwrite=False)

    assert exc.value.code == "ARCH_EXPORT_OUTPUT_EXISTS"
    assert exc.value.output_written is False
    assert output.read_bytes() == b"operator-created\n"
    assert leftovers(tmp_path) == []


def test_two_publishers_one_wins_without_clobber(tmp_path: Path):
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
    assert leftovers(tmp_path) == []


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

    def provider(root, payload_path, output_path, allowed_paths):
        return next(states)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(tmp_path, payload, output, "run", provenance_provider=provider)

    assert exc.value.code == "ARCH_EXPORT_PROVENANCE_DRIFT"
    assert changed_field in exc.value.reason
    assert not output.exists()
    assert leftovers(tmp_path) == []


def test_tracked_contract_drift_before_publication_writes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    calls = 0

    def provider(root, payload_path, output_path, allowed_paths):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise exporter.ExportError("ARCH_EXPORT_DIRTY_WORKTREE", "git_provenance", "tracked contract changed", "operator")
        return git()

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(tmp_path, payload, output, "run", provenance_provider=provider)

    assert exc.value.code == "ARCH_EXPORT_DIRTY_WORKTREE"
    assert not output.exists()
    assert leftovers(tmp_path) == []


def test_final_provenance_drift_removes_new_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    states = iter([git(), git(), git(sha="b" * 40)])

    def provider(root, payload_path, output_path, allowed_paths):
        return next(states)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(tmp_path, payload, output, "run", provenance_provider=provider)

    assert exc.value.code == "ARCH_EXPORT_PROVENANCE_DRIFT"
    assert not output.exists()
    assert leftovers(tmp_path) == []


def test_overwrite_restores_previous_output_on_final_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    output.write_bytes(b"previous-output\n")
    states = iter([git(), git(), git(ref="other")])

    def provider(root, payload_path, output_path, allowed_paths):
        return next(states)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(tmp_path, payload, output, "run", overwrite=True, provenance_provider=provider)

    assert exc.value.code == "ARCH_EXPORT_PROVENANCE_DRIFT"
    assert output.read_bytes() == b"previous-output\n"
    assert leftovers(tmp_path) == []


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
            raise exporter.ExportError("TEST_POSTWRITE_FAILURE", "post_write_validation", "fail", "repository_owner")

    monkeypatch.setattr(exporter, "validate_contracts", validate)

    def provider(root, payload_path, output_path, allowed_paths):
        return git()

    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(tmp_path, payload, output, "run", overwrite=True, provenance_provider=provider)

    assert exc.value.code == "TEST_POSTWRITE_FAILURE"
    assert output.read_bytes() == b"previous-output\n"
    assert leftovers(tmp_path) == []


def test_backup_cleanup_retry_does_not_invalidate_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "out.json"
    output.write_bytes(b"previous-output\n")
    original_unlink = Path.unlink
    backup_unlinks = 0

    def flaky_unlink(self, *args, **kwargs):
        nonlocal backup_unlinks
        if self.name.endswith(".bak"):
            backup_unlinks += 1
            if backup_unlinks == 2:
                raise OSError("interrupted cleanup")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", flaky_unlink)

    def provider(root, payload_path, output_path, allowed_paths):
        return git()

    result = exporter.run_export(tmp_path, payload, output, "run", overwrite=True, provenance_provider=provider)

    assert result.output_written is True
    assert output.read_bytes() != b"previous-output\n"
    assert leftovers(tmp_path) == []


def test_existing_symlink_is_rejected(tmp_path: Path):
    target = tmp_path / "target.json"
    target.write_text("target\n", encoding="utf-8")
    link = tmp_path / "out.json"
    link.symlink_to(target)

    with pytest.raises(exporter.ExportError) as exc:
        exporter.inside(tmp_path, link)

    assert exc.value.code == "ARCH_EXPORT_UNSAFE_OUTPUT_PATH"
