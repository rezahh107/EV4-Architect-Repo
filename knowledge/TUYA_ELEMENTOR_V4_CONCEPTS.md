# TUYA Elementor V4 Concepts — Internal Concept Reference Contract

Status: active_v1.0.0
Version: 1.0.0
Reference schema: ev4-tuya-concept-reference@1.0.0
Source: `TUYA_Standalone_Workbook_v32_0_0_lessons_1_21_release_candidate_v25.html`
Source type: `internal_concept_reference`
Fact class: `project_conceptual_model`
Aligned with:
- `references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md` / `ev4-rag-strategy-contract@1.0.0`
- `stages/02_RESEARCH.md` / `ev4-research-payload@1.0.0`
- `contracts/STAGE_ANCHOR_CONTRACT.md` / `ev4-stage-anchor@1.1.0`
- `contracts/PARTIAL_RERUN_CONTRACT.md` / `ev4-partial-rerun@1.0.0`
- `diagnostics/LLM_DEBUG_TRACE_CONTRACT.md` / `ev4-debug-trace@1.0.0`
Applies to: `/research`, `/architectures`, `/score-audit`, `/build-tree`, `/implementation`, `/final-audit`, `/handoff-export`, `/e2e-test`
Forbidden as evidence for: `/decompose` visual grouping, direct `/score-evidence` score boosts, direct `/recommend` preference, official Elementor capability proof, project-specific implementation observation

---

## Purpose

This file extracts pipeline-relevant concepts from the TUYA Elementor V4 workbook and hardens them into an internal concept-reference contract for the EV4 Architect Prompt Pack.

It is not official Elementor documentation. It is not export evidence. It is not visual evidence. It is not a scoring authority.

Core rule:

```text
Use TUYA to preserve EV4 vocabulary, thinking order, normal-flow discipline, stage/overlay caution, responsive caution, design-system mindset, and audit checklists.
Do not use TUYA to prove platform capability, infer screenshot contents, raise scores, break ties, override official docs/export evidence, or clean up unresolved risks.
```

The controlling distinction remains:

```text
platform_capability ≠ project_specific_behavior ≠ internal_conceptual_model
```

---

## Strict Critic Findings Against v0.2.0

The previous `active_reference v0.2.0` was useful but not strict enough to serve as an active source-policy contract.

Confirmed weaknesses:

```text
- source_type used `internal_course_reference`, while the RAG Strategy v1.0.0 requires `internal_concept_reference`.
- stage numbering was stale after `/research` became explicit Stage 2 and `/decompose` became Stage 3.
- `/decompose` still had a conceptual path to use TUYA as input basis, which risks visual-group hallucination.
- no TUYA-specific downstream permission matrix existed.
- no machine-readable TUYA concept fact schema existed.
- no explicit leakage probes existed for TUYA misuse in scoring, recommendation, final audit, or handoff.
- no repair route table existed for TUYA-derived contradictions or misuse.
- no self-audit, debug trace addendum, or Stage Anchor handoff block existed.
- pass criteria were helpful but not enforceable as a v1 contract.
```

Hardening response:

```text
This v1.0.0 contract adds input gates, source classification, concept-fact schema, downstream permissions, leakage probes, contradiction lifecycle, repair routes, self-audit, debug trace, and next-work anchor requirements.
```

---

## Contract Status Gate

This file may be treated as active only when all of these are true:

```yaml
TUYA_CONCEPT_REFERENCE_GATE:
  schema: ev4-tuya-concept-reference@1.0.0
  status: active_v1.0.0
  required_bindings:
    - ev4-rag-strategy-contract@1.0.0
    - ev4-research-payload@1.0.0
    - ev4-stage-anchor@1.1.0
    - ev4-partial-rerun@1.0.0
    - ev4-debug-trace@1.0.0
  required_controls:
    - source_type: internal_concept_reference
    - fact_class: project_conceptual_model
    - TUYA concept fact schema
    - downstream permission matrix
    - provisional/unknown/contradiction lifecycle
    - forbidden leakage probes
    - repair routes
    - self-audit
    - debug trace addendum
    - next-work anchor
```

If any required control is missing, this file is `active_but_repair_required` and must not be used to justify downstream decisions.

---

## Input Authorization Gate

A stage may use this file only if the Stage Anchor and active stage contract allow `internal_concept_reference` input for that stage.

Required input package:

```yaml
TUYA_INPUT_GATE:
  required:
    - valid ev4-stage-anchor@1.1.0
    - current stage source-access rule
    - source classification: internal_concept_reference
    - fact_class classification: project_conceptual_model
    - explicit allowed_use for the current stage
  fail_if:
    - target stage is /decompose and TUYA is being used as visual evidence
    - target stage is /score-evidence and TUYA is being used as an independent score booster
    - target stage is /recommend and TUYA is being used as a preference or tie-break signal
    - target stage is proving Elementor capability without official docs
    - target stage is claiming project-specific implementation behavior without user/export evidence
```

On failure, stop and emit a `TUYA_MISUSE_REPAIR_ANCHOR`.

---

## Trust Level

```yaml
TUYA_SOURCE_CLASSIFICATION:
  source_type: internal_concept_reference
  fact_class: project_conceptual_model
  trust_level: medium_high_for_pipeline_mindset
  valid_for:
    - vocabulary alignment
    - thinking order
    - normal-flow discipline
    - relative visual stage heuristic
    - responsive caution
    - design-system mindset
    - DOM/audit checklisting
    - regression-test inspiration
  not_valid_for:
    - official Elementor platform capability proof
    - screenshot visual grouping
    - exact widget settings
    - exact CSS values
    - score boosts
    - recommendation preference
    - tie breaking
    - project-specific runtime/export facts
```

Required supporting evidence by claim type:

| Claim type | Required source | TUYA role |
|---|---|---|
| Elementor can/cannot do something | official docs, release notes, developer docs | concept vocabulary only |
| current screenshot contains a visual group | screenshot/user-visible evidence | forbidden |
| current project uses a setting/export shape | export evidence / EDIS / user-provided project evidence | concept vocabulary only |
| architecture family is feasible | stage payload + approved platform facts | restricted conceptual check |
| score should increase | rubric + stage evidence | forbidden |
| final recommendation | audited Stage 5/6 outputs | forbidden as preference |
| audit risk taxonomy | active contracts + implementation payload | allowed as checklist support |

---

## TUYA Concept Fact Schema

Each TUYA-derived concept that travels downstream must be represented as a concept fact, not as general evidence.

```yaml
TUYA_CONCEPT_FACT:
  schema: ev4-tuya-concept-fact@1.0.0
  concept_id:
  source_id: TUYA_ELEMENTOR_V4_CONCEPTS
  source_type: internal_concept_reference
  source_file: knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
  concept_name:
  normalized_claim:
  fact_class: project_conceptual_model
  confidence: high | medium | low
  support_status: supported_internal_concept | provisional_internal_concept | contradicted_by_stage_evidence | superseded_by_official_or_export_evidence
  allowed_use:
  forbidden_use:
  downstream_visibility:
    /research: allowed | restricted | forbidden
    /decompose: allowed | restricted | forbidden
    /architectures: allowed | restricted | forbidden
    /score-evidence: allowed | restricted | forbidden
    /score-audit: allowed | restricted | forbidden
    /recommend: allowed | restricted | forbidden
    /build-tree: allowed | restricted | forbidden
    /implementation: allowed | restricted | forbidden
    /final-audit: allowed | restricted | forbidden
    /handoff-export: allowed | restricted | forbidden
    /e2e-test: allowed | restricted | forbidden
  contradiction_policy:
  repair_route:
```

No TUYA concept fact may omit `allowed_use`, `forbidden_use`, or `downstream_visibility`.

---

## Downstream Permission Matrix

| Pipeline stage | TUYA permission | Hard boundary |
|---|---|---|
| `/research` | Allowed as `internal_concept_reference`; classify and pin only | May not become official docs or project evidence |
| `/decompose` | Forbidden as visual evidence | Do not use TUYA to invent groups, classify meaningful/decorative nodes, or infer hidden content |
| `/architectures` | Restricted | May check architecture-family vocabulary and feasibility heuristics; may not choose winner |
| `/score-evidence` | Forbidden as independent score booster | Scores must come from rubric + stage evidence, not TUYA similarity |
| `/score-audit` | Allowed for leakage checks and conceptual consistency review | May not redesign or rescore except through audit protocol |
| `/recommend` | Forbidden as direct preference/tie-break | Recommendation must come from audited Stage 5/6 outputs |
| `/build-tree` | Restricted | May support naming, containment, and wrapper discipline after selected architecture is fixed |
| `/implementation` | Restricted | May support order-of-operations and risk cautions; may not invent exact settings/CSS |
| `/final-audit` | Restricted/allowed as checklist | May flag normal-flow, editability, responsive, DOM, or source-leakage risks |
| `/handoff-export` | Allowed as concept note only | Must not clean up blockers, flags, unknowns, or audit failures |
| `/e2e-test` | Allowed for negative-control probes | Must verify TUYA did not leak into forbidden stages |

Hard bans:

```text
/decompose must not use TUYA to see things.
/score-evidence must not use TUYA to raise a score directly.
/recommend must not use TUYA to prefer a candidate or break a tie.
/implementation must not use TUYA to invent exact settings.
/final-audit must not soften a defect because a TUYA pattern seems plausible.
/handoff-export must not remove TUYA-related flags or contradictions.
```

---

## Global Thinking Order

TUYA teaches a chain-like thinking order:

```text
Context
→ Structure
→ Flow / Display
→ Size / Units
→ Position / Layering
→ Responsive
→ Design System
→ DOM / Audit
```

EV4 use:

| TUYA concept | EV4 pipeline use |
|---|---|
| Context | `/intake`, `/research` scope, user constraints |
| Structure | `/decompose` output only from visible/user evidence; `/build-tree` tree shaping |
| Flow / Display | `/architectures` family feasibility; `/score-evidence` through rubric only |
| Size / Units | `/implementation` exact-value restraint and responsive carry-forward |
| Position / Layering | A03/A04 feasibility, relative visual stage, overlay containment |
| Responsive | responsive caps, mobile unknown propagation, Stage Anchor carry-forward |
| Design System | class/variable/component discipline after architecture selection |
| DOM / Audit | final audit, wrapper budget, source-leakage checks |

Operational rule:

```text
TUYA may define the order of questions.
TUYA may not answer project-specific questions without stage evidence.
```

---

## Confidence Labels Alignment

TUYA uses three thinking labels:

```text
confirmed
provisional
unknown
```

Map them into EV4 labels:

| TUYA label | EV4 nearest equivalent | Pipeline rule |
|---|---|---|
| confirmed | supported internal concept | May support vocabulary/checklist only |
| provisional | provisional internal concept / PARTIALLY_SUPPORTED_EVIDENCE | May guide exploration, not final decisions |
| unknown | unresolved_unknown / ABSENT_EVIDENCE | Must not become score, exact setting, or structural certainty |

Important distinction:

```text
provisional ≠ confirmed
unknown ≠ contradicted
internal concept ≠ external evidence
```

---

## Provisional / Unknown / Contradicted Lifecycle

A TUYA-derived provisional item is not permanently valid. Stronger stage evidence, official docs, export evidence, or user constraints override it.

| Previous state | New evidence | New label | Required action |
|---|---|---|---|
| `provisional_internal_concept` | visible/user evidence supports it | `PARTIALLY_SUPPORTED_EVIDENCE` or `SUPPORTED_EVIDENCE` depending on source | Update confidence_delta and allowed downstream use |
| `provisional_internal_concept` | evidence remains incomplete | `PARTIALLY_SUPPORTED_EVIDENCE` | Keep non-final and carry forward |
| `provisional_internal_concept` | visible/user evidence conflicts | `CONTRADICTED_EVIDENCE` | Lower/block dependent candidate; record contradiction; route repair |
| `provisional_internal_concept` | official docs conflict | `superseded_by_official_source` | Use official docs for capability, keep TUYA as concept note only |
| `provisional_internal_concept` | export evidence conflicts | `superseded_by_export_evidence` | Use export evidence for project observation; invalidate dependent implementation/audit payloads |
| `unknown` | later evidence confirms | `SUPPORTED_EVIDENCE` | Resolve unknown and update Stage Anchor |
| `unknown` | later evidence conflicts with an assumption | `CONTRADICTED_EVIDENCE` against the assumption | Do not treat the original unknown as contradiction by itself |

Operational rule:

```text
A TUYA concept may be used as a hypothesis generator.
It must be replaced by stronger evidence when stronger evidence exists.
If contradicted, the dependent candidate, score, tree node, setting, or audit status must be repaired from the earliest owning stage.
```

---

## Context / Structure / Node Vocabulary

Use these terms consistently:

| Term | Meaning in pipeline |
|---|---|
| Context | Goal, constraints, evidence scope, and user/project limits |
| Structure | Nested hierarchy of section, containers, groups, and widgets |
| Node | A distinct element in the structure tree; not necessarily a DOM node |
| Stage | A controlled area that contains visual/overlay elements |
| Visual Core | Main visual object or visual cluster that explains the section |
| Decoration | A visual layer that should not control content layout or reading order |
| Meaningful Content | Text, image, icon, CTA, card, data, or label that conveys information |

Stage rule:

```text
A Stage is useful only when it creates containment, layering control, or visual grouping.
Do not create a Stage just to make the tree look sophisticated.
```

Boundary:

```text
The vocabulary can be reused.
The actual current nodes must come from visible/user evidence or approved upstream payloads.
```

---

## Position / Relative / Absolute Rules

TUYA lesson 12 strongly aligns with EV4 overlay policy.

Core rule:

```text
Content stays in Flow.
Floating decoration lives inside a named relative Stage.
```

Allowed conceptual pattern:

```text
Section
├── Content Group        ← normal flow
└── Visual Stage         ← normal flow + position: relative
    ├── Visual Core      ← normal flow or controlled visual layer
    ├── Orbit Node       ← absolute only if decoration/controlled visual
    └── Connector Layer  ← absolute/SVG only if decoration/controlled visual
```

Forbidden conceptual pattern:

```text
Section
├── Copy position:absolute
├── Logo Strip position:absolute
└── CTA position:absolute
```

Reason:

- content height collapses or becomes unreliable;
- long text collides;
- mobile requires manual offset repair;
- reading order and editability degrade.

Stage boundary:

```text
TUYA may flag absolute-position risk.
TUYA may not decide that a specific observed node is decoration-only unless /decompose or later approved evidence supports it.
```

---

## Layering / Z-index / Overflow Rules

Use layer logic only after structure and flow are clear.

Rules:

- Layering must not compensate for a broken structure.
- Z-index must not decide content order.
- Overflow should be declared as a visual containment decision, not a hidden patch.
- Any floating node, badge, connector, orbit, or glow must declare its containing Stage.

Carry forward as unknown when unclear:

```text
z-index order
connector coordinates
mobile overlay behavior
overflow containment
floating card collision risk
```

Forbidden shortcut:

```text
Do not convert a TUYA layering heuristic into exact z-index, CSS selector, offset, breakpoint, or hidden-overflow setting.
```

---

## Responsive Inheritance Rules

TUYA responsive concepts align with EV4 responsive-risk propagation and Stage 4 caps.

Rules:

- Desktop evidence may support inheritance potential, not guaranteed mobile success.
- Normal-flow structures usually have better inheritance potential than fixed/absolute structures.
- If mobile evidence is absent, carry responsive unknowns and apply active cap rules where the scoring contract requires it.
- If a visual core, connector layer, floating card, or absolute node exists, mobile behavior must be explicitly carried into Stage Anchor and `/implementation`.

Forbidden:

```text
Do not silently hide visual layers on mobile.
Do not assume desktop offsets work on mobile.
Do not duplicate the section for mobile unless Stage 4/5/6 allowed it.
Do not mark responsive risk resolved without evidence.
```

---

## Design System Rules

TUYA lessons on Classes, Variables, and Components align with EV4 Design-System Fit only as conceptual guidance.

Rules:

- Use variables for repeated colors, spacing, typography, radius, shadows, and stable tokens when the implementation payload has enough evidence.
- Use reusable classes for repeated visual patterns after reuse is confirmed.
- Use local classes for one-off positioning or section-specific exceptions.
- Do not promote a class to global until reuse or design-system value is confirmed.
- Components should be created after real variation patterns are known.

EV4 mapping:

| TUYA design-system concept | EV4 use |
|---|---|
| Local Class | one-off stage, node, or exception styling |
| Global Class | repeated card, badge, CTA, media pattern |
| Variables | stable repeated values across sections |
| Components | repeated structures with real variants |

Forbidden shortcut:

```text
TUYA cannot prove that Elementor variables/classes/components are available or configured in the user's site.
Official docs or export/user evidence must ground capability and project-specific state.
```

---

## Performance / DOM / Audit Rules

TUYA treats performance as a result of structure, media, fonts, interactions, CSS, JS, third-party dependencies, and measurement.

EV4 use:

- Performance is not only node count.
- DOM depth, extra wrappers, visual assets, fonts, animations, third-party widgets, and custom code all affect risk.
- A deep tree is acceptable only with clear structural justification.
- A single flat static image may look visually accurate but fails editability and often accessibility.
- Audit must check the relationship between structure, responsive behavior, media, and maintainability.

Allowed stages:

- `/score-audit`: leakage and scoring-process review.
- `/build-tree`: wrapper-budget and structure-panel clarity check.
- `/implementation`: asset/CSS/animation risk carry-forward.
- `/final-audit`: final risk verification.

Forbidden shortcut:

```text
Do not use TUYA to declare actual performance pass/fail without implementation/export/runtime evidence.
```

---

## TUYA Project Pattern: Smart Visual + Content Flow

The TUYA workbook uses a continuing smart-home style reference with text/logos on one side and a visual cloud/orbit/node system on the other.

This pattern is useful as an internal calibration case for:

- visual core vs meaningful content;
- normal-flow content + relative visual stage;
- decorative connector/orbit logic;
- responsive risk propagation;
- build-tree naming and containment.

This pattern must not be treated as the only valid architecture. It is a calibration reference, not a universal template.

Negative rule:

```text
A screenshot resembling the TUYA pattern does not automatically justify A03/A04, absolute overlays, SVG connectors, or a specific build tree.
```

---

## Stage-Specific Use Rules

### `/research`

Allowed:

- classify this file as `internal_concept_reference`;
- produce TUYA concept facts with downstream visibility;
- compare concept vocabulary against official docs only for terminology clarity.

Forbidden:

- claiming official Elementor behavior from TUYA;
- interpreting screenshots;
- scoring or recommending.

### `/decompose`

Forbidden:

- using TUYA concepts to infer visual groups;
- using TUYA to classify a specific node as meaningful/decorative;
- using TUYA to fill unseen screenshot content.

Allowed only as a boundary reminder:

```text
Do not use RAG/TUYA/docs as visual evidence.
```

### `/architectures`

Allowed:

- use TUYA as a restricted conceptual check for architecture-family coherence;
- flag misuse of stage/overlay logic;
- preserve normal-flow discipline as a design constraint.

Forbidden:

- final recommendation language;
- score totals;
- winner selection;
- hidden preference signals.

### `/score-evidence`

Forbidden:

- score boosts from TUYA similarity;
- using TUYA as independent evidence for feasibility, editability, accessibility, or performance.

Allowed:

- reference active project rules already admitted by stage contracts.

### `/score-audit`

Allowed:

- audit for TUYA leakage;
- detect contradiction between TUYA-derived assumptions and Stage 3/4 evidence;
- route repair to the earliest owning stage.

Forbidden:

- redesigning candidates;
- rewriting scores except through audit protocol.

### `/recommend`

Forbidden:

- direct TUYA preference;
- tie-breaking based on TUYA pattern similarity;
- upgrading a candidate because it looks more like TUYA.

Allowed:

- preserve audit flags about TUYA leakage or concept mismatch.

### `/build-tree`

Allowed:

- use TUYA vocabulary for naming and containment after recommendation is stable;
- preserve normal-flow content and relative visual stage containment;
- carry responsive/overlay unknowns.

Forbidden:

- re-architecting;
- converting a calibration pattern into a universal tree;
- inventing exact widget settings.

### `/implementation`

Allowed:

- use TUYA as an order-of-operations checklist: structure → flow → size → position → responsive → design system → audit;
- carry risks into settings/CSS/accessibility maps.

Forbidden:

- exact CSS values, breakpoints, z-indexes, animations, or widget controls invented from TUYA.

### `/final-audit`

Allowed:

- audit normal-flow preservation, editability, responsive risk, DOM clarity, source leakage, and TUYA misuse.

Forbidden:

- softening blocker/high findings because TUYA pattern fit seems plausible.

### `/handoff-export`

Allowed:

- package TUYA concept notes, source limits, and audit flags.

Forbidden:

- removing unknowns, contradictions, blockers, or flags.

### `/e2e-test`

Allowed:

- test for TUYA leakage across all stages;
- verify negative-control probes and repair routes.

Forbidden:

- treating E2E output as proof of live Elementor/browser behavior unless the fixture includes such evidence.

---

## Forbidden Leakage Probes

Any E2E, final audit, or debug run must probe for these misuse patterns:

| Probe ID | Misuse pattern | Expected result |
|---|---|---|
| TUYA-LP-001 | TUYA used by `/decompose` to invent visual group | fail + repair to `/decompose` |
| TUYA-LP-002 | TUYA used to classify specific screenshot node as decoration-only | fail + repair to `/decompose` or `/architectures` |
| TUYA-LP-003 | TUYA used as official Elementor capability proof | fail + repair to `/research` |
| TUYA-LP-004 | TUYA used to raise Stage 5 score | fail + repair to `/score-evidence` |
| TUYA-LP-005 | TUYA used to break Stage 7 tie | fail + repair to `/recommend` |
| TUYA-LP-006 | TUYA pattern converted directly into final build tree | fail + repair to `/build-tree` |
| TUYA-LP-007 | TUYA used to invent CSS values or breakpoints | fail + repair to `/implementation` |
| TUYA-LP-008 | TUYA used to soften final-audit blocker/high | fail + repair to `/final-audit` |
| TUYA-LP-009 | TUYA contradiction removed from handoff | fail + repair to `/handoff-export` |
| TUYA-LP-010 | TUYA unknown silently resolved without evidence | fail + repair to earliest owner stage |

---

## Repair Routes

| Defect | Earliest safe repair stage | Invalidates |
|---|---|---|
| TUYA source classified as official docs | `/research` | all downstream payloads that used the claim |
| TUYA used for visual grouping | `/decompose` | `/architectures` onward |
| TUYA-derived node classification contradicted by visible evidence | `/decompose` or `/architectures` depending on owner | affected candidate onward |
| TUYA used as score booster | `/score-evidence` | `/score-audit` onward |
| TUYA score leakage missed by audit | `/score-audit` | `/recommend` onward |
| TUYA used as tie-break/preference | `/recommend` | `/build-tree` onward |
| TUYA pattern directly converted into tree | `/build-tree` | `/implementation` onward |
| TUYA used to invent settings/CSS | `/implementation` | `/final-audit` onward |
| TUYA contradiction softened by final audit | `/final-audit` | `/handoff-export` onward |
| TUYA flags dropped in handoff | `/handoff-export` | handoff only; upstream remains reusable if payloads are valid |

Partial rerun rule:

```text
Use the earliest owning stage. Do not rerun the full pipeline unless the owning-stage change invalidates all downstream payloads.
```

---

## TUYA_CONCEPT_REFERENCE_PAYLOAD

```yaml
TUYA_CONCEPT_REFERENCE_PAYLOAD:
  schema: ev4-tuya-concept-reference@1.0.0
  status: active_v1.0.0
  source_file: knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
  source_type: internal_concept_reference
  fact_class: project_conceptual_model
  aligned_contracts:
    - ev4-rag-strategy-contract@1.0.0
    - ev4-research-payload@1.0.0
    - ev4-stage-anchor@1.1.0
    - ev4-partial-rerun@1.0.0
    - ev4-debug-trace@1.0.0
  concept_fact_schema: ev4-tuya-concept-fact@1.0.0
  downstream_permission_matrix: present
  leakage_probes: present
  repair_routes: present
  self_audit: present
  debug_trace_addendum: present
  next_work_anchor: present
```

---

## Self-Audit Checklist

Before using this file as an active contract, verify:

- [ ] `source_type` is exactly `internal_concept_reference`.
- [ ] `fact_class` is exactly `project_conceptual_model`.
- [ ] TUYA is not used as official Elementor documentation.
- [ ] TUYA is not used as export/runtime evidence.
- [ ] TUYA is forbidden for `/decompose` visual grouping.
- [ ] TUYA is forbidden as a Stage 5 score booster.
- [ ] TUYA is forbidden as a Stage 7 preference/tie-break signal.
- [ ] Exact settings, breakpoints, CSS values, z-indexes, and widget controls are not invented from TUYA.
- [ ] Provisional/unknown/contradicted lifecycle is preserved.
- [ ] Contradictions trigger repair routes instead of being smoothed.
- [ ] Stage Anchor v1.1 fields preserve TUYA flags and confidence deltas.
- [ ] EV4_DEBUG_TRACE logs TUYA concept use without exposing hidden reasoning.
- [ ] Handoff preserves TUYA limitations, flags, contradictions, and unknowns.

Pass condition:

```text
This file is active only if every applicable checklist item passes. If one fails, mark `active_but_repair_required` and repair this file or the consuming stage.
```

---

## EV4_DEBUG_TRACE Addendum

When a stage uses this file, add a compact external trace item:

```json
{
  "schema": "ev4-debug-trace@1.0.0",
  "stage": "<current-stage>",
  "decision_log": [
    {
      "decision_id": "TUYA-D-001",
      "decision": "internal concept reference used | internal concept reference rejected | leakage blocked | contradiction routed",
      "target": "<concept-or-stage-output>",
      "basis": {
        "evidence_ids": [],
        "rule_ids": ["ev4-tuya-concept-reference@1.0.0"],
        "unknown_ids": []
      },
      "confidence": "confirmed | inferred | uncertain | blocked",
      "downstream_effect": "<allowed-use-or-repair-route>"
    }
  ],
  "evidence_map": [
    {
      "evidence_id": "TUYA-E-001",
      "source_stage": "research",
      "source_payload": "TUYA_CONCEPT_REFERENCE_PAYLOAD",
      "claim_supported": "TUYA provides internal conceptual guidance only",
      "evidence_label": "SUPPORTED_EVIDENCE",
      "quote_or_summary": "source_type internal_concept_reference; fact_class project_conceptual_model"
    }
  ],
  "repair_route": "<earliest-safe-repair-stage-if-needed>",
  "handoff_payload_schema": "ev4-tuya-concept-reference@1.0.0"
}
```

Do not log hidden chain-of-thought. Log only external decisions, source classification, allowed use, blocked misuse, and repair routes.

---

## Pass Criteria

A stage uses this reference correctly only if:

- TUYA concepts are cited as internal conceptual guidance.
- official docs or export evidence are used for platform/runtime claims.
- visible/user evidence or approved payloads are used for project-specific behavior.
- provisional and unknown items remain visible.
- provisional claims are upgraded, downgraded, resolved, or contradicted when later evidence requires it.
- content remains in normal flow unless a later audited decision says otherwise.
- overlay layers stay inside named relative stages.
- build-tree decisions preserve editability and Structure Panel clarity.
- source-access boundaries from RAG Strategy v1.0.0 remain intact.
- debug trace and Stage Anchor preserve TUYA limitations and flags.

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
- confidence_delta:
  - item: TUYA source classification
    previous_confidence: provisional
    current_confidence: confirmed
    direction: resolved
    reason: v1.0.0 source classification and downstream permission matrix added
    downstream_impact: RAG/TUYA leakage checks can now enforce source boundaries
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
