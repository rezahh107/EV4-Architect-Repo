from __future__ import annotations

import copy
import importlib
import importlib.util
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Callable

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import architect_pcvp_producer as pcvp  # noqa: E402
import architect_quality_runtime as runtime  # noqa: E402
from architect_project_gate_exporter import contracts  # noqa: E402

_legacy = importlib.import_module("_legacy_architect_runtime_truth_spine")

PAYLOAD_HASH = "a" * 64


def _candidate(**changes: object) -> dict:
    values: dict[str, object] = {
        "run_id": "run-pcvp-architect-001",
        "payload_hash": PAYLOAD_HASH,
        "canonical_payload_valid": True,
        "handoff_allowed": True,
        "source_kind": "live_conversation",
        "unresolved_count": 0,
    }
    values.update(changes)
    return pcvp._format_continuation_assurance_candidate(**values)


def _document(**changes: object) -> dict:
    return {"continuation_assurance": _candidate(**changes)}


def _evaluate(document: dict) -> dict:
    return pcvp._evaluate_carrier_document(document, ROOT)


def _capture_genuine_runtime_carrier(
    monkeypatch: pytest.MonkeyPatch,
) -> dict:
    """Capture the dormant carrier inside the genuine terminal transaction."""

    captured: list[dict] = []
    real_build = contracts.build_export

    def capture_then_preserve_legacy(*args, **kwargs):
        export, hashes = real_build(*args, **kwargs)
        carrier = export.pop("continuation_assurance")
        captured.append(copy.deepcopy(carrier))
        hashes["export_hash"] = contracts.digest(export)
        return export, hashes

    monkeypatch.setattr(pcvp, "PRODUCER_EMISSION_ENABLED", True)
    monkeypatch.setattr(contracts, "build_export", capture_then_preserve_legacy)
    outcome = runtime.evaluate_run(
        _legacy.full_outputs(),
        root=ROOT,
        run_context=_legacy.context("live_conversation"),
    )
    assert outcome["status"] == "valid", outcome["errors"]
    assert len(captured) == 1
    return captured[0]


def test_resources_are_exactly_pinned_and_emission_is_hard_disabled() -> None:
    result = pcvp.verify_pcvp_resources(ROOT)
    assert result["producer_emission"] is False
    assert result["adoption_status"] == "not_yet_adopted"
    assert result["activation_effect"] == "NONE"
    assert len(result["resource_hashes"]) == 6
    assert pcvp.PRODUCER_EMISSION_ENABLED is False


def test_supported_surface_exposes_no_authoritative_raw_fact_minting_api() -> None:
    assert "build_continuation_assurance" not in pcvp.__all__
    assert "attach_to_export_if_enabled" not in pcvp.__all__
    assert "PRODUCER_EMISSION_ENABLED" not in pcvp.__all__
    assert not hasattr(pcvp, "build_continuation_assurance")
    assert not hasattr(pcvp, "attach_to_export_if_enabled")
    assert "repository_root" not in inspect.signature(contracts.build_export).parameters


def test_raw_true_values_cannot_mint_an_authoritative_carrier() -> None:
    public_functions = {
        name: value
        for name in pcvp.__all__
        if inspect.isfunction(value := getattr(pcvp, name))
    }
    assert set(public_functions) == {"verify_pcvp_resources"}
    assert issubclass(pcvp.PCVPProducerError, RuntimeError)
    assert all(
        "canonical_payload_valid" not in inspect.signature(value).parameters
        for value in public_functions.values()
    )
    assert all(
        "handoff_allowed" not in inspect.signature(value).parameters
        for value in public_functions.values()
    )


def test_caller_selected_repository_root_cannot_enter_official_construction() -> None:
    assert "repository_root" not in inspect.signature(contracts.build_export).parameters
    assert "repository_root" not in inspect.signature(
        pcvp._format_continuation_assurance_candidate
    ).parameters


def test_dormant_runtime_path_does_not_touch_pcvp_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("dormant path must not load or validate PCVP resources")

    monkeypatch.setattr(pcvp, "verify_pcvp_resources", forbidden)
    outcome = runtime.evaluate_run(
        _legacy.full_outputs(),
        root=ROOT,
        run_context=_legacy.context("live_conversation"),
    )
    assert outcome["status"] == "valid", outcome["errors"]
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["handoff_allowed"] is True


def test_only_genuine_runtime_transaction_reaches_official_carrier_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    carrier = _capture_genuine_runtime_carrier(monkeypatch)
    assert carrier["policy_id"] == "EV4-PCVP"
    assert carrier["policy_version"] == "1.0.0"
    assert carrier["source_stage"] == "ARCHITECT"
    assert carrier["effects"][0]["continuation_state"] == "CONTINUE"
    assert carrier["stage_summary"] == {
        **carrier["stage_summary"],
        "owner_projection": "YELLOW",
        "yellow_substate": "CONTINUATION_AVAILABLE",
    }
    downstream = carrier["claims"][1]
    assert downstream["verification_state"] == "UNVERIFIED"
    assert downstream["evidence_refs"] == []
    assert _evaluate({"continuation_assurance": carrier})["accepted"] is True


def test_copied_reconstructed_and_mutated_payloads_remain_non_authorizing() -> None:
    replay = runtime._replay_outcome(
        _legacy.full_outputs(),
        run_context=_legacy.context("fixture"),
        repository_root=ROOT,
        require_terminal=True,
        git_provider=_legacy.FixtureGitProvider(),
    )
    assert replay.status == "valid"
    execution = replay.results[-1]["project_gate_export"]
    original = execution.runtime_issued_payload

    for payload in (copy.deepcopy(original), dict(original)):
        with pytest.raises(contracts.ExportError) as caught:
            contracts.build_export(
                payload,
                execution.producer_provenance,
                replay.run_state["run_id"],
                "quality_runtime:runtime_issued_payload",
            )
        assert caught.value.code == "ARCH_EXPORT_RUNTIME_PAYLOAD_AUTHORITY_REQUIRED"

    original["continuation_assurance"] = _candidate()
    with pytest.raises(contracts.ExportError) as caught:
        contracts.build_export(
            original,
            execution.producer_provenance,
            replay.run_state["run_id"],
            "quality_runtime:runtime_issued_payload",
        )
    assert caught.value.code in {
        "ARCH_EXPORT_RUNTIME_PAYLOAD_AUTHORITY_REQUIRED",
        "ARCH_EXPORT_CALLER_PCVP_CARRIER_FORBIDDEN",
    }


Mutation = Callable[[dict], None]


def _duplicate_id(document: dict) -> None:
    carrier = document["continuation_assurance"]
    carrier["authorizations"][0]["authorization_id"] = carrier["effects"][0][
        "effect_id"
    ]
    carrier["effects"][0]["authorization_ref"] = carrier["effects"][0]["effect_id"]


def _unresolved_claim(document: dict) -> None:
    document["continuation_assurance"]["effects"][0]["depends_on_claim_ids"][0] = (
        "CLM-MISSING"
    )


def _unresolved_authorization(document: dict) -> None:
    document["continuation_assurance"]["effects"][0]["authorization_ref"] = (
        "AUTH-MISSING"
    )


def _inactive_authorization(document: dict) -> None:
    document["continuation_assurance"]["authorizations"][0]["status"] = "REVOKED"


def _non_covering_authorization(document: dict) -> None:
    auth = document["continuation_assurance"]["authorizations"][0]
    auth["allowed_effect_ids"] = ["EFF-OTHER"]
    auth["allowed_effect_classes"] = []


def _scope_mismatch(document: dict) -> None:
    document["continuation_assurance"]["authorizations"][0][
        "permitted_scope"
    ] = "Different bounded scope"


def _safe_default_external(document: dict) -> None:
    document["continuation_assurance"]["authorizations"][0]["basis"] = (
        "SAFE_REVERSIBLE_DEFAULT"
    )


def _critical_contradicted_continues(document: dict) -> None:
    document["continuation_assurance"]["claims"][0]["verification_state"] = (
        "CONTRADICTED"
    )
    document["continuation_assurance"]["claims"][0]["lifecycle_state"] = "ACTIVE"
    document["continuation_assurance"]["claims"][0]["evidence_refs"] = []


def _unresolved_summary_effect(document: dict) -> None:
    document["continuation_assurance"]["stage_summary"]["current_effect_id"] = (
        "EFF-MISSING"
    )


def _unresolved_summary_claim(document: dict) -> None:
    document["continuation_assurance"]["stage_summary"]["derived_from_claim_ids"][
        0
    ] = "CLM-MISSING"


def _summary_claim_not_dependency(document: dict) -> None:
    carrier = document["continuation_assurance"]
    extra = copy.deepcopy(carrier["claims"][1])
    extra["claim_id"] = "CLM-EXTRA-NONDEPENDENCY"
    carrier["claims"].append(extra)
    carrier["stage_summary"]["derived_from_claim_ids"][0] = extra["claim_id"]


def _invalid_green(document: dict) -> None:
    carrier = document["continuation_assurance"]
    critical = carrier["claims"][0]
    critical["verification_state"] = "UNVERIFIED"
    critical["lifecycle_state"] = "ACTIVE"
    critical["evidence_refs"] = []
    carrier["stage_summary"]["owner_projection"] = "GREEN"
    carrier["stage_summary"]["yellow_substate"] = None


def _invalid_yellow(document: dict) -> None:
    document["continuation_assurance"]["stage_summary"]["yellow_substate"] = (
        "OWNER_CHOICE_REQUIRED"
    )


def _red_nonblocked(document: dict) -> None:
    summary = document["continuation_assurance"]["stage_summary"]
    summary["owner_projection"] = "RED"
    summary["yellow_substate"] = None


def _required_red_missing(document: dict) -> None:
    carrier = document["continuation_assurance"]
    carrier["effects"][0]["continuation_state"] = "BLOCKED"
    carrier["effects"][0]["authorization_ref"] = None
    carrier["effects"][0]["blocker_reason"] = "EXTERNAL_VERIFICATION_REQUIRED"
    carrier["effects"][0]["permitted_scope"] = None
    carrier["authorizations"] = []


@pytest.mark.parametrize(
    ("mutation", "layer", "code"),
    [
        (_duplicate_id, "CROSS_RECORD", "PCVP_ID_NOT_GLOBALLY_UNIQUE"),
        (_unresolved_claim, "CROSS_RECORD", "PCVP_EFFECT_CLAIM_REF_UNRESOLVED"),
        (
            _unresolved_authorization,
            "CROSS_RECORD",
            "PCVP_EFFECT_AUTH_REF_UNRESOLVED",
        ),
        (_inactive_authorization, "CROSS_RECORD", "PCVP_EFFECT_AUTH_NOT_ACTIVE"),
        (
            _non_covering_authorization,
            "CROSS_RECORD",
            "PCVP_EFFECT_AUTH_NOT_COVERING",
        ),
        (_scope_mismatch, "CROSS_RECORD", "PCVP_EFFECT_AUTH_SCOPE_MISMATCH"),
        (
            _safe_default_external,
            "SEMANTIC_POLICY",
            "PCVP_SAFE_DEFAULT_FORBIDDEN_EFFECT",
        ),
        (
            _critical_contradicted_continues,
            "SEMANTIC_POLICY",
            "PCVP_CONTRADICTED_CRITICAL_EFFECT_NOT_BLOCKED",
        ),
        (
            _unresolved_summary_effect,
            "CROSS_RECORD",
            "PCVP_SUMMARY_EFFECT_REF_UNRESOLVED",
        ),
        (
            _unresolved_summary_claim,
            "CROSS_RECORD",
            "PCVP_SUMMARY_CLAIM_REF_UNRESOLVED",
        ),
        (
            _summary_claim_not_dependency,
            "CROSS_RECORD",
            "PCVP_SUMMARY_CLAIM_NOT_EFFECT_DEPENDENCY",
        ),
        (_invalid_green, "SEMANTIC_POLICY", "PCVP_GREEN_PROJECTION_INVALID"),
        (_invalid_yellow, "SEMANTIC_POLICY", "PCVP_YELLOW_PROJECTION_INVALID"),
        (
            _red_nonblocked,
            "SEMANTIC_POLICY",
            "PCVP_RED_WITH_NON_BLOCKED_EFFECT",
        ),
        (
            _required_red_missing,
            "SEMANTIC_POLICY",
            "PCVP_REQUIRED_RED_PROJECTION_MISSING",
        ),
    ],
)
def test_complete_cross_record_and_semantic_mutation_matrix(
    mutation: Mutation, layer: str, code: str
) -> None:
    document = _document()
    mutation(document)
    result = _evaluate(document)
    assert result["accepted"] is False
    assert result["observed_layer"] == layer
    assert code in {item["code"] for item in result["diagnostics"]}


def test_arbitrary_valid_cardinalities_are_supported() -> None:
    document = _document()
    carrier = document["continuation_assurance"]
    extra_claim = copy.deepcopy(carrier["claims"][1])
    extra_claim["claim_id"] = "CLM-ARCH-EXTRA-VALID"
    carrier["claims"].append(extra_claim)
    carrier["effects"][0]["depends_on_claim_ids"].append(extra_claim["claim_id"])
    carrier["stage_summary"]["derived_from_claim_ids"].append(extra_claim["claim_id"])
    assert _evaluate(document) == {
        "observed_layer": "ACCEPT",
        "accepted": True,
        "diagnostics": [],
    }


def test_all_canonical_fixtures_match_pinned_declared_layers() -> None:
    checkout = os.environ.get("EV4_DECISION_KERNEL_CHECKOUT")
    if not checkout:
        pytest.skip("exact Decision Kernel checkout is a CI-only dependency")
    fixture_root = Path(checkout) / "kernel/pcvp/v1.0.0/bundle/05-FIXTURES"
    index = yaml.safe_load((fixture_root / "fixture-index.yaml").read_text("utf-8"))
    suite = index["fixture_suite"]
    observed = {"accepted": 0, "rejected": 0}

    for entry in suite["valid"]:
        document = json.loads((fixture_root / entry["file"]).read_text("utf-8"))
        result = _evaluate(document)
        assert result["accepted"] is True, (entry, result)
        assert result["observed_layer"] == "ACCEPT"
        observed["accepted"] += 1

    for entry in suite["invalid"]:
        document = json.loads((fixture_root / entry["file"]).read_text("utf-8"))
        result = _evaluate(document)
        assert result["accepted"] is False, (entry, result)
        assert result["observed_layer"] == entry["layer"], (entry, result)
        observed["rejected"] += 1

    assert observed == {"accepted": 8, "rejected": 10}


def test_exact_project_gate_consumer_accepts_genuine_carrier_losslessly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout = os.environ.get("EV4_PROJECT_GATE_CHECKOUT")
    if not checkout:
        pytest.skip("exact Project Gate checkout is a CI-only dependency")
    carrier = _capture_genuine_runtime_carrier(monkeypatch)
    source = str(Path(checkout) / "src")
    sys.path.insert(0, source)
    try:
        module = importlib.import_module("ev4_transition.pcvp_carrier")
        artifact = {
            "producer": {"stage": "architect"},
            "continuation_assurance": copy.deepcopy(carrier),
        }
        projection, diagnostics = module.inspect_optional_pcvp_carrier(
            artifact, checkout
        )
    finally:
        sys.path.remove(source)
    assert diagnostics == []
    assert projection["status"] == "validated"
    assert projection["source_stage"] == "ARCHITECT"
    assert projection["carrier"] == {"continuation_assurance": carrier}


def test_exact_ce_consumer_accepts_genuine_carrier_without_upgrade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout = os.environ.get("EV4_CE_CHECKOUT")
    if not checkout:
        pytest.skip("exact CE checkout is a CI-only dependency")
    carrier = _capture_genuine_runtime_carrier(monkeypatch)
    path = Path(checkout) / "validator/pcvp_carrier.py"
    spec = importlib.util.spec_from_file_location("_exact_ce_pcvp_carrier", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    artifact = {"continuation_assurance": copy.deepcopy(carrier)}
    projection, diagnostics = module.inspect_optional_pcvp_carrier(artifact, checkout)
    assert diagnostics == []
    assert projection["status"] == "validated"
    assert projection["source_stage"] == "ARCHITECT"
    assert projection["carrier"] == {"continuation_assurance": carrier}
    downstream = projection["carrier"]["continuation_assurance"]["claims"][1]
    assert downstream["verification_state"] == "UNVERIFIED"
