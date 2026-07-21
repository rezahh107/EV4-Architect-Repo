# Stage 3 — /architectures: Architecture Enumeration

Status: confirmed  
Version: 1.1.0  
Depends on: Stage 2 — `/decompose`  
Allowed next step: `/score-evidence`

---

## Purpose

Stage 3 enumerates viable Elementor V4 implementation architecture candidates for a decomposed section.

It must generate architecture options, not choose one.

This stage exists to prevent the model from jumping directly from visual decomposition to a single favorite implementation.

Stage 3 is an enumeration and coverage stage. It is not a recommendation stage, not a scoring stage, and not an implementation stage.

---

## Core Rule

Generate architecture candidates first. Score and recommendation happen later.

The model must not decide the winner during `/architectures`.

The model must not secretly bias the user toward one candidate by using recommendation language before `/score-evidence` and `/recommend`.

---

## Source Grounding

Stage 3 is grounded in these project principles:

- Elementor Structure clarity matters because complex pages may include multi-layered designs, Z-index, negative margin, absolute positioning, special conditions, and hidden handles.
- Flexbox Containers are the default first-class layout base because they provide control over width, height, item order, spacing, alignment, and responsive arrangement.
- Grid Containers are valid candidates for repeated two-dimensional card/item layouts when row/column alignment is central.
- Loop Grid / dynamic architectures require a real data or templating reason. A repeated visual group alone is not enough to claim a dynamic Loop Grid is appropriate.
- Custom CSS is allowed, but only as scoped CSS attached to a named parent or controlled element scope. Global unscoped CSS is not a valid architecture.
- Repeated UI groups from Stage 2 may become component, repeater, loop, or widget-native candidates, but this remains only a candidate during Stage 3.
- Decorative connector or overlay layers may become SVG/CSS overlay candidates, but meaningful content must remain editable when practical.
- Third-party plugins are never included as normal candidates unless first marked as `requires_user_approval`.

---

## Required Input Gate

Stage 3 requires a completed Stage 2 `DECOMPOSITION SNAPSHOT` containing all of the following sections:

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

If Stage 2 contains blocking unknowns that make architecture enumeration impossible, Stage 3 must stop and ask only the minimal blocking question.

If Stage 2 contains non-blocking unknowns, Stage 3 must continue but must propagate them into the Unknown Propagation Ledger.

---

## Mandatory Execution Order

The model must execute Stage 3 in this order:

1. Validate Stage 2 input.
2. Produce a Stage 2 Evidence Digest.
3. Produce an Architecture Coverage Matrix.
4. Produce an Unknown Propagation Ledger.
5. Enumerate architecture candidates.
6. Add a tradeoff record for every candidate.
7. Run the Hidden Recommendation Self-Audit.
8. Hand off to `/score-evidence`.

The model must not skip the Coverage Matrix or Unknown Propagation Ledger.

---

## Stage 2 Evidence Digest

Before listing candidates, summarize only architecture-relevant facts from Stage 2:

```text
STAGE 2 EVIDENCE DIGEST

Visible structure:
- ...

Meaningful content that must remain editable:
- ...

Repeated component candidates:
- ...

Visual core:
- ...

Decoration / overlay / connector candidates:
- ...

Responsive risks:
- ...

Unknowns affecting architecture:
- ...
```

Rules:

- Do not add new facts not present in Stage 2 or user input.
- Do not convert `unknown` into `likely` just to make a candidate look stronger.
- Do not treat visual resemblance as implementation proof.

---

## Architecture Coverage Matrix

Stage 3 must consider every required architecture family and state whether it is included, omitted, rejected, or approval-gated.

```text
ARCHITECTURE COVERAGE MATRIX

| Family | Considered | Included as Candidate | Status | Reason |
|---|---|---|---|---|
| A01 Native Flow Flexbox | yes/no | yes/no | viable/risky/omitted | ... |
| A02 Native Grid / Repeated Card | yes/no | yes/no | viable/risky/omitted | ... |
| A03 Relative Stage + Absolute Overlay | yes/no | yes/no | viable/risky/omitted | ... |
| A04 SVG Connector Layer | yes/no | yes/no | viable/risky/omitted | ... |
| A05 Dynamic Loop / Repeater | yes/no | yes/no | viable/risky/omitted | ... |
| A06 Widget-Native | yes/no | yes/no | viable/risky/omitted | ... |
| A07 Hybrid Native + Scoped CSS | yes/no | yes/no | viable/risky/omitted | ... |
| A08 HTML/SVG Widget Isolated Decoration | yes/no | yes/no | viable/risky/omitted | ... |
| R01 Single Static Image | yes | yes/no | rejected/omitted | ... |
| R02 Third-Party Plugin | yes/no | yes/no | requires_user_approval/omitted | ... |
```

Rules:

- A family may be omitted, but omission must be explained.
- A family may be risky and still included if it tests an important tradeoff for Stage 4.
- R01 must be included as rejected when the visual source could tempt flattening the section into one image.
- R02 must not be included as a normal candidate. It may only appear as `requires_user_approval`.

---

## Unknown Propagation Ledger

Every architecture-relevant unknown from Stage 2 must be carried forward.

```text
UNKNOWN PROPAGATION LEDGER

| Stage 2 Unknown | Affected Candidate(s) | Effect on Architecture | Handling |
|---|---|---|---|
| mobile connector behavior unknown | A03, A04, A07 | responsive premise cannot be final | carry to scoring |
| data source unknown | A05, A06 | dynamic architecture cannot be assumed | mark as possible, not confirmed |
```

Rules:

- The model must not drop Stage 2 unknowns.
- If an unknown does not affect a candidate, write `not_applicable` with a reason.
- Unknowns must reduce certainty, not disappear.
- A candidate depending on an unresolved unknown must mark that dependency explicitly.

---

## Allowed Work

Allowed:

- Generate multiple viable architecture candidates.
- Include baseline architecture patterns even if they may later score poorly.
- Include section-specific architecture variants based on Stage 2.
- Mark each candidate as native, hybrid, overlay, dynamic, widget-native, rejected-risk, or approval-required.
- Explain the editable content strategy for each candidate.
- Explain normal-flow vs overlay boundaries.
- Explain the responsive premise for each candidate.
- List architecture-specific unknowns.
- List why a candidate may be risky.
- Explain what each candidate preserves and what it sacrifices.
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
- Do not use hidden recommendation language.
- Do not use `best_for`; use `fit_context` instead.

---

## Hidden Recommendation Ban

Before `/score-evidence`, the model must not use language that implies a winner.

Forbidden English terms:

- best
- recommended
- optimal
- safest
- cleanest
- strongest
- winner
- preferred
- obvious choice
- final choice

Forbidden Persian terms:

- بهترین
- پیشنهادی
- بهینه‌ترین
- امن‌ترین
- تمیزترین
- قوی‌ترین
- برنده
- گزینه اصلی
- انتخاب نهایی
- واضحاً بهتر

Allowed neutral alternatives:

- fits when
- useful when
- candidate for
- viable if
- risky because
- should be scored later
- باید در مرحله امتیازدهی بررسی شود

If the model accidentally uses recommendation language, it must revise the output before finalizing Stage 3.

---

## Evidence Labels

Each architecture claim should be grounded with one of these labels:

```text
from_stage2
project_default
elementor_capability
assumption
unknown
requires_verification
```

Examples:

```text
- normal_flow_strategy: primary text and cards remain in flow [project_default + from_stage2]
- overlay_strategy: connector lines may use SVG layer [from_stage2 + assumption]
- dynamic_data_need: possible, because cards repeat, but data source is unknown [from_stage2 + unknown]
```

Rules:

- Do not present assumptions as facts.
- Do not present Elementor capability as a user requirement.
- Do not present project defaults as evidence that a specific candidate will work.

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

Guardrail:

- Do not imply this is the default winner.
- If overlay or connector behavior is central, mark the limitation.

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

- Grid may not handle asymmetric overlays, highlighted variants, irregular item spans, or interaction states without additional wrappers or classes.

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
- Mobile overlay behavior must remain unknown unless the user explicitly provided it.

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

Hard boundary:

- Do not treat the SVG layer as a substitute for meaningful content.

---

### A05 — Dynamic Loop / Repeater Architecture

Use only when Stage 2 identifies repeated content and there is a plausible data, edit-frequency, CMS, CPT, ACF, WooCommerce, or reuse reason.

Typical fit:

- Services from CMS
- Portfolio items
- Products
- Testimonials
- FAQs
- Logo lists
- Pricing features

Core premise:

- Repeated item structure is defined once.
- Data may come from Loop Grid, dynamic content, ACF, CPT, WooCommerce, or other approved data sources.

Dynamic Candidate Guardrail:

- Repeated visual group does not automatically mean Dynamic Loop.
- If data source is unknown, mark `dynamic_data_need: possible` or `unknown`, never `likely`.
- Do not claim Loop Grid unless the content type fits an Elementor Loop/Grid style source.
- Do not invent CPT, ACF, WooCommerce, or API sources.

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
- Visible state in a screenshot is not proof of interaction rules.

Widget Guardrail:

- Do not infer autoplay, open/closed state, filtering logic, counter animation, or AJAX behavior from a static image.

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
- Do not output exact CSS in Stage 3.
- Do not rely on CSS to fake semantic content.

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

Hard boundary:

- HTML Widget must not own primary meaningful content unless the user explicitly approves a code-heavy approach.

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

Do not name a specific plugin unless the user has asked to consider plugins or the plugin path is materially necessary and must be approved first.

---

## Candidate Output Schema

Return:

```text
ARCHITECTURE CANDIDATES

STAGE 2 EVIDENCE DIGEST
- Visible structure:
- Meaningful editable content:
- Repeated component candidates:
- Visual core:
- Decoration / overlay / connector candidates:
- Responsive risks:
- Unknowns affecting architecture:

ARCHITECTURE COVERAGE MATRIX
| Family | Considered | Included as Candidate | Status | Reason |
|---|---|---|---|---|
| A01 Native Flow Flexbox | yes/no | yes/no | viable/risky/omitted | ... |
| A02 Native Grid / Repeated Card | yes/no | yes/no | viable/risky/omitted | ... |
| A03 Relative Stage + Absolute Overlay | yes/no | yes/no | viable/risky/omitted | ... |
| A04 SVG Connector Layer | yes/no | yes/no | viable/risky/omitted | ... |
| A05 Dynamic Loop / Repeater | yes/no | yes/no | viable/risky/omitted | ... |
| A06 Widget-Native | yes/no | yes/no | viable/risky/omitted | ... |
| A07 Hybrid Native + Scoped CSS | yes/no | yes/no | viable/risky/omitted | ... |
| A08 HTML/SVG Widget Isolated Decoration | yes/no | yes/no | viable/risky/omitted | ... |
| R01 Single Static Image | yes | yes/no | rejected/omitted | ... |
| R02 Third-Party Plugin | yes/no | yes/no | requires_user_approval/omitted | ... |

UNKNOWN PROPAGATION LEDGER
| Stage 2 Unknown | Affected Candidate(s) | Effect on Architecture | Handling |
|---|---|---|---|
| ... | ... | ... | ... |

Candidate A01 — [Neutral Architecture Name]
- family:
- status: viable | risky | rejected | requires_user_approval
- evidence_basis: from_stage2 | project_default | elementor_capability | assumption | unknown | requires_verification
- fit_context:
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
- what_it_preserves:
- what_it_sacrifices:
- verification_needed_later:
- why_include_this_candidate:

Candidate A02 — ...

Rejected / Approval-Gated Candidates:
- ...

HIDDEN RECOMMENDATION SELF-AUDIT
- ranking_language_used: yes/no
- winner_implied: yes/no
- omitted_family_without_reason: yes/no
- stage2_unknown_dropped: yes/no
- code_or_exact_css_given: yes/no
- result: pass/fail

Do not choose a winner yet.
Allowed next step:
- /score-evidence
```

---

## Minimum Candidate Count

Stage 3 must usually produce at least 3 viable candidates plus any relevant rejected-risk candidates.

For simple sections:

- Minimum 2 viable candidates may be acceptable.
- The Coverage Matrix must explain why fewer families are relevant.

For complex overlay, connector, dynamic, carousel, FAQ, pricing, or portfolio sections:

- Minimum 4 viable candidates are expected.

Rejected-risk candidates do not count toward the viable candidate minimum.

Approval-gated third-party candidates do not count toward the viable candidate minimum.

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

When excluding, record the exclusion in the Coverage Matrix.

---

## Candidate Tradeoff Requirement

Every candidate must include:

```text
what_it_preserves:
what_it_sacrifices:
verification_needed_later:
```

Rules:

- A candidate with no downside is suspicious and must be revised.
- Tradeoffs must be specific to the candidate, not generic.
- Verification items must be carried into `/score-evidence`.

---

## Pass Criteria

Stage 3 passes only if:

- It uses the Stage 2 decomposition as input.
- It generates more than one architecture candidate.
- It includes the Architecture Coverage Matrix.
- It includes the Unknown Propagation Ledger.
- It includes baseline patterns and section-specific variants when relevant.
- It separates viable, risky, rejected, and approval-required candidates.
- It explains editability, normal-flow, overlay, responsive, design-system, and accessibility implications for each candidate.
- It gives real tradeoffs for every candidate.
- It does not score, rank, or recommend a winner.
- It does not use hidden recommendation language.
- It hands off to `/score-evidence`.

---

## Failure Modes

Stage 3 fails if:

- It jumps directly to one final architecture.
- It says “best” or “recommended” before scoring.
- It implies a winner through softer language such as “cleanest,” “safest,” or “obvious choice.”
- It produces an Elementor tree.
- It writes implementation CSS or code.
- It ignores Stage 2 unknowns.
- It drops a Stage 2 unknown instead of propagating it.
- It treats visual resemblance as enough to approve an architecture.
- It omits a reasonable architecture family without explaining why.
- It treats repeated visual cards as proof of Dynamic Loop / CPT / ACF.
- It treats a visible accordion/carousel/counter/filter state as proof of interaction rules.
- It uses global unscoped CSS as an architecture.


## Intermediate Stage Artifact Boundary

Producer-owned intermediate Artifact: `/architectures` emits `ev4-architect-pipeline-stage-artifact@1.0.0` with `architecture_coverage_matrix` and `unknown_propagation_ledger`. Missing Matrix or Ledger, disappeared Stage 2 unknowns, untracked unknown dependencies, or unsupported resolution fail at Stage 3 under ASB-R03/ASB-R04.

If an executable validator/tool is available, write the canonical Stage Artifact, execute `python scripts/check-architect-pipeline-stage-boundary.py --artifact <artifact.json> --write-receipt <receipt.json>`, obtain the receipt, and emit a receipt-bound `NEXT STAGE ANCHOR` only after `status=valid`. If execution is unavailable, do not claim machine validation or emit a validated next-stage anchor; return `validation_required` or `insufficient_evidence`, preserve the Artifact, and provide the manual validator command.
