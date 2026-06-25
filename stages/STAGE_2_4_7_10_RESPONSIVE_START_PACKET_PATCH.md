# Stage 2/4/7/10 Responsive Start Packet Patch

Status: confirmed_hardening_patch_v1.0.0  
Version: 1.0.0  
Applies to:
- `stages/02_DECOMPOSE.md`
- `stages/04_SCORE_EVIDENCE.md`
- `rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md`
- `stages/07_BUILD_TREE.md`
- `stages/09_FINAL_AUDIT.md`
- `stages/10_HANDOFF_EXPORT.md`
- `contracts/EV4_RESPONSIVE_START_PACKET_CONTRACT.md`

Patch mode: conservative downstream-handoff alignment for EV4 Responsive Architect.

---

## 1. Purpose

This patch adds a guarded way for the existing Elementor V4 Architect pipeline to hand responsive-start evidence to a downstream responsive-tree system.

It does not replace the current stage contracts. It adds an alignment layer so the prior pipeline can produce a clean `EV4_RESPONSIVE_START_PACKET` without weakening architecture scoring.

Core patch rule:

```text
Keep the desktop architecture scoring strict. Add downstream responsive routing metadata and a start packet. Do not treat viewport-specific variants as score boosters.
```

---

## 2. Why This Patch Exists

The existing pipeline already has responsive awareness:

- `/decompose` identifies `Responsive Risks`.
- `/score-evidence` scores `Responsiveness` as a high-weight criterion.
- `/build-tree` emits a `responsive_structure_contract`.
- `/handoff-export` includes a `RESPONSIVE CHECKLIST`.

However, the existing pipeline is primarily a desktop/section architecture pipeline. Its `Responsiveness` score asks whether the selected architecture can work across breakpoints without brittle duplication.

A downstream `EV4 Responsive Architect` needs a different artifact:

```text
approved desktop tree + responsive risks + responsive structure contract + unknowns + route seed
```

This patch provides that artifact while preserving the original scoring standard.

---

## 3. Non-Regression Rule for the Rubric

The rubric must not be softened into accepting hidden/duplicate responsive sections as generally high quality.

Current rubric principle remains active:

```text
One DOM with credible desktop/tablet/mobile strategy and limited overrides is the strongest same-tree responsiveness pattern.
```

Patch clarification:

```text
A separate mobile/tablet section is still a responsiveness risk for the desktop architecture candidate unless it is explicitly classified as a designer-provided viewport-specific variant.

Even when a viewport-specific variant is authorized, it must not raise the desktop candidate's same-tree Responsiveness score. It must emit a downstream routing flag instead.
```

Forbidden scoring shortcut:

```text
Do not give a high Responsiveness score because the implementation can duplicate the section and hide/show per device.
```

Allowed routing distinction:

```text
If a designer-provided mobile/tablet mockup materially differs from the desktop section, route that work as `viewport_specific_variant_tree` or `hybrid_split` for downstream architecture, rather than scoring it as a successful same-tree responsive solution.
```

---

## 4. Stage 2 Patch — `/decompose`

Stage 2 keeps its existing role: it observes visible groups, content, visual core, decoration, overlay/connector candidates, responsive risks, and unknowns.

Add this optional output block after `Responsive Risks` and before `Unknowns` when evidence exists:

```yaml
responsive_relationship_hints:
  same_section_adaptation_likely:
    value: yes | no | unknown
    evidence:
    confidence: observed | likely | unknown
  viewport_specific_variant_likely:
    value: yes | no | unknown
    evidence:
    confidence: observed | likely | unknown
  hybrid_split_likely:
    value: yes | no | unknown
    evidence:
    confidence: observed | likely | unknown
  notes:
```

Rules:

- This is a hint, not a route decision.
- Stage 2 must not recommend `same_tree_responsive_overrides`, `viewport_specific_variant_tree`, or `hybrid_split` as final architecture.
- Stage 2 must not infer actual Elementor DOM or breakpoint behavior.
- If only a desktop screenshot is provided, mark responsive relationship as `unknown` unless the user explicitly states a responsive relationship.
- If a responsive mockup is supplied and it materially changes composition, Stage 2 may mark `viewport_specific_variant_likely: yes` with evidence.

---

## 5. Stage 4 Patch — `/score-evidence` and Rubric Binding

Stage 4 must continue scoring the selected architecture candidates against the active rubric.

Add this structured note to the `Responsiveness` criterion output when relevant:

```yaml
responsiveness_routing_note:
  same_tree_responsiveness_score:
  evidence_label:
  confidence:
  designer_provided_variant_signal:
    present: yes | no | unknown
    source_ref:
  duplicate_hidden_section_risk:
    status: none | low | medium | high | blocker | unknown
    reason:
  downstream_route_seed:
    route: same_tree_responsive_overrides | viewport_specific_variant_tree | hybrid_split | unresolved_requires_designer_input
    confidence: high | medium | low | unknown
    advisory_only: true
```

Rules:

- `same_tree_responsiveness_score` is the actual rubric score.
- `downstream_route_seed` is not part of the numeric score.
- A designer-provided viewport-specific variant may prevent false rejection of the overall project workflow, but it must not inflate the desktop architecture's same-tree `Responsiveness` score.
- A duplicate/hidden section without designer authorization remains a risk and may lower the same-tree responsiveness score.
- If the route seed is `viewport_specific_variant_tree`, Stage 4 must state that the downstream work belongs to a viewport-specific architecture pass, not to score improvement.

---

## 6. Stage 7 Patch — `/build-tree`

Stage 7 already owns the `responsive_structure_contract`.

Add this output section after `RESPONSIVE STRUCTURE CONTRACT` and before `DESIGN-SYSTEM HOOK MAP`:

```text
RESPONSIVE START PACKET DRAFT
```

Required draft fields:

```yaml
responsive_start_packet_draft:
  schema: ev4-responsive-start-packet@1.0.0_draft
  draft_status: complete | partial | blocked
  section_identity:
    section_id:
    selected_candidate_id:
    selected_candidate_family:
  desktop_tree_source:
    structure_tree_ref:
    naming_map_ref:
    class_map_ref:
    design_system_hook_map_ref:
  responsive_contract_from_build_tree:
    desktop_structure:
    tablet_structure:
    mobile_structure:
    responsive_order:
    hide_or_simplify_allowed:
    responsive_unknowns:
  responsive_route_seed:
    route: same_tree_responsive_overrides | viewport_specific_variant_tree | hybrid_split | unresolved_requires_designer_input
    confidence: high | medium | low | unknown
    reason:
    advisory_only: true
  blockers:
  questions_for_designer:
```

Rules:

- Stage 7 must not build the viewport-specific mobile/tablet tree unless the selected architecture already authorized it.
- Stage 7 must not hide meaningful content on mobile/tablet unless Stage 6 explicitly allowed it.
- Stage 7 must not treat `responsive_start_packet_draft` as final responsive truth.
- Stage 7 must preserve the `responsive_structure_contract` even when the draft route seed is unresolved.

---

## 7. Stage 9 Patch — `/final-audit`

Stage 9 must audit whether the packet draft can be safely packaged.

Add this check to the `RESPONSIVE AUDIT` and `UNKNOWN / CONFIRMATION SURVIVAL AUDIT` scopes:

```yaml
responsive_start_packet_audit:
  packet_draft_present: yes | no | partial
  required_sources_present: yes | no | partial
  route_seed_visible: yes | no
  route_seed_used_as_score_booster: yes | no
  responsive_unknowns_preserved: yes | no | partial
  meaningful_content_hide_policy_preserved: yes | no | partial
  viewport_variant_authorization_state:
    status: authorized | not_authorized | unknown | not_applicable
    source_ref:
  finding_severity: blocker | high | medium | low | info
  repair_owner: /score-evidence | /build-tree | /implementation | /final-audit | /handoff-export
```

Rules:

- If the packet route seed is used to soften Stage 4 scoring, Stage 9 must fail and route repair to `/score-evidence` or `/score-audit`.
- If responsive unknowns disappear, Stage 9 must fail or flag according to severity.
- If a viewport-specific variant is packaged without authorization evidence, Stage 9 must mark at least `high` and normally block downstream responsive handoff.
- If all packet risks are visible and no blocker/high finding remains, Stage 9 may allow Stage 10 to package the packet.

---

## 8. Stage 10 Patch — `/handoff-export`

Stage 10 must package the final `EV4_RESPONSIVE_START_PACKET` when final audit allows handoff and responsive downstream work is requested, likely, or explicitly enabled.

Add this section to Format A after `RESPONSIVE CHECKLIST` and before `DYNAMIC DATA / INTERACTION CHECKLIST`:

```text
EV4 RESPONSIVE START PACKET
```

Add this field to `HANDOFF_PAYLOAD`:

```json
"responsive_start_packet": null
```

When present, `responsive_start_packet` must follow `contracts/EV4_RESPONSIVE_START_PACKET_CONTRACT.md`.

Rules:

- Stage 10 packages only the audited packet record.
- Stage 10 must not choose a new route if Stage 9 did not audit it.
- Stage 10 must not clean up responsive unknowns for readability.
- Stage 10 must not replace `unresolved_requires_designer_input` with a stronger route.
- Stage 10 must include packet limitations in `AUDIT FLAGS TO PRESERVE` and `UNRESOLVED UNKNOWNS AND USER CONFIRMATIONS`.
- If Stage 9 is blocked, Stage 10 may emit a partial/blocked packet only inside `HANDOFF BLOCKED REPORT`; it must not label it builder-ready or downstream-ready.

---

## 9. Official Elementor Capability Boundary

This patch relies on the following platform-level facts only as capability context:

- Elementor supports responsive editing across desktop, tablet, and mobile.
- Elementor supports responsive values / inherited responsive behavior for many controls.
- Elementor Containers support responsive layout controls such as direction/order patterns.
- Elementor supports hide/show behavior per device.

These facts prove platform capability only. They do not prove a specific candidate uses the feature correctly, and they do not validate runtime output.

---

## 10. Source-of-Truth Order for Responsive Start Packets

When producing `EV4_RESPONSIVE_START_PACKET`, use this order:

```text
1. Final_Audit_Payload blockers, flags, and unknowns
2. Build_Tree_Payload structure_tree and responsive_structure_contract
3. Recommendation_Payload selected candidate identity and restrictions
4. Score_Audit_Payload / Score_Evidence responsiveness caps and evidence labels
5. Stage 2 decomposition responsive risks and unknowns
6. User-provided explicit responsive/variant instruction
7. Official Elementor docs for platform capability only
8. Inference, capped and marked as inference
```

Downstream override rule:

```text
A future responsive designer mockup submitted to EV4 Responsive Architect is new downstream evidence. It may supersede this packet's route seed, but the downstream system must report the conflict and must not silently rewrite the original desktop architecture record.
```

---

## 11. Regression Cases

### Regression 001 — `variant-inflates-score`

Input: A candidate has weak same-tree mobile behavior but says a mobile-only duplicate can be created.

Expected: The same-tree `Responsiveness` score remains low or incomplete. If a designer-provided variant exists, emit route seed only. Do not raise the numeric score.

### Regression 002 — `unknown-mobile-cleanup`

Input: Stage 7 carries `responsive_unknowns`, but Stage 10 omits them from the packet.

Expected: Fail or blocked/partial handoff. Unknowns must survive.

### Regression 003 — `unjustified-hidden-mobile-section`

Input: A candidate hides the desktop section and creates a separate mobile section without explicit designer/user authorization.

Expected: Treat as duplicate/hidden section risk. Do not classify as legitimate `viewport_specific_variant_tree`.

### Regression 004 — `designer-variant-route`

Input: The user/designer explicitly provides a materially different responsive mockup and states the desktop section is desktop-only.

Expected: Preserve same-tree score boundaries and emit `viewport_specific_variant_tree` or `hybrid_split` route seed for downstream responsive architecture.

### Regression 005 — `packet-as-final-truth`

Input: Downstream responsive system receives the packet and no responsive mockup.

Expected: Downstream system may use the packet as a start point only; it must not claim final responsive design or build tree without responsive evidence.

---

## 12. Machine-Readable Patch Payload

```json
{
  "schema": "ev4-responsive-start-packet-stage-patch@1.0.0",
  "status": "confirmed_hardening_patch_v1.0.0",
  "stage_scope": ["/decompose", "/score-evidence", "/build-tree", "/final-audit", "/handoff-export"],
  "new_contract": "contracts/EV4_RESPONSIVE_START_PACKET_CONTRACT.md",
  "new_payload_schema": "ev4-responsive-start-packet@1.0.0",
  "patch_effects": {
    "stage_2": "adds optional responsive relationship hints without final routing",
    "stage_4": "adds route seed metadata while preserving strict same-tree scoring",
    "stage_7": "adds responsive start packet draft after responsive structure contract",
    "stage_9": "audits packet safety and score-boundary preservation",
    "stage_10": "packages audited EV4_RESPONSIVE_START_PACKET for downstream responsive work"
  },
  "non_regression_rule": "viewport-specific variant routing must not improve desktop same-tree Responsiveness scoring",
  "next_work_anchor": "EV4 Responsive Architect /responsive-start-packet-ingest"
}
```

---

## 13. Pass Criteria for This Patch

This patch is valid only if future runs:

- keep the active rubric strict;
- do not treat hidden/duplicate sections as quality improvements;
- preserve designer-provided viewport variants as downstream route seeds, not score boosters;
- emit `EV4_RESPONSIVE_START_PACKET` only when audited and visible;
- preserve responsive risks, unknowns, route confidence, and meaningful-content hide policy;
- keep live render/export/pixel validation claims blocked without matching evidence.
