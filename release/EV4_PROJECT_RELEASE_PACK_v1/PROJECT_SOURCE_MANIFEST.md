# Project Source Manifest — EV4 Release Pack v1

Status: release_candidate_for_controlled_use_with_final_output_ux_case_memory_and_builder_feed_addons
Version: 1.0.4
Date: 2026-06-27

---

## Release Pack Files

```text
release/EV4_PROJECT_RELEASE_PACK_v1/README.md
release/EV4_PROJECT_RELEASE_PACK_v1/PROJECT_INSTRUCTIONS_FINAL.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_CORE_CONTRACTS_BUNDLE.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_STAGE_PROTOCOLS_BUNDLE.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_EXAMPLES_AND_CALIBRATION_BUNDLE.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FIRST_RUN_GUIDE.md
release/EV4_PROJECT_RELEASE_PACK_v1/PROJECT_SOURCE_MANIFEST.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_RUN_COPILOT_INSTRUCTIONS.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FINAL_OUTPUT_UX_PATCH.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_CASE_MEMORY_PROTOCOL.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_BUILDER_COMPANION_FEED_PROTOCOL.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_BUILDER_COMPANION_FEED_v1.1_INTERACTIVE_EXECUTION_PATCH.md
```

---

## UX Add-on Files

```text
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_RUN_COPILOT_INSTRUCTIONS.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FINAL_OUTPUT_UX_PATCH.md
```

Purpose:

```text
EV4_RUN_COPILOT_INSTRUCTIONS.md:
- Companion reviewer for stage outputs.
- Checks whether the latest stage obeyed EV4 contracts.
- Gives the user the exact next prompt.

EV4_FINAL_OUTPUT_UX_PATCH.md:
- Adds PIPELINE RESULT SNAPSHOT to final /handoff-export.
- Adds a simple teacher-style Persian explanation for the user.
- Preserves all flags, unknowns, and production-readiness boundaries.
```

---

## Case Memory Add-on File

```text
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_CASE_MEMORY_PROTOCOL.md
```

Purpose:

```text
Adds optional post-build learning after /handoff-export.
Turns Elementor build feedback into audited case memory.
Defines validation levels.
Blocks case memory from being used by /decompose to invent visual facts.
```

---

## Builder Companion Feed Add-on Files

```text
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_BUILDER_COMPANION_FEED_PROTOCOL.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_BUILDER_COMPANION_FEED_v1.1_INTERACTIVE_EXECUTION_PATCH.md
```

Purpose:

```text
EV4_BUILDER_COMPANION_FEED_PROTOCOL.md:
- Creates a copy-ready feed package for a separate interactive builder chat/model after /handoff-export.
- Defines required builder-facing outputs such as Class Creation & Application Map, Structure Panel Naming Checklist, Builder Step-by-Step Checklist, Widget Mapping Table, Editable Content Map, Asset Replacement Map, Scoped CSS Need Map, and Responsive QA Checklist.
- Preserves the audited handoff as source of truth and blocks redesign, new scoring, hidden assumptions, and production-readiness claims.

EV4_BUILDER_COMPANION_FEED_v1.1_INTERACTIVE_EXECUTION_PATCH.md:
- Adds Approved Handoff Mode, Live Interface Precedence, Control-Existence Failure Protocol, Session State Machine, Persian Control Triggers, Step Size Contract, Per-Element Instruction Contract, V3/V4 Separation Guard, No-Grid Assumption, Checkpoint Confirmation Rule, and Completion Gate Extension.
- Binds the feed to `stages/11_BUILDER_FEED_EXPORT.md` and `ev4-builder-context-package@1.0.0`.
```

---

## Primary Repository Sources

```text
STATUS.md
STATUS_0.16.1_BUILDER_FEED_EXPORT.md
02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md
contracts/STAGE_ANCHOR_CONTRACT.md
contracts/PARTIAL_RERUN_CONTRACT.md
contracts/BUILD_TREE_NAMING_AND_STRUCTURE_CONTRACT.md
diagnostics/LLM_DEBUG_TRACE_CONTRACT.md
references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
experiments/END_TO_END_PIPELINE_TEST_PLAN.md
experiments/E2E-001-smart-home-connector-fixture.md
experiments/E2E-001-test-report.md
experiments/E2E-002-screenshot-validation-report.md
stages/02_RESEARCH.md
stages/02_DECOMPOSE.md
stages/03_ARCHITECTURES.md
stages/04_SCORE_EVIDENCE.md
stages/04_SCORE_EVIDENCE_v1.3_HARDENING_PATCH.md
stages/05_SCORE_AUDIT.md
stages/05_SCORE_AUDIT_v1.1_HARDENING_PATCH.md
stages/05_SCORE_AUDIT_v1.2_HARDENING_PATCH.md
stages/06_RECOMMEND.md
stages/06_RECOMMEND_v1.1_HARDENING_PATCH.md
stages/07_BUILD_TREE.md
stages/08_IMPLEMENTATION.md
stages/09_FINAL_AUDIT.md
stages/10_HANDOFF_EXPORT.md
stages/11_BUILDER_FEED_EXPORT.md
stages/STAGE_8_10_v1.0.1_HARDENING_ALIGNMENT_PATCH.md
rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md
schemas/ev4-builder-context-package.schema.json
examples/decomposition/README.md
examples/decomposition/EXAMPLE_AUTHORING_STANDARD.md
examples/scoring/README.md
cases/README.md
```

---

## Validation State

```yaml
validation_state:
  prompt_pack_full_pipeline:
    status: pass_with_minor_flags
    evidence: experiments/E2E-001-test-report.md
  raster_screenshot_visual_interpretation:
    status: pass_with_minor_flags
    evidence: experiments/E2E-002-screenshot-validation-report.md
  final_output_ux_addons:
    status: added_v1.0.1
    evidence:
      - release/EV4_PROJECT_RELEASE_PACK_v1/EV4_RUN_COPILOT_INSTRUCTIONS.md
      - release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FINAL_OUTPUT_UX_PATCH.md
  case_memory_protocol:
    status: added_v1.0.0
    evidence:
      - release/EV4_PROJECT_RELEASE_PACK_v1/EV4_CASE_MEMORY_PROTOCOL.md
      - cases/README.md
  builder_companion_feed_protocol:
    status: added_v1.1.0
    evidence:
      - release/EV4_PROJECT_RELEASE_PACK_v1/EV4_BUILDER_COMPANION_FEED_PROTOCOL.md
      - release/EV4_PROJECT_RELEASE_PACK_v1/EV4_BUILDER_COMPANION_FEED_v1.1_INTERACTIVE_EXECUTION_PATCH.md
      - stages/11_BUILDER_FEED_EXPORT.md
      - schemas/ev4-builder-context-package.schema.json
  live_elementor_rendering:
    status: not_validated
  real_elementor_export_json_or_EDIS:
    status: not_validated
  exact_pixel_matching:
    status: not_validated
```

---

## Recommended Upload Set for ChatGPT Project

Minimum upload set:

```text
PROJECT_INSTRUCTIONS_FINAL.md
EV4_CORE_CONTRACTS_BUNDLE.md
EV4_STAGE_PROTOCOLS_BUNDLE.md
EV4_EXAMPLES_AND_CALIBRATION_BUNDLE.md
EV4_FIRST_RUN_GUIDE.md
```

Recommended add-ons:

```text
EV4_RUN_COPILOT_INSTRUCTIONS.md
EV4_FINAL_OUTPUT_UX_PATCH.md
EV4_CASE_MEMORY_PROTOCOL.md
EV4_BUILDER_COMPANION_FEED_PROTOCOL.md
EV4_BUILDER_COMPANION_FEED_v1.1_INTERACTIVE_EXECUTION_PATCH.md
```

Optional upload:

```text
PROJECT_SOURCE_MANIFEST.md
README.md
```

---

## File-limit note

If the ChatGPT Project file limit is reached, prefer uploading active add-ons over optional files.

Suggested replacement order:

```text
1. Remove README.md first if needed.
2. Remove PROJECT_SOURCE_MANIFEST.md second if needed.
3. Keep the five core release files.
4. Add EV4_RUN_COPILOT_INSTRUCTIONS.md if you want a companion review chat.
5. Add EV4_FINAL_OUTPUT_UX_PATCH.md if you want clearer final outputs.
6. Add EV4_CASE_MEMORY_PROTOCOL.md if you want post-build learning.
7. Add EV4_BUILDER_COMPANION_FEED_PROTOCOL.md if you want builder feed output.
8. Add EV4_BUILDER_COMPANION_FEED_v1.1_INTERACTIVE_EXECUTION_PATCH.md if you want the downstream interactive Builder Assistant session guardrails.
```

---

## Notes

The release pack is intentionally smaller than the repository. The repository is the source of truth; this folder is the operational bundle for ChatGPT Project usage.
