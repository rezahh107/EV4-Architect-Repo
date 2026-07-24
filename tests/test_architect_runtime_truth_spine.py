"""Regression facade retaining the prior truth-spine suite with real live provenance."""
from __future__ import annotations

import copy
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


def _downstream_unknown_outputs() -> list[dict]:
    items = copy.deepcopy(_legacy.full_outputs())
    items[0]["unknown_introductions"] = [
        {
            "unknown_id": "U-responsive-runtime",
            "statement": "Responsive behavior remains unverified.",
            "downstream_critical": False,
        }
    ]
    return items


def test_live_downstream_only_unknown_allows_handoff_with_visible_obligation() -> None:
    outcome = _run(
        _downstream_unknown_outputs(),
        source_kind="live_conversation",
    )

    assert outcome["status"] == "valid", outcome["errors"]
    terminal = outcome["results"][-1]["project_gate_export"]
    payload = terminal["runtime_issued_payload"]
    unresolved = next(
        item
        for item in payload["unresolved_evidence"]
        if item["unresolved_id"] == "U-responsive-runtime"
    )
    assert payload["payload_status"] == "complete"
    assert unresolved == {
        "unresolved_id": "U-responsive-runtime",
        "state": "insufficient_evidence",
        "owner": "responsive",
        "reason": "Responsive behavior remains unverified.",
        "blocks": ["responsive_validation", "production_readiness"],
        "required_before": "responsive_validation",
        "evidence_refs": [],
    }
    assert terminal["functional_eligibility"] == {
        "would_allow": True,
        "blockers": [],
    }
    assert terminal["handoff_allowed"] is True


def test_synthetic_downstream_only_unknown_is_functionally_eligible_but_blocked() -> None:
    outcome = _run(
        _downstream_unknown_outputs(),
        source_kind="fixture",
    )

    assert outcome["status"] == "valid", outcome["errors"]
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["runtime_issued_payload"]["payload_status"] == "complete"
    assert terminal["functional_eligibility"] == {
        "would_allow": True,
        "blockers": [],
    }
    assert terminal["handoff_allowed"] is False
    assert terminal["execution_context"] == {
        "source_kind": "fixture",
        "synthetic": True,
    }


def _unresolved(
    unresolved_id: str,
    *,
    blocks: list[str],
    required_before: str,
    owner: str,
) -> dict:
    return {
        "unresolved_id": unresolved_id,
        "state": "insufficient_evidence",
        "owner": owner,
        "reason": f"{unresolved_id} remains unresolved.",
        "blocks": blocks,
        "required_before": required_before,
        "evidence_refs": [],
    }


def _runtime_payload_with_items(monkeypatch, items: list[dict], source_kind: str = "fixture"):
    _, _, state = _evaluate_prefix(11, source_kind=source_kind)
    assembler = importlib.import_module("architect_runtime_payload_assembler")
    monkeypatch.setattr(
        assembler.INTERNAL_ASSEMBLER,
        "_unknowns",
        lambda _state: copy.deepcopy(items),
    )
    return assembler.INTERNAL_ASSEMBLER.assemble_architect_stage_payload(
        run_state=state,
        source_kind=source_kind,
    )


def test_runtime_generated_builder_only_obligation_keeps_payload_complete(monkeypatch) -> None:
    item = _unresolved(
        "U-builder-runtime",
        blocks=["builder_execution", "production_readiness"],
        required_before="builder_execution",
        owner="builder",
    )

    payload = _runtime_payload_with_items(monkeypatch, [item])

    assert payload["payload_status"] == "complete"
    assert payload["unresolved_evidence"] == [item]


def test_runtime_generated_architect_acceptance_blocker_is_insufficient(monkeypatch) -> None:
    item = _unresolved(
        "U-architect-runtime",
        blocks=["architect_stage_payload_acceptance"],
        required_before="project_gate_acceptance",
        owner="architect",
    )

    payload = _runtime_payload_with_items(monkeypatch, [item])

    assert payload["payload_status"] == "insufficient_evidence"
    assert payload["unresolved_evidence"] == [item]


def test_runtime_generated_ce_transition_blocker_is_insufficient(monkeypatch) -> None:
    item = _unresolved(
        "U-ce-runtime",
        blocks=["ce_transition"],
        required_before="ce_transition",
        owner="architect",
    )

    payload = _runtime_payload_with_items(monkeypatch, [item])

    assert payload["payload_status"] == "insufficient_evidence"
    assert payload["unresolved_evidence"] == [item]


def test_runtime_generated_mixed_evidence_preserves_all_items(monkeypatch) -> None:
    items = [
        _unresolved(
            "U-responsive-runtime",
            blocks=["responsive_validation", "production_readiness"],
            required_before="responsive_validation",
            owner="responsive",
        ),
        _unresolved(
            "U-builder-runtime",
            blocks=["builder_execution", "production_readiness"],
            required_before="builder_execution",
            owner="builder",
        ),
        _unresolved(
            "U-ce-runtime",
            blocks=["ce_transition"],
            required_before="ce_transition",
            owner="architect",
        ),
    ]

    payload = _runtime_payload_with_items(monkeypatch, items)

    assert payload["payload_status"] == "insufficient_evidence"
    assert payload["unresolved_evidence"] == items
