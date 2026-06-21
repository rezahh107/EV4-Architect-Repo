# Stage 4 v1.3 Hardening Patch — N/A and Calibration Alignment

Status: active_patch_for_stage_4  
Patch version: 1.3.0  
Applies to: `stages/04_SCORE_EVIDENCE.md`  
Rubric version: 1.3  
Payload schema extension: `ev4-score-evidence-payload@1.3.0`

---

## Purpose

This patch hardens Stage 4 after the Stage 5 review pass.

It adds:

1. explicit `N/A` handling,
2. Overlay Containment non-applicable logic,
3. denominator adjustment for non-applicable criteria,
4. scoring calibration references,
5. payload fields needed by Stage 5 v1.1.0.

---

## N/A Is Not A Score

`N/A` means the criterion does not structurally apply.

It is different from:

- `5`, which means strong performance,
- `?`, which means insufficient evidence,
- `ABSENT_EVIDENCE`, which means the source does not say enough.

Only the rubric may allow `N/A`.

---

## Overlay Containment N/A Rule

Overlay Containment may be marked `N/A` only when all are true:

1. Stage 2 has no overlay, connector, floating, absolute, z-index, or decorative layer candidate.
2. Stage 3 does not introduce an overlay, connector, floating, absolute, z-index, or decorative layer strategy.
3. The architecture is purely normal-flow for both meaningful content and decoration.

If any condition is false, Overlay Containment is applicable and must receive `1–5` or `?`.

Required row shape when `N/A` is used:

```text
criterion: Overlay Containment
score: N/A
weight: 2
evidence_label: NON_APPLICABLE
weight_excluded: true
reason: No overlay candidates in Stage 2 and none introduced by Stage 3.
```

---

## Denominator Rule

Default scoring denominator:

```text
applicable_weight_total = 25
applicable_raw_max = 125
```

When any criterion is `N/A`:

```text
applicable_weight_total = 25 - sum(N/A weights)
applicable_raw_max = applicable_weight_total * 5
normalized_total = raw_weighted_total / applicable_raw_max * 100
```

If any criterion is `?`, final totals remain `incomplete` even if other criteria are numeric.

---

## Payload Additions

Stage 4 payload must include these fields when using rubric `1.3`:

```text
schema_version: ev4-score-evidence-payload@1.3.0
criteria_with_na
excluded_weights
applicable_weight_total
applicable_raw_max
rubric_version: 1.3
```

---

## Calibration Reference Requirement

Stage 4 must consult `examples/scoring/` before scoring when the case involves:

- contradicted evidence,
- absent evidence,
- non-applicable criteria,
- arithmetic uncertainty,
- gate override risk.

Calibration examples do not replace the rubric. They show expected scoring behavior.

---

## Stage 5 Dependency

Stage 5 v1.1.0 must audit this patch by checking:

- `N/A` is used only where permitted,
- excluded weights are removed from the denominator,
- `N/A` is not treated as `5`,
- `?` still prevents a final total,
- schema version is current.

---

*This patch is part of the fixed Elementor V4 Architect Prompt Pack.*