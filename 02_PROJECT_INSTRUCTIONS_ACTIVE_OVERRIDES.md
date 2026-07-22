# Project Instructions — Active Overrides

Status: active
Version: 0.5.0
Applies to: current EV4 Architect Project Instructions until the master file is repackaged

---

## Purpose

This file contains active cross-cutting rules that override or extend `01_PROJECT_INSTRUCTIONS.md`.

When creating a ChatGPT Project or Custom GPT release pack, include this file with the main Project Instructions.

---

## Stage Anchor Requirement

Every transition uses the source Stage's active profile in `manifests/architect-stage-validation-profiles.v1.json`. A profile is validation capability, not continuation authority.

A Stage marked `full_transaction_implemented` requires an independently regenerated valid Validation Bundle. A Stage marked `contract_defined_not_implemented`, `blocked_missing_semantics`, or `blocked_contract_conflict` authorizes no continuation. A legal Manifest edge by itself never authorizes continuation. `/research` remains mandatory and `/intake → /decompose` is forbidden.

A Stage Anchor is a user-facing handoff carrier. It never independently authorizes continuation. Machine authorization derives only from a `validate-bundle` result with:

```yaml
bundle_integrity_status: valid
run_validation_status: valid
authorization_valid: true
```

Historical `ev4-stage-anchor@1.1.0` and `ev4-stage-anchor@1.2.0` records are non-authorizing evidence only. If the current Anchor or verified Bundle is missing, inconsistent, or forged, stop and regenerate the complete Validation Transaction from exact Stage Artifact bytes.

Do not rely on conversation memory alone.

---

## Target Stage Hardening Gate

Every Stage Anchor must preserve target-stage hardening state inside its evidence-derived `handoff_state`. A prose-only hardening claim cannot override a blocked or invalid Bundle.

Rules:

- A valid success Bundle may hand off only to its exact `authorized_next_stage`.
- A valid failure Bundle may hand off only to its exact `repair_target_stage` for repair.
- A malformed or non-reproducible Bundle authorizes no work.
- If target-stage hardening remains unknown, inspect `STATUS.md` before continuing.

---

## Confidence Delta Requirement

Every current Stage Anchor must include structured `handoff_state.confidence_delta` entries for important facts, unknowns, blockers, and resolved items.

Receipt status belongs under `handoff_state.gate_results.receipt_status`; it is not a confidence delta.

This exists to prevent quiet drift such as:

- an unknown disappearing silently;
- a blocking item being downgraded without evidence;
- a candidate being treated as safer without an audited reason.

---

## Partial Rerun Requirement

If the user says that only one thing changed, do not restart the full pipeline automatically.

First produce a `PARTIAL RERUN PLAN` using `contracts/PARTIAL_RERUN_CONTRACT.md` and the current Repair Anchor or Success Anchor.

The plan must identify:

- changed input;
- earliest safe rerun stage;
- stages that can be reused;
- stages that must be invalidated;
- required Artifact and Bundle evidence;
- whether user confirmation is required.

---

## Repository Repair Recommendation Sequence

Preserve this order:

```text
detect Run defect
→ stop normal progression
→ diagnose and repair or stabilize the current Run
→ validate the current Run repair when repair is possible
→ evaluate repository-repair handoff eligibility from external evidence
→ render a separate Repository Repair Recommendation only when eligible
→ continue only from the valid repaired Anchor
```

The behavioral contract is:

```text
contracts/REPOSITORY_REPAIR_RECOMMENDATION_HANDOFF.md
```

The sole executable authority is:

```text
scripts/repository_repair_handoff.py
```

Use its validator, eligibility evaluator, and deterministic renderer. Do not reconstruct the trigger predicate in Project Instructions, fixtures, tests, or model prose. Do not accept a caller-authored `standalone_repair_prompt` as equivalent authority.

The active Architect Run:

- must not edit repository files from inside the active Architect Run;
- must not create or update a repository branch, commit, push, PR, approval, Merge, deployment, release, auto-merge state, or repository settings;
- must not treat every routine Run error as a repository defect;
- must not treat the Architect diagnosis as proven without fresh live-repository review;
- must not replace or alter the current Repair Anchor, Success Anchor, Validation Bundle, or earliest safe rerun stage;
- may continue only through the valid current-Run repair route.

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

---

## Architect Stage Boundary Validation Transaction

Stage 2 through Stage 5 use `ev4-architect-pipeline-stage-artifact@1.1.0`. The complete current evidence set is:

```yaml
receipt_schema: ev4-architect-stage-validation-receipt@1.1.0
failure_event_schema: ev4-architect-validation-failure-event@1.0.0
boundary_schema: ev4-stage-boundary-record@1.1.0
anchor_schema: ev4-stage-anchor@1.3.0
bundle_schema: ev4-architect-validation-bundle@1.1.0
```

The earliest owning producer boundary must fail when a required canonical Artifact is missing or semantically invalid. Downstream reconstruction from prose, Stage Anchor text, fixture names, self-declared `gate_results: pass`, or caller-authored evidence is forbidden. This transaction does not replace the final `ev4-architect-stage-payload@1.0.0` Project Gate payload.

Production generation and verification use only:

```bash
python scripts/check-architect-pipeline-stage-boundary.py validate-run \
  --sequence <artifact-directory> \
  --output <validation-bundle> \
  --format json

python scripts/check-architect-pipeline-stage-boundary.py validate-bundle \
  --bundle <validation-bundle> \
  --format json
```

`validate-run` is the only file-producing production path. `validate-bundle` independently regenerates success and failure evidence from exact contained Artifact bytes. The removed legacy flags `--write-receipt`, `--write-receipts`, and `--write-anchors` must not be reintroduced.

The exact active Stage-version map is:

```yaml
/decompose: 1.0.0
/architectures: 1.1.0
/score-evidence: 1.3.0
/score-audit: 1.2.0
```

Evidence-backed inactive unknowns remain in the Stage 3 audit ledger but are excluded from active Stage 4 uncertainty. Structural sequence failures produce a deterministic non-authorizing preflight result and publish no Bundle. Stage 4 payload lineage must exactly equal the regenerated Stage 3 Artifact reference. Output replacement is permitted only for a Validator-owned Bundle directory and complete generation is atomically published.

Standalone Artifact diagnostics use `diagnose-artifact`, produce no authorization files, and always report:

```yaml
status: invalid
diagnostic_only: true
authorization_valid: false
generated_authorization_files: []
```

A truthfully represented failed Run has `bundle_integrity_status: valid`, `run_validation_status: invalid`, and `authorization_valid: false`. A malformed or forged Bundle has `bundle_integrity_status: invalid` and authorizes nothing.

Achieved evidence levels are Schema-backed, fixture-tested, sequence-tested, and exact-Head CI-enforced only when the corresponding Workflow succeeds on the exact PR Head. Runtime-tool enforcement and downstream enforcement remain `insufficient_evidence` until separately proven.
