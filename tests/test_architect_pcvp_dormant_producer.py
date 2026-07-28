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


def _capture_runtime_export(
    monkeypatch: pytest.MonkeyPatch,
    *,
    source_kind: str = "fixture",
) -> dict:
    """Capture the genuine terminal Runtime export without altering construction."""
    captured: list[dict] = []
    real_build = contracts.build_export

    def capture_unchanged(*args, **kwargs):
        export, hashes = real_build(*args, **kwargs)
        captured.append(copy.deepcopy(export))
        return export, hashes

    monkeypatch.setattr(contracts, "build_export", capture_unchanged)
    replay_kwargs = {}
    if source_kind != "live_conversation":
        replay_kwargs["git_provider"] = _legacy.FixtureGitProvider()
    outcome = runtime._replay_outcome(
        _legacy.full_outputs(),
        run_context=_legacy.context(source_kind),
        repository_root=ROOT,
        require_terminal=True,
        **replay_kwargs,
    )
    assert outcome.status == "valid", outcome.to_public()["errors"]
    assert len(captured) == 1
    return captured[0]


def test_resources_are_exactly_pinned_and_edge_activation_is_bounded() -> None:
    result = pcvp.verify_pcvp_resources(ROOT)
    assert result["producer_emission"] is True
    assert result["canonical_commit"] == "069a50fa243b01fa578a7c1bcb8864d9e796d34b"
    assert result["activation_commit"] == "ad0e7235929d7f6d847724f6b4d1a6a3c57453db"
    assert result["activation_id"] == "EV4-PCVP-ACT-ARCH-PG-CE-20260728-R1"
    assert result["activation_effect"] == "ARCHITECT_TO_PROJECT_GATE_TO_CE"
    assert result["disabled_edges"] == [
        "CE_TO_BUILDER",
        "BUILDER_TO_RESPONSIVE",
        "RESPONSIVE_TO_FINAL",
    ]
    assert result["full_rollout_authorized"] is False
    assert len(result["resource_hashes"]) == 6


def test_exact_decision_kernel_activation_authority_is_pinned_and_bounded() -> None:
    checkout = os.environ.get("EV4_DECISION_KERNEL_ACTIVATION_CHECKOUT")
    if not checkout:
        pytest.skip("exact Decision Kernel activation checkout is a CI-only dependency")
    path = Path(checkout) / pcvp.ACTIVATION_PATH
    document = json.loads(path.read_text(encoding="utf-8"))
    pcvp._validate_activation_authority_document(document)
    assert document["activation_scope"]["enabled_edges"] == [
        "ARCHITECT_TO_PROJECT_GATE_TO_CE"
    ]
    assert document["runtime_authorization"] == {
        "architect_producer_emission": True,
        "architect_to_project_gate": True,
        "project_gate_to_ce": True,
        "ce_to_builder_emission": False,
        "builder_to_responsive_emission": False,
        "responsive_to_final_emission": False,
    }
    assert document["full_rollout_authorized"] is False


def test_supported_surface_exposes_no_authoritative_raw_fact_minting_api() -> None:
    assert "build_continuation_assurance" not in pcvp.__all__
    assert "_build_runtime_continuation_assurance" not in pcvp.__all__
    assert "attach_to_export_if_enabled" not in pcvp.__all__
    assert "PRODUCER_EMISSION_ENABLED" not in pcvp.__all__
    public_functions = {
        name: value
        for name in pcvp.__all__
        if inspect.isfunction(value := getattr(pcvp, name))
    }
    assert set(public_functions) == {"verify_pcvp_resources"}
    assert all(
        "canonical_payload_valid" not in inspect.signature(value).parameters
        for value in public_functions.values()
    )
    assert all(
        "handoff_allowed" not in inspect.signature(value).parameters
        for value in public_functions.values()
    )
    assert "repository_root" not in inspect.signature(
        pcvp._build_runtime_continuation_assurance
    ).parameters
    assert list(inspect.signature(contracts.build_export).parameters) == [
        "payload",
        "git",
        "run_id",
        "input_ref",
    ]


def test_runtime_authority_manifest_and_export_schema_include_active_pcvp_surface() -> None:
    manifest = json.loads(
        (ROOT / "manifests/architect-runtime-authority-manifest.v1.json").read_text(
            encoding="utf-8"
        )
    )
    schema = json.loads(
        (ROOT / "contracts/project-gate/producer-gate-export.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert "scripts/architect_pcvp_producer.py" in manifest["python_authority_paths"]
    assert manifest["consumer_notes"]["pcvp_activation_edge"] == (
        "ARCHITECT_TO_PROJECT_GATE_TO_CE"
    )
    assert manifest["consumer_notes"]["pcvp_activation_authority_commit"] == (
        "ad0e7235929d7f6d847724f6b4d1a6a3c57453db"
    )
    assert schema["additionalProperties"] is False
    assert "continuation_assurance" in schema["properties"]
    assert "continuation_assurance" not in schema["required"]


def test_exporter_uses_private_pcvp_builder_without_env_or_public_override() -> None:
    module_source = Path(contracts.__file__).read_text(encoding="utf-8")
    build_source = inspect.getsource(contracts.build_export)
    assert "import architect_pcvp_producer as pcvp" in module_source
    assert "pcvp._build_runtime_continuation_assurance" in build_source
    assert "os.environ" not in build_source
    assert "os.getenv" not in build_source
    assert 'if "continuation_assurance" in payload' in build_source
    assert "ARCH_EXPORT_CALLER_PCVP_CARRIER_FORBIDDEN" in build_source


def test_runtime_revalidates_payload_before_active_pcvp_attachment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    real_validate = contracts.validate_payload

    def counted(root: Path, payload: object) -> dict:
        nonlocal calls
        calls += 1
        return real_validate(root, payload)

    monkeypatch.setattr(contracts, "validate_payload", counted)
    export = _capture_runtime_export(monkeypatch, source_kind="fixture")
    assert calls == 1
    assert "continuation_assurance" in export


def test_synthetic_runtime_export_emits_valid_red_carrier_without_handoff_upgrade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    export = _capture_runtime_export(monkeypatch, source_kind="fixture")
    carrier = export["continuation_assurance"]
    assert export["handoff"]["allowed"] is False
    assert carrier["source_stage"] == "ARCHITECT"
    assert carrier["stage_summary"]["owner_projection"] == "RED"
    assert carrier["effects"][0]["continuation_state"] == "BLOCKED"
    assert carrier["claims"][1]["verification_state"] == "UNVERIFIED"
    contracts.validate_contracts(ROOT, export)
    assert _evaluate({"continuation_assurance": carrier}) == {
        "observed_layer": "ACCEPT",
        "accepted": True,
        "diagnostics": [],
    }


def test_live_runtime_export_emits_yellow_carrier_when_existing_handoff_allows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    export = _capture_runtime_export(monkeypatch, source_kind="live_conversation")
    carrier = export["continuation_assurance"]
    assert export["handoff"]["allowed"] is True
    assert carrier["stage_summary"]["owner_projection"] == "YELLOW"
    assert carrier["stage_summary"]["yellow_substate"] == "CONTINUATION_AVAILABLE"
    assert carrier["effects"][0]["continuation_state"] == "CONTINUE"
    assert carrier["claims"][1]["verification_state"] == "UNVERIFIED"
    contracts.validate_contracts(ROOT, export)


def test_private_carrier_is_deterministic_and_canonically_valid() -> None:
    carrier = _candidate()
    assert carrier == _candidate()
    assert carrier["policy_id"] == "EV4-PCVP"
    assert carrier["policy_version"] == "1.0.0"
    assert carrier["source_stage"] == "ARCHITECT"
    assert carrier["effects"][0]["continuation_state"] == "CONTINUE"
    assert carrier["stage_summary"]["owner_projection"] == "YELLOW"
    assert carrier["stage_summary"]["yellow_substate"] == "CONTINUATION_AVAILABLE"
    assert carrier["claims"][1]["verification_state"] == "UNVERIFIED"
    assert _evaluate({"continuation_assurance": carrier})["accepted"] is True


def test_copied_reconstructed_and_caller_augmented_payloads_remain_non_authorizing() -> None:
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


def test_private_runtime_builder_fails_closed_when_active_lock_drifts(tmp_path: Path) -> None:
    lock = json.loads((ROOT / pcvp.LOCK_PATH).read_text(encoding="utf-8"))
    lock["activation_authority"]["enabled_edges"] = ["CE_TO_BUILDER"]
    target = tmp_path / pcvp.LOCK_PATH
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(pcvp.PCVPProducerError):
        pcvp.verify_pcvp_resources(tmp_path)


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


def _unresolved_claim_dependency(document: dict) -> None:
    document["continuation_assurance"]["claims"][1]["dependency_refs"][0] = (
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
    claim = document["continuation_assurance"]["claims"][0]
    claim["verification_state"] = "CONTRADICTED"
    claim["lifecycle_state"] = "ACTIVE"
    claim["evidence_refs"] = []


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


def _invalid_green_critical(document: dict) -> None:
    carrier = document["continuation_assurance"]
    critical = carrier["claims"][0]
    critical["verification_state"] = "UNVERIFIED"
    critical["lifecycle_state"] = "ACTIVE"
    critical["evidence_refs"] = []
    carrier["stage_summary"]["owner_projection"] = "GREEN"
    carrier["stage_summary"]["yellow_substate"] = None


def _invalid_green_material_unverified(document: dict) -> None:
    carrier = document["continuation_assurance"]
    assert carrier["claims"][1]["criticality"] == "MATERIAL"
    assert carrier["claims"][1]["applicability_state"] == "APPLICABLE"
    assert carrier["claims"][1]["verification_state"] == "UNVERIFIED"
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
            _unresolved_claim_dependency,
            "CROSS_RECORD",
            "PCVP_CLAIM_DEPENDENCY_UNRESOLVED",
        ),
        (_unresolved_authorization, "CROSS_RECORD", "PCVP_EFFECT_AUTH_REF_UNRESOLVED"),
        (_inactive_authorization, "CROSS_RECORD", "PCVP_EFFECT_AUTH_NOT_ACTIVE"),
        (_non_covering_authorization, "CROSS_RECORD", "PCVP_EFFECT_AUTH_NOT_COVERING"),
        (_scope_mismatch, "CROSS_RECORD", "PCVP_EFFECT_AUTH_SCOPE_MISMATCH"),
        (_safe_default_external, "SEMANTIC_POLICY", "PCVP_SAFE_DEFAULT_FORBIDDEN_EFFECT"),
        (
            _critical_contradicted_continues,
            "SEMANTIC_POLICY",
            "PCVP_CONTRADICTED_CRITICAL_EFFECT_NOT_BLOCKED",
        ),
        (_unresolved_summary_effect, "CROSS_RECORD", "PCVP_SUMMARY_EFFECT_REF_UNRESOLVED"),
        (_unresolved_summary_claim, "CROSS_RECORD", "PCVP_SUMMARY_CLAIM_REF_UNRESOLVED"),
        (
            _summary_claim_not_dependency,
            "CROSS_RECORD",
            "PCVP_SUMMARY_CLAIM_NOT_EFFECT_DEPENDENCY",
        ),
        (_invalid_green_critical, "SEMANTIC_POLICY", "PCVP_GREEN_PROJECTION_INVALID"),
        (
            _invalid_green_material_unverified,
            "SEMANTIC_POLICY",
            "PCVP_GREEN_PROJECTION_INVALID",
        ),
        (_invalid_yellow, "SEMANTIC_POLICY", "PCVP_YELLOW_PROJECTION_INVALID"),
        (_red_nonblocked, "SEMANTIC_POLICY", "PCVP_RED_WITH_NON_BLOCKED_EFFECT"),
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


def test_valid_multi_claim_dependency_chain_is_accepted() -> None:
    document = _document()
    carrier = document["continuation_assurance"]
    extra_claim = copy.deepcopy(carrier["claims"][1])
    extra_claim["claim_id"] = "CLM-ARCH-EXTRA-VALID"
    extra_claim["dependency_refs"] = [carrier["claims"][1]["claim_id"]]
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
        pytest.skip("exact Decision Kernel bundle checkout is a CI-only dependency")
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


def _actual_live_runtime_export(monkeypatch: pytest.MonkeyPatch) -> dict:
    return _capture_runtime_export(monkeypatch, source_kind="live_conversation")


def test_exact_current_project_gate_accepts_actual_runtime_emission_losslessly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout = os.environ.get("EV4_PROJECT_GATE_CHECKOUT")
    kernel_checkout = os.environ.get("EV4_DECISION_KERNEL_CHECKOUT")
    if not checkout or not kernel_checkout:
        pytest.skip("exact Project Gate and Decision Kernel checkouts are CI-only dependencies")
    export = _actual_live_runtime_export(monkeypatch)
    source = str(Path(checkout) / "src")
    sys.path.insert(0, source)
    try:
        module = importlib.import_module("ev4_transition.pcvp_carrier")
        assert Path(module.__file__).resolve() == (
            Path(checkout) / "src/ev4_transition/pcvp_carrier.py"
        ).resolve()
        original = copy.deepcopy(export)
        projection, diagnostics = module.inspect_optional_pcvp_carrier(
            export,
            checkout,
            decision_kernel_repo=kernel_checkout,
            downstream_stage="CONSTRUCTABILITY_ENGINEER",
        )
    finally:
        sys.path.remove(source)
    assert export == original
    assert diagnostics == []
    assert projection["status"] == "validated"
    assert projection["source_stage"] == "ARCHITECT"
    assert projection["downstream_stage"] == "CONSTRUCTABILITY_ENGINEER"
    assert projection["carrier"] == {
        "continuation_assurance": export["continuation_assurance"]
    }


def test_exact_current_ce_accepts_actual_runtime_emission_without_upgrade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout = os.environ.get("EV4_CE_CHECKOUT")
    if not checkout:
        pytest.skip("exact CE checkout is a CI-only dependency")
    export = _actual_live_runtime_export(monkeypatch)
    path = Path(checkout) / "validator/pcvp_carrier.py"
    spec = importlib.util.spec_from_file_location("_exact_ce_pcvp_carrier", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    original = copy.deepcopy(export)
    projection, diagnostics = module.inspect_optional_pcvp_carrier(export, checkout)
    assert export == original
    assert diagnostics == []
    assert projection["status"] == "validated"
    assert projection["source_stage"] == "ARCHITECT"
    downstream = projection["carrier"]["continuation_assurance"]["claims"][1]
    assert downstream["verification_state"] == "UNVERIFIED"
    statement = downstream["statement"]
    assert "Builder execution" in statement
    assert "Responsive completion" in statement
    assert "production readiness" in statement
