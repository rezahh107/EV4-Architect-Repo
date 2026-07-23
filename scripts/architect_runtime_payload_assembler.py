"""Runtime-owned assembly of the canonical Architect Stage Payload.

Project-specific intent is never invented. Every required Payload surface is
classified as a repository policy constant, Runtime-derived value, Stage-derived
value, or explicit unresolved evidence.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from architect_runtime_errors import PayloadDerivationError, RuntimeDiagnostic

POLICY_CONSTANT = "POLICY_CONSTANT"
RUNTIME_DERIVED = "RUNTIME_DERIVED"
STAGE_DERIVED = "STAGE_DERIVED"
EXPLICIT_UNRESOLVED = "EXPLICIT_UNRESOLVED"
DERIVATION_KINDS = {
    POLICY_CONSTANT,
    RUNTIME_DERIVED,
    STAGE_DERIVED,
    EXPLICIT_UNRESOLVED,
}
SUCCESS_COMPLETION_CLASSES = {"reasoning_complete", "validated_pass"}
RUNTIME_INTERFACE_ID = "ev4-architect-quality-runtime@2.0.0"
VALID_STATES = {
    "observed",
    "validated",
    "resolved",
    "derived",
    "proposed",
    "unverified",
    "insufficient_evidence",
}

FORBIDDEN_WORK = [
    "no_invent_geometry",
    "no_invent_assets",
    "no_invent_breakpoints",
    "no_infer_dynamic_data",
    "no_claim_builder_ready",
    "no_claim_production_ready",
    "no_claim_constructability_proven",
    "no_claim_responsive_complete",
    "no_create_builder_runtime_intake",
]
VALIDATION_RULES = [f"A-R{index:02d}" for index in range(1, 13)]

PAYLOAD_DERIVATION_RULES: dict[str, str] = {
    "schema_id": POLICY_CONSTANT,
    "schema_version": POLICY_CONSTANT,
    "owner_repository": POLICY_CONSTANT,
    "payload_status": RUNTIME_DERIVED,
    "synthetic": RUNTIME_DERIVED,
    "payload_identity": RUNTIME_DERIVED,
    "source_stage_lineage": RUNTIME_DERIVED,
    "architecture_identity": RUNTIME_DERIVED,
    "approved_structure_model": STAGE_DERIVED,
    "architect_intent": STAGE_DERIVED,
    "kernel_decision_records": STAGE_DERIVED,
    "evidence_register": RUNTIME_DERIVED,
    "unresolved_evidence": RUNTIME_DERIVED,
    "forbidden_work": POLICY_CONSTANT,
    "boundary_assertions": POLICY_CONSTANT,
    "validation_contract": POLICY_CONSTANT,
    "extension_records": RUNTIME_DERIVED,
    "architecture_identity.selected_candidate_id": RUNTIME_DERIVED,
    "architecture_identity.selected_candidate_locked": RUNTIME_DERIVED,
    "architecture_identity.architecture_family": STAGE_DERIVED,
    "architecture_identity.decision_source": RUNTIME_DERIVED,
    "architecture_identity.decision_source.stage": POLICY_CONSTANT,
    "architecture_identity.decision_source.payload_name": POLICY_CONSTANT,
    "architecture_identity.decision_source.schema_id": POLICY_CONSTANT,
    "architecture_identity.decision_source.evidence_refs": RUNTIME_DERIVED,
    "architecture_identity.decision_source.locked_decision_refs": RUNTIME_DERIVED,
    "architecture_identity.decision_source.approved_structure_ref": STAGE_DERIVED,
    "architecture_identity.decision_source.source_evidence_refs": RUNTIME_DERIVED,
    "architecture_identity.semantic_lock": POLICY_CONSTANT,
    "architecture_identity.semantic_lock.boolean_lock_alone_sufficient": POLICY_CONSTANT,
    "architecture_identity.semantic_lock.requires_candidate_identity": POLICY_CONSTANT,
    "architecture_identity.semantic_lock.requires_decision_source": POLICY_CONSTANT,
    "architecture_identity.semantic_lock.requires_locked_decision_refs": POLICY_CONSTANT,
    "architecture_identity.semantic_lock.requires_approved_structure_ref": POLICY_CONSTANT,
    "architecture_identity.semantic_lock.requires_source_evidence_refs": POLICY_CONSTANT,
    "approved_structure_model.structure_schema_version": POLICY_CONSTANT,
    "approved_structure_model.root_node_id": STAGE_DERIVED,
    "approved_structure_model.structure_nodes": STAGE_DERIVED,
    "approved_structure_model.structure_nodes[].node_id": STAGE_DERIVED,
    "approved_structure_model.structure_nodes[].parent_node_id": RUNTIME_DERIVED,
    "approved_structure_model.structure_nodes[].node_kind": RUNTIME_DERIVED,
    "approved_structure_model.structure_nodes[].role": STAGE_DERIVED,
    "approved_structure_model.structure_nodes[].hierarchy_path": RUNTIME_DERIVED,
    "approved_structure_model.structure_nodes[].evidence_refs": RUNTIME_DERIVED,
    "approved_structure_model.structure_nodes[].intent_refs": RUNTIME_DERIVED,
    "approved_structure_model.structure_nodes[].children": STAGE_DERIVED,
    "architect_intent.normal_flow_intent": RUNTIME_DERIVED,
    "architect_intent.normal_flow_intent.intent_id": POLICY_CONSTANT,
    "architect_intent.normal_flow_intent.state": RUNTIME_DERIVED,
    "architect_intent.normal_flow_intent.summary": RUNTIME_DERIVED,
    "architect_intent.normal_flow_intent.evidence_refs": RUNTIME_DERIVED,
    "architect_intent.overlay_intent": RUNTIME_DERIVED,
    "architect_intent.overlay_intent.intent_id": POLICY_CONSTANT,
    "architect_intent.overlay_intent.state": RUNTIME_DERIVED,
    "architect_intent.overlay_intent.overlay_allowed": RUNTIME_DERIVED,
    "architect_intent.overlay_intent.contained_in_named_stage_required": POLICY_CONSTANT,
    "architect_intent.overlay_intent.meaningful_content_in_overlay_allowed": POLICY_CONSTANT,
    "architect_intent.overlay_intent.evidence_refs": RUNTIME_DERIVED,
    "architect_intent.editable_content_intent": RUNTIME_DERIVED,
    "architect_intent.editable_content_intent.intent_id": POLICY_CONSTANT,
    "architect_intent.editable_content_intent.state": RUNTIME_DERIVED,
    "architect_intent.editable_content_intent.meaningful_content_editable_when_practical": POLICY_CONSTANT,
    "architect_intent.editable_content_intent.static_image_for_meaningful_content_allowed": POLICY_CONSTANT,
    "architect_intent.editable_content_intent.evidence_refs": RUNTIME_DERIVED,
    "architect_intent.class_intent": STAGE_DERIVED,
    "architect_intent.class_intent.approved_class_names": STAGE_DERIVED,
    "architect_intent.class_intent.class_application_map": STAGE_DERIVED,
    "architect_intent.class_intent.class_application_map[].class_name": STAGE_DERIVED,
    "architect_intent.class_intent.class_application_map[].target_node_ids": STAGE_DERIVED,
    "architect_intent.class_intent.class_application_map[].scope": STAGE_DERIVED,
    "architect_intent.class_intent.class_application_map[].evidence_refs": RUNTIME_DERIVED,
    "architect_intent.asset_intent": EXPLICIT_UNRESOLVED,
    "architect_intent.asset_intent.asset_requirements": STAGE_DERIVED,
    "architect_intent.asset_intent.asset_requirements[].asset_id": STAGE_DERIVED,
    "architect_intent.asset_intent.asset_requirements[].role": STAGE_DERIVED,
    "architect_intent.asset_intent.asset_requirements[].state": STAGE_DERIVED,
    "architect_intent.asset_intent.asset_requirements[].evidence_refs": RUNTIME_DERIVED,
    "architect_intent.asset_intent.missing_asset_policy": POLICY_CONSTANT,
    "architect_intent.scoped_css_intent": EXPLICIT_UNRESOLVED,
    "architect_intent.scoped_css_intent.css_allowed": STAGE_DERIVED,
    "architect_intent.scoped_css_intent.allowed_selector_scopes": POLICY_CONSTANT,
    "architect_intent.scoped_css_intent.global_css_allowed": POLICY_CONSTANT,
    "architect_intent.scoped_css_intent.meaningful_content_created_by_css_allowed": POLICY_CONSTANT,
    "architect_intent.scoped_css_intent.css_need_map": STAGE_DERIVED,
    "architect_intent.scoped_css_intent.css_need_map[].css_need_id": STAGE_DERIVED,
    "architect_intent.scoped_css_intent.css_need_map[].target_node_id": STAGE_DERIVED,
    "architect_intent.scoped_css_intent.css_need_map[].allowed_selector_scope": STAGE_DERIVED,
    "architect_intent.scoped_css_intent.css_need_map[].purpose": STAGE_DERIVED,
    "architect_intent.scoped_css_intent.css_need_map[].state": STAGE_DERIVED,
    "architect_intent.scoped_css_intent.css_need_map[].evidence_refs": RUNTIME_DERIVED,
    "architect_intent.responsive_risk_seeds": EXPLICIT_UNRESOLVED,
    "architect_intent.responsive_risk_seeds[].risk_id": STAGE_DERIVED,
    "architect_intent.responsive_risk_seeds[].risk_type": STAGE_DERIVED,
    "architect_intent.responsive_risk_seeds[].state": STAGE_DERIVED,
    "architect_intent.responsive_risk_seeds[].description": STAGE_DERIVED,
    "architect_intent.responsive_risk_seeds[].downstream_owner": STAGE_DERIVED,
    "architect_intent.responsive_risk_seeds[].evidence_refs": RUNTIME_DERIVED,
    "architect_intent.dynamic_loop_intent": EXPLICIT_UNRESOLVED,
    "architect_intent.dynamic_loop_intent.status": STAGE_DERIVED,
    "architect_intent.dynamic_loop_intent.evidence_refs": RUNTIME_DERIVED,
    "architect_intent.dynamic_loop_intent.reason": STAGE_DERIVED,
    "kernel_decision_records[].decision_family": STAGE_DERIVED,
    "kernel_decision_records[].decision_card_ref": POLICY_CONSTANT,
    "kernel_decision_records[].selected_option": STAGE_DERIVED,
    "kernel_decision_records[].rejected_options": STAGE_DERIVED,
    "kernel_decision_records[].evidence_refs": RUNTIME_DERIVED,
    "kernel_decision_records[].evidence_state": RUNTIME_DERIVED,
}


def _diagnostic(
    code: str,
    message: str,
    *,
    path: str | None = None,
    stage_id: str | None = None,
) -> RuntimeDiagnostic:
    return RuntimeDiagnostic(code, message, path=path, stage_id=stage_id)


def _fail(
    code: str,
    message: str,
    *,
    path: str | None = None,
    stage_id: str | None = None,
) -> None:
    raise PayloadDerivationError(
        _diagnostic(code, message, path=path, stage_id=stage_id)
    )


def _digest(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _output(state: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for item in reversed(state.get("evaluated_stage_outputs", [])):
        if isinstance(item, dict) and item.get("stage_id") == stage_id:
            return item
    _fail(
        "PAYLOAD_STAGE_OUTPUT_REQUIRED",
        "Evaluated Stage Output is required",
        stage_id=stage_id,
    )


def _result(state: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for item in reversed(state.get("derived_stage_results", [])):
        if isinstance(item, dict) and item.get("stage_id") == stage_id:
            return item
    _fail(
        "PAYLOAD_STAGE_RESULT_REQUIRED",
        "Derived Stage Result is required",
        stage_id=stage_id,
    )


def _content(state: dict[str, Any], stage_id: str) -> dict[str, Any]:
    value = _output(state, stage_id).get("canonical_content")
    if not isinstance(value, dict):
        _fail(
            "PAYLOAD_CANONICAL_CONTENT_REQUIRED",
            "Canonical content is required",
            stage_id=stage_id,
        )
    return value


def _evidence_id(stage_id: str) -> str:
    return "runtime-stage-" + stage_id.strip("/").replace("/", "-")


def _lineage(
    state: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    outputs = [
        item
        for item in state.get("evaluated_stage_outputs", [])
        if isinstance(item, dict) and item.get("stage_id") != "/project-gate-export"
    ]
    results = {
        item.get("stage_id"): item
        for item in state.get("derived_stage_results", [])
        if isinstance(item, dict)
    }
    lineage: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for item in outputs:
        stage_id = str(item["stage_id"])
        result = results.get(stage_id)
        if not isinstance(result, dict):
            _fail(
                "PAYLOAD_LINEAGE_RESULT_REQUIRED",
                "Lineage Stage lacks a derived result",
                stage_id=stage_id,
            )
        if (
            result.get("stage_status") != "pass"
            or result.get("completion_class") not in SUCCESS_COMPLETION_CLASSES
        ):
            _fail(
                "PAYLOAD_LINEAGE_FALSE_COMPLETION",
                "Terminal Payload lineage requires a passing Stage Result with a success completion class",
                stage_id=stage_id,
            )
        evidence_id = _evidence_id(stage_id)
        lineage.append(
            {
                "stage": stage_id,
                "payload_name": stage_id.strip("/").replace("-", "_")
                + "_Stage_Output",
                "schema_id": "ev4-architect-conversational-stage-output-base@1.0.0",
                "state": "derived",
                "evidence_refs": [evidence_id],
            }
        )
        evidence.append(
            {
                "evidence_id": evidence_id,
                "state": "derived",
                "source_ref": {
                    "source_type": "stage_payload",
                    "reference": stage_id,
                },
                "claim": (
                    f"Runtime evaluated {stage_id} as {result['completion_class']} "
                    f"with status {result['stage_status']}"
                ),
                "fact_class": "project_specific_behavior",
            }
        )
    if not lineage:
        _fail("PAYLOAD_LINEAGE_REQUIRED", "Evaluated Stage lineage is required")
    return lineage, evidence


def _architecture(state: dict[str, Any]) -> tuple[str, str, list[str]]:
    selected = state.get("selected_candidate_id")
    if (
        not isinstance(selected, str)
        or not selected.strip()
        or not state.get("selected_candidate_locked")
    ):
        _fail(
            "PAYLOAD_CANDIDATE_LOCK_REQUIRED",
            "A locked selected Candidate is required",
        )
    rows = _content(state, "/architectures").get("candidates")
    if not isinstance(rows, list):
        _fail(
            "PAYLOAD_ARCHITECTURE_CANDIDATES_REQUIRED",
            "Architecture candidates are required",
        )
    selected_row = next(
        (
            item
            for item in rows
            if isinstance(item, dict) and item.get("candidate_id") == selected
        ),
        None,
    )
    if not isinstance(selected_row, dict):
        _fail(
            "PAYLOAD_LOCKED_CANDIDATE_MISSING",
            "Locked Candidate is absent from architecture candidates",
        )
    family = selected_row.get("family")
    if not isinstance(family, str) or not family.strip():
        _fail(
            "PAYLOAD_ARCHITECTURE_FAMILY_REQUIRED",
            "Selected Candidate architecture family is required",
        )
    rejected = [
        str(item.get("family"))
        for item in rows
        if isinstance(item, dict)
        and item.get("candidate_id") != selected
        and isinstance(item.get("family"), str)
        and item.get("family").strip()
    ]
    if not rejected or len(rejected) != len(set(rejected)):
        _fail(
            "PAYLOAD_REJECTED_ARCHITECTURE_REQUIRED",
            "At least one unique rejected architecture is required",
        )
    return selected, family, rejected


def _structure(state: dict[str, Any]) -> dict[str, Any]:
    tree = _content(state, "/build-tree")
    root = tree.get("root")
    nodes = tree.get("nodes")
    if not isinstance(root, str) or not isinstance(nodes, list) or not nodes:
        _fail(
            "PAYLOAD_BUILD_TREE_REQUIRED",
            "A canonical Build Tree is required",
            stage_id="/build-tree",
        )
    node_map: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            _fail(
                "PAYLOAD_BUILD_TREE_NODE_INVALID",
                "Build Tree nodes must be objects",
                stage_id="/build-tree",
            )
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id.strip() or node_id in node_map:
            _fail(
                "PAYLOAD_BUILD_TREE_NODE_ID_REQUIRED",
                "Build Tree node identities must be unique non-empty strings",
                stage_id="/build-tree",
            )
        node_map[node_id] = node
    if root not in node_map:
        _fail(
            "PAYLOAD_BUILD_TREE_ROOT_INVALID",
            "Build Tree root must identify one node",
        )

    parent_by_child: dict[str, str] = {}
    for parent, node in node_map.items():
        children = node.get("children")
        if (
            not isinstance(children, list)
            or any(not isinstance(item, str) for item in children)
            or len(children) != len(set(children))
        ):
            _fail(
                "PAYLOAD_BUILD_TREE_CHILDREN_INVALID",
                "Build Tree children must be unique string identities",
                path=parent,
            )
        for child in children:
            if child not in node_map:
                _fail(
                    "PAYLOAD_BUILD_TREE_CHILD_UNKNOWN",
                    "Build Tree child must identify an existing node",
                    path=child,
                )
            if child in parent_by_child:
                _fail(
                    "PAYLOAD_BUILD_TREE_MULTIPLE_PARENTS",
                    "Build Tree node cannot have multiple parents",
                    path=child,
                )
            parent_by_child[child] = parent

    def hierarchy_path(node_id: str) -> list[str]:
        path: list[str] = []
        current = node_id
        seen: set[str] = set()
        while True:
            if current in seen:
                _fail(
                    "PAYLOAD_BUILD_TREE_CYCLE",
                    "Build Tree hierarchy contains a cycle",
                    path=node_id,
                )
            seen.add(current)
            path.append(current)
            if current == root:
                return list(reversed(path))
            parent = parent_by_child.get(current)
            if parent is None:
                _fail(
                    "PAYLOAD_BUILD_TREE_DISCONNECTED",
                    "Every non-root node must connect to the root",
                    path=node_id,
                )
            current = parent

    kind_by_role = {
        "section_root": "section_root",
        "normal_flow_group": "structural_container",
        "editable_content": "content_group",
        "contained_decoration_layer": "decoration_layer",
    }
    converted: list[dict[str, Any]] = []
    for node_id, node in node_map.items():
        role = node.get("role")
        if not isinstance(role, str) or not role.strip():
            _fail(
                "PAYLOAD_BUILD_TREE_ROLE_REQUIRED",
                "Build Tree node role is required",
                path=node_id,
            )
        if role not in kind_by_role:
            _fail(
                "PAYLOAD_BUILD_TREE_ROLE_UNCLASSIFIED",
                "Build Tree role has no deterministic node-kind mapping",
                path=node_id,
            )
        converted.append(
            {
                "node_id": node_id,
                "parent_node_id": parent_by_child.get(node_id),
                "node_kind": kind_by_role[role],
                "role": role,
                "hierarchy_path": hierarchy_path(node_id),
                "evidence_refs": [_evidence_id("/build-tree")],
                "intent_refs": [],
                "children": node["children"],
            }
        )
    return {
        "structure_schema_version": "architect-structure-model.v1",
        "root_node_id": root,
        "structure_nodes": converted,
    }


def _implementation(
    state: dict[str, Any], node_ids: set[str]
) -> dict[str, Any]:
    content = _content(state, "/implementation")
    element_mapping = content.get("element_mapping")
    if not isinstance(element_mapping, list) or not element_mapping:
        _fail(
            "PAYLOAD_ELEMENT_MAPPING_REQUIRED",
            "Implementation element_mapping is required",
            stage_id="/implementation",
        )
    mapped_nodes: set[str] = set()
    for item in element_mapping:
        if not isinstance(item, dict):
            _fail(
                "PAYLOAD_ELEMENT_MAPPING_INVALID",
                "Implementation element mapping entries must be objects",
                stage_id="/implementation",
            )
        node_id = item.get("node_id")
        element = item.get("element")
        if (
            not isinstance(node_id, str)
            or node_id not in node_ids
            or node_id in mapped_nodes
            or not isinstance(element, str)
            or not element.strip()
        ):
            _fail(
                "PAYLOAD_ELEMENT_MAPPING_INVALID",
                "Every approved Build Tree node must have one explicit element mapping",
                stage_id="/implementation",
            )
        mapped_nodes.add(node_id)
    if mapped_nodes != node_ids:
        _fail(
            "PAYLOAD_ELEMENT_MAPPING_INCOMPLETE",
            "Implementation element_mapping must cover every approved Build Tree node",
            stage_id="/implementation",
        )

    values = content.get("class_intent")
    classes = [item for item in values or [] if isinstance(item, str) and item.strip()]
    if not classes or len(classes) != len(set(classes)):
        _fail(
            "PAYLOAD_CLASS_INTENT_REQUIRED",
            "Implementation class_intent must contain unique class names",
            stage_id="/implementation",
        )
    mapping = content.get("class_application_map")
    if not isinstance(mapping, list) or not mapping:
        _fail(
            "PAYLOAD_CLASS_APPLICATION_MAP_REQUIRED",
            "Implementation class_application_map is required",
            stage_id="/implementation",
        )
    converted: list[dict[str, Any]] = []
    seen_classes: set[str] = set()
    for item in mapping:
        if not isinstance(item, dict):
            _fail(
                "PAYLOAD_CLASS_APPLICATION_MAP_INVALID",
                "Class application entries must be objects",
                stage_id="/implementation",
            )
        class_name = item.get("class_name")
        targets = item.get("target_node_ids")
        scope = item.get("scope")
        if class_name not in classes or class_name in seen_classes:
            _fail(
                "PAYLOAD_CLASS_APPLICATION_MAP_INVALID",
                "Every approved class must have one mapping",
                stage_id="/implementation",
            )
        if (
            not isinstance(targets, list)
            or not targets
            or len(targets) != len(set(targets))
            or any(target not in node_ids for target in targets)
        ):
            _fail(
                "PAYLOAD_CLASS_APPLICATION_TARGET_INVALID",
                "Class targets must be unique approved Build Tree nodes",
                stage_id="/implementation",
            )
        if scope not in {
            "section",
            "component",
            "widget",
            "utility",
            "global_candidate",
        }:
            _fail(
                "PAYLOAD_CLASS_APPLICATION_SCOPE_INVALID",
                "Class scope is invalid",
                stage_id="/implementation",
            )
        seen_classes.add(class_name)
        converted.append(
            {
                "class_name": class_name,
                "target_node_ids": targets,
                "scope": scope,
                "evidence_refs": [_evidence_id("/implementation")],
            }
        )
    if seen_classes != set(classes):
        _fail(
            "PAYLOAD_CLASS_APPLICATION_MAP_INCOMPLETE",
            "Every approved class must be mapped",
            stage_id="/implementation",
        )
    return {"content": content, "classes": classes, "class_map": converted}


def _unresolved(
    unresolved_id: str,
    reason: str,
    *,
    owner: str = "architect",
    blocks: list[str] | None = None,
    required_before: str = "project_gate_acceptance",
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "unresolved_id": unresolved_id,
        "state": "insufficient_evidence",
        "owner": owner,
        "reason": reason,
        "blocks": blocks or ["architect_stage_payload_acceptance", "ce_transition"],
        "required_before": required_before,
        "evidence_refs": evidence_refs or [],
    }


def _unknowns(state: dict[str, Any]) -> list[dict[str, Any]]:
    unresolved: list[dict[str, Any]] = []
    for item in state.get("unknown_ledger", []):
        if not isinstance(item, dict) or item.get("status") != "active":
            continue
        critical = item.get("downstream_critical") is True
        unresolved.append(
            _unresolved(
                str(item.get("unknown_id")),
                str(item.get("statement")),
                owner="architect" if critical else "responsive",
                blocks=(
                    ["architect_stage_payload_acceptance", "ce_transition"]
                    if critical
                    else ["responsive_validation", "production_readiness"]
                ),
                required_before=(
                    "project_gate_acceptance" if critical else "responsive_validation"
                ),
                evidence_refs=[
                    ref
                    for ref in item.get("evidence_refs", [])
                    if isinstance(ref, str) and ref.strip()
                ],
            )
        )
    return unresolved


def _asset_intent(
    content: dict[str, Any], unresolved: list[dict[str, Any]]
) -> dict[str, Any]:
    value = content.get("asset_intent")
    if value is None:
        unresolved.append(
            _unresolved(
                "U-payload-asset-intent",
                "Implementation did not state asset intent.",
            )
        )
        return {
            "asset_requirements": [],
            "missing_asset_policy": "missing_assets_remain_explicit_evidence_gaps",
        }
    if not isinstance(value, dict) or value.get("decision") not in {
        "none_required",
        "specified",
    }:
        _fail(
            "PAYLOAD_ASSET_INTENT_INVALID",
            "asset_intent must explicitly state none_required or specified",
            stage_id="/implementation",
        )
    reason = value.get("reason")
    requirements = value.get("asset_requirements")
    if (
        not isinstance(reason, str)
        or not reason.strip()
        or not isinstance(requirements, list)
    ):
        _fail(
            "PAYLOAD_ASSET_INTENT_INVALID",
            "asset_intent requires a reason and asset_requirements array",
            stage_id="/implementation",
        )
    if value["decision"] == "none_required" and requirements:
        _fail(
            "PAYLOAD_ASSET_INTENT_CONTRADICTORY",
            "none_required must use an explicit empty asset_requirements array",
        )
    if value["decision"] == "specified" and not requirements:
        _fail(
            "PAYLOAD_ASSET_INTENT_CONTRADICTORY",
            "specified asset intent requires at least one asset requirement",
        )
    converted: list[dict[str, Any]] = []
    for item in requirements:
        if not isinstance(item, dict):
            _fail(
                "PAYLOAD_ASSET_REQUIREMENT_INVALID",
                "Asset requirements must be objects",
            )
        asset_id = item.get("asset_id")
        role = item.get("role")
        state = item.get("state")
        if (
            not isinstance(asset_id, str)
            or not asset_id.strip()
            or role not in {"meaningful", "decorative", "visual_core", "unknown"}
            or state not in VALID_STATES
        ):
            _fail(
                "PAYLOAD_ASSET_REQUIREMENT_INVALID",
                "Asset requirements require explicit asset_id, role, and state",
            )
        converted.append(
            {
                "asset_id": asset_id,
                "role": role,
                "state": state,
                "evidence_refs": [_evidence_id("/implementation")],
            }
        )
    return {
        "asset_requirements": converted,
        "missing_asset_policy": "missing_assets_remain_explicit_evidence_gaps",
    }


def _css_intent(
    content: dict[str, Any], unresolved: list[dict[str, Any]]
) -> dict[str, Any]:
    value = content.get("scoped_css_intent")
    if value is None:
        unresolved.append(
            _unresolved(
                "U-payload-css-intent",
                "Implementation did not state whether scoped CSS is required.",
            )
        )
        return {
            "css_allowed": False,
            "allowed_selector_scopes": [
                "selected_class",
                "child_of_selected_class",
            ],
            "global_css_allowed": False,
            "meaningful_content_created_by_css_allowed": False,
            "css_need_map": [],
        }
    if not isinstance(value, dict) or value.get("decision") not in {
        "not_required",
        "specified",
    }:
        _fail(
            "PAYLOAD_CSS_INTENT_INVALID",
            "scoped_css_intent must explicitly state not_required or specified",
        )
    reason = value.get("reason")
    needs = value.get("css_need_map")
    if not isinstance(reason, str) or not reason.strip() or not isinstance(needs, list):
        _fail(
            "PAYLOAD_CSS_INTENT_INVALID",
            "scoped_css_intent requires a reason and css_need_map array",
        )
    if value["decision"] == "not_required" and needs:
        _fail(
            "PAYLOAD_CSS_INTENT_CONTRADICTORY",
            "not_required must use an explicit empty css_need_map",
        )
    if value["decision"] == "specified" and not needs:
        _fail(
            "PAYLOAD_CSS_INTENT_CONTRADICTORY",
            "specified CSS intent requires at least one CSS need",
        )
    allowed_scopes = {
        "selected_class",
        "child_of_selected_class",
        "state",
        "responsive_device",
        "media_query",
    }
    converted: list[dict[str, Any]] = []
    for item in needs:
        if not isinstance(item, dict):
            _fail("PAYLOAD_CSS_NEED_INVALID", "CSS need entries must be objects")
        css_need_id = item.get("css_need_id")
        target_node_id = item.get("target_node_id")
        scope = item.get("allowed_selector_scope")
        purpose = item.get("purpose")
        state = item.get("state")
        if (
            not isinstance(css_need_id, str)
            or not css_need_id.strip()
            or not isinstance(target_node_id, str)
            or not target_node_id.strip()
            or scope not in allowed_scopes
            or not isinstance(purpose, str)
            or not purpose.strip()
            or state not in VALID_STATES
        ):
            _fail(
                "PAYLOAD_CSS_NEED_INVALID",
                "CSS need entries require explicit identity, target, scope, purpose, and state",
            )
        converted.append(
            {
                "css_need_id": css_need_id,
                "target_node_id": target_node_id,
                "allowed_selector_scope": scope,
                "purpose": purpose,
                "state": state,
                "evidence_refs": [_evidence_id("/implementation")],
            }
        )
    return {
        "css_allowed": value["decision"] == "specified",
        "allowed_selector_scopes": [
            "selected_class",
            "child_of_selected_class",
        ],
        "global_css_allowed": False,
        "meaningful_content_created_by_css_allowed": False,
        "css_need_map": converted,
    }


def _dynamic_loop_intent(
    content: dict[str, Any], unresolved: list[dict[str, Any]]
) -> dict[str, Any]:
    value = content.get("dynamic_loop_intent")
    if value is None:
        unresolved.append(
            _unresolved(
                "U-payload-dynamic-loop-intent",
                "Implementation did not state Dynamic Loop applicability.",
            )
        )
        return {
            "status": "unknown",
            "evidence_refs": [],
            "reason": "Dynamic Loop applicability is unresolved.",
        }
    if not isinstance(value, dict) or value.get("status") not in {
        "none",
        "not_applicable",
        "possible",
        "unknown",
        "approved",
    }:
        _fail(
            "PAYLOAD_DYNAMIC_LOOP_INTENT_INVALID",
            "dynamic_loop_intent status is invalid",
        )
    reason = value.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        _fail(
            "PAYLOAD_DYNAMIC_LOOP_INTENT_INVALID",
            "dynamic_loop_intent requires a reason",
        )
    return {
        "status": value["status"],
        "evidence_refs": [_evidence_id("/implementation")],
        "reason": reason,
    }


def _responsive_risks(
    content: dict[str, Any],
    unresolved: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    values = content.get("responsive_risk_seeds")
    if values is None:
        unresolved.append(
            _unresolved(
                "U-payload-project-responsive-risk",
                "Implementation did not state project-specific responsive risks.",
                owner="responsive",
                blocks=["responsive_validation", "production_readiness"],
                required_before="responsive_validation",
            )
        )
        evidence_id = "runtime-contract-responsive-obligation"
        evidence.append(
            {
                "evidence_id": evidence_id,
                "state": "derived",
                "source_ref": {
                    "source_type": "contract",
                    "reference": "responsive-validation-boundary",
                },
                "claim": "Responsive validation remains a downstream contract obligation.",
                "fact_class": "contract_rule",
            }
        )
        return [
            {
                "risk_id": "contract-responsive-validation-pending",
                "risk_type": "mobile_behavior_not_proven",
                "state": "derived",
                "description": (
                    "Generic downstream responsive validation obligation; "
                    "no project-specific behavior is claimed."
                ),
                "downstream_owner": "responsive",
                "evidence_refs": [evidence_id],
            }
        ]
    if not isinstance(values, list) or not values:
        _fail(
            "PAYLOAD_RESPONSIVE_RISK_INVALID",
            "responsive_risk_seeds must be a non-empty explicit list",
        )
    allowed_types = {
        "mobile_behavior_not_proven",
        "tablet_behavior_not_proven",
        "breakpoints_not_provided",
        "connector_behavior_not_proven",
        "meaningful_content_visibility_unknown",
        "collision_risk_unknown",
    }
    allowed_owners = {"ce", "builder", "responsive", "unresolved"}
    converted: list[dict[str, Any]] = []
    for item in values:
        if not isinstance(item, dict):
            _fail(
                "PAYLOAD_RESPONSIVE_RISK_INVALID",
                "Responsive risk entries must be objects",
            )
        risk_id = item.get("risk_id")
        risk_type = item.get("risk_type")
        state = item.get("state")
        description = item.get("description")
        downstream_owner = item.get("downstream_owner")
        if (
            not isinstance(risk_id, str)
            or not risk_id.strip()
            or risk_type not in allowed_types
            or state not in VALID_STATES
            or not isinstance(description, str)
            or not description.strip()
            or downstream_owner not in allowed_owners
        ):
            _fail(
                "PAYLOAD_RESPONSIVE_RISK_INVALID",
                "Responsive risks require explicit identity, type, state, description, and owner",
            )
        converted.append(
            {
                "risk_id": risk_id,
                "risk_type": risk_type,
                "state": state,
                "description": description,
                "downstream_owner": downstream_owner,
                "evidence_refs": [_evidence_id("/implementation")],
            }
        )
    return converted


def _decision_record(
    value: Any, family: str, evidence_ref: str
) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        _fail("PAYLOAD_DECISION_INVALID", f"{family} decision must be an object")
    selected = value.get("selected_option")
    rejected = value.get("rejected_options")
    if (
        not isinstance(selected, str)
        or not selected.strip()
        or not isinstance(rejected, list)
        or not rejected
        or any(not isinstance(item, str) or not item.strip() for item in rejected)
        or len(rejected) != len(set(rejected))
    ):
        _fail(
            "PAYLOAD_DECISION_INVALID",
            f"{family} decision requires selected_option and unique rejected_options",
        )
    return {
        "decision_family": family,
        "decision_card_ref": (
            "kernel/decision-governance/p0-decision-matrices.v0.json"
            f"#decision_family_id={family}"
        ),
        "selected_option": selected,
        "rejected_options": rejected,
        "evidence_refs": [evidence_ref],
        "evidence_state": "derived",
    }


def assemble_architect_stage_payload(
    *, run_state: dict[str, Any], source_kind: str
) -> dict[str, Any]:
    if source_kind not in {
        "live_conversation",
        "fixture",
        "example",
        "test_vector",
    }:
        _fail(
            "PAYLOAD_SOURCE_KIND_INVALID",
            f"Unsupported source kind: {source_kind!r}",
        )
    lineage, evidence = _lineage(run_state)
    selected, family, rejected_families = _architecture(run_state)
    structure = _structure(run_state)
    node_ids = {item["node_id"] for item in structure["structure_nodes"]}
    implementation = _implementation(run_state, node_ids)
    content = implementation["content"]
    for node in structure["structure_nodes"]:
        node["intent_refs"] = sorted(
            item["class_name"]
            for item in implementation["class_map"]
            if node["node_id"] in item["target_node_ids"]
        )
    unresolved = _unknowns(run_state)
    build_ref = _evidence_id("/build-tree")
    recommend_ref = _evidence_id("/recommend")
    implementation_ref = _evidence_id("/implementation")
    asset_intent = _asset_intent(content, unresolved)
    css_intent = _css_intent(content, unresolved)
    dynamic_loop_intent = _dynamic_loop_intent(content, unresolved)
    responsive_risks = _responsive_risks(content, unresolved, evidence)
    decisions = [
        {
            "decision_family": "layout_structure",
            "decision_card_ref": (
                "kernel/decision-governance/p0-decision-matrices.v0.json"
                "#decision_family_id=layout_structure"
            ),
            "selected_option": family,
            "rejected_options": rejected_families,
            "evidence_refs": [recommend_ref, build_ref],
            "evidence_state": "derived",
        }
    ]
    media = _decision_record(
        content.get("media_decision"), "media_choice", implementation_ref
    )
    styling = _decision_record(
        content.get("styling_decision"), "styling_mechanism", implementation_ref
    )
    if media is None:
        unresolved.append(
            _unresolved(
                "U-payload-media-decision",
                "Implementation did not state the project media decision.",
            )
        )
    else:
        decisions.append(media)
    if styling is None:
        unresolved.append(
            _unresolved(
                "U-payload-styling-decision",
                "Implementation did not state the project styling decision.",
            )
        )
    else:
        decisions.append(styling)
    synthetic = source_kind != "live_conversation"
    payload_status = "insufficient_evidence" if unresolved else "complete"
    output_digests = {
        item["stage_id"]: _digest(item)
        for item in run_state.get("evaluated_stage_outputs", [])
        if isinstance(item, dict)
    }
    result_digests = {
        item["stage_id"]: _digest(item)
        for item in run_state.get("derived_stage_results", [])
        if isinstance(item, dict)
    }
    return {
        "schema_id": "ev4-architect-stage-payload@1.0.0",
        "schema_version": "1.0.0",
        "owner_repository": "rezahh107/EV4-Architect-Repo",
        "payload_status": payload_status,
        "synthetic": synthetic,
        "payload_identity": {
            "producer": "ev4_architect",
            "stage": "architect",
            "contract_purpose": "project_gate_stage_payload",
            "created_by": "architect_quality_runtime",
            "synthetic_fixture_notice": (
                "Runtime-derived live conversation context."
                if not synthetic
                else f"Runtime-derived {source_kind} context; real handoff is forbidden."
            ),
        },
        "source_stage_lineage": lineage,
        "architecture_identity": {
            "selected_candidate_id": selected,
            "selected_candidate_locked": True,
            "architecture_family": family,
            "decision_source": {
                "stage": "/recommend",
                "payload_name": "Recommendation_Payload",
                "schema_id": "ev4-architect-conversational-stage-output-base@1.0.0",
                "evidence_refs": [recommend_ref],
                "locked_decision_refs": [recommend_ref],
                "approved_structure_ref": structure["root_node_id"],
                "source_evidence_refs": [build_ref],
            },
            "semantic_lock": {
                "boolean_lock_alone_sufficient": False,
                "requires_candidate_identity": True,
                "requires_decision_source": True,
                "requires_locked_decision_refs": True,
                "requires_approved_structure_ref": True,
                "requires_source_evidence_refs": True,
            },
        },
        "approved_structure_model": structure,
        "architect_intent": {
            "normal_flow_intent": {
                "intent_id": "runtime-normal-flow",
                "state": "derived",
                "summary": (
                    "Primary meaningful content remains represented by the approved Build Tree."
                ),
                "evidence_refs": [build_ref],
            },
            "overlay_intent": {
                "intent_id": "runtime-overlay-intent",
                "state": "derived",
                "overlay_allowed": any(
                    item["node_kind"]
                    in {"decoration_layer", "overlay_stage", "connector_layer"}
                    for item in structure["structure_nodes"]
                ),
                "contained_in_named_stage_required": True,
                "meaningful_content_in_overlay_allowed": False,
                "evidence_refs": [build_ref],
            },
            "editable_content_intent": {
                "intent_id": "runtime-editable-content",
                "state": "derived",
                "meaningful_content_editable_when_practical": True,
                "static_image_for_meaningful_content_allowed": False,
                "evidence_refs": [build_ref],
            },
            "class_intent": {
                "approved_class_names": implementation["classes"],
                "class_application_map": implementation["class_map"],
            },
            "asset_intent": asset_intent,
            "scoped_css_intent": css_intent,
            "responsive_risk_seeds": responsive_risks,
            "dynamic_loop_intent": dynamic_loop_intent,
        },
        "kernel_decision_records": decisions,
        "evidence_register": evidence,
        "unresolved_evidence": unresolved,
        "forbidden_work": FORBIDDEN_WORK,
        "boundary_assertions": {
            "constructability_proven": False,
            "ce_approved": False,
            "ce_review_required": True,
            "builder_ready": False,
            "builder_executable": False,
            "builder_runtime_intake_authorized": False,
            "responsive_complete": False,
            "production_ready": False,
            "live_elementor_validated": False,
            "real_export_json_validated": False,
            "exact_pixel_match_validated": False,
            "project_gate_may_invent_architect_facts": False,
        },
        "validation_contract": {
            "schema_validation_required": True,
            "semantic_validation_required": True,
            "additional_properties_allowed_in_core": False,
            "rules": VALIDATION_RULES,
        },
        "extension_records": [
            {
                "extension_id": "runtime-truth-spine",
                "owner": "rezahh107/EV4-Architect-Repo",
                "evidence_state": "derived",
                "evidence_refs": [recommend_ref, build_ref, implementation_ref],
                "allowed_consumer": "project_gate",
                "cannot_override_core_fields": True,
                "downstream_readiness_claims_allowed": False,
                "data": {
                    "runtime_interface_id": RUNTIME_INTERFACE_ID,
                    "run_id": run_state.get("run_id"),
                    "source_kind": source_kind,
                    "stage_output_digests": output_digests,
                    "stage_result_digests": result_digests,
                    "build_tree_digest": run_state.get("build_tree_digest"),
                    "implementation_digest": run_state.get("implementation_digest"),
                    "final_audit_status": _result(
                        run_state, "/final-audit"
                    ).get("stage_status"),
                    "payload_derivation_complete": not unresolved,
                },
            }
        ],
    }
