# Stage 5 — /score-audit: Independent Scoring Audit

Status: confirmed_v1.0.0  
Version: 1.2.0  
Depends on: Stage 4 — `/score-evidence`  
Next stage: Stage 6 — `/recommend`  
Input payload schema: `ev4-score-evidence-payload@1.2.0`  
Output payload schema: `ev4-score-audit-payload@1.0.0`

---

## Purpose

The `/score-audit` phase independently audits whether Stage 4 scored architecture candidates correctly, conservatively, and reproducibly.

Stage 5 is not a recommendation stage. It does not choose a winner, rank candidates, or repair architecture candidates. It checks whether `/score-evidence` followed the rubric and whether the scoring output is safe enough to hand off to `/recommend`.

Mental model:

```text
Stage 4 is the scale.
Stage 5 is the inspector who checks whether the scale was calibrated,
used the right units, rejected invalid weights, and wrote a clean audit log.
```

---

## Core Rule

Audit the scoring process, not the visual design preference.

Stage 5 must answer one question:

```text
Can the Stage 4 scoring output be trusted enough for Stage 6 /recommend?
```

If the answer is no, Stage 5 must return the case to `/score-evidence` with precise repair instructions.

---

## Required Inputs Gate

Stage 5 requires all of the following:

1. Completed Stage 2 `DECOMPOSITION SNAPSHOT`.
2. Completed Stage 3 `ARCHITECTURE CANDIDATES`.
3. Stage 3 `Architecture Coverage Matrix`.
4. Stage 3 `Unknown Propagation Ledger`.
5. Completed Stage 4 `SCORE-EVIDENCE REPORT`.
6. Stage 4 `Audit_Trail_Payload`.
7. Current rubric: `rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md`.
8. Current Project Defaults from `STATUS.md` or Project Instructions.

If any required input is missing, Stage 5 must stop and return:

```text
audit_status: fail_missing_input
missing_inputs:
- ...
next_action: rerun_or_repair_previous_stage
```

---

## Payload Schema Gate

Stage 4 must provide:

```text
Audit_Trail_Payload.schema_version = ev4-score-evidence-payload@1.2.0
```

If the schema version is missing, unknown, older, or incompatible, Stage 5 must fail the audit.

Allowed result:

```text
audit_status: fail_schema_mismatch
required_schema: ev4-score-evidence-payload@1.2.0
received_schema: ...
next_action: rerun_stage_4_with_current_payload_schema
```

---

## Audit Source Policy

Stage 5 uses `Audit_Trail_Payload` as the primary audit index, but it must not trust the payload blindly.

Stage 5 may and should spot-check Stage 2, Stage 3, the rubric, and Project Defaults when any trigger appears.

Mandatory spot-check triggers:

1. Any immediate rejection gate pass/fail.
2. Any `?` on a ×4 or ×3 criterion.
3. Any `CONTRADICTED_EVIDENCE`.
4. Any `UNRESOLVED_CONFLICT`.
5. Any `ABSENT_EVIDENCE` converted into a numeric score.
6. Any criterion score of `5` without direct support.
7. Any `Responsiveness` score above the Elementor inheritance cap.
8. Any `arithmetic_confidence: needs_audit`.
9. Any hidden recommendation term or subjective phrase flag.
10. Any candidate classified as `complete_gate_pass` while still containing critical unknowns.
11. Any borderline normalized result near a decision band.
12. At least one random candidate sample, even if no trigger appears.

---

## Severity Levels

All audit findings must use this closed severity set:

| Severity | Meaning | Effect |
|---|---|---|
| `blocker` | Invalidates Stage 4 output | Must rerun or repair Stage 4 before Stage 6 |
| `major` | Material scoring defect or unstable decision risk | Repair required unless explicitly waived by user |
| `minor` | Local issue that does not change candidate classification | May proceed only with warning |
| `note` | Informational observation | No repair required |

---

## Audit Checkpoints

Stage 5 must check the following checkpoints in order.

### 1. Input Completeness Audit

Verify that Stage 4 used all required inputs.

Fail if Stage 4 scored without:

- Stage 2 decomposition,
- Stage 3 candidates,
- Stage 3 coverage matrix,
- Stage 3 unknown propagation ledger,
- current rubric,
- project defaults.

### 2. Rubric Fidelity Audit

Verify that Stage 4 used the current rubric weights and criteria:

| Criterion | Weight |
|---|---:|
| Elementor-Native Feasibility | ×4 |
| Normal-Flow Safety | ×4 |
| Responsiveness | ×4 |
| Editability | ×3 |
| Structural Clarity | ×2 |
| Overlay Containment | ×2 |
| Performance | ×2 |
| Accessibility | ×2 |
| Design-System Fit | ×1 |
| Visual Precision | ×1 |

Fail if:

- a criterion is missing,
- a weight is wrong,
- visual precision is allowed to override high-weight criteria,
- the total is treated as `/100` before normalization.

### 3. Evidence Label Audit

Every criterion score must use exactly one label from this closed set:

```text
SUPPORTED_EVIDENCE
PARTIALLY_SUPPORTED_EVIDENCE
INFERRED_EVIDENCE
ABSENT_EVIDENCE
CONTRADICTED_EVIDENCE
UNRESOLVED_CONFLICT
```

Audit rules:

- `ABSENT_EVIDENCE` must not be treated as contradiction.
- `CONTRADICTED_EVIDENCE` must not be hidden as unknown.
- `INFERRED_EVIDENCE` must not exceed medium confidence.
- `ABSENT_EVIDENCE` with critical impact must produce `?`.
- `CONTRADICTED_EVIDENCE` must produce a low score, gate failure, or explicit defect.

### 4. Unknown Discipline Audit

Verify that Stage 4 did not convert unknowns into confident numbers.

Blocker conditions:

- Any `?` criterion exists but Stage 4 still outputs a final `raw_weighted_total`.
- Any `?` criterion exists but Stage 4 still outputs a final `normalized_total`.
- A critical Stage 2 unknown disappears from Stage 4 without explanation.
- A shared unknown is treated inconsistently across affected candidates.

Allowed behavior:

```text
final_total: incomplete
provisional_known_percent: allowed only as non-final
```

### 5. Arithmetic Audit

Verify score arithmetic.

Stage 5 must check:

```text
raw_weighted_total = Σ(score × weight) for all known criteria
normalized_total = (raw_weighted_total / 125) × 100
known_weighted_average_1_to_5 = Σ(known score × weight) / Σ(known weights)
provisional_known_percent = known_weighted_average_1_to_5 × 20
```

Rules:

- If all criteria are numeric, verify raw `/125` and normalized `/100` math.
- If any criterion is `?`, final totals must be `incomplete`.
- If arithmetic tooling is available, Stage 5 should recompute using the tool.
- If arithmetic tooling is unavailable, Stage 5 must mark arithmetic as `not_verified_by_tool` and require external verification if the result affects a decision band.

### 6. Immediate Rejection Gate Audit

Verify the mandatory gates:

```text
Elementor-Native Feasibility < 3 → immediate_reject
Normal-Flow Safety < 2 → immediate_reject
Responsiveness < 2 → immediate_reject
```

Blocker conditions:

- Gate condition met but candidate not marked `immediate_reject`.
- Candidate marked `complete_gate_pass` while a gate failed.
- Gate score hidden as `?` when direct contradictory evidence exists.

### 7. Elementor Responsive Inheritance Audit

Verify that Stage 4 applied the Stage 4 Elementor Responsive Inheritance Rule correctly.

Audit checks:

- Missing mobile screenshot did not automatically become `?` when desktop flow was inferable.
- Missing mobile screenshot did not allow `Responsiveness = 5`.
- `Responsiveness = 4` was used only for low-risk native normal-flow cases with no mobile-risk signal.
- `Responsiveness = 3` was used for plausible but meaningfully uncertain cases.
- `Responsiveness = 2` was used for fixed/absolute/connector/floating collision risk.
- `Responsiveness = ?` was used only when structure was not inferable enough to score.

### 8. Hidden Recommendation Audit

Stage 5 must scan Stage 4 reasoning for recommendation leakage.

Auto-fail direct recommendation terms include:

```text
best
winner
recommended
preferred
optimal
clearly superior
strongest option
safest option
best overall
بهترین
برنده
پیشنهادی
گزینه اصلی
برتر
امن‌ترین
بهینه‌ترین
```

Flag-only subjective terms include:

```text
elegant
clean
simple
strong
beautifully
obviously
تمیز
قوی
زیبا
بدیهی
واضحاً
```

Rules:

- Direct recommendation terms before `/recommend` are `blocker` unless quoted as forbidden terms.
- Subjective terms are `minor` or `major` depending on whether they bias the score.
- Mechanical verbs are preferred: `maps_to`, `violates`, `requires`, `depends_on`, `conflicts_with`, `preserves`, `omits`, `contradicts`.

### 9. Fairness and Consistency Audit

Verify that the same criterion means the same thing across candidates.

Major defects:

- One candidate receives a higher score from weaker evidence than another candidate with stronger evidence.
- A shared unknown caps one candidate but not another without reason.
- Dynamic/Loop evidence is assumed for one repeated-card candidate but denied for another with similar evidence.
- Visual precision inflates the total despite low native/flow/responsive scores.

### 10. Candidate Classification Audit

Every candidate must have one classification:

```text
complete_gate_pass
complete_but_immediate_reject
incomplete_unresolved
approval_required_excluded
rejected_risk_documented
```

Fail if classification conflicts with gates, unknowns, or approval requirements.

### 11. Audit Trail Payload Audit

Verify that Stage 4 emitted a valid `Audit_Trail_Payload` containing at least:

```text
schema_version
stage_4_version
rubric_version
candidate_id
candidate_classification
gate_checks
criteria_with_question_mark
absent_evidence_items
contradicted_evidence_items
unresolved_conflicts
arithmetic_confidence
provisional_known_percent_if_any
hidden_recommendation_scan
stage_5_spot_check_triggers
```

Fail if payload is missing, malformed, schema-incompatible, or omits known defects.

---

## Stage 5 Output Format

Stage 5 must output exactly this structure:

Executable transaction boundary: the current `ev4-architect-pipeline-stage-artifact@1.1.0` Schema recognizes `pass`, `fail_missing_input`, `fail_scoring`, and `insufficient_evidence` for `overall_audit_status`. Only `pass` with `allowed_next_stage: /recommend` and an empty `required_repairs` list can authorize Stage 6. Every failure status, unsupported status, or contradictory pass is non-authorizing. The broader status vocabulary below, including `pass_with_minor_flags`, remains prose-only until separately implemented.

```text
SCORE AUDIT REPORT

Audit metadata:
- audit_stage: /score-audit
- audit_version: 1.0.0
- input_payload_schema: ev4-score-evidence-payload@1.2.0
- output_payload_schema: ev4-score-audit-payload@1.0.0
- rubric_version: ...

Overall audit status:
- pass
- pass_with_minor_flags
- fail_requires_score_repair
- fail_requires_stage_3_repair
- fail_missing_input
- fail_schema_mismatch

1. Input and schema gate
2. Candidate audit matrix
3. Gate audit
4. Evidence-label audit
5. Unknown-discipline audit
6. Arithmetic audit
7. Responsiveness inheritance audit
8. Hidden recommendation audit
9. Fairness and consistency audit
10. Findings
11. Required repairs
12. Score_Audit_Payload
```

---

## Candidate Audit Matrix Format

Use this table for every Stage 4 candidate:

| Candidate | Stage 4 classification | Audit status | Blockers | Majors | Minors | Repair required |
|---|---|---|---:|---:|---:|---|
| A01 | ... | pass/fail | 0 | 0 | 0 | yes/no |

---

## Finding Format

Each finding must use this format:

```text
Finding ID: AUD-###
Severity: blocker | major | minor | note
Candidate: ...
Checkpoint: ...
Observed: ...
Expected: ...
Evidence source: Stage 2 | Stage 3 | Stage 4 | Rubric | Defaults | Payload
Repair: ...
```

---

## Repair Routing

Stage 5 must route failed audits precisely:

| Failure type | Route |
|---|---|
| Bad arithmetic only | `/score-evidence` repair |
| Missing or invalid payload | `/score-evidence` rerun |
| Unknown converted to number | `/score-evidence` repair |
| Gate misapplied | `/score-evidence` repair |
| Stage 3 candidate lacks required structure | `/architectures` repair, then rerun `/score-evidence` |
| Stage 2 unknown missing or ambiguous | `/decompose` repair, then rerun later stages |
| Hidden recommendation leak | `/score-evidence` language repair |
| Rubric mismatch | update rubric reference, rerun `/score-evidence` |

---

## Pass Criteria

Stage 5 passes only if:

1. Required inputs are present.
2. Stage 4 payload schema is valid.
3. No blocker findings exist.
4. No unresolved major findings affect candidate classification.
5. All gate checks are correct.
6. `ABSENT_EVIDENCE` and `CONTRADICTED_EVIDENCE` are separated.
7. Unknowns are not converted into final totals.
8. Arithmetic is verified or explicitly marked `needs_external_verification`.
9. Hidden recommendation scan passes or flags only non-material phrasing.
10. Stage 4 is safe to hand off to `/recommend`.

If these are not met, Stage 5 must not allow Stage 6.

---

## Score_Audit_Payload Schema

Stage 5 must emit:

```text
Score_Audit_Payload:
  schema_version: ev4-score-audit-payload@1.0.0
  audit_stage: /score-audit
  audit_version: 1.0.0
  input_payload_schema: ev4-score-evidence-payload@1.2.0
  overall_audit_status: pass | pass_with_minor_flags | fail_requires_score_repair | fail_requires_stage_3_repair | fail_missing_input | fail_schema_mismatch
  stage_6_allowed: true | false
  candidates:
    - candidate_id: ...
      stage_4_classification: ...
      audit_status: pass | fail
      blocker_count: ...
      major_count: ...
      minor_count: ...
      required_repairs:
        - ...
  global_findings:
    - finding_id: ...
      severity: ...
      checkpoint: ...
      repair: ...
  spot_checks_performed:
    - trigger: ...
      source_checked: ...
      result: ...
  next_action: proceed_to_recommend | repair_score_evidence | repair_architectures | repair_decompose
```

---

## Forbidden Actions

Stage 5 must not:

- recommend a candidate,
- rank candidates,
- produce a final architecture,
- rewrite the Stage 4 scores silently,
- fix Stage 3 candidate content inside the audit,
- ignore schema mismatch,
- rely only on Stage 4 prose when payload contradicts it,
- allow Stage 6 if a blocker exists.

---

## Scientific and Architectural Basis

Stage 5 exists because a multi-stage LLM pipeline needs an independent verification layer.

Relevant principles:

1. **Structured judge handoff** — long context can hide important evidence; a compact payload gives the judge an audit index.
2. **Spot-check authority** — the judge must not trust its audit index blindly; otherwise a malformed payload becomes a single point of failure.
3. **LLM-as-a-judge limitations** — judge models can be useful but are vulnerable to position, verbosity, and self-enhancement biases.
4. **Arithmetic isolation** — score arithmetic must be checked separately from prose reasoning.
5. **Epistemic separation** — missing evidence, inferred evidence, contradicted evidence, and unresolved conflicts require different audit behavior.

---

## Handoff

If Stage 5 passes:

```text
Allowed next stage: /recommend
```

If Stage 5 fails:

```text
Return to the precise repair route indicated by Score_Audit_Payload.next_action.
```


## Intermediate Stage Artifact Boundary

Producer-owned intermediate Artifact: `/score-audit` emits `ev4-architect-pipeline-stage-artifact@1.1.0` and remains an independent audit. Missing Stage 2, Stage 3, or Stage 4 validated lineage returns the earliest repair target and must not be silently repaired. Passing audit preserves `selected_candidate_id: null`, `scores_audited: true`, and `allowed_next_stage: /recommend`.

For the current executable transaction, `overall_audit_status: pass` is necessary but not sufficient: `allowed_next_stage` must equal `/recommend` and `required_repairs` must be empty. `pass_with_minor_flags` is not currently Schema-supported and must not authorize continuation.

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
