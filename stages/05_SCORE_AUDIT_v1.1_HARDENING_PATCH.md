# Stage 5 v1.1 Hardening Patch — Independent Scoring Audit

Status: active_patch_for_stage_5  
Patch version: 1.1.0  
Applies to: `stages/05_SCORE_AUDIT.md`  
Input payload schemas: `ev4-score-evidence-payload@1.2.0`, `ev4-score-evidence-payload@1.3.0`  
Output payload schema: `ev4-score-audit-payload@1.1.0`

---

## Purpose

This patch makes Stage 5 stricter before Stage 6 `/recommend`.

Stage 5 is the independent inspector of Stage 4. It must not recommend, rank, or redesign. It audits whether Stage 4 scoring can be trusted.

---

## Immediate Hardening Additions

Stage 5 v1.1.0 adds these required controls:

1. **Arithmetic verification for every `needs_audit` flag.**
2. **Cross-candidate consistency audit.**
3. **Mandatory opening of all Stage 4 spot-check triggers.**
4. **Gate override detection.**
5. **Scoring calibration case awareness.**
6. **N/A denominator audit for rubric 1.3.**
7. **Schema-versioned output payload upgrade.**

---

## 1. Arithmetic Verification Upgrade

Stage 5 must recompute all arithmetic when Stage 4 reports:

```text
arithmetic_confidence: needs_audit
```

Recompute:

```text
raw_weighted_total
applicable_weight_total
applicable_raw_max
normalized_total
known_weighted_average_1_to_5
provisional_known_percent
known_weight_coverage
```

Rules:

- If arithmetic tooling is available, use it.
- If tooling is not available and the result affects a gate, classification, or decision band, Stage 5 cannot pass the audit.
- Arithmetic self-confirmation by Stage 4 is not sufficient.
- If any criterion is `?`, Stage 5 must verify that final totals are `incomplete`.
- If any criterion is `N/A`, Stage 5 must verify that its weight was excluded from the denominator.

Finding severity:

```text
wrong total that affects classification → blocker
wrong total that does not affect classification → major
missing arithmetic confidence flag → major
```

---

## 2. Cross-Candidate Consistency Audit

Stage 5 must check whether shared evidence and shared unknowns are handled consistently across candidates.

Required checks:

```text
same Stage 2 unknown → same cap logic unless Stage 3 changes the premise
same contradiction → same evidence label family
same absent evidence → not converted to numeric for one candidate and ? for another without reason
same mobile evidence state → same responsiveness cap family
same overlay absence → same N/A eligibility logic
same repeated-card evidence → same dynamic/Loop caution
```

This is not a second scoring pass. It is a consistency audit.

Defects:

- Inconsistent shared unknown handling → major.
- Inconsistent gate handling → blocker.
- Inconsistent use of `N/A` denominator → blocker if it affects normalized total.

---

## 3. Mandatory Spot-Check Trigger Resolution

Stage 4's `stage_5_spot_check_triggers` field is not informational. Stage 5 must open and resolve every trigger.

For each trigger, Stage 5 must output:

```text
trigger_id:
source:
what_was_checked:
spot_check_result: pass | fail | unresolved
finding_id_if_failed:
```

Minimum mandatory triggers:

- immediate rejection gate pass/fail,
- `?` on a high-weight criterion,
- `ABSENT_EVIDENCE` converted into a number,
- `CONTRADICTED_EVIDENCE`,
- `UNRESOLVED_CONFLICT`,
- criterion score `5` without direct support,
- responsiveness score above inheritance cap,
- arithmetic `needs_audit`,
- hidden recommendation flag,
- complete candidate with critical unknown,
- borderline normalized result,
- random candidate sample.

---

## 4. Gate Override Detection

Immediate rejection gates override totals.

Stage 5 must fail if:

```text
candidate has high normalized_total but a gate failed
candidate is described as acceptable while immediate_reject is true
candidate classification ignores a gate failure
candidate has gate score ? but is treated as primary-ready
```

Required audit line:

```text
gate_override_check: pass | fail
failed_gate:
was_hidden_by_total: yes | no
```

A hidden gate failure is always `blocker`.

---

## 5. Scoring Calibration Case Awareness

Stage 5 must verify that Stage 4 behavior is compatible with the scoring examples in:

```text
examples/scoring/
```

Stage 5 does not copy those examples. It uses them as calibration anchors for:

- `CONTRADICTED_EVIDENCE`,
- `ABSENT_EVIDENCE` vs `CONTRADICTED_EVIDENCE`,
- arithmetic `needs_audit`,
- `N/A` denominator handling,
- gate override detection.

If the example bank is missing, Stage 5 may still audit, but it must output:

```text
calibration_suite_status: missing
severity: minor
repair: create or restore examples/scoring before treating this pipeline as production-grade
```

---

## 6. N/A Denominator Audit

For payload schema `ev4-score-evidence-payload@1.3.0`, Stage 5 must audit:

```text
criteria_with_na
excluded_weights
applicable_weight_total
applicable_raw_max
```

Rules:

- `N/A` is allowed only by the rubric.
- Overlay Containment can be `N/A` only when no overlay-like candidate exists in Stage 2 and Stage 3.
- `N/A` weight must be excluded from `applicable_weight_total`.
- `N/A` must not be treated as score `5`.
- `?` still prevents a final score even if another criterion is `N/A`.

---

## 7. Output Payload Upgrade

Stage 5 must emit:

```text
Score_Audit_Payload.schema_version = ev4-score-audit-payload@1.1.0
```

Required payload fields:

```text
schema_version
stage_5_version
accepted_input_payload_schema
rubric_version
overall_audit_status
candidate_audit_matrix
findings
arithmetic_verification_results
cross_candidate_consistency_results
spot_check_results
gate_override_results
na_denominator_results
calibration_suite_status
stage_6_allowed
repair_route
```

---

## Pass / Fail Rules

Stage 5 may return `pass` only if:

- all required inputs exist,
- payload schema is compatible,
- no blocker exists,
- arithmetic is verified or not decision-relevant,
- gate failures are not hidden by totals,
- cross-candidate consistency has no major unresolved defect,
- required spot-check triggers are resolved,
- `N/A` denominator handling is correct when used.

Stage 5 may return `pass_with_minor_flags` only if all flags are non-blocking and do not affect candidate classification or Stage 6 eligibility.

Any blocker prevents Stage 6.

---

*This patch is part of the fixed Elementor V4 Architect Prompt Pack.*