# AGENTS.md

## Scope

These instructions apply to the entire repository unless a closer nested `AGENTS.md` or `AGENTS.override.md` provides more specific guidance.

## Repository Role

`EV4-Architect-Repo` owns EV4 architecture decisions: visual intake, evidence-governed research, candidate generation and scoring, `selected_candidate_id`, approved structure and class intent, forbidden work, unknowns, and Architect handoff.

It does not prove constructability, execute Elementor actions, or claim responsive or production completion.

## Mandatory Session Startup

Before modifying or validating the repository, read these active authorities in order:

1. `README.md`
2. `STATUS.md`
3. `docs/governance/AI_AUTHORITY_GOVERNANCE_ADOPTION.md`
4. `02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md`
5. `contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md`
6. `manifests/architect-conversation-bootstrap.v1.json`
7. `manifests/architect-pipeline-manifest.v1.json`
8. `contracts/ARCHITECT_STAGE_RESULT_V1.md`
9. `schemas/ev4-architect-stage-result.v1.schema.json`
10. `manifests/architect-stage-validation-profiles.v1.json`
11. `contracts/ARCHITECT_STAGE_EVIDENCE_PAYLOAD_V1.md`
12. the relevant Stage, contract, Schema, fixture, validator, workflow, and hardening-patch files

Identify the authorized work and check dependencies before edits. When sources conflict, the active Alignment Contract supersedes only continuation-authorization clauses. Preserve all stricter quality controls that do not conflict with quality-driven continuation.

## Human Authority Boundary

Human technical approval and owner acknowledgement must not be treated, accepted, or used as substitutes for repository evidence.

The user may perform the administrative Merge action after a valid technical recommendation; that action is not technical approval and does not prove correctness.

## Runtime Authority

The Pipeline Manifest is the sole machine-readable authority for Stage inventory, order, versions, legal successor, terminal identity, and the finite quality-check inventory owned by each Stage.

Normal user-facing continuation is owned by:

```text
contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md
contracts/ARCHITECT_STAGE_RESULT_V1.md
schemas/ev4-architect-stage-result.v1.schema.json
scripts/architect_quality_runtime.py#evaluate_stage
```

```text
Stage Output
+ current Run State
+ fixed Stage rules
→ evaluate_stage
→ evaluator-derived Stage Result
→ exact Manifest successor, minimum blocking input, or explicit repair route
```

A producer-authored or serialized Stage Result is not continuation authority. It may remain readable as a summary, resume hint, compatibility record, or fixture, but continuation must be recomputed from the corresponding Stage Output and Run State.

Stage Anchors, Receipts, Boundary Records, Failure Events, Validation Bundles, independent Bundle regeneration, exact-head CI, PR review, Merge evidence, and repository maintenance are not normal-run continuation prerequisites.

`manifests/architect-stage-validation-profiles.v1.json` describes optional deterministic audit capability. A Stage does not block merely because its profile is not `full_transaction_implemented`.

## User-Facing Bootstrap

The canonical new-run bootstrap contract is:

```text
manifests/architect-conversation-bootstrap.v1.json
```

If the user's intent is only a recognized new-run trigger such as `شروع`, and no screenshot, section description, active run, or resumable runtime material is present, return the exact bootstrap response and do nothing else.

If the user supplies a screenshot or usable section description with the trigger, run `/intake` directly without repeating supplied information.

If a prior Stage Result is supplied for resume, do not trust it merely because it is Schema-valid. Resolve the smallest available corresponding Stage Output and Run State, then recompute through `evaluate_stage`. Do not create persistent storage, an immutable receipt, or an Artifact registry solely for resume.

The first controlled sequence is always:

```text
/intake → /research → /decompose
```

Do not skip `/research`.

## Research Stage

`/research` records exactly one disposition:

```text
active_lookup_completed
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

`existing_evidence_sufficient` and `no_platform_question` are valid passing outcomes. Do not require external citations, URLs, retrieval receipts, or source metadata when no platform-capability claim requires active lookup.

Research does not score or recommend architecture. Official documentation proves platform capability only; it does not decide project-specific visual interpretation. Unsupported or version-sensitive claims remain unknown unless evidence resolves them.

## Quality Invariants

Do not:

- jump directly from screenshot or description to a final Elementor tree;
- recommend during `/intake`, `/research`, `/decompose`, `/architectures`, or `/score-evidence`;
- convert unknown evidence into numeric confidence or invented exact values;
- run `/recommend` before `/score-audit` is accepted;
- change `selected_candidate_id` after lock;
- re-architect during `/build-tree`, `/implementation`, or `/final-audit`;
- silently remove an active unknown;
- close a downstream-critical unknown with an arbitrary string;
- accept a caller-authored digest without canonical content;
- hand off with blocker/high final-audit findings;
- substitute legacy Builder Feed for canonical `/project-gate-export`.

All detailed Stage quality, source-access, scoring, accessibility, responsive, performance, and fidelity rules remain active from their owning documents and patches.

## Stage Result Semantics

```yaml
pass:
  blocking_issues: []
  next_stage: exact Manifest successor

needs_input:
  blocking_issues: minimum architecture-changing or required-evidence question
  next_stage: null

blocked:
  blocking_issues: genuine quality, evidence, fidelity, or handoff defect
  next_stage: null
```

The evaluator rejects missing, unknown, cross-Stage, failed, unresolved, or improperly `not_applicable` required checks.

Missing Anchor, Bundle, independent regeneration, incomplete Validation Profile, unavailable exact-head CI, unavailable PR review, or pending repository maintenance cannot by itself block a normal Run.

## Unknown Lifecycle

Active unknowns persist in the small Run State until the evaluator accepts an explicit resolution.

Ordinary resolution requires a resolution type and explanatory note. A resolvable evidence reference is required only for downstream-critical or Artifact-dependent unknowns.

Omission from a later Stage Output is not resolution.

## Candidate and Fidelity Boundary

After `/recommend`, the evaluator locks `selected_candidate_id`. Downstream Stages must preserve it unless a legitimate partial rerun reaches `/recommend` or an earlier Stage.

For `/build-tree` and `/implementation`, use the existing canonical structured Stage Output. Do not create a wrapper Artifact solely to compute a digest.

```text
no real canonical content
→ no claimed digest
```

The evaluator computes Build Tree and Implementation digests from actual content and rejects `null == null`, fabricated SHA-like strings, candidate drift, and approved-tree mismatch.

Conversational Stage output does not require cryptographic identity.

## Project Gate Handoff

```text
Architect output
→ EV4 Project Gate
→ accepted: CE Input Package
→ not accepted: Architect repair package
```

The terminal Stage is `/project-gate-export`.

Its pass result must be derived from the actual canonical Architect Stage Payload, existing Schema and semantic validation, selected-candidate consistency, existing Producer Gate exporter, actual canonical export, and contract/digest verification.

Caller-controlled success Booleans cannot substitute for actual validation. Preserve locked identity, canonical serialization, provenance, digest integrity, invalid-payload rejection, and legacy-output non-substitution.

## Optional Audit Tooling

`contracts/STAGE_ANCHOR_CONTRACT.md`, `contracts/ARCHITECT_PIPELINE_STAGE_ARTIFACT_V1.md`, Validation Profiles, and `architect_validation_*` scripts remain available for repository audits, compatibility evidence, and deterministic regression.

Historical carriers remain readable and truthfully labeled. They do not authorize ordinary internal Stage movement.

## Repository Repair Boundary

Run repair and repository maintenance are separate. A routine Stage quality failure returns an evidence-based Run repair route; it does not automatically require repository work.

An active Architect project Run must not edit repository files, create branches or PRs, commit, push, approve, merge, deploy, release, enable auto-merge, or modify repository settings.

## Change Rules

For repository changes:

- preserve public contract behavior unless a breaking change is explicitly approved;
- update owning contracts/Schemas and affected fixtures/tests;
- classify changed tests as preserved quality invariant, obsolete authorization expectation, historical compatibility, or unrelated;
- state compatibility and evidence boundaries;
- preserve locked identity and valid evidence;
- avoid unrelated refactoring;
- review `planning/DECISION_ESCAPE_ROUTES.yml` before changing decision-bearing outputs.

## Validation

For quality-first runtime changes:

```bash
python -m pip install 'jsonschema>=4.22.0' 'pytest>=8.0.0' 'PyYAML>=6.0.0'
python scripts/check-architect-quality-runtime.py
python scripts/check-architect-bootstrap.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p no:cacheprovider -q \
  tests/test_architect_quality_runtime.py \
  tests/test_architect_bootstrap_semantics.py
```

Existing payload, governance, release-pack, and optional transaction suites remain applicable.

Do not claim repository-wide, chat-runtime, downstream, browser, Elementor, or production validation unless that evidence was actually obtained.

## Evidence and Reporting

Use explicit states: `observed`, `implemented`, `validated`, `inferred`, `proposed`, `unverified`, and `insufficient_evidence`. Technical identifiers, paths, Schema IDs, and diagnostics remain in English.
