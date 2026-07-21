# Project Instructions — Active Overrides

Status: active
Version: 0.2.0
Applies to: current EV4 Architect Project Instructions until the master file is repackaged

---

## Purpose

This file contains active cross-cutting rules that override or extend `01_PROJECT_INSTRUCTIONS.md`.

When creating a ChatGPT Project or Custom GPT release pack, include this file with the main Project Instructions.

---

## Stage Anchor Requirement

Before starting any stage after `/intake`, the user or assistant must provide a valid Stage Anchor.

Required schema:

```text
ev4-stage-anchor@1.1.0
```

If a valid anchor is missing, outdated, schema-mismatched, or inconsistent with prior stage output, stop and request the correct anchor or regenerate it from the previous stage output.

Do not rely on conversation memory alone.

---

## Target Stage Hardening Gate

Every Stage Anchor must include:

```text
target_stage_hardening_status: confirmed | draft | scaffolded | unknown
```

Rules:

- If `confirmed`, the target stage may run normally.
- If `draft`, run only in review/test/hardening mode.
- If `scaffolded`, do not run as production output unless the user explicitly approves a scaffolded-stage run.
- If `unknown`, inspect `STATUS.md` before continuing.

---

## Confidence Delta Requirement

Every Stage Anchor must include `confidence_delta` for important facts, unknowns, blockers, and resolved items.

This exists to prevent quiet drift such as:

- an unknown disappearing silently;
- a blocking item being downgraded without evidence;
- a candidate being treated as safer without an audited reason.

---

## Partial Rerun Requirement

If the user says that only one thing changed, do not restart the full pipeline automatically.

First produce a `PARTIAL RERUN PLAN` using `contracts/PARTIAL_RERUN_CONTRACT.md`.

The plan must identify:

- changed input;
- earliest safe rerun stage;
- stages that can be reused;
- stages that must be invalidated;
- required anchor and payloads;
- whether user confirmation is required.

---

## Knowledge Base / RAG Rule

Elementor documentation, widget references, internal concept references, and future export evidence may support the pipeline, but must not replace it.

RAG may support:

- `/research`
- `/architectures`
- `/build-tree`
- `/implementation`

RAG must not bypass:

- `/decompose`
- `/score-evidence`
- `/score-audit`
- `/recommend`

Core distinction:

```text
platform capability ≠ project-specific behavior
```

If documentation only proves that Elementor can do something, do not treat it as proof that the current section should use it.

---

## Internal Concept Reference Rule

The file below is an active internal concept reference:

```text
knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
```

Use it for:

- EV4 thinking order;
- shared Persian vocabulary;
- normal-flow vs overlay discipline;
- relative stage containment;
- responsive inheritance caution;
- design-system class/variable/component logic;
- DOM/audit mindset.

Do not use it as:

- official Elementor platform documentation;
- proof that a widget or setting exists;
- proof that a current screenshot should use a specific architecture;
- permission to skip Stage 2, 4, 5, or 6.

Any fact retrieved from TUYA must be classified as:

```text
source_type: internal_concept_reference
fact_class: project_conceptual_model
```

---

## Direct Visual-to-Build-Tree Ban

Do not go directly from screenshot to final Elementor tree.

The model must not skip:

- visual role decomposition;
- architecture enumeration;
- evidence-bound scoring;
- independent audit;
- recommendation authorization.

Exception: only a user-approved quick sketch mode may produce a non-audited draft tree, and it must be clearly labeled as non-production.


## Architect Stage Boundary Artifact Enforcement

Stage 2 through Stage 5 now have an additive intermediate Artifact contract, `ev4-architect-pipeline-stage-artifact@1.1.0`, validated by `scripts/check-architect-pipeline-stage-boundary.py` with receipts using `ev4-architect-stage-validation-receipt@1.1.0`. The earliest owning producer boundary must fail when a required canonical artifact is missing; downstream reconstruction from prose, Stage Anchor text, or self-declared `gate_results: pass` is forbidden. This does not replace the final `ev4-architect-stage-payload@1.0.0` Project Gate payload.

If an executable validator/tool is available:
- write the canonical Stage Artifact;
- execute the official validator;
- obtain the receipt;
- emit the separate Boundary-referenced NEXT_STAGE_ANCHOR only from a valid generated Validation Bundle.

If execution is unavailable:
- do not claim machine validation;
- do not emit a validated separate NEXT STAGE ANCHOR;
- return validation_required or insufficient_evidence;
- provide the exact manual validator command;
- preserve the Artifact for external validation.

Canonical production authorization command: `python scripts/check-architect-pipeline-stage-boundary.py validate-run --sequence fixtures/architect-pipeline-stage-boundary/valid/complete-sequence --output /tmp/ev4-validation-bundle --format json`. Caller-supplied Receipts, Boundary Records, Anchors, and Manifests are untrusted assertions; only a freshly generated and independently `validate-bundle`-verified Validation Bundle authorizes the next stage. Standalone `--artifact` and `--anchor` paths are diagnostic-only and report `authorization_valid: false`. Achieved evidence levels in this repository are schema_backed, fixture_tested, sequence_fixture_tested, and ci_enforced only after the workflow runs on an exact PR head; runtime_tool_enforced and downstream_enforced remain insufficient_evidence until separately proven.
