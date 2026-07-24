"""Canonical validation for Architect Build Tree Stage content."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from architect_runtime_errors import PayloadDerivationError, RuntimeDiagnostic

NODE_KIND_BY_ROLE: dict[str, str] = {
    "section_root": "section_root",
    "normal_flow_group": "structural_container",
    "editable_content": "content_group",
    "contained_decoration_layer": "decoration_layer",
}


@dataclass(frozen=True)
class CanonicalBuildTree:
    root_id: str
    node_by_id: dict[str, dict[str, Any]]
    parent_by_child: dict[str, str]
    hierarchy_paths: dict[str, tuple[str, ...]]
    node_kind_by_id: dict[str, str]


def _fail(
    code: str,
    message: str,
    *,
    path: str | None = None,
    stage_id: str,
) -> None:
    raise PayloadDerivationError(
        RuntimeDiagnostic(code, message, path=path, stage_id=stage_id)
    )


def validate_canonical_build_tree(
    value: object,
    *,
    stage_id: str = "/build-tree",
) -> CanonicalBuildTree:
    """Validate one connected rooted directed tree and return normalized graph data."""
    if not isinstance(value, dict):
        _fail(
            "BUILD_TREE_OBJECT_REQUIRED",
            "Canonical Build Tree must be an object",
            path="canonical_content",
            stage_id=stage_id,
        )

    root = value.get("root")
    if not isinstance(root, str) or not root.strip():
        _fail(
            "BUILD_TREE_ROOT_REQUIRED",
            "Build Tree root must be a non-empty string",
            path="canonical_content.root",
            stage_id=stage_id,
        )

    nodes = value.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        _fail(
            "BUILD_TREE_NODES_REQUIRED",
            "Build Tree nodes must be a non-empty array",
            path="canonical_content.nodes",
            stage_id=stage_id,
        )

    node_by_id: dict[str, dict[str, Any]] = {}
    node_kind_by_id: dict[str, str] = {}
    for index, node in enumerate(nodes):
        path = f"canonical_content.nodes[{index}]"
        if not isinstance(node, dict):
            _fail(
                "BUILD_TREE_NODE_OBJECT_REQUIRED",
                "Build Tree nodes must be objects",
                path=path,
                stage_id=stage_id,
            )
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            _fail(
                "BUILD_TREE_NODE_ID_REQUIRED",
                "Build Tree node ID must be a non-empty string",
                path=f"{path}.id",
                stage_id=stage_id,
            )
        if node_id in node_by_id:
            _fail(
                "BUILD_TREE_NODE_ID_DUPLICATE",
                "Build Tree node IDs must be unique",
                path=f"{path}.id",
                stage_id=stage_id,
            )
        role = node.get("role")
        if not isinstance(role, str) or not role.strip():
            _fail(
                "BUILD_TREE_ROLE_REQUIRED",
                "Build Tree node role must be a non-empty string",
                path=f"{path}.role",
                stage_id=stage_id,
            )
        if role not in NODE_KIND_BY_ROLE:
            _fail(
                "BUILD_TREE_ROLE_UNSUPPORTED",
                "Build Tree role has no deterministic Payload node-kind mapping",
                path=f"{path}.role",
                stage_id=stage_id,
            )
        children = node.get("children")
        if not isinstance(children, list):
            _fail(
                "BUILD_TREE_CHILDREN_ARRAY_REQUIRED",
                "Build Tree node children must be an array",
                path=f"{path}.children",
                stage_id=stage_id,
            )
        if any(not isinstance(child, str) or not child.strip() for child in children):
            _fail(
                "BUILD_TREE_CHILD_ID_INVALID",
                "Build Tree child references must be non-empty strings",
                path=f"{path}.children",
                stage_id=stage_id,
            )
        if len(children) != len(set(children)):
            _fail(
                "BUILD_TREE_CHILD_DUPLICATE",
                "Build Tree child references must be unique per parent",
                path=f"{path}.children",
                stage_id=stage_id,
            )
        node_by_id[node_id] = {**node, "children": list(children)}
        node_kind_by_id[node_id] = NODE_KIND_BY_ROLE[role]

    if root not in node_by_id:
        _fail(
            "BUILD_TREE_ROOT_UNKNOWN",
            "Build Tree root must identify an existing node",
            path="canonical_content.root",
            stage_id=stage_id,
        )

    parent_by_child: dict[str, str] = {}
    for parent_id in sorted(node_by_id):
        for child_id in node_by_id[parent_id]["children"]:
            if child_id == parent_id:
                _fail(
                    "BUILD_TREE_SELF_CYCLE",
                    "Build Tree node cannot reference itself as a child",
                    path=child_id,
                    stage_id=stage_id,
                )
            if child_id == root:
                _fail(
                    "BUILD_TREE_ROOT_HAS_PARENT",
                    "Build Tree root cannot be assigned as a child",
                    path=child_id,
                    stage_id=stage_id,
                )
            if child_id not in node_by_id:
                _fail(
                    "BUILD_TREE_CHILD_UNKNOWN",
                    "Build Tree child must identify an existing node",
                    path=child_id,
                    stage_id=stage_id,
                )
            if child_id in parent_by_child:
                _fail(
                    "BUILD_TREE_MULTIPLE_PARENTS",
                    "Every non-root Build Tree node must have exactly one parent",
                    path=child_id,
                    stage_id=stage_id,
                )
            parent_by_child[child_id] = parent_id

    visit_state: dict[str, int] = {}

    def visit(node_id: str) -> None:
        state = visit_state.get(node_id, 0)
        if state == 1:
            _fail(
                "BUILD_TREE_CYCLE",
                "Build Tree contains a directed cycle",
                path=node_id,
                stage_id=stage_id,
            )
        if state == 2:
            return
        visit_state[node_id] = 1
        for child_id in node_by_id[node_id]["children"]:
            visit(child_id)
        visit_state[node_id] = 2

    for node_id in sorted(node_by_id):
        visit(node_id)

    missing_parent = sorted(
        node_id
        for node_id in node_by_id
        if node_id != root and node_id not in parent_by_child
    )
    if missing_parent:
        _fail(
            "BUILD_TREE_NON_ROOT_PARENT_REQUIRED",
            "Every non-root Build Tree node must have exactly one parent",
            path=missing_parent[0],
            stage_id=stage_id,
        )

    hierarchy_paths: dict[str, tuple[str, ...]] = {}
    reachable: set[str] = set()

    def walk(node_id: str, path: tuple[str, ...]) -> None:
        reachable.add(node_id)
        hierarchy_paths[node_id] = (*path, node_id)
        for child_id in node_by_id[node_id]["children"]:
            walk(child_id, hierarchy_paths[node_id])

    walk(root, ())
    disconnected = sorted(set(node_by_id) - reachable)
    if disconnected:
        _fail(
            "BUILD_TREE_DISCONNECTED",
            "Every Build Tree node must be reachable from the root",
            path=disconnected[0],
            stage_id=stage_id,
        )

    return CanonicalBuildTree(
        root_id=root,
        node_by_id=node_by_id,
        parent_by_child=parent_by_child,
        hierarchy_paths=hierarchy_paths,
        node_kind_by_id=node_kind_by_id,
    )
