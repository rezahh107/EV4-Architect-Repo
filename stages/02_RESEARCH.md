# Stage 2 — /research

Status: confirmed_hardened_v1.0.0
Stage version: 1.0.0
Payload schema: ev4-research-payload@1.0.0
Applies after: /intake
Feeds: /decompose, /architectures, /build-tree, /implementation, /final-audit
Validation Profile: `blocked_missing_semantics`
Continuation authorization: blocked. This document does not define an executable Anchor template; no `/intake → /research` or `/research → /decompose` transition is authorized until the relevant source Stages have complete executable Validation Profiles and independently regenerated Bundles.

---

## Purpose

`/research` is the controlled source-grounding stage for Elementor platform facts, project contracts, internal concept references, and future export evidence.

Core rule:

```text
Research may prove or disprove platform capability.
Research must not decide what the current screenshot visually contains.
Research must not score, recommend, build, implement, or audit the section.
```

This stage exists to prevent source leakage from RAG, TUYA, official docs, and exports into stages that are supposed to be evidence-bound.

---

## Required Input Gate

Before running `/research`, validate the input package.

Required:

```yaml
required_inputs:
  - independently regenerated Validation Bundle: ev4-architect-validation-bundle@1.2.0
  - contained current Anchor: ev4-stage-anchor@1.4.0
  - source_stage: /intake or approved repair/rerun stage
  - target_stage: /research
  - user constraints or research scope
  - active project overrides
  - active RAG/source-access policy
  - current date or retrieval date
```

Optional but useful:

```yaml
optional_inputs:
  - user-provided Elementor version
  - user-provided Pro/free constraint
  - user-provided plugin constraints
  - existing project/export JSON evidence
  - specific platform-capability question
  - docs or URLs supplied by the user
```

Fail the gate if:

```text
- Validation Bundle is missing, outdated, schema-mismatched, or inconsistent.
- Research scope is absent and no platform-capability question exists.
- The stage is being asked to infer visual hierarchy from a screenshot.
- The stage is being asked to score or recommend a candidate.
- The stage is being asked to produce a build tree or implementation plan.
```

If the gate fails, emit `RESEARCH_BLOCKED_REPAIR_REPORT` and stop.

---

## Source Access Policy

`/research` may use only these source classes:

| Source class | Allowed use | Forbidden use |
|---|---|---|
| `official_docs` | Prove documented Elementor capability, limitation, Pro/free status, or editor behavior | Prove that the current section should use that capability |
| `release_notes` | Version-pin changed behavior or new/removed capability | Treat future/old behavior as current without date/version context |
| `export_evidence` | Confirm project-specific implementation observations from real Elementor JSON/export/runtime evidence | Replace the staged pipeline or override user constraints silently |
| `project_contract` | Apply EV4 stage rules, source matrix, anchors, debug trace, partial rerun constraints | Invent platform behavior |
| `internal_concept_reference` | Use TUYA/EV4 concepts for vocabulary and thinking order | Prove Elementor platform capability or score/recommend |
| `user_input` | Record user constraints, preferences, and supplied facts | Convert ambiguous input into confirmed technical fact |
| `secondary_source` | Background context only when official docs are unavailable | Override official docs, export evidence, or project contracts |

Mandatory distinction:

```text
platform_capability ≠ project_specific_behavior
```

Official Elementor docs can prove Elementor can do something. They do not prove the current section should use it.

---

## Stage Source Matrix Binding

`/research` must preserve the active Stage Source Access Matrix.

Downstream permissions:

```yaml
/decompose:
  may_use_research_payload: only for project constraints and explicit user-supplied constraints
  must_not_use_research_payload_for: visual grouping, meaningful/decorative classification, hidden element inference

/architectures:
  may_use_research_payload: platform feasibility, Pro/free dependency, native/custom/hybrid feasibility
  must_not_use_research_payload_for: final recommendation or score totals

/score-evidence:
  may_use_research_payload: only if the fact is already represented in Stage 2/3 evidence or project rules
  must_not_use_research_payload_for: direct score boosting from broad RAG/TUYA claims

/score-audit:
  may_use_research_payload: spot-check source classification and detect leakage
  must_not_use_research_payload_for: adding new architecture evidence

/recommend:
  may_use_research_payload: only if Stage 5 explicitly routes a tie/source clarification through the tie protocol
  must_not_use_research_payload_for: hidden preference signals

/build-tree:
  may_use_research_payload: map approved architecture to documented widgets/containers/classes/variables
  must_not_use_research_payload_for: re-architecting

/implementation:
  may_use_research_payload: documented widget/settings/CSS/source constraints and export-backed implementation observations
  must_not_use_research_payload_for: inventing exact values, breakpoints, or assets

/final-audit:
  may_use_research_payload: verify preservation and documented capability claims
  must_not_use_research_payload_for: generating new implementation

/handoff-export:
  may_use_research_payload: package source ledger and flags
  must_not_use_research_payload_for: changing decisions
```

---

## Research Workflow

Run in this order.

### 1. Scope Classification

Classify the research request:

```yaml
research_scope_type:
  - platform_capability_check
  - pro_free_dependency_check
  - widget_or_container_reference
  - design_system_reference
  - responsive_behavior_reference
  - custom_css_or_selector_reference
  - export_evidence_inspection
  - internal_concept_reference_lookup
  - conflict_resolution
  - source_policy_only
```

If the scope includes visual interpretation, move it to `/decompose` and mark research use as forbidden for that part.

### 2. Query Plan

Produce a compact `RESEARCH_QUERY_PLAN` before facts.

```yaml
RESEARCH_QUERY_PLAN:
  schema: ev4-research-query-plan@1.0.0
  research_questions:
    - id:
      question:
      required_source_class:
      acceptable_source_classes:
      freshness_requirement: current | version_pinned | stable | export_only
      downstream_stage_allowed_use:
      stop_if_not_found: yes | no
```

### 3. Source Pinning

Every source must be pinned.

```yaml
SOURCE_PIN:
  source_id:
  source_type: official_docs | release_notes | export_evidence | project_contract | internal_concept_reference | user_input | secondary_source
  title:
  publisher_or_owner:
  url_or_repo_path:
  retrieval_date:
  document_last_update: known | unknown
  product_or_version_context: known | unknown
  access_method: web | repo | user_upload | export_inspection
  trust_level: high | medium | low
  limitations:
```

Rules:

```text
- If document_last_update is unknown, mark it unknown.
- If product/version context is missing, do not claim version-specific behavior.
- If a source cannot be reopened or cited, do not treat it as high-confidence.
- If official docs and export evidence conflict, export evidence may govern project-specific behavior but the conflict must be logged.
```

### 4. Retrieved Fact Ledger

Every fact must use this shape.

```yaml
RETRIEVED_FACT:
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

### 5. Unknown and Unsupported Claim Register

Unsupported claims must become unknowns, not implementation facts.

```yaml
UNKNOWN_REGISTER_ITEM:
  unknown_id:
  unknown:
  introduced_at_stage: /research
  reason:
  attempted_sources:
  effect_if_unresolved:
  propagated_to_stages:
  repair_route:
```

### 6. Conflict Register

```yaml
CONFLICT_REGISTER_ITEM:
  conflict_id:
  conflicting_claims:
  sources:
  conflict_type: official_vs_official | docs_vs_export | docs_vs_tuya | user_vs_docs | version_mismatch | unsupported_assumption
  current_resolution: unresolved | export_evidence_controls_project_behavior | official_docs_control_platform_capability | user_confirmation_required | repair_required
  downstream_effect:
```

---

## Official Source Pinning Rules

When researching Elementor, prefer:

```yaml
preferred_official_sources:
  - Elementor Help / Knowledge Hub pages
  - Elementor developer documentation
  - Elementor release notes or changelog when version-sensitive
  - official widget/control documentation when available
```

Do not rely on generic SEO articles, forum answers, snippets, or third-party tutorials to confirm platform capability unless no official source exists. If a secondary source is used, label it `secondary_source` and keep confidence at `low` or `medium` unless supported elsewhere.

If current official docs must be verified, browse or fetch them during the actual run. Do not assume older cached knowledge is current.

---

## TUYA / Internal Concept Reference Rules

When using `knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md`, classify each fact as:

```yaml
source_type: internal_concept_reference
fact_class: project_conceptual_model
```

Allowed:

```text
- vocabulary alignment;
- thinking order;
- normal-flow vs overlay discipline;
- relative visual stage concept;
- responsive inheritance caution;
- class/variable/component mindset;
- DOM/audit checklisting.
```

Forbidden:

```text
- proving an Elementor widget or setting exists;
- proving Pro/free availability;
- proving a current screenshot should use an architecture;
- increasing Stage 4 scores directly;
- breaking Stage 6 ties;
- replacing official docs or export evidence.
```

If a TUYA-derived provisional concept is contradicted by later stage evidence, reclassify it as `CONTRADICTED_EVIDENCE` against the dependent assumption.

---

## Export Evidence / EDIS Rules

If Elementor export evidence is available, treat it as a separate evidence class:

```yaml
EXPORT_EVIDENCE_ITEM:
  export_id:
  file_path_or_attachment_id:
  inspected_at:
  elementor_version_if_known:
  observed_property:
  observed_value:
  source_object_path:
  fact_class: implementation_observation | project_specific_behavior
  limitation:
  allowed_use:
```

Export evidence may confirm how a current project represents something. It must not bypass `/decompose`, `/score-evidence`, `/score-audit`, or `/recommend`.

---

## Forbidden Work

`/research` must not:

```text
- infer visual groups from a screenshot;
- classify meaningful vs decorative elements;
- create architecture candidates;
- score candidates;
- audit scores;
- recommend a candidate;
- build a Structure Panel tree;
- invent Elementor widgets/settings not found in docs or exports;
- invent exact breakpoints, CSS values, coordinates, z-indexes, colors, or assets;
- treat official docs as project-specific behavior;
- treat TUYA as official Elementor documentation;
- silently resolve unknowns;
- hide source conflicts;
- use RAG as a hidden preference signal.
```

---

## Output Contract

A passing `/research` stage must output these sections:

```text
1. RESEARCH INPUT GATE
2. RESEARCH QUERY PLAN
3. SOURCE LEDGER
4. RETRIEVED FACT LEDGER
5. CAPABILITY / DEPENDENCY MAP
6. UNSUPPORTED CLAIMS AND UNKNOWNS
7. SOURCE CONFLICT REGISTER
8. DOWNSTREAM SOURCE PERMISSION MAP
9. RESEARCH_PAYLOAD
10. RESEARCH SELF-AUDIT
11. EV4_DEBUG_TRACE
12. VALIDATOR-OWNED CONTINUATION TRANSACTION
```

If the stage cannot pass, output:

```text
RESEARCH BLOCKED REPORT
RESEARCH_BLOCKED_REPAIR_REPORT
```

---

## Research Payload Schema

```yaml
RESEARCH_PAYLOAD:
  schema: ev4-research-payload@1.0.0
  stage: /research
  stage_version: 1.0.0
  run_id:
  source_validation_bundle:
    schema: ev4-architect-validation-bundle@1.2.0
    contained_anchor_schema: ev4-stage-anchor@1.4.0
    source_stage:
  input_gate:
    status: pass | fail
    inputs_present:
    inputs_missing:
    stop_conditions_triggered:
  research_scope:
    scope_type:
    research_questions:
    excluded_requests:
  source_policy:
    active_strategy: references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
    active_overrides: 02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md
    tuya_reference: knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
    platform_capability_not_project_behavior: true
  query_plan:
    - question_id:
      query_or_lookup:
      required_source_class:
      freshness_requirement:
      downstream_allowed_use:
  source_ledger:
    - source_id:
      source_type:
      title:
      url_or_repo_path:
      retrieval_date:
      document_last_update:
      product_or_version_context:
      trust_level:
      limitations:
  retrieved_facts:
    - fact_id:
      source_id:
      source_type:
      normalized_claim:
      fact_class:
      confidence:
      support_status:
      limitation:
      allowed_use:
      forbidden_use:
      downstream_visibility:
  capability_map:
    native_capabilities:
    pro_or_plan_dependent_capabilities:
    third_party_or_custom_dependencies:
    unsupported_capabilities:
  export_evidence_register:
    available: yes | no
    items:
  unsupported_claims:
    - claim_id:
      claim:
      reason_not_supported:
      required_evidence_to_resolve:
  unknown_register:
    - unknown_id:
      unknown:
      effect_if_unresolved:
      propagated_to_stages:
      repair_route:
  conflict_register:
    - conflict_id:
      conflict_type:
      current_resolution:
      downstream_effect:
  downstream_source_permission_map:
    /decompose:
    /architectures:
    /score-evidence:
    /score-audit:
    /recommend:
    /build-tree:
    /implementation:
    /final-audit:
    /handoff-export:
  self_audit:
    status: pass | fail
    failures:
  debug_trace:
    schema: ev4-debug-trace@1.0.0
    trace_id:
  continuation_transaction:
    schema: ev4-architect-validation-bundle@1.2.0
    generated_by: registered_validator_only
    target_stage: /decompose
```

---

## Repair Routes

| Failure | Required output | Earliest safe repair stage | Forbidden shortcut |
|---|---|---|---|
| Missing/invalid Validation Bundle | `RESEARCH_BLOCKED_REPAIR_REPORT` | previous producing stage or `/intake` | Do not run from memory |
| Missing research scope | `RESEARCH BLOCKED REPORT` | `/intake` or user constraints | Do not invent platform questions |
| Official source unavailable | unknown register item | `/research` | Do not replace with low-trust source silently |
| Unsupported platform claim | unsupported claim register | `/research` | Do not treat as confirmed capability |
| TUYA used as official proof | source classification failure | `/research` | Do not relabel TUYA as docs |
| Research leaked into Stage 2 visual grouping | source-access violation | `/research` + `/decompose` repair | Do not keep downstream decomposition |
| Research boosted Stage 4 score | source-access violation | `/score-evidence` repair | Do not keep audited score |
| Research broke Stage 6 tie directly | source-access violation | `/recommend` repair | Do not keep recommendation |
| Docs/export conflict unresolved | conflict register + blocked repair report | `/research` or export inspection | Do not choose convenient source silently |
| Missing debug trace | local repair | `/research` | Do not mark confirmed |

---

## Regression Cases

A hardened `/research` contract must prevent these regressions:

```yaml
REGRESSION_CASES:
  - id: RSH-REG-001
    name: docs-to-visual-group-leak
    failure: Elementor docs are used to infer visible screenshot groups.
    expected: fail source-access audit; repair from /decompose.

  - id: RSH-REG-002
    name: tuya-as-official-proof
    failure: TUYA concept proves an Elementor setting exists.
    expected: classify as project_conceptual_model only; require official docs/export.

  - id: RSH-REG-003
    name: platform-capability-to-project-decision
    failure: documented capability becomes a build-tree decision before /recommend.
    expected: block; preserve as capability only.

  - id: RSH-REG-004
    name: unsupported-claim-promoted
    failure: undocumented exact value becomes confirmed.
    expected: unknown register + downstream flag.

  - id: RSH-REG-005
    name: secondary-source-overrides-official
    failure: blog/tutorial overrides official docs.
    expected: conflict register; official docs control platform capability.

  - id: RSH-REG-006
    name: stale-version-claim
    failure: old docs/release notes are treated as current without version/date.
    expected: version context unknown or stale; do not confirm current behavior.

  - id: RSH-REG-007
    name: rag-score-boost
    failure: RAG facts increase Stage 4 score directly.
    expected: source-access violation; rerun from /score-evidence.

  - id: RSH-REG-008
    name: missing-downstream-visibility
    failure: retrieved facts have no allowed/forbidden downstream map.
    expected: payload fail; local repair.
```

---

## Self-Audit Checklist

Before marking `/research` complete, verify:

```text
[ ] A current independently regenerated Validation Bundle and its contained Anchor were checked.
[ ] Every source is pinned with source_id, type, URL/path, retrieval date, trust level, and limitation.
[ ] Every fact has source_type, fact_class, confidence, support_status, allowed_use, and forbidden_use.
[ ] Platform capability and project-specific behavior are separated.
[ ] Unsupported claims became unknowns, not facts.
[ ] TUYA is classified only as internal_concept_reference/project_conceptual_model.
[ ] Export evidence is separate from generic docs.
[ ] Downstream source permissions are explicit for every stage.
[ ] No architecture, score, recommendation, tree, implementation, or audit work was performed.
[ ] Repair routes exist for missing sources, unsupported claims, source conflicts, and source-access leakage.
[ ] EV4_DEBUG_TRACE uses ev4-debug-trace@1.0.0.
[ ] The Registry profile is executable before any validator-owned transaction targets `/decompose`.
```

If any item fails, mark the stage `partial_or_blocked` and emit a non-authorizing blocked repair report.

---

## EV4_DEBUG_TRACE Addendum

A `/research` trace must include:

```json
{
  "schema": "ev4-debug-trace@1.0.0",
  "stage": "/research",
  "stage_version": "1.0.0",
  "input_digest": {
    "inputs_received": [],
    "inputs_missing": [],
    "input_payload_schemas": ["ev4-architect-validation-bundle@1.2.0"]
  },
  "decision_log": [],
  "evidence_map": [],
  "unknown_register": [],
  "rule_application_log": [],
  "failure_symptom_index": [],
  "repair_route": null,
  "handoff_payload_schema": "ev4-research-payload@1.0.0"
}
```

Decision log entries must be limited to source classification, support classification, conflict handling, and downstream permission mapping.

---

## Validation Transaction Boundary

This document defines detailed research semantics, but `/research` is currently `blocked_missing_semantics`. There is no canonical machine-readable Artifact Schema, complete deterministic semantic validator, or deterministic repair-ownership implementation for this Stage.

Therefore `/research` must not emit a Validation Bundle or Validation Bundle and must not continue to `/decompose`. The legal Manifest edge remains topology only. Future enablement requires closing every unresolved decision in `manifests/architect-stage-validation-profiles.v1.json`, implementing the registered handler and regeneration path, and versioning the carriers if their semantics change.

---

## Confirmation Boundary

This file confirms the `/research` prompt contract.

It does not mean every future research run has valid current sources. Each run must still retrieve or verify sources appropriate to that run, pin them, classify facts, and preserve downstream source permissions.
