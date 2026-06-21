# Stage 4 — /score-evidence: Evidence-Bound Architecture Scoring

Status: confirmed_hardened_v1.1.0  
Version: 1.1.0  
Depends on: Stage 3 — `/architectures`  
Next stage: Stage 5 — `/score-audit`

---

## Purpose

The `/score-evidence` phase evaluates each architecture candidate from Stage 3 using the architecture scoring rubric.

This stage is the scoring spine of the whole system. It must be strict, evidence-bound, conservative, reproducible, and auditable.

It must not recommend a winner yet.

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

## Critical Review Findings Applied in v1.1.0

Stage 4 v1.0.0 was structurally usable, but not strict enough for production-grade scoring.

v1.1.0 adds hardening for these failure modes:

1. Numeric scores based on vague reasoning instead of traceable evidence.
2. `?` values being avoided so the table looks complete.
3. Shared unknowns being applied inconsistently across candidates.
4. Visual polish leaking into high-weight criteria.
5. Dynamic/widget/CSS assumptions being scored as if they were confirmed.
6. Totals being compared before gate and completeness status are resolved.
7. Accessibility and responsive behavior being treated as obvious from a static image.
8. Hidden recommendation language appearing inside scoring notes.

---

## Core Rule

Score the candidate, not the model's preference.

Each score must be justified by:

```text
Stage 2 evidence
+ Stage 3 candidate claim
+ Rubric criterion definition
+ Evidence source hierarchy
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
6. Current Project Defaults from `STATUS.md` or Project Instructions.

If any required input is missing, stop and request the missing stage/input.

---

## Evidence Source Hierarchy

When assigning scores, use this hierarchy.

| Level | Evidence source | Allowed use |
|---|---|---|
| 1 | Direct Stage 2 observation | Strongest source for visible groups, meaningful content, decoration, overlay candidates, and visible responsive risk |
| 2 | Direct Stage 3 candidate claim | Strong source for proposed structure, flow strategy, overlay strategy, CSS strategy, and dynamic strategy |
| 3 | Rubric criterion definition | Controls score meaning and weighting |
| 4 | Project Defaults | Controls allowed tools, CSS policy, Elementor Pro availability, and default constraints |
| 5 | Official docs / verified external source | May support general platform capability, not proof that a candidate actually uses it |
| 6 | Reasonable inference | Allowed only with `inferred` evidence label and confidence not above `medium` |
| 7 | Missing evidence | Must become `?`, not a guessed numeric score |

Important:

- Official Elementor documentation proves platform capability, not the candidate's actual behavior.
- A screenshot proves appearance, not actual DOM, CSS, plugin use, query source, or responsive behavior.
- A Stage 3 candidate claim proves what the candidate proposes, not that the proposal will score high.

---

## Mandatory Execution Order

Always score in this order:

```text
1. Validate required inputs
2. Extract candidates from Stage 3
3. Extract Stage 3 Unknown Propagation Ledger
4. Build a Stage 4 Evidence Map
5. Exclude rejected-risk and approval-required candidates from primary scoring unless explicitly requested
6. Score each viable/risky candidate criterion-by-criterion
7. Attach evidence source, evidence label, and confidence to every criterion score
8. Apply criterion-specific score anchors
9. Apply immediate rejection gates
10. Calculate weighted totals only for complete candidates
11. Produce uncertainty register
12. Produce scoring table
13. Run Stage 4 self-audit
14. Hand off to /score-audit
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
- Preserve candidate order from Stage 3.
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
- Do not use totals from incomplete candidates for comparison.
- Do not treat a high total as primary-ready when a gate is unresolved or failed.

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

Neutral alternatives allowed:

```text
highest numeric total among complete candidates
lowest unresolved-risk count
requires audit
mechanical score only
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

## Score Anchor Scale

Use this common anchor scale before applying criterion-specific guidance:

| Score | Meaning |
|---:|---|
| 5 | Strongly supported; low material risk; no blocking unknowns for this criterion |
| 4 | Supported; minor unresolved risk; likely acceptable |
| 3 | Acceptable but meaningfully uncertain or partially constrained |
| 2 | Material risk, weak fit, or likely repair required |
| 1 | Fails the criterion or conflicts with core project defaults |
| ? | Evidence insufficient; numeric score would invent facts |

Important:

- `5` requires direct evidence or very strong candidate-specific support.
- `4` cannot be based on weak inference alone.
- `3` is not a dumping ground for unknowns; use `?` when evidence is truly missing.
- `1` or `2` may be used when evidence shows a real risk, not merely because details are absent.

---

## Criterion-Specific Scoring Anchors

### 1. Elementor-Native Feasibility ×4

Score higher when the candidate uses native Elementor V4/Pro capabilities, containers, standard widgets, SVG/Image widgets, or scoped CSS in a controlled way.

Score lower or use `?` when the candidate depends on:

- unstated JavaScript,
- unapproved third-party plugin,
- unknown widget behavior,
- unsupported interaction,
- full custom HTML for meaningful content.

Guardrail:

```text
Repeated visual group ≠ proof of Loop Grid, Repeater, CPT, ACF, WooCommerce, or dynamic data.
```

### 2. Normal-Flow Safety ×4

Score higher when meaningful content stays in normal document flow and overlays are limited to decoration or controlled layers.

Score lower when:

- meaningful cards, text, CTAs, or primary images are absolute-positioned without a fallback,
- DOM order is likely detached from visual order,
- content becomes dependent on fixed coordinates.

Use `?` when the candidate does not state where meaningful content lives.

### 3. Responsiveness ×4

Score higher when the candidate states a credible desktop/tablet/mobile behavior with minimal duplicate DOM and no brittle coordinate dependency.

Score lower or use `?` when:

- mobile behavior is not specified,
- connectors/floating cards depend on fixed coordinates,
- hidden/duplicate sections are required but not justified,
- tablet behavior is ignored.

Guardrail:

```text
A desktop screenshot does not prove mobile behavior.
```

### 4. Editability ×3

Score higher when text, icons, images, cards, links, and repeated items remain editable in Elementor or a clear content source.

Score lower when normal content updates require:

- editing SVG path text,
- editing custom HTML,
- editing CSS,
- replacing a full-section image,
- changing hardcoded coordinates for routine content edits.

### 5. Structural Clarity ×2

Score higher when the candidate would produce a readable Structure Panel/tree with named containers, limited nesting, and clear separation between content and decoration.

Score lower when:

- many wrappers are introduced without reason,
- decoration and content are mixed in the same layer,
- hidden mobile-only duplicates increase maintenance cost.

### 6. Overlay Containment ×2

Score higher when overlays/connectors/floating elements are isolated inside a named relative stage and do not control meaningful content layout.

Score lower when:

- overlays are global,
- z-index strategy is vague,
- connector lines are likely to collide with cards,
- overlay elements are used as layout primitives.

### 7. Performance ×2

Score higher when the candidate avoids heavy full-section images, avoids unnecessary DOM depth, and uses optimized visual assets.

Score lower when:

- full-section raster screenshots are used,
- many duplicate sections are required,
- heavy animation/JS is assumed,
- large SVG/HTML blocks are used without scope or optimization strategy.

### 8. Accessibility ×2

Score higher when the candidate preserves real text, logical reading order, focus behavior, and explicit image/alt handling.

Score lower or use `?` when:

- meaningful text becomes image text,
- image semantics are unresolved,
- interactive states are unknown,
- focus order may not match visual order,
- carousel/accordion/filter behavior is assumed without evidence.

Guardrail:

```text
Visual Core is not automatically decorative.
Decoration is not automatically alt="" unless context supports it.
```

### 9. Design-System Fit ×1

Score higher when the candidate supports reusable classes, variables, tokens, components, and repeatable naming.

Score lower when:

- one-off global classes are used,
- repeated styling is not reusable,
- design tokens are ignored,
- component variants are not identified.

### 10. Visual Precision ×1

Score visual precision only inside this criterion.

Score higher when the candidate can plausibly match the reference visual without violating higher-weight criteria.

Score lower when precision depends on brittle absolute positioning, static images, or uneditable content.

Guardrail:

```text
Visual Precision must never override Elementor-native feasibility, normal-flow safety, responsiveness, or editability.
```

---

## Unknown Handling

Use `?` when a criterion cannot be scored without inventing facts.

A `?` score must include:

```text
missing_evidence:
impact_on_score:
question_to_resolve:
blocking_level: blocking | non_blocking | audit_needed
```

Do not convert `?` to a numeric score merely to complete the table.

If a candidate has one or more `?` values, its total must be:

```text
TOTAL: incomplete
```

and it must be excluded from mechanical total comparison until resolved.

---

## Shared Unknown Consistency Rule

If the same unknown affects multiple candidates, handle it consistently.

Example:

```text
Unknown: mobile behavior of connector lines
Affected candidates: A03, A04, A07
```

The scorer must not mark this unknown as numeric `4` for one candidate and `?` for another unless the candidates provide different explicit mitigation evidence.

Every shared unknown must appear in the Uncertainty Register.

---

## Unknown-to-Score Ceiling Rule

If a criterion materially depends on unresolved evidence, numeric scores are capped:

| Evidence state | Max numeric score if not `?` |
|---|---:|
| Mostly confirmed | 5 |
| Partially supported | 4 |
| Inferred only | 3 |
| Unknown but non-blocking | 3 |
| Unknown and criterion-critical | `?` |
| Conflict | 2 unless resolved |

This rule prevents hidden optimism.

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

## Candidate Classification

After scoring, classify each candidate mechanically:

| Classification | Meaning |
|---|---|
| `complete_gate_pass` | All criteria numeric; no gate failure |
| `complete_but_immediate_reject` | All criteria numeric; at least one hard gate failed |
| `incomplete_unresolved` | One or more `?` values |
| `approval_required_excluded` | Third-party/plugin/externally dependent option without user approval |
| `rejected_risk_documented` | Known-bad or explicitly rejected architecture documented for contrast |

Do not call any classification `best`, `winner`, or `recommended`.

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

## Evidence Map Requirement

Before criterion scoring, produce a compact Evidence Map:

```text
STAGE 4 EVIDENCE MAP

Candidate: [ID]
Stage 2 evidence used:
- [group/risk/unknown]

Stage 3 claims used:
- [structure_premise]
- [normal_flow_strategy]
- [overlay_strategy]
- [responsive_premise]
- [custom_css_need]

Rubric gates relevant:
- Elementor-Native Feasibility
- Normal-Flow Safety
- Responsiveness

Missing evidence before scoring:
- ...
```

A score without evidence map support is invalid.

---

## Candidate Scoring Block Format

For every viable or risky candidate, output this block:

```text
CANDIDATE SCORE — [Candidate ID + Name]

Candidate status from Stage 3:
- viable | risky | rejected | requires_user_approval

Candidate classification after scoring:
- complete_gate_pass | complete_but_immediate_reject | incomplete_unresolved | approval_required_excluded | rejected_risk_documented

Gate status:
- pass | immediate_reject | unresolved

Criterion scores:

1. Elementor-Native Feasibility
- score: 1 | 2 | 3 | 4 | 5 | ?
- weight: ×4
- weighted_result: score × weight | incomplete
- evidence_source: Stage 2 | Stage 3 | Rubric | Project Defaults | official docs | inference | missing
- evidence_label: confirmed | partially_supported | inferred | unknown | conflict
- confidence: high | medium | low | unknown
- evidence:
- reasoning:
- score_anchor_used:
- missing_evidence: only if score is ?
- blocking_level: only if score is ?

2. Normal-Flow Safety
- score:
- weight: ×4
- weighted_result:
- evidence_source:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- score_anchor_used:
- missing_evidence:
- blocking_level:

3. Responsiveness
- score:
- weight: ×4
- weighted_result:
- evidence_source:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- score_anchor_used:
- missing_evidence:
- blocking_level:

4. Editability
- score:
- weight: ×3
- weighted_result:
- evidence_source:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- score_anchor_used:
- missing_evidence:
- blocking_level:

5. Structural Clarity
- score:
- weight: ×2
- weighted_result:
- evidence_source:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- score_anchor_used:
- missing_evidence:
- blocking_level:

6. Overlay Containment
- score:
- weight: ×2
- weighted_result:
- evidence_source:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- score_anchor_used:
- missing_evidence:
- blocking_level:

7. Performance
- score:
- weight: ×2
- weighted_result:
- evidence_source:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- score_anchor_used:
- missing_evidence:
- blocking_level:

8. Accessibility
- score:
- weight: ×2
- weighted_result:
- evidence_source:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- score_anchor_used:
- missing_evidence:
- blocking_level:

9. Design-System Fit
- score:
- weight: ×1
- weighted_result:
- evidence_source:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- score_anchor_used:
- missing_evidence:
- blocking_level:

10. Visual Precision
- score:
- weight: ×1
- weighted_result:
- evidence_source:
- evidence_label:
- confidence:
- evidence:
- reasoning:
- score_anchor_used:
- missing_evidence:
- blocking_level:

TOTAL:
- numeric_total: /100 | incomplete
- completeness: complete | incomplete
- gate_status: pass | immediate_reject | unresolved
- uncertainty_count:
- blocking_unknown_count:
- scoring_notes:
```

---

## Summary Table Format

After individual scoring blocks, output:

```text
SCORING SUMMARY TABLE

| Candidate | Status | Gate | Elementor-Native ×4 | Normal-Flow ×4 | Responsiveness ×4 | Editability ×3 | Structural ×2 | Overlay ×2 | Performance ×2 | Accessibility ×2 | Design-System ×1 | Visual ×1 | Total | Completeness |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A01 | viable | pass | 20 | 20 | 16 | 12 | 8 | 10 | 8 | 8 | 4 | 3 | 109 INVALID — recalc | complete |
```

Important:

- Do not allow totals over `/100`.
- Use weighted results in the table, not raw scores.
- Use `?` or `incomplete` where evidence is missing.
- Do not sort the table by preference.
- Preserve Stage 3 candidate order unless `/score-audit` later requests reordering.
- If an example row accidentally exceeds `/100`, label it invalid and recalculate; never normalize silently.

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

Arithmetic must be shown as:

```text
ARITHMETIC CHECK
Candidate A01:
20 + 16 + 20 + 12 + 8 + 8 + 6 + 8 + 4 + 4 = 106 INVALID
Action: recalculate before handoff
```

No candidate may be handed off with invalid arithmetic.

---

## Uncertainty Register

After the scoring table, output:

```text
UNCERTAINTY REGISTER

| Unknown | Source Stage | Affected Candidate(s) | Affected Criterion | Current Handling | Blocking Level | Evidence Needed |
|---|---|---|---|---|---|---|
```

Every `?` score must appear in the Uncertainty Register.

Every Stage 3 Unknown Propagation Ledger item must either:

- appear in the Uncertainty Register, or
- be marked `not scoring-relevant` with reason.

---

## Fairness and Consistency Check

Before self-audit, run this consistency check:

```text
FAIRNESS AND CONSISTENCY CHECK

- Same unknown treated consistently across candidates: yes/no
- Same criterion interpreted consistently across candidates: yes/no
- No candidate received optimism from weaker evidence than another: yes/no
- No candidate penalized for simplifying decoration while preserving content: yes/no
- No Visual Precision leakage into high-weight criteria: yes/no
- No hidden recommendation wording: yes/no
```

If any answer is `no`, revise Stage 4 output before proceeding.

---

## Stage 4 Self-Audit

Before handing off, run this checklist:

```text
STAGE 4 SELF-AUDIT

- Required inputs present: yes/no
- Evidence Map produced for every scored candidate: yes/no
- Every viable/risky candidate scored: yes/no
- Every score has evidence_source: yes/no
- Every score has evidence label: yes/no
- Every score has confidence: yes/no
- Score anchors used: yes/no
- Every ? has missing evidence: yes/no
- Every ? has blocking level: yes/no
- Shared unknowns handled consistently: yes/no
- Gate rules applied: yes/no
- No hidden recommendation language: yes/no
- No Visual Precision override: yes/no
- Arithmetic verified: yes/no
- No total exceeds /100: yes/no
- Summary table complete: yes/no
- Uncertainty Register complete: yes/no
- Candidate classification assigned: yes/no
- Allowed next step is /score-audit: yes/no
```

If any answer is `no`, revise Stage 4 output before proceeding.

---

## Pass Criteria

Stage 4 passes only if:

- It uses the rubric weights correctly.
- It scores only actual Stage 3 candidates.
- It produces an Evidence Map for each scored candidate.
- It attaches evidence source, evidence label, and confidence to every criterion score.
- It applies score anchors consistently.
- It uses `?` instead of inventing missing facts.
- It applies immediate rejection gates.
- It excludes unresolved candidates from primary-ready treatment.
- It does not recommend or rank a final architecture.
- It does not let Visual Precision override higher-weight criteria.
- It includes a complete Uncertainty Register.
- It treats shared unknowns consistently across candidates.
- It validates arithmetic with no total above `/100`.
- It classifies candidates mechanically without winner language.
- It hands off to `/score-audit`.

---

## Allowed Next Step

```text
/score-audit
```
