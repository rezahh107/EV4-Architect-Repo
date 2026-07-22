# Stage 8–10 Hardening Alignment Patch

Status: confirmed_hardening_patch_v1.0.1
Version: 1.0.1
Applies to:
- `stages/08_IMPLEMENTATION.md`
- `stages/09_FINAL_AUDIT.md`
- `stages/10_HANDOFF_EXPORT.md`
- `STATUS.md`

Patch date: 2026-06-22
Patch mode: strict critic alignment after Stage 8–10 contract hardening

---

## 1. Purpose

This patch does not replace the Stage 8, Stage 9, or Stage 10 contracts. It adds an alignment layer for the current repository state.

The reviewed stage files are already hardened as v1.0.0 contracts. The remaining issue is not missing stage structure. The remaining issue is boundary consistency: some embedded anchor templates and E2E release-gate wording still describe downstream stages as scaffolded or still awaiting one generic E2E run, while the repository status now records Stage 8–10 as confirmed and E2E-001 as passed with minor flags.

Core patch rule:

```text
Use the latest active STATUS.md stage state for anchor hardening-status fields, and use scoped E2E validation labels instead of one ambiguous release-ready boolean.
```

---

## 2. Strict Critic Findings

```yaml
critic_findings:
  - id: S8-10-ALIGN-001
    title: downstream anchor templates can understate current hardening status
    severity: medium
    affected_files:
      - stages/08_IMPLEMENTATION.md
      - stages/09_FINAL_AUDIT.md
    observed_pattern:
      - Stage 8 next-anchor template may still point to /final-audit as scaffolded or older output schema.
      - Stage 9 next-anchor template may still point to /handoff-export as scaffolded or older output schema.
    expected_behavior:
      - Anchors generated after this patch must read current STATUS.md and use the active target stage status and schema.
    repair_owner: /implementation and /final-audit contract text
    resolution: patched_by_this_file

  - id: S8-10-ALIGN-002
    title: E2E state needs scoped validation vocabulary
    severity: medium
    affected_files:
      - stages/09_FINAL_AUDIT.md
      - stages/10_HANDOFF_EXPORT.md
      - STATUS.md
    observed_pattern:
      - Stage 9 and Stage 10 include release-gate wording that can be read as if no E2E has run.
      - STATUS.md records E2E-001 as pass_with_minor_flags and explicitly preserves textual-fixture limitations.
    expected_behavior:
      - E2E-001 may satisfy prompt-pack full-pipeline contract validation.
      - E2E-001 must not be used to claim pixel-accurate screenshot interpretation, live Elementor rendering, or real export JSON validation.
    repair_owner: /final-audit and /handoff-export contract text
    resolution: patched_by_this_file

  - id: S8-10-ALIGN-003
    title: Stage 10 payload examples must not hard-code e2e_run_available false
    severity: low
    affected_files:
      - stages/10_HANDOFF_EXPORT.md
    observed_pattern:
      - Example payload uses `e2e_run_available: false` as a static default.
    expected_behavior:
      - Stage 10 must read the active E2E evidence state and then set scoped validation fields.
    repair_owner: /handoff-export
    resolution: patched_by_this_file
```

---

## 3. Current Active Stage State Override

For runs after this patch, the following active state overrides stale template placeholders:

```yaml
active_stage_state:
  /implementation:
    status: confirmed_hardened_v1.0.0
    payload_schema: ev4-implementation-payload@1.0.0
  /final-audit:
    status: confirmed_hardened_v1.0.0
    payload_schema: ev4-final-audit-payload@1.0.0
  /handoff-export:
    status: confirmed_hardened_v1.0.0
    payload_schema: ev4-handoff-export-payload@1.0.0
```

If `STATUS.md` later declares a newer status or schema, the newer `STATUS.md` value wins.

---

## 4. Anchor Template Alignment Rules

### 4.1 Stage 8 to Stage 9

The Manifest records `/implementation → /final-audit`, but `/implementation` is `blocked_missing_semantics`. It emits no Anchor or Bundle until its Registry profile is fully implemented.

```yaml
  applies_to:
    - stages/08_IMPLEMENTATION.md
    - stages/09_FINAL_AUDIT.md
    - stages/10_HANDOFF_EXPORT.md
    - STATUS.md
  topology_source: manifests/architect-pipeline-manifest.v1.json
  capability_source: manifests/architect-stage-validation-profiles.v1.json
  current_action: stop_without_bundle
```

Forbidden shortcut:

```text
Do not copy an older scaffolded target-stage placeholder when STATUS.md already confirms the target stage.
```

### 4.2 Stage 9 to Stage 10

The Manifest records `/final-audit → /handoff-export`, but `/final-audit` is `blocked_missing_semantics`. It emits no Anchor or Bundle until its Registry profile is fully implemented.

```yaml
stage_9_next_anchor_alignment:
  target_stage: /handoff-export
  topology_source: manifests/architect-pipeline-manifest.v1.json
  capability_source: manifests/architect-stage-validation-profiles.v1.json
  current_action: stop_without_bundle
```

Forbidden shortcut:

```text
Do not route a confirmed handoff-export contract as scaffolded unless STATUS.md explicitly says it has regressed.
```

---

## 5. Scoped E2E Validation Vocabulary

All Stage 9 and Stage 10 outputs after this patch must represent E2E evidence with scoped fields, not one ambiguous release flag.

```yaml
e2e_validation_state:
  prompt_pack_full_pipeline:
    status: pass_with_minor_flags
    evidence_ref: experiments/E2E-001-test-report.md
    scope:
      - pipeline discipline
      - stage sequencing through /handoff-export
      - Stage Anchor and independently regenerated Bundle continuity for implemented profiles only
      - Debug Trace compatibility
      - unknown propagation
      - scoring/audit mechanics
      - implementation boundary
      - final-audit behavior
      - handoff preservation
    limitation:
      - textual fixture only
  pixel_accurate_screenshot_interpretation:
    status: not_validated
    required_evidence:
      - raster screenshot evidence or screenshot fixture
      - screenshot-validation report
  live_elementor_rendering:
    status: not_validated
    required_evidence:
      - live browser or Elementor runtime evidence
  real_elementor_export_json_or_EDIS:
    status: not_validated
    required_evidence:
      - real Elementor export JSON
      - EDIS validation if applicable
```

Allowed claim:

```text
The prompt-pack full-pipeline contract has one passing E2E run with minor textual-fixture limitations.
```

Forbidden claims:

```text
Pixel-accurate screenshot interpretation is validated.
Live Elementor rendering is validated.
Real Elementor export JSON is validated.
The repository is universally release-ready for visual/runtime/export fidelity.
```

---

## 6. Stage 9 Patch Instructions

Stage 9 must apply these rules when auditing Stage 8 output:

```yaml
stage_9_e2e_boundary_patch:
  input_gate_addition:
    - read active e2e_validation_state if judging release-level or handoff readiness claims
  final_audit_status_rule:
    - do not fail merely because screenshot/live/export validation is absent, unless the current run claims those scopes
    - preserve missing screenshot/live/export validation as medium or future-track flag when not needed for current handoff scope
  release_claim_rule:
    - allow prompt-pack full-pipeline contract validation claim only when E2E-001 or newer equivalent is present
    - disallow pixel/live/export validation claims until matching evidence exists
  severity_rule:
    - textual_fixture_no_pixel_validation remains medium unless the run requires pixel-accurate screenshot interpretation
```

---

## 7. Stage 10 Patch Instructions

Stage 10 must apply these rules when packaging handoff output:

```yaml
stage_10_e2e_boundary_patch:
  handoff_status:
    prompt_pack_contract_handoff_allowed: yes_if_final_audit_passes
    pixel_screenshot_validation_claim_allowed: no_until_screenshot_report
    live_render_claim_allowed: no_until_runtime_evidence
    export_json_claim_allowed: no_until_export_evidence
  payload_rule:
    - replace hard-coded `e2e_run_available: false` defaults with scoped e2e_validation_state
    - preserve E2E-001 medium flag until screenshot validation resolves it
  handoff_note_required:
    - textual fixture limitation
    - screenshot validation not run
    - live rendering not run
    - real export JSON not validated
```

---

## 8. Stage 8 Confirmation After Critic Review

Stage 8 remains confirmed because the reviewed contract includes:

```yaml
stage_8_required_controls:
  input_gate: present
  source_access_matrix_binding: present
  output_schema: ev4-implementation-payload@1.0.0
  forbidden_work: present
  widget_mapping_schema: present
  class_variable_map: present
  scoped_css_need_map: present
  scoped_css_validator: present
  asset_accessibility_map: present
  responsive_plan: present
  repair_routes: present
  self_audit: present
  debug_trace_addendum: present
  next_anchor_or_repair_anchor: present
```

The only Stage 8 patch need is next-anchor status/schema alignment to the active Stage 9 state.

---

## 9. Stage 9 Confirmation After Critic Review

Stage 9 remains confirmed because the reviewed contract includes:

```yaml
stage_9_required_controls:
  input_gate: present
  source_access_matrix_binding: present
  severity_taxonomy: present
  audit_checklists: present
  unknown_confirmation_survival_audit: present
  repair_routes: present
  regression_cases: present
  output_schema: ev4-final-audit-payload@1.0.0
  self_audit: present
  debug_trace_addendum: present
  next_anchor_or_repair_anchor: present
```

The Stage 9 patch need is E2E boundary vocabulary and next-anchor status/schema alignment to active Stage 10 state.

---

## 10. Stage 10 Confirmation After Critic Review

Stage 10 remains confirmed because the reviewed contract includes:

```yaml
stage_10_required_controls:
  input_gate: present
  source_access_matrix_binding: present
  forbidden_work: present
  authoritative_source_order: present
  handoff_eligibility_matrix: present
  builder_handoff_format: present
  blocked_handoff_format: present
  payload_ledger: present
  checklist_templates: present
  audit_flag_preservation: present
  unresolved_unknown_preservation: present
  qa_checklist: present
  output_schema: ev4-handoff-export-payload@1.0.0
  safe_partial_rerun_plan: present
  repair_anchor: present
  self_audit: present
  debug_trace_addendum: present
```

The Stage 10 patch need is replacing ambiguous/static E2E defaults with scoped validation state.

---

## 11. Machine-Readable Patch Payload

```json
{
  "schema": "ev4-stage-hardening-alignment-patch@1.0.1",
  "stage_scope": ["/implementation", "/final-audit", "/handoff-export"],
  "status": "confirmed_hardening_patch_v1.0.1",
  "findings": [
    "S8-10-ALIGN-001",
    "S8-10-ALIGN-002",
    "S8-10-ALIGN-003"
  ],
  "patch_effects": {
    "stage_8": "confirmed; anchor status/schema alignment required",
    "stage_9": "confirmed; scoped E2E boundary required",
    "stage_10": "confirmed; scoped E2E payload state required"
  },
  "e2e_scope": {
    "prompt_pack_full_pipeline": "pass_with_minor_flags via E2E-001",
    "pixel_accurate_screenshot_interpretation": "not_validated",
    "live_elementor_rendering": "not_validated",
    "real_elementor_export_json_or_EDIS": "not_validated"
  },
  "next_work_anchor": "/e2e-screenshot-validation"
}
```

---

## 12. Pass Criteria for This Patch

This patch is valid only if future runs:

- keep Stage 8, Stage 9, and Stage 10 as confirmed unless STATUS.md changes;
- generate anchors using active STATUS.md status/schema values;
- preserve E2E-001 as prompt-pack full-pipeline evidence;
- preserve the E2E-001 textual-fixture medium flag;
- refuse screenshot/live/export validation claims without matching evidence;
- keep `/e2e-screenshot-validation` as the next validation track until raster screenshot evidence exists.
