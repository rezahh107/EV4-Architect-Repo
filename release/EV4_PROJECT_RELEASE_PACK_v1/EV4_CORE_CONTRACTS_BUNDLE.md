# EV4 Core Contracts Bundle

Status: release_candidate_for_controlled_use
Version: 1.0.0

---

## 1. Stage Anchor Contract

Schema:

```text
ev4-stage-anchor@1.1.0
```

Purpose: keep critical facts, unknowns, flags, gates, and repair routes at the front of each stage to reduce context drift.

Required fields:

```text
source_stage
target_stage
target_stage_hardening_status
project_status_version
payload_schema_in
payload_schema_out
critical_unknowns
confidence_delta
blocking_items
gate_results
audit_flags
required_user_confirmations
partial_rerun_state
allowed_work
forbidden_work
stop_conditions
debug_trace_required
```

Stop if anchor is missing, stale, contradicted, or schema-mismatched.

---

## 2. Partial Rerun Contract

Schema:

```text
ev4-partial-rerun@1.0.0
```

Core rule:

```text
Rerun from the earliest stage whose owned information changed.
Never reuse downstream payloads that depend on stale upstream facts.
```

Examples:

```text
Screenshot changed → rerun from /decompose.
Platform capability changed → rerun from /research or /architectures depending on impact.
Rubric changed → rerun from /score-evidence.
Selected candidate changed → rerun from /recommend or /build-tree.
Naming-only issue → rerun from /build-tree.
Implementation setting issue → rerun from /implementation.
```

---

## 3. Debug Trace Contract

Schema:

```text
ev4-debug-trace@1.0.0
```

Debug must be external and auditable, not private chain-of-thought.

Required trace components:

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

---

## 4. Source Access Contract

Rules:

```text
/decompose must only use visible screenshot/user evidence.
/research owns source pinning and platform capability facts.
TUYA is internal conceptual reference only.
RAG may ground platform capability claims.
RAG/TUYA must not infer screenshot content, boost scores, break ties, or soften audit findings.
```

---

## 5. TUYA Concept Reference Contract

Schema:

```text
ev4-tuya-concept-reference@1.0.0
```

TUYA may guide:

```text
Context → Structure → Flow/Display → Size/Units → Position/Layering → Responsive → Design System → DOM/Audit
```

TUYA must not prove platform capability or override official docs/export evidence.

Confidence lifecycle:

```text
confirmed → SUPPORTED_EVIDENCE
provisional → PARTIALLY_SUPPORTED_EVIDENCE unless upgraded or contradicted
unknown → ABSENT_EVIDENCE unless later contradicted
provisional + direct conflicting evidence → CONTRADICTED_EVIDENCE
```

---

## 6. Release Boundary

Current pack status:

```text
Controlled real screenshot use: allowed.
Production-grade implementation claim: not allowed.
```

Still future work:

```text
live Elementor rendering
real Elementor export JSON / EDIS validation
browser/device QA
exact pixel matching
```
