# EV4 Core Contracts Bundle

Status: release_candidate_quality_first_runtime  
Version: 1.2.0

## 1. Runtime Alignment

The active runtime alignment is:

```text
contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md
```

It supersedes only authorization-driven continuation clauses in older contracts and mirrors. All stricter non-conflicting quality controls remain active.

## 2. Stage Result Contract

Schema:

```text
ev4-architect-stage-result@1.0.0
```

Purpose: govern ordinary internal continuation through Stage-specific quality criteria.

```text
pass → exact Manifest successor
needs_input → minimum blocking question
blocked → evidence-based repair route
```

This is the active user-facing continuation carrier.

## 3. Stage Anchor Contract

Current Schema:

```text
ev4-stage-anchor@1.4.0
```

```yaml
active_runtime_role: optional_resume_checkpoint
authorization_role: none
required_for_internal_continuation: false
```

Anchors preserve user-facing facts, unknowns, flags, gates, and repair history for optional audit or resume diagnostics. They are not required for ordinary Stage movement.

Historical Anchor versions remain readable evidence and are never silently upgraded.

## 4. Validation Bundle and Carrier Tooling

Current deterministic audit carrier identities remain:

```yaml
artifact_schema: ev4-architect-pipeline-stage-artifact@1.1.0
receipt_schema: ev4-architect-stage-validation-receipt@1.1.0
failure_event_schema: ev4-architect-validation-failure-event@1.0.0
boundary_schema: ev4-stage-boundary-record@1.1.0
anchor_schema: ev4-stage-anchor@1.4.0
bundle_schema: ev4-architect-validation-bundle@1.2.0
```

Optional roles:

```text
repository audit tool
compatibility evidence
deterministic validator regression
historical carrier readability
```

These carriers do not authorize normal internal continuation. Missing Bundle evidence, missing independent regeneration, or an incomplete Validation Profile does not block an ordinary project Run.

`authorization_valid` is retained only for optional/historical transaction compatibility.

## 5. Partial Rerun Contract

Schema:

```text
ev4-partial-rerun@1.0.0
```

Core rule:

```text
Rerun from the earliest Stage whose owned information changed.
Never reuse downstream outputs that depend on stale upstream facts.
```

Use the latest valid Stage output and Stage Result. Optional Anchors/Bundles may provide audit context but are not required.

## 6. Debug Trace Contract

Schema:

```text
ev4-debug-trace@1.0.0
```

Debug must be external and auditable, not private chain-of-thought.

Required trace components remain:

```text
input_digest
decision_log
evidence_map
unknown_register
rule_application_log
failure_symptom_index
repair_route
handoff_payload_schema
```

## 7. Source Access Contract

```text
/decompose uses visible screenshot/user evidence only.
/research owns platform capability evidence and source freshness.
TUYA is an internal conceptual reference only.
RAG may ground platform capability claims.
RAG/TUYA must not infer screenshot content, boost scores, break ties, or soften audit findings.
```

Older source-access clauses requiring Anchor, Bundle, independent regeneration, or profile completeness before ordinary source use are superseded.

## 8. Quality Invariants

```text
mandatory Stage order
mandatory /research disposition
observation/inference separation
unknown preservation
architecture coverage
evidence-backed scoring
Score Audit before recommendation
selected candidate lock
build-tree fidelity
implementation fidelity
Final Audit
fail-closed Project Gate export
legacy-output non-substitution
```

## 9. Final Project Gate Boundary

The final Architect → Project Gate handoff remains strongly validated through the canonical Architect Stage Payload and Producer Gate Export contracts.

Invalid payloads, identity drift, digest/provenance failure, blocker/high final-audit findings, and legacy output substitution remain fail-closed.

## 10. Release Boundary

```text
Controlled architecture analysis: allowed.
Quality-first internal continuation: implemented in repository contracts and deterministic tests.
Live chat-runtime enforcement: insufficient_evidence.
Production-grade Elementor implementation claim: not allowed.
```

Still outside the current evidence boundary:

```text
live Elementor rendering
real Elementor export JSON / EDIS validation
browser/device QA
exact pixel matching
downstream acceptance of a real non-synthetic Run
production readiness
```
