from __future__ import annotations

import copy
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import architect_quality_runtime as runtime
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


def provenance() -> base.GitProvenance:
    return base.GitProvenance(
        repository=base.REPOSITORY,
        ref="test/handoff-validator-consistency",
        commit_sha="a" * 40,
    )


def test_transition_blocker_is_consistent_across_classifier_assembler_eligibility_and_validator(
    monkeypatch,
) -> None:
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
    assert mismatch["severity"] == "insufficient_evidence"
    assert mismatch["details"] == {"transition_blocker_ids": ["U-ce-consistency"]}


def test_downstream_only_obligation_remains_valid_and_visible(monkeypatch) -> None:
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
    assert ArchitectPayloadValidator(ROOT).validate_value(payload) == {
        "status": "valid",
        "diagnostics": [],
    }


def test_validator_accepted_raw_payload_still_cannot_authorize_export(monkeypatch) -> None:
    item = unresolved(
        "U-responsive-consistency",
        blocks=["responsive_validation"],
        required_before="responsive_validation",
        owner="responsive",
    )
    payload = runtime_payload(monkeypatch, [item])
    assert ArchitectPayloadValidator(ROOT).validate_value(payload)["status"] == "valid"
    with pytest.raises(contracts.ExportError) as caught:
        contracts.build_export(
            payload,
            provenance(),
            payload["payload_identity"].get("run_id", "caller-run"),
            "quality_runtime:runtime_issued_payload",
        )
    assert caught.value.code == "ARCH_EXPORT_RUNTIME_PAYLOAD_AUTHORITY_REQUIRED"


def test_canonical_runtime_preserves_downstream_and_synthetic_separation() -> None:
    fixture_outcome = _legacy.run(source_kind="fixture")
    assert fixture_outcome["status"] == "valid", fixture_outcome["errors"]
    fixture_terminal = fixture_outcome["results"][-1]["project_gate_export"]
    assert fixture_terminal["functional_eligibility"]["would_allow"] is True
    assert fixture_terminal["handoff_allowed"] is False

    live_outcome = runtime.evaluate_run(
        _legacy.full_outputs(),
        root=ROOT,
        run_context=_legacy.context("live_conversation"),
    )
    assert live_outcome["status"] == "valid", live_outcome["errors"]
    live_terminal = live_outcome["results"][-1]["project_gate_export"]
    assert live_terminal["functional_eligibility"]["would_allow"] is True
    assert live_terminal["handoff_allowed"] is True
