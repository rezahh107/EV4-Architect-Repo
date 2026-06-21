# STATUS — Elementor V4 Architect Prompt Pack

Version: 0.7.3
Status: in_progress
Last confirmed stage: Stage 7 — /build-tree
Current next step: Run first E2E pipeline test or continue to Stage 8 — /implementation hardening
Language: Persian reports, English technical labels allowed

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

## Stage Status

| Stage | Status | Notes |
|---|---|---|
| /intake | confirmed | Lightweight default-based intake |
| /research | draft_required | Needs source policy, version-pinned source rules, and RAG integration |
| /decompose | confirmed_with_example_bank | Controlled Visual Role Decomposition with 12 examples |
| /decomposition-example-bank | active_enhanced | Pattern-based examples plus authoring standard |
| /architectures | confirmed_hardened_v1.1.0 | Coverage matrix, unknown propagation, recommendation ban, dynamic guardrails |
| /score-evidence | confirmed_hardened_v1.3.0_patch | Uses rubric 1.3 and Stage 4 v1.3 hardening patch |
| /score-audit | confirmed_hardened_v1.2.0_patch | Adds Stage 5 self-audit, hidden recommendation guard, tie handoff, responsive cap reference binding |
| /scoring-calibration-bank | active | examples/scoring calibration cases added |
| /recommend | confirmed_hardened_v1.1.0_patch | Recommendation matrix, provenance ledger, tie handling, build-tree readiness gate, debug record |
| /stage-anchor-contract | active_v1.1.0 | Adds confidence_delta, target_stage_hardening_status, and partial_rerun_state |
| /partial-rerun-contract | active_v1.0.0 | Defines safe partial reruns and invalidation rules |
| /debug-trace-contract | active | External trace contract for pipeline debugging |
| /build-tree | confirmed_hardened_v1.0.0 | Naming convention, Structure Panel tree schema, wrapper budget, widget constraints, responsive contract |
| /implementation | draft_scaffolded | Stage 8 scaffold created; needs hardening |
| /final-audit | draft_scaffolded | Stage 9 scaffold created; needs hardening |
| /handoff-export | draft_scaffolded | Stage 10 scaffold created; needs hardening |
| /elementor-knowledge-base-strategy | draft_active_v0.2.0 | RAG/docs strategy now includes TUYA internal concept reference layer |
| /tuya-concept-reference | active_v0.1.0 | Internal conceptual reference extracted from TUYA workbook for Stage 3/7/8/9 support |
| /e2e-test-plan | draft_active | First real pipeline run recommended before finalizing later stages |

## Active Hardening / Contract Files

- 02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md
- contracts/STAGE_ANCHOR_CONTRACT.md
- contracts/PARTIAL_RERUN_CONTRACT.md
- contracts/BUILD_TREE_NAMING_AND_STRUCTURE_CONTRACT.md
- diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
- references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
- knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
- experiments/END_TO_END_PIPELINE_TEST_PLAN.md
- stages/04_SCORE_EVIDENCE_v1.3_HARDENING_PATCH.md
- stages/05_SCORE_AUDIT_v1.1_HARDENING_PATCH.md
- stages/05_SCORE_AUDIT_v1.2_HARDENING_PATCH.md
- stages/06_RECOMMEND.md
- stages/06_RECOMMEND_v1.1_HARDENING_PATCH.md
- stages/07_BUILD_TREE.md
- examples/scoring/README.md
- examples/scoring/SCORING-CAL-001-contradicted-evidence.md
- examples/scoring/SCORING-CAL-002-absent-vs-contradicted.md
- examples/scoring/SCORING-CAL-003-arithmetic-needs-audit.md
- examples/scoring/SCORING-CAL-004-overlay-na.md

## Scaffolded Stage Files

- stages/08_IMPLEMENTATION.md
- stages/09_FINAL_AUDIT.md
- stages/10_HANDOFF_EXPORT.md

## Stage Anchor v1.1 Notes

A Stage Anchor is required before starting each stage after `/intake`.

New v1.1 fields:

- `target_stage_hardening_status`
- `confidence_delta`
- `partial_rerun_state`

Purpose:

- preserve critical unknowns;
- preserve blockers and gate results;
- record whether confidence increased, decreased, stayed unchanged, or was resolved;
- prevent running scaffolded/draft stages as production output without explicit user approval;
- preserve invalidation triggers for partial reruns;
- prevent long-context drift;
- keep handoffs compact and auditable.

The anchor is an external structured handoff.

## Partial Rerun Notes

If only one input changes, the assistant must not automatically rerun the full pipeline.

It must first produce a `PARTIAL RERUN PLAN` that identifies:

- changed input;
- earliest safe rerun stage;
- reusable stages;
- invalidated downstream stages;
- required payloads;
- required user confirmation.

## Knowledge Base / RAG Notes

A structured Elementor knowledge base may support `/research`, `/architectures`, `/build-tree`, and `/implementation`.

It must not replace the pipeline or skip `/decompose`, `/score-evidence`, `/score-audit`, or `/recommend`.

Core distinction:

```text
platform capability ≠ project-specific behavior
```

Official documentation can prove Elementor can do something; it cannot by itself prove that the current section should use that thing.

Future export evidence / EDIS may strengthen implementation grounding but must still pass through the pipeline.

## TUYA Internal Concept Reference Notes

The TUYA workbook is now treated as an internal conceptual reference, not as official Elementor documentation.

Use `knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md` to preserve:

- Global Thinking Order: `Context → Structure → Flow/Display → Size/Units → Position/Layering → Responsive → Design System → DOM/Audit`;
- the `confirmed | provisional | unknown` thinking labels;
- normal-flow content plus relative visual stage discipline;
- responsive inheritance caution;
- design-system class/variable/component logic;
- performance and DOM/audit mindset.

Any TUYA-derived fact must be classified as:

```text
source_type: internal_concept_reference
fact_class: project_conceptual_model
```

It may guide reasoning but must not prove platform capability or bypass the EV4 pipeline.

## E2E Test Notes

Before finalizing later stages, run at least one realistic section through:

```text
/intake → /decompose → /architectures → /score-evidence → /score-audit → /recommend → /build-tree
```

The test should measure anchor quality, drift control, repair loop cost, output usability, and whether unknowns survive to the correct stage.

## Current Next Step

Preferred next action:

```text
Run one E2E test before Stage 8 hardening.
```

Alternative:

```text
Continue to Stage 8 — /implementation hardening, but keep the first E2E test as a release blocker before Stage 9.
```
