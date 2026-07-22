# Stage 8 — /implementation

Status: confirmed_hardened_v1.0.0
Version: 1.0.0
Payload schema: ev4-implementation-payload@1.0.0
Validation transaction required for continuation: yes; current profile blocked
Debug trace compatible: yes
Source policy: Stage Source Access Matrix applies
Active Manifest version: 1.0.1 via `stages/STAGE_8_10_v1.0.1_HARDENING_ALIGNMENT_PATCH.md`
Validation Profile: `blocked_missing_semantics`
Continuation authorization: blocked. This document does not define an executable Anchor template; enablement requires a canonical active payload Schema, registered semantic handler, deterministic repair ownership, and independent Bundle regeneration.

## Purpose

`/implementation` converts the approved `/build-tree` output into an implementation-ready Elementor V4 plan.

It maps the approved tree to Elementor elements, widgets, classes, variables, responsive controls, asset requirements, accessibility requirements, and scoped CSS needs.

## Non-Purpose

Stage 8 is not a design, architecture, scoring, recommendation, or final audit stage.

Stage 8 must not:

- create a new architecture candidate;
- change the selected candidate;
- improve or reduce scores;
- override `/score-audit` or `/recommend`;
- reinterpret the original screenshot;
- silently drop unknowns;
- invent exact assets, copy, coordinates, breakpoints, plugin availability, dynamic sources, or export behavior;
- convert meaningful editable content into static images, SVG paths, or hard-coded HTML;
- create hidden global CSS;
- mark implementation as production-ready when required verification evidence is missing.

## Core Rule

```text
Implement the approved tree. Do not redesign it.
```

Every implementation decision must trace back to one of:

1. `Build_Tree_Payload`;
2. independently regenerated `VALIDATION BUNDLE` from an implemented `/build-tree` profile, currently unavailable;
3. prior approved pipeline payloads carried forward by the verified transaction;
4. official Elementor documentation for platform-capability claims;
5. verified export/runtime evidence, if available;
6. user-provided implementation constraints;
7. TUYA internal concepts only as conceptual guidance.

## Required Input Gate

Stage 8 must stop with `fail_requires_implementation_input_repair` if any required input is missing.

Required inputs:

```yaml
required_inputs:
  validation_bundle:
    schema: ev4-architect-validation-bundle@1.2.0
    contained_anchor_schema: ev4-stage-anchor@1.4.0
    source_stage: /build-tree
    target_stage: /implementation
  build_tree_payload:
    schema: ev4-build-tree-payload@1.0.0
    required_fields:
      - selected_candidate_id
      - selected_candidate_family
      - structure_tree
      - naming_map
      - wrapper_justifications
      - content_editability_map
      - overlay_decoration_map
      - responsive_structure_contract
      - design_system_hook_map
      - carried_forward_unknowns
      - required_user_confirmations
      - implementation_blockers
      - implementation_allowed
      - stage_8_bundle_required
  prior_stage_payload_refs:
    - Recommendation_Payload
    - Score_Audit_Payload
    - relevant Stage 2 decomposition summary
    - relevant Stage 3 selected candidate premise
  source_access_state:
    - official_docs_available: yes | no
    - export_evidence_available: yes | no
    - tuya_reference_available: yes | no
```

Input authorization fails when:

- `implementation_allowed: false`;
- `decision_requires_user_input` is active;
- required user confirmation remains unresolved;
- selected candidate is absent or ambiguous;
- Stage 7 tree lacks required node schemas;
- Stage 7 responsive contract is absent;
- Stage 7 has unapproved plugin, HTML, SVG, or overlay dependency;
- Build_Tree_Payload schema is older than `ev4-build-tree-payload@1.0.0` with no explicit compatibility note;
- Validation Bundle is missing, outdated, not independently reproducible, or comes from a non-executable source profile.

If input authorization fails, Stage 8 must output a `BLOCKED REPAIR REPORT` and must not emit `Implementation_Payload`.

## Stage Source Access Matrix Binding

Stage 8 may use:

```text
Stage 7 Build_Tree_Payload
Validation Bundle
official Elementor docs
widget/settings references
TUYA internal concepts
verified export evidence, if available
user-provided implementation constraints
```

Stage 8 must not use:

```text
new visual assumptions
new scoring evidence
new recommendation preference signals
new candidate families
unverified third-party tutorials as capability proof
TUYA concepts as official Elementor capability proof
```

Source classification is mandatory for every retrieved fact:

```yaml
source_fact:
  source_id:
  source_type: official_docs | release_notes | export_evidence | project_contract | internal_concept_reference | user_input | secondary_source
  retrieved_claim:
  applies_to_stage: /implementation
  fact_class: platform_capability | project_default | project_conceptual_model | project_specific_behavior | implementation_observation | unsupported_claim
  confidence: high | medium | low
  limitation:
  allowed_use:
```

Official docs can prove Elementor capability. They cannot prove that the current section should use that capability unless Stage 7 already selected the relevant structure.

TUYA can guide thinking order and terminology. It cannot prove platform capability or resolve project-specific unknowns.

## Recommended Official Source Ledger

When Stage 8 uses Elementor-specific capability claims, include a `SOURCE LEDGER`.

Minimum source ledger shape:

```yaml
source_ledger:
  - source_id:
    title:
    url:
    source_type: official_docs | release_notes | export_evidence | project_contract | internal_concept_reference | user_input
    retrieved_date:
    last_update_if_available:
    fact_class:
    allowed_use:
    limitation:
```

Known useful official docs to verify during a run:

```yaml
official_docs_candidates:
  - source_id: elementor-v4-flexbox-element
    title: Flexbox element
    url: https://elementor.com/help/flexbox-element/
    allowed_use: verify Flexbox as a container element and verify its broad settings categories
  - source_id: elementor-v4-classes
    title: Classes in Elementor
    url: https://elementor.com/help/classes-in-elementor-2/
    allowed_use: verify local/global class behavior and class hierarchy concepts
  - source_id: elementor-v4-variables
    title: Variables
    url: https://elementor.com/help/variables/
    allowed_use: verify variable concept, current limitations, and relationship to classes
  - source_id: elementor-v4-custom-css-element
    title: Add Custom CSS to an element
    url: https://elementor.com/help/add-custom-css-to-an-element/
    allowed_use: verify class-scoped custom CSS behavior and device/state CSS handling
  - source_id: elementor-container-overview
    title: How do I learn about Flexbox Containers?
    url: https://elementor.com/help/container-element/
    allowed_use: verify container intent, responsive control framing, and container documentation entry points
```

If a document is unavailable, outdated, or ambiguous, the relevant capability must be marked `unknown` or `requires verification`.

## Authoritative Source Order

When sources conflict, use this order:

1. User-provided hard constraints for the current project.
2. Valid Validation Bundle and carried-forward blockers.
3. Stage 7 `Build_Tree_Payload`.
4. Stage 6 `Recommendation_Payload`.
5. Stage 5 audit restrictions.
6. Stage 4 scoring constraints and caps.
7. Stage 2/3 evidence and candidate premise.
8. Official Elementor documentation for platform capability.
9. Verified Elementor export/runtime evidence for project-specific implementation observation.
10. Project defaults and active EV4 contracts.
11. TUYA internal concept reference.
12. Secondary sources.

If official docs conflict with TUYA, official docs win for platform capability.
If Stage 7 conflicts with Stage 6, Stage 8 must stop and route repair to `/build-tree` or `/recommend`.

## Output Format

Stage 8 must output these sections in order:

1. `INPUT AUTHORIZATION`
2. `SOURCE LEDGER`
3. `IMPLEMENTATION SUMMARY`
4. `ELEMENTOR SETTINGS PLAN`
5. `WIDGET MAPPING`
6. `CLASS AND VARIABLE APPLICATION MAP`
7. `SCOPED CSS NEED MAP`
8. `ASSET AND ACCESSIBILITY MAP`
9. `RESPONSIVE IMPLEMENTATION PLAN`
10. `POSITION / LAYERING IMPLEMENTATION PLAN`
11. `DYNAMIC DATA / INTERACTION PLAN`
12. `IMPLEMENTATION RISKS`
13. `STAGE 8 SELF-AUDIT`
14. `Implementation_Payload`
15. `EV4_DEBUG_TRACE` if debug mode is active
16. `VALIDATION PROFILE BLOCKED REPORT` — no Bundle while this profile remains blocked

## Elementor Settings Plan Schema

Each implementation target must use this schema:

```yaml
elementor_settings_plan:
  - source_tree_node_id:
    source_structure_label:
    source_class_name:
    element_type: section_container | container | widget | decoration_layer | overlay_stage | svg_layer | html_layer | loop_item | template_ref
    elementor_element:
      proposed_element: Flexbox | Grid | Div Block | Heading | Paragraph | Button | Image | Icon | HTML | SVG | Loop/Grid | Template | Other | Unknown
      widget_or_element_source: official_docs | build_tree | export_evidence | unknown
      pro_dependency: yes | no | unknown
      third_party_dependency: yes | no | unknown
      dependency_authorized_by: Stage 6 | user | none
    content_binding:
      content_source: existing_copy | existing_asset | user_input_needed | dynamic_source | decorative_none | unknown
      editable_in_elementor: yes | no | partial | unknown
      meaningful_content_preserved: yes | no | partial | unknown
    controls:
      layout:
        display:
        direction:
        align_items:
        justify_content:
        gap:
        wrap:
        value_policy: exact_from_payload | infer_from_tree | needs_builder_verification | unknown
      size:
        width:
        min_width:
        max_width:
        height:
        min_height:
        max_height:
        unit_policy: px | rem | em | percent | vw | vh | auto | clamp | variable | unknown
        value_policy:
      spacing:
        margin:
        padding:
        gap:
        value_policy:
      position:
        position_type: default | relative | absolute | fixed | sticky | unknown
        offset_policy:
        containing_stage:
        z_index_policy:
      background:
        type: none | color | image | gradient | video | unknown
        asset_ref:
        value_policy:
      typography:
        tag:
        variable_ref:
        class_ref:
        value_policy:
      border_effects:
        radius_ref:
        shadow_ref:
        transform_or_motion:
        value_policy:
      attributes:
        html_tag:
        aria:
        custom_attributes:
        link_behavior:
      custom_css:
        required: yes | no | unknown
        css_need_ids: []
      responsive:
        desktop:
        tablet:
        mobile:
        unknowns:
    source_refs:
      build_tree_refs: []
      official_doc_refs: []
      export_refs: []
      tuya_refs: []
    risks:
    verification_needed:
```

Rules:

- Use `exact_from_payload` only when the value is explicitly present in the input payload or verified export evidence.
- Use `infer_from_tree` only for broad control categories implied by the tree, not numeric values.
- Use `needs_builder_verification` for builder-facing values that require live Elementor confirmation.
- Use `unknown` when no safe basis exists.
- Do not invent exact pixels, percentages, breakpoints, animation timing, or z-index values unless they were provided upstream or verified.

## Widget Mapping Schema

```yaml
widget_mapping:
  - source_tree_node_id:
    structure_label:
    role:
    recommended_elementor_widget_or_element:
    acceptable_alternatives:
    rejected_widgets:
      - widget:
        reason:
    editable_content_policy:
    semantic_tag_policy:
    accessibility_requirement:
    dynamic_data_requirement:
    pro_or_plugin_dependency:
      status: none | pro_required | third_party_required | unknown
      authorized: yes | no | n/a
    source_refs:
    fallback_if_unavailable:
```

Widget mapping rules:

- Headings must remain editable headings or semantically equivalent editable text elements.
- Body copy must remain editable text/paragraph content.
- CTA must remain editable and link-capable.
- Meaningful images must remain asset-manageable with alt text.
- Decoration may use CSS/SVG/HTML only if Stage 7 marked it decoration-only or visual-core and meaningful content is not trapped.
- HTML widgets require explicit authorization when they carry anything beyond decoration or controlled visual markup.
- If a widget requires Elementor Pro or a third-party plugin, Stage 8 must verify authorization from Stage 6 or user constraints.

## Class and Variable Application Map Schema

```yaml
class_variable_application_map:
  - class_name:
    source_tree_node_id:
    class_scope: local | section-reusable | global-candidate | global-confirmed
    class_origin: Stage 7 | existing_design_system | new_in_stage_8 | unknown
    applies_to:
    properties_owned:
      - layout
      - spacing
      - typography
      - color
      - radius
      - shadow
      - position
      - motion
      - state
      - responsive
    variable_refs:
      - variable_name:
        variable_type: font_family | text_color | font_size | spacing | color | radius | shadow | motion | unknown
        source: existing | proposed | unknown
        value_policy: exact | placeholder | needs_design_system_confirmation | unknown
    local_override_allowed: yes | no | limited | unknown
    conflict_risk: none | low | medium | high | unknown
    promotion_rule:
    notes:
```

Class and variable rules:

- Repeated patterns should use reusable classes.
- One-off coordinates and section-specific exceptions should stay local.
- Do not promote a class to global unless reuse value is confirmed.
- Do not create class conflicts knowingly.
- Variables should represent stable repeated values, not one-off guesses.
- If current Elementor documentation limits variables to specific property classes, Stage 8 must not claim broader support without stronger evidence.
- Classes and variables must preserve Stage 7 naming intent and design-system hook map.

## Scoped CSS Need Map

Stage 8 does not need to write final CSS unless the user explicitly requests production CSS or an export implementation patch. It must define CSS needs and scoping boundaries.

```yaml
scoped_css_need_map:
  - css_need_id:
    source_tree_node_id:
    target_class_name:
    css_scope: selected_class | child_of_selected_class | state | responsive_device | media_query | unknown
    purpose:
    allowed_property_families:
      - layout
      - position
      - size
      - visual_effect
      - animation
      - interaction_state
      - accessibility_support
    forbidden_property_families:
    selector_policy:
      selector_root:
      selector_examples_allowed:
      selector_examples_forbidden:
    responsive_scope:
      desktop:
      tablet:
      mobile:
      media_query_allowed: yes | no | needs_verification
    state_scope:
      normal:
      hover:
      focus:
      active:
    content_safety:
      meaningful_content_created_by_css: yes | no
      meaningful_content_hidden_by_css: yes | no
    verification_needed:
```

### Scoped CSS Validator

Before emitting `Implementation_Payload`, run this validator:

```yaml
scoped_css_validator:
  - check: css is attached to an approved selected class or local element scope
    pass: true | false
  - check: no rule targets html, body, unrelated global selectors, or theme-wide selectors
    pass: true | false
  - check: no meaningful text or asset is generated only through CSS
    pass: true | false
  - check: no meaningful mobile content is hidden without Stage 6 authorization
    pass: true | false
  - check: position:absolute is used only inside an approved containing stage
    pass: true | false | n/a
  - check: z-index does not decide reading order
    pass: true | false | n/a
  - check: CSS state/device scope is explicit when used
    pass: true | false | n/a
  - check: selector does not leak outside the section or component
    pass: true | false
  - check: custom CSS need is justified by a gap in native controls
    pass: true | false
```

If any required CSS validator check fails, Stage 8 must output `fail_requires_css_scope_repair`.

## Asset and Accessibility Map Schema

```yaml
asset_accessibility_map:
  - asset_id:
    source_tree_node_id:
    asset_type: image | icon | svg | video | lottie | background | document | unknown
    role: meaningful | decorative | visual_core | unknown
    source_status: provided | missing | dynamic | existing_library | needs_user | unknown
    alt_text_policy:
      required: yes | no | unknown
      source: user_provided | infer_from_context | decorative_empty | needs_user | unknown
      final_alt_text:
    caption_or_label_requirement:
    responsive_asset_requirement:
      desktop:
      tablet:
      mobile:
    optimization_requirement:
      compression:
      format:
      lazy_loading:
      dimensions:
    rights_or_license_status: confirmed | assumed | unknown | n/a
    replacement_if_missing:
    implementation_blocker: yes | no
```

Rules:

- Meaningful images require alt text or a `needs_user` flag.
- Decorative images may use empty alt only if Stage 7 marked them decoration-only or Stage 8 can trace the decorative role to prior payloads.
- Missing required assets are blockers unless the implementation can safely use a user-provided placeholder policy.
- Do not invent asset filenames, dimensions, license status, or media variants.

## Responsive Implementation Plan

Stage 8 converts Stage 7 responsive structure into builder-facing implementation checks. It must not invent final breakpoints.

```yaml
responsive_implementation_plan:
  breakpoint_source: site_settings | Elementor_default | user_provided | unknown
  breakpoint_values:
    desktop:
    tablet:
    mobile:
    value_policy: exact | inherited | not_available | needs_builder_verification
  groups:
    - source_tree_node_id:
      structure_label:
      desktop_behavior:
      tablet_behavior:
      mobile_behavior:
      responsive_controls_to_verify:
        - direction
        - order
        - width
        - min_height
        - gap
        - padding
        - typography
        - visibility
        - position
        - overflow
      hide_or_simplify_policy:
      collision_risks:
      reading_order_check:
      unknowns_carried_forward:
```

### Responsive Examples

These are examples of output shape, not default values:

```yaml
example_normal_flow_card_grid:
  desktop_behavior: row/grid layout per Stage 7
  tablet_behavior: may reduce columns only if Stage 7 permits
  mobile_behavior: stack in logical reading order
  controls_to_verify: [direction, order, gap, width, padding, typography]
  forbidden: hide meaningful cards to make the layout easier

example_relative_visual_stage:
  desktop_behavior: relative stage contains visual core plus decoration
  tablet_behavior: verify contained decorations do not collide
  mobile_behavior: simplify or hide only decoration-only layers if authorized
  controls_to_verify: [position, overflow, z-index, stage size, visual-core scale]
  forbidden: move meaningful content into absolute overlays

example_cta_group:
  desktop_behavior: inline or grouped per Stage 7
  tablet_behavior: verify tap target and wrapping
  mobile_behavior: stack or full-width only if consistent with design intent
  controls_to_verify: [gap, width, typography, alignment, link behavior]
  forbidden: convert CTA to a non-editable image
```

## Position / Layering Implementation Plan

```yaml
position_layering_plan:
  - source_tree_node_id:
    structure_label:
    position_type: default | relative | absolute | fixed | sticky | unknown
    containing_stage_required: yes | no | n/a
    containing_stage_node_id:
    layer_role: content | decoration | visual_core | connector | overlay | unknown
    z_index_policy:
    overflow_policy:
    collision_risk:
    mobile_behavior:
    accessibility_effect:
    repair_if_invalid:
```

Rules:

- Content stays in normal flow unless a prior audited decision explicitly allows otherwise.
- Floating decoration must live inside a named relative stage.
- Absolute positioning must not control reading order.
- Overlay and connector layers must not escape the section/component boundary.
- If mobile overlay behavior is unknown, keep it visible as an implementation risk and carry it to `/final-audit`.

## Dynamic Data / Interaction Plan

```yaml
dynamic_interaction_plan:
  - source_tree_node_id:
    requirement_type: static | dynamic_data | link | hover_state | animation | form | carousel | loop | filter | unknown
    source_authorization: Stage 6 | Stage 7 | user | none | unknown
    elementor_feature_or_widget:
    pro_dependency: yes | no | unknown
    third_party_dependency: yes | no | unknown
    accessibility_requirement:
    fallback:
    implementation_blocker: yes | no
```

Rules:

- Do not add interactions because they feel modern.
- Do not add dynamic data unless Stage 6/7 or user constraints require it.
- Any Pro, plugin, loop, form, carousel, or filter dependency must be authorization-checked.
- Hover-only content disclosure is not acceptable for meaningful content unless an accessible non-hover path exists.

## Implementation Risks

Stage 8 must list all risks using this schema:

```yaml
implementation_risks:
  - risk_id:
    risk_type: missing_asset | unknown_widget | pro_dependency | plugin_dependency | responsive_collision | class_conflict | css_leakage | accessibility | performance | export_unknown | dynamic_unknown | other
    source_tree_node_id:
    severity: blocker | high | medium | low
    evidence:
    effect:
    mitigation:
    owner_stage: /implementation | /build-tree | /recommend | /architectures | /research | user
    carry_to_final_audit: yes | no
```

Risk handling:

- `blocker` means do not authorize `/final-audit`; record it in the non-authorizing blocked repair report.
- `high` means `/final-audit` may run only if the risk is explicitly carried and audited.
- `medium` and `low` must still appear in `Implementation_Payload`.

## Stage 8 Self-Audit

Before emitting `Implementation_Payload`, Stage 8 must verify:

```yaml
stage_8_self_audit:
  - check: valid Validation Bundle v1.2 received
    result: pass | fail
  - check: valid Build_Tree_Payload v1.0.0 received
    result: pass | fail
  - check: no new architecture candidate introduced
    result: pass | fail
  - check: no scoring or recommendation performed
    result: pass | fail
  - check: approved tree node IDs preserved
    result: pass | fail
  - check: all Stage 7 unknowns carried forward or explicitly resolved with source
    result: pass | fail
  - check: widget mapping preserves editability for meaningful content
    result: pass | fail
  - check: Pro/plugin dependencies are authorized or blocked
    result: pass | fail
  - check: classes and variables follow Stage 7 design-system hook map
    result: pass | fail
  - check: CSS needs are scoped and validator passed
    result: pass | fail
  - check: responsive plan covers desktop/tablet/mobile without inventing breakpoints
    result: pass | fail
  - check: asset and alt-text requirements are explicit
    result: pass | fail
  - check: overlay/decoration remains contained in named relative stages
    result: pass | fail | n/a
  - check: Implementation_Payload emitted with schema
    result: pass | fail
  - check: blocked profile emits a non-authorizing report and no Bundle
    result: pass | fail
```

If any required self-audit check fails, Stage 8 must output:

```text
Status: fail_requires_implementation_repair
```

and emit a non-authorizing `BLOCKED REPAIR REPORT`.

## Implementation_Payload Schema

```yaml
Implementation_Payload:
  payload_schema: ev4-implementation-payload@1.0.0
  source_stage: /implementation
  target_stage: /final-audit
  input_authorized: true | false
  selected_candidate_id:
  selected_candidate_family:
  source_build_tree_payload_schema:
  source_validation_bundle_schema:
  source_ledger:
  implementation_summary:
  elementor_settings_plan:
  widget_mapping:
  class_variable_application_map:
  scoped_css_need_map:
  scoped_css_validator:
  asset_accessibility_map:
  responsive_implementation_plan:
  position_layering_plan:
  dynamic_interaction_plan:
  implementation_risks:
  carried_forward_unknowns:
  resolved_unknowns:
  required_user_confirmations:
  final_audit_blockers:
  final_audit_allowed: true | false
  stage_9_bundle_required: true
```

`final_audit_allowed` may be `true` only if:

- input authorization passed;
- no blocker risks remain;
- all plugin/pro dependencies are authorized or absent;
- all meaningful content remains editable;
- all required assets are available or explicitly marked as user-required placeholders;
- scoped CSS validator passes;
- responsive unknowns are carried forward rather than hidden;
- `Implementation_Payload` is complete.

## EV4_DEBUG_TRACE Addendum

When debug mode is active, Stage 8 must emit:

```json
{
  "schema": "ev4-debug-trace@1.0.0",
  "stage": "/implementation",
  "stage_version": "1.0.0",
  "input_digest": {
    "inputs_received": [],
    "inputs_missing": [],
    "input_payload_schemas": []
  },
  "decision_log": [],
  "evidence_map": [],
  "unknown_register": [],
  "rule_application_log": [],
  "failure_symptom_index": [],
  "repair_route": null,
  "handoff_payload_schema": "ev4-implementation-payload@1.0.0"
}
```

Minimum Stage 8 debug entries:

- one decision record for each widget mapping family;
- one decision record for every CSS need;
- one evidence record for each official documentation fact used;
- one unknown record for every unresolved responsive, asset, dependency, or export uncertainty;
- one rule application record for input authorization, source access, CSS validator, and self-audit.

## Repair Routes

```yaml
repair_routes:
  missing_validation_bundle:
    status: blocked_requires_source_profile_implementation
    repair_target_stage: /build-tree
    instruction: do not regenerate or continue until /build-tree has a full_transaction_implemented Registry profile
  missing_or_invalid_build_tree_payload:
    status: fail_requires_build_tree_repair
    repair_target_stage: /build-tree
    instruction: regenerate Build_Tree_Payload with required schema and node maps
  implementation_not_allowed:
    status: fail_requires_recommend_or_build_tree_repair
    repair_target_stage: /recommend
    instruction: resolve blockers or user confirmations before implementation
  unauthorized_dependency:
    status: fail_requires_dependency_confirmation
    repair_target_stage: /architectures
    instruction: route plugin/pro dependency back through architecture/recommendation gates
  css_scope_failure:
    status: fail_requires_css_scope_repair
    repair_target_stage: /implementation
    instruction: constrain CSS to approved classes or replace with native Elementor controls
  responsive_blocker:
    status: fail_requires_responsive_repair
    repair_target_stage: /build-tree
    instruction: repair responsive structure before settings plan
  asset_blocker:
    status: fail_requires_user_asset_input
    repair_target_stage: /implementation
    instruction: request missing asset or define placeholder policy
  accessibility_blocker:
    status: fail_requires_accessibility_repair
    repair_target_stage: /implementation
    instruction: restore editable/semantic/alt/accessibility requirements
```

## Validation Transaction Boundary

Stage 8 prose remains grounding input, but `/implementation` is `blocked_missing_semantics`. Its active payload is not published as a canonical JSON Schema, deterministic conformance against the exact build-tree Artifact is not implemented, and cross-stage repair ownership is unresolved.

No NEXT_STAGE or REPAIR Anchor and no Validation Bundle may be emitted from this Stage. The Manifest edge to `/final-audit` is not authorization. Future enablement must close the Registry decisions and add a registered handler plus independent Bundle regeneration.

## Pass Criteria

The prose-level Stage 8 contract is internally complete only when:

- the `/implementation` Validation Profile is first upgraded to `full_transaction_implemented` and a current independently regenerated Bundle is present;
- valid Build_Tree_Payload v1.0.0 is present;
- input authorization passes;
- approved tree is preserved;
- Elementor settings plan uses the required schema;
- widget mapping preserves meaningful content editability;
- class and variable map follows the Stage 7 design-system hook map;
- CSS need map is scoped and validator-passed;
- asset and accessibility map is complete;
- responsive plan covers desktop/tablet/mobile without invented breakpoints;
- position/layering plan preserves normal-flow content and contained overlays;
- risks are listed with severity and repair owner;
- Stage 8 self-audit passes;
- `Implementation_Payload` is emitted;
- the registered validator emits the complete versioned transaction rather than a prose-authored Anchor;
- debug trace is emitted when debug mode is active.
