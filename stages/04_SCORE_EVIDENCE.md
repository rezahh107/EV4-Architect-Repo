# Stage 4 — /score-evidence: Evidence-Bound Architecture Scoring

Status: confirmed_v1.0.0  
Version: 1.0.0  
Depends on: Stage 3 — `/architectures`  
Next stage: Stage 5 — `/score-audit`

---

## Purpose

The `/score-evidence` phase evaluates each architecture candidate from Stage 3 using the architecture scoring rubric.

This stage must score with evidence, uncertainty, and explicit rule application. It must not recommend a winner yet.

---

## Source of Truth

Use the scoring criteria and decision rules from:

```text
rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md
```

The current rubric has 10 criteria with weighted scoring:

| Criterion | Weight | Max weighted score |
|---|---:|---:|
| Elementor-Native Feasibility | ×4 | 20 |
| Normal-Flow Safety | ×4 | 20 |
| Responsiveness | ×4 | 20 |
| Editability | ×3 | 15 |
| Structural Clarity | ×2 | 10 |
| Overlay Containment | ×2 | 10 |
| Performance | ×2 | 10 |
| Accessibility | ×2 | 10 |
| Design-System Fit | ×1 | 5 |
| Visual Precision | ×1 | 5 |

Total: `/100`.

---

## Core Rule

Score the candidate, not the model's preference.

Each score must be justified by:

```text
Stage 2 evidence
+ Stage 3 candidate claim
+ Rubric criterion definition
+ Explicit uncertainty handling
```

If the required evidence is missing, do not invent it. Use `?` and explain the missing evidence.

---

## Required Inputs

Stage 4 requires all of the following:

1. Completed Stage 2 `DECOMPOSITION SNAPSHOT`.
2. Completed Stage 3 `ARCHITECTURE CANDIDATES`.
3. Stage 3 `Architecture Coverage Matrix`.
4. Stage 3 `Unknown Propagation Ledger`.
5. Current scoring rubric from `rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md`.

If any required input is missing, stop and request the missing stage/input.

---

## Mandatory Execution Order

Always score in this order:

```text
1. Validate required inputs
2. Extract candidates from Stage 3
3. Exclude rejected-risk and approval-required candidates from primary scoring unless explicitly requested
4. Score each viable/risky candidate criterion-by-criterion
5. Attach evidence and confidence to every criterion score
6. Apply immediate rejection gates
7. Calculate weighted totals
8. Produce uncertainty register
9. Produce scoring table
10. Hand off to /score-audit
```

---

## Allowed Work

Allowed:

- Score each architecture candidate against the rubric.
- Use integer scores from `1` to `5` only.
- Use `?` when evidence is insufficient.
- Calculate weighted totals only when all criteria have numeric scores.
- Mark candidates with hard-gate failures.
- Explain why each criterion received its score.
- Explain what evidence would be needed to replace a `?` score.
- Compare scores mechanically in the scoring table.
- Hand off to `/score-audit`.

---

## Forbidden Work

Forbidden:

- Do not recommend a final architecture.
- Do not write `best`, `winner`, `recommended`, `preferred`, `optimal`, `cleanest`, `safest`, or their Persian equivalents.
- Do not use visual taste to override weighted criteria.
- Do not hide unknowns inside a numeric score.
- Do not give fractional scores.
- Do not score an omitted architecture family as if it were a full candidate.
- Do not score a third-party plugin candidate as normal unless user approval exists.
- Do not let Visual Precision decide the outcome.
- Do not produce a final Elementor tree.
- Do not write CSS or implementation code.

Forbidden Persian winner-implying words before `/recommend`:

```text
بهترین
برنده
پیشنهادی
گزینه اصلی
امن‌ترین
تمیزترین
بهینه‌ترین
انتخاب نهایی
```

---

## Evidence Labels

Every criterion score must use one evidence label:

| Label | Meaning |
|---|---|
| `confirmed` | Directly supported by Stage 2 or Stage 3 evidence |
| `partially_supported` | Some evidence exists, but one or more assumptions remain |
| `inferred` | Reasonable inference from candidate structure, not directly proven |
| `unknown` | Evidence is insufficient; score must be `?` |
| `conflict` | Evidence contradicts the candidate claim; explain and score conservatively |

---

## Scoring Confidence

Every criterion score must include confidence:

```text
confidence: high | medium | low | unknown
```

Rules:

- `confirmed` usually allows `high`.
- `partially_supported` usually allows `medium`.
- `inferred` must not exceed `medium`.
- `unknown` must use `unknown` confidence.
- `conflict` must use `low` unless resolved by explicit evidence.

---

## Unknown Handling

Use `?` when a criterion cannot be scored without inventing facts.

A `?` score must include:

```text
missing_evidence:
impact_on_score:
question_to_resolve:
```

Do not convert `?` to a numeric score merely to complete the table.

If a candidate has one or more `?` values, its total must be:

```text
TOTAL: incomplete
```

and it must be excluded from mechanical total ranking until resolved.

---

## Immediate Rejection Gates

Apply the rubric gates after criterion scoring:

```text
Elementor-Native Feasibility < 3 → immediate_reject
Normal-Flow Safety < 2 → immediate_reject
Responsiveness < 2 → immediate_reject
```

Gate handling rules:

- A gate failure must be displayed separately from total score.
- A high total score cannot override a gate failure.
- A gate score of `?` means `gate_status: unresolved`, not pass.
- If gate status is unresolved, the candidate cannot be treated as primary-ready.

---

## Conservative Scoring Rules

Use conservative scoring when evidence is weak:

1. If a candidate relies on an unstated custom interaction, lower Elementor-Native or mark `?`.
2. If meaningful content appears outside normal flow, lower Normal-Flow Safety.
3. If mobile behavior depends on unverified hidden/duplicate sections, lower Responsiveness or mark `?`.
4. If editing requires CSS/HTML changes for normal content updates, lower Editability.
5. If overlays are not contained inside a named relative Stage, lower Overlay Containment.
6. If the candidate increases DOM depth or uses large raster assets without optimization strategy, lower Performance.
7. If reading order, alt decision, or focus behavior is unresolved, lower Accessibility or mark `?`.
8. If classes, variables, or reusable component candidates are not clear, lower Design-System Fit.
9. Visual Precision may improve the score only inside its own criterion.
10. Do not punish a candidate for simplifying decoration when content, responsiveness, and editability improve.

---

## Candidate Scoring Block Format

For every viable or risky candidate, output this block:

```text
CANDIDATE SCORE — [Candidate ID + Name]

Candidate status from Stage 3:
- viable | risky | rejected | requires_user_approval

Gate status:
- pass | immediate_reject | unresolved

Criterion scores:

1. Elementor-Native Feasibility
- score: 1 | 2 | 3 | 4 | 5 | ?
- weight: ×4
- weighted_result: score × weight | incomplete
- evidence_label: confirmed | partially_supported | inferred | unknown | conflict
- confidence: high | medium | low | unknown
- evidence:
- reasoning:
- missing_evidence: only if score is ?

2. Normal-Flow Safety
- score:
- weight: ×4
- weighted_result:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- missing_evidence:

3. Responsiveness
- score:
- weight: ×4
- weighted_result:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- missing_evidence:

4. Editability
- score:
- weight: ×3
- weighted_result:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- missing_evidence:

5. Structural Clarity
- score:
- weight: ×2
- weighted_result:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- missing_evidence:

6. Overlay Containment
- score:
- weight: ×2
- weighted_result:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- missing_evidence:

7. Performance
- score:
- weight: ×2
- weighted_result:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- missing_evidence:

8. Accessibility
- score:
- weight: ×2
- weighted_result:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- missing_evidence:

9. Design-System Fit
- score:
- weight: ×1
- weighted_result:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- missing_evidence:

10. Visual Precision
- score:
- weight: ×1
- weighted_result:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- missing_evidence:

TOTAL:
- numeric_total: /100 | incomplete
- completeness: complete | incomplete
- gate_status: pass | immediate_reject | unresolved
- uncertainty_count:
- scoring_notes:
```

---

## Summary Table Format

After individual scoring blocks, output:

```text
SCORING SUMMARY TABLE

| Candidate | Status | Gate | Elementor-Native ×4 | Normal-Flow ×4 | Responsiveness ×4 | Editability ×3 | Structural ×2 | Overlay ×2 | Performance ×2 | Accessibility ×2 | Design-System ×1 | Visual ×1 | Total | Completeness |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A01 | viable | pass | 20 | 20 | 16 | 12 | 8 | 10 | 8 | 8 | 4 | 3 | 109? | complete/incomplete |
```

Important:

- Do not allow totals over `/100`.
- Use weighted results in the table, not raw scores.
- Use `?` or `incomplete` where evidence is missing.
- Do not sort the table by preference.
- Preserve Stage 3 candidate order unless `/score-audit` later requests reordering.

---

## Arithmetic Check

Before finalizing Stage 4 output, verify:

```text
Elementor-Native max = 20
Normal-Flow max = 20
Responsiveness max = 20
Editability max = 15
Structural Clarity max = 10
Overlay Containment max = 10
Performance max = 10
Accessibility max = 10
Design-System Fit max = 5
Visual Precision max = 5
TOTAL max = 100
```

If total exceeds `/100`, stop and recalculate.

---

## Uncertainty Register

After the scoring table, output:

```text
UNCERTAINTY REGISTER

| Unknown | Affected Candidate(s) | Affected Criterion | Current Handling | Evidence Needed |
|---|---|---|---|---|
```

Every `?` score must appear in the Uncertainty Register.

---

## Stage 4 Self-Audit

Before handing off, run this checklist:

```text
STAGE 4 SELF-AUDIT

- Required inputs present: yes/no
- Every viable/risky candidate scored: yes/no
- Every score has evidence label: yes/no
- Every score has confidence: yes/no
- Every ? has missing evidence: yes/no
- Gate rules applied: yes/no
- No hidden recommendation language: yes/no
- No Visual Precision override: yes/no
- Arithmetic verified: yes/no
- Summary table complete: yes/no
- Uncertainty Register complete: yes/no
- Allowed next step is /score-audit: yes/no
```

If any answer is `no`, revise Stage 4 output before proceeding.

---

## Pass Criteria

Stage 4 passes only if:

- It uses the rubric weights correctly.
- It scores only actual Stage 3 candidates.
- It attaches evidence, evidence label, and confidence to every criterion score.
- It uses `?` instead of inventing missing facts.
- It applies immediate rejection gates.
- It excludes unresolved candidates from primary-ready treatment.
- It does not recommend or rank a final architecture.
- It does not let Visual Precision override higher-weight criteria.
- It includes a complete Uncertainty Register.
- It hands off to `/score-audit`.

---

## Allowed Next Step

```text
/score-audit
```
