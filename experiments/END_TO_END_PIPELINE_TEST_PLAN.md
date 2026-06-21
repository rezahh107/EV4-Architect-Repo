# End-to-End Pipeline Test Plan

Status: confirmed_hardened_v1.0.0
Version: 1.0.0
Plan schema: ev4-e2e-test-plan@1.0.0
Report schema: ev4-e2e-test-report@1.0.0
Applies to: validation before release-ready confirmation

---

## Release Boundary

This file confirms the E2E test plan contract. It does not confirm that the EV4 prompt pack has passed a real E2E run.

Core rule:

```text
Do not mark the prompt pack release-ready until one realistic section completes a traceable E2E run and produces a passing ev4-e2e-test-report@1.0.0.
```

---

## Source / Contract Inputs Read

The E2E plan must be executed against these active repository contracts:

```text
- STATUS.md
- contracts/STAGE_ANCHOR_CONTRACT.md
- contracts/PARTIAL_RERUN_CONTRACT.md
- diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
- references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
- knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
- stages/08_IMPLEMENTATION.md
- stages/09_FINAL_AUDIT.md
- stages/10_HANDOFF_EXPORT.md
```

The first prepared fixture is:

```text
experiments/E2E-001-smart-home-connector-fixture.md
```

---

## Strict Critic Findings Applied

The previous v0.1.0 test plan was useful but insufficient for release validation.

Confirmed weaknesses:

```text
- scope stopped at /build-tree and treated /implementation → /handoff-export as optional;
- no versioned report schema;
- no fixture contract;
- no explicit source-access checks per stage;
- no pass/fail taxonomy;
- no per-stage trace requirements;
- no blocker/high defect behavior;
- no negative-control or regression probes;
- no repair-anchor requirements;
- no Stage 10 audit-flag preservation check;
- no release-ready boundary strong enough to prevent false confidence.
```

This v1.0.0 plan patches those gaps.

---

## Required Test Scope

The first release-blocking E2E validation must run the full hardened pipeline:

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

A partial run ending at `/build-tree` is allowed only as a diagnostic preflight. It cannot remove the release blocker.

---

## Required Test Input

Use a realistic section screenshot or controlled realistic mockup with all of these properties:

```text
- at least one repeated component group;
- at least one meaningful image, dashboard, illustration, or visual core;
- at least one decorative layer;
- at least one responsive risk;
- at least one unknown that must survive through downstream stages;
- enough semantic content to test editability vs flattened visual tradeoffs;
- enough visual layering to test scoped CSS and absolute-position constraints.
```

For the first run, use:

```text
test_id: E2E-001
fixture: experiments/E2E-001-smart-home-connector-fixture.md
fixture_type: realistic_mockup_description
```

Limitation:

```text
E2E-001 is a realistic textual mockup, not a raster screenshot. It can validate contract propagation, stage boundaries, unknown survival, repair routing, and handoff discipline. It cannot validate pixel-accurate screenshot interpretation.
```

---

## Stage Source Access Matrix Check

The E2E runner must verify that every stage follows the active Source Access Matrix.

| Stage | Required source behavior |
|---|---|
| `/intake` | Use fixture and project defaults. Do not research unless a blocking platform capability question exists. |
| `/decompose` | Use only visible/provided fixture facts. Do not use TUYA, Elementor docs, or RAG to invent visual groups. |
| `/architectures` | May use fixture output, project defaults, TUYA conceptual model, and official docs for feasibility. Must not recommend. |
| `/score-evidence` | Score from rubric + Stage 2/3 evidence only. TUYA/RAG cannot boost scores. |
| `/score-audit` | Audit scoring mechanics and evidence use. Do not create a new architecture. |
| `/recommend` | Recommend only from audited eligible candidates. Do not use new RAG signals or hidden preferences. |
| `/build-tree` | Build only from selected recommendation and approved constraints. No re-architecture. |
| `/implementation` | Map the approved tree into implementation details using official docs/export evidence where available. Do not invent exact values. |
| `/final-audit` | Audit preservation, capability claims, CSS scope, editability, responsive risk, accessibility, and unknown survival. No new implementation. |
| `/handoff-export` | Package final audited outputs only. No new decisions, CSS, widgets, or architecture. |

---

## Stage Anchor Requirements

Before every stage after `/intake`, the E2E runner must validate a `STAGE ANCHOR` with schema:

```text
ev4-stage-anchor@1.1.0
```

Minimum required anchor fields:

```text
- source_stage
- target_stage
- target_stage_hardening_status
- project_status_version
- payload_schema_in
- payload_schema_out
- critical_unknowns
- confidence_delta
- blocking_items
- gate_results
- audit_flags
- required_user_confirmations
- partial_rerun_state
- allowed_work
- forbidden_work
- stop_conditions
- debug_trace_required
```

If an anchor is missing, outdated, schema-mismatched, or inconsistent with the previous payload, the E2E report must mark:

```text
e2e_status: fail
first_failure_stage: stage_before_invalid_anchor
failure_type: bad_handoff
repair_target: owning previous stage
```

---

## Debug Trace Requirements

Every stage in the E2E run must emit an external trace block compatible with:

```text
ev4-debug-trace@1.0.0
```

The E2E validator must check at least:

```text
- inputs_received
- inputs_missing
- input_payload_schemas
- decision_log
- evidence_map
- unknown_register
- rule_application_log
- failure_symptom_index
- repair_route
- handoff_payload_schema
```

The trace must externalize auditable facts only. It must not expose or request hidden chain-of-thought.

---

## Measurement Matrix

The E2E report must measure:

| Area | Required check |
|---|---|
| Anchor quality | All required anchor fields present and consistent. |
| Drift control | Stage 2 unknowns survive into Stage 4/5/6/7/8/9/10 when unresolved. |
| Source discipline | No RAG/TUYA leakage into Stage 2, Stage 4, or Stage 6. |
| Scoring correctness | Unknowns are not converted to numeric evidence; arithmetic and N/A logic are auditable. |
| Score audit effectiveness | Stage 5 catches scoring, gate, contradiction, recommendation, or arithmetic defects. |
| Recommendation discipline | Stage 6 does not force ties or invent user priorities. |
| Build-tree usability | Stage 7 output is Structure Panel-readable, editable, wrapper-budget aware, and overlay-contained. |
| Implementation discipline | Stage 8 produces settings/schema maps without inventing exact values. |
| Final audit rigor | Stage 9 blocks global CSS leaks, editability loss, hidden content, architecture drift, and unresolved blocker/high issues. |
| Handoff preservation | Stage 10 preserves every blocker/high/medium/low/info flag and does not introduce new decisions. |
| Repair loop cost | First failure stage, repair target, invalidated downstream stages, and rerun cost are explicit. |

---

## Negative-Control Probes

The E2E runner must actively look for these failure symptoms:

```text
NC-001: Stage 2 uses Elementor docs or TUYA concepts to infer invisible visual groups.
NC-002: Stage 3 includes recommendation language before scoring/audit.
NC-003: Stage 4 turns unknown breakpoints, unknown z-index, or unknown spacing into numeric evidence.
NC-004: Stage 5 misses an arithmetic/gate/evidence-label inconsistency.
NC-005: Stage 6 forces a winner when audited candidates are tied or require user confirmation.
NC-006: Stage 7 flattens meaningful content into an image without editability penalty.
NC-007: Stage 8 invents exact Elementor settings, CSS values, breakpoints, z-index, asset filenames, or animation timing.
NC-008: Stage 9 passes implementation despite global CSS leakage, hidden meaningful content, or architecture drift.
NC-009: Stage 10 softens a failed audit into a builder-friendly handoff.
NC-010: Any stage drops unresolved unknowns without named resolving evidence.
```

If any negative-control probe is triggered without a repair route, the E2E run fails.

---

## E2E Status Taxonomy

```text
e2e_status: pass
```

Allowed only when the full pipeline reaches `/handoff-export`, no blocker/high issue remains, all required anchors and payloads are valid, all unresolved unknowns are preserved, and the final handoff does not introduce new decisions.

```text
e2e_status: pass_with_minor_flags
```

Allowed only when no blocker/high issue remains, medium/low/info flags are preserved in Stage 10, and the report names why they are not release blockers.

```text
e2e_status: fail_repairable
```

Use when a stage fails but has a clear repair target and partial rerun route.

```text
e2e_status: fail_blocked
```

Use when required input, payload, fixture, anchor, or stage contract evidence is missing, or when no safe repair route can be named.

---

## Report Schema

Every E2E run must produce:

```yaml
E2E_TEST_REPORT:
  schema: ev4-e2e-test-report@1.0.0
  test_id: null
  fixture: null
  fixture_type: screenshot | realistic_mockup_description | export_evidence | mixed
  project_status_version_at_start: null
  e2e_status: pass | pass_with_minor_flags | fail_repairable | fail_blocked
  stages_completed: []
  first_failure_stage: null
  failure_type: null
  release_blocker_removed: yes | no
  release_blocker_reason: null
  source_access_violations: []
  anchor_validation:
    anchors_checked: []
    anchor_failures: []
  payload_validation:
    payloads_checked: []
    payload_schema_failures: []
  unknown_propagation:
    introduced_unknowns: []
    preserved_unknowns: []
    resolved_unknowns_with_evidence: []
    dropped_unknowns_without_evidence: []
  scoring_audit:
    arithmetic_result: pass | fail | n/a
    unknown_to_number_result: pass | fail | n/a
    gate_result: pass | fail | n/a
    contradiction_handling_result: pass | fail | n/a
  recommendation_audit:
    eligible_candidates_only: yes | no
    tie_protocol_followed: yes | no | n/a
    hidden_preference_detected: yes | no
  build_tree_audit:
    structure_panel_readable: yes | no
    editability_preserved: yes | no
    wrapper_budget_result: pass | fail | n/a
    overlay_containment_result: pass | fail | n/a
  implementation_audit:
    settings_schema_valid: yes | no | n/a
    scoped_css_valid: yes | no | n/a
    exact_values_invented: yes | no
    responsive_risks_preserved: yes | no
  final_audit_result:
    final_audit_status: pass | pass_with_minor_flags | fail | blocked | n/a
    blocker_findings: []
    high_findings: []
    medium_findings: []
    low_findings: []
    info_findings: []
  handoff_export_result:
    mode: final_builder_handoff | handoff_blocked_report | n/a
    audit_flags_preserved: yes | no | n/a
    new_decisions_introduced: yes | no | n/a
  repair_routes:
    - issue_id: null
      owner_stage: null
      earliest_safe_rerun_stage: null
      invalidated_downstream: []
      minimal_repair: null
      forbidden_shortcut: null
  required_contract_changes: []
  next_work_anchor: null
```

---

## Repair Routing Rules

If the E2E run fails, the report must produce a repair route instead of vague advice.

| Failure | Owner stage | Earliest safe rerun |
|---|---|---|
| Fixture ambiguous or insufficient | `/intake` or test fixture | `/intake` |
| Bad visual decomposition | `/decompose` | `/decompose` |
| Candidate missing or recommendation leak | `/architectures` | `/architectures` |
| Unknown converted into score | `/score-evidence` | `/score-evidence` |
| Audit misses score defect | `/score-audit` | `/score-audit` |
| Forced recommendation/tie break | `/recommend` | `/recommend` |
| Uneditable or unreadable tree | `/build-tree` | `/build-tree` |
| Invented settings/CSS/exact values | `/implementation` | `/implementation` |
| Final audit fails to block blocker/high | `/final-audit` | `/final-audit` |
| Handoff drops flags or adds decisions | `/handoff-export` | `/handoff-export` |
| Invalid anchor or missing payload | Producing previous stage | Producing previous stage |

The report must also list downstream payloads invalidated by the repair.

---

## Pass Criteria

The first E2E run passes only if:

```text
- full stage sequence completes through /handoff-export;
- no stage starts without a valid ev4-stage-anchor@1.1.0 where required;
- no required payload schema is missing;
- unknowns do not disappear silently;
- Stage 4 does not convert ? / unknown / N/A into unsupported numeric score;
- Stage 5 detects scoring, gate, arithmetic, and evidence-label issues;
- Stage 6 does not force a recommendation when tie or user input is required;
- Stage 7 keeps meaningful content editable and overlays contained;
- Stage 8 does not invent exact unsupported implementation settings;
- Stage 9 blocks unresolved blocker/high defects;
- Stage 10 preserves audit flags and does not add new implementation decisions;
- failures produce minimal repair routes instead of broad advice.
```

---

## Release Blocker Rule

A passing E2E report may recommend removing the release blocker only if:

```text
release_blocker_removed: yes
```

and the report proves:

```text
- e2e_status is pass or pass_with_minor_flags;
- full pipeline reached /handoff-export;
- no blocker/high finding remains;
- Stage 10 did not soften or hide flags;
- every medium flag is explicitly preserved and non-release-blocking;
- every unresolved unknown is preserved into final handoff;
- no required source, anchor, or payload is missing.
```

If any condition is not met, the release blocker remains.

---

## E2E Plan Self-Audit

```text
input_gate_defined: yes
full_pipeline_scope_defined: yes
fixture_contract_defined: yes
source_access_matrix_checked: yes
stage_anchor_schema_checked: yes
debug_trace_schema_checked: yes
report_schema_versioned: yes
negative_controls_defined: yes
repair_routes_defined: yes
release_boundary_defined: yes
stage_10_flag_preservation_checked: yes
```

---

## NEXT WORK ANCHOR — Run E2E-001

```text
NEXT WORK ANCHOR — /e2e-test
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /e2e-test-plan
target_stage: /e2e-test
target_stage_hardening_status: confirmed
project_status_version: 0.11.0
payload_schema_in:
  - ev4-e2e-test-plan@1.0.0
  - ev4-e2e-fixture@1.0.0
payload_schema_out:
  - ev4-e2e-test-report@1.0.0

Carry-forward facts:
- key_decisions:
  - E2E test plan contract is confirmed_hardened_v1.0.0.
  - First fixture is E2E-001 smart-home connector hero.
  - E2E-001 is a realistic textual mockup, not a raster screenshot.
- selected_or_active_candidates:
  - Full pipeline validation from /intake through /handoff-export.
- rejected_or_blocked_candidates:
  - Partial /build-tree-only run cannot remove release blocker.
- critical_unknowns:
  - Pixel-accurate screenshot interpretation is not testable with textual fixture alone.
  - Real Elementor export evidence is not available in E2E-001.
- confidence_delta:
  - item: E2E test harness readiness
    previous_confidence: unknown
    current_confidence: confirmed
    direction: increased
    reason: v1.0.0 test plan now defines fixture, report schema, negative controls, repair routes, and release boundary.
    downstream_impact: E2E-001 can run without asking for additional planning input.
- blocking_items:
  - Prompt pack is not release-ready until one E2E report passes.
- gate_results:
  - E2E plan hardening gate passed.
  - E2E execution gate not yet run.
- audit_flags:
  - Textual fixture cannot validate pixel-accurate visual interpretation.
- tie_or_ambiguity_flags:
  - If E2E recommendation reaches a tie, Stage 6 must preserve tie protocol.
- required_user_confirmations:
  - None for E2E-001 test execution.
- repair_routes:
  - Use report repair routing table to identify earliest safe rerun stage.

Partial rerun state:
- reusable_until: E2E plan remains reusable unless fixture, stage schema, anchor schema, debug trace schema, or source matrix changes.
- invalidation_triggers:
  - fixture changed
  - Stage 8/9/10 schema changed
  - Stage Anchor Contract changed
  - Debug Trace Contract changed
  - Source Access Matrix changed
- earliest_safe_rerun_stage: /e2e-test-plan if the plan changes; /intake if only fixture content changes before first run.
- downstream_payloads_dependent_on_this_stage:
  - ev4-e2e-test-report@1.0.0

Stage input package:
- required_inputs_present:
  - experiments/END_TO_END_PIPELINE_TEST_PLAN.md
  - experiments/E2E-001-smart-home-connector-fixture.md
  - STATUS.md
  - active stage/contracts listed in STATUS.md
- required_inputs_missing:
  - None for textual-fixture E2E execution
- files_or_sections_to_reference:
  - experiments/END_TO_END_PIPELINE_TEST_PLAN.md
  - experiments/E2E-001-smart-home-connector-fixture.md
  - contracts/STAGE_ANCHOR_CONTRACT.md
  - diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
  - references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md

Stage boundary:
- allowed_work:
  - Run E2E-001 through every stage and produce ev4-e2e-test-report@1.0.0.
  - Record first failure, repair route, invalidated downstream, and release-blocker state.
- forbidden_work:
  - Do not mark release-ready unless the E2E report passes all release-blocker conditions.
  - Do not skip anchors, payloads, score audit, final audit, or handoff preservation checks.
  - Do not invent screenshot-only facts beyond the textual fixture.
- stop_conditions:
  - Missing required stage/contract file.
  - Invalid or absent E2E fixture.
  - Any blocker/high defect without repair route.
  - E2E report cannot be produced in schema ev4-e2e-test-report@1.0.0.

Debug trace:
- debug_trace_required: yes
- previous_debug_trace_id: None
- expected_debug_trace_schema: ev4-debug-trace@1.0.0
```
