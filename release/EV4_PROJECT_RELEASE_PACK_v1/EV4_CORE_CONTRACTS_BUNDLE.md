# EV4 Core Contracts Bundle

Status: release_candidate_quality_first_runtime  
Version: 1.3.0

## 1. Runtime Alignment

The active runtime alignment is:

```text
contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md
```

It supersedes only authorization-driven continuation clauses in older contracts and mirrors. All non-conflicting quality controls remain active.

## 2. Stage Result Contract

Schema:

```text
ev4-architect-stage-result@1.0.0
```

Canonical continuation authority:

```text
scripts/architect_quality_runtime.py#evaluate_stage
```

```text
Stage Output + Run State + finite Stage rules
→ evaluator-derived Stage Result
→ exact Manifest successor, minimum blocking input, or repair route
```

A serialized Stage Result is readable but non-authorizing until recomputed from the corresponding Stage Output and Run State.

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

Historical Anchor versions remain readable evidence and are never silently upgraded.

## 4. Validation Bundle and Carrier Tooling

Current optional audit-carrier identities remain:

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

## 5. Research Contract

`/research` remains mandatory, but external lookup is conditional.

Valid passing dispositions include:

```text
active_lookup_completed
existing_evidence_sufficient
no_platform_question
```

`blocked_by_missing_required_source` blocks only when a downstream decision genuinely requires unobtainable evidence.

No URL, citation, retrieval receipt, or external lookup is required for a truthful `no_platform_question` result.

## 6. Partial Rerun Contract

Schema:

```text
ev4-partial-rerun@1.0.0
```

Core rule:

```text
Rerun from the earliest Stage whose owned information changed.
Never reuse downstream results that depend on invalidated upstream work.
```

Preserve unaffected Run State, reactivate unknowns whose resolutions depended on invalidated work, and invalidate the candidate lock only when the rerun reaches `/recommend` or earlier.

Anchor or Bundle authorization is not required.

## 7. Unknown Lifecycle

Active unknowns live in the small Run State and cannot disappear through omission.

Ordinary resolution requires an explicit resolution type and explanatory note. Resolvable evidence is mandatory only for downstream-critical or Artifact-dependent unknowns.

Do not add a general evidence graph, immutable unknown receipt, or chained hash system.

## 8. Canonical Content and Fidelity

For `/build-tree` and `/implementation`, the existing structured Stage Output is the canonical content. Do not create wrapper Artifacts merely to compute digests.

```text
no real canonical content
→ no claimed digest
```

The evaluator computes Build Tree and Implementation digests from actual content and rejects fabricated strings, `null == null`, candidate drift, and approved-tree mismatch.

Conversational Stage output does not require cryptographic identity.

## 9. Source Access Contract

```text
/decompose uses visible screenshot/user evidence only.
/research owns platform capability evidence and source freshness.
TUYA is an internal conceptual reference only.
RAG may ground platform capability claims.
RAG/TUYA must not infer screenshot content, boost scores, break ties, or soften audit findings.
```

Older source-access clauses requiring Anchor, Bundle, independent regeneration, or profile completeness before ordinary source use are superseded.

## 10. Quality Invariants

```text
mandatory 12-Stage order
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
fail-closed /project-gate-export
legacy-output non-substitution
```

## 11. Final Project Gate Boundary

The terminal Stage is:

```text
/project-gate-export
```

Its pass result is derived only from:

```text
actual canonical Architect Stage Payload
→ existing Schema and semantic validation
→ selected-candidate consistency
→ existing Producer Gate exporter
→ actual canonical export
→ contract and digest verification
```

Caller-controlled success Booleans are informational only. Invalid payloads, identity drift, digest/provenance failure, blocking unknowns, and legacy output substitution remain fail-closed.

## 12. Debug Trace Contract

Debug remains external and auditable, not private chain-of-thought. It may report inputs, decisions, evidence use, unknowns, applied rules, failure symptoms, and repair routes without becoming a continuation receipt system.

## 13. Release Boundary

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
