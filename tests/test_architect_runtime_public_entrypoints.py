from __future__ import annotations

import copy
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


def _write_root(tmp_path: Path, *, marker: str = "A") -> tuple[Path, dict]:
    root = tmp_path / f"root-{marker}"
    scripts = root / "scripts"
    data = root / "data"
    scripts.mkdir(parents=True)
    data.mkdir()
    (data / "authority.json").write_text("{}", encoding="utf-8")
    (scripts / "shared_runtime.py").write_text(
        "RUNTIME_INTERFACE_ID = 'ev4-architect-quality-runtime@2.0.0'\n"
        "class RunContext: pass\n"
        "def evaluate_run(): return %r\n" % marker,
        encoding="utf-8",
    )
    (scripts / "architect_quality_runtime.py").write_text(
        "from shared_runtime import *\nEXTRA_EXPORT = 'allowed'\n",
        encoding="utf-8",
    )
    (scripts / "architect_runtime_payload_assembler.py").write_text(
        "def assemble_architect_stage_payload(): return 'payload'\n"
        "EXTRA_EXPORT = True\n",
        encoding="utf-8",
    )
    (scripts / "architect_runtime_project_gate.py").write_text(
        "def validate_payload(): return 'valid'\n"
        "def validate_contracts(): return 'valid'\n",
        encoding="utf-8",
    )
    document = {
        "manifest_id": authority.MANIFEST_ID,
        "manifest_version": authority.MANIFEST_VERSION,
        "owner_repository": authority.OWNER_REPOSITORY,
        "runtime_interface_id": authority.RUNTIME_INTERFACE_ID,
        "public_entry_points": [
            {
                "path": "scripts/architect_quality_runtime.py",
                "symbols": ["RUNTIME_INTERFACE_ID", "RunContext", "evaluate_run"],
            },
            {
                "path": "scripts/architect_runtime_payload_assembler.py",
                "symbols": ["assemble_architect_stage_payload"],
            },
            {
                "path": "scripts/architect_runtime_project_gate.py",
                "symbols": ["validate_contracts", "validate_payload"],
            },
        ],
        "python_authority_paths": sorted(
            [
                "scripts/architect_quality_runtime.py",
                "scripts/architect_runtime_payload_assembler.py",
                "scripts/architect_runtime_project_gate.py",
                "scripts/shared_runtime.py",
            ]
        ),
        "data_authority_paths": ["data/authority.json"],
    }
    return root, document


def test_all_entrypoints_use_independent_exact_processes(tmp_path: Path) -> None:
    root, document = _write_root(tmp_path)
    results = authority.probe_manifest_entrypoints(document, root)
    assert len(results) == len(document["public_entry_points"])
    assert len({item["process_id"] for item in results}) == len(results)
    assert [item["entrypoint_path"] for item in results] == [
        item["path"] for item in document["public_entry_points"]
    ]
    assert all(item["executed_file"] == item["entrypoint_path"] for item in results)
    assert all(item["missing_symbols"] == [] for item in results)
    assert all(item["status"] == "valid" for item in results)


def test_additional_exports_are_allowed(tmp_path: Path) -> None:
    root, document = _write_root(tmp_path)
    authority.validate_manifest_document(document, root)


def test_parent_module_cache_cannot_substitute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, document = _write_root(tmp_path)
    fake = type(sys)("shared_runtime")
    fake.RUNTIME_INTERFACE_ID = "wrong"
    monkeypatch.setitem(sys.modules, "shared_runtime", fake)
    authority.validate_manifest_document(document, root)


@pytest.mark.parametrize("entry_index", [0, 1, 2])
def test_missing_symbol_fails_for_every_entrypoint(
    tmp_path: Path, entry_index: int
) -> None:
    root, document = _write_root(tmp_path)
    mutated = copy.deepcopy(document)
    mutated["public_entry_points"][entry_index]["symbols"].append("ZZZ_MISSING")
    mutated["public_entry_points"][entry_index]["symbols"].sort()
    with pytest.raises(
        authority.RuntimeAuthorityManifestError,
        match="ENTRYPOINT_SYMBOL_MISSING",
    ):
        authority.validate_manifest_document(mutated, root)


def test_broken_wrapper_fails_with_healthy_package(tmp_path: Path) -> None:
    root, document = _write_root(tmp_path)
    (root / "scripts/architect_quality_runtime.py").write_text(
        "from shared_runtime import RUNTIME_INTERFACE_ID\n",
        encoding="utf-8",
    )
    with pytest.raises(
        authority.RuntimeAuthorityManifestError,
        match="ENTRYPOINT_SYMBOL_MISSING",
    ):
        authority.validate_manifest_document(document, root)


def test_wrong_entrypoint_file_fails(tmp_path: Path) -> None:
    root, document = _write_root(tmp_path)
    mutated = copy.deepcopy(document)
    mutated["public_entry_points"][1]["path"] = "scripts/shared_runtime.py"
    mutated["public_entry_points"].sort(key=lambda item: item["path"])
    with pytest.raises(
        authority.RuntimeAuthorityManifestError,
        match="ENTRYPOINT_SYMBOL_MISSING",
    ):
        authority.validate_manifest_document(mutated, root)


def test_interface_identity_drift_fails(tmp_path: Path) -> None:
    root, document = _write_root(tmp_path)
    (root / "scripts/shared_runtime.py").write_text(
        "RUNTIME_INTERFACE_ID = 'drift'\n"
        "class RunContext: pass\n"
        "def evaluate_run(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(
        authority.RuntimeAuthorityManifestError,
        match="INTERFACE_ID_MISMATCH",
    ):
        authority.validate_manifest_document(document, root)


def test_undeclared_repository_module_fails(tmp_path: Path) -> None:
    root, document = _write_root(tmp_path)
    (root / "scripts/extra.py").write_text("VALUE = 1\n", encoding="utf-8")
    wrapper = root / "scripts/architect_runtime_project_gate.py"
    wrapper.write_text(
        "import extra\n"
        "def validate_payload(): pass\n"
        "def validate_contracts(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(
        authority.RuntimeAuthorityManifestError,
        match="CLOSURE_UNDECLARED",
    ):
        authority.validate_manifest_document(document, root)


@pytest.mark.parametrize(
    "completed, code",
    [
        (
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            "RESULT_MISSING",
        ),
        (
            subprocess.CompletedProcess([], 0, stdout="not-json", stderr=""),
            "RESULT_MALFORMED",
        ),
        (
            subprocess.CompletedProcess([], 7, stdout="", stderr="failure"),
            "LOAD_FAILED",
        ),
        (
            subprocess.CompletedProcess(
                [], 0, stdout=json.dumps({"status": "valid"}), stderr=""
            ),
            "RESULT_MALFORMED",
        ),
        (
            subprocess.CompletedProcess(
                [],
                0,
                stdout=json.dumps(
                    {
                        "status": "valid",
                        "entrypoint_path": "scripts/architect_quality_runtime.py",
                        "executed_file": "scripts/wrong.py",
                        "missing_symbols": [],
                        "loaded_repository_python_paths": [],
                        "process_id": 1,
                    }
                ),
                stderr="",
            ),
            "PATH_MISMATCH",
        ),
    ],
)
def test_malformed_child_protocol_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    completed: subprocess.CompletedProcess,
    code: str,
) -> None:
    root, document = _write_root(tmp_path)
    monkeypatch.setattr(
        authority.subprocess,
        "run",
        lambda *args, **kwargs: completed,
    )
    with pytest.raises(authority.RuntimeAuthorityManifestError, match=code):
        authority.probe_manifest_entrypoints(document, root)


def test_probe_timeout_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, document = _write_root(tmp_path)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=1)

    monkeypatch.setattr(authority.subprocess, "run", timeout)
    with pytest.raises(
        authority.RuntimeAuthorityManifestError,
        match="PROBE_TIMEOUT",
    ):
        authority.probe_manifest_entrypoints(document, root, timeout_seconds=1)


def test_sequential_roots_do_not_reuse_modules(tmp_path: Path) -> None:
    root_a, document_a = _write_root(tmp_path, marker="A")
    root_b, document_b = _write_root(tmp_path, marker="B")
    result_a = authority.probe_manifest_entrypoints(document_a, root_a)[0]
    result_b = authority.probe_manifest_entrypoints(document_b, root_b)[0]
    assert result_a["process_id"] != result_b["process_id"]
    assert result_a["executed_file"] == "scripts/architect_quality_runtime.py"
    assert result_b["executed_file"] == "scripts/architect_quality_runtime.py"
