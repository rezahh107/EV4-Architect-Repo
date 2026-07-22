# EV4 First Run Guide

Status: release_candidate_for_controlled_use
Version: 1.2.0

---

<!-- EV4_ARCHITECT_FIRST_RUN_FAST_START_START -->
## Fast Start

In a new user-facing Architect chat with the project or repository instructions loaded, send only:

```text
شروع
```

When no screenshot, section description, active run, or valid Stage Anchor is present, the expected response is exactly:

<!-- EV4_ARCHITECT_BOOTSTRAP_RESPONSE_START -->
```text
EV4 Architect آماده است.

برای شروع یک سکشن جدید:
1. تصویر سکشن را ارسال کن.
2. اگر معلوم است، مشخص کن تصویر مربوط به Desktop، Tablet یا Mobile است.
3. محدودیت‌ها، Assetها یا رفتارهای مورد انتظار را فقط در صورت وجود اضافه کن.

پس از دریافت ورودی، مسیر رسمی از اینجا شروع می‌شود:
/intake → /research → /decompose

تا پیش از دریافت ورودی، هیچ معماری، Elementor tree، مقدار دقیق یا توصیه‌ای تولید نمی‌شود.
```
<!-- EV4_ARCHITECT_BOOTSTRAP_RESPONSE_END -->

The canonical machine-readable source for this response is:

```text
manifests/architect-conversation-bootstrap.v1.json
```

If the user supplies `شروع` together with a screenshot or usable section description, do not repeat the bootstrap questions. Run `/intake` using the supplied input.
<!-- EV4_ARCHITECT_FIRST_RUN_FAST_START_END -->

---

## Recommended First Input

Upload one Elementor V4 section screenshot and optionally include:

```text
- Device context: Desktop, Tablet, Mobile, or unknown
- Available assets
- Known interaction or content requirements
- Explicit constraints or exceptions
```

Do not provide details that are already obvious from the screenshot unless they are important constraints.

The model must run `/intake` first. It must not recommend architecture, produce an Elementor tree, or invent exact values during intake.

---

## After /intake

```text
Current status: BLOCKED_VALIDATION_PROFILE.
The Manifest requires /intake → /research, but /intake is not full_transaction_implemented.
Do not continue from an Anchor or from conversation memory. Preserve the intake output and stop.
```

---

## After /research

```text
Current status: BLOCKED_VALIDATION_PROFILE.
/research remains mandatory, but its executable Validation Transaction is not implemented.
Do not authorize /research → /decompose and never bypass with /intake → /decompose.
```

---

## After /decompose

If the decomposition looks correct, continue:

```text
Continue to /architectures using the Stage Anchor.
Generate candidate architecture families with coverage matrix, unknown propagation ledger, and no recommendation.
```

---

## After /architectures

```text
Continue to /score-evidence.
Use the rubric only.
Use ? for missing evidence.
Use N/A only when criterion is truly non-applicable.
Do not convert unknowns into numbers.
```

---

## After /score-evidence

```text
Run /score-audit.
Check arithmetic, gate overrides, unknown handling, hidden recommendation, N/A denominator, and consistency.
```

---

## After /score-audit

```text
If audit passes or pass_with_minor_flags, run /recommend.
If tie remains unresolved, ask one minimal user question.
```

---

## After /recommend

```text
Run /build-tree.
Use naming convention:
[section-role]__[content-group]--[variant]
Keep meaningful content editable.
Keep decorative overlays isolated.
Carry unknowns forward.
```

---

## After /build-tree

```text
Run /implementation.
Map tree to Elementor widgets, classes, variables, assets, responsive settings, and scoped CSS needs.
Do not invent exact values.
```

---

## After /implementation

```text
Run /final-audit.
Audit but do not repair.
Route all defects.
```

---

## After /final-audit

```text
Run /handoff-export.
Produce either FINAL BUILDER HANDOFF or HANDOFF BLOCKED REPORT.
```

---

<!-- EV4_ARCHITECT_FINAL_PROJECT_GATE_START -->
## Final Project Gate Step

`/project-gate-export` is the terminal Manifest Stage. The legal `/handoff-export → /project-gate-export` edge does not authorize continuation while `/handoff-export` remains `blocked_missing_semantics`. Run the following only after an active Registry profile and independently regenerated Bundle authorize that exact edge:

```text
Run /project-gate-export.
Produce the canonical Architect Producer Gate Export or a fail-closed blocked result.
Do not substitute the legacy /builder-feed-export.
```
<!-- EV4_ARCHITECT_FINAL_PROJECT_GATE_END -->

---

## Quick Stop Rules

Stop and repair if:

```text
- Stage Anchor is missing or stale.
- A mandatory stage in the manifest is skipped.
- Screenshot evidence does not support a visual claim.
- Unknown is converted into a number.
- Recommendation appears before /recommend.
- Meaningful content is flattened into static image/SVG.
- Connector/mobile behavior is assumed without evidence.
- Final audit finds blocker/high issues.
```

---

## Current Beta Boundary

This release pack is valid for controlled real screenshot use.

It is not yet validated for:

```text
live Elementor rendering
real Elementor export JSON
EDIS
browser/device QA
exact pixel matching
```
