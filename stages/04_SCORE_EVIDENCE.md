# Stage 4 — /score-evidence: Evidence-Bound Architecture Scoring

Status: confirmed_hardened_v1.2.0  
Version: 1.3.0  
Depends on: Stage 3 — `/architectures`  
Next stage: Stage 5 — `/score-audit`  
Payload schema: `ev4-score-evidence-payload@1.2.0`

---

## Purpose

The `/score-evidence` phase evaluates each Stage 3 architecture candidate against the fixed Elementor V4 architecture rubric.

This stage is the scoring spine of the entire pipeline. It must be strict, evidence-bound, conservative, reproducible, arithmetically safe, and auditable.

It must not recommend a winner.

---

## Source of Truth

Use the scoring criteria and decision rules from:

```text
rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md
```

The rubric has 10 weighted criteria:

| Criterion | Weight | Raw weighted max |
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

Raw weighted maximum: `/125`  
Normalized total: `/100`

```text
normalized_total = (raw_weighted_total / 125) × 100
```

Important:

- Never treat the raw weighted total as `/100`.
- Decision bands apply to `normalized_total` only.
- If any criterion is `?`, final total is `incomplete`.
- If arithmetic tooling is unavailable, output formulas and hand arithmetic verification to `/score-audit`; do not claim arithmetic certainty.

---

## Critical Hardening Applied in v1.2.0

Stage 4 v1.2.0 adds these production controls:

1. **Tool-first arithmetic** — avoid confident mental totals; use Python/calculator/runtime when available.
2. **Provisional known-score formula** — if any criterion is `?`, final score remains incomplete, but a clearly labeled provisional known-score may be shown.
3. **Hidden recommendation enforcement** — direct recommendation terms auto-fail; non-mechanical subjective language is flagged.
4. **Elementor inheritance nuance** — absent mobile evidence is not automatically `?`, but responsive score is capped by evidence quality and risk.
5. **Absent vs contradicted evidence separation** — missing evidence is not the same as evidence conflict.
6. **Audit_Trail_Payload** — Stage 4 must hand Stage 5 a structured audit index.
7. **Schema versioning** — the handoff payload must declare its schema version.
8. **Stage 5 spot-check authority** — Stage 5 uses the payload as primary index but may inspect Stage 2, Stage 3, and the rubric.

---

## Core Rule

Score the candidate, not the model's preference.

Each score must be justified by:

```text
Stage 2 evidence
+ Stage 3 candidate claim
+ Rubric criterion definition
+ Evidence source hierarchy
+ Evidence label
+ Confidence label
+ Explicit uncertainty handling
+ Correct arithmetic policy
```

If the required evidence is missing, do not invent it. Use `?`, explain the missing evidence, and record it in the Uncertainty Register and Audit_Trail_Payload.

---

## Required Inputs Gate

Stage 4 requires all of the following:

1. Completed Stage 2 `DECOMPOSITION SNAPSHOT`.
2. Completed Stage 3 `ARCHITECTURE CANDIDATES`.
3. Stage 3 `Architecture Coverage Matrix`.
4. Stage 3 `Unknown Propagation Ledger`.
5. Current scoring rubric from `rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md`.
6. Current Project Defaults from `STATUS.md` or Project Instructions.

If any required input is missing, stop and request the missing input.

---

## Evidence Source Hierarchy

When assigning scores, use this hierarchy:

| Level | Evidence source | Allowed use |
|---|---|---|
| 1 | Direct Stage 2 observation | Strongest source for visible groups, meaningful content, decoration, overlay candidates, and visible responsive risk |
| 2 | Direct Stage 3 candidate claim | Strong source for proposed structure, flow strategy, overlay strategy, CSS strategy, and dynamic strategy |
| 3 | Rubric criterion definition | Controls score meaning and weighting |
| 4 | Project Defaults | Controls allowed tools, CSS policy, Elementor Pro availability, and default constraints |
| 5 | Official docs / verified external source | Supports platform capability only; not proof that a candidate actually uses it |
| 6 | Reasonable inference | Allowed only with `INFERRED_EVIDENCE` and confidence not above `medium` |
| 7 | Missing evidence | Must become `ABSENT_EVIDENCE` and usually `?`, not a guessed score |

Critical distinction:

- Official Elementor documentation proves platform capability, not the candidate's actual behavior.
- A screenshot proves appearance, not DOM, CSS, plugin use, query source, alt semantics, or responsive behavior.
- A Stage 3 candidate claim proves what the candidate proposes, not whether the proposal is high-scoring.

---

## Evidence Labels

Every criterion score must use one label from this closed set:

| Label | Meaning | Default scoring effect |
|---|---|---|
| `SUPPORTED_EVIDENCE` | Direct Stage 2/3 evidence supports the criterion claim | Numeric score allowed; may be high if anchor supports it |
| `PARTIALLY_SUPPORTED_EVIDENCE` | Some support exists but important assumptions remain | Numeric score allowed, usually capped at 4 |
| `INFERRED_EVIDENCE` | Reasonable inference; not directly proven | Numeric score allowed only if non-critical, capped at 3 |
| `ABSENT_EVIDENCE` | Source material does not say enough | Use `?` unless clearly non-blocking; never treat as contradiction |
| `CONTRADICTED_EVIDENCE` | Stage 2/3 evidence conflicts with the candidate claim | Low score or gate failure; do not use `?` to hide the contradiction |
| `UNRESOLVED_CONFLICT` | Conflicting evidence exists but cannot yet be resolved | `?` if criterion-critical; otherwise capped at 2 |

Rules:

- `ABSENT_EVIDENCE` means “we do not know.”
- `CONTRADICTED_EVIDENCE` means “the evidence pushes against the claim.”
- Do not punish a candidate as if contradicted merely because evidence is absent.
- Do not hide a contradiction by marking it as unknown.

---

## Scoring Confidence

Every criterion score must include:

```text
confidence: high | medium | low | unknown
```

Rules:

- `SUPPORTED_EVIDENCE` may allow `high`.
- `PARTIALLY_SUPPORTED_EVIDENCE` usually allows `medium`.
- `INFERRED_EVIDENCE` must not exceed `medium`.
- `ABSENT_EVIDENCE` must use `unknown` when score is `?`.
- `CONTRADICTED_EVIDENCE` must use `low` unless resolved by explicit evidence.
- `UNRESOLVED_CONFLICT` must use `low` or `unknown`.

---

## Score Anchor Scale

Use this common anchor scale before applying criterion-specific guidance:

| Score | Meaning |
|---:|---|
| 5 | Strongly supported; low material risk; no blocking unknowns for this criterion |
| 4 | Supported; minor unresolved risk; likely acceptable after audit |
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

## Elementor Responsive Inheritance Rule

Absence of a mobile screenshot does not automatically force `Responsiveness = ?`.

Elementor responsive behavior can inherit from larger breakpoints, so Stage 4 may score the candidate based on desktop normal-flow inheritance potential when mobile-specific evidence is absent.

However, absent mobile evidence limits certainty.

| Situation | Max Responsiveness score |
|---|---:|
| Explicit desktop/tablet/mobile behavior is provided and credible | 5 |
| No mobile view, but candidate uses native normal-flow containers/grid, no fixed-width or coordinate-driven meaningful content, and Stage 2 has no mobile-risk signals | 4 |
| No mobile view, normal-flow potential is plausible, but section has complex cards, visual core, connector, overlay, or dense content | 3 |
| No mobile view and candidate relies on absolute/fixed coordinates, connector lines, floating cards, duplicate hidden sections, or unresolved collision risk | 2 |
| Candidate does not state enough structure to infer flow or breakpoint behavior | ? |

Rationale:

- `5` means responsive behavior is materially resolved.
- `4` means responsive behavior is not fully shown but low-risk inheritance is plausible.
- `3` means plausible but meaningfully uncertain.
- `2` means material risk is visible or structurally implied.
- `?` means scoring would require inventing the structure.

Evidence note required when mobile evidence is absent:

```text
evidence_note: Scored based on desktop normal-flow inheritance potential; mobile evidence absent.
```

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

Apply the Elementor Responsive Inheritance Rule above.

Score lower or use `?` when:

- mobile behavior is not specified and desktop flow is not inferable,
- connectors/floating cards depend on fixed coordinates,
- hidden/duplicate sections are required but not justified,
- tablet behavior is ignored and layout complexity is high.

Guardrail:

```text
A desktop screenshot does not prove mobile behavior.
A desktop normal-flow candidate may still have responsive inheritance potential.
```

### 4. Editability ×3

Score higher when text, icons, images, cards, links, and repeated items remain editable in Elementor or a clear content source.

Score lower when routine updates require:

- editing SVG path text,
- editing custom HTML,
- editing CSS,
- replacing a full-section image,
- changing hardcoded coordinates.

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

If a candidate has one or more `?` values, its final total must be:

```text
raw_weighted_total: incomplete
normalized_total: incomplete
final_score_status: incomplete
```

It must be excluded from mechanical total comparison until resolved.

---

## Unknown-to-Score Ceiling Rule

If a criterion materially depends on unresolved evidence, numeric scores are capped:

| Evidence state | Max numeric score if not `?` |
|---|---:|
| Supported evidence | 5 |
| Partially supported evidence | 4 |
| Inferred evidence only | 3 |
| Absent evidence but clearly non-blocking | 3 |
| Absent evidence and criterion-critical | `?` |
| Contradicted evidence | 2 unless resolved |
| Unresolved conflict | `?` or 2 depending on criterion criticality |

This rule prevents hidden optimism.

---

## Shared Unknown Consistency Rule

If the same unknown affects multiple candidates, handle it consistently.

The scorer must not mark a shared unknown as numeric `4` for one candidate and `?` for another unless the candidates provide different explicit mitigation evidence.

Every shared unknown must appear in the Uncertainty Register.

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
- A high normalized score cannot override a gate failure.
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

## Hidden Recommendation Ban v1.2

Stage 4 may report mechanical scores. It must not recommend.

### Auto-fail terms

If any of these appear in Stage 4 reasoning, the Self-Audit must fail:

```text
best
winner
recommended
preferred
optimal
safest
cleanest
final choice
primary choice
obviously better
clearly superior
بهترین
برنده
پیشنهادی
گزینه اصلی
انتخاب نهایی
امن‌ترین
تمیزترین
بهینه‌ترین
واضحاً بهتر
```

### Flag-only subjective terms

Non-mechanical adjectives/adverbs are flagged, not automatically failed, unless they imply a recommendation.

Examples:

```text
elegant
beautifully
simple
strong
weak
nice
polished
high-quality
تمیز
زیبا
قوی
ضعیف
حرفه‌ای
```

Rule:

```text
Default: non-mechanical term → flag for audit.
Auto-fail: direct recommendation, dismissal, or winner language.
```

### Mechanical vocabulary preference

Use structural language such as:

```text
maps_to
violates
requires
depends_on
conflicts_with
preserves
omits
contradicts
inherits_from
caps_at
```

Do not produce a full word dump. Output only:

```text
banned_terms_found:
subjective_phrases_flagged:
hidden_recommendation_scan: pass | fail
```

---

## Arithmetic Policy v1.2

LLMs are not trusted arithmetic engines.

### Complete candidates

For complete candidates with no `?`:

```text
raw_weighted_total = Σ(score × weight)
normalized_total = (raw_weighted_total / 125) × 100
```

If Python, calculator, spreadsheet, or runtime arithmetic is available, use it.

If arithmetic tooling is not available:

- show the formula,
- show row-level weighted values,
- mark `arithmetic_confidence: needs_audit`,
- do not claim final arithmetic certainty.

### Incomplete candidates

If any criterion is `?`:

```text
final_score_status: incomplete
raw_weighted_total: incomplete
normalized_total: incomplete
```

A provisional known-score may be shown only with this formula:

```text
known_weighted_average_1_to_5 = Σ(known score × weight) / Σ(known weights)
provisional_known_percent = known_weighted_average_1_to_5 × 20
known_weight_coverage = Σ(known weights) / 25
```

Required warning:

```text
This is not a final score. It excludes unresolved criteria and cannot be used for decision bands.
```

Never compare incomplete candidates by provisional known percent.

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

A score without Evidence Map support is invalid.

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
- raw_score: 1 | 2 | 3 | 4 | 5 | ?
- weight: ×4
- weighted_result: raw_score × weight | incomplete
- evidence_source: Stage 2 | Stage 3 | Rubric | Project Defaults | official docs | inference | missing
- evidence_label: SUPPORTED_EVIDENCE | PARTIALLY_SUPPORTED_EVIDENCE | INFERRED_EVIDENCE | ABSENT_EVIDENCE | CONTRADICTED_EVIDENCE | UNRESOLVED_CONFLICT
- confidence: high | medium | low | unknown
- evidence:
- reasoning:
- score_anchor_used:
- missing_evidence: only if score is ?
- blocking_level: only if score is ?
- evidence_note: optional, required for Responsiveness when mobile evidence is absent

[Repeat this exact structure for all 10 criteria.]

TOTAL:
- raw_weighted_total: /125 | incomplete
- normalized_total: /100 | incomplete
- provisional_known_percent: optional, incomplete candidates only
- known_weight_coverage: optional, incomplete candidates only
- arithmetic_confidence: verified_by_tool | needs_audit
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

| Candidate | Status | Gate | Elementor-Native ×4 | Normal-Flow ×4 | Responsiveness ×4 | Editability ×3 | Structural ×2 | Overlay ×2 | Performance ×2 | Accessibility ×2 | Design-System ×1 | Visual ×1 | Raw /125 | Normalized /100 | Completeness |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
```

Important:

- Use weighted results in the table, not raw criterion scores.
- Raw totals must be `/125`.
- Normalized totals must be `/100`.
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
RAW WEIGHTED TOTAL max = 125
NORMALIZED TOTAL max = 100
```

If using arithmetic tooling, show:

```text
ARITHMETIC CHECK
Candidate A01:
20 + 20 + 16 + 12 + 8 + 10 + 8 + 8 + 4 + 3 = 109 / 125
109 / 125 × 100 = 87.2 / 100
arithmetic_confidence: verified_by_tool
```

If tooling is unavailable, show:

```text
ARITHMETIC CHECK
Candidate A01:
formula: [row weighted results] / 125 × 100
arithmetic_confidence: needs_audit
```

If raw total exceeds `/125`, stop and recalculate.

If normalized total exceeds `/100`, stop and recalculate.

No candidate may be handed off with invalid arithmetic.

---

## Decision Bands

Decision bands use `normalized_total`, not `raw_weighted_total`.

```text
85–100 normalized → primary candidate after /score-audit
70–84 normalized  → acceptable with repair after /score-audit
below 70 normalized → reject or keep only as documented risk
```

Do not apply decision bands to incomplete candidates.

Do not apply decision bands before `/score-audit` as a recommendation.

---

## Uncertainty Register

After the scoring table, output:

```text
UNCERTAINTY REGISTER

| Unknown | Source Stage | Affected Candidate(s) | Affected Criterion | Evidence Label | Current Handling | Blocking Level | Evidence Needed |
|---|---|---|---|---|---|---|---|
```

Every `?` score must appear in the Uncertainty Register.

Every Stage 3 Unknown Propagation Ledger item must either:

- appear in the Uncertainty Register, or
- be marked `not scoring-relevant` with reason.

---

## Audit_Trail_Payload

Stage 4 must produce a structured payload for Stage 5.

Stage 5 uses this payload as the primary audit index, but Stage 5 may inspect Stage 2, Stage 3, and the rubric when a spot-check trigger exists.

Required schema:

```text
Audit_Trail_Payload:
  schema_version: ev4-score-evidence-payload@1.2.0
  stage4_version: 1.2.0
  rubric_version: 1.2
  candidates:
    - candidate_id:
      classification:
      gate_status:
      final_score_status: complete | incomplete
      raw_weighted_total:
      normalized_total:
      provisional_known_percent:
      known_weight_coverage:
      arithmetic_confidence: verified_by_tool | needs_audit
      gates_checked:
        - gate:
          result: pass | fail | unresolved
          evidence_label:
      unknown_scores:
        - criterion:
          evidence_label:
          missing_evidence:
          blocking_level:
      contradictions:
        - criterion:
          contradicted_claim:
          evidence:
          scoring_effect:
      banned_terms_found:
        - term:
          location:
          severity: auto_fail | flag
      subjective_phrases_flagged:
        - phrase:
          location:
      spot_check_triggers:
        - trigger:
          source_to_check: Stage 2 | Stage 3 | Rubric | Project Defaults
```

Spot-check triggers include:

- any gate fail or unresolved gate,
- any `?` on a ×4 criterion,
- any `CONTRADICTED_EVIDENCE`,
- any `UNRESOLVED_CONFLICT`,
- arithmetic confidence `needs_audit`,
- hidden recommendation scan failure,
- unusually high score from weak evidence,
- random audit sample requested by `/score-audit`.

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
- Hidden recommendation scan passed: yes/no
- Raw and normalized totals separated correctly: yes/no
- Arithmetic confidence declared: yes/no
- Audit_Trail_Payload generated with schema version: yes/no
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
- Every score has evidence label from the v1.2 closed set: yes/no
- Every score has confidence: yes/no
- Score anchors used: yes/no
- Every ? has missing evidence: yes/no
- Every ? has blocking level: yes/no
- ABSENT_EVIDENCE not treated as contradiction: yes/no
- CONTRADICTED_EVIDENCE not hidden as unknown: yes/no
- Elementor inheritance rule applied to Responsiveness when mobile evidence is absent: yes/no
- Shared unknowns handled consistently: yes/no
- Gate rules applied: yes/no
- Hidden recommendation scan completed: yes/no
- No auto-fail recommendation term appears: yes/no
- Subjective phrase flags recorded: yes/no
- No Visual Precision override: yes/no
- Complete candidates use /125 raw and /100 normalized totals: yes/no
- Incomplete candidates do not have final totals: yes/no
- Provisional known-score, if used, is marked non-final: yes/no
- Arithmetic confidence declared: yes/no
- No raw total exceeds /125: yes/no
- No normalized total exceeds /100: yes/no
- Summary table complete: yes/no
- Uncertainty Register complete: yes/no
- Audit_Trail_Payload present and schema-versioned: yes/no
- Candidate classification assigned: yes/no
- Allowed next step is /score-audit: yes/no
```

If any answer is `no`, revise Stage 4 output before proceeding.

---

## Scientific & Architectural Basis

This stage is based on five design principles:

1. **Program-aided arithmetic** — use tools or formulas for numeric work; do not trust mental arithmetic for weighted scoring.
2. **Constrained evaluation language** — reduce hidden recommendation bias by banning winner language and flagging subjective phrasing.
3. **Domain-specific rule injection** — Elementor responsive inheritance must be handled as a rule, not guessed from generic web-design intuition.
4. **Epistemic separation** — absent evidence, contradicted evidence, and unresolved conflict are separate states.
5. **Structured judge handoff** — Stage 5 receives a schema-versioned audit payload and retains spot-check authority.

Reference basis to keep in project research notes:

- Program-Aided Language Models (PAL), Gao et al., 2022.
- Lost in the Middle, Liu et al., 2023.
- Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena, Zheng et al., 2023.
- Elementor Responsive Editing and inherited responsive values.
- W3C WAI Image Alt Decision Tree.
- OpenAI Evals guidance for structured evaluation workflows.

---

## Pass Criteria

Stage 4 passes only if:

- It uses the rubric weights correctly.
- It treats `/125` raw total and `/100` normalized total separately.
- It uses the v1.2 evidence label closed set.
- It separates `ABSENT_EVIDENCE` from `CONTRADICTED_EVIDENCE`.
- It applies Elementor Responsive Inheritance scoring caps.
- It does not calculate final totals for incomplete candidates.
- It uses tool-first arithmetic or marks arithmetic as `needs_audit`.
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
- It includes `Audit_Trail_Payload` with `schema_version: ev4-score-evidence-payload@1.2.0`.
- It gives Stage 5 spot-check authority.
- It classifies candidates mechanically without winner language.
- It hands off to `/score-audit`.

---

## Allowed Next Step

```text
/score-audit
```


## Intermediate Stage Artifact Boundary

Producer-owned intermediate Artifact: `/score-evidence` emits `ev4-architect-pipeline-stage-artifact@1.1.0` and must reference a valid Stage 3 receipt and exact artifact digest before scoring acceptance. It must not reconstruct a missing Matrix/Ledger from prose or anchors, normalize absent artifacts, score candidates absent from validated Stage 3, discard Stage 3 unknowns, emit final totals for contract-critical `?`, or claim audited scores.

If an executable validator/tool is available, place the complete ordered Stage Artifact sequence in one directory and execute the canonical Validation Transaction:

```bash
python scripts/check-architect-pipeline-stage-boundary.py validate-run \
  --sequence <artifact-directory> \
  --output <validation-bundle-directory> \
  --format json

python scripts/check-architect-pipeline-stage-boundary.py validate-bundle \
  --bundle <validation-bundle-directory> \
  --format json
```

Only a Bundle independently verified by `validate-bundle` with `bundle_integrity_status=valid`, `run_validation_status=valid`, and `authorization_valid=true` authorizes next-stage continuation. `diagnose-artifact` is non-authorizing and must never be used to construct a Receipt, Boundary, Anchor, or continuation claim. If execution is unavailable, do not claim machine validation or emit a validated next-stage anchor; return `validation_required` or `insufficient_evidence`, preserve the Artifact sequence, and provide both canonical commands above.
