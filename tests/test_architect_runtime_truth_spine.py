"""Regression facade retaining the prior truth-spine suite with real live provenance."""
from __future__ import annotations

import importlib

_legacy = importlib.import_module("_legacy_architect_runtime_truth_spine")


def _run(items=None, *, source_kind="fixture"):
    provider = None if source_kind == "live_conversation" else _legacy.FixtureGitProvider()
    return _legacy.runtime.evaluate_run(
        items or _legacy.full_outputs(),
        root=_legacy.REPO_ROOT,
        run_context=_legacy.context(source_kind),
        git_provider=provider,
    )


def _evaluate_prefix(count: int, *, source_kind: str = "fixture"):
    items = _legacy.outputs()
    state = _legacy.runtime.initial_run_state(items[0]["run_id"], root=_legacy.REPO_ROOT)
    results = []
    provider = None if source_kind == "live_conversation" else _legacy.FixtureGitProvider()
    for output in items[:count]:
        result, state = _legacy.runtime.evaluate_stage(
            output["stage_id"],
            output,
            state,
            root=_legacy.REPO_ROOT,
            run_context=_legacy.context(source_kind),
            git_provider=provider,
        )
        assert result["stage_status"] == "pass", result["blocking_issues"]
        results.append(result)
    return items, results, state


_legacy.run = _run
_legacy.evaluate_prefix = _evaluate_prefix
for _name in dir(_legacy):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_legacy, _name)
