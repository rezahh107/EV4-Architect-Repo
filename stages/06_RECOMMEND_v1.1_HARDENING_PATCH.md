# Stage 6 — /recommend v1.1 Hardening Patch

Status: active_patch
Patch version: 1.1.0
Applies to: stages/06_RECOMMEND.md v1.0.0
Output payload schema: ev4-recommend-payload@1.1.0

## Purpose

This patch hardens Stage 6 against premature selection, hidden ranking, weak tie handling, and untraceable recommendation reasoning.

Stage 6 remains the first stage allowed to recommend an architecture, but it must now recommend through a bounded, audit-driven, provenance-backed decision protocol.

## Core Rule

Recommend from audited evidence only.

Stage 6 must not invent new evidence, reinterpret Stage 2, re-score Stage 4, or relax Stage 5 findings. It may only select from the audit-eligible candidate set produced by Stage 5.

## Critic Findings Addressed

This patch addresses these weaknesses in Stage 6 v1.0:

1. A selected candidate could be implicitly over-highlighted by prose.
2. Conditional alternatives could be framed as inferior instead of conditionally valid.
3. Tie-break logic existed but did not require a strict provenance ledger.
4. The recommendation payload did not expose enough debug information.
5. Build-tree handoff could be allowed before required confirmations were resolved.
6. Stage 6 self-audit did not explicitly detect recommendation leakage created by the recommendation report itself.

## Mandatory Recommendation Basis Matrix

Before selecting a primary candidate, Stage 6 must produce a neutral matrix for every audit-eligible candidate.

Required columns:

| Candidate | Audit status | Gate status | Score status | Normalized score | Provisional score | x4 criteria summary | Blockers | Major flags | Minor flags | Unresolved unknowns | Required confirmations | Eligible? |
|---|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|

Rules:

- The matrix must list all eligible and near-eligible candidates.
- Candidate order must follow Stage 3 candidate ID order unless Stage 5 supplied a neutral audited ordering.
- The matrix must not use subjective labels such as `clean`, `strong`, `safe`, `best`, `ضعیف`, `قوی`, `تمیز`, or `بهترین`.
- The matrix is not a ranking table. It is a decision evidence table.

## Recommendation Provenance Ledger

Every reason used to recommend a candidate must have a provenance entry.

Required format:

```text
RECOMMENDATION PROVENANCE LEDGER

Reason ID:
Candidate:
Claim:
Source:
- Stage 4 criterion:
- Stage 4 evidence label:
- Stage 5 audit finding ID:
- Stage 5 audit status:
- Related unknowns:
Decision effect:
- included_in_primary_reason: yes/no
- carried_forward_to_build_tree: yes/no
```

Rules:

- No recommendation reason may appear in prose unless it appears in the ledger.
- If a reason has no Stage 4/Stage 5 provenance, it must be removed.
- Visual preference alone cannot appear as a decision effect.
- `pass_with_minor_flags` must be carried forward; it cannot be converted into a clean pass.

## Strict Tie and Near-Tie Handling

Stage 6 must treat a decision as ambiguous when any of the following is true:

- Stage 5 emits `selection_ambiguity_flag: true`.
- Two or more eligible candidates are within `<= 3 normalized percentage points`.
- Final totals are incomplete and candidates are within `<= 3 provisional_known_percent points`.
- One candidate leads in total score but loses on one or more x4 criteria.
- One candidate has fewer unknowns but another has stronger normal-flow or responsiveness evidence.
- Stage 5 emits a `Tie_Handoff_Payload`.

### Tie Resolution Rule

Stage 6 may resolve a tie only if one candidate has an audited, provenance-backed advantage in this order:

1. Fewer blockers.
2. Fewer major audit findings.
3. Strictly better x4 criteria profile.
4. Fewer unresolved critical unknowns.
5. Lower normal-flow risk.
6. Lower responsive collision risk.
7. Fewer required confirmations before build-tree.

If no strict advantage exists, Stage 6 must output:

```text
recommendation_status: decision_requires_user_input
```

It must ask exactly one minimal architecture-changing question.

## Conditional Alternatives Rule

Conditional alternatives are not consolation prizes and must not be described as weaker unless Stage 5 explicitly supports that classification.

Each alternative must be written as:

```text
Choose [Candidate] instead only if [specific condition] is true.
Required confirmation: [confirmation]
Risk carried forward: [risk]
```

Forbidden alternative language:

- weaker
- worse
- less ideal
- inferior
- backup only
- ضعیف‌تر
- بدتر
- گزینه فرعی بی‌ارزش

Unless the wording is directly quoting a finding from Stage 5, these terms trigger self-audit failure.

## Build-Tree Readiness Gate

Stage 6 must not hand off to `/build-tree` unless all of the following are true:

- `recommendation_status: recommended`
- exactly one primary candidate is selected
- no blocker flags remain
- no required user confirmation remains unresolved
- no `decision_requires_user_input` status remains
- Stage 5 authorization is `pass` or `pass_with_minor_flags`
- all carried-forward flags are visible in the handoff
- naming convention requirement is acknowledged

If any condition fails:

```text
allowed_next_stage: blocked
build_tree_blockers: [explicit blockers]
```

## Stage 6 Hidden Recommendation Self-Audit

Stage 6 must audit its own output for hidden recommendation leakage.

Self-audit checklist:

```text
recommendation_self_audit:
  selected_candidate_only_named_in_allowed_sections: pass/fail
  no_subjective_candidate_comparison_outside_recommendation: pass/fail
  no_banned_terms_outside_allowed_quote_context: pass/fail
  conditional_alternatives_are_condition_based: pass/fail
  tie_not_forced_without_strict_advantage: pass/fail/not_applicable
  recommendation_reasons_all_have_provenance: pass/fail
  build_tree_handoff_gate_checked: pass/fail
```

If any self-audit item fails, Stage 6 must repair its own report before handoff.

## Recommendation Debug Record

Stage 6 must emit a compact debug record. This is not private chain-of-thought. It is an external decision trace.

Required object:

```json
{
  "schema": "ev4-recommend-debug-record@1.0.0",
  "stage": "recommend",
  "input_payloads": {
    "score_audit_payload_schema": null,
    "score_evidence_payload_schema": null
  },
  "candidate_pool": [],
  "excluded_candidates": [],
  "selection_checks": [],
  "tie_checks": [],
  "provenance_reason_ids": [],
  "carried_forward_flags": [],
  "blocked_handoff_reasons": [],
  "minimal_user_question": null
}
```

Rules:

- This debug record must be safe to show to the user.
- It must explain which external evidence and rules drove the decision.
- It must not claim to reveal hidden model reasoning.
- It must be usable by a later debug agent to locate the failed stage.

## Updated Recommendation Payload Schema

Stage 6 now emits:

```json
{
  "schema": "ev4-recommend-payload@1.1.0",
  "recommendation_status": "recommended | decision_requires_user_input | blocked_missing_input | blocked_by_stage_5_failure | blocked_by_build_tree_readiness",
  "stage_5_schema_used": "ev4-score-audit-payload@1.2.0",
  "primary_candidate_id": null,
  "primary_architecture_family": null,
  "eligible_candidates": [],
  "non_eligible_candidates": [],
  "near_tie_candidates": [],
  "tie_detected": false,
  "tie_break_protocol_applied": false,
  "selection_ambiguity_flag": false,
  "recommendation_basis_matrix_present": false,
  "provenance_ledger_present": false,
  "carried_forward_flags": [],
  "required_user_confirmations": [],
  "required_verifications_before_build_tree": [],
  "allowed_next_stage": null,
  "build_tree_blockers": [],
  "debug_record_schema": "ev4-recommend-debug-record@1.0.0"
}
```

## Patch Pass Criteria

Stage 6 v1.1 passes only if:

- it lists the neutral Recommendation Basis Matrix;
- every recommendation reason appears in the Recommendation Provenance Ledger;
- it applies strict tie handling;
- it does not imply preference through prose outside allowed sections;
- it carries forward all Stage 5 flags;
- it blocks build-tree when confirmations or blockers remain;
- it emits `ev4-recommend-payload@1.1.0`;
- it emits `ev4-recommend-debug-record@1.0.0`.

## Allowed Next Stage

If pass and build-tree readiness gate passes:

```text
/build-tree
```

If blocked:

```text
return to the relevant repair route or ask the minimal user confirmation question
```
