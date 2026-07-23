#!/usr/bin/env python3
"""Emit the official Architect-owned Project Gate artifact."""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPTS / "architect_project_gate_exporter"
PACKAGE_NAME = "_ev4_architect_project_gate_exporter"

# Some legacy tests load this compatibility entrypoint under the public package
# name. Publish the real package path so later Runtime submodule imports remain
# deterministic and do not depend on test/import order.
__path__ = [str(PACKAGE_DIR)]

if PACKAGE_NAME not in sys.modules:
    package_spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        PACKAGE_DIR / "__init__.py",
        submodule_search_locations=[str(PACKAGE_DIR)],
    )
    if package_spec is None or package_spec.loader is None:
        raise ImportError("Architect Project Gate exporter package could not be loaded.")
    package = importlib.util.module_from_spec(package_spec)
    sys.modules[PACKAGE_NAME] = package
    package_spec.loader.exec_module(package)

# ARCH-02 is the bounded operational entrypoint. It preserves the complete
# ARCH-01 surface and overrides only commit-boundary/result semantics.
_implementation = importlib.import_module(f"{PACKAGE_NAME}.arch02")

globals().update(
    {name: value for name, value in vars(_implementation).items() if not name.startswith("__")}
)

_SYNC_RUNNER = (
    "validate_payload",
    "build_export",
    "validate_contracts",
    "verify_hashes",
    "inspect_repository",
    "OutputTransaction",
)
_ORIGINAL_IMPLEMENTATION_RUN_EXPORT = _implementation.run_export


def _sync_test_overrides() -> None:
    for name in _SYNC_RUNNER:
        if name in globals():
            setattr(_implementation, name, globals()[name])
    if "_ancestry_primitives_available" in globals():
        setattr(
            _implementation._ancestry_module,
            "_ancestry_primitives_available",
            globals()["_ancestry_primitives_available"],
        )
    for name in ("fcntl", "msvcrt"):
        if name in globals():
            setattr(_implementation._locking_module, name, globals()[name])
    current_run_export = globals().get("run_export")
    _implementation.run_export = (
        _ORIGINAL_IMPLEMENTATION_RUN_EXPORT
        if current_run_export is _RUN_EXPORT_PROXY
        else current_run_export
    )


def run_export(*args, **kwargs):
    _sync_test_overrides()
    return _ORIGINAL_IMPLEMENTATION_RUN_EXPORT(*args, **kwargs)


_RUN_EXPORT_PROXY = run_export


def atomic_write(*args, **kwargs):
    _sync_test_overrides()
    return _implementation.atomic_write(*args, **kwargs)


def main(argv=None):
    _sync_test_overrides()
    return _implementation.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
