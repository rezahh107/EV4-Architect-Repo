# EV4 Responsive Start Packet Contract

Status: active_v1.0.0  
Version: 1.0.0  
Schema: `ev4-responsive-start-packet@1.0.0`  
Target consumer: `EV4 Responsive Architect` / downstream responsive-tree pipeline  
Source producer: `Elementor V4 Architect Prompt Pack` `/handoff-export`

---

## 1. Purpose

`EV4_RESPONSIVE_START_PACKET` is a conservative downstream handoff artifact.

It packages the audited desktop architecture/tree record plus responsive-risk and responsive-structure signals so a downstream responsive-tree system can start with evidence instead of guessing.

It does not change the winning architecture, does not soften the rubric, and does not treat a separate mobile/tablet section as a quality improvement for the desktop architecture.

Core rule:

```text
Package responsive routing inputs. Do not redesign, repair, re-score, or infer a final responsive tree.
```

---

## 2. Non-Purpose

This packet must not:

- claim that the desktop architecture is responsive-validated;
- claim live Elementor rendering;
- claim real Elementor export JSON validation;
- claim pixel-accurate screenshot interpretation;
- convert absent tablet/mobile evidence into a passing responsive result;
- treat a desktop screenshot as proof of mobile behavior;
- use a separate mobile/tablet section to raise the desktop candidate's `Responsiveness` score;
- resolve `responsive_unknowns` without named evidence;
- hide meaningful content on mobile/tablet without explicit upstream authorization;
- decide final breakpoint values unless they are present in approved inputs.

---

## 3. Required Producer Inputs

The producer may emit a full packet only when these upstream payloads are present or explicitly marked as unavailable:

```yaml
required_upstream_inputs:
  decomposition_snapshot:
    source_stage: /decompose
    used_for:
      - visible groups
      - meaningful content
      - repeated component candidates
      - visual core
      - decoration layers
      - overlay / connector candidates
      - responsive risks
      - unknowns
  score_evidence_payload:
    source_stage: /score-evidence
    used_for:
      - responsiveness score
      - evidence label
      - confidence
      - scoring caps
      - unresolved evidence state
  score_audit_payload:
    source_stage: /score-audit
    used_for:
      - arithmetic and evidence-state confirmation
      - gate status
      - final score eligibility state
  recommendation_payload:
    source_stage: /recommend
    used_for:
      - selected candidate identity
      - selected candidate family
      - recommendation boundary
  build_tree_payload:
    source_stage: /build-tree
    used_for:
      - desktop structure tree
      - naming map
      - responsive structure contract
      - content editability map
      - overlay / decoration map
      - design-system hook map
  final_audit_payload:
    source_stage: /final-audit
    used_for:
      - final blockers
      - responsive audit flags
      - unresolved unknowns
      - handoff eligibility
```

If any required upstream input is missing, the packet may still be emitted as `packet_status: blocked_or_partial`, but the missing input must remain visible.

---

## 4. Route Vocabulary

The downstream route seed must use this closed set:

```yaml
responsive_route_seed:
  route:
    - same_tree_responsive_overrides
    - viewport_specific_variant_tree
    - hybrid_split
    - unresolved_requires_designer_input
  confidence:
    - high
    - medium
    - low
    - unknown
```

Definitions:

| Route | Meaning |
|---|---|
| `same_tree_responsive_overrides` | Current evidence suggests the approved desktop tree can be adapted with Elementor responsive controls, order, direction, spacing, sizing, and limited visibility controls. |
| `viewport_specific_variant_tree` | Current evidence suggests the responsive mockup is materially a separate mobile/tablet composition and must be architected as a viewport-specific variant, not treated as a repair of the desktop tree. |
| `hybrid_split` | Some groups are same-tree candidates while other groups need a viewport-specific variant. |
| `unresolved_requires_designer_input` | The current record cannot safely decide whether the responsive design is same-section adaptation or a separate viewport variant. |

---

## 5. Designer-Provided Variant Boundary

A separate mobile/tablet section is a risk by default.

It may be routed as a legitimate viewport-specific variant only when at least one of these is present:

```yaml
variant_authorization_evidence:
  - explicit designer responsive mockup showing a materially different mobile/tablet composition
  - explicit user instruction that the desktop section is desktop-only and a separate responsive section must be built
  - explicit Stage 6/7 authorization that a viewport-specific section is required and not merely a workaround
```

If none of the above is present, hidden/duplicate responsive sections must remain a responsiveness risk, not a positive architecture feature.

---

## 6. Packet Schema

```yaml
payload_schema: ev4-responsive-start-packet@1.0.0
producer_stage: /handoff-export
consumer_project: EV4 Responsive Architect
packet_status: full | partial | blocked_or_partial

section_identity:
  section_id:
  selected_candidate_id:
  selected_candidate_family:
  source_run_id:

source_payload_ledger:
  - payload_name:
    schema:
    source_stage:
    status: present | missing | partial | incompatible | referenced_only
    used_for:
    limitation:

desktop_architecture_source:
  recommendation_summary:
  build_tree_payload_ref:
  structure_tree:
  naming_map:
  class_map:
  design_system_hook_map:

responsive_contract_from_ev4_architect:
  desktop_structure:
  tablet_structure:
  mobile_structure:
  responsive_order:
  hide_or_simplify_allowed:
  responsive_unknowns:

responsive_scoring_summary:
  same_tree_responsiveness_score:
  responsiveness_evidence_label:
  responsiveness_confidence:
  responsiveness_score_status:
  scoring_caps_applied:
  missing_evidence:
  unresolved_mobile_or_tablet_unknowns:
  note: "This score evaluates the selected architecture's same-tree responsiveness potential; it does not validate a downstream viewport-specific variant."

decomposition_transfer:
  visible_groups:
  meaningful_content:
  repeated_component_candidates:
  visual_core:
  decoration_layers:
  overlay_connector_candidates:
  responsive_risks:
  unknowns:

content_and_accessibility_transfer:
  content_editability_map:
  meaningful_content_hide_policy:
  asset_accessibility_map:
  reading_order_constraints:
  focus_or_interaction_unknowns:

overlay_and_decoration_transfer:
  overlay_decoration_map:
  decoration_meaningfulness_status:
  connector_simplification_allowed:
  mobile_collision_risks:

routing_seed_for_responsive_architect:
  route: same_tree_responsive_overrides | viewport_specific_variant_tree | hybrid_split | unresolved_requires_designer_input
  confidence: high | medium | low | unknown
  reason:
  route_is_advisory_only: true
  required_downstream_inputs:
    - responsive designer mockup or explicit no-responsive-mockup state
    - target breakpoint scope
    - visibility policy preference
  blockers:
  questions_for_designer:

forbidden_downstream_assumptions:
  - do_not_assume_mobile_is_same_as_desktop
  - do_not_treat_desktop_screenshot_as_mobile_evidence
  - do_not_hide_meaningful_content_without_authorization
  - do_not_treat_viewport_variant_as_desktop_responsiveness_score_improvement
  - do_not_treat_old_responsive_structure_contract_as_final_responsive_truth
  - do_not_claim_live_render_or_export_validation_from_this_packet
```

---

## 7. Producer Rules

1. Preserve all carried-forward responsive unknowns.
2. Preserve all final-audit responsive flags.
3. Preserve meaningful-content editability and hiding constraints.
4. Preserve overlay/connector meaningfulness state.
5. Use the route seed as advisory only.
6. Do not use this packet to alter Stage 4 scoring or Stage 6 recommendation.
7. Do not emit a full packet if Stage 9 failed with blocker/high findings that affect the responsive handoff.
8. If Stage 10 output is blocked, emit a blocked/partial packet only when it helps downstream repair triage; do not package it as builder-ready.

---

## 8. Consumer Rules

A downstream responsive system must treat this packet as a start packet, not a final responsive design.

The downstream system must still ingest:

```yaml
required_downstream_evidence:
  responsive_designer_mockup: required_or_explicitly_absent
  target_breakpoint_scope: required
  current_desktop_build_or_tree: required
  user_visibility_policy: required_if_variant_possible
```

If the downstream responsive mockup conflicts with this packet, the downstream system must report the conflict instead of silently preferring either source.

---

## 9. Pass Criteria

This contract is satisfied only if future handoff outputs:

- include `EV4_RESPONSIVE_START_PACKET` when downstream responsive work is requested or likely;
- keep the packet advisory;
- preserve scoring strictness;
- preserve hidden/duplicate section risk unless variant authorization exists;
- preserve unresolved responsive unknowns;
- keep forbidden validation claims blocked.
