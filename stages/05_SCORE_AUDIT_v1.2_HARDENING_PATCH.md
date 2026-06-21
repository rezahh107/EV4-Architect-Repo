# Stage 5 v1.2 Hardening Patch — Audit Self-Check and Tie Handoff

Status: active_patch_for_stage_5  
Patch version: 1.2.0  
Applies to: `stages/05_SCORE_AUDIT.md`  
Supersedes: `stages/05_SCORE_AUDIT_v1.1_HARDENING_PATCH.md` where stricter  
Input payload schemas: `ev4-score-evidence-payload@1.2.0`, `ev4-score-evidence-payload@1.3.0`  
Output payload schema: `ev4-score-audit-payload@1.2.0`

---

## Purpose

Stage 5 audits Stage 4. However, Stage 5 itself can accidentally leak recommendation language or imply a preferred candidate through the way it reports findings.

This patch makes Stage 5 self-auditing and prepares a neutral handoff for Stage 6 when candidates are close.

Core addition:

```text
Stage 5 must audit its own audit report before allowing Stage 6.
```

---

## 1. Stage 5 Self-Audit Requirement

After producing the `SCORE AUDIT REPORT`, Stage 5 must run a self-audit over its own output.

The self-audit must check:

```text
- hidden recommendation leakage inside Stage 5 report
- candidate preference implied by prose
- non-neutral ordering language
- subjective candidate adjectives
- accidental ranking by wording
- missing tie/ambiguity signal when scores are close
- payload schema completeness
```

Stage 5 must output:

```text
Stage_5_Self_Audit:
  hidden_recommendation_scan: pass | fail
  banned_terms_found:
    - term:
      location:
      severity: blocker | major | minor
  subjective_terms_found:
    - term:
      location:
      severity: minor | major
  candidate_preference_leakage: pass | fail
  neutral_reporting_check: pass | fail
  tie_handoff_check: pass | fail | not_applicable
  self_audit_status: pass | fail
```

If `self_audit_status: fail`, Stage 5 must repair its own report language and rerun the self-audit before returning the final Stage 5 result.

---

## 2. Stage 5 Hidden Recommendation Ban

Stage 5 inherits the Hidden Recommendation Ban from Stage 4.

Stage 5 must not use language that recommends, ranks, favors, dismisses, or implicitly selects a candidate.

### Direct Recommendation Terms — Auto-Fail

Use of these terms about a candidate before `/recommend` is a blocker unless the terms are quoted as forbidden examples:

```text
best
winner
recommended
preferred
optimal
best overall
clearly superior
strongest option
safest option
cleanest candidate
primary candidate
بهترین
برنده
پیشنهادی
گزینه اصلی
برتر
امن‌ترین
بهینه‌ترین
تمیزترین گزینه
قوی‌ترین گزینه
```

### Subjective Terms — Flag, Then Classify

These terms are not automatic blockers, but Stage 5 must flag them and decide whether they bias candidate selection:

```text
elegant
clean
simple
strong
beautifully
obviously
safe-looking
low-risk-looking
تمیز
قوی
ساده
زیبا
بدیهی
واضحاً
کم‌ریسک به نظر می‌رسد
```

Rules:

```text
Default: non-mechanical language → flag, not auto-fail.
Auto-fail: wording that directly recommends, ranks, or dismisses a candidate.
```

Preferred mechanical vocabulary:

```text
maps_to
violates
requires
depends_on
conflicts_with
preserves
omits
contradicts
is_unsupported_by
is_absent_from
is_inconsistent_with
triggers
blocks
```

---

## 3. Neutral Candidate Reporting Rule

Stage 5 must report candidates neutrally.

Allowed:

```text
A01: audit_status=pass, blockers=0, majors=0, minors=0
A02: audit_status=pass_with_minor_flags, blockers=0, majors=0, minors=1
```

Forbidden:

```text
A01 is the clean pass.
A01 is the safest audited option.
Only A01 is free of issues.
A02 and A03 are weaker.
A01 should proceed.
```

Stage 5 may state factual audit counts, but must not convert them into preference language.

Required line in every successful Stage 5 report:

```text
candidate_selection_not_performed: true
candidate_ranking_not_performed: true
```

---

## 4. Selection Ambiguity and Tie Handoff Protocol

Stage 5 must not break ties. Tie-breaking belongs to Stage 6 `/recommend`.

However, Stage 5 must detect when Stage 6 will need a tie-breaking protocol.

### Trigger Conditions

Set `selection_ambiguity_flag: true` when two or more candidates meet all of the following:

```text
- audit_status is pass or pass_with_minor_flags
- no blocker findings
- no unresolved major finding affecting candidate classification
- candidate classification allows Stage 6 consideration
- normalized totals are close OR final totals are incomplete but provisional_known_percent is close
```

Close means:

```text
absolute difference <= 3 normalized percentage points
```

If totals are incomplete, use:

```text
absolute difference <= 3 provisional_known_percent points
```

But provisional values must remain non-final.

### Required Neutral Payload

When `selection_ambiguity_flag: true`, Stage 5 must emit:

```text
Tie_Handoff_Payload:
  schema_version: ev4-tie-handoff@1.0.0
  tie_break_owner: /recommend
  stage_5_breaks_tie: false
  candidate_ids:
    - ...
  closeness_basis: normalized_total | provisional_known_percent | same_decision_band | incomplete_scores
  score_delta:
  shared_decision_band: yes | no | unknown
  high_weight_criteria_delta_summary:
    Elementor-Native Feasibility:
    Normal-Flow Safety:
    Responsiveness:
  unresolved_unknowns_summary:
    - ...
  minor_flags_summary:
    - candidate_id:
      minor_count:
      material_to_selection: yes | no | unknown
  required_stage_6_tie_break_inputs:
    - high-weight criteria comparison
    - unresolved unknown risk comparison
    - project constraint fit
    - editability and normal-flow priority
    - user-approved tradeoff preference, if needed
```

Stage 5 must not say which tied candidate should win.

---

## 5. Repair Routing Addition for Tie and Self-Audit Cases

Add these routes to Stage 5 repair routing:

| Case | Route |
|---|---|
| Stage 5 report contains hidden recommendation leakage | repair Stage 5 wording and rerun Stage 5 self-audit |
| Stage 5 implies candidate preference without Stage 6 | repair Stage 5 neutral reporting |
| Two or more candidates are close and pass audit | emit `Tie_Handoff_Payload`; proceed to `/recommend` only if no blocker exists |
| Close candidates have unresolved major scoring defects | repair `/score-evidence`, then rerun `/score-audit` |
| Close candidates differ mainly by unknowns | Stage 6 may request user clarification or choose lower-unknown path; Stage 5 must not decide |

---

## 6. Responsive Inheritance Reference Binding

Stage 5 must verify responsive caps against the authoritative Stage 4 rule, not from prose memory.

Authoritative references:

```text
- stages/04_SCORE_EVIDENCE.md
- stages/04_SCORE_EVIDENCE_v1.3_HARDENING_PATCH.md
- rubric version declared by Stage 4 payload
```

Stage 5 must verify:

```text
responsiveness_cap_reference_checked: true | false
responsive_cap_source:
responsive_cap_application: pass | fail | unresolved
```

If Stage 4 assigned a Responsiveness score above the declared cap, Stage 5 must produce a finding.

Severity:

```text
cap violation that affects candidate classification → blocker
cap violation that affects only minor wording → major
cap source missing or stale → major
```

---

## 7. Output Payload Upgrade

Stage 5 must emit:

```text
Score_Audit_Payload.schema_version = ev4-score-audit-payload@1.2.0
```

Required additional fields:

```text
stage_5_self_audit
candidate_selection_not_performed
candidate_ranking_not_performed
selection_ambiguity_flag
tie_handoff_payload_if_needed
responsive_cap_reference_checked
responsive_cap_application_results
stage_6_allowed
stage_6_conditions
```

`stage_6_conditions` must include:

```text
- only audited candidates may be considered
- candidates with blocker findings are excluded
- candidates with unresolved major findings are excluded unless user explicitly accepts the risk
- if selection_ambiguity_flag is true, Stage 6 must run tie-break protocol
- Stage 6 must not treat pass_with_minor_flags as a recommendation ranking
```

---

## 8. Pass / Fail Rule Updates

Stage 5 may return `pass` only if:

```text
- Stage 5 self-audit passes
- no hidden recommendation leakage exists in the audit report
- candidate reporting is neutral
- tie handoff is emitted when needed
- responsive cap source is checked when Responsiveness is audited
- no blocker exists
```

Stage 5 may return `pass_with_minor_flags` only if:

```text
- all flags are non-blocking
- no flag implies a candidate preference
- selection ambiguity is explicitly handed off to Stage 6 when present
```

Any Stage 5 hidden recommendation blocker prevents Stage 6 until repaired.

---

*This patch is part of the fixed Elementor V4 Architect Prompt Pack.*