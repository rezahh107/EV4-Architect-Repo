# TUYA Elementor V4 Concepts — Internal Pipeline Reference

Status: active_reference
Version: 0.2.0
Source: `TUYA_Standalone_Workbook_v32_0_0_lessons_1_21_release_candidate_v25.html`
Applies to: `/research`, `/architectures`, `/build-tree`, `/implementation`, `/final-audit`

---

## Purpose

This file extracts pipeline-relevant concepts from the TUYA Elementor V4 workbook.

It is not a replacement for official Elementor documentation, export evidence, or the staged EV4 pipeline. It is an internal conceptual reference that helps the model keep the same mental model across architecture, tree-building, implementation, and audit.

Core rule:

```text
Use TUYA concepts to guide thinking order and terminology.
Do not use TUYA concepts to bypass evidence, scoring, audit, or recommendation gates.
```

---

## Trust Level

```text
source_type: internal_course_reference
fact_class: project_conceptual_model
trust_level: medium_high_for_pipeline_mindset
not_valid_for: proving platform capability by itself
```

TUYA concepts are useful for EV4 project reasoning because they encode the same learning path and mental model used by this prompt pack.

However:

- Official Elementor documentation is still required for platform capability claims.
- Real Elementor exports / EDIS are still required for implementation observations.
- User constraints are still required for project-specific behavior.

---

## Global Thinking Order

The workbook teaches a chain-like thinking order:

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

EV4 pipeline use:

| TUYA concept | EV4 pipeline use |
|---|---|
| Context | Stage 1 `/intake`; Stage 2 input basis |
| Structure | Stage 2 visible groups; Stage 7 build tree |
| Flow / Display | Stage 3 architecture families; Stage 4 Normal-Flow Safety |
| Size / Units | Stage 8 implementation constraints; responsive checks |
| Position / Layering | Stage 3 A03/A04; Stage 7 overlay containment |
| Responsive | Stage 4 responsiveness scoring; Stage 8 breakpoint implementation |
| Design System | Stage 4 Design-System Fit; Stage 7 class/variable hooks |
| DOM / Audit | Stage 4 performance/clarity; Stage 9 final audit |

Required behavior:

```text
Before visual styling decisions, reason in this order.
If a later decision contradicts an earlier layer, stop and mark a conflict.
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
| confirmed | SUPPORTED_EVIDENCE / user_provided / confirmed_from_image | May support a limited decision |
| provisional | INFERRED_EVIDENCE / PARTIALLY_SUPPORTED_EVIDENCE | May support a candidate, not a final decision |
| unknown | ABSENT_EVIDENCE / unresolved_unknown | Must not be converted into final score, exact setting, or structural certainty |

Important distinction:

```text
provisional ≠ confirmed
unknown ≠ contradicted
```

### Provisional-to-Contradicted Transition Rule

A `provisional` item is not permanently provisional. If a later stage receives stronger evidence that directly conflicts with the provisional claim, the item must be reclassified as `CONTRADICTED_EVIDENCE`.

Required transition logic:

| Previous state | New evidence | New EV4 label | Required action |
|---|---|---|---|
| `provisional` | Later evidence supports it | `SUPPORTED_EVIDENCE` or `PARTIALLY_SUPPORTED_EVIDENCE` | Update `confidence_delta` in Stage Anchor |
| `provisional` | Later evidence is still incomplete | `PARTIALLY_SUPPORTED_EVIDENCE` | Keep as non-final and carry forward |
| `provisional` | Later evidence directly conflicts | `CONTRADICTED_EVIDENCE` | Lower score or block dependent decision; record contradiction |
| `unknown` | Later evidence confirms | `SUPPORTED_EVIDENCE` | Resolve unknown and update Anchor |
| `unknown` | Later evidence conflicts with an assumed claim | `CONTRADICTED_EVIDENCE` against the assumed claim | Do not treat the original unknown as contradiction by itself |

Operational rule:

```text
A provisional TUYA-derived heuristic may guide exploration.
It must be replaced by Stage evidence when Stage evidence is stronger.
If contradicted, the downstream candidate, score, tree node, or implementation setting must be repaired.
```

Example:

```text
TUYA concept says a visual node may be decoration inside a relative visual stage.
Stage 2 observes that this node carries readable product data.
Result: the decoration assumption becomes CONTRADICTED_EVIDENCE for any candidate that treats it as decoration-only.
```

---

## Context / Structure / Node Vocabulary

Use these terms consistently:

| Term | Meaning in pipeline |
|---|---|
| Context | What the section is trying to accomplish and what constraints exist |
| Structure | The nested hierarchy of section, containers, groups, and widgets |
| Node | A distinct element in the structure tree, not necessarily a DOM node |
| Stage | A controlled area that contains visual/overlay elements |
| Visual Core | The main visual object or visual cluster that explains the section |
| Decoration | A visual layer that should not control content layout or reading order |
| Meaningful Content | Text, image, icon, CTA, card, data, or label that conveys information |

Stage rule:

```text
A Stage is useful only when it creates containment, layering control, or visual grouping.
Do not create a Stage just to make the tree look sophisticated.
```

---

## Position / Relative / Absolute Rules

TUYA lesson 12 strongly aligns with EV4 overlay policy.

Core rule:

```text
Content stays in Flow.
Floating decoration lives inside a named relative Stage.
```

Use this for:

- Stage 3 A03 — Relative Stage + Absolute Overlay Architecture.
- Stage 3 A04 — SVG Connector Layer Architecture.
- Stage 4 Normal-Flow Safety.
- Stage 4 Overlay Containment.
- Stage 7 build-tree overlay stage construction.
- Stage 8 implementation constraints.

Allowed pattern:

```text
Section
├── Content Group        ← normal flow
└── Visual Stage         ← normal flow + position: relative
    ├── Visual Core      ← normal flow or controlled visual layer
    ├── Orbit Node       ← absolute only if decoration/controlled visual
    └── Connector Layer  ← absolute/SVG only if decoration/controlled visual
```

Forbidden pattern:

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

---

## Responsive Inheritance Rules

TUYA's responsive lessons align with Elementor V4 responsive inheritance and EV4 Stage 4 caps.

Rules:

- Desktop evidence may support inheritance potential, not guaranteed mobile success.
- A normal-flow structure has better inheritance potential than a fixed/absolute structure.
- If mobile evidence is absent, do not automatically mark Responsiveness as `?`, but do apply score caps and carry unknowns forward.
- If a visual core, connector layer, floating cards, or absolute nodes exist, mobile behavior must be explicitly carried into Stage Anchor and Stage 8.

Forbidden:

```text
Do not silently hide visual layers on mobile.
Do not assume desktop offsets work on mobile.
Do not duplicate the section for mobile unless Stage 4/5/6 allowed it.
```

---

## Design System Rules

TUYA lessons on Classes, Variables, and Components align with EV4 Design-System Fit.

Rules:

- Use variables for repeated colors, spacing, typography, radius, shadows, and stable tokens.
- Use reusable classes for repeated visual patterns.
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

---

## Performance / DOM / Audit Rules

TUYA lesson 20 treats performance as a result of structure, media, fonts, interactions, CSS, JS, third-party dependencies, and measurement.

EV4 rules:

- Performance is not only node count.
- DOM depth, extra wrappers, visual assets, fonts, animations, third-party widgets, and custom code all affect risk.
- A deep tree is acceptable only with clear structural justification.
- A single flat static image may look visually accurate but fails editability and often accessibility.
- Audit must check the relationship between structure, responsive behavior, media, and maintainability.

Use for:

- Stage 4 Performance criterion.
- Stage 7 wrapper budget.
- Stage 8 asset and CSS constraints.
- Stage 9 final audit.

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

---

## How Stages May Use This File

### `/research`

Use it to retrieve internal conceptual definitions and compare them with official docs.

### `/architectures`

Use it to check whether architecture families match the TUYA thinking order and whether overlay/stage logic is being misused.

### `/build-tree`

Use it to maintain structure-first naming, stage containment, wrapper justification, and class strategy.

### `/implementation`

Use it to prevent jumping from visual similarity to arbitrary settings. Implementation must preserve the TUYA order: structure → flow → size → position → responsive → design system → audit.

### `/final-audit`

Use it as a conceptual checklist for DOM depth, normal flow, mobile fragility, editability, and design-system consistency.

---

## Forbidden Uses

Do not use this file to:

- prove an Elementor platform capability without official docs;
- infer exact widget settings from a screenshot;
- replace Stage 2 decomposition;
- replace Stage 4 scoring;
- skip Stage 5 audit;
- jump from TUYA pattern similarity to a final build tree;
- promote provisional values to confirmed implementation;
- keep a provisional claim unchanged after stronger evidence contradicts it.

---

## Pass Criteria

A stage uses this reference correctly only if:

- TUYA concepts are cited as internal conceptual guidance;
- official docs or export evidence are used for platform/runtime claims;
- provisional and unknown items remain visible;
- provisional claims are upgraded, downgraded, resolved, or contradicted when later evidence requires it;
- content remains in normal flow unless a later audited decision says otherwise;
- overlay layers stay inside named relative stages;
- build-tree decisions preserve editability and Structure Panel clarity.
