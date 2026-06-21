# LLM Debug Trace Contract — EV4 Architect

Status: active
Version: 1.0.0
Schema: ev4-debug-trace@1.0.0

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

## Debug Agent Contract

A model-language debugger may be added as a separate workflow.

The debugger must not solve the Elementor architecture task again. It must inspect traces and answer:

1. Which stage first produced the defect?
2. Which rule was missing, weak, or ignored?
3. Which payload field failed?
4. What minimal prompt/document patch would prevent recurrence?
5. Which calibration case should be added?

## Forbidden Debug Behavior

The debugger must not:

- claim access to hidden chain-of-thought;
- invent model intentions;
- re-score candidates unless asked to run Stage 4 repair;
- recommend architecture directly;
- bypass the existing repair route;
- rewrite the whole system when a local patch is enough.

## Recommended Debug Output

```text
EV4 DEBUG REPORT

1. Failure Summary
2. First Broken Stage
3. Evidence Trail
4. Rule or Schema Violation
5. Minimal Repair Patch
6. Regression Test / Calibration Case Needed
7. Rerun From Stage
```

## Relation To Tracing Tools

This contract is compatible with external trace systems. Tool calls, model calls, stage outputs, payloads, validator results, and repair routes can be captured as trace spans.

However, this repository must remain useful even without external observability infrastructure; therefore every stage must emit compact, text-based debug payloads when debug mode is requested.
