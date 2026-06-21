# STATUS — Elementor V4 Architect Prompt Pack

Version: 0.5.1
Status: in_progress
Last confirmed stage: Stage 5 — /score-audit
Current next stage: Stage 6 — /recommend
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
| /score-audit | confirmed_hardened_v1.1.0_patch | Uses Stage 5 v1.1 hardening patch |
| /scoring-calibration-bank | active | examples/scoring calibration cases added |
| /recommend | current_next | Depends on Stage 5 pass or pass_with_minor_flags |
| /build-tree | not_started_requires_naming | Needs naming convention |
| /implementation | not_started | Needs Elementor settings schema |
| /final-audit | not_started | Needs checklist |

## Active Hardening Files

- stages/04_SCORE_EVIDENCE_v1.3_HARDENING_PATCH.md
- stages/05_SCORE_AUDIT_v1.1_HARDENING_PATCH.md
- examples/scoring/README.md
- examples/scoring/SCORING-CAL-001-contradicted-evidence.md
- examples/scoring/SCORING-CAL-002-absent-vs-contradicted.md
- examples/scoring/SCORING-CAL-003-arithmetic-needs-audit.md
- examples/scoring/SCORING-CAL-004-overlay-na.md

## Current Next Step

Define Stage 6 — /recommend.
