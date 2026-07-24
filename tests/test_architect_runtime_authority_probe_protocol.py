from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import architect_runtime_authority_manifest as authority


def _write_root(tmp_path: Path) -> tuple[Path, dict]:
    root = tmp_path / "root"
    scripts = root / "scripts"
    data = root / "data"
    scripts.mkdir(parents=True)
    data.mkdir()
    (scripts / "entry.py").write_text("SYMBOL = 1\n", encoding="utf-8")
    (data / "authority.json").write_text("{}", encoding="utf-8")
    document = {
        "manifest_id": authority.MANIFEST_ID,
        "manifest_version": authority.MANIFEST_VERSION,
        "owner_repository": authority.OWNER_REPOSITORY,
        "runtime_interface_id": authority.RUNTIME_INTERFACE_ID,
        "public_entry_points": [
            {
                "path": "scripts/entry.py",
                "symbols": ["SYMBOL"],
            }
        ],
        "python_authority_paths": ["scripts/entry.py"],
        "data_authority_paths": ["data/authority.json"],
    }
    return root, document


def _completed_result(paths: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        [],
        0,
        stdout=json.dumps(
            {
                "status": "valid",
                "entrypoint_path": "scripts/entry.py",
                "executed_file": "scripts/entry.py",
                "missing_symbols": [],
                "loaded_repository_python_paths": paths,
                "process_id": 1234,
            }
        ),
        stderr="",
    )


def _execute_child_probe(
    monkeypatch: pytest.MonkeyPatch,
    request: dict,
) -> dict:
    stdin = io.StringIO(json.dumps(request))
    stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(
        sys,
        "dont_write_bytecode",
        sys.dont_write_bytecode,
    )
    with pytest.raises(SystemExit) as exc_info:
        exec(authority._CHILD_ENTRYPOINT_PROBE, {})
    assert exc_info.value.code == 0
    return json.loads(stdout.getvalue())


def _child_request(root: Path, document: dict) -> dict:
    entry = document["public_entry_points"][0]
    return {
        "root": str(root),
        "entrypoint_path": entry["path"],
        "declared_symbols": entry["symbols"],
        "runtime_interface_id": document["runtime_interface_id"],
        "declared_python_authority_paths": (
            document["python_authority_paths"]
        ),
    }


def test_manifest_symbols_fully_own_interface_exports(tmp_path: Path) -> None:
    root, document = _write_root(tmp_path)
    assert authority.validate_manifest_document(document, root) is document


def test_authority_path_resolution_cannot_escape_repository(
    tmp_path: Path,
) -> None:
    root, _ = _write_root(tmp_path)
    (tmp_path / "outside.py").write_text("SYMBOL = 1\n", encoding="utf-8")
    with pytest.raises(
        authority.RuntimeAuthorityManifestError,
        match="RUNTIME_AUTHORITY_PATH_UNOWNED",
    ):
        authority._native_repository_path(root, "../outside.py")


def test_child_rejects_resolved_entrypoint_outside_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, document = _write_root(tmp_path)
    (tmp_path / "outside.py").write_text("SYMBOL = 1\n", encoding="utf-8")
    document["public_entry_points"][0]["path"] = "../outside.py"
    result = _execute_child_probe(
        monkeypatch,
        _child_request(root, document),
    )
    assert result["status"] == "invalid"
    assert result["error_code"] == (
        "RUNTIME_AUTHORITY_ENTRYPOINT_PATH_UNOWNED"
    )


def test_parent_rejects_mocked_symlink_before_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, document = _write_root(tmp_path)
    target = (root / "scripts/entry.py").resolve()
    real_is_symlink = Path.is_symlink

    def mocked_is_symlink(path: Path) -> bool:
        return path == target or real_is_symlink(path)

    def unexpected_subprocess(*args, **kwargs):
        pytest.fail("unowned entrypoint started a subprocess")

    monkeypatch.setattr(Path, "is_symlink", mocked_is_symlink)
    monkeypatch.setattr(authority.subprocess, "run", unexpected_subprocess)
    with pytest.raises(
        authority.RuntimeAuthorityManifestError,
        match="RUNTIME_AUTHORITY_ENTRYPOINT_PATH_UNOWNED",
    ):
        authority.probe_manifest_entrypoints(document, root)


def test_child_rejects_mocked_symlink_component(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, document = _write_root(tmp_path)
    target = (root / "scripts/entry.py").resolve()
    real_is_symlink = Path.is_symlink

    def mocked_is_symlink(path: Path) -> bool:
        return path == target or real_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", mocked_is_symlink)
    result = _execute_child_probe(
        monkeypatch,
        _child_request(root, document),
    )
    assert result["status"] == "invalid"
    assert result["error_code"] == (
        "RUNTIME_AUTHORITY_ENTRYPOINT_PATH_UNOWNED"
    )


@pytest.mark.parametrize(
    "reported_paths",
    [
        "scripts/entry.py",
        [1],
        ["scripts/entry.py", "scripts/entry.py"],
        ["scripts/z.py", "scripts/entry.py"],
        ["scripts/../entry.py"],
        ["scripts\\entry.py"],
        ["scripts/data.json"],
    ],
)
def test_parent_rejects_malformed_reported_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reported_paths: object,
) -> None:
    root, document = _write_root(tmp_path)
    monkeypatch.setattr(
        authority.subprocess,
        "run",
        lambda *args, **kwargs: _completed_result(reported_paths),
    )
    with pytest.raises(
        authority.RuntimeAuthorityManifestError,
        match="ENTRYPOINT_RESULT_MALFORMED",
    ):
        authority.probe_manifest_entrypoints(document, root)


def test_parent_rejects_reported_undeclared_repository_module(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, document = _write_root(tmp_path)
    monkeypatch.setattr(
        authority.subprocess,
        "run",
        lambda *args, **kwargs: _completed_result(
            ["scripts/entry.py", "scripts/extra.py"]
        ),
    )
    with pytest.raises(
        authority.RuntimeAuthorityManifestError,
        match="ENTRYPOINT_CLOSURE_UNDECLARED",
    ):
        authority.probe_manifest_entrypoints(document, root)


def test_parent_accepts_canonical_declared_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, document = _write_root(tmp_path)
    monkeypatch.setattr(
        authority.subprocess,
        "run",
        lambda *args, **kwargs: _completed_result(["scripts/entry.py"]),
    )
    results = authority.probe_manifest_entrypoints(document, root)
    assert results[0]["loaded_repository_python_paths"] == ["scripts/entry.py"]
