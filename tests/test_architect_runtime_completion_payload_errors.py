from __future__ import annotations

import copy
import importlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import architect_conversational_stage_output as conversational
import architect_quality_runtime as runtime
import architect_runtime_payload_assembler as assembler
from architect_project_gate_exporter import base
from architect_runtime_errors import PayloadDerivationError, StageOutputValidationError

PREFINAL_DIR = REPO_ROOT / "fixtures/conversational-run/valid/minimal-complete-run"
TERMINAL_PATH = REPO_ROOT / "fixtures/conversational-run/valid/terminal/project-gate-export.json"


class FixtureGitProvider:
    def provenance(self, root: Path):
        assert root == REPO_ROOT
        return base.GitProvenance(
            "rezahh107/EV4-Architect-Repo", "fixture-exact-head", "7" * 40
        )


def all_outputs() -> list[dict]:
    return [
        *conversational.load_output_files(PREFINAL_DIR, root=REPO_ROOT),
        json.loads(TERMINAL_PATH.read_text(encoding="utf-8")),
    ]


def context(kind: str = "fixture") -> runtime.RunContext:
    return runtime.RunContext(source_kind=kind)


def evaluate_prefix(items: list[dict], count: int, *, kind: str = "fixture"):
    state = runtime.initial_run_state(items[0]["run_id"], root=REPO_ROOT)
    results = []
    for output in items[:count]:
        result, state = runtime.evaluate_stage(
            output["stage_id"],
            output,
            state,
            root=REPO_ROOT,
            run_context=context(kind),
            git_provider=FixtureGitProvider(),
        )
        assert result["stage_status"] == "pass", result["blocking_issues"]
        results.append(result)
    return results, state


def evaluate_full(items: list[dict] | None = None, *, kind: str = "fixture"):
    return runtime.evaluate_run(
        items or all_outputs(),
        root=REPO_ROOT,
        run_context=context(kind),
        git_provider=FixtureGitProvider(),
    )


def _resolve(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    while "$ref" in node:
        reference = node["$ref"]
        assert reference.startswith("#/$defs/")
        node = schema["$defs"][reference.removeprefix("#/$defs/")]
    return node


def _required_paths(
    schema: dict[str, Any], node: dict[str, Any], prefix: str
) -> set[str]:
    node = _resolve(schema, node)
    result: set[str] = set()
    properties = node.get("properties", {})
    for key in node.get("required", []):
        path = f"{prefix}.{key}" if prefix else key
        result.add(path)
        child = _resolve(schema, properties[key])
        if child.get("type") == "array" and isinstance(child.get("items"), dict):
            item = _resolve(schema, child["items"])
            if item.get("type") == "object" or "properties" in item:
                result.update(_required_paths(schema, item, path + "[]"))
        elif child.get("type") == "object" or "properties" in child:
            result.update(_required_paths(schema, child, path))
    return result


def test_runtime_interface_identity_is_exact() -> None:
    assert runtime.RUNTIME_INTERFACE_ID == "ev4-architect-quality-runtime@2.0.0"


def test_every_passing_stage_gets_the_truthful_completion_class() -> None:
    outcome = evaluate_full()
    assert outcome["status"] == "valid", outcome["errors"]
    reasoning_stages = importlib.import_module(
        "architect_stage_claim_guard"
    ).REASONING_STAGES
    for result in outcome["results"]:
        expected = (
            "reasoning_complete"
            if result["stage_id"] in reasoning_stages
            else "validated_pass"
        )
        assert result["stage_status"] == "pass"
        assert result["completion_class"] == expected


@pytest.mark.parametrize("status_kind", ["blocked", "needs_input"])
@pytest.mark.parametrize("stage_index", range(12))
def test_unsuccessful_stage_never_emits_a_success_completion_class(
    stage_index: int, status_kind: str
) -> None:
    items = all_outputs()
    _, state = evaluate_prefix(items, stage_index)
    candidate = copy.deepcopy(items[stage_index])
    candidate["blockers"] = [
        {
            "issue_id": (
                "TEST_USER_INPUT" if status_kind == "needs_input" else "TEST_BLOCK"
            ),
            "reason": "Adversarial unsuccessful Stage.",
            "repair_stage": candidate["stage_id"],
            "kind": "user_input" if status_kind == "needs_input" else "quality",
        }
    ]
    result, next_state = runtime.evaluate_stage(
        candidate["stage_id"],
        candidate,
        state,
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
    )
    assert result["stage_status"] == status_kind
    assert "completion_class" not in result
    assert next_state == state


def test_stage_result_schema_rejects_success_class_on_blocked_and_needs_input() -> None:
    result, _ = evaluate_prefix(all_outputs(), 1)
    schema = json.loads(
        (
            REPO_ROOT / "schemas/ev4-architect-stage-result.v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    for status in ("blocked", "needs_input"):
        mutated = copy.deepcopy(result[0])
        mutated["stage_status"] = status
        assert list(validator.iter_errors(mutated))
    historical_pass = copy.deepcopy(result[0])
    historical_pass.pop("completion_class")
    assert list(validator.iter_errors(historical_pass)) == []


def test_payload_lineage_rejects_failed_stage_with_success_completion() -> None:
    outcome = evaluate_full()
    state = copy.deepcopy(outcome["run_state"])
    state["derived_stage_results"][0]["stage_status"] = "blocked"
    state["derived_stage_results"][0]["completion_class"] = "reasoning_complete"
    with pytest.raises(PayloadDerivationError, match="PAYLOAD_LINEAGE_FALSE_COMPLETION"):
        assembler.assemble_architect_stage_payload(
            run_state=state, source_kind="fixture"
        )


def test_structural_invalidity_is_typed_and_has_no_stage_result() -> None:
    item = copy.deepcopy(all_outputs()[0])
    item.pop("blockers")
    state = runtime.initial_run_state(item["run_id"], root=REPO_ROOT)
    with pytest.raises(StageOutputValidationError) as caught:
        runtime.evaluate_stage(
            "/intake", item, state, root=REPO_ROOT, run_context=context()
        )
    assert any(
        diagnostic.code == "RUNTIME_STAGE_OUTPUT_SCHEMA_INVALID"
        for diagnostic in caught.value.diagnostics
    )
    assert state["completed_stages"] == []


def test_evaluate_run_structures_only_expected_domain_failures() -> None:
    outcome = runtime.evaluate_run(
        [],
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
    )
    assert outcome["status"] == "invalid"
    assert any("RUNTIME_RUN_EMPTY" in error for error in outcome["errors"])


@pytest.mark.parametrize(
    "target",
    ["stage_predicate", "assembler", "payload_validator", "exporter", "hash_verifier"],
)
def test_unexpected_programming_defects_propagate(
    monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    defect = RuntimeError("synthetic programming defect")
    items = all_outputs()
    if target == "stage_predicate":
        guard = importlib.import_module("architect_stage_claim_guard")
        monkeypatch.setattr(
            guard,
            "evaluate_claims",
            lambda **kwargs: (_ for _ in ()).throw(defect),
        )
        state = runtime.initial_run_state(items[0]["run_id"], root=REPO_ROOT)
        with pytest.raises(RuntimeError, match="synthetic programming defect"):
            runtime.evaluate_stage(
                "/intake", items[0], state, root=REPO_ROOT, run_context=context()
            )
        return

    _, state = evaluate_prefix(items, 11)
    if target == "assembler":
        module = importlib.import_module("architect_runtime_payload_assembler")
        monkeypatch.setattr(
            module,
            "assemble_architect_stage_payload",
            lambda **kwargs: (_ for _ in ()).throw(defect),
        )
    elif target == "payload_validator":
        module = importlib.import_module("architect_runtime_project_gate")
        monkeypatch.setattr(
            module,
            "validate_payload",
            lambda *args, **kwargs: (_ for _ in ()).throw(defect),
        )
    elif target == "exporter":
        module = importlib.import_module("architect_project_gate_exporter.contracts")
        monkeypatch.setattr(
            module,
            "build_export",
            lambda *args, **kwargs: (_ for _ in ()).throw(defect),
        )
    else:
        module = importlib.import_module("architect_project_gate_exporter.contracts")
        monkeypatch.setattr(
            module,
            "verify_hashes",
            lambda *args, **kwargs: (_ for _ in ()).throw(defect),
        )
    with pytest.raises(RuntimeError, match="synthetic programming defect"):
        runtime.evaluate_stage(
            "/project-gate-export",
            items[11],
            state,
            root=REPO_ROOT,
            run_context=context(),
            git_provider=FixtureGitProvider(),
        )


def test_required_implementation_intent_blocks_at_owning_stage() -> None:
    items = all_outputs()
    _, state = evaluate_prefix(items, 8)
    for field in ("class_intent", "class_application_map", "element_mapping"):
        candidate = copy.deepcopy(items[8])
        candidate["canonical_content"].pop(field)
        result, next_state = runtime.evaluate_stage(
            "/implementation",
            candidate,
            state,
            root=REPO_ROOT,
            run_context=context(),
        )
        assert result["stage_status"] == "blocked"
        assert "completion_class" not in result
        assert any(
            item["issue_id"] == "RUNTIME_STAGE_PREDICATE_FAILED"
            for item in result["blocking_issues"]
        )
        assert next_state == state


@pytest.mark.parametrize(
    "field, unresolved_id",
    [
        ("asset_intent", "U-payload-asset-intent"),
        ("scoped_css_intent", "U-payload-css-intent"),
        ("dynamic_loop_intent", "U-payload-dynamic-loop-intent"),
        ("responsive_risk_seeds", "U-payload-project-responsive-risk"),
        ("media_decision", "U-payload-media-decision"),
        ("styling_decision", "U-payload-styling-decision"),
    ],
)
def test_missing_conditional_intent_never_creates_a_false_complete_payload(
    field: str, unresolved_id: str
) -> None:
    items = all_outputs()
    items[8]["canonical_content"].pop(field)
    outcome = evaluate_full(items, kind="live_conversation")
    assert outcome["status"] == "valid", outcome["errors"]
    export = outcome["results"][-1]["project_gate_export"]
    payload = export["runtime_issued_payload"]
    assert payload["payload_status"] == "insufficient_evidence"
    assert any(
        item["unresolved_id"] == unresolved_id
        for item in payload["unresolved_evidence"]
    )
    assert export["functional_eligibility"]["would_allow"] is False
    assert export["handoff_allowed"] is False
    assert "architect-section" not in json.dumps(payload)


def test_explicit_empty_decisions_are_distinct_from_omission() -> None:
    complete = evaluate_full(kind="live_conversation")
    payload = complete["results"][-1]["project_gate_export"][
        "runtime_issued_payload"
    ]
    assert payload["payload_status"] == "complete"
    assert payload["architect_intent"]["asset_intent"]["asset_requirements"] == []
    assert payload["architect_intent"]["scoped_css_intent"]["css_allowed"] is False
    assert (
        payload["architect_intent"]["dynamic_loop_intent"]["status"]
        == "not_applicable"
    )
    assert not any(
        item["unresolved_id"].startswith("U-payload-")
        for item in payload["unresolved_evidence"]
    )
    assert complete["results"][-1]["project_gate_export"]["handoff_allowed"] is True


@pytest.mark.parametrize(
    "mutation, expected_code",
    [
        (
            lambda content: content.__setitem__(
                "asset_intent",
                {
                    "decision": "specified",
                    "reason": "One project asset is required.",
                    "asset_requirements": [{"asset_id": "hero-image"}],
                },
            ),
            "PAYLOAD_ASSET_REQUIREMENT_INVALID",
        ),
        (
            lambda content: content.__setitem__(
                "scoped_css_intent",
                {
                    "decision": "specified",
                    "reason": "One scoped CSS need is required.",
                    "css_need_map": [
                        {
                            "css_need_id": "css-1",
                            "target_node_id": "node-root",
                            "allowed_selector_scope": "selected_class",
                            "purpose": "Maintain the selected geometry.",
                        }
                    ],
                },
            ),
            "PAYLOAD_CSS_NEED_INVALID",
        ),
        (
            lambda content: content.__setitem__(
                "responsive_risk_seeds",
                [
                    {
                        "risk_id": "risk-1",
                        "risk_type": "mobile_behavior_not_proven",
                        "description": "Mobile behavior is unverified.",
                    }
                ],
            ),
            "PAYLOAD_RESPONSIVE_RISK_INVALID",
        ),
    ],
)
def test_specified_conditional_items_require_explicit_project_fields(
    mutation, expected_code: str
) -> None:
    items = all_outputs()
    mutation(items[8]["canonical_content"])
    outcome = evaluate_full(items, kind="live_conversation")
    assert outcome["status"] == "invalid"
    assert any(expected_code in error for error in outcome["errors"])
    assert outcome["results"][-1]["project_gate_export"] is None


def test_structure_hierarchy_and_intent_refs_are_derived_from_real_sources() -> None:
    outcome = evaluate_full(kind="fixture")
    payload = outcome["results"][-1]["project_gate_export"][
        "runtime_issued_payload"
    ]
    nodes = {
        item["node_id"]: item
        for item in payload["approved_structure_model"]["structure_nodes"]
    }
    assert nodes["node-content"]["hierarchy_path"] == [
        "node-root",
        "node-wrapper",
        "node-content",
    ]
    assert nodes["node-content"]["intent_refs"] == ["section-content"]
    assert nodes["node-connector"]["intent_refs"] == ["section-connector"]


def test_fixture_complete_run_is_functionally_eligible_but_never_handoff_allowed() -> None:
    outcome = evaluate_full(kind="fixture")
    export = outcome["results"][-1]["project_gate_export"]
    assert export["runtime_issued_payload"]["synthetic"] is True
    assert export["functional_eligibility"] == {"would_allow": True, "blockers": []}
    assert export["handoff_allowed"] is False


def test_payload_derivation_rules_cover_all_required_governed_surfaces() -> None:
    schema = json.loads(
        (
            REPO_ROOT / "schemas/ev4-architect-stage-payload.v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    required = set(schema["required"])
    for key in (
        "architecture_identity",
        "approved_structure_model",
        "architect_intent",
        "kernel_decision_records",
    ):
        property_schema = _resolve(schema, schema["properties"][key])
        if property_schema.get("type") == "array":
            required.update(
                _required_paths(schema, property_schema["items"], key + "[]")
            )
        else:
            required.update(_required_paths(schema, property_schema, key))
    assert required <= set(assembler.PAYLOAD_DERIVATION_RULES)
    assert set(assembler.PAYLOAD_DERIVATION_RULES.values()) <= assembler.DERIVATION_KINDS
