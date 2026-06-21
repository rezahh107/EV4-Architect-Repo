# Elementor Knowledge Base / RAG Strategy

Status: draft_active
Version: 0.1.0
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
- identify documentation-backed constraints.

### `/build-tree`

- map selected architecture concepts to plausible Elementor containers/widgets;
- verify naming and structure against known Elementor concepts;
- avoid inventing widgets or settings.

### `/implementation`

- ground widget settings, responsive controls, asset handling, and scoped CSS boundaries;
- distinguish documented behavior from project-specific implementation assumptions.

---

## Source Classes

Preferred source classes:

1. Official Elementor documentation.
2. Version-pinned Elementor release notes when relevant.
3. Verified exported Elementor JSON or real project exports, if available.
4. Project defaults and EV4 contracts in this repository.
5. User-provided implementation constraints.

Lower-trust sources may be used only as secondary context and must not override official docs, exports, or project rules.

---

## Platform Capability vs Project-Specific Behavior

Every retrieved fact must be classified as one of:

```text
platform_capability
project_default
project_specific_behavior
implementation_observation
unsupported_claim
```

Rules:

- `platform_capability` means Elementor can do something in general.
- `project_default` means this project allows or disallows something.
- `project_specific_behavior` means the current section/project has a confirmed requirement.
- `implementation_observation` means real exported/runtime evidence confirms a behavior.
- `unsupported_claim` means the model has no reliable source and must not treat it as fact.

---

## Retrieval Output Shape

A `/research` or RAG-supported stage should include:

```text
RETRIEVED FACT
- source_id:
- source_type: official_docs | release_notes | export_evidence | project_contract | user_input | secondary_source
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
- treat undocumented behavior as confirmed.

---

## Pass Criteria

The knowledge base strategy is valid only if:

- every retrieved fact has a source and fact class;
- platform capability is not confused with project-specific behavior;
- docs support Stage 3/7/8 decisions but do not replace Stage 2/4/5/6;
- unsupported claims become `unknown`, not implementation facts;
- future export evidence is allowed to strengthen implementation grounding.
