# Stage 2 — /decompose: Controlled Visual Role Decomposition

Status: confirmed  
Version: 1.0.0  

---

## Purpose

The `/decompose` phase converts a screenshot, reference image, wireframe, or section description into a role-based visual inventory.

It is not an implementation phase.

The goal is to separate what is visible from what is unknown, and to classify visible groups by role before any architecture is proposed.

---

## Research Grounding

Stage 2 uses a combined basis:

1. Elementor Structure / Navigator logic: Elementor provides a tree-style page structure view for navigating and managing page elements, which makes role clarity and naming important before build decisions.
2. Elementor Container / Flexbox logic: containers are the main layout grouping mechanism, so decomposition must identify visual groups before choosing Flow, Flex, Grid, or Stage patterns.
3. Atomic Design: UI can be understood as smaller pieces combined into larger patterns, such as atoms, molecules, organisms, templates, and pages.
4. UI grouping research: UI text, widgets, images, and visual fragments often need to be grouped into semantic units to improve code structure, accessibility, and UI-to-code workflows.
5. Accessibility practice: meaningful, informative, functional, decorative, and unknown images must be separated before alt decisions are made.

Reference URLs:

- https://elementor.com/help/navigator/
- https://elementor.com/help/container-element/
- https://atomicdesign.bradfrost.com/chapter-2/
- https://www.w3.org/WAI/tutorials/images/decorative/
- https://arxiv.org/abs/2109.08763
- https://arxiv.org/abs/2212.03440
- https://arxiv.org/abs/2403.04984

---

## Example Bank

Stage 2 uses an active few-shot and calibration bank:

- `examples/decomposition/README.md`
- `examples/decomposition/EXAMPLE_AUTHORING_STANDARD.md`
- `examples/decomposition/EX-DCP-001` through `EX-DCP-012`

The model must use the examples to copy the decomposition method, not the content.

The authoring standard requires examples to include, where practical:

- metadata;
- pattern type;
- complexity;
- teaching goal;
- source pattern;
- synthetic example description;
- expected decomposition;
- forbidden assumptions;
- negative decomposition examples.

---

## Core Principle

Decompose by visual role first, implementation never.

A screenshot can show visible roles, visual grouping, hierarchy, repetition, and possible overlay relationships. It cannot prove the actual Elementor DOM, exact CSS, widget choice, plugin dependency, or final responsive implementation.

---

## Confidence Labels

Use these labels in every relevant item:

| Label | Meaning |
|---|---|
| `observed` | Directly visible in the image or explicitly stated by the user |
| `likely` | Reasonable visual inference, but not confirmed |
| `unknown` | Not knowable from the current evidence |
| `not_allowed_yet` | Implementation assumption that belongs to a later stage |

Rule:

```text
No evidence → no fact.
If unsure, mark unknown.
```

---

## Allowed Work

The model may:

- Identify visible groups.
- Classify meaningful content.
- Classify repeated component candidates.
- Identify the visual core.
- Identify decorative layers.
- Identify overlay or connector candidates.
- Identify responsive risks.
- List unknowns.
- List implementation assumptions that are forbidden at this stage.

---

## Forbidden Work

The model must not:

- Recommend an architecture.
- Score architecture options.
- Produce an Elementor tree.
- Assign exact CSS values.
- Infer the actual DOM.
- Choose Flex, Grid, Absolute, SVG, WebP, HTML Widget, or plugins as final implementation.
- Claim exact pixel measurements from a screenshot.
- Treat visual order as confirmed DOM order.
- Convert a visual observation into an implementation fact.

---

## Decomposition Categories

### 1. Visible Groups

Large visual regions or groupings visible in the reference.

Examples:

- left content column
- right visual area
- central image area
- row of repeated cards
- logo strip
- connector line cluster

### 2. Meaningful Content

Content that users read, understand, click, or interact with.

Examples:

- headings
- paragraphs
- feature cards
- buttons
- icons when they communicate meaning
- product/service labels
- logos when meaningful

### 3. Repeated Component Candidates

Repeated visual/content patterns that may later become reusable classes, components, or repeated containers.

Examples:

- feature card pattern
- testimonial card pattern
- pricing item pattern
- icon + heading + text group

### 4. Visual Core

The central visual object or focal visual anchor of the section.

Examples:

- hero product image
- house illustration
- app screenshot
- central device mockup
- dashboard preview

Important:

- Visual core is not automatically decorative.
- If the visual explains the product, service, state, or proof, mark accessibility/meaning as `unknown` unless the user provides context.

### 5. Decoration Layers

Visual elements that improve mood, direction, depth, or polish but are not meaningful standalone content.

Examples:

- connector lines
- glow
- background blobs
- shadows
- ornamental dividers
- abstract shapes

### 6. Overlay / Connector Candidates

Elements that visually relate or attach one group to another and may later require controlled layering.

Examples:

- lines connecting cards to a central image
- orbit nodes around a product
- labels over an image
- hotspots
- decorative markers attached to visual core

Implementation status must remain `unknown` in Stage 2.

### 7. Responsive Risks

Visual patterns that may break or need simplification across desktop, tablet, and mobile.

Examples:

- connector lines crossing responsive columns
- side cards around a central image
- long text inside fixed-size cards
- overlapping badges
- absolute-looking decorations
- desktop-only visual symmetry

### 8. Unknowns

Facts that affect later decisions but cannot be known from the current evidence.

Examples:

- actual Elementor DOM
- asset availability
- exact image dimensions
- breakpoint requirements
- whether a decoration must remain visible on mobile
- whether a group is interactive
- whether a carousel auto-plays
- whether an accordion is exclusive or multi-open
- whether a filter is AJAX, client-side, URL-based, or static
- whether content is static, CMS-driven, ACF-driven, CPT-driven, or WooCommerce-driven

### 9. Implementation Assumptions Not Allowed Yet

Things the model is tempted to assume but must not decide in Stage 2.

Examples:

- “This must be Flexbox.”
- “This must be Grid.”
- “This must be SVG.”
- “This must be absolute positioned.”
- “This is definitely one container.”
- “This is definitely the DOM order.”
- “This should use ACF Repeater.”
- “This should use Elementor Loop Grid.”
- “This should be hardcoded because the screenshot shows a fixed number of cards.”

---

## Output Format

```text
DECOMPOSITION SNAPSHOT

1. Visible Groups
- item:
  role:
  evidence:
  confidence: observed | likely | unknown

2. Meaningful Content
- item:
  content_type:
  evidence:
  confidence: observed | likely | unknown

3. Repeated Component Candidates
- component_candidate:
  repeated_parts:
  evidence:
  confidence: observed | likely | unknown

4. Visual Core
- item:
  evidence:
  confidence: observed | likely | unknown

5. Decoration Layers
- item:
  decorative_function:
  evidence:
  confidence: observed | likely | unknown

6. Overlay / Connector Candidates
- item:
  relationship:
  evidence:
  implementation_status: unknown
  confidence: observed | likely | unknown

7. Responsive Risks
- risk:
  reason:
  confidence: observed | likely | unknown

8. Unknowns
- unknown:
  why_it_matters:
  blocking: yes | no

9. Implementation Assumptions Not Allowed Yet
- assumption:
  reason:

Allowed next step:
- /architectures
```

---

## Pass Criteria

Stage 2 is successful when:

- It separates content from decoration.
- It identifies repeated patterns as component candidates.
- It classifies the main visual focal point.
- It does not automatically treat visual core as decorative.
- It marks possible overlays/connectors without choosing implementation.
- It identifies responsive risks.
- It lists unknowns instead of inventing facts.
- It treats interactive state and dynamic data behavior as unknown unless explicitly provided.
- It does not recommend a final architecture.
- It does not score anything.
- It does not generate an Elementor tree.
- It allows `/architectures` only after the decomposition snapshot is complete.

---

## Example: Smart Home Feature Section

```text
DECOMPOSITION SNAPSHOT

1. Visible Groups
- item: left feature-card group
  role: side content group
  evidence: three rounded feature cards are visible on the left side
  confidence: observed

- item: central house image area
  role: visual focal area
  evidence: a large house image sits in the center
  confidence: observed

- item: right feature-card group
  role: side content group
  evidence: three rounded feature cards are visible on the right side
  confidence: observed

2. Meaningful Content
- item: six feature cards
  content_type: feature descriptions with icons, headings, and short text
  evidence: each rounded card contains an icon, title, and subtitle
  confidence: observed

3. Repeated Component Candidates
- component_candidate: feature card
  repeated_parts: icon, heading, short description, rounded background
  evidence: the same card pattern repeats on both sides
  confidence: observed

4. Visual Core
- item: house image
  evidence: the house is the largest central visual object
  confidence: observed

5. Decoration Layers
- item: gray connector lines
  decorative_function: visually connect feature cards to the central house
  evidence: thin curved lines extend between side cards and center area
  confidence: observed

6. Overlay / Connector Candidates
- item: connector line layer
  relationship: connects side feature groups to central visual core
  evidence: lines visually bridge cards and house
  implementation_status: unknown
  confidence: observed

7. Responsive Risks
- risk: connector lines may not adapt to stacked mobile layout
  reason: lines depend on desktop spatial relationships between side cards and central visual
  confidence: likely

8. Unknowns
- unknown: whether the house image is available separately
  why_it_matters: affects later architecture options
  blocking: no

- unknown: whether connector lines must remain visible on mobile
  why_it_matters: affects later responsive architecture
  blocking: no

9. Implementation Assumptions Not Allowed Yet
- assumption: use SVG for connector lines
  reason: implementation choice belongs to `/architectures`

- assumption: use three-column Flex
  reason: architecture choice belongs to `/architectures`

Allowed next step:
- /architectures
```


## Intermediate Stage Artifact Boundary

Producer-owned intermediate Artifact: `/decompose` emits `ev4-architect-pipeline-stage-artifact@1.1.0` with all canonical sections. Missing Decoration Layers, Overlay / Connector Candidates, Unknowns, or any other canonical section fails at the Stage 2 boundary under ASB-R01/ASB-R02.

If an executable validator/tool is available, place the complete ordered Stage Artifact sequence in one directory and execute the canonical Validation Transaction:

```bash
python scripts/check-architect-pipeline-stage-boundary.py validate-run \
  --sequence <artifact-directory> \
  --output <validation-bundle-directory> \
  --format json

python scripts/check-architect-pipeline-stage-boundary.py validate-bundle \
  --bundle <validation-bundle-directory> \
  --format json
```

Only a Bundle independently verified by `validate-bundle` with `bundle_integrity_status=valid`, `run_validation_status=valid`, and `authorization_valid=true` authorizes next-stage continuation. `diagnose-artifact` is non-authorizing and must never be used to construct a Receipt, Boundary, Anchor, or continuation claim. If execution is unavailable, do not claim machine validation or emit a validated next-stage anchor; return `validation_required` or `insufficient_evidence`, preserve the Artifact sequence, and provide both canonical commands above.
