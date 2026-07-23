"""Runtime-owned assembly of the canonical Architect Stage Payload."""
from __future__ import annotations

import hashlib
import json
from typing import Any

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


def _digest(value: Any) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _output(state: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for item in reversed(state.get("evaluated_stage_outputs", [])):
        if isinstance(item, dict) and item.get("stage_id") == stage_id:
            return item
    raise ValueError(f"Runtime Payload assembly requires evaluated output {stage_id}")


def _result(state: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for item in reversed(state.get("derived_stage_results", [])):
        if isinstance(item, dict) and item.get("stage_id") == stage_id:
            return item
    raise ValueError(f"Runtime Payload assembly requires derived result {stage_id}")


def _content(state: dict[str, Any], stage_id: str) -> dict[str, Any]:
    value = _output(state, stage_id).get("canonical_content")
    if not isinstance(value, dict):
        raise ValueError(f"Runtime Payload assembly requires canonical content {stage_id}")
    return value


def _evidence_id(stage_id: str) -> str:
    return "runtime-stage-" + stage_id.strip("/").replace("/", "-")


def _lineage(state: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    outputs = [
        item for item in state.get("evaluated_stage_outputs", [])
        if isinstance(item, dict) and item.get("stage_id") != "/project-gate-export"
    ]
    results = {
        item.get("stage_id"): item for item in state.get("derived_stage_results", [])
        if isinstance(item, dict)
    }
    lineage: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for item in outputs:
        stage_id = str(item["stage_id"])
        result = results.get(stage_id, {})
        evidence_id = _evidence_id(stage_id)
        lineage.append(
            {
                "stage": stage_id,
                "payload_name": stage_id.strip("/").replace("-", "_") + "_Stage_Output",
                "schema_id": "ev4-architect-conversational-stage-output-base@1.0.0",
                "state": "derived",
                "evidence_refs": [evidence_id],
            }
        )
        evidence.append(
            {
                "evidence_id": evidence_id,
                "state": "derived",
                "source_ref": {"source_type": "stage_payload", "reference": stage_id},
                "claim": (
                    f"Runtime evaluated {stage_id} as "
                    f"{result.get('completion_class', 'unknown_completion_class')} "
                    f"with status {result.get('stage_status', 'unknown')}"
                ),
                "fact_class": "project_specific_behavior",
            }
        )
    if not lineage:
        raise ValueError("Runtime Payload assembly requires evaluated Stage lineage")
    return lineage, evidence


def _architecture(state: dict[str, Any]) -> tuple[str, str, list[str]]:
    selected = state.get("selected_candidate_id")
    if not isinstance(selected, str) or not selected.strip() or not state.get("selected_candidate_locked"):
        raise ValueError("Runtime Payload assembly requires a locked selected Candidate")
    rows = _content(state, "/architectures").get("candidates")
    if not isinstance(rows, list):
        raise ValueError("Runtime Payload assembly requires architecture candidates")
    selected_row = next(
        (item for item in rows if isinstance(item, dict) and item.get("candidate_id") == selected),
        None,
    )
    if not isinstance(selected_row, dict):
        raise ValueError("Locked Candidate is absent from evaluated architecture candidates")
    family = selected_row.get("family")
    if not isinstance(family, str) or not family.strip():
        raise ValueError("Selected Candidate architecture family is required")
    rejected = [
        str(item.get("family")) for item in rows
        if isinstance(item, dict)
        and item.get("candidate_id") != selected
        and isinstance(item.get("family"), str)
        and item.get("family").strip()
    ]
    if not rejected:
        raise ValueError("Runtime Payload assembly requires at least one rejected architecture")
    return selected, family, rejected


def _structure(state: dict[str, Any]) -> dict[str, Any]:
    tree = _content(state, "/build-tree")
    root, nodes = tree.get("root"), tree.get("nodes")
    if not isinstance(root, str) or not isinstance(nodes, list) or not nodes:
        raise ValueError("Runtime Payload assembly requires a canonical Build Tree")
    parent_by_child: dict[str, str] = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        parent = node.get("id")
        for child in node.get("children", []):
            if isinstance(parent, str) and isinstance(child, str):
                parent_by_child[child] = parent
    kind_by_role = {
        "section_root": "section_root",
        "normal_flow_group": "structural_container",
        "editable_content": "content_group",
        "contained_decoration_layer": "decoration_layer",
    }
    converted: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("Build Tree nodes must be objects")
        node_id, role, children = node.get("id"), node.get("role"), node.get("children")
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("Build Tree node identity is required")
        if not isinstance(role, str) or not role.strip():
            raise ValueError("Build Tree node role is required")
        if not isinstance(children, list) or any(not isinstance(item, str) for item in children):
            raise ValueError("Build Tree node children must be string identities")
        converted.append(
            {
                "node_id": node_id,
                "parent_node_id": parent_by_child.get(node_id),
                "node_kind": kind_by_role.get(role, "structural_container"),
                "role": role,
                "hierarchy_path": [root, node_id] if node_id != root else [root],
                "evidence_refs": [_evidence_id("/build-tree")],
                "intent_refs": [],
                "children": children,
            }
        )
    if root not in {item["node_id"] for item in converted}:
        raise ValueError("Build Tree root must identify one converted node")
    return {
        "structure_schema_version": "architect-structure-model.v1",
        "root_node_id": root,
        "structure_nodes": converted,
    }


def _classes(state: dict[str, Any], root_node_id: str) -> tuple[list[str], list[dict[str, Any]]]:
    values = _content(state, "/implementation").get("class_intent")
    classes = [item for item in values or [] if isinstance(item, str) and item.strip()]
    if not classes:
        classes = ["architect-section"]
    return classes, [
        {
            "class_name": class_name,
            "target_node_ids": [root_node_id],
            "scope": "section",
            "evidence_refs": [_evidence_id("/implementation")],
        }
        for class_name in classes
    ]


def _unknowns(state: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    unresolved: list[dict[str, Any]] = []
    transition_blocked = False
    for item in state.get("unknown_ledger", []):
        if not isinstance(item, dict) or item.get("status") != "active":
            continue
        critical = item.get("downstream_critical") is True
        transition_blocked = transition_blocked or critical
        unresolved.append(
            {
                "unresolved_id": str(item.get("unknown_id")),
                "state": "insufficient_evidence",
                "owner": "architect" if critical else "responsive",
                "reason": str(item.get("statement")),
                "blocks": (
                    ["architect_stage_payload_acceptance", "ce_transition"]
                    if critical else ["responsive_validation", "production_readiness"]
                ),
                "required_before": (
                    "project_gate_acceptance" if critical else "responsive_validation"
                ),
                "evidence_refs": [
                    ref for ref in item.get("evidence_refs", [])
                    if isinstance(ref, str) and ref.strip()
                ],
            }
        )
    return unresolved, transition_blocked


def assemble_architect_stage_payload(*, run_state: dict[str, Any], source_kind: str) -> dict[str, Any]:
    """Assemble the official payload from evaluator-owned Run history."""
    lineage, evidence = _lineage(run_state)
    selected, family, rejected_families = _architecture(run_state)
    structure = _structure(run_state)
    root_node_id = structure["root_node_id"]
    classes, class_map = _classes(run_state, root_node_id)
    unresolved, transition_blocked = _unknowns(run_state)
    synthetic = source_kind != "live_conversation"
    recommend_ref = _evidence_id("/recommend")
    build_ref = _evidence_id("/build-tree")
    implementation_ref = _evidence_id("/implementation")
    output_digests = {
        item["stage_id"]: _digest(item) for item in run_state.get("evaluated_stage_outputs", [])
        if isinstance(item, dict)
    }
    result_digests = {
        item["stage_id"]: _digest(item) for item in run_state.get("derived_stage_results", [])
        if isinstance(item, dict)
    }
    return {
        "schema_id": "ev4-architect-stage-payload@1.0.0",
        "schema_version": "1.0.0",
        "owner_repository": "rezahh107/EV4-Architect-Repo",
        "payload_status": "insufficient_evidence" if transition_blocked else "complete",
        "synthetic": synthetic,
        "payload_identity": {
            "producer": "ev4_architect",
            "stage": "architect",
            "contract_purpose": "project_gate_stage_payload",
            "created_by": "architect_quality_runtime",
            "synthetic_fixture_notice": (
                "Runtime-derived live conversation context."
                if not synthetic else f"Runtime-derived {source_kind} context; real handoff is forbidden."
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
                "approved_structure_ref": root_node_id,
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
                "summary": "Primary meaningful content remains represented by the approved Build Tree.",
                "evidence_refs": [build_ref],
            },
            "overlay_intent": {
                "intent_id": "runtime-overlay-intent",
                "state": "derived",
                "overlay_allowed": any(
                    item["node_kind"] in {"decoration_layer", "overlay_stage", "connector_layer"}
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
                "approved_class_names": classes,
                "class_application_map": class_map,
            },
            "asset_intent": {
                "asset_requirements": [],
                "missing_asset_policy": "missing_assets_remain_explicit_evidence_gaps",
            },
            "scoped_css_intent": {
                "css_allowed": bool(classes),
                "allowed_selector_scopes": ["selected_class", "child_of_selected_class"],
                "global_css_allowed": False,
                "meaningful_content_created_by_css_allowed": False,
                "css_need_map": [],
            },
            "responsive_risk_seeds": [
                {
                    "risk_id": "runtime-responsive-validation-pending",
                    "risk_type": "mobile_behavior_not_proven",
                    "state": "insufficient_evidence",
                    "description": "Responsive behavior remains a downstream validation responsibility.",
                    "downstream_owner": "responsive",
                    "evidence_refs": [implementation_ref],
                }
            ],
            "dynamic_loop_intent": {
                "status": "unknown",
                "evidence_refs": [],
                "reason": "The evaluated Run does not establish a Dynamic Loop requirement.",
            },
        },
        "kernel_decision_records": [
            {
                "decision_family": "layout_structure",
                "decision_card_ref": "kernel/decision-governance/p0-decision-matrices.v0.json#decision_family_id=layout_structure",
                "selected_option": family,
                "rejected_options": rejected_families,
                "evidence_refs": [recommend_ref, build_ref],
                "evidence_state": "derived",
            },
            {
                "decision_family": "media_choice",
                "decision_card_ref": "kernel/decision-governance/p0-decision-matrices.v0.json#decision_family_id=media_choice",
                "selected_option": "explicit asset requirements remain unresolved",
                "rejected_options": ["invented final assets", "silent decorative conversion"],
                "evidence_refs": [build_ref],
                "evidence_state": "unverified",
            },
            {
                "decision_family": "styling_mechanism",
                "decision_card_ref": "kernel/decision-governance/p0-decision-matrices.v0.json#decision_family_id=styling_mechanism",
                "selected_option": "scoped class intent",
                "rejected_options": ["global CSS", "CSS-created meaningful content"],
                "evidence_refs": [implementation_ref],
                "evidence_state": "derived",
            },
        ],
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
                    "run_id": run_state.get("run_id"),
                    "source_kind": source_kind,
                    "stage_output_digests": output_digests,
                    "stage_result_digests": result_digests,
                    "build_tree_digest": run_state.get("build_tree_digest"),
                    "implementation_digest": run_state.get("implementation_digest"),
                    "final_audit_status": _result(run_state, "/final-audit").get("stage_status"),
                },
            }
        ],
    }
