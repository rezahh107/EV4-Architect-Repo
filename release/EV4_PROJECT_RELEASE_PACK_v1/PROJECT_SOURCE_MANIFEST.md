# Project Source Manifest — EV4 Release Pack v1

Status: release_candidate_for_controlled_use_with_final_output_ux_addons
Version: 1.0.1
Date: 2026-06-22

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
```

---

## UX Add-on Files

```text
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_RUN_COPILOT_INSTRUCTIONS.md
release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FINAL_OUTPUT_UX_PATCH.md
```

Purpose:

```text
EV4_RUN_COPILOT_INSTRUCTIONS.md
- Companion reviewer for stage outputs.
- Checks whether the latest stage obeyed EV4 contracts.
- Gives the user the exact next prompt.

EV4_FINAL_OUTPUT_UX_PATCH.md
- Adds PIPELINE RESULT SNAPSHOT to final /handoff-export.
- Adds a simple teacher-style Persian explanation for the user.
- Preserves all flags, unknowns, and production-readiness boundaries.
```

---

## Primary Repository Sources

```text
STATUS.md
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
stages/STAGE_8_10_v1.0.1_HARDENING_ALIGNMENT_PATCH.md
rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md
examples/decomposition/README.md
examples/decomposition/EXAMPLE_AUTHORING_STANDARD.md
examples/scoring/README.md
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
    status: added_v1.0.0
    evidence:
      - release/EV4_PROJECT_RELEASE_PACK_v1/EV4_RUN_COPILOT_INSTRUCTIONS.md
      - release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FINAL_OUTPUT_UX_PATCH.md
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

Recommended UX add-ons:

```text
EV4_RUN_COPILOT_INSTRUCTIONS.md
EV4_FINAL_OUTPUT_UX_PATCH.md
```

Optional upload:

```text
PROJECT_SOURCE_MANIFEST.md
README.md
```

---

## File-limit note

If the ChatGPT Project file limit is reached, prefer uploading the UX add-ons over optional files.

Suggested replacement order:

```text
1. Remove README.md first if needed.
2. Remove PROJECT_SOURCE_MANIFEST.md second if needed.
3. Keep the five core release files.
4. Add EV4_RUN_COPILOT_INSTRUCTIONS.md if you want a companion review chat.
5. Add EV4_FINAL_OUTPUT_UX_PATCH.md if you want clearer final outputs.
```

---

## Notes

The release pack is intentionally smaller than the repository. The repository is the source of truth; this folder is the operational bundle for ChatGPT Project usage.
