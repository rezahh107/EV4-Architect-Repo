# STATUS — Elementor V4 Architect Prompt Pack

Version: 0.2.2  
Status: in_progress  
Last confirmed stage: Stage 2 — `/decompose`  
Current next stage: Stage 3 — `/architectures`  
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
| `/research` | draft | Documentation source policy remains useful, but Stage 2 embeds initial research grounding |
| `/decompose` | confirmed_with_example_bank | Controlled Visual Role Decomposition; no architecture recommendation allowed |
| `/decomposition-example-bank` | active_enhanced | 12 synthetic pattern-based examples plus authoring standard under `examples/decomposition/` |
| `/architectures` | current_next | Needs architecture enumeration rules |
| `/score-evidence` | not_started | Needs Rubric v2 and evidence schema |
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

## Current Next Step

Define Stage 3 — `/architectures`.

Goal:
Create rules for enumerating all viable Elementor V4 implementation architectures before scoring or recommendation.
