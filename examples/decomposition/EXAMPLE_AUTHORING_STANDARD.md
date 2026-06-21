# Decomposition Example Authoring Standard

Status: active  
Stage: Stage 2 — `/decompose`  
Purpose: stronger few-shot and calibration quality for the decomposition example bank  
Version: 1.0.0

---

## Why this exists

The original example bank already provides synthetic, pattern-based examples. This standard strengthens those examples with a consistent teaching structure.

Use this file when creating or revising any `EX-DCP-*` decomposition example.

The goal is not to make examples verbose for their own sake. The goal is to make every example teach the model how to:

- classify visible UI groups by role;
- separate meaningful content from decoration;
- identify repeated component candidates;
- identify visual core versus decorative layers;
- mark interactive/state behavior as unknown unless explicitly provided;
- list responsive risks without choosing an implementation;
- block premature architecture decisions.

---

## Recommended Example Shape

Every decomposition example should prefer this structure:

```markdown
# EX-DCP-XXX — Pattern Name

## Metadata
- ID:
- Pattern Type:
- Complexity: Low | Medium | High
- Teaching Goal:

---

## Source Pattern

Short description of the general UI pattern.

## Synthetic Example Description

A synthetic, non-copied section description that represents the pattern.

---

## Expected Decomposition

### Visible Groups

### Meaningful Content

### Repeated Component Candidates

### Visual Core

### Decoration & Overlay Candidates

### Responsive Risks

### Unknowns

### Forbidden Assumptions

---

## Forbidden Decomposition Examples

Examples of wrong reasoning the model must avoid.
```

---

## Metadata Rules

### ID

Use the exact `EX-DCP-XXX` ID.

### Pattern Type

Describe the UI pattern by design role, not Elementor implementation.

Good:

```text
Visual Core + Feature Cards + Connector Decoration
Repeated Component Grid
Interactive Content + State Unknown
Overlay + Responsive Collision Risk
```

Bad:

```text
Flexbox section
Absolute positioning section
SVG connector section
```

### Complexity

Use complexity to warn the model how cautious it must be.

| Complexity | Meaning |
|---|---|
| Low | Mostly flow-based, few unknowns, little interaction |
| Medium | Repeated groups, responsive risk, or minor state/interaction unknowns |
| High | Overlap, connector logic, carousel/filter/toggle behavior, dynamic content, or major responsive uncertainty |

### Teaching Goal

The teaching goal should name the specific decomposition skill the example trains.

Examples:

- separate editable cards from connector decoration;
- detect interactive state unknowns;
- distinguish meaningful logos from decorative logos;
- avoid assuming mobile overlay behavior;
- treat repeated UI fragments as semantic component candidates.

---

## Expected Decomposition Rules

### 1. Visible Groups

List the visible semantic groups, not every tiny visual fragment.

Good:

```text
Pricing Card Grid
FAQ Accordion Group
Visual Mockup Group
Logo Strip
```

Bad:

```text
blue box, white box, small icon, first paragraph, second paragraph
```

### 2. Meaningful Content

Meaningful content includes anything users read, click, understand, compare, or rely on.

Examples:

- headings;
- body copy;
- CTA labels and links;
- pricing values;
- feature-list items;
- rating values;
- testimonial author names;
- step numbers when they communicate sequence;
- product or dashboard screenshots when they communicate product meaning.

### 3. Repeated Component Candidates

Mark repeated patterns as component candidates, but do not decide implementation yet.

Allowed:

```text
Feature Card × 6 → repeated component candidate
FAQ Item × N → repeated component candidate
Logo Item × N → repeated visual/content candidate
```

Not allowed:

```text
Use Elementor Loop Grid
Use ACF Repeater
Hardcode six cards
```

Those belong to later stages.

### 4. Visual Core

The visual core is the main focal visual object or visual group of the section.

Examples:

- central smart-home device;
- dashboard mockup;
- product image;
- hero illustration;
- main overlapping image group.

Important distinction:

- Visual Core is not automatically decorative.
- Visual Core may be meaningful, decorative, or unknown depending on context.
- If the visual explains the product or service, do not mark it as decorative without evidence.

### 5. Decoration & Overlay Candidates

Decoration includes visuals that improve polish, depth, rhythm, or visual association but do not independently carry content.

Examples:

- connector lines;
- glow;
- shadows;
- mesh gradients;
- abstract blobs;
- ornamental dividers;
- background grid;
- decorative quote marks.

Overlay candidates include visuals that appear layered or attached to another group.

Examples:

- floating cards;
- badges over images;
- connector lines;
- timeline connectors;
- orbit nodes;
- hotspot markers.

Implementation status must remain `unknown` in Stage 2.

### 6. Responsive Risks

Responsive risks should describe what may break, not how to build it.

Good:

```text
Connector lines may lose alignment when cards stack on mobile.
Floating cards may collide with the main visual on narrow screens.
A three-card pricing row may need a readable mobile comparison strategy.
```

Bad:

```text
Use display:none on mobile.
Use SVG viewBox 1200x420.
Use flex-direction: column.
```

### 7. Unknowns

Use unknowns aggressively. If something is not visible or explicitly stated, do not invent it.

Common unknowns:

- whether a visual is meaningful or decorative;
- whether icons need alt text or are purely ornamental;
- whether items are static or dynamic;
- whether an animation exists;
- whether a carousel auto-plays;
- whether an accordion allows one item or multiple items open;
- whether a filter is client-side, AJAX, URL-based, or static;
- whether mobile connector lines should remain visible.

### 8. Forbidden Assumptions

Every example should list at least 3 forbidden assumptions.

Good forbidden assumptions:

- Do not assume connector lines are SVG, CSS borders, Canvas, or JS.
- Do not assume the first FAQ item is open by default just because it appears open in the screenshot.
- Do not assume all rating values are 5 stars.
- Do not assume the whole card is clickable if only a text link is visible.
- Do not assume logos are decorative or meaningful without context.
- Do not assume hover overlay is sufficient on mobile.
- Do not assume floating cards should be hidden on mobile.

---

## Negative Examples Rule

Each example should include a short `Forbidden Decomposition Examples` section.

This section is used to train the model against common hallucinations and premature implementation choices.

Examples:

```text
Wrong: “Use CSS border-left for the connector because it is the simplest.”
Why wrong: Stage 2 may identify a connector candidate, but cannot choose implementation.
```

```text
Wrong: “The dashboard mockup is decorative, so alt='' is correct.”
Why wrong: A product/dashboard mockup may be meaningful. Accessibility status is unknown until context is known.
```

```text
Wrong: “The FAQ is exclusive because only one item is open in the screenshot.”
Why wrong: A screenshot cannot prove accordion behavior or default state.
```

---

## Interactive Pattern Rules

For any interactive-looking section, the following must be treated as unknown unless explicit evidence exists:

- carousel auto-play;
- number of visible slides;
- swipe behavior;
- accordion default-open state;
- exclusive vs multi-open accordion behavior;
- toggle behavior;
- filter mechanism;
- AJAX vs URL-based pagination;
- hover behavior on touch devices;
- animation trigger;
- JS library or widget choice.

Examples should explicitly teach this.

---

## Accessibility Rules

Do not decide image accessibility status too early.

Use:

```text
meaningful | decorative | unknown
```

Examples:

- A decorative blob or gradient is decoration-only.
- A product image or dashboard mockup is often meaningful or at least unknown.
- Logos may be meaningful if they identify partners, clients, sponsors, or link targets.
- Avatar images may be meaningful if connected to a real testimonial author.
- Step numbers are meaningful when they communicate sequence.
- Checkmark icons may be decorative if the feature text already communicates the meaning.

---

## Dynamic Content Rules

Do not assume static content just because the screenshot is static.

Mark these as unknown when relevant:

- source is hardcoded vs CMS vs ACF vs CPT vs WooCommerce;
- number of cards fixed vs dynamic;
- pricing monthly/yearly toggle behavior;
- testimonials fixed vs dynamic;
- logo list fixed vs dynamic;
- metrics static vs real-time;
- portfolio filters static vs dynamic.

Do not choose the data source in Stage 2.

---

## Quality Checklist

Before accepting any example, verify:

- Metadata exists.
- Source pattern is synthetic, not copied from a live design.
- Expected decomposition follows the Stage 2 output categories.
- Meaningful content is separated from decoration.
- Repeated component candidates are identified without implementation decisions.
- Visual Core is not automatically treated as decorative.
- Interaction/state assumptions are marked unknown.
- Responsive risks are stated without implementation choices.
- At least 3 forbidden assumptions exist.
- Negative examples show what wrong reasoning looks like.

---

## Relation to Stage 3

This file must not be used to recommend implementation architectures.

It exists only to improve `/decompose` quality.

After Stage 2, the next permitted step is `/architectures`.
