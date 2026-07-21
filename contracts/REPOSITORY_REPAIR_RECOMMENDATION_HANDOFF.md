# Repository Repair Recommendation Handoff Contract

Status: active
Contract identity: `ev4-repository-repair-recommendation-handoff@1.0.0`
Owner repository: `rezahh107/EV4-Architect-Repo`
Compatibility: `additive_nonbreaking`

## Purpose

This contract defines the bounded user-facing escalation used when an Architect run has reached a stable repaired, blocked, or terminal state and external evidence indicates a repeatable repository enforcement gap may have contributed to the incident.

The handoff separates two authorities:

```text
Current Run Repair
= allowed inside the active Architect conversation
= governed by the current Repair Anchor, Success Anchor, Partial Rerun plan, and validated Run evidence

Repository Root-Cause Repair
= separate repository-maintenance session
= requires fresh live-repository inspection
= may produce only a bounded Draft PR when Scope is independently validated
```

The active Architect run must not edit repository files, create a repository branch, commit, push, open a pull request, approve, merge, deploy, or enable auto-merge.

## Non-authority

A Repository Repair Recommendation Handoff is not:

- a Stage Artifact;
- a Stage Anchor;
- a Validation Bundle, Receipt, Boundary, or machine-validation result;
- repository modification authorization for the active Architect run;
- proof that a repository defect exists;
- proof that the proposed repair is correct;
- technical approval;
- a merge recommendation;
- deployment or release authorization.

The incident description is evidence to investigate, not an authoritative diagnosis.

## Repository-gap classification

A full handoff may be emitted only when both conditions are true:

1. the current run is in a stable `repaired`, `blocked`, or `terminal` state; and
2. `repository_gap_state` is `confirmed` or `probable` for an allowed repository-gap class.

Allowed classes:

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

Evidence states:

```text
confirmed
probable
possible
insufficient_evidence
not_repository_related
```

Trigger rule:

```text
emit_full_handoff =
  current_run_status in {repaired, blocked, terminal}
  and repository_gap_state in {confirmed, probable}
  and repository_gap_class in allowed_repository_gap_classes
```

For `possible`, the Architect may state that repository review could be useful, but it must not emit the full standalone maintenance prompt. For `insufficient_evidence` or `not_repository_related`, no handoff is emitted.

Do not emit a full handoff for ordinary isolated run errors such as:

```text
user input missing
temporary tool failure
single arithmetic mistake already caught by existing controls
model formatting error with an adequate existing validator
unavailable external source
one-off misunderstanding with no repeatability evidence
```

## Timing and run continuity

The handoff is evaluated only after the current run repair route is determined and the run has reached a stable repaired, blocked, or terminal state.

- Downstream Run outputs remain invalid until the current Run repair is validated.
- The repository handoff does not change the earliest safe rerun stage.
- The repository handoff does not replace a Repair Anchor or Success Anchor.
- A repaired and validated current Run may continue only from its valid repaired Stage Anchor.
- A blocked Run remains blocked even when a repository handoff is emitted.
- The recommendation itself is informational and must not independently block an otherwise valid current Run.

## Semantic handoff fields

The user-facing output may be Markdown, but these semantic fields must be explicit:

```yaml
handoff_schema: ev4-repository-repair-recommendation-handoff@1.0.0
incident_id:
source_run_id:
current_run_status: repaired | blocked | terminal
current_run_repair_status:
repository_gap_state: confirmed | probable
repository_gap_class:
first_broken_stage:
first_detection_stage:
root_cause_summary:
repository_gap_hypothesis:
evidence_summary:
violated_or_weak_authorities:
recurrence_risk:
current_run_resume_stage:
repository_maintenance_scope:
forbidden_actions:
standalone_repair_prompt:
```

Unknown values must remain `unknown` or visible placeholders. Do not invent repository names, commit SHAs, PR numbers, paths, Schema IDs, Validator IDs, Workflow names, test results, or evidence.

## Incident evidence requirements

The handoff must concisely preserve:

- what failed;
- what the model previously claimed;
- what later contradicted the claim;
- which Stage first owned the missing or invalid information;
- where the defect was first detected;
- which outputs became invalid;
- how the current Run was repaired or why it remains blocked;
- why recurrence is plausible;
- which repository controls might be involved.

Use external traces, Artifact identities, diagnostic codes, Stage IDs, contract references, Validator output, and concise evidence summaries. Do not include the full conversation transcript by default. Do not request or expose hidden chain-of-thought.

## User-facing section

<!-- EV4_REPOSITORY_REPAIR_HANDOFF_USER_SECTION_START -->

```text
## پیشنهاد بررسی و اصلاح ریشه‌ای ریپو

تعمیر اجرای جاری انجام شد یا به وضعیت پایدار رسیده است.

بررسی خطا نشان می‌دهد این رخداد احتمالاً فقط یک اشتباه موردی در این گفتگو نبوده و ممکن است یک ضعف قابل‌تکرار در قراردادها، Gateها، Validatorها یا کنترل‌های ریپو نیز در ایجاد یا کشف دیرهنگام آن نقش داشته باشد.

در این اجرای Architect، من مجاز نیستم از مسیر جاری خارج شوم یا فایل‌های ریپو را تغییر دهم.

می‌توانید پرامپت مستقلی را که در ادامه آمده است در یک گفتگوی جدید به یک مدل دارای دسترسی GitHub یا محیط پیاده‌سازی بدهید.

مدل نگهدارنده باید:

- وضعیت زنده ریپو را مستقلاً بررسی کند؛
- میان خطای اجرای جاری و نقص ساختاری ریپو تفکیک قائل شود؛
- راه‌حل‌های ممکن را استخراج و مقایسه کند؛
- متناسب‌ترین روش اصلاح را پیشنهاد دهد؛
- و فقط در صورت احراز Scope، تغییر را در یک Draft PR محدود پیاده‌سازی کند.

این پیشنهاد به معنی اثبات قطعی باگ ریپو، تأیید یک راه‌حل مشخص یا مجوز Merge نیست.
```

<!-- EV4_REPOSITORY_REPAIR_HANDOFF_USER_SECTION_END -->

The wording may be adapted for incident facts, but its authority boundary and uncertainty must remain explicit.

## Standalone repository-maintenance prompt

Every emitted full handoff must contain a self-contained prompt with all sections below. The maintenance model must be able to execute it without access to the active Architect conversation.

<!-- EV4_REPOSITORY_REPAIR_HANDOFF_PROMPT_START -->

```text
[ROLE]

Act as the bounded repository-maintenance implementer and independent root-cause verifier for the target repository.

[TARGET REPOSITORY]

repository: [TARGET_REPOSITORY_OR_UNKNOWN]
default_branch: [DEFAULT_BRANCH_OR_UNKNOWN]
observed_revision: [OBSERVED_REVISION_OR_UNKNOWN]

[OBSERVED INCIDENT]

incident_id: [INCIDENT_ID]
source_run_id: [SOURCE_RUN_ID]
current_run_status: [REPAIRED_BLOCKED_OR_TERMINAL]
first_broken_stage: [STAGE_ID_OR_UNKNOWN]
first_detection_stage: [STAGE_ID_OR_UNKNOWN]

Summarize what failed, what was previously claimed, and what later evidence contradicted that claim.

[CURRENT-RUN EVIDENCE]

Provide concise external evidence only:
- Artifact, trace, diagnostic, Stage, contract, or Validator identities;
- invalidated downstream outputs;
- current Run repair result or blocking reason;
- current Run resume Stage or `none`.

Do not request hidden chain-of-thought and do not assume access to the original conversation.

[SUSPECTED REPOSITORY GAP]

repository_gap_state: [CONFIRMED_OR_PROBABLE]
repository_gap_class: [ALLOWED_CLASS]
repository_gap_hypothesis: [HYPOTHESIS]
recurrence_risk: [RISK_SUMMARY]

The incident description is evidence to investigate, not an authoritative diagnosis.
The repository-maintenance model must verify or reject the hypothesis from live repository evidence.

[UNCERTAINTIES]

List every unknown repository identity, path, Schema, Validator, Workflow, test result, or causal claim as `unknown` or a visible placeholder. Do not invent missing evidence.

[REQUIRED LIVE REPOSITORY REVIEW]

Before modifying anything:
1. revalidate the live default branch and exact current Head;
2. inspect current `AGENTS.md`, `STATUS.md`, active overrides, governance files, contracts, schemas, validators, diagnostics, fixtures, tests, workflows, and open pull requests;
3. inspect any newer repair-mode, diagnostic, partial-rerun, Stage Anchor, or overlapping patch;
4. determine whether the incident is a run-only defect, documentation weakness, contract ambiguity, missing validator, missing sequence enforcement, missing negative regression, conflicting authorities, or another evidence-backed cause;
5. stop if live authorities conflict or materially equivalent work already exists.

[SOLUTION COMPARISON REQUIREMENT]

Identify at least two materially different repair options when credible alternatives exist. Do not blindly implement the Architect Run hypothesis.

[SELECTION CRITERIA]

Compare credible options by:
- effectiveness;
- failure-detection timing;
- determinism;
- scope;
- compatibility;
- implementation cost;
- maintenance burden;
- AIGOV alignment;
- overengineering risk.

Select the smallest complete solution supported by live evidence.

[BOUNDED IMPLEMENTATION AUTHORITY]

Only after the Scope Gate is `authorized`, create a focused branch and implement the bounded repository repair. A Draft PR may be created only after Scope validation and relevant validation. Preserve existing roles, Stage IDs, contracts, historical evidence, and downstream boundaries.

[NON-GOALS]

Do not redesign the pipeline, create self-healing behavior, add automatic repository repair, add a repository-editing mode to the Architect Run, alter unrelated repositories, broadly refactor, change secrets or permissions, or claim repository-wide enforcement.

[VALIDATION REQUIREMENTS]

Run targeted tests for the selected cause, relevant regression tests, deterministic negative cases, `git diff --check`, and applicable Schema/YAML/JSON validation. Report exact commands and exact observed results. Do not claim runtime enforcement from prose, fixtures, or CI alone.

[DRAFT PR REQUIREMENT]

If implementation is authorized and validated, push one bounded branch and open one Draft PR. Never merge or approve. Do not enable auto-merge, deploy, release, or modify repository settings.

[INDEPENDENT REVIEW REQUIREMENT]

Request a fresh independent exact-Head review after the final Head is known. Any Head change makes an earlier review stale.

[FINAL RESPONSE FORMAT]

Return:
- repository and live base SHA;
- Scope Gate result;
- selected option and rejected alternatives;
- files changed;
- exact validation commands and results;
- Draft PR number and URL if created;
- enforcement achieved and not achieved;
- remaining evidence gaps;
- independent review state;
- merge_performed: false;
- approval_performed: false;
- deployment_performed: false.

[STOP CONDITIONS]

Stop without modifying the repository when:
- the Scope Gate is `unauthorized` or `insufficient_evidence`;
- live authorities conflict;
- materially equivalent open work exists;
- the repository identity or exact behavior cannot be established;
- the repair requires a new broad framework or downstream contract change;
- the proposed change would authorize the active Architect Run to edit its own repository.
```

<!-- EV4_REPOSITORY_REPAIR_HANDOFF_PROMPT_END -->

## Forbidden claims

The handoff and standalone prompt must not claim:

```text
repository bug proven
proposed repair proven correct
merge authorized
approval granted
runtime enforced
automatic diagnosis
automatic repository modification
self-healing
production ready
repository-wide AIGOV compliance
```

## Determinism and testability

Repository fixtures and tests may validate:

- required semantic fields;
- allowed trigger states and classes;
- absence of a prompt for non-trigger cases;
- mandatory standalone prompt sections;
- explicit uncertainty and live-review requirements;
- forbidden claims and actions;
- separation of Run repair from repository repair;
- preservation of current Run Anchor authority.

Fixture and CI validation establish only repository-fixture enforcement for the exact tested revision. Real conversational runtime enforcement remains `insufficient_evidence`.
