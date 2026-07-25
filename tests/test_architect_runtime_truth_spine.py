"""G1 facade retaining truth-spine tests on canonical Package semantics."""
from __future__ import annotations

import importlib

from _runtime_private_execution_projection import (
    evaluate_run_with_private_payload,
)

_legacy = importlib.import_module(
    "_legacy_architect_runtime_truth_spine_g1_public"
)


def _run(items=None, *, source_kind="fixture"):
    provider = (
        None
        if source_kind == "live_conversation"
        else _legacy._legacy.FixtureGitProvider()
    )
    return evaluate_run_with_private_payload(
        _legacy._legacy.runtime,
        items or _legacy._legacy.full_outputs(),
        root=_legacy._legacy.REPO_ROOT,
        run_context=_legacy._legacy.context(source_kind),
        git_provider=provider,
    )


_legacy._run = _run
_legacy._legacy.run = _run
for _name in dir(_legacy):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_legacy, _name)
