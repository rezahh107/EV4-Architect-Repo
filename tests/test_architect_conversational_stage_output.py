"""G1 facade retaining conversational Stage Output mutation coverage."""
from __future__ import annotations

import importlib

from _runtime_private_execution_projection import (
    evaluate_run_with_private_payload,
)

_legacy = importlib.import_module(
    "_legacy_architect_conversational_stage_output_g1"
)


def test_terminal_fixture_passes_official_evaluator_and_exporter() -> None:
    outcome = evaluate_run_with_private_payload(
        _legacy.runtime,
        [*_legacy.prefinal_outputs(), _legacy.terminal_output()],
        root=_legacy.REPO_ROOT,
        run_context=_legacy.run_context("fixture"),
        git_provider=_legacy.FixtureGitProvider(),
    )
    assert outcome["status"] == "valid", outcome["errors"]
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["canonical_payload_valid"] is True
    assert terminal["legacy_export_substituted"] is False
    assert terminal["source_payload_digest"].startswith("sha256:")
    assert terminal["export_digest"].startswith("sha256:")
    assert terminal["runtime_issued_payload"]["synthetic"] is True
    assert terminal["functional_eligibility"]["would_allow"] is True
    assert terminal["handoff_allowed"] is False


_legacy.test_terminal_fixture_passes_official_evaluator_and_exporter = (
    test_terminal_fixture_passes_official_evaluator_and_exporter
)
for _name in dir(_legacy):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_legacy, _name)
