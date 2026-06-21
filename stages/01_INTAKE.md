# Stage 1 — /intake: Project Defaults + Exception Check

Status: confirmed  
Version: 1.0.0  

---

## Purpose

The `/intake` phase is a lightweight constraint check.

It must not ask repetitive setup questions that are already answered by Project Defaults.

---

## Rules

Use Project Defaults unless the user explicitly overrides them.

Ask only blocking or architecture-changing questions.

Do not recommend an architecture during `/intake`.  
Do not score architectures during `/intake`.  
Do not produce an Elementor tree during `/intake`.

---

## Project Defaults

- Elementor V4
- Elementor Pro available
- Container/Flexbox-first workflow
- Structure Panel clarity matters
- Scoped Custom CSS is allowed
- SVG Widget is allowed
- HTML Widget is allowed when practical
- No third-party plugin/add-on may be included in the final recommendation unless approved first
- Meaningful text, cards, icons, buttons, and images should remain editable when practical
- Do not convert meaningful content into a single static image
- Primary content should remain in normal flow
- Absolute positioning is allowed only for controlled overlays inside a clearly named relative Stage
- Decorative connector lines may be SVG and may be hidden or simplified on mobile
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

## When to Ask Questions

Ask only if the answer can change the architecture.

Valid blocking questions include:

- A constraint conflicts with Project Defaults.
- A third-party plugin/add-on seems significantly useful.
- The section requires behavior not covered by defaults.
- Mobile behavior changes the architecture.
- Source assets are unclear and affect the layout strategy.

Do not repeatedly ask:

- Do you have Elementor Pro?
- Is Custom CSS allowed?
- Is SVG allowed?
- Is HTML Widget allowed?
- Should content remain editable?

---

## Output Format

```text
INTAKE SNAPSHOT

Using Project Defaults:
- ...

Section-specific overrides:
- ...

Unknowns:
- ...

Blocking questions:
- ...

Allowed next step:
- /decompose
```

---

## Pass Criteria

Stage 1 is successful when:

- It summarizes relevant defaults without repeating fixed questions.
- It identifies section-specific overrides, if any.
- It lists non-blocking unknowns without stopping the workflow.
- It asks only blocker or architecture-changing questions.
- It allows `/decompose` when no blocking question exists.

---

## Example Output

```text
INTAKE SNAPSHOT

Using Project Defaults:
- Elementor V4
- Elementor Pro available
- Scoped Custom CSS allowed
- SVG Widget allowed
- HTML Widget allowed when practical
- Editable real content required
- Primary content stays in normal flow
- No third-party plugin unless approved

Section-specific overrides:
- None

Unknowns:
- Exact image dimensions
- Final breakpoint values

Blocking questions:
- None

Allowed next step:
- /decompose
```
