# Repository Repair Recommendation Handoff Contract

Status: active
Contract identity: `ev4-repository-repair-recommendation-handoff@1.0.0`
Owner repository: `rezahh107/EV4-Architect-Repo`
Compatibility: `additive_nonbreaking`

## Purpose

This contract separates current Architect Run repair from repository root-cause repair.

```text
Current Run repair
= remains inside the active Architect conversation
= follows the valid Repair/Success Anchor and Partial Rerun route

Repository root-cause repair
= separate repository-maintenance session
= requires fresh live-repository verification
= may produce at most one bounded Draft PR after Scope Gate authorization
```

A Repository Repair Recommendation is informational. It is not a Stage Artifact, Stage Anchor, Validation Bundle, repository-write authority, proof of a repository defect, technical approval, Merge authorization, deployment authorization, or runtime-enforcement claim.

## Executable authority

The sole repository-side executable authority is:

```text
scripts/repository_repair_handoff.py
```

It owns:

```python
validate_repository_repair_handoff_record(record)
evaluate_repository_repair_handoff_eligibility(record)
render_repository_maintenance_prompt(validated_record)
validate_rendered_repository_maintenance_prompt(prompt)
```

Prose, fixtures, tests, Debug Trace output, Project Instructions, and `AGENTS.md` must reference these functions. They must not define a competing eligibility predicate or maintain independent full prompt bodies.

## Closed Run-state relationship

The validator owns this minimal relationship:

| `current_run_status` | allowed `current_run_repair_status` | emission meaning |
|---|---|---|
| `in_progress` | `pending` | never eligible |
| `repairing` | `pending` | never eligible |
| `repaired` | `validated` | eligible only when the repository-gap predicate also passes |
| `blocked` | `failed` | stable and eligible only when the repository-gap predicate also passes |
| `terminal` | `not_applicable` | stable and eligible only when the repository-gap predicate also passes |

All other combinations fail closed. A `repaired` Run with `pending` or `failed` repair status is not eligible.

## Eligibility

The evaluator returns a structured result:

```text
eligible
not_eligible
invalid_input
```

with a concise `reason_code`.

A full handoff is eligible only when:

```text
current_run_status is stable and contract-valid
repository_gap_state is confirmed or probable
repository_gap_class is in the closed allowed class set
ordinary_run_error is false
```

`possible` permits only a brief review suggestion. `insufficient_evidence` and `not_repository_related` emit no handoff. Missing fields, unknown decision-bearing values, contradictory Run/repair states, and pre-rendered prompt input fail closed.

Allowed repository-gap classes are owned by the executable module:

```text
repository_enforcement_gap
contract_ambiguity
validator_gap
missing_negative_regression
stage_boundary_escape_route
conflicting_authorities
fail_late_detection
repeatable_prompt_or_protocol_defect
```

Ordinary isolated errors do not trigger a full handoff, including missing user input, temporary tool failure, a formatting error already rejected by an adequate validator, or an arithmetic error correctly rejected at its owning boundary.

## Validated record

The validator requires at least:

```text
handoff_schema
incident_id
source_run_id
current_run_status
current_run_repair_status
repository_gap_state
repository_gap_class
ordinary_run_error
first_broken_stage
first_detection_stage
root_cause_summary
repository_gap_hypothesis
evidence_summary
violated_or_weak_authorities
recurrence_risk
current_run_resume_stage
repository_maintenance_scope
forbidden_actions
```

Unknown factual repository details may remain `unknown` or visible placeholders. Decision-bearing states and classes are closed enums. The validator rejects an input field named `standalone_repair_prompt`; prompt bytes must come from the canonical renderer.

Required forbidden actions include:

```text
modify_repository_inside_active_architect_run
merge
approve
deploy
modify_repository_settings
```

## Deterministic prompt rendering

`render_repository_maintenance_prompt()` accepts only a validated eligible record. It is the sole executable source for emitted standalone prompt bodies.

The canonical section order is:

```text
[ROLE]
[TARGET REPOSITORY]
[OBSERVED INCIDENT]
[CURRENT-RUN EVIDENCE]
[SUSPECTED REPOSITORY GAP]
[UNCERTAINTIES]
[REQUIRED LIVE REPOSITORY REVIEW]
[SOLUTION COMPARISON REQUIREMENT]
[SELECTION CRITERIA]
[BOUNDED IMPLEMENTATION AUTHORITY]
[NON-GOALS]
[VALIDATION REQUIREMENTS]
[DRAFT PR REQUIREMENT]
[INDEPENDENT REVIEW REQUIREMENT]
[FINAL RESPONSE FORMAT]
[STOP CONDITIONS]
```

Every prompt explicitly carries the incident and Run identities, Run repair state, broken and detection stages, repository-gap state/class/hypothesis, and current Run resume stage. It requires live repository revalidation, exact current Head verification, authority inspection, Scope Gate evaluation, credible option comparison, the smallest complete solution, at most one bounded Draft PR, and fresh independent exact-Head review.

Every prompt explicitly reports:

```text
merge_performed: false
approval_performed: false
deployment_performed: false
```

## User-facing recommendation

<!-- EV4_REPOSITORY_REPAIR_HANDOFF_USER_SECTION_START -->

```text
## پیشنهاد بررسی و اصلاح ریشه‌ای ریپو

تعمیر اجرای جاری انجام شده یا اجرای جاری به وضعیت پایدار رسیده است.

شواهد بیرونی نشان می‌دهد ممکن است یک ضعف قابل‌تکرار در قراردادها، Gateها، Validatorها یا کنترل‌های ریپو در رخداد یا کشف دیرهنگام خطا نقش داشته باشد.

این تشخیص قطعی نیست. اجرای فعال Architect مجاز به تغییر ریپو نیست. پرامپت مستقل repository-maintenance فقط از رکورد معتبر و توسط renderer رسمی تولید می‌شود و باید در یک گفتگوی جداگانه با بررسی زنده ریپو اجرا شود.
```

<!-- EV4_REPOSITORY_REPAIR_HANDOFF_USER_SECTION_END -->

## Run continuity

The recommendation does not replace or modify a Repair Anchor, Success Anchor, Validation Bundle, or earliest safe rerun stage. A repaired Run continues only from its valid repaired Anchor. A blocked or terminal Run remains non-resumable even when a handoff is emitted.

The active Architect Run must not modify repository files, create a branch, commit, push, open or update a PR, approve, merge, deploy, release, enable auto-merge, or modify repository settings.

## Fixtures and tests

Fixtures are data-first:

```text
fixture record
→ canonical validator
→ canonical evaluator
→ canonical renderer when eligible
→ asserted result
```

Fixtures must not contain `should_emit_handoff`, a competing predicate, or hand-authored `standalone_repair_prompt` bodies. One minimal renderer-produced golden snapshot may be retained to detect deterministic byte drift.

Repository tests may establish fixture/test and exact-Head CI enforcement for the tested revision. They do not establish real conversational runtime enforcement, downstream enforcement, automatic diagnosis, automatic repository repair, self-healing, repository-wide enforcement, or production readiness.
