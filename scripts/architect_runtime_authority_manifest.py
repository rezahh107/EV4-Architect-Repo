"""Bounded functional dependency declaration for Architect Runtime v2."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Any, Iterable

MANIFEST_PATH = Path("manifests/architect-runtime-authority-manifest.v1.json")
MANIFEST_ID = "ev4-architect-runtime-authority-manifest"
MANIFEST_VERSION = "1.0.0"
OWNER_REPOSITORY = "rezahh107/EV4-Architect-Repo"
RUNTIME_INTERFACE_ID = "ev4-architect-quality-runtime@2.0.0"
DEFAULT_ENTRYPOINT_PROBE_TIMEOUT_SECONDS = 20.0


class RuntimeAuthorityManifestError(ValueError):
    pass


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeAuthorityManifestError(
            f"RUNTIME_AUTHORITY_MANIFEST_INVALID: {type(exc).__name__}: {exc}"
        ) from exc


def _compat_required_public_symbols() -> tuple[str, ...]:
    """Preserve the legacy name while deriving its value from the manifest."""
    try:
        document = _load_json(Path(__file__).resolve().parents[1] / MANIFEST_PATH)
    except RuntimeAuthorityManifestError:
        return ()
    entries = document.get("public_entry_points") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        return ()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        symbols = entry.get("symbols")
        if isinstance(symbols, list) and "RUNTIME_INTERFACE_ID" in symbols:
            return tuple(item for item in symbols if isinstance(item, str))
    return ()


REQUIRED_PUBLIC_SYMBOLS = _compat_required_public_symbols()


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


def _native_repository_path(root: Path, repository_path: str) -> Path:
    return (root / Path(*PurePosixPath(repository_path).parts)).resolve()


_CHILD_ENTRYPOINT_PROBE = r'''
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import sys

sys.dont_write_bytecode = True


def emit(value):
    sys.stdout.write(json.dumps(value, sort_keys=True) + "\n")
    sys.stdout.flush()


try:
    request = json.load(sys.stdin)
    root = Path(request["root"]).resolve()
    entrypoint_path = request["entrypoint_path"]
    declared_symbols = request["declared_symbols"]
    runtime_interface_id = request["runtime_interface_id"]
    declared_python_paths = set(request["declared_python_authority_paths"])
    expected = (root / Path(*PurePosixPath(entrypoint_path).parts)).resolve()
    scripts = (root / "scripts").resolve()
    sys.path.insert(0, str(scripts))
    synthetic_name = "_ev4_public_entrypoint_probe_" + hashlib.sha256(
        (str(root) + "\0" + entrypoint_path).encode("utf-8")
    ).hexdigest()
    spec = importlib.util.spec_from_file_location(synthetic_name, expected)
    if spec is None or spec.loader is None:
        raise ImportError("entrypoint module spec is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[synthetic_name] = module
    spec.loader.exec_module(module)
    executed = Path(module.__file__).resolve()
    if executed != expected:
        emit({
            "status": "invalid",
            "entrypoint_path": entrypoint_path,
            "executed_file": executed.as_posix(),
            "missing_symbols": [],
            "loaded_repository_python_paths": [],
            "process_id": os.getpid(),
            "error_code": "RUNTIME_AUTHORITY_ENTRYPOINT_PATH_MISMATCH",
            "error_type": "PathMismatch",
            "message": "Executed module path differs from the manifest entrypoint path",
        })
        raise SystemExit(0)
    missing = [name for name in declared_symbols if not hasattr(module, name)]
    if missing:
        emit({
            "status": "invalid",
            "entrypoint_path": entrypoint_path,
            "executed_file": entrypoint_path,
            "missing_symbols": missing,
            "loaded_repository_python_paths": [],
            "process_id": os.getpid(),
            "error_code": "RUNTIME_AUTHORITY_ENTRYPOINT_SYMBOL_MISSING",
            "error_type": "MissingSymbol",
            "message": "Manifest-declared entrypoint symbols are missing",
        })
        raise SystemExit(0)
    if "RUNTIME_INTERFACE_ID" in declared_symbols and getattr(module, "RUNTIME_INTERFACE_ID") != runtime_interface_id:
        emit({
            "status": "invalid",
            "entrypoint_path": entrypoint_path,
            "executed_file": entrypoint_path,
            "missing_symbols": [],
            "loaded_repository_python_paths": [],
            "process_id": os.getpid(),
            "error_code": "RUNTIME_AUTHORITY_INTERFACE_ID_MISMATCH",
            "error_type": "InterfaceIdentityMismatch",
            "message": "Manifest-declared Runtime interface identity differs",
        })
        raise SystemExit(0)
    observed = set()
    for loaded in tuple(sys.modules.values()):
        raw = getattr(loaded, "__file__", None)
        if not raw:
            continue
        try:
            resolved = Path(raw).resolve()
            relative = resolved.relative_to(root).as_posix()
        except (OSError, ValueError):
            continue
        if relative.endswith(".py"):
            observed.add(relative)
    undeclared = sorted(observed - declared_python_paths)
    if undeclared:
        emit({
            "status": "invalid",
            "entrypoint_path": entrypoint_path,
            "executed_file": entrypoint_path,
            "missing_symbols": [],
            "loaded_repository_python_paths": sorted(observed),
            "undeclared_repository_python_paths": undeclared,
            "process_id": os.getpid(),
            "error_code": "RUNTIME_AUTHORITY_ENTRYPOINT_CLOSURE_UNDECLARED",
            "error_type": "UndeclaredRepositoryModule",
            "message": "Entrypoint loaded an undeclared repository-owned Python module",
        })
        raise SystemExit(0)
    emit({
        "status": "valid",
        "entrypoint_path": entrypoint_path,
        "executed_file": entrypoint_path,
        "missing_symbols": [],
        "loaded_repository_python_paths": sorted(observed),
        "process_id": os.getpid(),
    })
except BaseException as exc:
    if isinstance(exc, SystemExit):
        raise
    emit({
        "status": "invalid",
        "entrypoint_path": request.get("entrypoint_path") if isinstance(locals().get("request"), dict) else None,
        "executed_file": None,
        "missing_symbols": [],
        "loaded_repository_python_paths": [],
        "process_id": os.getpid(),
        "error_code": "RUNTIME_AUTHORITY_ENTRYPOINT_LOAD_FAILED",
        "error_type": type(exc).__name__,
        "message": "Exact manifest entrypoint execution failed",
    })
'''


def _probe_error(code: str, entrypoint_path: str, message: str) -> RuntimeAuthorityManifestError:
    return RuntimeAuthorityManifestError(f"{code}: {entrypoint_path}: {message}")


def _run_entrypoint_probe(
    root: Path,
    entry: dict[str, Any],
    *,
    runtime_interface_id: str,
    declared_python_paths: list[str],
    timeout_seconds: float,
) -> dict[str, Any]:
    entrypoint_path = entry["path"]
    request = {
        "root": str(root),
        "entrypoint_path": entrypoint_path,
        "declared_symbols": entry["symbols"],
        "runtime_interface_id": runtime_interface_id,
        "declared_python_authority_paths": declared_python_paths,
    }
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-c", _CHILD_ENTRYPOINT_PROBE],
            input=json.dumps(request, sort_keys=True),
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise _probe_error(
            "RUNTIME_AUTHORITY_ENTRYPOINT_PROBE_TIMEOUT",
            entrypoint_path,
            "Fresh interpreter probe timed out",
        ) from exc
    if completed.returncode != 0:
        raise _probe_error(
            "RUNTIME_AUTHORITY_ENTRYPOINT_LOAD_FAILED",
            entrypoint_path,
            f"Fresh interpreter exited with code {completed.returncode}",
        )
    stdout = completed.stdout.strip()
    if not stdout:
        raise _probe_error(
            "RUNTIME_AUTHORITY_ENTRYPOINT_RESULT_MISSING",
            entrypoint_path,
            "Fresh interpreter returned no structured result",
        )
    try:
        result = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise _probe_error(
            "RUNTIME_AUTHORITY_ENTRYPOINT_RESULT_MALFORMED",
            entrypoint_path,
            "Fresh interpreter result is not one JSON object",
        ) from exc
    required_result_keys = {
        "status",
        "entrypoint_path",
        "executed_file",
        "missing_symbols",
        "loaded_repository_python_paths",
        "process_id",
    }
    if not isinstance(result, dict) or not required_result_keys.issubset(result):
        raise _probe_error(
            "RUNTIME_AUTHORITY_ENTRYPOINT_RESULT_MALFORMED",
            entrypoint_path,
            "Fresh interpreter result is missing required protocol fields",
        )
    if result["entrypoint_path"] != entrypoint_path:
        raise _probe_error(
            "RUNTIME_AUTHORITY_ENTRYPOINT_RESULT_MALFORMED",
            entrypoint_path,
            "Fresh interpreter reported a different entrypoint identity",
        )
    if result["status"] == "invalid":
        code = result.get("error_code")
        if not isinstance(code, str) or not code:
            code = "RUNTIME_AUTHORITY_ENTRYPOINT_RESULT_MALFORMED"
        message = result.get("message")
        if not isinstance(message, str) or not message:
            message = "Fresh interpreter rejected the manifest entrypoint"
        raise _probe_error(code, entrypoint_path, message)
    if result["status"] != "valid":
        raise _probe_error(
            "RUNTIME_AUTHORITY_ENTRYPOINT_RESULT_MALFORMED",
            entrypoint_path,
            "Fresh interpreter returned an unsupported status",
        )
    if result["executed_file"] != entrypoint_path:
        raise _probe_error(
            "RUNTIME_AUTHORITY_ENTRYPOINT_PATH_MISMATCH",
            entrypoint_path,
            "Fresh interpreter executed a different file",
        )
    if result["missing_symbols"]:
        raise _probe_error(
            "RUNTIME_AUTHORITY_ENTRYPOINT_SYMBOL_MISSING",
            entrypoint_path,
            "Fresh interpreter reported missing manifest-declared symbols",
        )
    if not isinstance(result["loaded_repository_python_paths"], list):
        raise _probe_error(
            "RUNTIME_AUTHORITY_ENTRYPOINT_RESULT_MALFORMED",
            entrypoint_path,
            "Fresh interpreter returned an invalid module-closure field",
        )
    return result


def probe_manifest_entrypoints(
    document: dict[str, Any],
    root: Path,
    *,
    timeout_seconds: float = DEFAULT_ENTRYPOINT_PROBE_TIMEOUT_SECONDS,
) -> list[dict[str, Any]]:
    root = Path(root).resolve()
    entries = document.get("public_entry_points")
    python_paths = document.get("python_authority_paths")
    runtime_interface_id = document.get("runtime_interface_id")
    if not isinstance(entries, list) or not isinstance(python_paths, list):
        raise RuntimeAuthorityManifestError(
            "RUNTIME_AUTHORITY_ENTRYPOINT_RESULT_MALFORMED: manifest entrypoint probe input is invalid"
        )
    if not isinstance(runtime_interface_id, str):
        raise RuntimeAuthorityManifestError("runtime_interface_id mismatch")
    return [
        _run_entrypoint_probe(
            root,
            entry,
            runtime_interface_id=runtime_interface_id,
            declared_python_paths=python_paths,
            timeout_seconds=timeout_seconds,
        )
        for entry in entries
    ]


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
            resolved = _native_repository_path(root, value)
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
    if not any("RUNTIME_INTERFACE_ID" in entry["symbols"] for entry in entries):
        raise RuntimeAuthorityManifestError(
            "At least one public entrypoint must declare RUNTIME_INTERFACE_ID"
        )

    if check_public_symbols:
        probe_manifest_entrypoints(document, root)

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
    "DEFAULT_ENTRYPOINT_PROBE_TIMEOUT_SECONDS",
    "MANIFEST_PATH",
    "RUNTIME_INTERFACE_ID",
    "REQUIRED_PUBLIC_SYMBOLS",
    "RuntimeAuthorityManifestError",
    "load_runtime_authority_manifest",
    "probe_manifest_entrypoints",
    "validate_manifest_document",
]
