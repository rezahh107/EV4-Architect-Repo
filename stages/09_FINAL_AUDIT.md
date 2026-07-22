# Stage 9 — /final-audit

Status: confirmed_hardened_v1.0.0
Version: 1.0.0
Payload schema: ev4-final-audit-payload@1.0.0
Validation transaction required for continuation: yes; current profile blocked
Debug trace compatible: yes
Source policy: Stage Source Access Matrix applies
Production release gate: one realistic E2E pipeline run is still required before release-level confirmation
Active Manifest version: 1.0.1 via `stages/STAGE_8_10_v1.0.1_HARDENING_ALIGNMENT_PATCH.md`
Validation Profile: `blocked_missing_semantics`
Continuation authorization: blocked. This document does not define an executable Anchor template; enablement requires a canonical active payload Schema, registered semantic handler, deterministic repair ownership, and independent Bundle regeneration.

## Purpose

`/final-audit` audits the Stage 8 `Implementation_Payload` before the run is allowed to move to `/handoff-export`.

It verifies that the implementation plan preserves the approved architecture, build tree, scoring/audit constraints, user confirmations, unresolved unknowns, accessibility requirements, responsive risks, design-system rules, scoped CSS boundaries, and handoff readiness.

## Non-Purpose

Stage 9 is not an implementation, design, scoring, recommendation, research, or export-packaging stage.

Stage 9 must not:

- create or select a new architecture candidate;
- change the Stage 6 recommendation;
- rewrite the Stage 7 build tree;
- silently repair the Stage 8 implementation plan;
- add new Elementor widgets, sections, classes, variables, CSS, copy, assets, animations, breakpoints, or dynamic data;
- reinterpret the original screenshot;
- use RAG/TUYA as a hidden preference signal;
- treat an unknown as resolved without named evidence;
- approve `/handoff-export` while blocker-level defects remain;
- mark a real run as release-ready when E2E evidence is missing.

## Core Rule

```text
Audit the implementation against the approved pipeline record. Do not redesign, re-score, or silently repair.
```

Every Stage 9 audit finding must trace to at least one of:

1. `Implementation_Payload`;
2. `Build_Tree_Payload`;
3. `Recommendation_Payload`;
4. `Score_Audit_Payload` and relevant Stage 4 scoring constraints;
5. Validation Bundle v1.2;
6. project defaults and active contracts;
7. verified export/runtime evidence, if available;
8. official Elementor documentation only for platform capability claims;
9. TUYA internal concepts only as conceptual audit guidance.

## Required Input Gate

Stage 9 must stop with `fail_missing_input` if any required input is missing or schema-incompatible.

Required inputs:

```yaml
required_inputs:
  validation_bundle:
    schema: ev4-architect-validation-bundle@1.2.0
    contained_anchor_schema: ev4-stage-anchor@1.4.0
    source_stage: /implementation
    target_stage: /final-audit
    required_bundle_fields:
      - bundle_integrity_status
      - run_validation_status
      - authorization_valid
      - bundle_content_digest
    required_anchor_fields:
      - boundary_ref
      - handoff_state
  implementation_payload:
    schema: ev4-implementation-payload@1.0.0
    required_fields:
      - input_authorization
      - source_ledger
      - implementation_summary
      - elementor_settings_plan
      - widget_mapping
      - class_variable_application_map
      - scoped_css_need_map
      - scoped_css_validator
      - asset_accessibility_map
      - responsive_implementation_plan
      - position_layering_plan
      - dynamic_interaction_plan
      - implementation_risks
      - stage_8_self_audit
      - carried_forward_unknowns
      - required_user_confirmations
      - debug_trace_ref_or_payload
      - continuation_transaction
  prior_payload_refs:
    - Build_Tree_Payload
    - Recommendation_Payload
    - Score_Audit_Payload
    - relevant Stage 2 decomposition summary
    - relevant Stage 3 selected candidate premise
  source_access_state:
    - official_docs_available: yes | no
    - export_evidence_available: yes | no
    - tuya_reference_available: yes | no
    - e2e_run_available: yes | no
```

Input authorization fails when:

- Validation Bundle is missing, outdated, not `ev4-architect-validation-bundle@1.2.0`, or not independently reproducible;
- `/implementation` is not `full_transaction_implemented` in the Registry;
- Validation Bundle target is not `/final-audit`;
- `Implementation_Payload` is missing, partial, or older than `ev4-implementation-payload@1.0.0` without a compatibility note;
- Stage 8 self-audit contains any failed required check;
- Stage 8 emitted a `BLOCKED REPAIR REPORT` instead of a validator-owned complete transaction;
- Stage 8 risk register contains unresolved `blocker` risk;
- required user confirmations remain unresolved;
- Build Tree node IDs cannot be matched to implementation targets;
- selected candidate identity or architecture family differs across Stage 6/7/8;
- scoped CSS validator is absent;
- responsive implementation plan is absent;
- unknowns from Stage 7/8 disappear without named resolution evidence;
- required export evidence is claimed but not supplied.

If input authorization fails, Stage 9 must emit `BLOCKED REPAIR REPORT` and must not emit a pass status.

## Stage Source Access Matrix Binding

Stage 9 may use:

```text
Stage 8 Implementation_Payload
Stage 7 Build_Tree_Payload
Stage 6 Recommendation_Payload
Stage 5 Score_Audit_Payload
Stage 4 score constraints and caps
Stage 2/3 summaries only to check preservation
Validation Bundle
Rubric and active project contracts
TUYA audit concepts as internal conceptual guidance
official Elementor docs for platform-capability verification
verified export/runtime evidence, if available
```

Stage 9 must not use:

```text
new visual assumptions
new architecture candidates
new scoring preference signals
new recommendations
new implementation choices
unverified third-party tutorials as capability proof
TUYA concepts as official Elementor capability proof
RAG facts to override prior audited pipeline decisions
```

Source classification is mandatory for every audit claim:

```yaml
audit_source_ref:
  source_id:
  source_type: implementation_payload | build_tree_payload | recommendation_payload | score_audit_payload | validation_bundle | project_contract | official_docs | export_evidence | internal_concept_reference | user_input | secondary_source
  claim_checked:
  fact_class: platform_capability | project_default | project_conceptual_model | project_specific_behavior | implementation_observation | unsupported_claim
  allowed_use:
  limitation:
```

## Authoritative Source Order

When sources conflict, Stage 9 must use this order:

1. user-provided hard constraints for the current run;
2. active Validation Bundle blockers, unknowns, confirmations, and gates;
3. Stage 8 `Implementation_Payload`;
4. Stage 7 `Build_Tree_Payload`;
5. Stage 6 `Recommendation_Payload`;
6. Stage 5 `Score_Audit_Payload`;
7. Stage 4 scoring constraints, caps, and N/A rules;
8. Stage 2/3 evidence only for preservation checks;
9. verified export/runtime evidence for implementation observations;
10. official Elementor documentation for platform capability;
11. active EV4 contracts and project defaults;
12. TUYA internal concept reference;
13. secondary sources.

Conflict rules:

- If Stage 8 conflicts with Stage 7, route repair to `/implementation` or `/build-tree` depending on the owner of the defect.
- If Stage 7 conflicts with Stage 6, route repair to `/build-tree` or `/recommend`.
- If a platform capability claim lacks official docs or export evidence, classify it as `unsupported_claim` and audit as `requires_verification`.
- If TUYA conflicts with official docs, official docs win for platform capability.
- If export evidence conflicts with generic docs for current project behavior, export evidence wins for implementation observation, but Stage 9 still must not redesign.

## Output Format

Stage 9 must output these sections in order:

1. `INPUT AUTHORIZATION`
2. `SOURCE / PAYLOAD LEDGER`
3. `ARCHITECTURE PRESERVATION AUDIT`
4. `BUILD TREE PRESERVATION AUDIT`
5. `ELEMENTOR-NATIVE / DEPENDENCY AUDIT`
6. `EDITABILITY AUDIT`
7. `NORMAL-FLOW / POSITION / LAYERING AUDIT`
8. `RESPONSIVE AUDIT`
9. `ACCESSIBILITY AUDIT`
10. `PERFORMANCE / DOM AUDIT`
11. `DESIGN-SYSTEM AUDIT`
12. `SCOPED CSS AUDIT`
13. `ASSET / MEDIA AUDIT`
14. `DYNAMIC DATA / INTERACTION AUDIT`
15. `UNKNOWN / CONFIRMATION SURVIVAL AUDIT`
16. `SEVERITY REGISTER`
17. `BLOCKERS AND REPAIR ROUTES`
18. `FINAL AUDIT STATUS`
19. `STAGE 9 SELF-AUDIT`
20. `Final_Audit_Payload`
21. `EV4_DEBUG_TRACE` if debug mode is active
22. `VALIDATION PROFILE BLOCKED REPORT` — no Bundle while this profile remains blocked

## Severity Taxonomy

Every finding must use this taxonomy:

```yaml
severity_taxonomy:
  blocker:
    meaning: prevents handoff; must repair before /handoff-export
    allowed_final_status: fail_requires_repair
  high:
    meaning: serious risk; may pass only if explicit mitigation and owner are present
    allowed_final_status: pass_with_minor_flags is not allowed unless risk is downgraded with evidence
  medium:
    meaning: non-blocking defect or verification need; must be carried to handoff notes
    allowed_final_status: pass_with_minor_flags
  low:
    meaning: minor polish, naming, clarity, or documentation issue
    allowed_final_status: pass or pass_with_minor_flags
  info:
    meaning: non-actionable note; must not affect pass/fail
    allowed_final_status: pass
```

Severity rules:

- A missing required payload is always `blocker`.
- A hidden architecture change is always `blocker`.
- A missing scoped CSS validator is always `blocker`.
- A meaningful-content editability loss is always `blocker`.
- Unapproved plugin, Pro, HTML, SVG, form, loop, carousel, or dynamic dependency is always `blocker`.
- A mobile collision risk involving meaningful content is `high` or `blocker` depending on mitigation.
- Decorative-only responsive simplification may be `medium` or lower only if Stage 7/8 authorized it.
- Accessibility failures affecting meaningful content are `blocker` or `high`.
- Global CSS leakage is `blocker`.
- Unsupported platform-capability claims are at least `medium`; they become `blocker` if implementation depends on them.

## Final Audit Statuses

Stage 9 may emit only one of these statuses:

```yaml
final_audit_status:
  - pass
  - pass_with_minor_flags
  - fail_missing_input
  - fail_requires_implementation_repair
  - fail_requires_build_tree_repair
  - fail_requires_recommendation_repair
  - fail_requires_score_audit_repair
  - fail_requires_e2e_test_before_release_confirmation
```

Status rules:

- `pass` is allowed only when there are no blocker/high findings, all required payloads pass, all repair routes are empty or low/info, and handoff-export is safe.
- `pass_with_minor_flags` is allowed only when there are no blocker/high findings and all medium findings have explicit handoff notes.
- `fail_missing_input` is required when input authorization fails.
- `fail_requires_implementation_repair` is required when Stage 8 owns the defect.
- `fail_requires_build_tree_repair` is required when Stage 7 owns the defect.
- `fail_requires_recommendation_repair` is required when selected candidate or eligibility ownership belongs to Stage 6.
- `fail_requires_score_audit_repair` is required when Stage 5 audit constraints are missing or contradicted.
- `fail_requires_e2e_test_before_release_confirmation` applies to repository release-level confirmation when no realistic E2E run exists. It must not be used to hide Stage 9 contract defects.

## Audit Checklists

### 1. Architecture Preservation Audit

```yaml
architecture_preservation_audit:
  - check: selected candidate id preserved from Stage 6 through Stage 8
    result: pass | fail | blocked | n/a
  - check: candidate family preserved
    result: pass | fail | blocked | n/a
  - check: no new architecture family introduced in Stage 8
    result: pass | fail | blocked | n/a
  - check: Stage 4/5 caps and disallowed patterns preserved
    result: pass | fail | blocked | n/a
  - check: rejected candidates did not re-enter through implementation details
    result: pass | fail | blocked | n/a
```

### 2. Build Tree Preservation Audit

```yaml
build_tree_preservation_audit:
  - source_tree_node_id:
    expected_structure_label:
    implementation_target_found: yes | no | partial
    class_name_preserved: yes | no | partial | n/a
    wrapper_justification_preserved: yes | no | partial | n/a
    role_preserved: yes | no | partial
    finding_severity:
    repair_owner:
```

Rules:

- Every meaningful Stage 7 node must map to an implementation target.
- Additional wrappers are allowed only if Stage 8 justifies them and they do not change reading order or editability.
- Wrapper bloat without structural purpose is at least `medium`.

### 3. Elementor-Native / Dependency Audit

```yaml
elementor_native_dependency_audit:
  - target_id:
    proposed_element_or_widget:
    native_status: native | pro | third_party | custom_html | custom_css | svg | unknown
    authorization_source:
    official_or_export_source_ref:
    dependency_risk: none | low | medium | high | blocker
    fallback_required:
```

Rules:

- Unknown widget availability must not be treated as native.
- Pro or third-party dependency requires Stage 6/user authorization.
- Custom HTML/SVG is not forbidden, but it must be scoped, justified, editable-safe, and accessible.
- CSS should solve only gaps not handled by native controls.

### 4. Editability Audit

```yaml
editability_audit:
  - content_id:
    content_role: heading | body | cta | image | icon | card | data | label | decoration | unknown
    meaningful_content: yes | no | unknown
    editable_in_elementor: yes | no | partial | unknown
    preserved_from_tree: yes | no | partial
    violation:
    severity:
    repair_owner:
```

Rules:

- Meaningful headings, body copy, CTA text, product/data labels, and meaningful images must remain editable or explicitly marked as unresolved.
- Meaningful text in static image/SVG/HTML without editability is a blocker unless the user explicitly approved it.
- Decoration may be non-editable if it is correctly classified and does not carry meaning.

### 5. Normal-Flow / Position / Layering Audit

```yaml
position_layering_audit:
  - target_id:
    position_type:
    layer_role:
    containing_stage:
    content_in_normal_flow: yes | no | n/a | unknown
    absolute_position_authorized: yes | no | n/a | unknown
    z_index_reads_order: yes | no | unknown
    overflow_policy_valid: yes | no | unknown
    mobile_collision_risk:
    severity:
```

Rules:

- Meaningful content stays in normal flow unless a prior audited decision authorizes otherwise.
- Floating decoration must be inside a named relative stage.
- Absolute positioning must not determine reading order.
- Z-index must not compensate for incorrect structure.
- Overflow hidden must not hide meaningful content.

### 6. Responsive Audit

```yaml
responsive_audit:
  breakpoint_source:
  breakpoint_values_available: yes | no | partial | unknown
  groups:
    - target_id:
      desktop_behavior_checked: yes | no | blocked
      tablet_behavior_checked: yes | no | blocked
      mobile_behavior_checked: yes | no | blocked
      reading_order_preserved: yes | no | unknown
      meaningful_content_hidden: yes | no | unknown
      collision_risk: none | low | medium | high | blocker | unknown
      repair_owner:
```

Rules:

- Desktop evidence supports inheritance potential, not guaranteed mobile success.
- Missing mobile evidence must remain visible as risk.
- Stage 9 must not invent breakpoint values.
- Hiding meaningful content on mobile without authorization is a blocker.
- Decorative simplification must be authorized by Stage 7/8.

### 7. Accessibility Audit

```yaml
accessibility_audit:
  - target_id:
    semantic_role:
    heading_order_risk:
    alt_text_policy:
    link_or_button_label:
    keyboard_access:
    focus_state:
    hover_only_disclosure:
    contrast_status: confirmed | needs_check | unknown | n/a
    severity:
```

Rules:

- Meaningful images need alt policy.
- Decorative images may use empty alt only when classification is supported.
- Interactive elements need label, focus, and keyboard path.
- Hover-only access to meaningful content is a blocker unless there is a non-hover path.
- Contrast may remain `needs_check`, but must be carried to handoff.

### 8. Performance / DOM Audit

```yaml
performance_dom_audit:
  node_count_policy:
  wrapper_budget_result:
  asset_weight_risk:
  css_js_risk:
  animation_or_interaction_risk:
  third_party_dependency_risk:
  export_complexity_risk:
  findings:
```

Rules:

- DOM depth is acceptable only when structurally justified.
- A flat static image may be performant but fails editability/accessibility when meaningful content is trapped.
- Heavy media, animation, third-party widgets, custom code, and global CSS increase risk.
- Performance must be assessed as structure + media + CSS/JS + dependencies + maintainability, not node count alone.

### 9. Design-System Audit

```yaml
design_system_audit:
  - class_name:
    scope: local | section-reusable | global-candidate | global-confirmed | unknown
    source:
    variable_refs:
    promotion_justified: yes | no | n/a | unknown
    conflict_risk:
    local_override_policy:
    severity:
```

Rules:

- Repeated patterns should use reusable classes.
- One-off coordinates and exceptions stay local.
- Global class promotion requires confirmed reuse or design-system value.
- Variables must not become containers for guessed one-off values.
- Class/variable naming must remain compatible with Stage 7 naming policy.

### 10. Scoped CSS Audit

```yaml
scoped_css_audit:
  - css_need_id:
    selector_scope_valid: yes | no | unknown
    global_leakage: yes | no | unknown
    meaningful_content_generated_by_css: yes | no
    meaningful_content_hidden_by_css: yes | no | unknown
    native_control_gap_justified: yes | no | unknown
    device_state_scope_explicit: yes | no | n/a
    position_absolute_contained: yes | no | n/a | unknown
    severity:
```

Rules:

- CSS must attach to approved local class or element scope.
- No `html`, `body`, unrelated global selector, or theme-wide selector leakage.
- CSS must not create meaningful content.
- CSS must not hide meaningful mobile content without Stage 6/7/8 authorization.
- Custom CSS needs must be justified by a native-control gap.

### 11. Asset / Media Audit

```yaml
asset_media_audit:
  - asset_id:
    role:
    source_status:
    alt_text_policy:
    responsive_variants:
    optimization_status:
    rights_or_license_status:
    missing_asset_policy:
    severity:
```

Rules:

- Missing meaningful assets are blockers unless a placeholder policy is explicitly authorized.
- Asset dimensions, filenames, license, or responsive variants must not be invented.
- Decorative roles must trace to prior payloads.

### 12. Dynamic Data / Interaction Audit

```yaml
dynamic_interaction_audit:
  - target_id:
    requirement_type:
    authorization_source:
    dependency_status:
    accessibility_path:
    fallback:
    blocker:
```

Rules:

- Do not add interactions because they feel modern.
- Dynamic data must be authorized by Stage 6/7 or user constraints.
- Pro/plugin/loop/form/carousel/filter requirements must be authorized.
- Hover-only disclosure of meaningful content is not acceptable without fallback.

### 13. Unknown / Confirmation Survival Audit

```yaml
unknown_confirmation_survival_audit:
  carried_forward_unknowns_expected: []
  carried_forward_unknowns_found: []
  dropped_unknowns: []
  resolved_unknowns:
    - unknown_id:
      resolution_source:
      valid_resolution: yes | no
  required_confirmations_expected: []
  required_confirmations_found: []
  unresolved_confirmations:
```

Rules:

- Unknowns must survive until named evidence resolves them.
- Required user confirmations cannot disappear.
- A confirmation can move from blocker to resolved only with named evidence.
- `unknown` by itself is not contradiction.
- provisional TUYA-derived assumptions must be upgraded/downgraded/contradicted when stronger evidence exists.

## Blockers and Repair Routes

Stage 9 must convert every blocker/high defect into an explicit route:

```yaml
repair_route:
  finding_id:
  severity:
  owner_stage: /implementation | /build-tree | /recommend | /score-audit | /score-evidence | /architectures | /decompose | /intake | user
  rerun_mode: local_repair | forward_rerun | score_only_rerun | build_only_rerun | user_confirmation
  earliest_safe_rerun_stage:
  invalidated_downstream:
  minimal_repair_instruction:
  forbidden_shortcut:
  evidence_required_to_close:
```

Repair examples:

```yaml
examples:
  - symptom: Stage 8 maps a meaningful heading to a background image
    severity: blocker
    owner_stage: /implementation
    repair: remap heading to editable Heading/Text element; keep decorative image separate
    forbidden_shortcut: approve because visual match is high

  - symptom: Stage 8 adds absolute positioning to CTA without Stage 7 authorization
    severity: blocker
    owner_stage: /implementation
    repair: keep CTA in normal-flow content group or reroute to /build-tree if structure cannot support it
    forbidden_shortcut: hide CTA on mobile

  - symptom: Stage 8 uses a carousel plugin not authorized by Stage 6
    severity: blocker
    owner_stage: /recommend
    repair: return to /recommend for dependency authorization or choose already audited no-plugin path
    forbidden_shortcut: assume plugin availability

  - symptom: Stage 7 node has no implementation target
    severity: blocker
    owner_stage: /implementation
    repair: add mapped implementation target or explain why the node was invalidated by approved upstream evidence
    forbidden_shortcut: omit the node silently

  - symptom: Scoped CSS targets body or theme-wide selectors
    severity: blocker
    owner_stage: /implementation
    repair: scope CSS to approved class/element and document native-control gap
    forbidden_shortcut: rely on CSS cascade order
```

## Regression Examples

Stage 9 must defend against these regression patterns:

```yaml
regression_cases:
  - id: FA-REG-001
    name: visual-match-over-editability
    bad_pattern: high visual fidelity achieved by flattening meaningful text into image/SVG
    expected_stage_9_result: fail_requires_implementation_repair

  - id: FA-REG-002
    name: hidden-architecture-change
    bad_pattern: Implementation_Payload changes selected architecture family or reintroduces rejected candidate
    expected_stage_9_result: fail_requires_build_tree_repair or fail_requires_recommendation_repair

  - id: FA-REG-003
    name: mobile-risk-disappears
    bad_pattern: Stage 7/8 mobile collision unknown is missing from final audit
    expected_stage_9_result: fail_requires_implementation_repair

  - id: FA-REG-004
    name: global-css-leak
    bad_pattern: custom CSS uses html/body/global theme selectors
    expected_stage_9_result: fail_requires_implementation_repair

  - id: FA-REG-005
    name: unapproved-dynamic-dependency
    bad_pattern: form, loop, carousel, dynamic source, Pro feature, or plugin appears without authorization
    expected_stage_9_result: fail_requires_recommendation_repair or fail_requires_implementation_repair

  - id: FA-REG-006
    name: unknown-collapsed-to-pass
    bad_pattern: unresolved asset, breakpoint, plugin, z-index, or interaction unknown is treated as resolved
    expected_stage_9_result: pass_with_minor_flags only if non-blocking and carried; otherwise fail_requires_repair

  - id: FA-REG-007
    name: silent-repair-inside-audit
    bad_pattern: Stage 9 changes implementation instead of routing a repair
    expected_stage_9_result: stage_boundary_violation

  - id: FA-REG-008
    name: e2e-missing-release-claim
    bad_pattern: repository or prompt pack is marked release-ready without a realistic E2E run
    expected_stage_9_result: fail_requires_e2e_test_before_release_confirmation for release-level confirmation
```

## Stage 9 Self-Audit

Before emitting `Final_Audit_Payload`, Stage 9 must verify:

```yaml
stage_9_self_audit:
  - check: valid Validation Bundle v1.2 received
    result: pass | fail
  - check: valid Implementation_Payload v1.0.0 received
    result: pass | fail
  - check: Build_Tree_Payload and Recommendation_Payload referenced
    result: pass | fail
  - check: no new architecture generated
    result: pass | fail
  - check: no new recommendation generated
    result: pass | fail
  - check: no implementation repair applied silently
    result: pass | fail
  - check: all meaningful nodes audited for editability
    result: pass | fail
  - check: scoped CSS validator audited
    result: pass | fail
  - check: responsive unknowns carried forward
    result: pass | fail
  - check: required confirmations preserved or resolved with evidence
    result: pass | fail
  - check: every blocker/high finding has repair route
    result: pass | fail
  - check: blocked profile emits no Anchor or Bundle
    result: pass | fail
  - check: debug trace shape compatible when debug mode active
    result: pass | fail
```

If any self-audit check fails, Stage 9 must not emit `pass`.

## Final_Audit_Payload Schema

```yaml
Final_Audit_Payload:
  schema: ev4-final-audit-payload@1.0.0
  stage: /final-audit
  input_authorization:
    status: pass | fail
    missing_inputs: []
    schema_mismatches: []
    repair_report_required: yes | no
  source_payload_ledger:
    validation_bundle_ref:
    implementation_payload_ref:
    build_tree_payload_ref:
    recommendation_payload_ref:
    score_audit_payload_ref:
    export_evidence_refs: []
    official_doc_refs: []
    tuya_refs: []
  audit_summary:
    final_audit_status:
    blocker_count:
    high_count:
    medium_count:
    low_count:
    info_count:
    handoff_export_allowed: yes | no
    e2e_release_confirmation_available: yes | no
  architecture_preservation_audit: []
  build_tree_preservation_audit: []
  elementor_native_dependency_audit: []
  editability_audit: []
  position_layering_audit: []
  responsive_audit: []
  accessibility_audit: []
  performance_dom_audit: []
  design_system_audit: []
  scoped_css_audit: []
  asset_media_audit: []
  dynamic_interaction_audit: []
  unknown_confirmation_survival_audit: []
  severity_register:
    - finding_id:
      title:
      severity: blocker | high | medium | low | info
      evidence_refs: []
      affected_stage:
      affected_node_or_payload_field:
      effect:
      repair_owner:
      handoff_note_required: yes | no
  repair_routes: []
  pass_with_minor_flags_notes: []
  release_blockers:
    - blocker_id:
      blocker:
      required_action:
      owner:
  stage_9_self_audit: []
  debug_trace_ref:
  continuation_transaction: null_while_profile_blocked
```

Payload rules:

- `handoff_export_allowed: yes` only when final status is `pass` or `pass_with_minor_flags`.
- `handoff_export_allowed` is prose-level only while the profile is blocked and never authorizes continuation.
- Emit a non-authorizing `BLOCKED REPAIR REPORT`; only a future registered validator may emit a complete transaction after Registry enablement.
- `release_blockers` must include missing E2E evidence when the repository is being judged for release-level confirmation.
- Medium findings must become handoff notes if handoff is allowed.

## EV4_DEBUG_TRACE Addendum

When debug mode is active, Stage 9 must emit `EV4_DEBUG_TRACE` using `ev4-debug-trace@1.0.0`.

Required Stage 9 additions:

```json
{
  "schema": "ev4-debug-trace@1.0.0",
  "stage": "/final-audit",
  "stage_version": "1.0.0",
  "input_digest": {
    "inputs_received": [
      "VALIDATION_BUNDLE",
      "Implementation_Payload",
      "Build_Tree_Payload",
      "Recommendation_Payload",
      "Score_Audit_Payload"
    ],
    "inputs_missing": [],
    "input_payload_schemas": [
      "ev4-architect-validation-bundle@1.2.0",
      "ev4-implementation-payload@1.0.0",
      "ev4-build-tree-payload@1.0.0"
    ]
  },
  "decision_log": [],
  "evidence_map": [],
  "unknown_register": [],
  "rule_application_log": [],
  "failure_symptom_index": [],
  "repair_route": null,
  "handoff_payload_schema": "ev4-final-audit-payload@1.0.0"
}
```

Failure symptoms Stage 9 must classify when observed:

```text
missing_input
stage_boundary_violation
hallucinated_evidence
unknown_collapsed_to_number
contradiction_softened
gate_override
hidden_recommendation
bad_handoff
naming_contract_missing
implementation_drift
editability_loss
global_css_leak
mobile_risk_dropped
unapproved_dependency
silent_repair_inside_audit
```

## Validation Transaction Boundary

Stage 9 prose remains grounding input, but `/final-audit` is `blocked_missing_semantics`. Its active payload is not published as a canonical JSON Schema, deterministic severity/pass semantics are not implemented, and cross-stage earliest repair ownership is unresolved.

No NEXT_STAGE or REPAIR Anchor and no Validation Bundle may be emitted from this Stage. The Manifest edge to `/handoff-export` is topology only. Future enablement must close the Registry decisions and add a registered handler plus independent Bundle regeneration.

## Strict Critic Hardening Notes Applied

The scaffolded Stage 9 was insufficient because it named broad audit categories but lacked:

- exact input authorization rules;
- Stage Source Access Matrix binding;
- payload/source classification;
- severity taxonomy;
- detailed audit checklists;
- unknown/confirmation survival checks;
- scoped CSS and responsive-risk audits;
- repair route schema and examples;
- regression examples;
- `Final_Audit_Payload` schema;
- self-audit;
- debug trace addendum;
- a future registered validator-owned next-stage and repair transaction;
- E2E release-confirmation boundary.

This version adds those controls. Stage 9 is now a hardened final-audit contract, but a real E2E run remains required before repository-level release confirmation.
