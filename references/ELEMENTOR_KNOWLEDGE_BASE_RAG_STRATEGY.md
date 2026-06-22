# Elementor Knowledge Base / RAG Strategy

Status: active_v1.0.0
Version: 1.0.0
Strategy schema: ev4-rag-strategy-contract@1.0.0
Aligned with: `stages/02_RESEARCH.md` / `ev4-research-payload@1.0.0`
Applies to: `/research`, `/decompose`, `/architectures`, `/score-evidence`, `/score-audit`, `/recommend`, `/build-tree`, `/implementation`, `/final-audit`, `/handoff-export`, `/e2e-test`

---

## Purpose

A structured Elementor knowledge base may improve factual grounding, but it must never replace the EV4 staged pipeline.

Core rule:

```text
Use RAG to ground source-backed capability claims.
Do not use RAG to infer what the screenshot contains, select an architecture, improve a score, bypass audit, or package a run with hidden decisions.
```

This file is the active source-access contract that binds RAG, official Elementor documentation, export evidence / EDIS, TUYA internal concepts, and project contracts to their allowed stage boundaries.

---

## Critical Distinction

```text
platform_capability ≠ project_specific_behavior
```

Official Elementor documentation can show that Elementor can do something in general. It cannot, by itself, prove that the current section should use that capability.

Export evidence can show how a real Elementor project currently represents a value or structure. It still cannot bypass `/decompose`, `/score-evidence`, `/score-audit`, or `/recommend`.

TUYA can preserve the EV4 mental model. It cannot prove official Elementor behavior.

---

## Strict Critic Findings Against v0.3.0

The previous `draft_active_v0.3.0` strategy was useful but insufficient as an active contract.

Confirmed weaknesses:

```text
- stage numbering was stale after `/research` became an explicit Stage 2 contract;
- `/research` was described as a supported consumer, but not clearly defined as the source-pinning owner;
- downstream visibility was not mandatory for every retrieved fact;
- source freshness and version context were not enforceable enough;
- conflict lifecycle was shallow;
- EDIS/export evidence boundaries were underspecified;
- Stage 9/10/E2E source-access checks were not strict enough;
- repair routes and leakage probes were missing as first-class contract requirements;
- pass criteria did not require debug trace and Stage Anchor handoff references;
- no machine-readable strategy payload/schema existed.
```

Hardening response:

```text
This v1.0.0 file makes source pinning, retrieved-fact classification, downstream permission, freshness handling, conflict lifecycle, repair routing, leakage probes, self-audit, debug trace, and Stage Anchor handoff mandatory.
```

---

## Contract Status Gate

This strategy may be treated as active only when all of these are true:

```yaml
RAG_STRATEGY_CONTRACT_GATE:
  schema: ev4-rag-strategy-contract@1.0.0
  status: active_v1.0.0
  required_bindings:
    - stages/02_RESEARCH.md
    - ev4-research-payload@1.0.0
    - contracts/STAGE_ANCHOR_CONTRACT.md
    - contracts/PARTIAL_RERUN_CONTRACT.md
    - diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
    - knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
  required_controls:
    - source class taxonomy
    - source pin schema
    - retrieved fact schema
    - downstream permission matrix
    - official source freshness rules
    - export evidence / EDIS boundary
    - conflict lifecycle
    - forbidden leakage probes
    - repair routes
    - self-audit
    - debug trace addendum
    - next-work anchor
```

If any required control is missing or contradicted by a later active contract, this file must be treated as `active_but_repair_required`, not silently trusted.

---

## Source Class Taxonomy

Every source used by RAG or source-grounding must be classified before its facts can travel downstream.

| Source class | Trust role | Allowed use | Forbidden use |
|---|---|---|---|
| `official_docs` | High for documented Elementor capability when current/version-appropriate | Prove documented capability, editor behavior, widget/control existence, Pro/free dependency when explicitly stated | Prove project-specific design choice, visual grouping, or exact implementation value for the current section |
| `release_notes` | High for version-sensitive changes when version/date is pinned | Prove changed/new/removed behavior for a known version window | Treat old or future behavior as current without version context |
| `developer_docs` | High for API/control/export concepts when official and current | Ground developer-facing behavior, export/control vocabulary, integration limits | Override project contracts or visual evidence |
| `export_evidence` | High for project-specific implementation observation when the export is real and traceable | Confirm actual Elementor JSON/runtime representation for the current project | Replace Stage 2–7 decisions or repair upstream logic silently |
| `project_contract` | High for EV4 pipeline rules | Enforce stage boundaries, payload schemas, anchors, debug trace, partial rerun rules | Invent platform behavior |
| `internal_concept_reference` | Medium/high for project mental model only | Preserve vocabulary, thinking order, safe heuristics, TUYA conceptual discipline | Prove Elementor capability, score directly, break ties, or override official docs/export evidence |
| `user_input` | High for user constraints when explicit | Record constraints, preferences, supplied project facts | Convert ambiguous wording into confirmed technical facts |
| `secondary_source` | Low/medium background context only | Fill context when official docs are absent and clearly labeled | Override official docs, export evidence, project contracts, or user constraints |
| `unsupported_claim` | No evidentiary authority | Preserve as unknown/unsupported item | Become an implementation fact, score input, or handoff instruction |

---

## `/research` Is the Source-Pinning Owner

`/research` owns source discovery, source pinning, retrieved fact classification, unsupported claim handling, conflict registration, and downstream permission mapping.

Required `/research` behavior:

```text
1. Receive a valid ev4-stage-anchor@1.1.0.
2. Classify the research scope.
3. Produce a compact query plan.
4. Retrieve or inspect appropriate sources.
5. Pin each source.
6. Convert only supported claims into RETRIEVED_FACT records.
7. Convert unsupported claims into unknowns.
8. Register conflicts instead of smoothing them.
9. Assign downstream visibility for every fact.
10. Emit ev4-research-payload@1.0.0 and an EV4_DEBUG_TRACE.
```

Forbidden `/research` behavior:

```text
- no screenshot visual grouping;
- no meaningful/decorative classification;
- no architecture generation;
- no score assignment;
- no score audit;
- no recommendation;
- no build tree;
- no implementation plan;
- no final audit;
- no exact setting/value invention.
```

---

## Stage Source Access Matrix

Use stage IDs as authoritative. Numeric labels are descriptive only.

| Pipeline stage | Primary sources allowed | Restricted / forbidden sources | Hard rule |
|---|---|---|---|
| Stage 1 `/intake` | User request, user constraints, project defaults | RAG only if the user asks a blocking platform-capability question | Do not research by default. Preserve unknowns. |
| Stage 2 `/research` | Official docs, release notes, developer docs, project contracts, TUYA as internal concept reference, user-supplied URLs, export evidence if provided | Screenshot interpretation, scoring, recommendation, implementation decisions | Pin sources and classify facts only. |
| Stage 3 `/decompose` | Screenshot/image, user description, explicit user constraints, valid Stage Anchor | Official docs, TUYA, RAG facts as visual evidence | Decompose only visible/provided evidence. RAG must not invent visual groups or hidden content. |
| Stage 4 `/architectures` | Decomposition payload, Stage Anchor, project defaults, approved research facts for feasibility, TUYA concepts, official docs | Final recommendation language, scoring totals, hidden RAG preference signals | Generate candidate families; do not choose a winner. |
| Stage 5 `/score-evidence` | Rubric, decomposition evidence, architecture candidates, Stage Anchor, calibration cases | TUYA/RAG as independent score boosters | Score only from rubric + stage evidence. RAG may only support a fact already admitted by stage evidence/project rules. |
| Stage 6 `/score-audit` | Stage 5 report, audit payload, rubric, Stage 3/4 spot checks, Stage Anchor, source classification records | New architecture evidence except audit spot-checks | Audit scoring process and source leakage; do not redesign. |
| Stage 7 `/recommend` | Audited Stage 5/6 outputs, tie handoff, Stage Anchor | New RAG claims, new visual assumptions, direct TUYA preference | Recommend only among audited eligible candidates. |
| Stage 8 `/build-tree` | Recommendation payload, Stage Anchor, approved research facts for widget/container feasibility, TUYA concepts, naming contract | New candidate selection, direct screenshot reinterpretation | Build the tree from the selected architecture; do not re-architect. |
| Stage 9 `/implementation` | Build tree payload, Stage Anchor, official widget/settings references, approved research facts, TUYA concepts, export evidence if available | New scoring, recommendation, visual reinterpretation | Implement the approved tree with exact-value restraint and scoped constraints. |
| Stage 10 `/final-audit` | Implementation payload, build tree, recommendation, score/audit constraints, research payload, TUYA audit concepts, export evidence if available | New architecture or implementation generation | Audit preservation, evidence, source leakage, CSS scope, responsive risk, and blockers. |
| Stage 11 `/handoff-export` | Final audited outputs, payloads, anchors, debug traces, audit flags, source ledger | New decisions, new source interpretation, silent repairs | Package only. Preserve blockers, flags, unknowns, and source limits. |
| Stage 12 `/e2e-test` | All stage contracts, payloads, anchors, debug traces, fixture/evidence | Skipping source-access checks | Validate source access across stages; failures need repair routes. |

Hard bans:

```text
/decompose must not use RAG/TUYA/docs to see things.
/score-evidence must not use RAG/TUYA to raise a score directly.
/recommend must not use RAG/TUYA to break a tie unless Stage 6 explicitly routes the tie through the protocol.
/handoff-export must not soften a failed final audit.
```

---

## Source Pin Schema

Every source used by `/research` or a RAG-supported stage must be pinned.

```yaml
SOURCE_PIN:
  schema: ev4-source-pin@1.0.0
  source_id:
  source_type: official_docs | release_notes | developer_docs | export_evidence | project_contract | internal_concept_reference | user_input | secondary_source
  title:
  publisher_or_owner:
  url_or_repo_path:
  retrieval_date:
  document_last_update: known | unknown | n/a
  product_or_version_context: known | unknown | n/a
  access_method: web | repo | user_upload | export_inspection | user_message
  trust_level: high | medium | low | none
  limitations:
  citation_or_reference:
```

Pinning rules:

```text
- If document_last_update is unknown, mark it unknown.
- If product/version context is unknown, do not make version-specific claims.
- If a source cannot be reopened, cited, or inspected, do not classify it as high trust.
- If a secondary source is used because no official source exists, record the failed official-source lookup.
- If export evidence and docs conflict, log the conflict; do not choose the convenient source silently.
```

---

## Retrieved Fact Schema

Every retrieved fact must use this structure.

```yaml
RETRIEVED_FACT:
  schema: ev4-retrieved-fact@1.0.0
  fact_id:
  source_id:
  source_type:
  retrieved_claim:
  normalized_claim:
  applies_to_stage:
  fact_class: platform_capability | project_default | project_conceptual_model | project_specific_behavior | implementation_observation | unsupported_claim
  confidence: high | medium | low
  support_status: supported | partially_supported | unsupported | contradicted | unresolved_conflict
  quote_or_summary:
  limitation:
  allowed_use:
  forbidden_use:
  downstream_visibility:
    /decompose: allowed | restricted | forbidden
    /architectures: allowed | restricted | forbidden
    /score-evidence: allowed | restricted | forbidden
    /score-audit: allowed | restricted | forbidden
    /recommend: allowed | restricted | forbidden
    /build-tree: allowed | restricted | forbidden
    /implementation: allowed | restricted | forbidden
    /final-audit: allowed | restricted | forbidden
    /handoff-export: allowed | restricted | forbidden
```

Fact-class rules:

```text
platform_capability: proves Elementor can/cannot do something generally.
project_default: proves an EV4/project rule.
project_conceptual_model: preserves TUYA/EV4 vocabulary or heuristic only.
project_specific_behavior: requires user input or export/runtime evidence.
implementation_observation: requires real export/runtime inspection.
unsupported_claim: must remain unknown; it cannot feed build/audit as fact.
```

---

## Downstream Permission Defaults

Unless a retrieved fact overrides this explicitly with a stricter rule, use these defaults.

| Fact class | /decompose | /architectures | /score-evidence | /score-audit | /recommend | /build-tree | /implementation | /final-audit | /handoff-export |
|---|---|---|---|---|---|---|---|---|---|
| `platform_capability` | forbidden for visual grouping | allowed for feasibility | restricted | allowed for leakage checks | restricted via tie protocol only | allowed for mapping | allowed for settings/capability limits | allowed for verification | allowed for source ledger only |
| `project_default` | restricted | allowed | allowed if rubric/project rule | allowed | allowed | allowed | allowed | allowed | allowed |
| `project_conceptual_model` | forbidden for visual grouping | restricted | forbidden as score booster | allowed for leakage checks | forbidden as preference | restricted | restricted | restricted | allowed as concept note only |
| `project_specific_behavior` | allowed only if user/visual evidence | allowed | allowed if evidence-bound | allowed | allowed through audited path | allowed | allowed | allowed | allowed |
| `implementation_observation` | forbidden for initial visual grouping | restricted | restricted | allowed | restricted | allowed if selected architecture is stable | allowed | allowed | allowed |
| `unsupported_claim` | forbidden | forbidden | forbidden | allowed only as defect/unknown | forbidden | forbidden | forbidden except as unknown | allowed as blocker/flag | allowed as blocker/flag |

---

## Official Source Freshness Rules

Freshness must be checked according to claim type.

```yaml
FRESHNESS_POLICY:
  stable_concept:
    examples: container basics, general editor concept names
    requirement: source pin with retrieval date; last update preferred
  version_sensitive:
    examples: new V4 features, Pro/free status, beta/experimental features, editor UI changes
    requirement: current official docs or version-pinned release notes
  project_specific:
    examples: actual settings, JSON structure, live behavior, export values
    requirement: export_evidence or user-provided project evidence
  unsupported_or_unclear:
    requirement: unknown register; do not promote to fact
```

Rules:

```text
- Do not assume cached model knowledge is current for version-sensitive Elementor behavior.
- Do not make Pro/free claims without an official or user-provided source.
- Do not claim a specific control path exists unless the source actually supports the control path or export evidence shows it.
- When official pages lack dates, mark document_last_update: unknown and avoid version-specific certainty.
```

---

## EDIS / Export Evidence Boundary

`EDIS` means Elementor Document/Export Inspection System. It is a future or external evidence layer for real Elementor JSON/export/runtime inspection.

Export evidence schema:

```yaml
EXPORT_EVIDENCE_ITEM:
  schema: ev4-export-evidence-item@1.0.0
  export_id:
  file_path_or_attachment_id:
  inspected_at:
  elementor_version_if_known:
  observed_property:
  observed_value:
  source_object_path:
  fact_class: implementation_observation | project_specific_behavior
  confidence: high | medium | low
  limitation:
  allowed_use:
  forbidden_use:
```

Allowed:

```text
- confirm how a real project currently stores or renders a value;
- verify implementation preservation in /final-audit;
- strengthen /implementation grounding after upstream decisions are approved;
- provide repair evidence for source conflicts.
```

Forbidden:

```text
- bypass /decompose;
- bypass /score-evidence;
- bypass /score-audit;
- bypass /recommend;
- choose a candidate because an export pattern exists;
- hide a mismatch between approved architecture and actual export evidence.
```

Conflict priority:

```text
Official docs control general platform capability.
Export evidence controls observed current-project implementation behavior.
User constraints control project requirements unless impossible or contradictory.
Project contracts control pipeline legality.
```

---

## Conflict Lifecycle

Conflicts must remain visible until resolved by named evidence.

```yaml
CONFLICT_REGISTER_ITEM:
  schema: ev4-source-conflict@1.0.0
  conflict_id:
  conflicting_claims:
  sources:
  conflict_type: official_vs_official | docs_vs_export | docs_vs_tuya | user_vs_docs | version_mismatch | unsupported_assumption | contract_vs_stage_output
  current_resolution: unresolved | export_evidence_controls_project_behavior | official_docs_control_platform_capability | user_confirmation_required | project_contract_controls_pipeline | repair_required
  confidence_delta:
    previous_confidence:
    current_confidence:
    direction: increased | decreased | unchanged | resolved | blocked
    reason:
  downstream_effect:
  repair_route:
```

Resolution rules:

```text
- Do not resolve conflict by omission.
- Do not downgrade contradicted evidence to absent evidence.
- Do not let an unresolved conflict enter /handoff-export as a clean item.
- If conflict affects architecture eligibility, rerun from /architectures or earlier.
- If conflict affects score arithmetic/evidence, rerun from /score-evidence.
- If conflict affects implementation preservation, rerun from /implementation or /final-audit as appropriate.
```

---

## Unsupported Claims and Unknowns

Unsupported claims must become explicit unknowns.

```yaml
UNKNOWN_REGISTER_ITEM:
  schema: ev4-rag-unknown@1.0.0
  unknown_id:
  unknown:
  introduced_at_stage:
  reason:
  attempted_sources:
  effect_if_unresolved:
  propagated_to_stages:
  repair_route:
```

Rules:

```text
- unknown ≠ contradiction;
- provisional ≠ confirmed;
- unsupported ≠ safe default;
- low-confidence source ≠ confirmed fact;
- no exact setting, breakpoint, z-index, asset, selector, widget, or plugin dependency may be invented from an unknown.
```

---

## Forbidden Leakage Probes

Any E2E or audit run must probe for these failures.

```yaml
RAG_LEAKAGE_PROBES:
  - id: RAG-LEAK-001
    name: docs-to-visual-group
    failure: official docs are used to infer visible screenshot groups
    expected_result: fail /decompose source-access audit; rerun from /decompose

  - id: RAG-LEAK-002
    name: tuya-score-boost
    failure: TUYA concept directly raises Stage 5 score
    expected_result: fail /score-evidence; rerun from /score-evidence

  - id: RAG-LEAK-003
    name: rag-tie-break
    failure: RAG fact breaks a recommendation tie outside the tie protocol
    expected_result: fail /recommend; rerun from /recommend

  - id: RAG-LEAK-004
    name: docs-as-project-decision
    failure: documented capability becomes project-specific behavior without user/export evidence
    expected_result: unsupported/unknown; no build-tree instruction

  - id: RAG-LEAK-005
    name: tuya-as-official-proof
    failure: TUYA concept proves Elementor platform capability
    expected_result: source classification failure; require official docs/export evidence

  - id: RAG-LEAK-006
    name: secondary-source-overrides-official
    failure: blog/tutorial overrides official Elementor docs
    expected_result: conflict register; official source controls platform capability

  - id: RAG-LEAK-007
    name: export-bypasses-pipeline
    failure: export evidence directly chooses architecture or skips scoring
    expected_result: fail source-access audit; rerun earliest affected stage

  - id: RAG-LEAK-008
    name: unsupported-to-setting
    failure: unsupported claim becomes exact setting, selector, breakpoint, z-index, asset, or plugin instruction
    expected_result: unknown register + implementation/final-audit blocker

  - id: RAG-LEAK-009
    name: final-audit-softening
    failure: /final-audit uses RAG context to excuse an implementation mismatch
    expected_result: blocker/high remains; repair route required

  - id: RAG-LEAK-010
    name: handoff-cleanup
    failure: /handoff-export drops source flags, unknowns, or unresolved conflicts
    expected_result: handoff blocked or flagged; no clean final handoff
```

---

## Repair Routes

| Failure | Required output | Earliest safe repair stage | Invalidates | Forbidden shortcut |
|---|---|---|---|---|
| Missing active RAG strategy | `SOURCE_POLICY_REPAIR_ANCHOR` | `/research` | source-backed downstream payloads | Do not run from memory |
| Missing source pin | local repair | `/research` | affected retrieved facts | Do not cite unpinned source |
| Unsupported claim promoted to fact | unknown register + repair anchor | `/research` | affected downstream stages | Do not keep the promoted fact |
| TUYA used as official proof | source classification failure | `/research` | affected facts/stages | Do not relabel TUYA as docs |
| Docs used for visual grouping | source-access violation | `/decompose` | `/architectures` onward | Do not keep downstream decomposition |
| RAG/TUYA boosted score | source-access violation | `/score-evidence` | `/score-audit` onward | Do not keep audited score |
| RAG broke recommendation tie directly | source-access violation | `/recommend` | `/build-tree` onward | Do not keep recommendation |
| Official docs vs export conflict unresolved | conflict register + repair anchor | `/research` or export inspection | affected implementation/audit/handoff | Do not choose convenient source silently |
| Missing downstream visibility map | payload fail | `/research` | affected RAG payload | Do not mark research complete |
| Missing debug trace | local repair | producing stage | downstream trace continuity | Do not mark confirmed |
| Handoff dropped source flags | handoff blocked report | `/handoff-export` | final package | Do not clean up risks for readability |

Partial rerun rule:

```text
Rerun from the earliest stage whose owned information changed. Never reuse downstream payloads that depend on stale source facts.
```

---

## RAG Strategy Payload Schema

When this strategy itself is audited or handed forward, use this shape.

```yaml
RAG_STRATEGY_PAYLOAD:
  schema: ev4-rag-strategy-contract@1.0.0
  strategy_file: references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
  status: active_v1.0.0
  version: 1.0.0
  aligned_contracts:
    - stages/02_RESEARCH.md
    - contracts/STAGE_ANCHOR_CONTRACT.md
    - contracts/PARTIAL_RERUN_CONTRACT.md
    - diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
    - knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
  source_class_taxonomy_status: pass | fail
  source_pin_schema_status: pass | fail
  retrieved_fact_schema_status: pass | fail
  downstream_permission_matrix_status: pass | fail
  freshness_policy_status: pass | fail
  edis_boundary_status: pass | fail
  conflict_lifecycle_status: pass | fail
  leakage_probe_status: pass | fail
  repair_routes_status: pass | fail
  self_audit_status: pass | fail
  known_limitations:
  next_anchor:
    schema: ev4-stage-anchor@1.1.0
```

---

## Self-Audit Checklist

Before marking this strategy active, verify:

```text
[ ] Status is active_v1.0.0 and schema is ev4-rag-strategy-contract@1.0.0.
[ ] `/research` is explicitly the source-pinning owner.
[ ] Stage Source Access Matrix uses current pipeline IDs and includes /research, /handoff-export, and /e2e-test.
[ ] Every source class has allowed and forbidden uses.
[ ] SOURCE_PIN includes retrieval date, version/update context, trust level, limitations, and reference.
[ ] RETRIEVED_FACT includes fact_class, support_status, allowed_use, forbidden_use, and downstream_visibility.
[ ] Platform capability is separated from project-specific behavior.
[ ] TUYA is internal_concept_reference/project_conceptual_model only.
[ ] Official source freshness and version-sensitive behavior rules are explicit.
[ ] EDIS/export evidence cannot bypass Stage 2–7 gates.
[ ] Conflict lifecycle has resolution states, confidence_delta, downstream effect, and repair route.
[ ] Unsupported claims become unknowns.
[ ] Leakage probes cover /decompose, /score-evidence, /recommend, /final-audit, and /handoff-export.
[ ] Repair routes name earliest safe rerun stages and invalidated downstream outputs.
[ ] Debug trace and Stage Anchor handoff are referenced.
```

If any item fails, status must be `active_but_repair_required` or `partial`, not `active_v1.0.0`.

Current self-audit result:

```yaml
SELF_AUDIT_RESULT:
  status: pass
  checked_against:
    - stages/02_RESEARCH.md
    - contracts/STAGE_ANCHOR_CONTRACT.md
    - contracts/PARTIAL_RERUN_CONTRACT.md
    - diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
  remaining_limitations:
    - This strategy confirms source-access policy, not the freshness of every future Elementor source.
    - Future runs must still browse/fetch current official docs when version-sensitive claims are made.
    - Real export JSON / EDIS and live rendering remain future validation tracks.
```

---

## EV4_DEBUG_TRACE Addendum

A source-access or RAG-supported stage must include trace entries for:

```json
{
  "schema": "ev4-debug-trace@1.0.0",
  "trace_scope": "source_access_and_rag_policy",
  "decision_log_required_for": [
    "source_classification",
    "support_status_classification",
    "downstream_permission_mapping",
    "conflict_resolution",
    "unknown_registration",
    "repair_route_selection"
  ],
  "forbidden_trace_content": [
    "hidden chain-of-thought",
    "unstated visual inference",
    "unstated preference signal",
    "architecture decision outside authorized stage"
  ]
}
```

Debug traces must externalize what source was used, what claim was supported, what rule was applied, what remained unknown, and what repair route applies. They must not expose or depend on private reasoning.

---

## NEXT WORK ANCHOR

```text
NEXT WORK ANCHOR — /tuya-concept-reference hardening
anchor_schema: ev4-stage-anchor@1.1.0
source_stage: /elementor-knowledge-base-strategy
target_stage: /tuya-concept-reference
target_stage_hardening_status: draft
project_status_version: 0.14.0
payload_schema_in:
  - ev4-rag-strategy-contract@1.0.0
  - active TUYA concept reference v0.2.0
payload_schema_out:
  - ev4-tuya-concept-reference@1.0.0 or newer active schema

Carry-forward facts:
- key_decisions:
  - RAG Strategy is active_v1.0.0.
  - TUYA must remain internal_concept_reference/project_conceptual_model.
  - TUYA cannot prove platform capability, raise scores directly, break ties, or replace official docs/export evidence.
- selected_or_active_candidates: None
- rejected_or_blocked_candidates: None
- critical_unknowns:
  - TUYA reference file is still v0.2.0 and should be checked against this v1.0.0 RAG strategy.
  - Pixel-accurate screenshot validation, real export JSON / EDIS, and live rendering remain future validation tracks.
- confidence_delta:
  - item: RAG source-access policy
    previous_confidence: likely
    current_confidence: confirmed
    direction: increased
    reason: RAG strategy now has active v1.0.0 schema, stage matrix, source pins, fact schema, conflict lifecycle, repair routes, self-audit, debug trace, and anchor handoff.
    downstream_impact: /research and downstream source use can treat this file as active policy input.
- blocking_items: None for RAG strategy contract; validation tracks remain open.
- gate_results:
  - source_access_policy_gate: pass
  - downstream_permission_gate: pass
  - repair_route_gate: pass
  - debug_trace_reference_gate: pass
- audit_flags:
  - Do not treat this strategy as proof that future docs are fresh.
  - Each run must still retrieve/pin current sources for version-sensitive claims.
- tie_or_ambiguity_flags: None
- required_user_confirmations: None
- repair_routes: See Repair Routes section in this file.

Partial rerun state:
- reusable_until: source policy, official docs, export evidence, TUYA concept rules, project contracts, or pipeline stage order changes
- invalidation_triggers:
  - changed EV4 stage order or stage IDs
  - changed Stage Anchor schema
  - changed Research_Payload schema
  - new source class or new export/EDIS policy
  - discovered RAG leakage in E2E/final audit
  - TUYA reference contradiction with official docs/export evidence
- earliest_safe_rerun_stage: /research for source facts; /elementor-knowledge-base-strategy for policy defects
- downstream_payloads_dependent_on_this_stage:
  - /research
  - /architectures
  - /build-tree
  - /implementation
  - /final-audit
  - /handoff-export
  - /e2e-test

Stage input package:
- required_inputs_present:
  - references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
  - stages/02_RESEARCH.md
  - knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
  - active Stage Anchor / Partial Rerun / Debug Trace contracts
- required_inputs_missing: None
- files_or_sections_to_reference:
  - knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
  - references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
  - stages/02_RESEARCH.md

Stage boundary:
- allowed_work:
  - Harden TUYA internal concept reference.
  - Align source_type/fact_class vocabulary with RAG Strategy v1.0.0.
  - Add TUYA-specific leakage probes, contradiction handling, repair routes, self-audit, debug trace, and anchor handoff.
- forbidden_work:
  - No official Elementor capability claims from TUYA alone.
  - No scoring/recommendation changes.
  - No architecture selection.
  - No deletion of E2E-001 minor flags.
- stop_conditions:
  - TUYA cannot be aligned without contradicting active RAG or Research contracts.
  - Missing repair routes for TUYA leakage.
  - Missing downstream permission matrix.

Debug trace:
- debug_trace_required: yes
- previous_debug_trace_id: RAG-STRATEGY-HARDENING-v1.0.0
- expected_debug_trace_schema: ev4-debug-trace@1.0.0
```

---

## Confirmation Boundary

This file confirms the source-access and RAG strategy contract.

It does not mean every future research run has valid current sources. Each run must still retrieve or verify sources appropriate to that run, pin them, classify facts, and preserve downstream source permissions.

It also does not validate pixel-accurate screenshot interpretation, live Elementor rendering, or real Elementor export JSON. Those remain separate validation tracks.
