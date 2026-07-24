"""Bounded functional dependency declaration for Architect Runtime v2."""
from __future__ import annotations

import importlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

MANIFEST_PATH = Path("manifests/architect-runtime-authority-manifest.v1.json")
MANIFEST_ID = "ev4-architect-runtime-authority-manifest"
MANIFEST_VERSION = "1.0.0"
OWNER_REPOSITORY = "rezahh107/EV4-Architect-Repo"
RUNTIME_INTERFACE_ID = "ev4-architect-quality-runtime@2.0.0"
REQUIRED_PUBLIC_SYMBOLS = (
    "RunContext",
    "RuntimeSession",
    "SessionProjection",
    "SubprocessGitProvider",
    "resume_run",
    "evaluate_run",
    "evaluate_stage",
    "apply_partial_rerun",
    "validate_stage_result",
    "load_authority",
    "initial_run_state",
)


class RuntimeAuthorityManifestError(ValueError):
    pass


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeAuthorityManifestError(
            f"RUNTIME_AUTHORITY_MANIFEST_INVALID: {type(exc).__name__}: {exc}"
        ) from exc


def _path_list(document: dict[str, Any], key: str) -> list[str]:
    values = document.get(key)
    if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
        raise RuntimeAuthorityManifestError(f"{key} must be an array of strings")
    if values != sorted(values):
        raise RuntimeAuthorityManifestError(f"{key} must be sorted")
    if len(values) != len(set(values)):
        raise RuntimeAuthorityManifestError(f"{key} must contain unique paths")
    return values


def _validate_relative_path(value: str, key: str) -> None:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or str(path) != value:
        raise RuntimeAuthorityManifestError(
            f"{key} contains a non-canonical repository-relative path: {value!r}"
        )


def validate_manifest_document(
    document: Any,
    root: Path,
    *,
    observed_python_paths: Iterable[str] | None = None,
    observed_data_paths: Iterable[str] | None = None,
    check_public_symbols: bool = True,
) -> dict[str, Any]:
    root = Path(root).resolve()
    if not isinstance(document, dict):
        raise RuntimeAuthorityManifestError("Runtime authority manifest must be an object")
    expected = {
        "manifest_id": MANIFEST_ID,
        "manifest_version": MANIFEST_VERSION,
        "owner_repository": OWNER_REPOSITORY,
        "runtime_interface_id": RUNTIME_INTERFACE_ID,
    }
    for key, value in expected.items():
        if document.get(key) != value:
            raise RuntimeAuthorityManifestError(f"{key} mismatch")

    python_paths = _path_list(document, "python_authority_paths")
    data_paths = _path_list(document, "data_authority_paths")
    for key, paths in (
        ("python_authority_paths", python_paths),
        ("data_authority_paths", data_paths),
    ):
        for value in paths:
            _validate_relative_path(value, key)
            resolved = root / value
            if not resolved.is_file():
                raise RuntimeAuthorityManifestError(f"Declared authority path is missing: {value}")

    entries = document.get("public_entry_points")
    if not isinstance(entries, list) or not entries:
        raise RuntimeAuthorityManifestError("public_entry_points must be a non-empty array")
    entry_paths: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise RuntimeAuthorityManifestError(f"public_entry_points[{index}] must be an object")
        path = entry.get("path")
        symbols = entry.get("symbols")
        if not isinstance(path, str):
            raise RuntimeAuthorityManifestError(f"public_entry_points[{index}].path is invalid")
        _validate_relative_path(path, "public_entry_points")
        if path not in python_paths:
            raise RuntimeAuthorityManifestError(f"Public entry point is not declared: {path}")
        if (
            not isinstance(symbols, list)
            or not symbols
            or any(not isinstance(item, str) or not item for item in symbols)
            or symbols != sorted(symbols)
            or len(symbols) != len(set(symbols))
        ):
            raise RuntimeAuthorityManifestError(
                f"public_entry_points[{index}].symbols must be sorted unique strings"
            )
        entry_paths.append(path)
    if entry_paths != sorted(entry_paths) or len(entry_paths) != len(set(entry_paths)):
        raise RuntimeAuthorityManifestError("public_entry_points must be sorted and unique")

    if check_public_symbols:
        runtime = importlib.import_module("architect_quality_runtime")
        if getattr(runtime, "RUNTIME_INTERFACE_ID", None) != RUNTIME_INTERFACE_ID:
            raise RuntimeAuthorityManifestError("Runtime interface identity mismatch")
        missing = [name for name in REQUIRED_PUBLIC_SYMBOLS if not hasattr(runtime, name)]
        if missing:
            raise RuntimeAuthorityManifestError(
                f"Runtime public symbols are missing: {sorted(missing)}"
            )

    if observed_python_paths is not None:
        observed = set(observed_python_paths)
        declared = set(python_paths)
        undeclared = sorted(observed - declared)
        public_shims = set(entry_paths)
        stale = sorted(declared - observed - public_shims)
        if undeclared or stale:
            raise RuntimeAuthorityManifestError(
                "Runtime Python closure mismatch: "
                f"undeclared={undeclared}, stale={stale}"
            )

    if observed_data_paths is not None:
        observed = set(observed_data_paths)
        declared = set(data_paths)
        missing = sorted(observed - declared)
        stale = sorted(declared - observed)
        if missing or stale:
            raise RuntimeAuthorityManifestError(
                "Runtime data closure mismatch: "
                f"undeclared={missing}, stale={stale}"
            )
    return document


def load_runtime_authority_manifest(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    document = _load_json(root / MANIFEST_PATH)
    return validate_manifest_document(document, root)


__all__ = [
    "MANIFEST_PATH",
    "RUNTIME_INTERFACE_ID",
    "REQUIRED_PUBLIC_SYMBOLS",
    "RuntimeAuthorityManifestError",
    "load_runtime_authority_manifest",
    "validate_manifest_document",
]
