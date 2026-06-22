# EV4 Case Memory Protocol

Status: active_addon_for_post_build_learning
Version: 1.0.1
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
/builder-companion-feed optional, if the user wants a separate interactive builder chat
/post-build-feedback
/case-memory-author
/case-memory-audit
/case-repo-export
```

These stages are optional and must not replace the main EV4 pipeline.

`/builder-companion-feed` is a build execution bridge, not a validation stage. It can help the user build from the handoff in another chat/model, but it does not create Case Memory by itself.

## Validation Levels

```text
pipeline_completed_not_built
builder_companion_feed_created
builder_confirmed
screenshot_after_build_confirmed
mobile_tablet_screenshot_confirmed
export_json_or_EDIS_validated
browser_device_QA_validated
regression_case
```

Rules:

- Do not assign a higher validation level than the supplied evidence supports.
- A Builder Companion Feed alone is `builder_companion_feed_created`, not proof that the section was built.
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
| `/builder-companion-feed` | allowed to generate a step-by-step build package from the audited handoff | must not validate the build or modify the handoff |
| `/post-build-feedback` | allowed to record actual build feedback and evidence | must not generalize into global law |
| `/case-memory-author` | allowed to draft a case from feedback | must mark validation level correctly |
| `/case-memory-audit` | allowed to audit case safety before repo export | must block source leakage into `/decompose` |
| `/case-repo-export` | allowed only after explicit user approval | branch and PR required |

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
    builder-feed/
      builder-companion-feed.md
      class-application-map.md
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
builder_companion_feed: available | not_available
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

## Repository Export Rule

The model may create a draft case and audit it. It must not update GitHub until the user explicitly approves repository export.

When repository export is approved:

```text
- create or reuse a feature branch;
- add the case files under cases/;
- include available before/after evidence references;
- open a pull request;
- do not merge automatically.
```

## Completion Criteria

```yaml
case_memory_protocol_checks:
  post_build_feedback_collected: required
  validation_level_declared: required
  stage_2_visual_inference_blocked: required
  builder_companion_feed_separated_from_validation: required
  case_audit_before_repository_export: required
  explicit_user_approval_before_repository_write: required
  branch_and_PR_required: required
  production_ready_claim_blocked_without_export_render_QA: required
```
