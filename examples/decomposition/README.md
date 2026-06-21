# Decomposition Example Bank

Status: active  
Stage: Stage 2 — `/decompose`  
Purpose: few-shot guidance + calibration for Controlled Visual Role Decomposition  
Minimum examples: 5  
Current examples: 12  
Authoring standard: `examples/decomposition/EXAMPLE_AUTHORING_STANDARD.md`

---

## Why this exists

Stage 2 is intentionally limited. It converts a screenshot, reference image, wireframe, or section description into a role-based visual inventory. It must not recommend an Elementor architecture, score architecture options, produce an Elementor tree, or choose implementation details.

This bank gives the model reusable examples for how to decompose common web-section patterns. The examples are synthetic, pattern-based, and grounded in common UI/component patterns rather than copied from a specific third-party design.

---

## Research basis

Use these examples together with the Stage 2 rules:

- Elementor Structure/Navigator logic: a section should be understandable as a structured tree before implementation decisions.
- Elementor Container/Flexbox logic: visual groups should be identified before choosing layout mechanisms.
- Atomic Design: UI can be decomposed into smaller elements, repeated component-like groups, and larger section organisms.
- UI grouping research: text, widgets, images, and visual fragments often function as semantic groups, not isolated atoms.
- Accessibility practice: meaningful images/logos/content must be distinguished from decorative visuals and unknown alt requirements.

---

## How to use these examples

The model must copy the method, not the content.

For a new section:

1. Observe visible groups.
2. Classify by visual/content role.
3. Identify repeated component candidates.
4. Identify the visual core.
5. Separate decoration from meaningful content.
6. Mark overlay/connector candidates without choosing implementation.
7. Identify responsive risks.
8. Mark unknowns instead of inventing facts.
9. List implementation assumptions that are not allowed yet.

---

## Enhanced authoring requirements

New or revised examples should follow `EXAMPLE_AUTHORING_STANDARD.md`.

Useful additions from external review have been adopted as an example-authoring standard:

- each example should include metadata: ID, pattern type, complexity, and teaching goal;
- each example should distinguish `Source Pattern` from `Synthetic Example Description`;
- examples should include explicit `Forbidden Assumptions`;
- examples should include short negative examples under `Forbidden Decomposition Examples`;
- interactive patterns must mark state and behavior as unknown unless explicitly stated;
- accessibility status should use `meaningful | decorative | unknown`, not premature certainty;
- repeated UI patterns should be marked as component candidates without choosing Repeater, Loop, CPT, ACF, or static hardcoding in Stage 2.

---

## Example index

| ID | Pattern | Primary lesson |
|---|---|---|
| EX-DCP-001 | Smart Home Connector Section | Connector decoration vs editable feature cards |
| EX-DCP-002 | Split Hero with Dashboard Mockup | Copy area vs visual mockup vs background decoration |
| EX-DCP-003 | Services / Feature Cards Grid | Repeated card components and flow groups |
| EX-DCP-004 | Pricing Cards | Repeated plan cards, CTA content, feature lists |
| EX-DCP-005 | Testimonial Cards / Carousel | Quote/avatar/name grouping and carousel unknowns |
| EX-DCP-006 | Logo Strip / Partner Grid | Repeated logos, meaningful vs decorative uncertainty |
| EX-DCP-007 | CTA Band | Primary message, CTA, background image/decorations |
| EX-DCP-008 | FAQ Accordion | Interactive content groups and state unknowns |
| EX-DCP-009 | Stats / Metrics | Repeated metric blocks and long-number risks |
| EX-DCP-010 | Product / Portfolio Grid | Repeated item cards with image/title/meta/CTA |
| EX-DCP-011 | Process Timeline | Step sequence, connector lines, order semantics |
| EX-DCP-012 | Overlapping Floating Cards | Overlay risks, z-index-like visuals, responsive collision |

---

## Non-negotiable rule

Examples must never be used to jump directly to `/architectures` or `/recommend`.

They exist only to improve `/decompose` quality.
