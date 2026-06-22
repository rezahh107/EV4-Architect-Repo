# EV4 First Run Guide

Status: release_candidate_for_controlled_use
Version: 1.0.0

---

## Recommended First Prompt

```text
Use the EV4 Architect Project Instructions and uploaded reference files.

Input: I will provide a screenshot of one Elementor V4 section.

Goal: run the controlled pipeline for this section.

Start with /intake and /decompose only.
Do not recommend architecture yet.
Do not build Elementor tree yet.
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

## Final Step

```text
Run /handoff-export.
Produce either FINAL BUILDER HANDOFF or HANDOFF BLOCKED REPORT.
```

---

## Quick Stop Rules

Stop and repair if:

```text
- Stage Anchor is missing or stale.
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
