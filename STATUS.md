# STATUS — Elementor V4 Architect Prompt Pack

Version: 0.5.0
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
| /research | draft | Documentation source policy remains useful |
| /decompose | confirmed_with_example_bank | Controlled Visual Role Decomposition with 12 examples |
| /decomposition-example-bank | active_enhanced | Synthetic pattern-based examples plus authoring standard |
| /architectures | confirmed_hardened_v1.1.0 | Coverage matrix, unknown propagation, recommendation ban, dynamic guardrails, tradeoff requirements |
| /score-evidence | confirmed_hardened_v1.2.0 | Evidence-bound scoring spine with arithmetic policy, evidence labels, unknown discipline, inheritance caps, payload handoff |
| /score-audit | confirmed_v1.0.0 | Independent audit of Stage 4 scoring quality before recommendation |
| /recommend | current_next | Depends on Stage 5 pass or pass_with_minor_flags |
| /build-tree | not_started | Needs naming convention |
| /implementation | not_started | Needs Elementor settings schema |
| /final-audit | not_started | Needs checklist |

## Confirmed Project Defaults

- Elementor V4
- Elementor Pro available
- Container/Flexbox-first workflow
- Structure Panel clarity matters
- Scoped Custom CSS allowed
- SVG Widget allowed
- HTML Widget allowed when practical
- No third-party plugin/add-on unless approved by the user
- Meaningful content should remain editable when practical
- Do not convert meaningful content into a single static image
- Primary content should remain in normal flow
- Absolute positioning only inside a clearly named relative Stage
- Decorative connector lines may use SVG and may be hidden or simplified on mobile
- Prefer one DOM across desktop, tablet, and mobile
- Avoid duplicate mobile-only sections unless strongly justified
- Use reusable classes and variables for repeated visual patterns
- Do not create global classes for one-off coordinates
- Meaningful text must remain real text
- Images must be classified as meaningful or decorative
- DOM reading order should remain logical
- Avoid heavy full-image sections and excessive wrappers
- Optimize large visual assets
- Reports and reasoning must be in Persian

## Stage 2 Summary

/decompose converts a screenshot, reference image, or section description into a role-based visual inventory. It classifies visible groups, meaningful content, repeated component candidates, visual core, decoration layers, overlay or connector candidates, responsive risks, unknowns, and forbidden implementation assumptions. It must not recommend architecture, score options, produce an Elementor tree, infer actual DOM, or choose widgets/plugins.

The decomposition example bank lives in examples/decomposition/ and currently contains 12 synthetic pattern-based examples plus an authoring standard.

## Stage 3 Summary

/architectures enumerates multiple Elementor V4 architecture candidates from the completed Stage 2 decomposition. It must not score, rank, recommend, produce a final Elementor tree, or write implementation code.

Stage 3 v1.1.0 requires: Architecture Coverage Matrix, Unknown Propagation Ledger, Hidden Recommendation Ban, Dynamic/Loop Guardrail, Widget-State Guardrail, Scoped CSS Guardrail, and Tradeoff Requirement.

## Stage 4 Summary

/score-evidence evaluates Stage 3 candidates using rubrics/ELEMENTOR_V4_ARCHITECTURE_RUBRIC_v1.md.

Rubric version: 1.2
Raw weighted max: 125
Normalized total formula: normalized_total = (raw_weighted_total / 125) * 100

Immediate rejection gates:
- Elementor-Native Feasibility < 3
- Normal-Flow Safety < 2
- Responsiveness < 2

Stage 4 v1.2.0 requires: tool-first arithmetic policy, provisional known-score formula, closed evidence-label set, absent-vs-contradicted separation, Elementor Responsive Inheritance Rule, Hidden Recommendation Scan, Evidence Map Requirement, Unknown-to-Score Ceiling, Shared Unknown Consistency Rule, Candidate Classification, Fairness and Consistency Check, schema-versioned Audit_Trail_Payload, and Stage 5 Spot-Check Authority.

## Stage 5 Summary

/score-audit independently audits Stage 4 scoring quality. It does not choose a winner, rank candidates, or repair scores silently.

File: stages/05_SCORE_AUDIT.md
Status: confirmed_v1.0.0
Input payload schema: ev4-score-evidence-payload@1.2.0
Output payload schema: ev4-score-audit-payload@1.0.0

Stage 5 controls:
- Required Inputs Gate
- Payload Schema Gate
- Mandatory spot-check triggers
- Severity levels: blocker, major, minor, note
- Rubric Fidelity Audit
- Evidence Label Audit
- Unknown Discipline Audit
- Arithmetic Audit
- Immediate Rejection Gate Audit
- Elementor Responsive Inheritance Audit
- Hidden Recommendation Audit
- Fairness and Consistency Audit
- Candidate Classification Audit
- Audit Trail Payload Audit
- Precise Repair Routing

Stage 6 is allowed only if Stage 5 returns pass or pass_with_minor_flags.

## Current Next Step

Define Stage 6 — /recommend.

Goal: choose a recommended architecture only from audited Stage 4 outputs that passed Stage 5. The recommendation must be evidence-bound and must preserve the audit trail into later implementation stages.
