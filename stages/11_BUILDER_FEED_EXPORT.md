# Stage 11 — /builder-feed-export

Status: role_aligned_compatibility_export_v1.2.0  
Version: 1.2.0  
Payload schema: `ev4-architect-builder-feed-export@1.0.0`  
Legacy compatibility schema: `ev4-builder-context-package@1.0.0` is deprecated for Architect-only exports  
Anchor required: yes  
Applies after: `/handoff-export`

---

## Purpose

`/builder-feed-export` packages the audited `/handoff-export` as a non-executable Architect handoff and CE intake source.

It does not produce a Builder-runtime intake package by default. It does not authorize Builder execution and it must not bypass the Constructability Engineer.

Builder execution is allowed only after CE constructability proof is present and Builder-side intake validation passes.

---

## Boundary

Stage 11 packages only approved handoff data.

It preserves:

```text
selected_candidate_id
approved_structure_tree
class_creation_application_map
approved widget/content/decoration maps
forbidden_work
visible audit flags
unknowns_to_preserve
production_ready_allowed: false
```

It does not add classes, widgets, breakpoints, CSS, clickability, Dynamic Loop assumptions, mobile/tablet connector behavior, Golden Reference locking, Builder package-gate authorization, or executable strategy.

---

## Required Architect Builder Feed Export

Stage 11 emits:

```yaml
Architect_Builder_Feed_Export:
  schema: ev4-architect-builder-feed-export@1.0.0
  source_stage: /builder-feed-export
  source_handoff_stage: /handoff-export
  packet_purpose: ce_intake_source
  intended_consumer: constructability_engineer
  ce_review_required: true
  requires_constructability_engineer_review: true
  builder_executable_allowed: false
  builder_ready_status: not_builder_ready_without_ce_proof
  package_status: ready | ready_with_visible_flags | blocked
  selected_candidate_id:
  selected_candidate_locked: true
  production_ready_allowed: false
  source_payload_ledger:
    - Handoff_Payload
    - Final_Audit_Payload
    - Implementation_Payload
    - Build_Tree_Payload
    - Recommendation_Payload
  reference_screenshot_instruction:
    required_in_new_chat: true
    allowed_use: visual_reference_only
    forbidden_use: do_not_infer_reference_paradigm_or_responsive_behavior
  approved_structure_tree: []
  class_creation_application_map: []
  widget_mapping_table: []
  editable_content_map: []
  decoration_only_map: []
  asset_replacement_map: []
  scoped_css_need_map: []
  responsive_qa_seed:
    unresolved_breakpoints:
    connector_behavior_status:
    meaningful_content_visibility_rule:
  audit_flags_to_preserve: []
  unknowns_to_preserve: []
  forbidden_work: []
  first_suggested_builder_batch:
    max_actions:
    actions: []
  confirmation_request_seed:
    confirmation_id: CONFIRM-BATCH-001
    confirmed_action_ids: []
    expected_user_token: تایید BATCH-001
    template_id: standard_batch_confirmation
```

`first_suggested_builder_batch` and `confirmation_request_seed` are CE intake data only. They are not Builder execution authorization.

---

## Compatibility Mapping

Historical Architect exports used:

```yaml
schema: ev4-builder-context-package@1.0.0
Builder_Context_Package:
```

That historical name is now compatibility-only when produced by Architect.

Compatibility exports must declare:

```yaml
compatibility_note: architect_export_legacy_name_not_builder_runtime_intake
packet_purpose: ce_intake_source
intended_consumer: constructability_engineer
ce_review_required: true
builder_executable_allowed: false
builder_ready_status: not_builder_ready_without_ce_proof
```

Builder must not treat an Architect-only compatibility export as execution-ready unless CE proof has been added and Builder adapter validation passes.

---

## Architect-Owned Intent Fields

Architect may own and emit design-level intent only:

```yaml
reference_role: inspiration_only | visual_direction | candidate_source_evidence
desired_outcome: string
high_level_design_intent: string
experience_intent: advisory object
source_visual_evidence_registration:
  evidence_id:
  evidence_type:
  source_ref:
  allowed_use: design_level_reference_only
```

Architect must not own:

```text
- final Golden Reference locking
- Builder Executable Package issuance
- Builder runtime intake authorization
- Builder batch execution strategy
- final visual parity result
- responsive tablet/mobile reference-family authorization
```

---

## Required User-Facing Sections

Stage 11 output includes Persian user-facing sections while keeping technical identifiers in English. It must say explicitly that the output is not Builder-ready until CE emits an executable package and Builder validates the runtime intake package.
