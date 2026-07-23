from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import architect_conversational_stage_output as conversational
import architect_quality_runtime as runtime
from architect_build_tree_validation import (
    NODE_KIND_BY_ROLE,
    validate_canonical_build_tree,
)
from architect_runtime_errors import PayloadDerivationError

PREFINAL_DIR = REPO_ROOT / "fixtures/conversational-run/valid/minimal-complete-run"


def valid_tree() -> dict:
    return {
        "candidate_id": "ARCH-FAM-C",
        "root": "root",
        "nodes": [
            {
                "id": "root",
                "role": "section_root",
                "children": ["group", "decoration"],
            },
            {
                "id": "group",
                "role": "normal_flow_group",
                "children": ["content"],
            },
            {"id": "content", "role": "editable_content", "children": []},
            {
                "id": "decoration",
                "role": "contained_decoration_layer",
                "children": [],
            },
        ],
    }


def code_for(value: object) -> str:
    with pytest.raises(PayloadDerivationError) as caught:
        validate_canonical_build_tree(value)
    return caught.value.diagnostics[0].code


def test_valid_single_root_tree() -> None:
    result = validate_canonical_build_tree(
        {
            "root": "root",
            "nodes": [
                {"id": "root", "role": "section_root", "children": []}
            ],
        }
    )
    assert result.root_id == "root"
    assert result.parent_by_child == {}
    assert result.hierarchy_paths == {"root": ("root",)}
    assert result.node_kind_by_id == {"root": "section_root"}


def test_valid_multi_level_tree_normalizes_graph_and_role_mapping() -> None:
    result = validate_canonical_build_tree(valid_tree())
    assert result.parent_by_child == {
        "group": "root",
        "decoration": "root",
        "content": "group",
    }
    assert result.hierarchy_paths == {
        "root": ("root",),
        "group": ("root", "group"),
        "content": ("root", "group", "content"),
        "decoration": ("root", "decoration"),
    }
    assert result.node_kind_by_id == {
        "root": "section_root",
        "group": "structural_container",
        "content": "content_group",
        "decoration": "decoration_layer",
    }
    assert result.node_kind_by_id == {
        node_id: NODE_KIND_BY_ROLE[node["role"]]
        for node_id, node in result.node_by_id.items()
    }


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (
            lambda value: value["nodes"].append(copy.deepcopy(value["nodes"][0])),
            "BUILD_TREE_NODE_ID_DUPLICATE",
        ),
        (
            lambda value: value.__setitem__("root", "missing"),
            "BUILD_TREE_ROOT_UNKNOWN",
        ),
        (
            lambda value: value["nodes"][0]["children"].append("missing"),
            "BUILD_TREE_CHILD_UNKNOWN",
        ),
        (
            lambda value: value["nodes"][0].__setitem__(
                "children", ["group", "group"]
            ),
            "BUILD_TREE_CHILD_DUPLICATE",
        ),
        (
            lambda value: value["nodes"][1]["children"].append("group"),
            "BUILD_TREE_SELF_CYCLE",
        ),
        (
            lambda value: value["nodes"].extend(
                [
                    {"id": "cycle-a", "role": "normal_flow_group", "children": ["cycle-b"]},
                    {"id": "cycle-b", "role": "normal_flow_group", "children": ["cycle-a"]},
                ]
            ),
            "BUILD_TREE_CYCLE",
        ),
        (
            lambda value: value["nodes"].extend(
                [
                    {"id": "cycle-a", "role": "normal_flow_group", "children": ["cycle-b"]},
                    {"id": "cycle-b", "role": "normal_flow_group", "children": ["cycle-c"]},
                    {"id": "cycle-c", "role": "normal_flow_group", "children": ["cycle-a"]},
                ]
            ),
            "BUILD_TREE_CYCLE",
        ),
        (
            lambda value: value["nodes"][2]["children"].append("group"),
            "BUILD_TREE_MULTIPLE_PARENTS",
        ),
        (
            lambda value: value["nodes"].append(
                {"id": "orphan", "role": "normal_flow_group", "children": []}
            ),
            "BUILD_TREE_NON_ROOT_PARENT_REQUIRED",
        ),
        (
            lambda value: value["nodes"].extend(
                [
                    {"id": "detached", "role": "normal_flow_group", "children": ["leaf"]},
                    {"id": "leaf", "role": "editable_content", "children": []},
                ]
            ),
            "BUILD_TREE_NON_ROOT_PARENT_REQUIRED",
        ),
        (
            lambda value: value["nodes"][2]["children"].append("root"),
            "BUILD_TREE_ROOT_HAS_PARENT",
        ),
        (
            lambda value: value["nodes"][2].pop("children"),
            "BUILD_TREE_CHILDREN_ARRAY_REQUIRED",
        ),
        (
            lambda value: value["nodes"][2].__setitem__("children", "none"),
            "BUILD_TREE_CHILDREN_ARRAY_REQUIRED",
        ),
        (
            lambda value: value["nodes"][2].__setitem__("role", "unknown_role"),
            "BUILD_TREE_ROLE_UNSUPPORTED",
        ),
        (
            lambda value: value["nodes"][2].__setitem__("role", ""),
            "BUILD_TREE_ROLE_REQUIRED",
        ),
    ],
)
def test_invalid_graph_mutations_fail_direct_validator(
    mutation, expected_code: str
) -> None:
    value = valid_tree()
    mutation(value)
    assert code_for(value) == expected_code


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["nodes"].append(copy.deepcopy(value["nodes"][0])),
        lambda value: value.__setitem__("root", "missing"),
        lambda value: value["nodes"][0]["children"].append("missing"),
        lambda value: value["nodes"][0].__setitem__("children", ["node-wrapper", "node-wrapper"]),
        lambda value: value["nodes"][1]["children"].append("node-wrapper"),
        lambda value: value["nodes"].append(
            {"id": "orphan", "role": "normal_flow_group", "children": []}
        ),
        lambda value: value["nodes"][2].__setitem__("role", "unsupported"),
    ],
)
def test_malformed_tree_blocks_owning_stage_without_state_or_digest(
    mutation,
) -> None:
    outputs = conversational.load_output_files(PREFINAL_DIR, root=REPO_ROOT)
    state = runtime.initial_run_state(outputs[0]["run_id"], root=REPO_ROOT)
    context = runtime.RunContext(source_kind="fixture")
    for output in outputs[:7]:
        result, state = runtime.evaluate_stage(
            output["stage_id"],
            output,
            state,
            root=REPO_ROOT,
            run_context=context,
        )
        assert result["stage_status"] == "pass"

    before = copy.deepcopy(state)
    candidate = copy.deepcopy(outputs[7])
    mutation(candidate["canonical_content"])
    result, after = runtime.evaluate_stage(
        "/build-tree",
        candidate,
        state,
        root=REPO_ROOT,
        run_context=context,
    )

    assert result["stage_status"] == "blocked"
    assert "completion_class" not in result
    assert result["next_stage"] is None
    assert any(
        item["issue_id"] == "RUNTIME_STAGE_PREDICATE_FAILED"
        for item in result["blocking_issues"]
    )
    assert result["decision_state"]["build_tree_digest"] == before["build_tree_digest"]
    assert after == before
    assert after["build_tree_digest"] is None
    assert "/build-tree" not in after["completed_stages"]


def test_valid_fixture_build_tree_passes_and_sets_digest_once() -> None:
    outputs = conversational.load_output_files(PREFINAL_DIR, root=REPO_ROOT)
    state = runtime.initial_run_state(outputs[0]["run_id"], root=REPO_ROOT)
    context = runtime.RunContext(source_kind="fixture")
    for output in outputs[:7]:
        _, state = runtime.evaluate_stage(
            output["stage_id"],
            output,
            state,
            root=REPO_ROOT,
            run_context=context,
        )
    result, after = runtime.evaluate_stage(
        "/build-tree",
        outputs[7],
        state,
        root=REPO_ROOT,
        run_context=context,
    )
    assert result["stage_status"] == "pass"
    assert result["completion_class"] == "validated_pass"
    assert after["build_tree_digest"]
    assert result["decision_state"]["build_tree_digest"] == after["build_tree_digest"]
