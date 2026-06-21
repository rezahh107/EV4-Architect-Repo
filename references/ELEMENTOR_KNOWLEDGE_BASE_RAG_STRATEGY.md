# Elementor Knowledge Base / RAG Strategy

Status: draft_active
Version: 0.3.0
Applies to: `/research`, `/architectures`, `/build-tree`, `/implementation`

---

## Purpose

A structured Elementor knowledge base can improve factual grounding, but it must not replace the EV4 pipeline.

Core rule:

```text
Use knowledge retrieval to ground platform capability claims.
Do not use it to skip decomposition, scoring, audit, or recommendation gates.
```

---

## Why This Is Not a Replacement for the Pipeline

A direct path such as:

```text
Elementor docs + screenshot → final build tree
```

is not equivalent to the staged EV4 pipeline.

It skips:

- meaningful vs decorative classification;
- architecture enumeration;
- evidence-bound scoring;
- independent score audit;
- tie and recommendation discipline;
- debug trace and repair routing.

Therefore, RAG may support a stage, but it must not collapse the pipeline into a single visual-to-tree guess.

---

## Stage Source Access Matrix

This matrix controls which knowledge sources may influence each stage. It is mandatory because otherwise retrieval can leak conceptual guidance into scoring or recommendation and bias the pipeline.

| Stage | Primary sources allowed | Restricted / forbidden sources | Rule |
|---|---|---|---|
| Stage 1 `/intake` | User constraints, project defaults | RAG docs only if user asks a platform-capability question | Do not research unless a blocking constraint depends on platform capability. |
| Stage 2 `/decompose` | Screenshot/image, user description, user-provided constraints, Stage Anchor | TUYA, Elementor docs, RAG concepts as decision sources | Decompose what is visible/provided only. Do not use docs to invent visual groups. |
| Stage 3 `/architectures` | Stage 2 output, Stage Anchor, project defaults, TUYA concepts, official Elementor docs, RAG facts | Final recommendation language, scoring totals | RAG may verify architecture feasibility and candidate families, not choose a winner. |
| Stage 4 `/score-evidence` | Rubric, Stage 2 output, Stage 3 candidates, Stage Anchor, scoring calibration cases | TUYA as independent scoring evidence; broad RAG docs as direct score boosters | Score only evidence and rubric. TUYA can explain terminology but cannot raise a score. |
| Stage 5 `/score-audit` | Stage 4 report, Audit_Trail_Payload, Rubric, Stage 2/3 spot-checks, Stage Anchor | New architecture evidence except for audit spot-check | Audit the scoring process, not the section design. |
| Stage 6 `/recommend` | Audited Stage 4/5 outputs, Tie_Handoff_Payload, Stage Anchor | New RAG claims, new visual assumptions, direct TUYA preference | Recommend only among audited eligible candidates. |
| Stage 7 `/build-tree` | Stage 6 Recommendation_Payload, Stage Anchor, TUYA concepts, Elementor docs, naming contract | New candidate selection, direct screenshot reinterpretation | Build the tree from the selected architecture; do not re-architect. |
| Stage 8 `/implementation` | Stage 7 Build_Tree_Payload, Stage Anchor, official Elementor docs, widget/settings references, TUYA concepts, export evidence if available | New recommendation, new scoring | Implement the approved tree with documented settings and scoped constraints. |
| Stage 9 `/final-audit` | Stage 8 output, Stage 7 tree, Stage 6 recommendation, Rubric, TUYA audit concepts, export evidence if available | New architecture generation | Audit implementation against the approved tree and prior gates. |
| Stage 10 `/handoff-export` | Final audited outputs, debug traces, anchors, payloads | New decisions | Package the run; do not change decisions. |

Hard rule:

```text
Stage 4 must not use TUYA or RAG to improve a candidate score unless the same fact is already present in Stage 2/3 evidence or official project rules.
Stage 2 must not use RAG to see things that are not visible or user-provided.
Stage 6 must not use RAG to break a tie unless Stage 5 explicitly requested a source-backed clarification and the result is routed through the tie protocol.
```

---

## What the Knowledge Base Can Safely Do

The knowledge base may support:

### `/research`

- retrieve official Elementor capabilities;
- pin documentation source and retrieval date;
- separate platform capability from project-specific behavior;
- mark unsupported or undocumented claims as `unknown`.

### `/architectures`

- verify whether a proposed architecture family is Elementor-native, widget-native, or custom/hybrid;
- check whether a candidate depends on features that require Elementor Pro or third-party plugins;
- identify documentation-backed constraints;
- use internal TUYA concepts to preserve the structure-first thinking order.

### `/build-tree`

- map selected architecture concepts to plausible Elementor containers/widgets;
- verify naming and structure against known Elementor concepts;
- avoid inventing widgets or settings;
- use TUYA concepts for Structure Panel clarity, relative stage containment, wrapper discipline, and class/variable strategy.

### `/implementation`

- ground widget settings, responsive controls, asset handling, and scoped CSS boundaries;
- distinguish documented behavior from project-specific implementation assumptions;
- use TUYA concepts as a conceptual checklist for structure → flow → size → position → responsive → design system → audit.

---

## Internal Concept Reference Layer

The repository may include project-authored conceptual references, such as:

```text
knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
```

This source class is useful for preserving the EV4 mental model, especially when the user wants reports and instructions in Persian.

Rules:

- Internal concept references may define project vocabulary, thinking order, and safe heuristics.
- Internal concept references may not prove Elementor platform capability by themselves.
- Internal concept references may not override official Elementor docs, exported Elementor evidence, project defaults, or user constraints.
- Internal concept references should be classified as `project_conceptual_model`, not `official_docs`.

Allowed use examples:

```text
Use TUYA to remember: content stays in normal flow; floating nodes live inside a relative visual stage.
Use official Elementor docs to verify: Structure window behavior, container capabilities, responsive inheritance.
Use export evidence to verify: exact runtime/project behavior.
```

---

## Source Classes

Preferred source classes:

1. Official Elementor documentation.
2. Version-pinned Elementor release notes when relevant.
3. Verified exported Elementor JSON or real project exports, if available.
4. Project defaults and EV4 contracts in this repository.
5. Internal concept references, including `knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md`.
6. User-provided implementation constraints.

Lower-trust sources may be used only as secondary context and must not override official docs, exports, or project rules.

---

## Platform Capability vs Project-Specific Behavior

Every retrieved fact must be classified as one of:

```text
platform_capability
project_default
project_conceptual_model
project_specific_behavior
implementation_observation
unsupported_claim
```

Rules:

- `platform_capability` means Elementor can do something in general.
- `project_default` means this project allows or disallows something.
- `project_conceptual_model` means an internal EV4/TUYA concept guides reasoning but does not prove platform behavior.
- `project_specific_behavior` means the current section/project has a confirmed requirement.
- `implementation_observation` means real exported/runtime evidence confirms a behavior.
- `unsupported_claim` means the model has no reliable source and must not treat it as fact.

---

## Retrieval Output Shape

A `/research` or RAG-supported stage should include:

```text
RETRIEVED FACT
- source_id:
- source_type: official_docs | release_notes | export_evidence | project_contract | internal_concept_reference | user_input | secondary_source
- retrieved_claim:
- applies_to_stage:
- fact_class:
- confidence: high | medium | low
- limitation:
- allowed_use:
```

---

## EDIS / Export Evidence Layer

Future enhancement:

```text
EDIS = Elementor Document/Export Inspection System
```

If real Elementor exports are available, export evidence has higher implementation value than generic documentation for project-specific behavior.

Example:

- docs can say a feature exists;
- export evidence can show how the feature is represented in real Elementor data;
- the pipeline decides whether that feature is appropriate for the current section.

EDIS should support Stage 8 and Stage 9, not bypass Stage 2 through Stage 6.

---

## Forbidden Uses

Do not use the knowledge base to:

- infer visual hierarchy directly from a screenshot;
- classify meaningful vs decorative content without Stage 2 evidence;
- select a final architecture before Stage 6;
- bypass scoring or audit;
- fabricate exact widget settings not present in docs or exports;
- treat undocumented behavior as confirmed;
- treat TUYA internal concepts as official Elementor platform documentation;
- allow Stage 4 or Stage 6 to use conceptual references as hidden preference signals.

---

## Pass Criteria

The knowledge base strategy is valid only if:

- every retrieved fact has a source and fact class;
- the Stage Source Access Matrix is followed;
- platform capability is not confused with project-specific behavior;
- internal concept references are classified as conceptual guidance, not official capability proof;
- docs support Stage 3/7/8 decisions but do not replace Stage 2/4/5/6;
- unsupported claims become `unknown`, not implementation facts;
- future export evidence is allowed to strengthen implementation grounding;
- Stage 4 scoring and Stage 6 recommendation remain bound to their approved inputs and cannot import new RAG preference signals.
