# EV4 Case Memory Protocol

Status: active_addon_for_post_build_learning
Version: 1.0.0
Applies after: `/handoff-export`
Language: Persian reports, English technical identifiers allowed

## Purpose

This protocol defines how a completed Elementor build can become a controlled Case Memory entry after the main EV4 pipeline has finished.

The goal is to let the system learn from real builds without weakening evidence discipline.

## Core Rule

A built section can become a reusable case only after:

1. the original pipeline reached `/handoff-export`;
2. the user provided post-build feedback;
3. available evidence was inventoried;
4. a validation level was assigned;
5. a case draft was produced;
6. the case draft was audited;
7. the user explicitly approved repository export.

## Optional Post-Handoff Loop

```text
/handoff-export
/post-build-feedback
/case-memory-author
/case-memory-audit
/case-repo-export
```

These stages are optional and must not replace the main EV4 pipeline.

## Validation Levels

```text
pipeline_completed_not_built
builder_confirmed
screenshot_after_build_confirmed
mobile_tablet_screenshot_confirmed
export_json_or_EDIS_validated
browser_device_QA_validated
regression_case
```

Rules:

- Do not assign a higher validation level than the supplied evidence supports.
- A user OK alone is `builder_confirmed`.
- An after-build screenshot can support `screenshot_after_build_confirmed`.
- Mobile/tablet screenshots can support `mobile_tablet_screenshot_confirmed`.
- Elementor export JSON or EDIS evidence can support `export_json_or_EDIS_validated`.
- Browser/device QA evidence can support `browser_device_QA_validated`.
- Only stable, validated cases may become `regression_case`.

## Stage Use Matrix

| Stage | Case Memory use | Restriction |
|---|---|---|
| `/decompose` | not allowed for visual facts | screenshot/user evidence only |
| `/architectures` | allowed for risk patterns and candidate caution | must not force a copied architecture |
| `/score-evidence` | not allowed to boost scores | rubric plus Stage 2/3 evidence only |
| `/score-audit` | allowed to detect source leakage | must not add scores |
| `/recommend` | only if Stage 5 routes a tie/source clarification | no hidden preference signal |
| `/build-tree` | allowed as structural precedent after recommendation | must preserve current recommendation |
| `/implementation` | allowed for practical implementation cautions | must not invent exact values |
| `/final-audit` | allowed to check known risk survival | must not soften findings |
| `/handoff-export` | allowed to package lessons as future reference | must preserve flags |

Core prohibition:

```text
Case Memory must never be used in `/decompose` to invent visual groups, assume mobile behavior, assume clickability, or classify content without current evidence.
```

## Case Folder Standard

```text
cases/
  CASE-EV4-###-[slug]/
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

Image files may be added when available:

```text
input/before-screenshot.png
output/after-screenshot.png
output/after-mobile.png
output/after-tablet.png
```

## Required Case Metadata

```yaml
case_id:
case_title:
pattern_type:
source_pipeline_run:
selected_candidate_id:
handoff_status:
validation_level:
user_build_result: OK | Not OK | Mixed | Unknown
before_evidence:
after_evidence:
export_evidence: available | not_available
mobile_tablet_evidence: available | not_available
allowed_future_use:
forbidden_future_use:
deprecated: false
```

## Lesson Rules

Lessons must be scoped observations, not global laws.

Allowed:

```text
In this validated connector-heavy case, mobile connector behavior required explicit QA.
```

Forbidden:

```text
All connector-heavy sections should hide connectors on mobile.
```

## Completion Criteria

```yaml
case_memory_protocol_checks:
  post_build_feedback_collected: required
  validation_level_declared: required
  stage_2_visual_inference_blocked: required
  case_audit_before_repository_export: required
  explicit_user_approval_before_repository_write: required
  branch_and_PR_required: required
  production_ready_claim_blocked_without_export_render_QA: required
```
