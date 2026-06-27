# Elementor V4 Architect Prompt Pack

سیستم پرامپت معماری و audit برای Elementor V4

This repository stores the stable instructions, stage specifications, contracts, rubrics, calibration cases, and examples for a GPT Project that works as an **Elementor V4 layout architect and auditor**.

---

## Core Idea

The system is a staged prompt pipeline, not one giant prompt.

Its job is to answer:

```text
What is the safest, editable, Elementor-native architecture for this section?
```

It does **not** act as the final interactive builder assistant. Instead, after the architecture pipeline is completed, it can export a builder-ready feed for a separate downstream assistant.

---

## Current Pipeline

```text
/intake
/research
/decompose
/architectures
/score-evidence
/score-audit
/recommend
/build-tree
/implementation
/final-audit
/handoff-export
/builder-feed-export
```

### Stage 11 — `/builder-feed-export`

`/builder-feed-export` is a terminal bridge stage after `/handoff-export`.

It converts the audited EV4 handoff into:

```text
Builder_Context_Package
```

This package is designed for a separate interactive Elementor builder chat/project.

It must not:

```text
- redesign;
- re-score;
- re-recommend;
- change selected_candidate_id;
- add or remove approved classes;
- write final CSS;
- resolve unknowns by assumption;
- claim production readiness.
```

It may:

```text
- package approved structure;
- package Class Creation & Application Map;
- package Structure Panel Naming Checklist;
- package Widget Mapping Table;
- package Editable Content Map;
- package Decoration-Only Map;
- package Scoped CSS Need Map;
- package first builder action batch;
- export Builder Assistant guardrails.
```

---

## Repository Role

This repo is the **Architect** system:

```text
EV4 Architect
= تحلیل، candidateها، scoring، audit، recommendation، build tree، implementation plan، handoff، builder feed
```

The downstream builder assistant is separate:

```text
EV4 Builder Assistant
= اجرای تعاملی داخل Elementor بر اساس Builder_Context_Package
```

Companion repo:

```text
https://github.com/rezahh107/EV4-Builder-Assistant-Repo
```

---

## System Flow

```text
Reference Section Screenshot
        │
        ▼
EV4 Architect Pipeline
/intake → /decompose → /architectures → /score-evidence → /score-audit
→ /recommend → /build-tree → /implementation → /final-audit → /handoff-export
        │
        ▼
/builder-feed-export
        │
        ▼
Builder_Context_Package
        │
        ▼
EV4 Builder Assistant Repo / Project
        │
        ▼
Interactive Elementor build
        │
        ▼
Optional downstream: EV4 Responsive Architect
```

---

## Production Boundary

This project may produce a controlled builder handoff or a builder context package.

It must not claim:

```text
production-ready
release-ready
pixel-perfect
live Elementor validated
export JSON / EDIS validated
```

unless real validation evidence exists.

---

## Important Files

```text
STATUS.md
STATUS_0.16.1_BUILDER_FEED_EXPORT.md
02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md
contracts/STAGE_ANCHOR_CONTRACT.md
contracts/PARTIAL_RERUN_CONTRACT.md
contracts/BUILD_TREE_NAMING_AND_STRUCTURE_CONTRACT.md
diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md
stages/10_HANDOFF_EXPORT.md
stages/11_BUILDER_FEED_EXPORT.md
schemas/ev4-builder-context-package.schema.json
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_BUILDER_COMPANION_FEED_PROTOCOL.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_BUILDER_COMPANION_FEED_v1.1_INTERACTIVE_EXECUTION_PATCH.md
```

---

## Current Status

```yaml
project_status:
  architect_pipeline: hardened_for_controlled_handoff
  builder_feed_export: added
  builder_context_package_schema: added
  live_elementor_rendering: not_validated
  real_elementor_export_json_or_EDIS: not_validated
  exact_pixel_matching: not_validated
  production_ready: false
```

Next downstream work belongs in:

```text
https://github.com/rezahh107/EV4-Builder-Assistant-Repo
```
