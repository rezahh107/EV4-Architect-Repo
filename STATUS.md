# STATUS — Elementor V4 Architect Prompt Pack

Version: 0.3.1  
Status: in_progress  
Last confirmed stage: Stage 3 — `/architectures`  
Current next stage: Stage 4 — `/score-evidence`  
Language: Persian reports, English technical labels allowed  

---

## Confirmed Decisions

### System Architecture

- This project uses GPT Projects.
- The system is a prompt pipeline, not a single giant prompt.
- The GPT Project will contain:
  - Project Instructions / Master Prompt
  - Elementor V4 documentation files
  - Workbook methodology notes
  - Architecture scoring rubric
  - Few-shot examples
  - Calibration cases

### Pipeline

Current planned stages:

1. `/intake`
2. `/research`
3. `/decompose`
4. `/architectures`
5. `/score-evidence`
6. `/score-audit`
7. `/recommend`
8. `/build-tree`
9. `/implementation`
10. `/final-audit`

---

## Stage Status

| Stage | Status | Notes |
|---|---|---|
| `/intake` | confirmed | Lightweight default-based intake |
| `/research` | draft | Documentation source policy remains useful, but Stage 2 and Stage 3 embed initial research grounding |
| `/decompose` | confirmed_with_example_bank | Controlled Visual Role Decomposition; no architecture recommendation allowed |
| `/decomposition-example-bank` | active_enhanced | 12 synthetic pattern-based examples plus authoring standard under `examples/decomposition/` |
| `/architectures` | confirmed_hardened_v1.1.0 | Architecture Enumeration with coverage matrix, unknown propagation, hidden recommendation ban, dynamic guardrails, and tradeoff requirements |
| `/score-evidence` | current_next | Needs Rubric v2 and evidence schema |
| `/score-audit` | not_started | Needs audit rules |
| `/recommend` | not_started | Depends on score audit |
| `/build-tree` | not_started | Needs naming convention |
| `/implementation` | not_started | Needs Elementor settings schema |
| `/final-audit` | not_started | Needs checklist |

---

## Confirmed Project Defaults

- Elementor V4
- Elementor Pro available
- Container/Flexbox-first workflow
- Structure Panel clarity matters
- Scoped Custom CSS allowed
- SVG Widget allowed
- HTML Widget allowed when practical
- No third-party plugin/add-on unless approved by the user
- Meaningful content should remain editable when practical
- Do not convert meaningful content into a single static image
- Primary content should remain in normal flow
- Absolute positioning only inside a clearly named relative Stage
- Decorative connector lines may use SVG and may be hidden or simplified on mobile
- Prefer one DOM across desktop, tablet, and mobile
- Avoid duplicate mobile-only sections unless strongly justified
- Use reusable classes for repeated visual patterns
- Use variables for repeated colors, spacing, radius, typography, and shadows when useful
- Do not create global classes for one-off coordinates
- Meaningful text must remain real text
- Images must be classified as meaningful or decorative
- DOM reading order should remain logical
- Avoid heavy full-image sections
- Avoid excessive wrappers
- Optimize large visual assets
- Reports and reasoning must be in Persian
- Elementor labels, class names, and technical terms may remain English

---

## Confirmed Stage 2 Summary

Stage 2 is `/decompose`: Controlled Visual Role Decomposition.

It converts a screenshot, reference image, or section description into a role-based visual inventory. It must classify visible groups, meaningful content, repeated component candidates, visual core, decoration layers, overlay or connector candidates, responsive risks, unknowns, and forbidden implementation assumptions.

Stage 2 must not recommend an architecture, score options, produce an Elementor tree, assign exact CSS values, infer actual DOM, or choose widgets/plugins.

Stage 2 now includes an active Example Bank with 12 synthetic, pattern-based decomposition examples. These examples act as few-shot guidance and calibration material for the GPT Project.

A new example authoring standard has been added at `examples/decomposition/EXAMPLE_AUTHORING_STANDARD.md`. It requires metadata, pattern type, complexity, teaching goal, negative examples, stricter unknown handling, accessibility caution, and interactive state uncertainty for future example revisions.

---

## Decomposition Example Bank

Location: `examples/decomposition/`

| ID | Pattern | Purpose |
|---|---|---|
| EX-DCP-001 | Smart Home Connector Section | Connector decoration vs editable feature cards |
| EX-DCP-002 | Split Hero with Dashboard Mockup | Copy area vs visual mockup vs decoration |
| EX-DCP-003 | Services / Feature Cards Grid | Repeated card components and flow groups |
| EX-DCP-004 | Pricing Cards | Repeated plan cards, CTA content, feature lists |
| EX-DCP-005 | Testimonial Cards / Carousel | Quote/avatar/name grouping and carousel unknowns |
| EX-DCP-006 | Logo Strip / Partner Grid | Repeated logos and accessibility unknowns |
| EX-DCP-007 | CTA Band | Primary message, CTA, and background decoration |
| EX-DCP-008 | FAQ Accordion | Interactive content groups and state unknowns |
| EX-DCP-009 | Stats / Metrics | Repeated metric blocks and long-number risks |
| EX-DCP-010 | Product / Portfolio Grid | Repeated item cards with image/title/meta/CTA |
| EX-DCP-011 | Process Timeline | Step sequence, connector lines, order semantics |
| EX-DCP-012 | Overlapping Floating Cards | Overlay risks and responsive collision |

---

## Confirmed Stage 3 Summary

Stage 3 is `/architectures`: Architecture Enumeration.

It uses the completed Stage 2 decomposition to generate multiple viable Elementor V4 implementation architecture candidates. It must not score, rank, recommend, produce a final Elementor tree, or write implementation code.

Stage 3 uses a hybrid strategy:

```text
Baseline Patterns + Section-Specific Variants
```

Required architecture families include:

- A01 — Native Flow Flexbox Architecture
- A02 — Native Grid / Repeated Card Architecture
- A03 — Relative Stage + Absolute Overlay Architecture
- A04 — SVG Connector Layer Architecture
- A05 — Dynamic Loop / Repeater Architecture
- A06 — Widget-Native Architecture
- A07 — Hybrid Native + Scoped Custom CSS Architecture
- A08 — HTML/SVG Widget Isolated Decoration Architecture
- R01 — Rejected Single Static Image Architecture
- R02 — Third-Party Plugin Architecture requiring user approval

Stage 3 usually requires at least 3 viable candidates plus any relevant rejected-risk candidates. Complex overlay, connector, dynamic, carousel, FAQ, pricing, or portfolio sections usually require at least 4 viable candidates.

### Stage 3 v1.1.0 Hardening

Stage 3 has been hardened with these mandatory controls:

1. Architecture Coverage Matrix — every architecture family must be considered, included, omitted, rejected, or approval-gated with a reason.
2. Unknown Propagation Ledger — every architecture-relevant Stage 2 unknown must be carried into the affected candidates or marked not applicable with reason.
3. Hidden Recommendation Ban — no ranking or winner-implying words before `/score-evidence` and `/recommend`.
4. Dynamic/Loop Guardrail — repeated visual groups do not automatically justify Loop Grid, CPT, ACF, WooCommerce, or dynamic architecture.
5. Widget-State Guardrail — visible carousel, FAQ, counter, toggle, filter, or hover states do not prove interaction behavior.
6. Scoped CSS Guardrail — custom CSS candidates must stay scoped; global unscoped CSS is invalid.
7. Tradeoff Requirement — every candidate must state what it preserves, what it sacrifices, and what must be verified later.

---

## Current Next Step

Define Stage 4 — `/score-evidence`.

Goal:
Create an evidence-bound scoring schema that evaluates architecture candidates using the rubric without hallucinating, ranking by taste, or hiding unknowns.
