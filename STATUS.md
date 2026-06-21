# STATUS — Elementor V4 Architect Prompt Pack

Version: 0.8.0
Status: in_progress
Last confirmed stage: Stage 8 — /implementation
Current next step: Continue to Stage 9 — /final-audit hardening. Release blocker: run one E2E pipeline test before marking Stage 9 production-confirmed.
Language: Persian reports, English technical labels allowed
Last automation update: 2026-06-22

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
| /implementation | confirmed_hardened_v1.0.0 | Stage 8 hardened with input gate, exact payload schema, source ledger, settings schema, widget map, class/variable map, scoped CSS validator, asset/accessibility map, responsive examples, repair routes, self-audit, debug trace, and anchor handoff |
| /final-audit | draft_scaffolded | Stage 9 scaffold created; needs hardening |
| /handoff-export | draft_scaffolded | Stage 10 scaffold created; needs hardening |
| /elementor-knowledge-base-strategy | draft_active_v0.3.0 | Adds mandatory Stage Source Access Matrix to prevent RAG/source leakage into scoring and recommendation |
| /tuya-concept-reference | active_v0.2.0 | Adds provisional-to-contradicted transition rule and evidence reclassification behavior |
| /e2e-test-plan | draft_active | First real pipeline run remains a release blocker before Stage 9 production confirmation |

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
- stages/08_IMPLEMENTATION.md
- examples/scoring/README.md
- examples/scoring/SCORING-CAL-001-contradicted-evidence.md
- examples/scoring/SCORING-CAL-002-absent-vs-contradicted.md
- examples/scoring/SCORING-CAL-003-arithmetic-needs-audit.md
- examples/scoring/SCORING-CAL-004-overlay-na.md

## Hardened Stage Files

- stages/08_IMPLEMENTATION.md

## Scaffolded Stage Files

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

### Stage Source Access Matrix

The RAG Strategy now defines which sources each stage may use.

Key gates:

- Stage 2 uses only image/user-provided evidence and must not use RAG to invent visual groups.
- Stage 3 may use TUYA concepts and official docs to verify architecture feasibility.
- Stage 4 must score from Rubric + Stage 2/3 evidence; TUYA/RAG cannot boost scores by themselves.
- Stage 6 must recommend only from audited Stage 4/5 outputs; no new RAG preference signals.
- Stage 7/8 may use TUYA + official docs to map approved architecture/tree decisions to structure and implementation.

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

### TUYA Evidence Transition Rule

A TUYA-derived `provisional` item may be reclassified later.

```text
provisional + stronger supporting evidence → supported / partially supported
provisional + still incomplete evidence → stays provisional
provisional + direct conflicting evidence → CONTRADICTED_EVIDENCE
unknown by itself ≠ contradiction
```

This prevents the pipeline from preserving a weak provisional heuristic after later Stage evidence disproves it.

## Stage 8 — /implementation Hardening Notes

Stage 8 is now confirmed as a hardened contract, not a scaffold.

Added controls:

- strict input authorization against `ev4-stage-anchor@1.1.0` and `ev4-build-tree-payload@1.0.0`;
- mandatory Stage Source Access Matrix binding;
- official source ledger for Elementor platform-capability claims;
- exact `elementor_settings_plan` schema;
- widget mapping schema with editability, accessibility, dependency, and fallback policy;
- class and variable application map;
- scoped CSS need map and validator;
- asset and accessibility schema;
- responsive implementation schema and safe example shapes;
- position/layering implementation plan;
- dynamic data / interaction plan;
- implementation risks schema;
- Stage 8 self-audit;
- `Implementation_Payload` schema;
- debug trace addendum;
- repair routes;
- NEXT STAGE ANCHOR template for `/final-audit`.

Important limitation:

```text
Stage 8 hardening confirms the prompt contract. It does not replace the first real E2E pipeline run.
```

## E2E Test Notes

Before marking Stage 9 as production-confirmed, run at least one realistic section through:

```text
/intake → /decompose → /architectures → /score-evidence → /score-audit → /recommend → /build-tree → /implementation
```

The test should measure anchor quality, drift control, repair loop cost, output usability, unknown survival, CSS scoping, responsive-risk propagation, and whether implementation preserves the approved tree.

## Current Next Step

Preferred next action:

```text
Continue to Stage 9 — /final-audit hardening in hardening mode.
```

Release blocker before production confirmation:

```text
Run one E2E test before marking Stage 9 confirmed for production pipeline use.
```
