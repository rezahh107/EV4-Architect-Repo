# SCORING-CAL-001 — Contradicted Evidence

## Purpose

Teach Stage 4 that contradiction is not unknown.

## Synthetic Input

Stage 2 says meaningful card text must remain editable.

Stage 3 candidate says the card text will be delivered as part of a non-editable visual asset.

## Correct Scoring Behavior

| Criterion | Expected Evidence Label | Expected Score Behavior |
|---|---|---|
| Editability | `CONTRADICTED_EVIDENCE` | Low score, usually `1` |
| Accessibility | `CONTRADICTED_EVIDENCE` | Low score when meaningful text is no longer real text |
| Normal-Flow Safety | `CONTRADICTED_EVIDENCE` or `PARTIALLY_SUPPORTED_EVIDENCE` | Low score if meaningful content is removed from normal flow |
| Elementor-Native Feasibility | `PARTIALLY_SUPPORTED_EVIDENCE` | Technical feasibility alone does not create a high-quality architecture score |

## Wrong Behavior

```text
Do not mark Editability as ?.
Do not say evidence is missing.
Do not give a medium score because the visual is achievable.
Do not let Visual Precision override Editability or Accessibility.
```

## Expected Audit Trigger

```text
stage_5_spot_check_triggers:
- CONTRADICTED_EVIDENCE
- visual_precision_override_risk
- possible_gate_override
```
