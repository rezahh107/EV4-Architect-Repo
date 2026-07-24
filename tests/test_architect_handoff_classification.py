from __future__ import annotations

import ast
import copy
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from architect_handoff_classification import (
    blocks_architect_transition,
    partition_unresolved_evidence,
)
from architect_project_gate_exporter import eligibility

_legacy = importlib.import_module("_legacy_architect_runtime_truth_spine")
DOWNSTREAM_FIXTURE = ROOT / (
    "fixtures/architect-stage-payload/valid/"
    "complete-with-unresolved-downstream-evidence.v1.json"
)


def unresolved(
    unresolved_id: str,
    *,
    blocks: list[str],
    required_before: str,
    owner: str = "architect",
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


def fixture_payload() -> dict:
    return json.loads(DOWNSTREAM_FIXTURE.read_text(encoding="utf-8"))


def runtime_payload(monkeypatch, items: list[dict]) -> dict:
    _, _, state = _legacy.evaluate_prefix(11)
    assembler = importlib.import_module("architect_runtime_payload_assembler")
    monkeypatch.setattr(
        assembler.INTERNAL_ASSEMBLER,
        "_unknowns",
        lambda _state: copy.deepcopy(items),
    )
    return assembler.INTERNAL_ASSEMBLER.assemble_architect_stage_payload(
        run_state=state,
        source_kind="fixture",
    )


@pytest.mark.parametrize(
    ("boundary", "expected"),
    [
        ("architect_stage_payload_acceptance", True),
        ("ce_transition", True),
        ("builder_execution", False),
        ("responsive_validation", False),
        ("production_readiness", False),
    ],
)
def test_blocks_matrix(boundary: str, expected: bool) -> None:
    item = unresolved(
        boundary,
        blocks=[boundary],
        required_before="production_release",
    )
    assert blocks_architect_transition(item) is expected


@pytest.mark.parametrize(
    ("deadline", "expected"),
    [
        ("project_gate_acceptance", True),
        ("ce_transition", True),
        ("builder_execution", False),
        ("responsive_validation", False),
        ("production_release", False),
    ],
)
def test_required_before_matrix(deadline: str, expected: bool) -> None:
    item = unresolved(
        deadline,
        blocks=["production_readiness"],
        required_before=deadline,
    )
    assert blocks_architect_transition(item) is expected


def test_partition_preserves_order_identity_and_input() -> None:
    items = [
        unresolved(
            "responsive",
            blocks=["responsive_validation", "production_readiness"],
            required_before="responsive_validation",
            owner="responsive",
        ),
        unresolved(
            "architect",
            blocks=["architect_stage_payload_acceptance"],
            required_before="project_gate_acceptance",
        ),
        unresolved(
            "builder",
            blocks=["builder_execution", "production_readiness"],
            required_before="builder_execution",
            owner="builder",
        ),
        unresolved(
            "ce",
            blocks=["ce_transition"],
            required_before="ce_transition",
        ),
    ]
    before = copy.deepcopy(items)
    classification = partition_unresolved_evidence(items)
    assert [item["unresolved_id"] for item in classification.transition_blockers] == [
        "architect",
        "ce",
    ]
    assert [item["unresolved_id"] for item in classification.downstream_obligations] == [
        "responsive",
        "builder",
    ]
    assert classification.transition_blockers[0] is items[1]
    assert classification.downstream_obligations[0] is items[0]
    assert items == before


@pytest.mark.parametrize(
    ("item", "error", "message"),
    [
        ("not-a-mapping", TypeError, "item must be a mapping"),
        (
            {"blocks": "ce_transition", "required_before": "ce_transition"},
            TypeError,
            "blocks must be a list",
        ),
        (
            {"blocks": [""], "required_before": "ce_transition"},
            ValueError,
            "blocks must contain non-empty strings",
        ),
        (
            {"blocks": ["ce_transition"]},
            ValueError,
            "required_before must be a non-empty string",
        ),
    ],
)
def test_malformed_items_fail_deterministically(item, error, message) -> None:
    with pytest.raises(error, match=message):
        partition_unresolved_evidence([item])


def test_existing_downstream_fixture_remains_functionally_nonblocking() -> None:
    payload = fixture_payload()
    classification = partition_unresolved_evidence(payload["unresolved_evidence"])
    assert payload["payload_status"] == "complete"
    assert classification.transition_blockers == ()
    assert eligibility.derive_handoff_eligibility(payload) == {
        "would_allow": True,
        "blockers": [],
    }


@pytest.mark.parametrize(
    ("case_id", "items", "status", "would_allow"),
    [
        ("none", [], "complete", True),
        (
            "responsive-only",
            [
                unresolved(
                    "responsive-only",
                    blocks=["responsive_validation", "production_readiness"],
                    required_before="responsive_validation",
                    owner="responsive",
                )
            ],
            "complete",
            True,
        ),
        (
            "builder-only",
            [
                unresolved(
                    "builder-only",
                    blocks=["builder_execution", "production_readiness"],
                    required_before="builder_execution",
                    owner="builder",
                )
            ],
            "complete",
            True,
        ),
        (
            "production-only",
            [
                unresolved(
                    "production-only",
                    blocks=["production_readiness"],
                    required_before="production_release",
                    owner="builder",
                )
            ],
            "complete",
            True,
        ),
        (
            "architect-acceptance",
            [
                unresolved(
                    "architect-acceptance",
                    blocks=["architect_stage_payload_acceptance"],
                    required_before="project_gate_acceptance",
                )
            ],
            "insufficient_evidence",
            False,
        ),
        (
            "ce-transition",
            [
                unresolved(
                    "ce-transition",
                    blocks=["ce_transition"],
                    required_before="ce_transition",
                )
            ],
            "insufficient_evidence",
            False,
        ),
        (
            "mixed",
            [
                unresolved(
                    "responsive",
                    blocks=["responsive_validation"],
                    required_before="responsive_validation",
                    owner="responsive",
                ),
                unresolved(
                    "ce",
                    blocks=["ce_transition"],
                    required_before="ce_transition",
                ),
            ],
            "insufficient_evidence",
            False,
        ),
    ],
)
def test_assembler_and_functional_eligibility_share_matrix(
    monkeypatch,
    case_id: str,
    items: list[dict],
    status: str,
    would_allow: bool,
) -> None:
    payload = runtime_payload(monkeypatch, items)
    assert payload["payload_status"] == status, case_id
    assert payload["unresolved_evidence"] == items
    assert eligibility.derive_handoff_eligibility(payload)["would_allow"] is would_allow


def test_all_four_consumers_delegate_to_shared_classifier() -> None:
    paths = [
        ROOT / "scripts/architect_runtime_payload_assembler_core.py",
        ROOT / "scripts/architect_project_gate_exporter/eligibility.py",
        ROOT / "scripts/architect_project_gate_exporter/contracts.py",
        ROOT / "scripts/check_architect_stage_payload_core.py",
    ]
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        assert any(
            isinstance(node, ast.ImportFrom)
            and node.module == "architect_handoff_classification"
            and any(alias.name == "partition_unresolved_evidence" for alias in node.names)
            for node in ast.walk(tree)
        ), path
        assert any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "partition_unresolved_evidence"
            for node in ast.walk(tree)
        ), path
        assigned_names = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            for target in (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
            if isinstance(target, ast.Name)
        }
        assert "ARCHITECT_TRANSITION_BLOCKS" not in assigned_names, path
        assert "ARCHITECT_TRANSITION_DEADLINES" not in assigned_names, path
