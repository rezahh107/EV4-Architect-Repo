# STATUS — Elementor V4 Architect Prompt Pack

Version: 0.15.1
Status: stage_8_10_alignment_patch_applied
Last confirmed stage: Stage 8–10 hardening alignment patch
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
| /research | confirmed_hardened_v1.0.0 | Source-pinning owner, source ledger, downstream permission map, repair routes, self-audit, debug trace, anchor handoff |
| /decompose | confirmed_with_example_bank | Controlled Visual Role Decomposition; must not use research/RAG/TUYA/docs to invent visual groups |
| /decomposition-example-bank | active_enhanced | Pattern-based examples plus authoring standard |
| /architectures | confirmed_hardened_v1.1.0 | Coverage matrix, unknown propagation, recommendation ban, dynamic guardrails |
| /score-evidence | confirmed_hardened_v1.3.0_patch | Uses rubric 1.3 and Stage 4 hardening patch |
| /score-audit | confirmed_hardened_v1.2.0_patch | Stage 5 self-audit, hidden recommendation guard, tie handoff, responsive cap reference binding |
| /scoring-calibration-bank | active | examples/scoring calibration cases added |
| /recommend | confirmed_hardened_v1.1.0_patch | Recommendation matrix, provenance ledger, tie handling, build-tree readiness gate, debug record |
| /stage-anchor-contract | active_v1.1.0 | Required target hardening status, confidence delta, partial rerun state, visible external anchor |
| /partial-rerun-contract | active_v1.0.0 | Safe partial rerun and invalidation rules |
| /debug-trace-contract | active_v1.0.0 | External trace contract for pipeline debugging |
| /build-tree | confirmed_hardened_v1.0.0 | Naming convention, Structure Panel schema, wrapper budget, widget constraints, responsive contract |
| /implementation | confirmed_hardened_v1.0.0 + alignment_patch_v1.0.1 | Stage 8 remains confirmed; next-anchor status/schema must follow active STATUS.md |
| /final-audit | confirmed_hardened_v1.0.0 + alignment_patch_v1.0.1 | Stage 9 remains confirmed; scoped E2E validation vocabulary applies |
| /handoff-export | confirmed_hardened_v1.0.0 + alignment_patch_v1.0.1 | Stage 10 remains confirmed; E2E payload state must not be hard-coded |
| /elementor-knowledge-base-strategy | active_v1.0.0 | RAG source-access strategy and source classification contract |
| /tuya-concept-reference | active_v1.0.0 | TUYA is internal_concept_reference only; project_conceptual_model only |
| /stage-8-10-alignment-patch | confirmed_hardening_patch_v1.0.1 | `stages/STAGE_8_10_v1.0.1_HARDENING_ALIGNMENT_PATCH.md` |
| /e2e-test-plan | confirmed_hardened_v1.0.0 | Full-pipeline E2E scope, fixture contract, source-access checks, anchor/debug validation |
| /e2e-test | pass_with_minor_flags | E2E-001 completed through /handoff-export; textual fixture limitation remains medium non-blocking flag |
| /e2e-screenshot-validation | not_run | Requires raster screenshot evidence or screenshot fixture before pixel-accurate interpretation can be validated |

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
- stages/STAGE_8_10_v1.0.1_HARDENING_ALIGNMENT_PATCH.md
- examples/scoring/README.md
- examples/scoring/SCORING-CAL-001-contradicted-evidence.md
- examples/scoring/SCORING-CAL-002-absent-vs-contradicted.md
- examples/scoring/SCORING-CAL-003-arithmetic-needs-audit.md
- examples/scoring/SCORING-CAL-004-overlay-na.md

---

## Scaffolded / Draft / Validation Work Remaining

- `/e2e-screenshot-validation` is not run and cannot run without raster screenshot evidence or a screenshot fixture.
- E2E-001 used a realistic textual mockup, not a raster screenshot.
- Pixel-accurate screenshot interpretation remains unvalidated by E2E-001.
- Real Elementor export JSON / EDIS validation remains future work.
- Live Elementor/browser rendering remains future work.

---

## Stage 8–10 Alignment Patch Result

```yaml
STAGE_8_10_ALIGNMENT_PATCH:
  file: stages/STAGE_8_10_v1.0.1_HARDENING_ALIGNMENT_PATCH.md
  status: confirmed_hardening_patch_v1.0.1
  version: 1.0.1
  applies_to:
    - stages/08_IMPLEMENTATION.md
    - stages/09_FINAL_AUDIT.md
    - stages/10_HANDOFF_EXPORT.md
  fixes:
    - Stage 8 and Stage 9 next-anchor templates must use active STATUS.md status/schema values, not stale scaffolded placeholders.
    - Stage 9 and Stage 10 must use scoped E2E validation vocabulary.
    - Stage 10 must not hard-code e2e_run_available false when E2E-001 evidence exists.
  confirmed_stage_state:
    /implementation: confirmed_hardened_v1.0.0
    /final-audit: confirmed_hardened_v1.0.0
    /handoff-export: confirmed_hardened_v1.0.0
```

Strict boundary:

```text
E2E-001 may support prompt-pack full-pipeline contract validation with minor textual-fixture limitation.
E2E-001 must not be used to claim pixel-accurate screenshot interpretation, live Elementor rendering, or real Elementor export JSON validation.
```

---

## E2E Validation State

```yaml
e2e_validation_state:
  prompt_pack_full_pipeline:
    status: pass_with_minor_flags
    evidence_ref: experiments/E2E-001-test-report.md
    limitation: realistic textual mockup, not raster screenshot
  pixel_accurate_screenshot_interpretation:
    status: not_validated
    required_next_stage: /e2e-screenshot-validation
  live_elementor_rendering:
    status: not_validated
  real_elementor_export_json_or_EDIS:
    status: not_validated
```

Release boundary interpretation:

```text
The previous release blocker requiring one passing E2E run is removed for the prompt-pack full-pipeline contract because E2E-001 reached /handoff-export and preserved anchors, payloads, unknowns, and flags.

This does not claim pixel-accurate screenshot interpretation, live Elementor rendering, or real export JSON validation. Those remain future validation tracks.
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
```

Strict boundary:

```text
TUYA may guide vocabulary, thinking order, normal-flow discipline, relative visual stage logic, responsive caution, design-system mindset, and DOM/audit checklisting.
TUYA must not prove platform capability, infer screenshot content, raise scores, break recommendation ties, invent exact settings, override official docs/export evidence, soften final-audit findings, or clean up handoff risks.
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
source_stage: /stage-8-10-alignment-patch
target_stage: /e2e-screenshot-validation
target_stage_hardening_status: draft
project_status_version: 0.15.1
payload_schema_in:
  - ev4-stage-hardening-alignment-patch@1.0.1
  - ev4-e2e-test-report@1.0.0
  - ev4-rag-strategy-contract@1.0.0
  - ev4-tuya-concept-reference@1.0.0
payload_schema_out:
  - ev4-e2e-screenshot-validation-report@0.1.0 or newer active schema

Carry-forward facts:
- key_decisions:
  - Stage 8 /implementation is confirmed_hardened_v1.0.0.
  - Stage 9 /final-audit is confirmed_hardened_v1.0.0.
  - Stage 10 /handoff-export is confirmed_hardened_v1.0.0.
  - Stage 8–10 alignment patch v1.0.1 is active.
  - E2E-001 validates prompt-pack full-pipeline contract with minor textual-fixture limitation.
- critical_unknowns:
  - pixel-accurate raster screenshot interpretation remains unvalidated.
  - real Elementor export JSON / EDIS remains unvalidated.
  - live Elementor/browser rendering remains unvalidated.
- confidence_delta:
  - item: Stage 8–10 contract hardening consistency
    previous_confidence: confirmed
    current_confidence: confirmed
    direction: increased
    reason: strict critic review found only alignment issues and patched them in v1.0.1
    downstream_impact: /implementation, /final-audit, and /handoff-export may run with aligned anchors and scoped E2E wording
- blocking_items:
  - None for Stage 8–10 prompt-contract hardening.
  - Screenshot/export/live-rendering validation remain separate future tracks.
- gate_results:
  - Stage 8 contract review: pass
  - Stage 9 contract review: pass
  - Stage 10 contract review: pass
  - Alignment patch: pass
- audit_flags:
  - Do not remove E2E-001 textual-fixture medium flag.
  - Do not claim screenshot/live/export validation without evidence.
- required_user_confirmations:
  - A real screenshot or screenshot fixture is required before pixel-accurate validation can run.

Partial rerun state:
- reusable_until:
  - Stage 8–10 contracts remain reusable until STATUS.md, stage schemas, source-access matrix, Stage Anchor Contract, Partial Rerun Contract, Debug Trace Contract, RAG/TUYA boundaries, or E2E evidence scope changes.
- invalidation_triggers:
  - Stage 8/9/10 schema changes
  - E2E-001 evidence contradicted or superseded
  - screenshot fixture added
  - real Elementor export JSON added
  - live rendering evidence added
  - source-access or TUYA/RAG boundary changes
- earliest_safe_rerun_stage:
  - /e2e-screenshot-validation for screenshot-specific validation
  - /handoff-export for packaging wording defects only
  - /final-audit for audit-scope or severity-boundary defects
  - /implementation for implementation schema or CSS/widget-map defects
- downstream_payloads_dependent_on_this_stage:
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
