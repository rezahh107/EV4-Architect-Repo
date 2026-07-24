from __future__ import annotations

import ast
import copy
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from architect_handoff_classification import partition_unresolved_evidence
from architect_project_gate_exporter import base, contracts, eligibility
from check_architect_stage_payload_core import ArchitectPayloadValidator

_legacy = importlib.import_module("_legacy_architect_runtime_truth_spine")


def unresolved(
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


def runtime_payload(monkeypatch, items: list[dict]) -> dict:
    outputs = _legacy.outputs()
    state = _legacy.runtime.initial_run_state(outputs[0]["run_id"], root=ROOT)
    provider = _legacy.FixtureGitProvider()
    for output in outputs[:11]:
        result, state = _legacy.runtime.evaluate_stage(
            output["stage_id"],
            output,
            state,
            root=ROOT,
            run_context=_legacy.context("fixture"),
            git_provider=provider,
        )
        assert result["stage_status"] == "pass", result["blocking_issues"]

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


def provenance() -> base.GitProvenance:
    return base.GitProvenance(
        repository=base.REPOSITORY,
        ref="test/handoff-validator-consistency",
        commit_sha="a" * 40,
    )


def test_transition_blocker_is_consistent_across_all_consumers(monkeypatch) -> None:
    item = unresolved(
        "U-ce-consistency",
        blocks=["ce_transition"],
        required_before="ce_transition",
        owner="architect",
    )
    payload = runtime_payload(monkeypatch, [item])
    classification = partition_unresolved_evidence(payload["unresolved_evidence"])

    assert payload["payload_status"] == "insufficient_evidence"
    assert list(classification.transition_blockers) == [item]
    assert eligibility.derive_handoff_eligibility(payload) == {
        "would_allow": False,
        "blockers": [item],
    }

    export, _ = contracts.build_export(
        payload,
        provenance(),
        "transition-blocker-consistency",
        "consistency-test",
    )
    assert export["handoff"]["allowed"] is False
    assert export["handoff"]["status"] == "insufficient_evidence"

    validator = ArchitectPayloadValidator(ROOT)
    assert validator.validate_value(payload)["status"] == "insufficient_evidence"

    inconsistent = copy.deepcopy(payload)
    inconsistent["payload_status"] = "complete"
    result = validator.validate_value(inconsistent)
    assert result["status"] == "insufficient_evidence"
    mismatch = next(
        diagnostic
        for diagnostic in result["diagnostics"]
        if diagnostic["code"] == "A_R05_TRANSITION_BLOCKER_STATUS_MISMATCH"
    )
    assert mismatch == {
        "code": "A_R05_TRANSITION_BLOCKER_STATUS_MISMATCH",
        "severity": "insufficient_evidence",
        "message": (
            "Payload status cannot be complete while unresolved evidence blocks "
            "Architect Payload acceptance or CE transition."
        ),
        "path": "$.payload_status",
        "rule_id": "A-R05",
        "details": {"transition_blocker_ids": ["U-ce-consistency"]},
    }


def test_downstream_only_obligation_remains_valid_for_all_consumers(monkeypatch) -> None:
    item = unresolved(
        "U-responsive-consistency",
        blocks=["responsive_validation", "production_readiness"],
        required_before="responsive_validation",
        owner="responsive",
    )
    payload = runtime_payload(monkeypatch, [item])
    classification = partition_unresolved_evidence(payload["unresolved_evidence"])

    assert payload["payload_status"] == "complete"
    assert classification.transition_blockers == ()
    assert list(classification.downstream_obligations) == [item]
    assert eligibility.derive_handoff_eligibility(payload) == {
        "would_allow": True,
        "blockers": [],
    }

    export, _ = contracts.build_export(
        payload,
        provenance(),
        "downstream-obligation-consistency",
        "consistency-test",
    )
    assert export["handoff"]["allowed"] is False
    assert export["handoff"]["status"] == "blocked"

    live_payload = copy.deepcopy(payload)
    live_payload["synthetic"] = False
    live_export, _ = contracts.build_export(
        live_payload,
        provenance(),
        "downstream-obligation-live-consistency",
        "consistency-test",
    )
    assert live_export["handoff"]["allowed"] is True
    assert live_export["handoff"]["status"] == "successful_with_flags"
    assert ArchitectPayloadValidator(ROOT).validate_value(payload) == {
        "status": "valid",
        "diagnostics": [],
    }


def test_every_consumer_delegates_to_the_shared_classifier() -> None:
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
