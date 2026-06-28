# Stage 11 — /builder-feed-export

Status: confirmed_hardened_v1.1.0
Version: 1.1.0
Payload schema: ev4-builder-context-package@1.0.0
Anchor required: yes
Applies after: `/handoff-export`

---

## Purpose

`/builder-feed-export` converts the audited `/handoff-export` into a copy-ready `Builder_Context_Package` for EV4 Builder Assistant.

It is a terminal packaging stage. It does not redesign, rescore, repair, or implement the section.

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

It does not add classes, widgets, breakpoints, CSS, clickability, Dynamic Loop assumptions, or mobile/tablet connector behavior.

---

## Required Builder Context Package

Stage 11 emits:

```yaml
Builder_Context_Package:
  schema: ev4-builder-context-package@1.0.0
  source_stage: /builder-feed-export
  source_handoff_stage: /handoff-export
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
  first_builder_batch:
    max_actions:
    actions:
      - action_id:
        target_element:
        parent:
        element_type:
        structure_panel_name:
        active_class:
        instruction:
        properties_not_to_change:
        expected_result:
  confirmation_request:
    confirmation_id: CONFIRM-BATCH-001
    confirmed_action_ids:
      - BATCH-001-A01
      - BATCH-001-A02
      - BATCH-001-A03
    expected_user_token: تایید BATCH-001
    template_id: standard_batch_confirmation
```

---

## Structured Confirmation Rule

New exports use `confirmation_request` only.

```yaml
confirmation_request:
  required_fields:
    - confirmation_id
    - confirmed_action_ids
    - expected_user_token
    - template_id
  template_id: standard_batch_confirmation
```

`confirmation_request.confirmed_action_ids` must match existing `first_builder_batch.actions[*].action_id` values.

Legacy fields are not emitted in new packages:

```text
confirmation_sentence
builder_assistant_prompt_seed
```

If legacy package data is imported, treat those fields as compatibility notes, not checkpoint authority.

---

## Required User-Facing Sections

Stage 11 output includes these Persian sections while keeping technical identifiers in English:

1. `BUILDER FEED STATUS`
2. `SOURCE BOUNDARY`
3. `APPROVED STRUCTURE SUMMARY`
4. `CLASS CREATION & APPLICATION MAP`
5. `STRUCTURE PANEL NAMING CHECKLIST`
6. `WIDGET MAPPING TABLE`
7. `EDITABLE CONTENT MAP`
8. `DECORATION-ONLY MAP`
9. `ASSET REPLACEMENT MAP`
10. `SCOPED CSS NEED MAP`
11. `RESPONSIVE / ACCESSIBILITY QA SEED`
12. `WHAT NOT TO DO`
13. `FIRST BUILDER BATCH`
14. `COPY-READY BUILDER_CONTEXT_PACKAGE`
15. `FIRST PROMPT FOR BUILDER ASSISTANT CHAT`
16. `EV4_DEBUG_TRACE`

---

## Output Payload

```yaml
Builder_Feed_Export_Payload:
  schema: ev4-builder-feed-export-payload@1.1.0
  source_stage: /builder-feed-export
  source_handoff_stage: /handoff-export
  package_status: ready | ready_with_visible_flags | blocked
  builder_context_package_schema: ev4-builder-context-package@1.0.0
  selected_candidate_id:
  selected_candidate_preserved: true | false
  build_tree_payload_preserved: true | false
  implementation_payload_preserved: true | false
  handoff_payload_preserved: true | false
  new_architecture_created: false
  new_classes_created: false
  final_css_written: false
  production_ready_claim: false
  first_builder_batch_present: true | false
  confirmation_request_present: true | false
  legacy_confirmation_sentence_present: false
  legacy_prompt_seed_present: false
  debug_trace_ref_or_payload:
```

---

## Self-Audit

```yaml
stage_11_self_audit:
  completed_handoff_used: pass | fail
  selected_candidate_preserved: pass | fail
  build_tree_payload_preserved: pass | fail
  implementation_payload_preserved: pass | fail
  audit_flags_preserved: pass | fail
  unknowns_preserved: pass | fail
  no_new_classes_added: pass | fail
  no_final_css_written: pass | fail
  no_redesign_or_rescore: pass | fail
  approved_handoff_mode_exported: pass | fail
  confirmation_request_present: pass | fail
  confirmation_request_action_ids_match_first_batch: pass | fail
  no_legacy_runtime_confirmation_fields: pass | fail
  production_ready_claim_blocked: pass | fail
  self_audit_status: pass | fail
```

If any required self-audit item fails, emit `BUILDER_FEED_BLOCKED_REPORT` and do not emit a ready `Builder_Context_Package`.
