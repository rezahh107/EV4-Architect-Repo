# E2E-001 Test Report — Smart Home Connector Hero

Status: pass_with_minor_flags
Version: 1.0.0
Report schema: ev4-e2e-test-report@1.0.0
Test id: E2E-001
Fixture: experiments/E2E-001-smart-home-connector-fixture.md
Fixture schema: ev4-e2e-fixture@1.0.0
Fixture type: realistic_mockup_description
Project status version at start: 0.11.0
Run mode: full pipeline validation
Release effect: release-blocker-removal eligible for the prompt-pack contract, with non-blocking limitation noted for raster screenshot interpretation

Historical evidence notice: this report predates the Validation Profiles Registry. Its `ev4-stage-anchor@1.1.0` records are preserved verbatim as historical evidence and do not authorize current continuation.

---

## 1. Input Authorization

Read inputs:

```text
- STATUS.md version 0.11.0
- experiments/END_TO_END_PIPELINE_TEST_PLAN.md
- experiments/E2E-001-smart-home-connector-fixture.md
- 02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md
- contracts/STAGE_ANCHOR_CONTRACT.md
- contracts/PARTIAL_RERUN_CONTRACT.md
- diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
- references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
- knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
- rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md
- stages/01_INTAKE.md through stages/10_HANDOFF_EXPORT.md where relevant
```

Input gate result:

```yaml
input_authorization:
  fixture_present: yes
  fixture_schema_valid: yes
  test_plan_present: yes
  test_plan_schema_valid: yes
  stage_anchor_contract_present: yes
  debug_trace_contract_present: yes
  partial_rerun_contract_present: yes
  source_access_matrix_present: yes
  e2e_execution_allowed: yes
```

Known limitation carried from fixture:

```text
E2E-001 is a realistic textual mockup, not a raster screenshot. It validates pipeline discipline, role classification, unknown propagation, scoring/audit mechanics, implementation boundary, final-audit blocking behavior, and handoff preservation. It does not validate pixel-accurate screenshot interpretation.
```

---

## 2. Strict Critic Findings Before Running

The E2E runner applied strict critic mode before accepting the run as meaningful.

Confirmed risks in this E2E mode:

```text
- The fixture is textual, so screenshot-only visual interpretation cannot be validated.
- There is no real Elementor export evidence, so exact generated Elementor JSON cannot be audited.
- No external arithmetic runtime was available in the connector run, so arithmetic is shown explicitly and Stage 5 rechecks it.
- Official Elementor docs were not needed to prove new platform claims because the test used repository defaults and stage contracts; any platform-capability claim remains generic and non-project-specific.
```

Patch applied in this report:

```text
- mark screenshot interpretation as medium non-release-blocking flag;
- preserve every fixture unknown through Stage 10;
- keep all exact values as unknown or token placeholders;
- keep dynamic data as unresolved/non-required;
- explicitly verify every negative-control probe;
- emit a next work anchor for /research hardening rather than claiming the whole repository is fully finished.
```

---

## 3. Full Pipeline Execution Summary

Pipeline executed:

```text
/intake
/decompose
/architectures
/score-evidence
/score-audit
/recommend
/build-tree
/implementation
/final-audit
/handoff-export
```

### 3.1 /intake

Result:

```yaml
stage: /intake
status: pass
payload_schema: ev4-intake-payload@1.0.0-compatible
blocking_questions: none
```

Applied defaults:

```text
- Elementor V4 target.
- Container/Flexbox-first workflow.
- Elementor Pro available by project default, but do not require Pro unless proven needed.
- Scoped Custom CSS allowed.
- No third-party plugins by default.
- Meaningful content remains editable where practical.
- Primary content remains in normal flow.
- Absolute positioning allowed only for controlled decorative overlays inside a named relative stage.
```

No architecture, score, or build tree was produced during intake.

### 3.2 NEXT STAGE ANCHOR — /decompose

```text
NEXT STAGE ANCHOR — /decompose
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /intake
target_stage: /decompose
target_stage_hardening_status: confirmed
project_status_version: 0.11.0
payload_schema_in: ev4-intake-payload@1.0.0-compatible
payload_schema_out: ev4-decomposition-payload@1.0.1-compatible
critical_unknowns:
  - U-E2E-001 through U-E2E-009 from fixture
confidence_delta:
  - item: input sufficiency
    previous_confidence: unknown
    current_confidence: confirmed
    direction: increased
    reason: fixture provides complete controlled mockup description
    downstream_impact: /decompose can run without asking questions
blocking_items: none
gate_results: intake_pass
audit_flags:
  - textual_fixture_no_pixel_validation
required_user_confirmations: none
partial_rerun_state:
  reusable_until: fixture or defaults change
  invalidation_triggers: fixture content change, project default change
  earliest_safe_rerun_stage: /intake
  downstream_payloads_dependent_on_this_stage: all downstream E2E payloads
allowed_work: classify provided visual/content facts only
forbidden_work: no implementation, scoring, recommendation, RAG/TUYA visual inference
stop_conditions: missing fixture or invalid schema
debug_trace_required: yes
```

### 3.3 /decompose

Result:

```yaml
stage: /decompose
status: pass
source_access_result: pass
rag_or_tuya_used: no
```

DECOMPOSITION SNAPSHOT:

```yaml
visible_groups:
  - hero_section_full_width
  - left_copy_column
  - right_dashboard_visual_area
  - dashboard_card
  - repeated_device_tiles
  - energy_chart
  - room_status_list
  - connector_lines
  - floating_device_nodes
  - background_grid_or_glow
meaningful_content:
  - eyebrow_label: SMART HOME AUTOMATION
  - headline: Connect every room. Automate every routine.
  - paragraph: Control lights, sensors, scenes, and energy usage from one calm dashboard.
  - primary_cta: Start automation
  - secondary_cta: View devices
  - feature_chips:
      - No-code scenes
      - Energy insights
      - Device groups
  - dashboard_card_substructure:
      - mini_status_bar
      - four_device_tiles
      - circular_energy_chart
      - room_status_list
repeated_component_candidates:
  - four_device_tiles
visual_core:
  - dashboard_card_with_semantic_substructure
decoration_layers:
  - connector_lines
  - background_grid_or_radial_glow
overlay_connector_candidates:
  - connector_lines
  - floating_device_nodes
responsive_risks:
  - two_column_to_mobile_stack
  - floating_node_collision
  - connector_line_overflow_or_unreadable_mobile_position
  - dashboard_card_density_on_small_widths
ambiguous_items:
  - floating_device_nodes: meaningful if they communicate thermostat/light/lock labels; decorative if purely ornamental
unknowns:
  - U-E2E-001: exact desktop/tablet/mobile breakpoints are not provided
  - U-E2E-002: exact spacing scale is not provided
  - U-E2E-003: exact color tokens are not provided beyond light neutral + modern technical mood
  - U-E2E-004: exact dashboard tile content beyond labels is not provided
  - U-E2E-005: exact icon source/library is not provided
  - U-E2E-006: exact connector-line geometry and z-index are not provided
  - U-E2E-007: whether animation is required is not provided
  - U-E2E-008: whether Elementor Pro is available is not provided by fixture, but project default says available
  - U-E2E-009: whether the right dashboard is purely illustrative or should use dynamic data is not provided
forbidden_assumptions:
  - no exact pixels
  - no exact z-index
  - no exact breakpoint values
  - no asset filenames or icon library
  - no animation timings
  - no Pro/dynamic requirement inferred from visual repetition alone
```

Negative-control check:

```yaml
NC-001_stage_2_rag_or_tuya_visual_inference: pass
```

### 3.4 NEXT STAGE ANCHOR — /architectures

```text
NEXT STAGE ANCHOR — /architectures
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /decompose
target_stage: /architectures
target_stage_hardening_status: confirmed
project_status_version: 0.11.0
payload_schema_in: ev4-decomposition-payload@1.0.1-compatible
payload_schema_out: ev4-architecture-candidates-payload@1.1.0-compatible
critical_unknowns: U-E2E-001..U-E2E-009 preserved
confidence_delta:
  - item: floating node role
    previous_confidence: unknown
    current_confidence: uncertain
    direction: unchanged
    reason: fixture gives labels but not whether nodes are informational or decorative
    downstream_impact: candidate designs must preserve node text/editability unless explicitly classified as decorative later
gate_results: decompose_pass
audit_flags:
  - textual_fixture_no_pixel_validation
  - floating_node_role_ambiguous
required_user_confirmations: none
partial_rerun_state:
  reusable_until: fixture visual/content facts change
  invalidation_triggers: new screenshot, changed visual groups, changed meaningful content
  earliest_safe_rerun_stage: /decompose
  downstream_payloads_dependent_on_this_stage: /architectures onward
allowed_work: enumerate architecture families only
forbidden_work: no recommendation, no scoring, no exact settings
stop_conditions: missing decomposition snapshot or blocking unknown preventing enumeration
debug_trace_required: yes
```

### 3.5 /architectures

Result:

```yaml
stage: /architectures
status: pass
source_access_result: pass
recommendation_language_scan: pass
```

Architecture Coverage Matrix:

```yaml
candidate_families:
  A01_native_container_widget_composition:
    summary: Native containers/widgets, simplified decoration, dashboard built as editable card/tile/list/chart groups.
    dependency: no third-party plugin; no required Pro-specific dynamic feature
    risk: connector-line visual precision may be simplified
  A02_native_plus_scoped_decorative_css:
    summary: Native editable structure for all meaningful content, plus section-scoped CSS/SVG-like decorative connector and glow layers inside a named visual stage.
    dependency: scoped Custom CSS allowed by project defaults
    risk: must audit CSS scope and mobile collision
  A03_flattened_visual_asset:
    summary: Left content native, right dashboard flattened into a static image or SVG asset.
    dependency: no plugin
    risk: editability loss for dashboard card, tiles, chart, and list
  A04_custom_heavy_absolute_visual_stage:
    summary: Dashboard, nodes, and connector lines heavily coordinate-driven with absolute positioning.
    dependency: custom CSS/positioning; possible HTML/SVG layer
    risk: mobile brittleness, editability and maintenance risk
```

Unknown Propagation Ledger:

```yaml
U-E2E-001: propagated_to_score_evidence
U-E2E-002: propagated_to_score_evidence
U-E2E-003: propagated_to_score_evidence
U-E2E-004: propagated_to_score_evidence
U-E2E-005: propagated_to_score_evidence
U-E2E-006: propagated_to_score_evidence
U-E2E-007: propagated_to_score_evidence
U-E2E-008: project_default_available_but_fixture_specific_need_unresolved
U-E2E-009: propagated_to_score_evidence
```

Negative-control check:

```yaml
NC-002_premature_recommendation_language: pass
```

### 3.6 NEXT STAGE ANCHOR — /score-evidence

```text
NEXT STAGE ANCHOR — /score-evidence
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /architectures
target_stage: /score-evidence
target_stage_hardening_status: confirmed
project_status_version: 0.11.0
payload_schema_in: ev4-architecture-candidates-payload@1.1.0-compatible
payload_schema_out: ev4-score-evidence-payload@1.3.0
critical_unknowns: U-E2E-001..U-E2E-009 preserved
confidence_delta:
  - item: candidate coverage
    previous_confidence: unknown
    current_confidence: confirmed
    direction: increased
    reason: native, hybrid, flattened, and custom-heavy families were enumerated
    downstream_impact: Stage 4 can score without adding candidates
blocking_items: none
gate_results: architecture_enumeration_pass
audit_flags:
  - no architecture selected yet
  - textual_fixture_no_pixel_validation
required_user_confirmations: none
partial_rerun_state:
  reusable_until: candidate set or decomposition changes
  invalidation_triggers: candidate added/removed, decomposition changed, rubric changed
  earliest_safe_rerun_stage: /architectures
  downstream_payloads_dependent_on_this_stage: /score-evidence onward
allowed_work: score candidates from Stage 2/3 + rubric only
forbidden_work: no recommendation, no RAG/TUYA scoring boost, no unknown-to-number conversion
stop_conditions: missing candidate payload or rubric
debug_trace_required: yes
```

### 3.7 /score-evidence

Result:

```yaml
stage: /score-evidence
status: pass
rubric_version: 1.3
payload_schema: ev4-score-evidence-payload@1.3.0
source_access_result: pass
```

Scoring method:

```text
Default applicable raw max = 125.
If Overlay Containment is N/A, its weight 2 is excluded and applicable raw max = 115.
No criterion used unknown breakpoint, spacing, z-index, icon library, or animation as numeric evidence.
```

Candidate scoring summary:

```yaml
A01_native_container_widget_composition:
  criterion_scores:
    elementor_native_feasibility: 5
    normal_flow_safety: 5
    responsiveness: 3
    editability: 5
    structural_clarity: 5
    overlay_containment: 3
    performance: 5
    accessibility: 4
    design_system_fit: 5
    visual_precision: 3
  raw_weighted_total: 109
  applicable_raw_max: 125
  normalized_total: 87.2
  decision_band: primary_candidate_after_audit
  flags:
    - visual connector fidelity may be simplified
    - responsive overlay/floating behavior remains uncertain

A02_native_plus_scoped_decorative_css:
  criterion_scores:
    elementor_native_feasibility: 4
    normal_flow_safety: 5
    responsiveness: 4
    editability: 5
    structural_clarity: 5
    overlay_containment: 5
    performance: 4
    accessibility: 4
    design_system_fit: 5
    visual_precision: 5
  raw_weighted_total: 113
  applicable_raw_max: 125
  normalized_total: 90.4
  decision_band: primary_candidate_after_audit
  flags:
    - scoped CSS must remain decorative and section-scoped
    - exact connector geometry and z-index remain unknown

A03_flattened_visual_asset:
  criterion_scores:
    elementor_native_feasibility: 5
    normal_flow_safety: 5
    responsiveness: 4
    editability: 1
    structural_clarity: 3
    overlay_containment: N/A
    performance: 2
    accessibility: 2
    design_system_fit: 2
    visual_precision: 4
  raw_weighted_total: 79
  applicable_raw_max: 115
  normalized_total: 68.7
  decision_band: reject_or_documented_risk
  flags:
    - meaningful dashboard content would be flattened
    - editability and accessibility penalties are material

A04_custom_heavy_absolute_visual_stage:
  criterion_scores:
    elementor_native_feasibility: 3
    normal_flow_safety: 2
    responsiveness: 2
    editability: 2
    structural_clarity: 2
    overlay_containment: 2
    performance: 2
    accessibility: 2
    design_system_fit: 2
    visual_precision: 5
  raw_weighted_total: 57
  applicable_raw_max: 125
  normalized_total: 45.6
  decision_band: reject_or_documented_risk
  flags:
    - responsive and normal-flow risks are high
    - visual precision does not override higher-priority criteria
```

Arithmetic check shown explicitly:

```text
A01 = (5×4)+(5×4)+(3×4)+(5×3)+(5×2)+(3×2)+(5×2)+(4×2)+(5×1)+(3×1) = 109 / 125 = 87.2
A02 = (4×4)+(5×4)+(4×4)+(5×3)+(5×2)+(5×2)+(4×2)+(4×2)+(5×1)+(5×1) = 113 / 125 = 90.4
A03 = (5×4)+(5×4)+(4×4)+(1×3)+(3×2)+(2×2)+(2×2)+(2×1)+(4×1) = 79 / 115 = 68.7 because Overlay Containment is N/A
A04 = (3×4)+(2×4)+(2×4)+(2×3)+(2×2)+(2×2)+(2×2)+(2×2)+(2×1)+(5×1) = 57 / 125 = 45.6
```

Negative-control check:

```yaml
NC-003_unknown_to_number: pass
```

### 3.8 NEXT STAGE ANCHOR — /score-audit

```text
NEXT STAGE ANCHOR — /score-audit
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /score-evidence
target_stage: /score-audit
target_stage_hardening_status: confirmed
project_status_version: 0.11.0
payload_schema_in: ev4-score-evidence-payload@1.3.0
payload_schema_out: ev4-score-audit-payload@1.2.0
critical_unknowns: U-E2E-001..U-E2E-009 preserved
confidence_delta:
  - item: scoring readiness
    previous_confidence: unknown
    current_confidence: confirmed
    direction: increased
    reason: all candidates scored or rejected with denominator and evidence labels
    downstream_impact: Stage 5 can audit arithmetic, gates, evidence labels, N/A use, and hidden recommendation language
blocking_items: none
gate_results: score_evidence_complete
audit_flags:
  - A02 highest score but must pass CSS scope audit later
  - A01 remains eligible but with visual precision simplification flag
  - A03/A04 rejected/risk-only
required_user_confirmations: none
partial_rerun_state:
  reusable_until: scoring rules, candidate set, or evidence labels change
  invalidation_triggers: arithmetic error, rubric change, candidate change
  earliest_safe_rerun_stage: /score-evidence
  downstream_payloads_dependent_on_this_stage: /score-audit onward
allowed_work: audit scoring mechanics only
forbidden_work: no recommendation, no new architecture, no re-score except audit correction
stop_conditions: missing score payload or schema mismatch
debug_trace_required: yes
```

### 3.9 /score-audit

Result:

```yaml
stage: /score-audit
status: pass_with_minor_flags
payload_schema: ev4-score-audit-payload@1.2.0-compatible
```

Audit findings:

```yaml
arithmetic_result: pass
unknown_to_number_result: pass
gate_result: pass
contradiction_handling_result: pass
na_handling_result: pass
hidden_recommendation_scan: pass
selection_ambiguity_flag: false
minor_flags:
  - A02 depends on later scoped CSS validator and final audit; this is not a Stage 5 blocker because Stage 8/9 own implementation and CSS validation.
```

Stage 5 repair needed:

```yaml
score_repair_required: no
architecture_repair_required: no
tie_payload_required: no
```

Negative-control check:

```yaml
NC-004_stage_5_misses_arithmetic_or_gate_defect: pass
```

### 3.10 NEXT STAGE ANCHOR — /recommend

```text
NEXT STAGE ANCHOR — /recommend
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /score-audit
target_stage: /recommend
target_stage_hardening_status: confirmed
project_status_version: 0.11.0
payload_schema_in: ev4-score-audit-payload@1.2.0-compatible
payload_schema_out: ev4-recommend-payload@1.1.0-compatible
critical_unknowns: U-E2E-001..U-E2E-009 preserved
confidence_delta:
  - item: eligible candidate set
    previous_confidence: unknown
    current_confidence: confirmed
    direction: increased
    reason: Stage 5 approved A01 and A02; rejected/risk-only handling for A03/A04 was audited
    downstream_impact: Stage 6 may recommend only from audited eligible candidates
blocking_items: none
gate_results: score_audit_pass_with_minor_flags
audit_flags:
  - A02 scoped CSS validator required downstream
  - textual_fixture_no_pixel_validation
required_user_confirmations: none
partial_rerun_state:
  reusable_until: Stage 5 output or candidate eligibility changes
  invalidation_triggers: score audit failure, tie flag, candidate eligibility change
  earliest_safe_rerun_stage: /score-audit
  downstream_payloads_dependent_on_this_stage: /recommend onward
allowed_work: select from audited eligible candidates only
forbidden_work: no new RAG, no hidden preferences, no new scoring
stop_conditions: Stage 5 not pass/pass_with_minor_flags
debug_trace_required: yes
```

### 3.11 /recommend

Result:

```yaml
stage: /recommend
status: pass
payload_schema: ev4-recommend-payload@1.1.0-compatible
selected_candidate_id: A02_native_plus_scoped_decorative_css
```

Recommendation decision:

```yaml
primary_recommendation:
  candidate_id: A02_native_plus_scoped_decorative_css
  reason:
    - highest audited normalized score: 90.4
    - preserves meaningful content as editable native widgets/containers
    - gives the decorative connector/glow layer a named containment strategy
    - avoids flattened visual asset editability loss
    - avoids custom-heavy coordinate-driven architecture
  carried_flags:
    - scoped CSS must be section-scoped and decoration-only
    - connector geometry and z-index remain unknown
    - no exact breakpoints or spacing values are approved
conditional_alternative:
  candidate_id: A01_native_container_widget_composition
  use_if:
    - Custom CSS is disallowed later
    - connector-line visual fidelity may be simplified
rejected_or_risk_only:
  - A03_flattened_visual_asset
  - A04_custom_heavy_absolute_visual_stage
```

Tie protocol:

```yaml
tie_protocol_followed: n/a
hidden_preference_detected: no
```

Negative-control check:

```yaml
NC-005_forced_tie_break: pass
```

### 3.12 NEXT STAGE ANCHOR — /build-tree

```text
NEXT STAGE ANCHOR — /build-tree
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /recommend
target_stage: /build-tree
target_stage_hardening_status: confirmed
project_status_version: 0.11.0
payload_schema_in: ev4-recommend-payload@1.1.0-compatible
payload_schema_out: ev4-build-tree-payload@1.0.0
critical_unknowns: U-E2E-001..U-E2E-009 preserved
confidence_delta:
  - item: selected architecture
    previous_confidence: unknown
    current_confidence: confirmed
    direction: resolved
    reason: Stage 6 selected A02 from audited eligible candidates
    downstream_impact: Stage 7 must build only the native + scoped decorative CSS tree
blocking_items: none
gate_results: recommendation_pass
audit_flags:
  - A02 scoped CSS validation required downstream
  - unknown exact connector geometry/z-index/breakpoints/spacing/token values
required_user_confirmations: none
partial_rerun_state:
  reusable_until: selected candidate or user constraints change
  invalidation_triggers: selected candidate changes, CSS disallowed, user requires dynamic dashboard
  earliest_safe_rerun_stage: /recommend
  downstream_payloads_dependent_on_this_stage: /build-tree onward
allowed_work: produce Structure Panel-readable tree only
forbidden_work: no implementation CSS, no exact values, no re-architecture
stop_conditions: missing Recommendation_Payload or active decision_requires_user_input
debug_trace_required: yes
```

### 3.13 /build-tree

Result:

```yaml
stage: /build-tree
status: pass
payload_schema: ev4-build-tree-payload@1.0.0
structure_panel_readable: yes
editability_preserved: yes
```

Structure tree summary:

```yaml
root:
  node_id: e2e001-hero
  structure_label: Hero / Smart Home Connector
  element_type: section_container
  role: structure
  class_name: smart-home-hero
  children:
    - node_id: e2e001-hero-inner
      structure_label: Hero / Inner Two Column Layout
      element_type: container
      role: structure
      class_name: smart-home-hero__inner
      children:
        - node_id: e2e001-copy
          structure_label: Hero / Copy Column
          element_type: container
          role: content
          class_name: smart-home-hero__copy
          children:
            - Eyebrow Text widget: SMART HOME AUTOMATION
            - Heading widget: Connect every room. Automate every routine.
            - Text Editor widget: Control lights, sensors, scenes, and energy usage from one calm dashboard.
            - Button Group container: Start automation / View devices
            - Feature Chips repeated small containers: No-code scenes / Energy insights / Device groups
        - node_id: e2e001-visual-stage
          structure_label: Hero / Visual Stage
          element_type: overlay_stage
          role: visual_core
          class_name: smart-home-hero__visual-stage
          children:
            - Dashboard Card container
            - Dashboard Status Bar group
            - Device Tiles group with four repeated editable tile containers
            - Energy Chart visual widget/container placeholder
            - Room Status List editable list group
            - Connector Decoration Layer
            - Floating Device Nodes group
            - Background Glow/Grid decoration layer
```

Required tree policies:

```yaml
meaningful_text_real_text: yes
four_device_tiles_editable: yes
dashboard_not_flattened: yes
connector_lines_decorative_layer: yes
visual_stage_named_relative_container: yes
wrapper_budget_result: pass
responsive_contract:
  desktop: two-column layout, right visual stage contained
  tablet: preserve one DOM; allow narrower two-column or early stack based on builder testing
  mobile: stack copy before visual; simplify or reposition decorative connectors; do not hide meaningful floating node labels without preserving equivalent editable content
unknowns_carried_forward:
  - U-E2E-001
  - U-E2E-002
  - U-E2E-003
  - U-E2E-004
  - U-E2E-005
  - U-E2E-006
  - U-E2E-007
  - U-E2E-009
```

Negative-control check:

```yaml
NC-006_flattened_meaningful_content: pass
```

### 3.14 NEXT STAGE ANCHOR — /implementation

```text
NEXT STAGE ANCHOR — /implementation
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /build-tree
target_stage: /implementation
target_stage_hardening_status: confirmed
project_status_version: 0.11.0
payload_schema_in: ev4-build-tree-payload@1.0.0
payload_schema_out: ev4-implementation-payload@1.0.0
critical_unknowns: U-E2E-001..U-E2E-009 preserved, except U-E2E-008 handled by project default for availability but not used as required dependency
confidence_delta:
  - item: tree editability
    previous_confidence: uncertain
    current_confidence: confirmed
    direction: increased
    reason: tree uses editable widgets/containers for copy, CTAs, chips, tiles, chart/list placeholders
    downstream_impact: Stage 8 must map widgets/settings without flattening content
blocking_items: none
gate_results: build_tree_pass
audit_flags:
  - CSS scope validator required for connector/glow layers
  - exact values remain unknown
required_user_confirmations: none
partial_rerun_state:
  reusable_until: selected candidate or tree schema changes
  invalidation_triggers: naming convention change, editability requirement change, CSS policy change
  earliest_safe_rerun_stage: /build-tree
  downstream_payloads_dependent_on_this_stage: /implementation onward
allowed_work: map approved tree to implementation plan
forbidden_work: no redesign, no score changes, no exact invented values
stop_conditions: missing Build_Tree_Payload or unresolved blocking confirmation
debug_trace_required: yes
```

### 3.15 /implementation

Result:

```yaml
stage: /implementation
status: pass_with_minor_flags
payload_schema: ev4-implementation-payload@1.0.0
source_access_result: pass
exact_values_invented: no
```

Implementation summary:

```yaml
elementor_settings_plan:
  layout:
    root: full-width section/container using approved project defaults
    inner: two-column desktop structure, responsive stack without exact breakpoint value
  classes:
    - smart-home-hero
    - smart-home-hero__inner
    - smart-home-hero__copy
    - smart-home-hero__actions
    - smart-home-hero__chips
    - smart-home-hero__visual-stage
    - smart-home-hero__dashboard-card
    - smart-home-hero__device-tile
    - smart-home-hero__connector-layer
    - smart-home-hero__floating-node
  variables:
    - color/background/light-neutral: token placeholder
    - color/accent/technical: token placeholder
    - spacing/section-y: token placeholder
    - radius/card: token placeholder
    - shadow/card-soft: token placeholder
widget_mapping:
  headline: Heading widget
  paragraph: Text Editor widget
  ctas: Button widgets
  chips: repeated editable containers/text widgets
  dashboard_tiles: repeated editable containers/text/icon placeholders
  chart: visual placeholder container or supported chart-like static editable composition; dynamic chart remains unknown
  connector_lines: decoration-only scoped CSS or SVG/shape layer inside visual stage
scoped_css_need_map:
  css_needed: yes
  reason: decorative connector lines and glow/grid may exceed native controls
  scope_rule: must be attached under .smart-home-hero only
  forbidden_selectors:
    - html
    - body
    - :root unless using approved design tokens outside this section
    - global widget selectors without parent section class
responsive_implementation_plan:
  desktop: two-column, dashboard visual on right
  tablet: preserve one DOM; test wrapping/stacking; no exact breakpoint invented
  mobile: stack; simplify connector layer; preserve floating node meaning as visible/editable labels or equivalent content if meaningful
position_layering_plan:
  visual_stage_position_context: relative
  decoration_layers: contained within visual stage
  meaningful_content: normal flow unless explicitly documented as overlay label with mobile fallback
asset_accessibility_map:
  decorative_glow_grid: decorative
  connector_lines: decorative if not required for understanding
  floating_nodes: meaningful labels unless final copy states decorative-only
  dashboard_content: meaningful visual core; not flattened
implementation_risks:
  - medium: textual fixture cannot validate exact visual match
  - low: exact token values unknown
  - low: icon library/source unknown
  - low: dynamic data requirement unresolved
```

Negative-control check:

```yaml
NC-007_invented_exact_settings_css_values: pass
```

### 3.16 NEXT STAGE ANCHOR — /final-audit

```text
NEXT STAGE ANCHOR — /final-audit
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /implementation
target_stage: /final-audit
target_stage_hardening_status: confirmed
project_status_version: 0.11.0
payload_schema_in: ev4-implementation-payload@1.0.0
payload_schema_out: ev4-final-audit-payload@1.0.0
critical_unknowns: U-E2E-001..U-E2E-009 preserved where unresolved
confidence_delta:
  - item: implementation boundary compliance
    previous_confidence: unknown
    current_confidence: confirmed
    direction: increased
    reason: implementation plan used token placeholders and section-scoped CSS only; no exact unsupported values
    downstream_impact: Stage 9 may audit instead of repairing
blocking_items: none
gate_results: implementation_pass_with_minor_flags
audit_flags:
  - medium: textual fixture cannot validate pixel-accurate screenshot interpretation
  - low: exact tokens, icon library, animation, dynamic data unresolved
required_user_confirmations: none
partial_rerun_state:
  reusable_until: implementation payload, tree, or selected candidate changes
  invalidation_triggers: exact export evidence appears, CSS policy changes, dynamic data becomes required
  earliest_safe_rerun_stage: /implementation
  downstream_payloads_dependent_on_this_stage: /final-audit onward
allowed_work: audit implementation only
forbidden_work: no silent repair, no new implementation, no new architecture
stop_conditions: missing Implementation_Payload or unresolved blocker risk
debug_trace_required: yes
```

### 3.17 /final-audit

Result:

```yaml
stage: /final-audit
status: pass_with_minor_flags
payload_schema: ev4-final-audit-payload@1.0.0
blocker_findings: []
high_findings: []
medium_findings:
  - E2E001-MED-001: textual fixture cannot validate pixel-accurate screenshot interpretation or exact visual matching
low_findings:
  - E2E001-LOW-001: exact token values remain unknown
  - E2E001-LOW-002: exact icon source/library remains unknown
  - E2E001-LOW-003: animation requirement remains unknown and must not be implemented by default
  - E2E001-LOW-004: dynamic dashboard data requirement remains unknown and must not be assumed
```

Audit checklist:

```yaml
architecture_preservation_audit: pass
build_tree_preservation_audit: pass
elementor_native_dependency_audit: pass
editability_audit: pass
position_layering_audit: pass
responsive_audit: pass_with_minor_flags
accessibility_audit: pass_with_minor_flags
performance_dom_audit: pass
design_system_audit: pass
scoped_css_audit: pass
asset_media_audit: pass_with_minor_flags
dynamic_data_interaction_audit: pass_with_minor_flags
unknown_confirmation_survival_audit: pass
```

Stage 9 blocking behavior test:

```yaml
global_css_leak_passed: no
hidden_meaningful_content_passed: no
architecture_drift_passed: no
unresolved_blocker_or_high_allowed: no
result: pass
```

Negative-control check:

```yaml
NC-008_final_audit_passes_global_css_or_hidden_content: pass
```

### 3.18 NEXT STAGE ANCHOR — /handoff-export

```text
NEXT STAGE ANCHOR — /handoff-export
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /final-audit
target_stage: /handoff-export
target_stage_hardening_status: confirmed
project_status_version: 0.11.0
payload_schema_in: ev4-final-audit-payload@1.0.0
payload_schema_out: ev4-handoff-export-payload@1.0.0
critical_unknowns: U-E2E-001..U-E2E-009 preserved or explicitly classified as project-default/non-required
confidence_delta:
  - item: final audit eligibility
    previous_confidence: unknown
    current_confidence: confirmed
    direction: increased
    reason: final audit found no blocker/high issues and preserved all flags
    downstream_impact: Stage 10 may package final audited handoff
blocking_items: none
gate_results: final_audit_pass_with_minor_flags
audit_flags:
  - E2E001-MED-001 textual fixture cannot validate pixel-accurate screenshot interpretation
  - E2E001-LOW-001 exact token values unknown
  - E2E001-LOW-002 exact icon source/library unknown
  - E2E001-LOW-003 animation requirement unknown
  - E2E001-LOW-004 dynamic dashboard data requirement unknown
required_user_confirmations: none
partial_rerun_state:
  reusable_until: final audit payload changes
  invalidation_triggers: blocker/high finding appears, implementation changes, export evidence contradicts plan
  earliest_safe_rerun_stage: /final-audit
  downstream_payloads_dependent_on_this_stage: /handoff-export
allowed_work: package final audited outputs only
forbidden_work: no new CSS, widgets, architecture, exact values, or softened findings
stop_conditions: missing final audit payload or blocker/high issue
debug_trace_required: yes
```

### 3.19 /handoff-export

Result:

```yaml
stage: /handoff-export
status: pass
payload_schema: ev4-handoff-export-payload@1.0.0
mode: final_builder_handoff
audit_flags_preserved: yes
new_decisions_introduced: no
```

Final builder handoff summary:

```yaml
approved_architecture: A02_native_plus_scoped_decorative_css
builder_tree: use Stage 7 Structure Panel tree exactly
implementation: use Stage 8 maps and token placeholders; no exact values invented
css: section-scoped only under .smart-home-hero; decoration-only; no global leak
responsive: one DOM; stack/simplify connector layer on mobile; preserve meaningful node labels if meaningful
flags_to_preserve:
  medium:
    - textual fixture cannot validate pixel-accurate screenshot interpretation
  low:
    - exact token values unknown
    - icon source/library unknown
    - animation requirement unknown
    - dynamic dashboard data requirement unknown
unknowns_preserved: yes
release_boundary: E2E-001 passes the prompt-pack full-pipeline validation contract with minor flags
```

Negative-control check:

```yaml
NC-009_stage_10_softens_failed_audit: pass
NC-010_unknown_dropped_without_evidence: pass
```

---

## 4. E2E_TEST_REPORT

```yaml
E2E_TEST_REPORT:
  schema: ev4-e2e-test-report@1.0.0
  test_id: E2E-001
  fixture: experiments/E2E-001-smart-home-connector-fixture.md
  fixture_type: realistic_mockup_description
  project_status_version_at_start: 0.11.0
  e2e_status: pass_with_minor_flags
  stages_completed:
    - /intake
    - /decompose
    - /architectures
    - /score-evidence
    - /score-audit
    - /recommend
    - /build-tree
    - /implementation
    - /final-audit
    - /handoff-export
  first_failure_stage: null
  failure_type: null
  release_blocker_removed: yes
  release_blocker_reason: >
    Full pipeline reached /handoff-export; no blocker/high issue remains; anchors and payloads were emitted;
    unknowns were preserved; Stage 9 preserved and classified all findings; Stage 10 preserved flags and did not introduce new decisions.
    The remaining textual-fixture limitation is a medium validation-scope flag, not a blocker for the prompt-pack contract E2E.
  source_access_violations: []
  anchor_validation:
    anchors_checked:
      - /intake_to_/decompose
      - /decompose_to_/architectures
      - /architectures_to_/score-evidence
      - /score-evidence_to_/score-audit
      - /score-audit_to_/recommend
      - /recommend_to_/build-tree
      - /build-tree_to_/implementation
      - /implementation_to_/final-audit
      - /final-audit_to_/handoff-export
    anchor_failures: []
  payload_validation:
    payloads_checked:
      - ev4-intake-payload@1.0.0-compatible
      - ev4-decomposition-payload@1.0.1-compatible
      - ev4-architecture-candidates-payload@1.1.0-compatible
      - ev4-score-evidence-payload@1.3.0
      - ev4-score-audit-payload@1.2.0-compatible
      - ev4-recommend-payload@1.1.0-compatible
      - ev4-build-tree-payload@1.0.0
      - ev4-implementation-payload@1.0.0
      - ev4-final-audit-payload@1.0.0
      - ev4-handoff-export-payload@1.0.0
    payload_schema_failures: []
  unknown_propagation:
    introduced_unknowns:
      - U-E2E-001
      - U-E2E-002
      - U-E2E-003
      - U-E2E-004
      - U-E2E-005
      - U-E2E-006
      - U-E2E-007
      - U-E2E-008
      - U-E2E-009
    preserved_unknowns:
      - U-E2E-001
      - U-E2E-002
      - U-E2E-003
      - U-E2E-004
      - U-E2E-005
      - U-E2E-006
      - U-E2E-007
      - U-E2E-009
    resolved_unknowns_with_evidence:
      - unknown_id: U-E2E-008
        resolution: Elementor Pro availability exists as project default, but no Pro-only feature was required by the selected architecture.
        resolution_source: stages/01_INTAKE.md project defaults
    dropped_unknowns_without_evidence: []
  scoring_audit:
    arithmetic_result: pass
    unknown_to_number_result: pass
    gate_result: pass
    contradiction_handling_result: pass
  recommendation_audit:
    eligible_candidates_only: yes
    tie_protocol_followed: n/a
    hidden_preference_detected: no
  build_tree_audit:
    structure_panel_readable: yes
    editability_preserved: yes
    wrapper_budget_result: pass
    overlay_containment_result: pass
  implementation_audit:
    settings_schema_valid: yes
    scoped_css_valid: yes
    exact_values_invented: no
    responsive_risks_preserved: yes
  final_audit_result:
    final_audit_status: pass_with_minor_flags
    blocker_findings: []
    high_findings: []
    medium_findings:
      - E2E001-MED-001: textual fixture cannot validate pixel-accurate screenshot interpretation or exact visual matching
    low_findings:
      - E2E001-LOW-001: exact token values remain unknown
      - E2E001-LOW-002: exact icon source/library remains unknown
      - E2E001-LOW-003: animation requirement remains unknown
      - E2E001-LOW-004: dynamic dashboard data requirement remains unknown
    info_findings: []
  handoff_export_result:
    mode: final_builder_handoff
    audit_flags_preserved: yes
    new_decisions_introduced: no
  repair_routes: []
  required_contract_changes: []
  next_work_anchor: NEXT WORK ANCHOR — /research hardening
```

---

## 5. Source Access Matrix Result

```yaml
/intake:
  status: pass
  violation: none
/decompose:
  status: pass
  violation: none
  note: used fixture facts only; no RAG/TUYA visual inference
/architectures:
  status: pass
  violation: none
  note: candidate enumeration only; no recommendation
/score-evidence:
  status: pass
  violation: none
  note: scored from Stage 2/3 + rubric; no TUYA/RAG boost
/score-audit:
  status: pass
  violation: none
  note: audited scoring mechanics only
/recommend:
  status: pass
  violation: none
  note: recommended only from audited eligible candidates
/build-tree:
  status: pass
  violation: none
  note: built from selected recommendation only
/implementation:
  status: pass
  violation: none
  note: no exact unsupported values invented
/final-audit:
  status: pass
  violation: none
  note: audited preservation; no silent repair
/handoff-export:
  status: pass
  violation: none
  note: packaged final audited outputs only
```

---

## 6. Negative-Control Probe Register

```yaml
NC-001: pass
NC-002: pass
NC-003: pass
NC-004: pass
NC-005: pass
NC-006: pass
NC-007: pass
NC-008: pass
NC-009: pass
NC-010: pass
```

---

## 7. EV4_DEBUG_TRACE

```json
{
  "schema": "ev4-debug-trace@1.0.0",
  "run_id": "E2E-001",
  "stage": "/e2e-test",
  "stage_version": "ev4-e2e-test-report@1.0.0",
  "input_digest": {
    "inputs_received": [
      "STATUS.md@0.11.0",
      "experiments/END_TO_END_PIPELINE_TEST_PLAN.md",
      "experiments/E2E-001-smart-home-connector-fixture.md",
      "active contracts and stage files"
    ],
    "inputs_missing": [],
    "input_payload_schemas": [
      "ev4-e2e-test-plan@1.0.0",
      "ev4-e2e-fixture@1.0.0",
      "ev4-stage-anchor@1.1.0",
      "ev4-debug-trace@1.0.0"
    ]
  },
  "decision_log": [
    {
      "decision_id": "D-E2E-001",
      "decision": "selected E2E-001 as next unfinished highest-priority step",
      "target": "/e2e-test",
      "basis": {
        "evidence_ids": ["STATUS-current-next-step", "E2E-plan-next-work-anchor"],
        "rule_ids": ["release-boundary-rule"],
        "unknown_ids": []
      },
      "confidence": "confirmed",
      "downstream_effect": "run full pipeline and produce E2E report"
    },
    {
      "decision_id": "D-E2E-002",
      "decision": "selected A02 after Stage 5 authorization",
      "target": "/recommend",
      "basis": {
        "evidence_ids": ["Stage4-scoring-summary", "Stage5-audit-pass"],
        "rule_ids": ["Stage6-eligible-candidates-only"],
        "unknown_ids": ["U-E2E-001", "U-E2E-006"]
      },
      "confidence": "confirmed",
      "downstream_effect": "build native editable tree with scoped decorative CSS"
    },
    {
      "decision_id": "D-E2E-003",
      "decision": "release blocker removable for prompt-pack E2E contract with minor flags",
      "target": "STATUS.md",
      "basis": {
        "evidence_ids": ["E2E_TEST_REPORT"],
        "rule_ids": ["E2E-release-blocker-rule"],
        "unknown_ids": ["pixel-accurate-screenshot-interpretation"]
      },
      "confidence": "confirmed",
      "downstream_effect": "STATUS may move to 0.12.0 and next work may focus on /research hardening or screenshot-based E2E"
    }
  ],
  "evidence_map": [
    {
      "evidence_id": "E-FIXTURE-001",
      "source_stage": "intake",
      "source_payload": "experiments/E2E-001-smart-home-connector-fixture.md",
      "claim_supported": "fixture has repeated tiles, visual core, decorative layer, responsive risk, and unknowns",
      "evidence_label": "SUPPORTED_EVIDENCE",
      "quote_or_summary": "Fixture stress features table and known unknowns."
    },
    {
      "evidence_id": "E-RUBRIC-001",
      "source_stage": "score-evidence",
      "source_payload": "rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md",
      "claim_supported": "weighted scoring uses total 25 weights and normalized total over applicable raw max",
      "evidence_label": "SUPPORTED_EVIDENCE",
      "quote_or_summary": "Rubric scoring method and criteria weights."
    },
    {
      "evidence_id": "E-CONTRACT-001",
      "source_stage": "e2e-test",
      "source_payload": "contracts/STAGE_ANCHOR_CONTRACT.md",
      "claim_supported": "anchors must preserve unknowns, blockers, gate results, confidence deltas, and partial rerun state",
      "evidence_label": "SUPPORTED_EVIDENCE",
      "quote_or_summary": "Stage Anchor Contract v1.1 canonical fields."
    }
  ],
  "unknown_register": [
    {
      "unknown_id": "U-E2E-001",
      "unknown": "exact desktop/tablet/mobile breakpoints are not provided",
      "introduced_at_stage": "/decompose",
      "propagated_to_stages": ["/architectures", "/score-evidence", "/score-audit", "/recommend", "/build-tree", "/implementation", "/final-audit", "/handoff-export"],
      "resolved": false,
      "resolution_source": null,
      "effect_if_unresolved": "use responsive strategy placeholders; do not invent breakpoint values"
    },
    {
      "unknown_id": "U-E2E-006",
      "unknown": "exact connector-line geometry and z-index are not provided",
      "introduced_at_stage": "/decompose",
      "propagated_to_stages": ["/architectures", "/score-evidence", "/score-audit", "/recommend", "/build-tree", "/implementation", "/final-audit", "/handoff-export"],
      "resolved": false,
      "resolution_source": null,
      "effect_if_unresolved": "keep connector CSS decorative and section-scoped; no exact geometry or z-index"
    },
    {
      "unknown_id": "U-E2E-009",
      "unknown": "whether right dashboard should use dynamic data is not provided",
      "introduced_at_stage": "/decompose",
      "propagated_to_stages": ["/architectures", "/recommend", "/build-tree", "/implementation", "/final-audit", "/handoff-export"],
      "resolved": false,
      "resolution_source": null,
      "effect_if_unresolved": "do not introduce dynamic data; package as editable illustrative dashboard"
    }
  ],
  "rule_application_log": [
    {
      "rule_id": "R-E2E-001",
      "rule_source": "stage_contract",
      "rule_name": "Stage Source Access Matrix",
      "applied_to": "all stages",
      "result": "pass",
      "notes": "No forbidden source use detected."
    },
    {
      "rule_id": "R-E2E-002",
      "rule_source": "rubric",
      "rule_name": "unknowns are not numeric evidence",
      "applied_to": "/score-evidence",
      "result": "pass",
      "notes": "Exact breakpoints, spacing, z-index, assets, and animation remained unknown."
    },
    {
      "rule_id": "R-E2E-003",
      "rule_source": "hardening_patch",
      "rule_name": "Stage 10 flag preservation",
      "applied_to": "/handoff-export",
      "result": "pass",
      "notes": "Medium and low flags were preserved."
    }
  ],
  "failure_symptom_index": [],
  "repair_route": null,
  "handoff_payload_schema": "ev4-handoff-export-payload@1.0.0"
}
```

---

## 8. Release Boundary Result

```yaml
release_blocker_removed: yes
release_blocker_scope: prompt-pack full-pipeline E2E contract
not_claimed:
  - pixel-accurate screenshot interpretation validated
  - real Elementor export JSON validated
  - live browser/Elementor rendering validated
remaining_non_blocking_flags:
  - E2E001-MED-001 textual fixture limitation
recommended_next_validation:
  - run E2E-002 with actual screenshot or Elementor export evidence when available
```

---

## 9. NEXT WORK ANCHOR — /research hardening

```text
NEXT WORK ANCHOR — /research hardening
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /e2e-test
target_stage: /research
target_stage_hardening_status: draft
project_status_version: 0.12.0
payload_schema_in:
  - ev4-e2e-test-report@1.0.0
  - active RAG strategy v0.3.0
  - active project overrides v0.2.0
payload_schema_out:
  - ev4-research-payload@1.0.0 or newer active schema

Carry-forward facts:
- key_decisions:
  - E2E-001 completed full pipeline through /handoff-export.
  - E2E status is pass_with_minor_flags.
  - Prompt-pack E2E release blocker is removable for textual-fixture contract validation.
  - /research remains draft_required and is now the highest-priority unfinished stage/contract.
- selected_or_active_candidates:
  - A02 native + section-scoped decorative CSS was selected in E2E-001.
- rejected_or_blocked_candidates:
  - A03 flattened right-side visual asset.
  - A04 custom-heavy absolute visual stage.
- critical_unknowns:
  - Pixel-accurate screenshot interpretation is still unvalidated by E2E-001.
  - Real Elementor export evidence is not available.
  - /research lacks a confirmed payload schema and source pinning contract.
- confidence_delta:
  - item: prompt-pack full-pipeline continuity
    previous_confidence: unknown
    current_confidence: confirmed_with_minor_flags
    direction: increased
    reason: E2E-001 completed all stages, preserved unknowns, and passed negative-control probes.
    downstream_impact: next work can harden /research rather than continue Stage 8-10 contract hardening.
- blocking_items:
  - /research is draft_required.
- gate_results:
  - E2E-001 full-pipeline gate passed_with_minor_flags.
  - release blocker removed for prompt-pack E2E contract, but raster screenshot validation remains a non-blocking limitation.
- audit_flags:
  - textual fixture cannot validate pixel-accurate screenshot interpretation.
  - /research must not let RAG bypass /decompose, /score-evidence, /score-audit, or /recommend.
- tie_or_ambiguity_flags:
  - none active.
- required_user_confirmations:
  - none for /research hardening.
- repair_routes:
  - if /research source policy contradicts RAG Strategy, repair /research first and invalidate only research-dependent downstream docs.

Partial rerun state:
- reusable_until: E2E report remains reusable unless fixture, source matrix, Stage Anchor contract, Debug Trace contract, or stage schemas change.
- invalidation_triggers:
  - E2E fixture changed
  - RAG Strategy changed
  - /research source policy changed
  - Stage Anchor Contract changed
  - Debug Trace Contract changed
- earliest_safe_rerun_stage: /research for research contract hardening; /e2e-test if validating a new fixture only.
- downstream_payloads_dependent_on_this_stage:
  - ev4-research-payload@1.0.0
  - any future source-pinned research fixtures

Stage input package:
- required_inputs_present:
  - STATUS.md
  - references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
  - knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
  - 02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md
  - contracts/STAGE_ANCHOR_CONTRACT.md
  - diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
  - experiments/E2E-001-test-report.md
- required_inputs_missing:
  - confirmed /research stage contract
- files_or_sections_to_reference:
  - stages/02_DECOMPOSE.md
  - stages/03_ARCHITECTURES.md
  - stages/04_SCORE_EVIDENCE.md
  - stages/05_SCORE_AUDIT.md
  - stages/06_RECOMMEND.md
  - references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md

Stage boundary:
- allowed_work:
  - harden /research input gate, source classification, source pinning, retrieval output schema, forbidden RAG behavior, repair routes, self-audit, debug trace, and anchor handoff.
- forbidden_work:
  - do not let /research infer visual groups.
  - do not let /research score or recommend candidates.
  - do not let official docs prove project-specific behavior.
  - do not let TUYA prove platform capability.
- stop_conditions:
  - missing active RAG strategy.
  - missing source classification rules.
  - inability to define ev4-research-payload schema.
  - unresolved conflict between /research contract and Stage Source Access Matrix.

Debug trace:
- debug_trace_required: yes
- previous_debug_trace_id: E2E-001
- expected_debug_trace_schema: ev4-debug-trace@1.0.0
```
