# LLM Debug Trace Contract — EV4 Architect

Status: active
Version: 1.1.0
Schema: ev4-debug-trace@1.0.0
Optional extension: ev4-repository-repair-diagnostic-extension@1.0.0

## Purpose

This document defines a model-readable debugging layer for the EV4 Architect pipeline.

The goal is not to expose hidden chain-of-thought. The goal is to force each stage to produce an explicit, safe, structured decision trace that can be audited and repaired.

## Core Principle

Debug the pipeline through external traces, not private thoughts.

A language model is not required or trusted to reveal its hidden reasoning. Instead, every stage must externalize:

- what input it used;
- what claims it made;
- what evidence supported each claim;
- which rule or rubric item was applied;
- what was unknown;
- what was blocked;
- what repair route is required if the output fails.

## Why This Exists

When a final Elementor architecture output is wrong, the user needs to know where the failure happened:

- bad visual decomposition;
- missing unknown;
- biased architecture enumeration;
- scoring arithmetic error;
- hidden recommendation leak;
- invalid handoff;
- build-tree naming or structure error.

Without a structured trace, failures become vague and the prompt cannot be repaired precisely.

## Debug Mode

Any pipeline run may request:

```text
/debug-run
```

In debug mode, each stage must include an `EV4_DEBUG_TRACE` block after its normal output.

## EV4_DEBUG_TRACE Required Shape

```json
{
  "schema": "ev4-debug-trace@1.0.0",
  "run_id": null,
  "stage": null,
  "stage_version": null,
  "input_digest": {
    "inputs_received": [],
    "inputs_missing": [],
    "input_payload_schemas": []
  },
  "decision_log": [],
  "evidence_map": [],
  "unknown_register": [],
  "rule_application_log": [],
  "failure_symptom_index": [],
  "repair_route": null,
  "handoff_payload_schema": null
}
```

## Repository Repair Diagnostic Extension

When the Debug Agent classifies recurrence risk after the current Run repair route is determined, it may append this additive extension:

```yaml
incident_class: ordinary_run_error | repeatable_run_defect | unresolved_causality
repository_gap_state: confirmed | probable | possible | insufficient_evidence | not_repository_related
repository_gap_class: repository_enforcement_gap | contract_ambiguity | validator_gap | missing_negative_regression | stage_boundary_escape_route | conflicting_authorities | fail_late_detection | repeatable_prompt_or_protocol_defect | null
repository_gap_evidence:
  - evidence_ref:
    evidence_summary:
repository_repair_handoff_required: true | false
repository_repair_handoff_reason:
```

Closed rules:

- `repository_repair_handoff_required: true` is allowed only for `confirmed` or `probable` and an allowed non-null `repository_gap_class`.
- `possible` may justify a brief repository-review suggestion but no full standalone maintenance prompt.
- `insufficient_evidence` and `not_repository_related` require `repository_repair_handoff_required: false`.
- An ordinary isolated Run error must not be reclassified as a repository defect without repeatability evidence.
- Classification occurs only after the current Run is stable as repaired, blocked, or terminal.
- The extension is external diagnostic evidence only. It does not authorize repository modification and does not replace the current Repair Anchor, Success Anchor, or Partial Rerun plan.
- Full handoff semantics are owned by `contracts/REPOSITORY_REPAIR_RECOMMENDATION_HANDOFF.md`.

## Decision Log

Each stage must log only decisions that affect downstream output.

```json
{
  "decision_id": "D-001",
  "decision": "candidate included | candidate excluded | score assigned | gate failed | recommendation blocked",
  "target": null,
  "basis": {
    "evidence_ids": [],
    "rule_ids": [],
    "unknown_ids": []
  },
  "confidence": "confirmed | inferred | uncertain | blocked",
  "downstream_effect": null
}
```

## Evidence Map

```json
{
  "evidence_id": "E-001",
  "source_stage": "intake | research | decompose | architectures | score-evidence | score-audit | recommend",
  "source_payload": null,
  "claim_supported": null,
  "evidence_label": "SUPPORTED_EVIDENCE | PARTIALLY_SUPPORTED_EVIDENCE | INFERRED_EVIDENCE | ABSENT_EVIDENCE | CONTRADICTED_EVIDENCE | UNRESOLVED_CONFLICT",
  "quote_or_summary": null
}
```

## Unknown Register

```json
{
  "unknown_id": "U-001",
  "unknown": null,
  "introduced_at_stage": null,
  "propagated_to_stages": [],
  "resolved": false,
  "resolution_source": null,
  "effect_if_unresolved": null
}
```

## Rule Application Log

```json
{
  "rule_id": "R-001",
  "rule_source": "project_defaults | stage_contract | rubric | hardening_patch | example_bank",
  "rule_name": null,
  "applied_to": null,
  "result": "pass | fail | n/a | blocked | requires_user_input",
  "notes": null
}
```

## Failure Symptom Index

A debug agent should classify bad outputs using this taxonomy:

| Symptom | Meaning | Likely repair stage |
|---|---|---|
| `missing_input` | Required payload or artifact absent | Same stage input gate |
| `stage_boundary_violation` | Stage did work reserved for another stage | Current stage contract |
| `hallucinated_evidence` | Claim lacks source evidence | Current stage or earlier evidence map |
| `unknown_collapsed_to_number` | Unknown was scored or treated as resolved | Stage 4 |
| `contradiction_softened` | Contradicted evidence treated as absent/minor | Stage 4 or Stage 5 |
| `arithmetic_error` | Score math or denominator wrong | Stage 4 or validator |
| `gate_override` | Failed gate hidden behind high score | Stage 4 or Stage 5 |
| `hidden_recommendation` | Premature or biased recommendation language | Stage 3, 4, 5, or 6 |
| `forced_tie_break` | Close decision resolved without strict evidence | Stage 6 |
| `bad_handoff` | Payload missing or wrong schema | Producing stage |
| `naming_contract_missing` | Build tree cannot proceed safely | Stage 7 |

The repository-gap classes above extend this existing taxonomy; they do not create a second failure taxonomy.

## Debug Agent Contract

A model-language debugger may be added as a separate workflow.

The debugger must not solve the Elementor architecture task again. It must inspect traces and answer:

1. Which stage first produced the defect?
2. Which rule was missing, weak, or ignored?
3. Which payload field failed?
4. What minimal Run repair is required?
5. Which regression test or calibration case is required?
6. What is the earliest safe rerun stage?
7. After the Run is stable, is repository recurrence evidence `confirmed`, `probable`, `possible`, `insufficient_evidence`, or `not_repository_related`?
8. Is a separate Repository Repair Recommendation Handoff required?

## Forbidden Debug Behavior

The debugger must not:

- claim access to hidden chain-of-thought;
- invent model intentions;
- re-score candidates unless asked to run Stage 4 repair;
- recommend architecture directly;
- bypass the existing repair route;
- rewrite the whole system when a local patch is enough;
- edit repository files inside the active Architect Run;
- treat a repository-gap hypothesis as proven without fresh live-repository review;
- emit a full repository-maintenance prompt for every routine Run error.

## Recommended Debug Output

```text
EV4 DEBUG REPORT

1. Failure Summary
2. First Broken Stage
3. First Detection Stage
4. Evidence Trail
5. Rule or Schema Violation
6. Minimal Current-Run Repair
7. Regression Test / Calibration Case Needed
8. Rerun From Stage
9. Repository Recurrence Classification
10. Repository Repair Recommendation Handoff, if allowed
```

## Relation To Tracing Tools

This contract is compatible with external trace systems. Tool calls, model calls, stage outputs, payloads, validator results, and repair routes can be captured as trace spans.

However, this repository must remain useful even without external observability infrastructure; therefore every stage must emit compact, text-based debug payloads when debug mode is requested.
