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

import architect_conversational_stage_output as conversational
import architect_css_target_validation as shared
import architect_payload_semantic_validator as semantic
import architect_quality_runtime as runtime
import architect_runtime_payload_assembler as assembler
from architect_project_gate_exporter import base

PREFINAL_DIR = REPO_ROOT / "fixtures/conversational-run/valid/minimal-complete-run"
TERMINAL_PATH = REPO_ROOT / "fixtures/conversational-run/valid/terminal/project-gate-export.json"


class FixtureGitProvider:
    def provenance(self, root: Path):
        return base.GitProvenance(
            "rezahh107/EV4-Architect-Repo", "fixture-css", "8" * 40
        )


def outputs() -> list[dict]:
    return [
        *conversational.load_output_files(PREFINAL_DIR, root=REPO_ROOT),
        json.loads(TERMINAL_PATH.read_text(encoding="utf-8")),
    ]


def context() -> runtime.RunContext:
    return runtime.RunContext(source_kind="fixture")


def specified_css(content: dict, targets: list[str | None]) -> None:
    content["scoped_css_intent"] = {
        "decision": "specified",
        "reason": "Scoped CSS is needed for an approved node.",
        "css_need_map": [
            {
                "css_need_id": f"css-{index}",
                **({"target_node_id": target} if target is not None else {}),
                "allowed_selector_scope": "selected_class",
                "purpose": "Preserve the approved visual intent.",
                "state": "proposed",
            }
            for index, target in enumerate(targets)
        ],
    }
    content["styling_decision"] = {
        "selected_option": "scoped class CSS",
        "rejected_options": ["global CSS", "CSS-created meaningful content"],
    }


def payload_with_valid_css() -> dict:
    items = outputs()
    specified_css(items[8]["canonical_content"], ["node-content"])
    outcome = runtime.evaluate_run(
        items,
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
    )
    assert outcome["status"] == "valid", outcome["errors"]
    return outcome["results"][-1]["project_gate_export"]["runtime_issued_payload"]


def codes(result: dict) -> list[str]:
    return [item["code"] for item in result["diagnostics"]]


def test_both_layers_use_the_same_shared_operation() -> None:
    assert assembler.validate_css_target_references is shared.validate_css_target_references
    assert semantic.validate_css_target_references is shared.validate_css_target_references


def test_valid_target_passes_and_payload_is_unchanged() -> None:
    payload = payload_with_valid_css()
    before = copy.deepcopy(payload)
    assert shared.validate_css_target_references(payload) == []
    result = semantic.ArchitectPayloadValidator(REPO_ROOT).validate_value(payload)
    assert result["status"] == "valid", result["diagnostics"]
    assert payload == before


@pytest.mark.parametrize(
    "target, expected",
    [
        (None, "PAYLOAD_CSS_TARGET_REQUIRED"),
        ("", "PAYLOAD_CSS_TARGET_REQUIRED"),
        ("missing-node", "PAYLOAD_CSS_TARGET_UNKNOWN"),
    ],
)
def test_semantic_validator_rejects_missing_empty_and_unknown_target(target, expected) -> None:
    payload = payload_with_valid_css()
    need = payload["architect_intent"]["scoped_css_intent"]["css_need_map"][0]
    if target is None:
        need.pop("target_node_id")
    else:
        need["target_node_id"] = target
    result = semantic.ArchitectPayloadValidator(REPO_ROOT).validate_value(payload)
    assert result["status"] == "invalid"
    assert expected in codes(result)


def test_assembler_rejects_unknown_target_before_payload_emission() -> None:
    items = outputs()
    specified_css(items[8]["canonical_content"], ["missing-node"])
    outcome = runtime.evaluate_run(
        items,
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
    )
    assert outcome["status"] == "invalid"
    assert any("PAYLOAD_CSS_TARGET_UNKNOWN" in error for error in outcome["errors"])
    assert outcome["results"][-1]["project_gate_export"] is None


def test_disconnected_payload_node_is_not_an_approved_css_target() -> None:
    payload = payload_with_valid_css()
    payload["approved_structure_model"]["structure_nodes"].append(
        {
            "node_id": "disconnected",
            "parent_node_id": None,
            "node_kind": "content_group",
            "role": "editable_content",
            "hierarchy_path": ["disconnected"],
            "evidence_refs": ["runtime-stage-build-tree"],
            "intent_refs": [],
            "children": [],
        }
    )
    payload["architect_intent"]["scoped_css_intent"]["css_need_map"][0][
        "target_node_id"
    ] = "disconnected"
    result = semantic.ArchitectPayloadValidator(REPO_ROOT).validate_value(payload)
    assert result["status"] == "invalid"
    assert "PAYLOAD_CSS_TARGET_UNKNOWN" in codes(result)


def test_rejected_raw_build_tree_never_produces_css_payload() -> None:
    items = outputs()
    items[7]["canonical_content"]["nodes"].append(
        {"id": "disconnected", "role": "editable_content", "children": []}
    )
    specified_css(items[8]["canonical_content"], ["disconnected"])
    outcome = runtime.evaluate_run(
        items,
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
    )
    assert outcome["status"] == "invalid"
    assert outcome["stages_visited"][-1] == "/build-tree"
    assert not any(item.get("project_gate_export") for item in outcome["results"])


def test_multiple_css_diagnostics_are_deterministically_ordered() -> None:
    payload = payload_with_valid_css()
    payload["architect_intent"]["scoped_css_intent"]["css_need_map"] = [
        {
            "css_need_id": "css-0",
            "target_node_id": "z-missing",
            "allowed_selector_scope": "selected_class",
            "purpose": "A",
            "state": "proposed",
            "evidence_refs": ["runtime-stage-implementation"],
        },
        {
            "css_need_id": "css-1",
            "target_node_id": "a-missing",
            "allowed_selector_scope": "selected_class",
            "purpose": "B",
            "state": "proposed",
            "evidence_refs": ["runtime-stage-implementation"],
        },
    ]
    diagnostics = shared.validate_css_target_references(payload)
    assert [item.path for item in diagnostics] == sorted(item.path for item in diagnostics)
    assert [item.code for item in diagnostics] == [
        "PAYLOAD_CSS_TARGET_UNKNOWN",
        "PAYLOAD_CSS_TARGET_UNKNOWN",
    ]
