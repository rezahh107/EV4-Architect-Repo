# EV4 Case Memory Library

Status: initialized
Version: 1.0.0

This folder stores controlled EV4 cases created after a real Elementor build has been attempted from a completed `/handoff-export`.

Each case must follow `EV4_CASE_MEMORY_PROTOCOL.md` and preserve evidence level, source-access limits, unknowns, and validation boundaries.

## What belongs here

A case may be added when there is at least:

```text
- completed EV4 pipeline run ending in /handoff-export
- user post-build feedback
- validation level assignment
- case draft
- case audit result
- explicit user approval for repository export
```

## What does not belong here

```text
- raw chat excerpts without audit
- unreviewed model outputs
- screenshots with no case metadata
- global rules inferred from one build
- production-ready claims without render/export/QA evidence
```

## Standard case path

```text
cases/CASE-EV4-###-[slug]/
  case.md
  input/
    before-screenshot.md
    before-notes.md
  output/
    after-screenshot.md
    builder-feedback.md
    optional-export-json.md
  evidence/
    validation-summary.md
    regression-prompt.md
```

## Boundary

Case Memory must not be used by `/decompose` to infer visual facts. It may inform later stages only where the protocol allows it.
