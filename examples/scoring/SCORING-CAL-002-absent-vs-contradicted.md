# SCORING-CAL-002 — Absent Evidence vs Contradicted Evidence

## Purpose

Teach Stage 4 to separate missing evidence from conflicting evidence.

## Case A — Absent Evidence

Stage 2 does not say whether a logo strip has links or alt text.

Stage 3 says logos remain as individual editable image widgets but does not specify link or alt policy.

Expected behavior:

| Criterion | Evidence Label | Score Behavior |
|---|---|---|
| Accessibility | `ABSENT_EVIDENCE` | `?` or capped score, depending on impact |
| Editability | `SUPPORTED_EVIDENCE` or `PARTIALLY_SUPPORTED_EVIDENCE` | Numeric score allowed if editability is stated |

Do not punish as contradiction. The problem is missing evidence.

## Case B — Contradicted Evidence

Stage 2 says each logo is meaningful partner content.

Stage 3 says all logos will be treated as decoration without alt or text alternative.

Expected behavior:

| Criterion | Evidence Label | Score Behavior |
|---|---|---|
| Accessibility | `CONTRADICTED_EVIDENCE` | Low score or defect |

## Audit Rule

```text
ABSENT_EVIDENCE → usually ?
CONTRADICTED_EVIDENCE → low score, defect, or gate-related warning
```

Stage 5 must fail any report that mixes these two states.
