"""Regression facade retaining prior payload/error tests on the canonical API."""
from __future__ import annotations

import copy
import importlib

import pytest

_legacy = importlib.import_module("_legacy_architect_runtime_completion_payload_errors")


def _provider(kind: str):
    return None if kind == "live_conversation" else _legacy.FixtureGitProvider()


def _evaluate_prefix(items, count: int, *, kind: str = "fixture"):
    state = _legacy.runtime.initial_run_state(items[0]["run_id"], root=_legacy.REPO_ROOT)
    results = []
    for output in items[:count]:
        result, state = _legacy.runtime.evaluate_stage(
            output["stage_id"],
            output,
            state,
            root=_legacy.REPO_ROOT,
            run_context=_legacy.context(kind),
            git_provider=_provider(kind),
        )
        assert result["stage_status"] == "pass", result["blocking_issues"]
        results.append(result)
    return results, state


def _evaluate_full(items=None, *, kind: str = "fixture"):
    return _legacy.runtime.evaluate_run(
        items or _legacy.all_outputs(),
        root=_legacy.REPO_ROOT,
        run_context=_legacy.context(kind),
        git_provider=_provider(kind),
    )


def test_payload_ignores_forged_derived_state_and_replays_history() -> None:
    outcome = _evaluate_full()
    forged = copy.deepcopy(outcome["run_state"])
    forged["derived_stage_results"][0]["stage_status"] = "blocked"
    forged["derived_stage_results"][0]["completion_class"] = "reasoning_complete"
    forged["selected_candidate_id"] = "FORGED-CANDIDATE"
    forged["selected_candidate_locked"] = True
    forged["unknown_ledger"] = [{"unknown_id": "FORGED", "status": "active"}]
    forged["build_tree_digest"] = "sha256:" + "f" * 64
    canonical = _legacy.assembler.assemble_architect_stage_payload(
        run_state=outcome["run_state"], source_kind="fixture"
    )
    replayed = _legacy.assembler.assemble_architect_stage_payload(
        run_state=forged, source_kind="fixture"
    )
    assert replayed == canonical
    assert replayed["architecture_identity"]["selected_candidate_id"] != "FORGED-CANDIDATE"


_legacy.evaluate_prefix = _evaluate_prefix
_legacy.evaluate_full = _evaluate_full
_legacy.test_payload_lineage_rejects_failed_stage_with_success_completion = (
    test_payload_ignores_forged_derived_state_and_replays_history
)
for _name in dir(_legacy):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_legacy, _name)


@pytest.mark.parametrize(
    "field, unresolved_id, payload_status, would_allow, handoff_allowed",
    [
        ("asset_intent", "U-payload-asset-intent", "insufficient_evidence", False, False),
        ("scoped_css_intent", "U-payload-css-intent", "insufficient_evidence", False, False),
        (
            "dynamic_loop_intent",
            "U-payload-dynamic-loop-intent",
            "insufficient_evidence",
            False,
            False,
        ),
        (
            "responsive_risk_seeds",
            "U-payload-project-responsive-risk",
            "complete",
            True,
            True,
        ),
        ("media_decision", "U-payload-media-decision", "insufficient_evidence", False, False),
        (
            "styling_decision",
            "U-payload-styling-decision",
            "insufficient_evidence",
            False,
            False,
        ),
    ],
)
def test_missing_conditional_intent_never_creates_a_false_complete_payload(
    field: str,
    unresolved_id: str,
    payload_status: str,
    would_allow: bool,
    handoff_allowed: bool,
) -> None:
    items = _legacy.all_outputs()
    items[8]["canonical_content"].pop(field)
    outcome = _evaluate_full(items, kind="live_conversation")
    assert outcome["status"] == "valid", outcome["errors"]
    export = outcome["results"][-1]["project_gate_export"]
    payload = export["runtime_issued_payload"]
    assert payload["payload_status"] == payload_status
    assert any(
        item["unresolved_id"] == unresolved_id
        for item in payload["unresolved_evidence"]
    )
    assert export["functional_eligibility"]["would_allow"] is would_allow
    assert export["handoff_allowed"] is handoff_allowed
    assert "architect-section" not in _legacy.json.dumps(payload)
