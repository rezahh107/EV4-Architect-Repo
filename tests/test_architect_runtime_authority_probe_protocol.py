from __future__ import annotations

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


def test_manifest_symbols_fully_own_interface_exports(tmp_path: Path) -> None:
    root, document = _write_root(tmp_path)
    assert authority.validate_manifest_document(document, root) is document


@pytest.mark.parametrize(
    "reported_paths",
    [
        "scripts/entry.py",
        [1],
        ["scripts/entry.py", "scripts/entry.py"],
        ["scripts/z.py", "scripts/entry.py"],
        ["scripts/../entry.py"],
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
