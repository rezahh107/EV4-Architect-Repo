# STATUS — Elementor V4 Architect Prompt Pack

Version: 0.6.0
Status: in_progress
Last confirmed stage: Stage 6 — /recommend
Current next stage: Stage 7 — /build-tree
Language: Persian reports, English technical labels allowed

## Pipeline

1. /intake
2. /research
3. /decompose
4. /architectures
5. /score-evidence
6. /score-audit
7. /recommend
8. /build-tree
9. /implementation
10. /final-audit

## Stage Status

| Stage | Status | Notes |
|---|---|---|
| /intake | confirmed | Lightweight default-based intake |
| /research | draft_required | Needs source policy |
| /decompose | confirmed_with_example_bank | Controlled Visual Role Decomposition with 12 examples |
| /decomposition-example-bank | active_enhanced | Pattern-based examples plus authoring standard |
| /architectures | confirmed_hardened_v1.1.0 | Coverage matrix, unknown propagation, recommendation ban, dynamic guardrails |
| /score-evidence | confirmed_hardened_v1.3.0_patch | Uses rubric 1.3 and Stage 4 v1.3 hardening patch |
| /score-audit | confirmed_hardened_v1.2.0_patch | Adds Stage 5 self-audit, hidden recommendation guard, tie handoff, responsive cap reference binding |
| /scoring-calibration-bank | active | examples/scoring calibration cases added |
| /recommend | confirmed_v1.0.0 | Audited recommendation stage; may select only after Stage 5 pass/pass_with_minor_flags; emits ev4-recommend-payload@1.0.0 |
| /build-tree | current_next_requires_naming | Needs naming convention and Elementor Structure Panel naming contract |
| /implementation | not_started | Needs Elementor settings schema |
| /final-audit | not_started | Needs checklist |

## Active Hardening Files

- stages/04_SCORE_EVIDENCE_v1.3_HARDENING_PATCH.md
- stages/05_SCORE_AUDIT_v1.1_HARDENING_PATCH.md
- stages/05_SCORE_AUDIT_v1.2_HARDENING_PATCH.md
- stages/06_RECOMMEND.md
- examples/scoring/README.md
- examples/scoring/SCORING-CAL-001-contradicted-evidence.md
- examples/scoring/SCORING-CAL-002-absent-vs-contradicted.md
- examples/scoring/SCORING-CAL-003-arithmetic-needs-audit.md
- examples/scoring/SCORING-CAL-004-overlay-na.md

## Stage 5 v1.2 Notes

Stage 5 now has these additional constraints before Stage 6:

- It must audit its own audit report for hidden recommendation leakage.
- It must keep candidate reporting neutral and avoid implied preference.
- It must emit a tie handoff payload instead of breaking ties.
- It must bind responsive inheritance audits to the authoritative Stage 4/rubric rule.
- It must emit `ev4-score-audit-payload@1.2.0` when the v1.2 patch is active.

## Stage 6 v1.0 Notes

Stage 6 is the first stage allowed to recommend an architecture.

It may run only after Stage 5 returns `pass` or `pass_with_minor_flags`.

It must:

- select only from audit-eligible candidates;
- never override failed gates or Stage 5 findings;
- run the tie-break protocol when Stage 5 emits `selection_ambiguity_flag` or candidates are within the configured close-score threshold;
- carry forward unresolved flags and required confirmations;
- emit `ev4-recommend-payload@1.0.0`;
- hand off to `/build-tree` only when recommendation is authorized and no blockers remain.

## Current Next Step

Define Stage 7 — /build-tree, including naming convention and Elementor Structure Panel tree contract.
