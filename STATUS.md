# STATUS — Elementor V4 Architect Prompt Pack

Version: 0.12.0
Status: e2e_validated_with_minor_flags
Last confirmed stage: E2E-001 — full-pipeline validation
Current next step: Harden `/research` into a confirmed contract with versioned source policy, source pinning, `ev4-research-payload@1.0.0`, repair routes, self-audit, debug trace, and Stage Anchor handoff.
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

---

## Stage Status

| Stage | Status | Notes |
|---|---|---|
| /intake | confirmed | Lightweight default-based intake |
| /research | draft_required | Highest-priority unfinished stage. Needs source policy, version-pinned source rules, retrieval output schema, RAG integration, repair routes, self-audit, debug trace, and anchor handoff. |
| /decompose | confirmed_with_example_bank | Controlled Visual Role Decomposition with example bank |
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
| /elementor-knowledge-base-strategy | draft_active_v0.3.0 | Adds mandatory Stage Source Access Matrix to prevent RAG/source leakage into scoring and recommendation |
| /tuya-concept-reference | active_v0.2.0 | Adds provisional-to-contradicted transition rule and evidence reclassification behavior |
| /e2e-test-plan | confirmed_hardened_v1.0.0 | Defines full-pipeline E2E scope, fixture contract, source-access checks, anchor validation, debug trace validation, negative controls, report schema, repair routing, and release-boundary rules |
| /e2e-test | pass_with_minor_flags | E2E-001 completed through /handoff-export and produced `ev4-e2e-test-report@1.0.0`; textual fixture limitation remains as medium non-blocking flag |

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

## Hardened Stage / Validation Files

- stages/08_IMPLEMENTATION.md
- stages/09_FINAL_AUDIT.md
- stages/10_HANDOFF_EXPORT.md
- experiments/END_TO_END_PIPELINE_TEST_PLAN.md
- experiments/E2E-001-test-report.md

---

## Scaffolded / Draft Work Remaining

- `/research` remains `draft_required` and is now the next highest-priority unfinished contract.
- E2E-001 used a realistic textual mockup, not a raster screenshot.
- Pixel-accurate screenshot interpretation remains unvalidated by E2E-001.
- Real Elementor export JSON / EDIS validation remains future work.

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
  low_findings:
    - E2E001-LOW-001: exact token values remain unknown
    - E2E001-LOW-002: exact icon source/library remains unknown
    - E2E001-LOW-003: animation requirement remains unknown
    - E2E001-LOW-004: dynamic dashboard data requirement remains unknown
```

E2E-001 selected architecture during the authorized `/recommend` stage:

```yaml
selected_candidate_id: A02_native_plus_scoped_decorative_css
selected_candidate_family: native editable structure + section-scoped decorative CSS
reason: highest audited eligible score, editable meaningful content, contained decorative connector/glow layer, no third-party dependency, no flattened dashboard content
```

Release boundary interpretation:

```text
The previous release blocker requiring one passing E2E test is removed for the prompt-pack full-pipeline contract because E2E-001 reached /handoff-export, preserved anchors/payloads/unknowns/flags, and left no blocker/high finding.

This does not claim pixel-accurate screenshot interpretation, live Elementor rendering, or real export JSON validation. Those remain future validation tracks.
```

---

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
- prevent running scaffolded/draft stages as production output without explicit approval;
- preserve invalidation triggers for partial reruns;
- prevent long-context drift;
- keep handoffs compact and auditable.

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

## Knowledge Base / RAG Notes

A structured Elementor knowledge base may support `/research`, `/architectures`, `/build-tree`, `/implementation`, and `/final-audit`.

It must not replace the pipeline or skip `/decompose`, `/score-evidence`, `/score-audit`, or `/recommend`.

Core distinction:

```text
platform capability ≠ project-specific behavior
```

Official documentation can prove Elementor can do something; it cannot by itself prove that the current section should use that thing.

Future export evidence / EDIS may strengthen implementation grounding and final audit checks but must still pass through the pipeline.

### Stage Source Access Matrix

The RAG Strategy defines which sources each stage may use.

Key gates:

- Stage 2 uses only image/user-provided evidence and must not use RAG to invent visual groups.
- Stage 3 may use TUYA concepts and official docs to verify architecture feasibility.
- Stage 4 must score from Rubric + Stage 2/3 evidence; TUYA/RAG cannot boost scores by themselves.
- Stage 6 must recommend only from audited Stage 4/5 outputs; no new RAG preference signals.
- Stage 7/8 may use TUYA + official docs to map approved architecture/tree decisions to structure and implementation.
- Stage 9 may use Stage 8, Stage 7, Stage 6, Stage 5, Stage 4 constraints, TUYA audit concepts, official docs, and export evidence only to audit preservation and capability claims; it must not generate new architecture or implementation.
- Stage 10 may use final audited outputs, debug traces, anchors, and payloads only to package the run; it must not change decisions.
- E2E validation must check source-access compliance across every stage, especially Stage 2, Stage 4, Stage 6, Stage 9, and Stage 10.

---

## TUYA Internal Concept Reference Notes

The TUYA workbook is treated as an internal conceptual reference, not as official Elementor documentation.

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

```text
provisional + stronger supporting evidence → supported / partially supported
provisional + still incomplete evidence → stays provisional
provisional + direct conflicting evidence → CONTRADICTED_EVIDENCE
unknown by itself ≠ contradiction
```

---

## Stage 8 — /implementation Hardening Notes

Stage 8 is confirmed as a hardened contract, not a scaffold.

Important limitation:

```text
Stage 8 hardening confirms the prompt contract. It does not replace a real pipeline run.
```

---

## Stage 9 — /final-audit Hardening Notes

Stage 9 is confirmed as a hardened contract, not a scaffold.

Important limitation:

```text
Stage 9 hardening confirms the final-audit prompt contract. It does not mean every future real implementation has passed final audit.
```

---

## Stage 10 — /handoff-export Hardening Notes

Stage 10 is confirmed as a hardened contract, not a scaffold.

Important limitation:

```text
Stage 10 hardening confirms the handoff-export prompt contract. It does not mean a future real EV4 run can skip final audit or E2E validation.
```

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
Harden /research from draft_required to a confirmed contract.
```

The next run should build or complete `stages/02_RESEARCH.md` or the existing research-stage equivalent with:

- input gate;
- source access policy;
- official source pinning rules;
- retrieval output schema;
- `ev4-research-payload@1.0.0`;
- forbidden RAG behavior;
- repair routes;
- self-audit;
- debug trace addendum;
- NEXT STAGE ANCHOR handoff.
