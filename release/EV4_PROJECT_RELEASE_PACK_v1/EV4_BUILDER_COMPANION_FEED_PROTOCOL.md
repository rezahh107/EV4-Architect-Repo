# EV4 Builder Companion Feed Protocol

Status: active_addon_for_post_handoff_builder_execution
Version: 1.0.0
Applies after: `/handoff-export`
Language: Persian builder guidance, English technical identifiers allowed

---

## Purpose

This protocol defines a controlled bridge between a completed EV4 `/handoff-export` and a separate interactive builder chat or implementation assistant.

The main EV4 pipeline produces an audited architecture record. The Builder Companion Feed converts that record into a practical, step-by-step building package without redesigning, re-scoring, or weakening audit boundaries.

Mental model:

```text
EV4 pipeline = architect and auditor
Builder Companion Feed = sealed work order
Builder Companion chat = step-by-step site-building guide
```

---

## Core Rule

```text
Create a builder feed from the audited handoff. Do not create a new design.
```

The feed may explain how to build the selected structure, where classes apply, what to validate, and what not to assume. It must not change the selected candidate, Build_Tree_Payload, Implementation_Payload, Handoff_Payload, audit flags, unknowns, or production boundary.

---

## When To Use

Use this protocol only after `/handoff-export` is complete and one of these is true:

```text
- the user wants a practical step-by-step builder guide;
- the user wants to continue in a separate chat/model;
- the user wants a class creation/application map;
- the user wants an interactive Elementor build companion;
- the user wants a copy-ready feed package for another model.
```

This protocol is optional. It does not replace `/handoff-export`.

---

## Required Inputs

```yaml
required_inputs:
  completed_handoff_export:
    required: true
  selected_candidate_id:
    required: true
  build_tree_payload:
    required: true
  implementation_payload:
    required: true
  final_audit_status:
    required: true
  remaining_unknowns_and_flags:
    required: true
  production_boundary_statement:
    required: true
  before_screenshot_reference:
    required_if_available: true
```

If the completed `/handoff-export` is missing, this protocol must stop and request the missing handoff output.

---

## Forbidden Work

The model must not:

- redesign the section;
- change the selected architecture;
- add new architecture candidates;
- change class names unless explicitly routed as a repair;
- add final CSS values not present in the approved implementation plan;
- invent exact breakpoints, colors, typography, coordinates, or spacing;
- assume card clickability;
- assume mobile connector behavior;
- introduce Dynamic Loop without a confirmed data source;
- claim production readiness;
- use Case Memory, TUYA, RAG, docs, or examples to override the approved handoff.

---

## Required Builder-Facing Outputs

Every Builder Companion Feed must include these sections.

### 1. Class Creation & Application Map

For every class from the approved tree or implementation plan, include:

```yaml
class_name:
related_structure_label:
elementor_node_or_element:
when_to_create:
reusable_or_one_off: reusable | one_off | section_scoped | unknown
purpose:
css_needed_now: yes | no | later | unknown
active_stage_dependency:
notes_or_unknowns:
```

Rules:

- Do not add a class that is not present in the approved payload unless explicitly labeled `proposed_for_user_approval`.
- Explain that Elementor CSS Classes field must use class names without the leading dot.
- Distinguish Structure Panel labels from class names.

### 2. Structure Panel Naming Checklist

For every major node, include:

```yaml
structure_label:
class_name_if_applicable:
element_type:
role:
builder_note:
```

Rules:

- Labels should help a human navigate Elementor Structure Panel.
- Class names should stay machine-readable and follow the approved naming convention.

### 3. Builder Step-by-Step Checklist

The checklist must be practical, small-step, and reversible.

It must sequence the build like this when applicable:

```text
1. create root section/container
2. create main shell or relative stage
3. create normal-flow content/card layer
4. create one representative repeated item
5. apply shared classes
6. duplicate repeated items only after validation
7. create visual core/media layer
8. create decorative/connector layer
9. apply scoped CSS only when explicitly required
10. run desktop QA
11. run responsive/accessibility checks
```

Rules:

- Do not combine unrelated work into one instruction batch.
- Prefer two small related actions per builder turn.
- End each interactive step with an exact confirmation sentence.

### 4. Widget Mapping Table

Include:

```yaml
structure_label:
class_name:
recommended_widget_or_element:
editable_content:
why_this_mapping:
unknowns:
```

### 5. Editable Content Map

Include all text, icons, media, buttons, cards, labels, and assets that must remain editable.

### 6. Asset Replacement Map

Include:

```yaml
asset_role:
current_source:
replacement_needed: yes | no | unknown
alt_decision: meaningful | decorative | unknown
notes:
```

### 7. Scoped CSS Need Map

Include only CSS needs, not full production CSS unless explicitly requested later.

```yaml
class_or_scope:
css_need:
reason:
native_elementor_alternative:
css_allowed_now: yes | no | later
risk:
```

### 8. Responsive QA Checklist

Include desktop/tablet/mobile checks without inventing final values.

Required warnings:

```text
- mobile behavior is not confirmed unless mobile evidence exists;
- connector/overlay behavior must be validated visually;
- cards must not become clickable unless confirmed;
- Dynamic Loop requires a confirmed data source.
```

### 9. What Not To Do

Include the key anti-errors:

```text
- do not put a dot before class names in Elementor CSS Classes field;
- do not flatten meaningful text into SVG/image/HTML;
- do not use absolute positioning for normal content;
- do not make cards clickable unless confirmed;
- do not use Dynamic Loop unless a data source is confirmed;
- do not claim production readiness.
```

---

## Builder Companion Feed Package

When the user wants to continue in another chat/model, output a self-contained feed package.

Required package shape:

```text
# EV4 Builder Companion Feed

## Source Boundary
Use this feed as the source for interactive Elementor building. Do not redesign.

## Reference
- selected_candidate_id:
- handoff_status:
- before_screenshot_reference:
- final_audit_status:
- production_ready_allowed: false

## Why This Structure Was Selected
Short Persian explanation based only on audited recommendation provenance.

## Approved Structure Summary
- Root:
- Main flow layer:
- Repeated content:
- Visual core:
- Decorative/connector layer:

## Class Creation & Application Map
...

## Builder Step-by-Step Mode
Rules for the companion chat:
- respond in Persian;
- preserve English technical identifiers;
- give confirmed/provisional/unknown;
- provide two small related actions per turn after initial analysis;
- ask for screenshot validation at milestones;
- never rebuild from scratch unless evidence requires it.

## Open Unknowns and Do-Not-Assume List
...

## First Interactive Prompt For Builder Companion
...
```

---

## Compatibility With Case Memory

The Builder Companion Feed can later become input to `/post-build-feedback` and Case Memory, but it is not itself a validated case.

Validation level remains unchanged until the user provides post-build feedback and evidence.

---

## Completion Criteria

```yaml
builder_companion_feed_checks:
  source_handoff_used: required
  selected_candidate_preserved: required
  class_map_present: required
  structure_naming_checklist_present: required
  step_by_step_checklist_present: required
  editable_content_map_present: required
  asset_map_present: required
  scoped_css_need_map_present: required
  responsive_qa_checklist_present: required
  forbidden_work_list_present: required
  production_ready_claim_blocked: required
```
