"""G1 facade retaining truth-spine tests without global test contamination."""
from __future__ import annotations

import importlib
import sys

from _runtime_private_execution_projection import (
    evaluate_run_with_private_payload,
)

_private = importlib.import_module(
    "_legacy_architect_runtime_truth_spine_g1_private"
)
_shared = sys.modules.get("_legacy_architect_runtime_truth_spine")
sys.modules["_legacy_architect_runtime_truth_spine"] = _private
try:
    _legacy = importlib.import_module(
        "_legacy_architect_runtime_truth_spine_g1_public"
    )
finally:
    if _shared is None:
        sys.modules.pop("_legacy_architect_runtime_truth_spine", None)
    else:
        sys.modules["_legacy_architect_runtime_truth_spine"] = _shared


def _run(items=None, *, source_kind="fixture"):
    provider = (
        None
        if source_kind == "live_conversation"
        else _private.FixtureGitProvider()
    )
    return evaluate_run_with_private_payload(
        _private.runtime,
        items or _private.full_outputs(),
        root=_private.REPO_ROOT,
        run_context=_private.context(source_kind),
        git_provider=provider,
    )


_legacy._run = _run
_private.run = _run
for _name in dir(_legacy):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_legacy, _name)
