# EV4 Project Release Pack v1

Status: release_candidate_fail_closed_by_validation_profile
Pack schema: ev4-project-release-pack@1.0.0
Date: 2026-06-22
Target runtime: ChatGPT Project

---

## Purpose

This folder packages the EV4 Architect Prompt Pack into a small set of files suitable for upload into a ChatGPT Project.

The repository remains the source of truth. This release pack is the operational subset for day-to-day use.

---

## Files

```text
PROJECT_INSTRUCTIONS_FINAL.md
EV4_CORE_CONTRACTS_BUNDLE.md
EV4_STAGE_PROTOCOLS_BUNDLE.md
EV4_EXAMPLES_AND_CALIBRATION_BUNDLE.md
EV4_FIRST_RUN_GUIDE.md
PROJECT_SOURCE_MANIFEST.md
```

---

## Release Boundary

This pack is ready for controlled use with real screenshots.

Validated:

```text
- full prompt-pack contract through /handoff-export using E2E-001 textual fixture
- raster screenshot role interpretation using E2E-002 screenshot validation
- historical Stage Anchor v1.1 evidence readability
- current Stage Anchor v1.4 + Validation Bundle v1.2 transaction for `/decompose` through `/score-audit`
- fail-closed Validation Profiles for every other non-terminal Stage
- RAG/TUYA source boundaries
- Stage 8–10 alignment patch
```

Not validated:

```text
- live Elementor rendering
- real Elementor export JSON
- EDIS validation
- browser/device QA
- exact pixel matching
```

---

## Recommended ChatGPT Project Setup

Upload the five operational files plus this README if file budget allows. Use `PROJECT_INSTRUCTIONS_FINAL.md` as the Project Instructions source.

Recommended project name:

```text
EV4 Architect — Controlled Use
```

Recommended memory mode:

```text
Project-only memory, where available.
```
