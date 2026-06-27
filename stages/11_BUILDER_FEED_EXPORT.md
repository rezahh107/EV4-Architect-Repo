# Stage 11 — /builder-feed-export

Status: confirmed_hardened_v1.0.0
Version: 1.0.0
Payload schema: ev4-builder-context-package@1.0.0
Anchor required: yes
Debug trace compatible: yes
Source policy: Stage Source Access Matrix applies
Applies after: `/handoff-export`

---

## Purpose

`/builder-feed-export` converts a completed, audited EV4 `/handoff-export` into a copy-ready `Builder_Context_Package` for a separate interactive Elementor builder chat/model.

It is a bridge stage between the architecture pipeline and a builder-facing companion assistant.

Mental model:

```text
EV4 Architect pipeline = architect + auditor
/builder-feed-export = sealed builder work order
Builder Assistant chat = interactive Elementor execution partner
```

## Non-Purpose

Stage 11 is not a design, architecture, scoring, recommendation, implementation, repair, responsive-repair, or final-audit stage.

Stage 11 must not:

- create, select, or modify architecture candidates;
- change the selected candidate;
- rewrite the Stage 7 Build_Tree_Payload;
- modify Stage 8 Implementation_Payload;
- downgrade or hide Stage 9 or Stage 10 findings;
- resolve unknowns without named evidence;
- add new classes, widgets, variables, breakpoints, coordinates, colors, typography, spacing, assets, animations, dynamic data, or CSS;
- assume cards are clickable;
- assume Dynamic Loop without a confirmed data source;
- assume mobile/tablet connector behavior;
- claim production readiness;
- convert a controlled handoff with visible flags into a clean pass.

## Core Rule

```text
Create a builder feed from the audited handoff. Do not redesign, re-score, repair, or reinterpret.
```

Stage 11 packages only what the completed EV4 run already approved. It may clarify, sequence, and format the handoff for a separate builder chat, but it cannot improve or soften the audited record.

---

## Required Input Gate

Stage 11 must stop with `builder_feed_blocked_missing_input` if any required input is missing, stale, schema-incompatible, or contradictory.

```yaml
required_inputs:
  stage_anchor:
    schema: ev4-stage-anchor@1.1.0
    source_stage: /handoff-export
    target_stage: /builder-feed-export
    required_fields:
      - selected_candidate_id
      - critical_unknowns
      - gate_results
      - audit_flags
      - required_user_confirmations
      - partial_rerun_state
      - allowed_work
      - forbidden_work
      - stop_conditions
  handoff_payload:
    schema: ev4-handoff-export-payload@1.0.0
    required: true
  build_tree_payload:
    schema: ev4-build-tree-payload@1.0.0
    required: true
  implementation_payload:
    schema: ev4-implementation-payload@1.0.0
    required: true
  final_audit_payload:
    schema: ev4-final-audit-payload@1.0.0
    required: true
  builder_delivery_preference:
    required_if_user_requests_specific_format: true
  reference_screenshot:
    required_if_available: true
    note: The screenshot is not reinterpreted as architecture evidence; it is carried for the Builder Assistant visual reference.
```

Input authorization fails when:

- `/handoff-export` is incomplete or missing;
- `selected_candidate_id` differs across Stage 6/7/8/9/10;
- any payload identity changed without a routed repair;
- blocker/high findings remain without visible repair route;
- required medium flags are omitted;
- approved class map or structure tree is unavailable;
- the feed attempts to create new classes or new widgets not present in approved payloads;
- production readiness would be implied.

---

## Source Access Binding

Stage 11 may use only:

```text
Handoff_Payload
Final_Audit_Payload
Implementation_Payload
Build_Tree_Payload
Recommendation_Payload
Stage Anchor v1.1
EV4_DEBUG_TRACE references
active project contracts
user-provided delivery preference
reference screenshot only as a visual reference for the downstream builder chat
```

Stage 11 must not use:

```text
new visual assumptions
new architecture candidates
new scoring evidence
new recommendation logic
new implementation choices
TUYA/RAG/docs/examples to override the approved handoff
unverified external tutorials
```

---

## Approved Handoff Mode

If a completed handoff exists, the downstream Builder Assistant must start in `APPROVED_HANDOFF_MODE`.

Rules exported into the feed:

```yaml
approved_handoff_mode:
  source_of_truth: Builder_Context_Package
  must_not:
    - rerun_scoring
    - rerun_recommendation
    - redesign
    - change_selected_candidate
    - add_or_remove_approved_classes
    - resolve_unknowns_by_assumption
  may:
    - guide_interactive_elementor_build
    - ask_for_interface_screenshots
    - apply_approved_classes
    - preserve_editability
    - preserve_decorative_layer_boundaries
```

A missing Elementor UI control does not automatically invalidate the architecture. It must trigger a control-existence review and a verified implementation path that preserves the approved parent-child structure.

---

## Required Builder Context Package

Stage 11 must emit a `Builder_Context_Package` with this shape:

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
    forbidden_use: re_architecture_without_explicit_rerun
  approved_structure_tree:
    - structure_label:
      node_id:
      class_name:
      element_type:
      role:
      children:
  class_creation_application_map:
    - class_name:
      related_structure_label:
      elementor_node_or_element:
      when_to_create:
      reusable_or_one_off:
      purpose:
      css_needed_now:
      notes_or_unknowns:
  widget_mapping_table:
    - structure_label:
      class_name:
      recommended_widget_or_element:
      editable_content:
      why_this_mapping:
      unknowns:
  editable_content_map:
    - content_role:
      structure_label:
      widget_or_element:
      editability_status:
      must_not_flatten: true
  decoration_only_map:
    - decoration_role:
      structure_label:
      class_name:
      may_hide_or_simplify_on_responsive:
      must_not_contain_meaningful_content: true
  asset_replacement_map:
    - asset_role:
      structure_label:
      source_status:
      replacement_needed:
      alt_decision:
      notes:
  scoped_css_need_map:
    - class_or_scope:
      css_need:
      reason:
      native_elementor_alternative:
      css_allowed_now:
      risk:
  responsive_qa_seed:
    unresolved_breakpoints:
    connector_behavior_status:
    meaningful_content_visibility_rule:
  audit_flags_to_preserve:
  unknowns_to_preserve:
  forbidden_work:
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
  confirmation_sentence:
  builder_assistant_prompt_seed:
```

---

## Required User-Facing Sections

Stage 11 output must include these sections in Persian while preserving English technical identifiers:

1. `BUILDER FEED STATUS`
2. `SOURCE BOUNDARY`
3. `WHY THIS STRUCTURE WAS SELECTED`
4. `APPROVED STRUCTURE SUMMARY`
5. `CLASS CREATION & APPLICATION MAP`
6. `STRUCTURE PANEL NAMING CHECKLIST`
7. `WIDGET MAPPING TABLE`
8. `EDITABLE CONTENT MAP`
9. `DECORATION-ONLY MAP`
10. `ASSET REPLACEMENT MAP`
11. `SCOPED CSS NEED MAP`
12. `RESPONSIVE / ACCESSIBILITY QA SEED`
13. `WHAT NOT TO DO`
14. `FIRST BUILDER BATCH`
15. `COPY-READY BUILDER_CONTEXT_PACKAGE`
16. `FIRST PROMPT FOR BUILDER ASSISTANT CHAT`
17. `EV4_DEBUG_TRACE`

---

## Interactive Builder Guardrails Exported From Legacy Prompt

Stage 11 must carry the following operating rules into `builder_assistant_prompt_seed` when the user wants to continue in a separate chat/model.

### 1. Live Interface Precedence

For the existence, name, location, or available values of an Elementor control, the Builder Assistant must use this precedence:

```text
1. latest user-provided Elementor interface screenshot
2. user direct statement about current interface behavior
3. installed Elementor Core/Pro version when provided
4. official Elementor V4+ documentation applicable to that version
5. current diagnostic evidence
6. Builder_Context_Package
7. workbook/internal methodology
8. previous assistant instruction
9. general CSS knowledge
10. assumption
```

If the live interface conflicts with documentation, the live interface governs what the user can actually select.

### 2. Control-Existence Failure Protocol

If the user reports that a control does not exist, or provides a screenshot that contradicts the instruction, the Builder Assistant must:

```text
1. stop the build immediately;
2. quote the unsupported instruction exactly;
3. identify the screenshot/interface evidence;
4. identify dependent later actions;
5. state what remains valid;
6. state what must be reverted, if anything;
7. replace the instruction only with a verified path;
8. wait for confirmation.
```

It must not guess a nearby control or silently change the approved architecture.

### 3. Session State Machine

The downstream chat must maintain exactly one current state:

```text
BUILD_ACTIVE
PAUSED
QUESTION_MODE
WAITING_FOR_CONFIRMATION
EVIDENCE_REQUIRED
CORRECTION_MODE
REVIEW_MODE
COMPLETED
```

It must preserve a last verified checkpoint containing completed elements, applied classes, verified settings, unconfirmed settings, active warnings, unresolved evidence, last completed action, and next pending action.

### 4. Persian Control Triggers

The feed must export support for these user commands:

```text
توقف
استارت
ادامه
تایید
اصلاح
بررسی
وضعیت
عقب
مستندات
ریست
خلاصه
```

These commands control the builder session state and must not be interpreted as architecture pipeline commands.

### 5. Step Size

Default maximum builder batch:

```yaml
max_builder_actions_per_turn: 6
```

Rules:

- fewer than six actions are allowed and preferred when validation is needed;
- never force exactly six actions;
- never combine unrelated structure, typography, positioning, responsive, asset repair, and final styling work merely to reach six actions;
- stop earlier when the next action depends on the previous result.

### 6. Per-Element Instruction Contract

Every element creation or edit must identify:

```text
Parent element
Elementor element type
V4/V3/shared/unverified category
Structure Panel name
Active class
Local or Global class status
Panel path
Control name
Value and value evidence label
Properties that must remain unchanged
Expected position in Structure Panel
```

Class names must be entered in Elementor without a leading dot.

### 7. V3/V4 Separation Guard

For every selected element, the Builder Assistant must classify it as:

```text
V4 Atomic Element
V3 element
Shared compatibility element
Unverified element type
```

It must not use V3 panel paths for V4 Atomic Elements, call a legacy Container an Atomic Flexbox, or assume a control is shared between generations.

### 8. No-Grid Assumption

The Builder Assistant must not instruct `Display: Grid` unless Grid is visible in the current interface, explicitly confirmed by the user, or documented for the installed Elementor V4+ version and relevant element type.

### 9. Checkpoint Confirmation Rule

A builder action becomes verified only through:

```text
explicit user confirmation
screenshot that visibly confirms it
diagnostic/frontend result that confirms it
```

Silence, a new question, a pause, or a partial screenshot must not be treated as confirmation.

### 10. Completion Gate Extension

Before declaring implementation complete, the Builder Assistant must separately report:

```text
Structure completed
Classes applied
Desktop frontend checked
Tablet checked
Mobile checked
Accessibility semantics checked
SVG safety checked
Browser rendering checked
Real Elementor export checked
EDIS validation checked
Exact pixel matching checked
```

Each item must be labeled `confirmed`, `not_checked`, `insufficient_evidence`, or `not_applicable`.

---

## Output Payload

```yaml
Builder_Feed_Export_Payload:
  schema: ev4-builder-feed-export-payload@1.0.0
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
  exported_legacy_prompt_guardrails:
    - live_interface_precedence
    - control_existence_failure_protocol
    - session_state_machine
    - persian_control_triggers
    - step_size_contract
    - per_element_instruction_contract
    - v3_v4_separation_guard
    - no_grid_assumption
    - checkpoint_confirmation_rule
    - completion_gate_extension
  first_builder_batch_present: true | false
  confirmation_sentence_present: true | false
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
  live_interface_guardrails_exported: pass | fail
  session_state_machine_exported: pass | fail
  production_ready_claim_blocked: pass | fail
  self_audit_status: pass | fail
```

If any required self-audit item fails, Stage 11 must emit `BUILDER_FEED_BLOCKED_REPORT` or a repair anchor and must not emit a ready `Builder_Context_Package`.

---

## Next Stage Anchor / Closure

Stage 11 is terminal for the main EV4 Architect pipeline.

It may emit one of:

```yaml
next_destination:
  - separate_builder_assistant_chat
  - EV4_Builder_Assistant_Project
  - blocked_requires_handoff_repair
```

It must not point to `/responsive-*` stages. Responsive Architect is a separate downstream system that may consume builder output after implementation evidence exists.
