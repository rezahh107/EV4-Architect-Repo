# STATUS — Elementor V4 Architect Prompt Pack

Version: 0.15.0
Status: tuya_concept_reference_hardened
Last confirmed stage: TUYA internal concept reference contract hardening
Current next step: Prepare or run `/e2e-screenshot-validation` when raster screenshot evidence is available; do not remove the E2E-001 textual-fixture limitation until screenshot-based validation passes.
Language: Persian reports, English technical labels allowed
Last automation update: 2026-06-22

---

## Pipeline

1. /intake
2. /research
3. /decompose
4. /architectures
5. /score-evidence
6. /score-audit
7. /recommend
8. /build-tree
9. /implementation
10. /final-audit
11. /handoff-export
12. /e2e-test
13. /e2e-screenshot-validation

---

## Stage Status

| Stage / Contract | Status | Notes |
|---|---|---|
| /intake | confirmed | Lightweight default-based intake |
| /research | confirmed_hardened_v1.0.0 | Stage 2 research contract with input gate, source access policy, source pinning, retrieval fact ledger, `ev4-research-payload@1.0.0`, downstream permission map, repair routes, self-audit, debug trace, and anchor handoff |
| /decompose | confirmed_with_example_bank | Controlled Visual Role Decomposition with example bank; must not use research/RAG/TUYA/docs to invent visual groups |
| /decomposition-example-bank | active_enhanced | Pattern-based examples plus authoring standard |
| /architectures | confirmed_hardened_v1.1.0 | Coverage matrix, unknown propagation, recommendation ban, dynamic guardrails |
| /score-evidence | confirmed_hardened_v1.3.0_patch | Uses rubric 1.3 and Stage 4 v1.3 hardening patch |
| /score-audit | confirmed_hardened_v1.2.0_patch | Adds Stage 5 self-audit, hidden recommendation guard, tie handoff, responsive cap reference binding |
| /scoring-calibration-bank | active | examples/scoring calibration cases added |
| /recommend | confirmed_hardened_v1.1.0_patch | Recommendation matrix, provenance ledger, tie handling, build-tree readiness gate, debug record |
| /stage-anchor-contract | active_v1.1.0 | Adds confidence_delta, target_stage_hardening_status, and partial_rerun_state |
| /partial-rerun-contract | active_v1.0.0 | Defines safe partial reruns and invalidation rules |
| /debug-trace-contract | active_v1.0.0 | External trace contract for pipeline debugging |
| /build-tree | confirmed_hardened_v1.0.0 | Naming convention, Structure Panel tree schema, wrapper budget, widget constraints, responsive contract |
| /implementation | confirmed_hardened_v1.0.0 | Stage 8 hardened with input gate, payload schema, source ledger, settings schema, widget map, class/variable map, scoped CSS validator, asset/accessibility map, responsive examples, repair routes, self-audit, debug trace, and anchor handoff |
| /final-audit | confirmed_hardened_v1.0.0 | Stage 9 hardened with input gate, Source Access Matrix binding, severity taxonomy, audit checklists, repair routes, regression cases, Final_Audit_Payload schema, self-audit, debug trace, and anchor handoff |
| /handoff-export | confirmed_hardened_v1.0.0 | Stage 10 hardened with input gate, Source Access Matrix binding, handoff eligibility matrix, blocked handoff report, payload ledger, audit-flag preservation, Handoff_Payload schema, repair anchor, self-audit, debug trace, and E2E release boundary |
| /elementor-knowledge-base-strategy | active_v1.0.0 | Hardened into `ev4-rag-strategy-contract@1.0.0`; owns current Stage Source Access Matrix, `/research` source-pinning ownership, source classes, retrieved fact schema, downstream permissions, freshness policy, EDIS boundary, conflict lifecycle, leakage probes, repair routes, self-audit, debug trace, and TUYA handoff |
| /tuya-concept-reference | active_v1.0.0 | Hardened into `ev4-tuya-concept-reference@1.0.0`; now explicitly `source_type: internal_concept_reference` and `fact_class: project_conceptual_model`, with TUYA concept fact schema, downstream permission matrix, leakage probes, repair routes, self-audit, debug trace addendum, and next-work anchor |
| /e2e-test-plan | confirmed_hardened_v1.0.0 | Defines full-pipeline E2E scope, fixture contract, source-access checks, anchor validation, debug trace validation, negative controls, report schema, repair routing, and release-boundary rules |
| /e2e-test | pass_with_minor_flags | E2E-001 completed through /handoff-export and produced `ev4-e2e-test-report@1.0.0`; textual fixture limitation remains as medium non-blocking flag |
| /e2e-screenshot-validation | not_run | Requires raster screenshot evidence or a screenshot fixture before pixel-accurate interpretation can be validated |

---

## Active Hardening / Contract Files

- 02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md
- contracts/STAGE_ANCHOR_CONTRACT.md
- contracts/PARTIAL_RERUN_CONTRACT.md
- contracts/BUILD_TREE_NAMING_AND_STRUCTURE_CONTRACT.md
- diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
- references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
- knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
- experiments/END_TO_END_PIPELINE_TEST_PLAN.md
- experiments/E2E-001-smart-home-connector-fixture.md
- experiments/E2E-001-test-report.md
- stages/02_RESEARCH.md
- stages/04_SCORE_EVIDENCE_v1.3_HARDENING_PATCH.md
- stages/05_SCORE_AUDIT_v1.1_HARDENING_PATCH.md
- stages/05_SCORE_AUDIT_v1.2_HARDENING_PATCH.md
- stages/06_RECOMMEND.md
- stages/06_RECOMMEND_v1.1_HARDENING_PATCH.md
- stages/07_BUILD_TREE.md
- stages/08_IMPLEMENTATION.md
- stages/09_FINAL_AUDIT.md
- stages/10_HANDOFF_EXPORT.md
- examples/scoring/README.md
- examples/scoring/SCORING-CAL-001-contradicted-evidence.md
- examples/scoring/SCORING-CAL-002-absent-vs-contradicted.md
- examples/scoring/SCORING-CAL-003-arithmetic-needs-audit.md
- examples/scoring/SCORING-CAL-004-overlay-na.md

---

## Hardened Stage / Validation / Strategy Files

- stages/02_RESEARCH.md
- references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
- knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
- stages/08_IMPLEMENTATION.md
- stages/09_FINAL_AUDIT.md
- stages/10_HANDOFF_EXPORT.md
- experiments/END_TO_END_PIPELINE_TEST_PLAN.md
- experiments/E2E-001-test-report.md

---

## Scaffolded / Draft / Validation Work Remaining

- `/e2e-screenshot-validation` is not run and cannot run without raster screenshot evidence or a screenshot fixture.
- E2E-001 used a realistic textual mockup, not a raster screenshot.
- Pixel-accurate screenshot interpretation remains unvalidated by E2E-001.
- Real Elementor export JSON / EDIS validation remains future work.
- Live Elementor/browser rendering remains future work.

---

## TUYA Concept Reference Contract Result

```yaml
TUYA_CONCEPT_REFERENCE:
  file: knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
  status: active_v1.0.0
  version: 1.0.0
  reference_schema: ev4-tuya-concept-reference@1.0.0
  source_type: internal_concept_reference
  fact_class: project_conceptual_model
  aligned_with:
    - ev4-rag-strategy-contract@1.0.0
    - ev4-research-payload@1.0.0
    - ev4-stage-anchor@1.1.0
    - ev4-partial-rerun@1.0.0
    - ev4-debug-trace@1.0.0
  confirmed_capabilities:
    - input authorization gate
    - corrected source classification
    - TUYA concept fact schema
    - downstream permission matrix
    - provisional / unknown / contradicted lifecycle
    - stage-specific use rules
    - forbidden leakage probes
    - repair routes
    - TUYA_CONCEPT_REFERENCE_PAYLOAD
    - self-audit checklist
    - EV4_DEBUG_TRACE addendum
    - NEXT WORK ANCHOR to /e2e-screenshot-validation
```

Strict boundary:

```text
TUYA may guide vocabulary, thinking order, normal-flow discipline, relative visual stage logic, responsive caution, design-system mindset, and DOM/audit checklisting.
TUYA must not prove platform capability, infer screenshot content, raise scores, break recommendation ties, invent exact settings, override official docs/export evidence, soften final-audit findings, or clean up handoff risks.
```

---

## RAG Strategy Contract Result

```yaml
RAG_STRATEGY_CONTRACT:
  file: references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
  status: active_v1.0.0
  version: 1.0.0
  strategy_schema: ev4-rag-strategy-contract@1.0.0
  aligned_with:
    - stages/02_RESEARCH.md
    - ev4-research-payload@1.0.0
    - contracts/STAGE_ANCHOR_CONTRACT.md
    - contracts/PARTIAL_RERUN_CONTRACT.md
    - diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
    - knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
```

Strict boundary:

```text
RAG may ground platform capability claims.
RAG must not infer screenshot content, select architecture, improve scores, break ties, soften final-audit defects, or clean up handoff risks.
```

Current stage-source correction:

```text
/research is Stage 2 and owns source pinning.
/decompose is Stage 3 and must use only visible/provided evidence for visual grouping.
```

---

## Research Contract Result

```yaml
RESEARCH_CONTRACT:
  file: stages/02_RESEARCH.md
  status: confirmed_hardened_v1.0.0
  stage_version: 1.0.0
  payload_schema: ev4-research-payload@1.0.0
```

Strict boundary:

```text
/research may prove or disprove platform capability.
/research must not decide what the current screenshot visually contains.
/research must not score, recommend, build, implement, or audit the section.
```

---

## E2E-001 Result

```yaml
E2E_TEST_REPORT:
  schema: ev4-e2e-test-report@1.0.0
  test_id: E2E-001
  fixture: experiments/E2E-001-smart-home-connector-fixture.md
  fixture_type: realistic_mockup_description
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
  release_blocker_removed: yes
  release_blocker_scope: prompt-pack full-pipeline E2E contract
  source_access_violations: []
  blocker_findings: []
  high_findings: []
  medium_findings:
    - E2E001-MED-001: textual fixture cannot validate pixel-accurate screenshot interpretation or exact visual matching
```

Release boundary interpretation:

```text
The previous release blocker requiring one passing E2E test is removed for the prompt-pack full-pipeline contract because E2E-001 reached /handoff-export, preserved anchors/payloads/unknowns/flags, and left no blocker/high finding.

This does not claim pixel-accurate screenshot interpretation, live Elementor rendering, or real export JSON validation. Those remain future validation tracks.
```

---

## Stage Anchor v1.1 Notes

A Stage Anchor is required before starting each stage after `/intake`.

Required v1.1 fields include:

- `target_stage_hardening_status`
- `confidence_delta`
- `partial_rerun_state`

The anchor is an external structured handoff, not hidden reasoning.

---

## Partial Rerun Notes

If only one input changes, the assistant must not automatically rerun the full pipeline.

It must first produce a `PARTIAL RERUN PLAN` that identifies:

- changed input;
- earliest safe rerun stage;
- reusable stages;
- invalidated downstream stages;
- required payloads;
- required confirmation if the rerun depends on a missing decision.

---

## E2E Test Notes

E2E-001 passed with minor flags.

Validated:

- full stage sequence through `/handoff-export`;
- Stage Source Access Matrix discipline;
- Stage Anchor v1.1 continuity;
- Debug Trace compatibility;
- unknown propagation;
- Stage 4 arithmetic / N/A / unknown handling;
- Stage 5 audit behavior;
- Stage 6 recommendation gate;
- Stage 7 editability and tree readability;
- Stage 8 exact-value restraint and scoped CSS map;
- Stage 9 blocker/high behavior;
- Stage 10 audit-flag preservation.

Not validated by E2E-001:

- pixel-accurate raster screenshot interpretation;
- live Elementor rendering;
- real Elementor export JSON;
- browser/device QA.

---

## Current Next Step

Preferred next action:

```text
Prepare or run /e2e-screenshot-validation when raster screenshot evidence or a screenshot fixture is available.
```

Do not remove the E2E-001 medium flag until screenshot-based validation produces a verifiable report.

---

## NEXT WORK ANCHOR — /e2e-screenshot-validation

```text
NEXT WORK ANCHOR — /e2e-screenshot-validation
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /tuya-concept-reference
target_stage: /e2e-screenshot-validation
target_stage_hardening_status: draft
project_status_version: 0.15.0
payload_schema_in:
  - ev4-tuya-concept-reference@1.0.0
  - ev4-e2e-test-report@1.0.0
  - ev4-rag-strategy-contract@1.0.0
payload_schema_out:
  - ev4-e2e-screenshot-validation-report@0.1.0 or newer active schema

Carry-forward facts:
- key_decisions:
  - TUYA is active only as internal_concept_reference.
  - TUYA facts are project_conceptual_model only.
  - TUYA cannot prove official platform capability, visual grouping, scoring, recommendation, exact settings, or export/runtime behavior.
- critical_unknowns:
  - pixel-accurate raster screenshot interpretation remains unvalidated.
  - real Elementor export JSON / EDIS remains unvalidated.
  - live Elementor/browser rendering remains unvalidated.
- blocking_items:
  - None for TUYA concept-reference contract hardening.
  - Screenshot/export/live-rendering validation remain separate future tracks.
- gate_results:
  - TUYA contract gate: pass
  - RAG alignment gate: pass
  - Debug trace compatibility: pass
- audit_flags:
  - TUYA-LP probes must be preserved in E2E/final-audit.
  - Do not remove E2E-001 textual-fixture medium flag.
- required_user_confirmations:
  - A real screenshot or screenshot fixture is required before pixel-accurate validation can run.

Partial rerun state:
- reusable_until:
  - RAG Strategy v1.0.0 remains active
  - Research contract v1.0.0 remains active
  - TUYA source classification remains unchanged
- invalidation_triggers:
  - TUYA workbook source changes
  - RAG Strategy source-class taxonomy changes
  - Stage Source Access Matrix changes
  - official docs/export evidence contradicts a TUYA concept used downstream
- earliest_safe_rerun_stage: /research for source classification changes; /decompose for visual evidence changes; /score-evidence for scoring leakage; /final-audit for audit-only leakage
- downstream_payloads_dependent_on_this_stage:
  - future research payloads
  - future architecture payloads
  - future final-audit payloads
  - future handoff payloads
  - future E2E reports

Stage boundary:
- allowed_work:
  - Prepare or run screenshot-based E2E validation when raster screenshot evidence exists.
  - Validate that /decompose uses only visible/user evidence.
  - Validate that TUYA does not leak into visual grouping, scoring, recommendation, implementation, final audit, or handoff.
- forbidden_work:
  - Do not mark pixel-accurate screenshot interpretation validated without raster screenshot evidence.
  - Do not use TUYA to infer screenshot content.
  - Do not remove E2E-001 medium flag unless a screenshot-based E2E resolves it.
- stop_conditions:
  - missing screenshot/visual fixture
  - missing required payload chain
  - TUYA leakage detected without repair route
  - no verifiable screenshot-validation report schema

Debug trace:
- debug_trace_required: yes
- expected_debug_trace_schema: ev4-debug-trace@1.0.0
```
