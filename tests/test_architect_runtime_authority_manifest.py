"""Regression-preserving collection shim for Runtime authority tests.

The historical test module is retained byte-for-byte. G1 changes only its fresh
process expectation from the former package-only private Payload exposure to the
canonical public terminal summary now shared by package and wrapper imports.
"""
from __future__ import annotations

import importlib

_legacy = importlib.import_module(
    "_legacy_architect_runtime_authority_manifest_g1"
)
_original_fresh_process_closure = _legacy._fresh_process_closure


def _fresh_process_closure():
    original_run = _legacy.subprocess.run
    old_assertion = (
        'assert terminal["runtime_issued_payload"]["synthetic"] is True'
    )
    new_assertions = (
        'assert "runtime_issued_payload" not in terminal\n'
        'assert terminal["execution_context"]["synthetic"] is True'
    )

    def run_with_canonical_summary(args, *positional, **keyword):
        updated = args
        if (
            isinstance(args, (list, tuple))
            and len(args) >= 3
            and args[1] == "-c"
            and isinstance(args[2], str)
            and old_assertion in args[2]
        ):
            values = list(args)
            values[2] = values[2].replace(
                old_assertion, new_assertions, 1
            )
            updated = type(args)(values) if isinstance(args, tuple) else values
        return original_run(updated, *positional, **keyword)

    _legacy.subprocess.run = run_with_canonical_summary
    try:
        return _original_fresh_process_closure()
    finally:
        _legacy.subprocess.run = original_run


_legacy._fresh_process_closure = _fresh_process_closure

for _name in dir(_legacy):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_legacy, _name)
