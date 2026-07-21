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
Continue to /research using the Stage Anchor from /intake.
Research only the current section's architecture-changing unknowns and version-sensitive Elementor capabilities.
Preserve unsupported or project-specific behavior as unknown.
Produce a STAGE ANCHOR for /decompose.
```

---

## After /research

```text
Continue to /decompose using the Stage Anchor from /research.
Decompose by visual role, not implementation.
Do not recommend architecture yet.
Do not build an Elementor tree yet.
Do not use TUYA/RAG/docs to invent visual groups.
Mark unknowns explicitly.
Produce a STAGE ANCHOR for /architectures.
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

When `/handoff-export` is accepted and its Stage Anchor authorizes the next stage:

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
