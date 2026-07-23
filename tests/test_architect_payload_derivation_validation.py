from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import architect_runtime_payload_assembler as assembler
from architect_payload_derivation_validation import (
    required_schema_paths,
    validate_payload_derivation_rules,
)
from architect_runtime_errors import PayloadDerivationError

SCHEMA_PATH = REPO_ROOT / "schemas/ev4-architect-stage-payload.v1.schema.json"


def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def diagnostics(value: dict, rules: dict[str, str] | None = None):
    with pytest.raises(PayloadDerivationError) as caught:
        validate_payload_derivation_rules(
            value,
            rules or assembler.REQUIRED_PAYLOAD_DERIVATION_RULES,
            assembler.DERIVATION_KINDS,
        )
    return [(item.code, item.path) for item in caught.value.diagnostics]


def test_root_recursive_required_paths_exactly_match_classifications() -> None:
    required = required_schema_paths(schema())
    assert required == set(assembler.REQUIRED_PAYLOAD_DERIVATION_RULES)
    assert assembler.validate_derivation_schema(schema()) == required


def test_required_path_traversal_reaches_all_root_containers() -> None:
    required = required_schema_paths(schema())
    expected = {
        "payload_identity.producer",
        "source_stage_lineage[].stage",
        "architecture_identity.decision_source.stage",
        "approved_structure_model.structure_nodes[].role",
        "architect_intent.class_intent.class_application_map[].class_name",
        "kernel_decision_records[].decision_family",
        "evidence_register[].source_ref.reference",
        "unresolved_evidence[].blocks",
        "boundary_assertions.production_ready",
        "validation_contract.rules",
        "extension_records[].data",
    }
    assert expected <= required


def test_important_derivation_ownership_is_explicit() -> None:
    rules = assembler.REQUIRED_PAYLOAD_DERIVATION_RULES
    for path in (
        "schema_id",
        "schema_version",
        "owner_repository",
        "forbidden_work",
        "boundary_assertions",
        "validation_contract",
    ):
        assert rules[path] == assembler.POLICY_CONSTANT
    for path in (
        "payload_status",
        "synthetic",
        "payload_identity",
        "source_stage_lineage",
        "evidence_register",
        "unresolved_evidence",
        "extension_records",
        "architecture_identity.selected_candidate_id",
        "architecture_identity.selected_candidate_locked",
    ):
        assert rules[path] == assembler.RUNTIME_DERIVED
    for path in (
        "architecture_identity.architecture_family",
        "approved_structure_model.root_node_id",
        "approved_structure_model.structure_nodes[].role",
        "architect_intent.class_intent",
        "architect_intent.asset_intent.asset_requirements",
        "architect_intent.scoped_css_intent.css_need_map",
        "architect_intent.dynamic_loop_intent.status",
        "architect_intent.responsive_risk_seeds[].risk_type",
    ):
        assert rules[path] == assembler.STAGE_DERIVED
    for path in (
        "architect_intent.asset_intent",
        "architect_intent.scoped_css_intent",
        "architect_intent.dynamic_loop_intent",
        "architect_intent.responsive_risk_seeds",
    ):
        assert rules[path] == assembler.EXPLICIT_UNRESOLVED


def test_new_required_root_field_is_unclassified() -> None:
    value = schema()
    value["properties"]["new_required_root"] = {"type": "string"}
    value["required"].append("new_required_root")
    assert diagnostics(value) == [
        (
            "PAYLOAD_DERIVATION_REQUIRED_PATH_UNCLASSIFIED",
            "new_required_root",
        )
    ]


def test_new_required_nested_object_field_is_unclassified() -> None:
    value = schema()
    target = value["$defs"]["payload_identity"]
    target["properties"]["new_nested"] = {"type": "string"}
    target["required"].append("new_nested")
    assert diagnostics(value) == [
        (
            "PAYLOAD_DERIVATION_REQUIRED_PATH_UNCLASSIFIED",
            "payload_identity.new_nested",
        )
    ]


def test_new_required_array_item_field_is_unclassified() -> None:
    value = schema()
    target = value["$defs"]["evidence_record"]
    target["properties"]["new_item_field"] = {"type": "string"}
    target["required"].append("new_item_field")
    assert diagnostics(value) == [
        (
            "PAYLOAD_DERIVATION_REQUIRED_PATH_UNCLASSIFIED",
            "evidence_register[].new_item_field",
        )
    ]


def test_removed_required_field_makes_classification_stale() -> None:
    value = schema()
    value["$defs"]["payload_identity"]["required"].remove("created_by")
    assert diagnostics(value) == [
        (
            "PAYLOAD_DERIVATION_CLASSIFICATION_PATH_UNKNOWN",
            "payload_identity.created_by",
        )
    ]


def test_renamed_required_nested_field_reports_sorted_missing_and_stale() -> None:
    value = schema()
    target = value["$defs"]["payload_identity"]
    target["properties"]["creator"] = target["properties"].pop("created_by")
    index = target["required"].index("created_by")
    target["required"][index] = "creator"
    assert diagnostics(value) == [
        (
            "PAYLOAD_DERIVATION_REQUIRED_PATH_UNCLASSIFIED",
            "payload_identity.creator",
        ),
        (
            "PAYLOAD_DERIVATION_CLASSIFICATION_PATH_UNKNOWN",
            "payload_identity.created_by",
        ),
    ]


def test_invalid_classification_kind_is_rejected() -> None:
    value = schema()
    rules = copy.deepcopy(assembler.REQUIRED_PAYLOAD_DERIVATION_RULES)
    rules["schema_id"] = "UNKNOWN_KIND"
    assert diagnostics(value, rules) == [
        (
            "PAYLOAD_DERIVATION_CLASSIFICATION_KIND_INVALID",
            "schema_id",
        )
    ]


def test_multiple_diagnostics_are_deterministically_sorted() -> None:
    value = schema()
    value["properties"]["z_required"] = {"type": "string"}
    value["properties"]["a_required"] = {"type": "string"}
    value["required"].extend(["z_required", "a_required"])
    assert diagnostics(value) == [
        (
            "PAYLOAD_DERIVATION_REQUIRED_PATH_UNCLASSIFIED",
            "a_required",
        ),
        (
            "PAYLOAD_DERIVATION_REQUIRED_PATH_UNCLASSIFIED",
            "z_required",
        ),
    ]
