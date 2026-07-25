"""G1 facade retaining Runtime regression tests on canonical Package semantics."""
from __future__ import annotations

import importlib

from _runtime_private_execution_projection import (
    evaluate_run_with_private_payload,
)

_legacy = importlib.import_module("_legacy_architect_quality_runtime_g1")


def _private_outcome() -> dict:
    return evaluate_run_with_private_payload(
        _legacy.runtime,
        _legacy.outputs(),
        root=_legacy.REPO_ROOT,
        run_context=_legacy.context("fixture"),
        git_provider=_legacy.FixtureGitProvider(),
    )


def test_full_pipeline_is_evaluator_derived_and_passes() -> None:
    outcome = _private_outcome()
    assert outcome["status"] == "valid", outcome["errors"]
    assert outcome["all_required_stages_visited"] is True
    assert all(
        item["evaluated_stage_output_digest"].startswith("sha256:")
        for item in outcome["results"]
    )
    assert [item["completion_class"] for item in outcome["results"][:5]] == [
        "reasoning_complete"
    ] * 5
    assert all(
        item["completion_class"] == "validated_pass"
        for item in outcome["results"][5:]
    )
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["source_payload_digest"].startswith("sha256:")
    assert terminal["export_digest"].startswith("sha256:")
    assert terminal["legacy_export_substituted"] is False
    assert terminal["runtime_issued_payload"]["synthetic"] is True
    assert terminal["functional_eligibility"]["would_allow"] is True
    assert terminal["handoff_allowed"] is False


def test_runtime_issued_candidate_matches_run_state() -> None:
    outcome = _private_outcome()
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["runtime_issued_payload"]["architecture_identity"][
        "selected_candidate_id"
    ] == outcome["run_state"]["selected_candidate_id"]


_legacy.test_full_pipeline_is_evaluator_derived_and_passes = (
    test_full_pipeline_is_evaluator_derived_and_passes
)
_legacy.test_runtime_issued_candidate_matches_run_state = (
    test_runtime_issued_candidate_matches_run_state
)
for _name in dir(_legacy):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_legacy, _name)
