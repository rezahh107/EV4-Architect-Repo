#!/usr/bin/env python3
"""Emit the official Architect-owned Project Gate artifact."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from architect_project_gate_exporter import runner as _implementation

globals().update({name: value for name, value in vars(_implementation).items() if not name.startswith("__")})

_SYNC_RUNNER = (
    "validate_payload", "build_export", "validate_contracts", "verify_hashes",
    "inspect_repository", "OutputTransaction",
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
