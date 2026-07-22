# Stage 6 — /recommend: Audited Architecture Recommendation

Status: confirmed_v1.0.0
Version: 1.0.0
Payload schema: ev4-recommend-payload@1.0.0
Active Manifest version: 1.1.0 via `stages/06_RECOMMEND_v1.1_HARDENING_PATCH.md`
Validation Profile: `blocked_missing_semantics`
Continuation authorization: blocked until the active payload has a canonical JSON Schema, registered semantic handler, deterministic repair ownership, and independent Bundle regeneration.

## Purpose

`/recommend` is the first pipeline stage allowed to select an architecture.

It converts the audited scoring output from Stage 4 and Stage 5 into one bounded recommendation, without inventing new evidence, re-scoring candidates, or bypassing audit findings.

## Core Contract

Recommend only after audit.

Stage 6 must not operate from Stage 3 candidates alone and must not trust Stage 4 scoring unless Stage 5 has approved the scoring process.

## Required Inputs Gate

Stage 6 may run only if all required inputs are present:

- Stage 2 `/decompose` output
- Stage 3 `/architectures` output
- Stage 4 `/score-evidence` output
- Stage 4 `Audit_Trail_Payload`
- Stage 5 `/score-audit` output
- Stage 5 `Score_Audit_Payload`
- Active rubric version
- Project defaults

If any required input is missing, Stage 6 must stop with:

```text
recommendation_status: blocked_missing_input
```

## Stage 5 Authorization Gate

Stage 6 may proceed only when Stage 5 returns one of:

- `pass`
- `pass_with_minor_flags`

Stage 6 must stop when Stage 5 returns any of:

- `fail_requires_score_repair`
- `fail_requires_stage_3_repair`
- `fail_missing_input`
- `fail_schema_mismatch`
- `fail_requires_audit_report_repair`
- `fail_requires_tie_payload_repair`

If Stage 5 fails, Stage 6 must not recommend and must output the repair route from Stage 5.

## Candidate Eligibility Rules

A candidate is eligible for recommendation only if:

- it passed immediate rejection gates
- Stage 5 did not mark it as blocker-failed
- Stage 5 did not require score repair for it
- it is not classified as rejected, toxic, or approval-blocked
- it does not depend on unapproved third-party plugins
- it has enough audited evidence to be compared against other eligible candidates

Candidates with `pass_with_minor_flags` may remain eligible, but Stage 6 must carry the flags forward into the recommendation.

## What Stage 6 Is Allowed To Do

Stage 6 may:

- select one primary recommended architecture
- name one or more conditional alternatives
- explain why the selected architecture survives the audited criteria
- identify remaining verification tasks before `/build-tree`
- handle close-score ties using the tie protocol
- produce a structured `Recommendation_Payload`

## What Stage 6 Must Not Do

Stage 6 must not:

- recompute Stage 4 scores
- override Stage 5 audit findings
- ignore failed gates because of a high normalized score
- invent missing evidence
- turn `?` into a number
- select a candidate with unresolved blocker flags
- choose a third-party plugin option without user approval
- produce Elementor tree output
- produce implementation settings or CSS
- repair Stage 2, Stage 3, Stage 4, or Stage 5 inside the recommendation stage

## Decision Basis Hierarchy

When choosing among eligible candidates, Stage 6 must use this hierarchy:

1. Stage 5 audit status
2. Immediate rejection gate status
3. Blocker and major findings
4. Stage 4 normalized score when complete and audit-approved
5. Stage 4 provisional known percent only when final score is incomplete, clearly labeled as provisional
6. High-weight rubric criteria, especially:
   - Elementor-Native Feasibility
   - Normal-Flow Safety
   - Responsiveness
7. Number and severity of unresolved unknowns
8. Fit with project defaults
9. Tie-break protocol, if applicable

Stage 6 must never use visual preference alone as the deciding factor.

## Tie-Break Protocol

Stage 6 must run the tie-break protocol when Stage 5 emits:

```text
selection_ambiguity_flag: true
```

or when two or more eligible candidates are within:

```text
<= 3 normalized percentage points
```

or, if final scores are incomplete:

```text
<= 3 provisional_known_percent points
```

### Tie-Break Order

Use this order and stop only when the tie is resolved with evidence:

1. Fewer blocker or major audit findings
2. Better performance on ×4 criteria
3. Fewer unresolved Stage 2 unknowns carried into final recommendation
4. Safer normal-flow behavior
5. Lower responsive collision risk
6. Better editability of meaningful content
7. Lower dependency on custom CSS, HTML widget, or manual coordinate positioning
8. Better alignment with design-system defaults
9. Fewer required user confirmations before `/build-tree`

If the tie remains unresolved after these checks, Stage 6 must not force a winner. It must output:

```text
recommendation_status: decision_requires_user_input
```

and ask only the minimum architecture-changing question required to resolve the tie.

## Recommendation Language Rules

Stage 6 is allowed to use recommendation language only inside explicitly named recommendation sections:

- `Primary Recommendation`
- `Conditional Alternative`
- `Decision Requires User Input`

Outside those sections, it must keep neutral audit-style language.

Stage 6 may say:

- `recommended`
- `selected`
- `primary`

Stage 6 must not use exaggerated subjective language such as:

- best
- perfect
- obviously
- cleanest
- safest
- strongest
- elegant
- زیباترین
- قوی‌ترین
- بهترین
- واضحاً

unless quoting a banned term as part of self-audit.

## Required Output Format

```text
STAGE 6 — RECOMMENDATION

1. Input Authorization
- stage_5_status:
- stage_5_payload_schema:
- recommendation_allowed: yes/no
- blocked_reason, if any:

2. Eligible Candidate Set
| Candidate | Stage 5 status | Gate status | Score status | Major flags | Eligible? |

3. Decision Basis Summary
- score_basis:
- high_weight_criteria_basis:
- audit_basis:
- unresolved_unknowns_basis:

4. Tie-Break Check
- tie_detected: yes/no
- tie_source:
- tie_break_protocol_applied: yes/no
- tie_result:

5. Primary Recommendation
- candidate_id:
- architecture_family:
- recommendation_status:
- concise_reason:
- carried_forward_flags:
- required_verifications_before_build_tree:

6. Conditional Alternatives
| Candidate | When to choose instead | Required confirmation |

7. Non-Eligible Candidates
| Candidate | Reason not eligible |

8. Handoff To /build-tree
- allowed_next_stage: /build-tree or blocked
- required inputs for build-tree:
- naming convention needed: yes/no

9. Recommendation Self-Audit
- did_not_recompute_scores: pass/fail
- did_not_override_stage_5: pass/fail
- did_not_select_blocked_candidate: pass/fail
- tie_protocol_applied_if_needed: pass/fail/not_applicable
- subjective_language_scan: pass/fail
- output_payload_schema_present: pass/fail

10. Recommendation_Payload
```json
{
  "schema": "ev4-recommend-payload@1.0.0",
  "recommendation_status": "recommended | decision_requires_user_input | blocked_missing_input | blocked_by_stage_5_failure",
  "stage_5_schema_used": "ev4-score-audit-payload@1.2.0",
  "primary_candidate_id": null,
  "primary_architecture_family": null,
  "eligible_candidates": [],
  "non_eligible_candidates": [],
  "tie_detected": false,
  "tie_break_protocol_applied": false,
  "selection_ambiguity_flag": false,
  "carried_forward_flags": [],
  "required_user_confirmations": [],
  "required_verifications_before_build_tree": [],
  "allowed_next_stage": null,
  "build_tree_blockers": []
}
```
```

## Self-Audit Failure Rule

If Stage 6 self-audit fails, Stage 6 must repair its own recommendation report before handing off to `/build-tree`.

It must not proceed if:

- it selected a blocked candidate
- it ignored Stage 5 failure
- it forced a winner during unresolved tie
- it used non-neutral selection language outside the recommendation section
- it omitted the `Recommendation_Payload`

## Pass Criteria

Stage 6 passes only if:

- Stage 5 authorized recommendation
- every selected candidate is eligible
- no failed gate is overridden
- tie protocol is applied when required
- all carried-forward flags are visible
- remaining confirmations are explicit
- output includes `ev4-recommend-payload@1.0.0`
- `/build-tree` handoff is either allowed or explicitly blocked

## Allowed Next Stage

If pass:

```text
/build-tree
```

If blocked:

return to the repair route specified by Stage 5, Stage 4, Stage 3, or Stage 2.
