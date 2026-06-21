# Elementor V4 — Architecture Scoring Rubric

Version: 1.2  
Status: confirmed_hardened_for_stage_4_v1.2.0  
Scope: Elementor V4 architecture evaluation  
Language: Persian reports, English technical labels allowed

---

## Purpose

This rubric scores Elementor V4 section architecture candidates. It is not a visual beauty contest and it must not be used as a recommendation stage.

The rubric prioritizes:

1. Elementor-native feasibility
2. Normal-flow safety
3. Responsiveness
4. Editability
5. Structural clarity
6. Overlay containment
7. Performance
8. Accessibility
9. Design-system fit
10. Visual precision

---

## Scoring Method

For each candidate:

1. Give each criterion a raw score from `1` to `5`, or `?` if evidence is insufficient.
2. Multiply each numeric raw score by its weight.
3. If all 10 criteria are numeric, sum all weighted values to get `raw_weighted_total`.
4. Normalize to `/100` using this formula:

```text
normalized_total = (raw_weighted_total / 125) × 100
```

Why `/125`?

```text
(5×4) + (5×4) + (5×4) + (5×3) + (5×2) + (5×2) + (5×2) + (5×2) + (5×1) + (5×1)
= 125
```

Therefore decision bands are based on `normalized_total`, not the raw weighted total.

If any criterion is `?`, do not calculate a final normalized score. Mark the candidate as `incomplete`.

---

## Incomplete Candidate Provisional Formula

If any criterion is `?`, Stage 4 may show a provisional known-score only for orientation:

```text
known_weighted_average_1_to_5 = Σ(known score × weight) / Σ(known weights)
provisional_known_percent = known_weighted_average_1_to_5 × 20
known_weight_coverage = Σ(known weights) / 25
```

Rules:

- This is not a final score.
- It cannot be used for decision bands.
- It cannot be used to compare incomplete candidates.
- The candidate must remain `final_score_status: incomplete`.

---

## Evidence Semantics

Every criterion score must be labeled with one evidence state:

| Label | Meaning | Scoring implication |
|---|---|---|
| `SUPPORTED_EVIDENCE` | Direct Stage 2/3 evidence supports the claim | Numeric score allowed |
| `PARTIALLY_SUPPORTED_EVIDENCE` | Some support exists, but assumptions remain | Usually capped at 4 |
| `INFERRED_EVIDENCE` | Reasonable inference, not directly proven | Usually capped at 3 |
| `ABSENT_EVIDENCE` | Source material does not say enough | Usually `?`; never contradiction by itself |
| `CONTRADICTED_EVIDENCE` | Evidence conflicts with the candidate claim | Low score or gate failure |
| `UNRESOLVED_CONFLICT` | Conflicting evidence cannot yet be resolved | `?` or capped at 2 |

Core rule:

```text
Absent evidence is not contradicted evidence.
Contradicted evidence is not unknown evidence.
```

---

## Arithmetic Policy

LLMs must not be trusted as arithmetic engines.

Stage 4 should use Python, calculator, spreadsheet, or another runtime when available.

If arithmetic tooling is not available:

- show weighted row values,
- show formulas,
- mark `arithmetic_confidence: needs_audit`,
- hand the result to `/score-audit` for arithmetic verification.

---

## Criteria

### 1. Elementor-Native Feasibility

Weight: ×4  
Raw weighted maximum: 20

Does this architecture work with the Elementor version and tools available in the project?

| Score | Meaning |
|---:|---|
| 5 | Feasible with native Elementor containers/widgets and no Custom CSS or HTML Widget |
| 4 | Needs simple scoped Custom CSS; no HTML Widget required for meaningful content |
| 3 | Needs HTML Widget, SVG Element, or controlled non-native layer but remains maintainable |
| 2 | Needs Pro plugin/add-on, unapproved dependency, or fragile custom interaction |
| 1 | Not realistically feasible in Elementor V4 or extremely risky |

Immediate rejection gate:

```text
Elementor-Native Feasibility < 3 → immediate_reject
```

Guardrail:

```text
Repeated visual group does not prove Loop Grid, CPT, ACF, WooCommerce, or dynamic data.
```

---

### 2. Normal-Flow Safety

Weight: ×4  
Raw weighted maximum: 20

Does meaningful content remain in normal flow?

| Score | Meaning |
|---:|---|
| 5 | All meaningful content remains in flow; absolute only for decoration/overlay inside a controlled stage |
| 4 | One justified content-related exception; still stable and auditable |
| 3 | Multiple content items rely on positioning; repair may be needed |
| 2 | Main columns, cards, or text are absolute/coordinate-driven |
| 1 | Most or all meaningful content is detached from normal flow |

Immediate rejection gate:

```text
Normal-Flow Safety < 2 → immediate_reject
```

---

### 3. Responsiveness

Weight: ×4  
Raw weighted maximum: 20

Can the architecture work across desktop, tablet, and mobile without brittle duplication?

| Score | Meaning |
|---:|---|
| 5 | One DOM; explicit credible desktop/tablet/mobile strategy; limited overrides |
| 4 | One DOM; no mobile view shown, but native normal-flow inheritance potential is strong and Stage 2 has no material mobile-risk signal |
| 3 | Plausible responsive inheritance, but meaningful uncertainty remains due to dense content, visual core, connectors, overlays, or layout complexity |
| 2 | Mobile likely breaks, or fixed/absolute/connector/floating strategy creates unresolved collision risk |
| 1 | Requires separate mobile section or is not usable on mobile |

Immediate rejection gate:

```text
Responsiveness < 2 → immediate_reject
```

Important:

- Absence of mobile evidence does not automatically force `?`.
- Absence of mobile evidence also does not allow score `5`.
- Use Stage 4's Elementor Responsive Inheritance Rule to cap the score.

---

### 4. Editability

Weight: ×3  
Raw weighted maximum: 15

Can normal content edits happen in Elementor or a clear content source without editing CSS/HTML?

| Score | Meaning |
|---:|---|
| 5 | Text, icons, images, links, and repeated items are editable; add/remove item flow is clear |
| 4 | Text/icon/image edits are easy; changing item count may need layout adjustment |
| 3 | Basic text edits are easy; layout changes need CSS or deeper editing |
| 2 | Routine edits require CSS/HTML/SVG changes |
| 1 | Section is mostly static image or hardcoded content |

---

### 5. Structural Clarity

Weight: ×2  
Raw weighted maximum: 10

Will the Elementor Structure Panel/tree remain understandable?

| Score | Meaning |
|---:|---|
| 5 | Clean purpose-first tree; each container has a clear role |
| 4 | Mostly clear tree with minor ambiguous labels/wrappers |
| 3 | Understandable but needs notes or conventions |
| 2 | Deep, wrapper-heavy, or hard to inspect |
| 1 | Chaotic structure with unclear role separation |

---

### 6. Overlay Containment

Weight: ×2  
Raw weighted maximum: 10

Are overlays/absolute elements contained inside a named relative stage?

| Score | Meaning |
|---:|---|
| 5 | All overlays are contained in a named relative stage and do not control meaningful content layout |
| 4 | Minor controlled overlay exception with clear reason |
| 3 | Some overlays are section/body-relative; manageable risk |
| 2 | Overlay containment is vague or collision-prone |
| 1 | Overlay strategy is absent or uncontrolled |

---

### 7. Performance

Weight: ×2  
Raw weighted maximum: 10

Are DOM depth, image weight, scripts, and visual layers controlled?

| Score | Meaning |
|---:|---|
| 5 | Efficient DOM, optimized assets, no unnecessary layers or scripts |
| 4 | Minor extra wrappers/layers with low performance impact |
| 3 | Moderately heavy DOM/assets; repair may be needed |
| 2 | Heavy images, deep DOM, or unverified animation/JS risk |
| 1 | Full-section image, very heavy DOM, or likely poor LCP/CLS profile |

---

### 8. Accessibility

Weight: ×2  
Raw weighted maximum: 10

Does the architecture preserve real text, logical reading order, alt decisions, and focus behavior?

| Score | Meaning |
|---:|---|
| 5 | Reading order is logical; meaningful images/alt/focus behavior are resolved |
| 4 | Reading order is likely correct; minor alt/focus unknown remains |
| 3 | DOM order may differ from visual order or some semantic decisions are unresolved |
| 2 | Meaningful text/image content is likely inaccessible |
| 1 | Section is effectively inaccessible |

Guardrail:

```text
Visual Core is not automatically decorative.
Decoration is not automatically alt="" unless context supports it.
```

---

### 9. Design-System Fit

Weight: ×1  
Raw weighted maximum: 5

Can the architecture use classes, variables, tokens, and component patterns?

| Score | Meaning |
|---:|---|
| 5 | Clear reusable class/variable/component strategy |
| 4 | Reusable styling is plausible with minor follow-up |
| 3 | Reuse is possible but not clean; many inline or one-off decisions |
| 2 | Each instance likely needs separate styling |
| 1 | Design system is not realistically applicable |

---

### 10. Visual Precision

Weight: ×1  
Raw weighted maximum: 5

Can the architecture approximate the reference visual without sacrificing higher-priority criteria?

| Score | Meaning |
|---:|---|
| 5 | Very close visual match without compromising core architecture |
| 4 | Close visual match with minor acceptable differences |
| 3 | Structure is right; some decoration/detail simplified |
| 2 | General structure remains but many details are lost |
| 1 | Low visual similarity |

Important:

```text
Visual Precision must never override Elementor-Native Feasibility, Normal-Flow Safety, Responsiveness, or Editability.
```

---

## Decision Rules

Decision bands use `normalized_total`:

```text
85–100 → primary candidate after /score-audit
70–84  → acceptable with repair after /score-audit
below 70 → reject or keep only as documented risk
```

Immediate rejection overrides total:

```text
Elementor-Native Feasibility < 3 → immediate_reject
Normal-Flow Safety < 2 → immediate_reject
Responsiveness < 2 → immediate_reject
```

If any gate score is `?`, gate status is `unresolved` and the candidate cannot be treated as primary-ready.

Incomplete candidates do not receive decision-band status.

---

## Notes for the Model

- Do not recommend an architecture before full scoring and `/score-audit`.
- Use only the Stage 4 v1.2 evidence labels.
- If two architectures have close normalized totals, ×4 criteria are more important than low-weight visual precision.
- Visual Precision is never a final decision reason by itself.
- If evidence is insufficient for a criterion, mark it `?` and explain the missing evidence.
- Do not convert unknowns into optimistic numeric scores.
- Never compare incomplete candidates by numeric total or provisional known percent.
- Hidden recommendation wording is a Stage 4 failure.

---

*This rubric is part of the fixed Elementor V4 Architect Prompt Pack.*
