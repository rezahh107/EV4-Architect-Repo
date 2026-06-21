# Stage 3 — /architectures: Architecture Enumeration

Status: confirmed  
Version: 1.0.0  
Depends on: Stage 2 — `/decompose`  
Allowed next step: `/score-evidence`

---

## Purpose

Stage 3 enumerates all viable Elementor V4 implementation architecture candidates for the decomposed section.

It must generate architecture options, not choose one.

This stage exists to prevent the model from jumping directly from visual decomposition to a single favorite implementation.

---

## Core Rule

Generate architecture candidates first. Score and recommendation happen later.

The model must not decide the winner during `/architectures`.

---

## Source Grounding

Stage 3 is grounded in these project principles:

- Elementor Structure clarity matters because complex pages may include multi-layered designs, Z-index, negative margin, absolute positioning, and hidden handles.
- Flexbox Containers are the default first-class layout base because they provide width, height, order, loading, and responsive control.
- Grid Containers are valid candidates for repeated two-dimensional card/item layouts when row/column alignment is central.
- Repeated UI groups from Stage 2 may become component, repeater, loop, or widget-native candidates, but this is only a candidate at Stage 3.
- Decorative connector or overlay layers may become SVG/CSS overlay candidates, but meaningful content must remain editable when practical.
- Third-party plugins are never included as final candidates unless first marked as `requires_user_approval`.

---

## Required Input

Stage 3 requires a completed Stage 2 `DECOMPOSITION SNAPSHOT` containing:

- Visible Groups
- Meaningful Content
- Repeated Component Candidates
- Visual Core
- Decoration Layers
- Overlay / Connector Candidates
- Responsive Risks
- Unknowns
- Implementation Assumptions Not Allowed Yet

If Stage 2 is missing or incomplete, Stage 3 must stop and request `/decompose` first.

---

## Allowed Work

Allowed:

- Generate multiple viable architecture candidates.
- Include baseline architecture patterns even if they may later score poorly.
- Include section-specific architecture variants based on Stage 2.
- Mark each candidate as native, hybrid, overlay, dynamic, widget-native, or rejected-risk.
- Explain the editable content strategy for each candidate.
- Explain normal-flow vs overlay boundaries.
- Explain the responsive premise for each candidate.
- List architecture-specific unknowns.
- List why a candidate may be risky.
- Hand off all candidates to `/score-evidence`.

Forbidden:

- Do not choose the final architecture.
- Do not score candidates.
- Do not rank candidates.
- Do not produce the final Elementor tree.
- Do not provide exact CSS values.
- Do not write implementation code.
- Do not remove candidates just because they seem weaker, unless they violate a hard project default.
- Do not introduce a third-party plugin as a normal candidate without `requires_user_approval`.

---

## Architecture Generation Strategy

Use a hybrid approach:

```text
Baseline Patterns + Section-Specific Variants
```

The model must always consider baseline patterns, then add variants that are specifically suggested by the Stage 2 decomposition.

---

## Required Baseline Pattern Families

Stage 3 must consider these families when relevant.

### A01 — Native Flow Flexbox Architecture

Use when the section can be expressed as semantic containers, columns, rows, and editable widgets in normal flow.

Typical fit:

- Hero sections
- CTA bands
- Simple split layouts
- Copy + visual sections
- Feature/card rows where one-dimensional alignment is enough

Core premise:

- Most content stays in normal flow.
- Flexbox Containers handle direction, gap, alignment, order, and responsive stacking.
- Minimal or no overlay is used.

Do not assume it is best. Only enumerate it.

---

### A02 — Native Grid / Repeated Card Architecture

Use when Stage 2 identifies a repeated two-dimensional card/item layout.

Typical fit:

- Services grid
- Pricing cards
- Logo grid
- Product/portfolio cards
- Stats blocks

Core premise:

- Repeated items are grouped into a clear card/item pattern.
- Grid or equivalent container layout handles rows and columns.
- Item internals remain editable.

Risk to mark:

- Grid may not handle asymmetric overlays or irregular highlighted variants without additional wrappers or classes.

---

### A03 — Relative Stage + Absolute Overlay Architecture

Use when Stage 2 identifies floating cards, badges, pins, connector nodes, or layered visual elements.

Typical fit:

- Floating cards over an image
- Overlapping avatars
- Badges pinned to a visual
- Hero mockups with floating UI fragments

Core premise:

- A named parent container becomes the controlled relative Stage.
- Only overlay elements are positioned absolutely inside that Stage.
- Primary content remains in normal flow.

Hard boundary:

- Absolute positioning is never allowed globally or for primary text flow.

---

### A04 — SVG Connector Layer Architecture

Use when Stage 2 identifies connector lines, process/timeline lines, radial links, orbit lines, or decorative relationship lines.

Typical fit:

- Smart home connector section
- Process timeline
- Feature cards linked to central visual
- Network/radial diagrams

Core premise:

- Connector lines are contained in a controlled SVG layer.
- Cards and text remain editable Elementor content.
- The SVG layer is decorative unless the user confirms semantic or interactive meaning.

Responsive premise:

- Mobile may simplify, hide, replace, or redraw connector lines.
- The model must not assume the mobile connector behavior.

---

### A05 — Dynamic Loop / Repeater Architecture

Use when Stage 2 identifies repeated content that may be CMS-driven or frequently edited.

Typical fit:

- Services
- Portfolio items
- Products
- Testimonials
- FAQs
- Logo lists
- Pricing features

Core premise:

- Repeated item structure is defined once.
- Data may come from Loop Grid, dynamic content, ACF, CPT, or other approved data sources.

Hard boundary:

- Stage 3 may propose this as a candidate, but must mark data source as `unknown` unless the user specified it.

---

### A06 — Widget-Native Architecture

Use when Elementor provides a native widget or Pro widget that directly matches the interaction or content model.

Typical fit:

- Accordion / FAQ
- Carousel / Testimonials
- Price Table
- Counter / Stats
- Loop Grid / Posts / Portfolio
- Tabs / Toggle

Core premise:

- Use a native Elementor widget when it preserves editability and reduces custom implementation risk.

Risk to mark:

- Widget-native output may be less visually precise or less structurally flexible than custom container composition.

---

### A07 — Hybrid Native + Scoped Custom CSS Architecture

Use when native Elementor structure is appropriate, but visual fidelity requires scoped CSS.

Typical fit:

- Advanced cards
- Responsive connector adjustments
- Equal-height fixes
- Hover states
- Decorative pseudo-elements
- Controlled transforms and layering

Core premise:

- Structure remains Elementor-native.
- CSS is scoped to a named parent class.
- CSS does not replace editable content.

Hard boundary:

- Do not use global, unscoped CSS.

---

### A08 — HTML/SVG Widget Isolated Decoration Architecture

Use only when a decorative visual layer cannot be reasonably built with native Elementor controls or SVG Widget alone.

Typical fit:

- Complex decorative SVG shells
- Pure decorative connector maps
- Non-semantic background ornaments

Core premise:

- HTML/SVG is isolated to decorative or non-primary layers.
- Meaningful text and controls remain native widgets.

Risk to mark:

- Lower editability for that layer.
- Requires stricter responsive testing.

---

### R01 — Rejected Single Static Image Architecture

This must be listed as a rejected-risk candidate when the visual source could tempt the model to flatten the section into one image.

Reject when:

- Meaningful text, cards, icons, buttons, or repeated content would become non-editable.
- DOM order or accessibility would be destroyed.
- Responsive behavior would depend on scaling one raster image.

---

### R02 — Third-Party Plugin Architecture

This must be listed only when a third-party plugin appears materially useful.

Status must be:

```text
requires_user_approval
```

Never include it as a normal candidate.

---

## Candidate Output Schema

Return:

```text
ARCHITECTURE CANDIDATES

Input basis:
- Stage 2 summary used:
- Key repeated groups:
- Key overlay/connector risks:
- Key unknowns that affect architecture:

Candidate A01 — [Architecture Name]
- family: Native Flow Flexbox | Native Grid | Relative Stage + Overlay | SVG Connector Layer | Dynamic Loop | Widget-Native | Hybrid CSS | HTML/SVG Decoration | Rejected-Risk | Third-Party Approval
- status: viable | risky | rejected | requires_user_approval
- best_for:
- structure_premise:
- editable_content_strategy:
- normal_flow_strategy:
- overlay_strategy:
- responsive_premise:
- design_system_strategy:
- likely_elementor_tools:
- custom_css_need: none | low | medium | high | unknown
- dynamic_data_need: none | possible | likely | unknown
- accessibility_notes:
- architecture_unknowns:
- known_risks:
- why_include_this_candidate:

Candidate A02 — ...

Rejected / Non-primary Candidates:
- ...

Do not choose a winner yet.
Allowed next step:
- /score-evidence
```

---

## Minimum Candidate Count

Stage 3 must usually produce at least 3 viable candidates plus any relevant rejected-risk candidates.

For simple sections:

- Minimum 2 viable candidates may be acceptable.

For complex overlay, connector, dynamic, carousel, FAQ, pricing, or portfolio sections:

- Minimum 4 viable candidates are expected.

Rejected-risk candidates do not count toward the viable candidate minimum.

---

## Candidate Inclusion Rules

Include a candidate if:

- It could plausibly implement the Stage 2 decomposition.
- It preserves meaningful content better than a flattened visual asset.
- It provides a different structural strategy than the other candidates.
- It tests an important tradeoff that scoring should evaluate later.

Exclude a candidate if:

- It violates a confirmed project default.
- It requires a third-party plugin and the user did not approve asking about that path.
- It turns meaningful content into a static image.
- It depends on unscoped global CSS.
- It assumes unknown interactive behavior as fact.

---

## Pass Criteria

Stage 3 passes only if:

- It uses the Stage 2 decomposition as input.
- It generates more than one architecture candidate.
- It includes baseline patterns and section-specific variants when relevant.
- It separates viable, risky, rejected, and approval-required candidates.
- It explains editability, normal-flow, overlay, responsive, design-system, and accessibility implications for each candidate.
- It does not score, rank, or recommend a winner.
- It hands off to `/score-evidence`.

---

## Failure Modes

Stage 3 fails if:

- It jumps directly to one final architecture.
- It says “best” or “recommended” before scoring.
- It produces an Elementor tree.
- It writes implementation CSS or code.
- It ignores Stage 2 unknowns.
- It treats visual resemblance as enough to approve an architecture.
- It omits a reasonable architecture family without explaining why.
