# Quality-First Architect Runtime Alignment

Status: active_canonical_alignment  
Version: 1.0.0  
Applies to: normal user-facing EV4 Architect Runs

## Authority and precedence

This contract is the active continuation-semantics alignment for:

```text
AGENTS.md
01_PROJECT_INSTRUCTIONS.md
02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md
all active Stage documents and hardening patches
references/ELEMENTOR_KNOWLEDGE_BASE_RAG_STRATEGY.md
knowledge/TUYA_ELEMENTOR_V4_CONCEPTS.md
release/EV4_PROJECT_RELEASE_PACK_v1/*
contracts/STAGE_ANCHOR_CONTRACT.md
contracts/PARTIAL_RERUN_CONTRACT.md
contracts/ARCHITECT_PIPELINE_STAGE_ARTIFACT_V1.md
```

It supersedes only clauses that treat internal authorization carriers, repository workflow evidence, or Validation Profile completeness as prerequisites for ordinary Stage continuation.

All evidence, scoring, candidate-lock, unknown-lifecycle, fidelity, audit, source-access, accessibility, responsive, performance, and final-handoff quality controls in those sources remain active unless explicitly changed here.

Machine-readable authority:

```text
Stage topology/order/version/successor/terminal
→ manifests/architect-pipeline-manifest.v1.json

Normal continuation result
→ ev4-architect-stage-result@1.0.0

Optional deterministic transaction capability
→ manifests/architect-stage-validation-profiles.v1.json

Final Architect → Project Gate handoff
→ canonical Architect Stage Payload and Producer Gate Export contracts
```

## Selected runtime architecture

```text
one canonical pipeline
one Stage order
one quality-driven continuation model
strong fail-closed final Project Gate boundary
```

Stage quality determines progression.

```text
Stage output
→ Stage-specific quality checks
→ Stage Result: pass | needs_input | blocked
→ exact Manifest successor, minimum blocking input, or explicit repair route
```

No `lean`, `strict`, `personal`, `enterprise`, or legacy authorization-driven runtime profile is introduced. There is no feature flag preserving old transition authorization behavior.

## Stage Result semantics

```yaml
pass:
  blocking_issues: []
  next_stage: exact Manifest successor or null for terminal Stage

needs_input:
  blocking_issues: minimum architecture-changing or required-evidence question
  next_stage: null

blocked:
  blocking_issues: genuine quality, evidence, fidelity, or final-handoff defect
  next_stage: null
```

A Stage Result does not claim real chat-runtime enforcement. It is the canonical repository contract and deterministic validation carrier for the normal Run.

## Internal carrier migration

```yaml
stage_anchor:
  active_runtime_role: optional_resume_checkpoint
  authorization_role: none
  required_for_internal_continuation: false

validation_bundle:
  active_runtime_role: none
  authorization_role: none
  optional_roles:
    - repository_audit_tool
    - compatibility_evidence
    - deterministic_validator_regression

validation_profiles_registry:
  active_runtime_role: none
  authorization_role: validation_capability_only
  full_transaction_implemented_required_for_normal_run: false
```

Receipt, Boundary, Failure Event, Anchor, Bundle, and independent regeneration tooling remain readable and testable. They do not authorize ordinary Stage movement.

`authorization_valid` is a legacy/optional transaction field only. It is not a normal-run continuation predicate.

## Conditions that do not block a normal Run

The following conditions may affect optional repository-audit evidence, but do not produce `needs_input` or `blocked` by themselves:

```text
Anchor missing
Validation Bundle missing
independent regeneration not executed
Validation Profile not full_transaction_implemented
profile status blocked_missing_semantics
exact-head CI unavailable
PR review unavailable
Merge evidence unavailable
repository status reconciliation pending
repository maintenance not performed
```

Repository development validation remains separate from project runtime validation.

## Required Stage order

```text
/intake
→ /research
→ /decompose
→ /architectures
→ /score-evidence
→ /score-audit
→ /recommend
→ /build-tree
→ /implementation
→ /final-audit
→ /handoff-export
→ /project-gate-export
```

No mandatory logical Stage may be skipped. Continuation to a non-successor Stage is invalid.

## Research disposition

`/research` remains mandatory and records exactly one:

```text
active_lookup_required
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

The first three may pass when their evidence obligations are satisfied. `blocked_by_missing_required_source` blocks only when a downstream decision genuinely depends on evidence that cannot be obtained.

Research continues to enforce:

```text
platform capability ≠ project-specific behavior
official documentation does not decide visual interpretation
research does not score or recommend architecture
unsupported claims remain unknown
version-sensitive claims require version-aware evidence
```

Any older RAG/TUYA clause requiring Anchor, Bundle, independent regeneration, or `full_transaction_implemented` before source use is superseded for normal Runs. Its source-classification and leakage-prevention controls remain active.

## Quality invariants preserved

### Intake

- lightweight defaults/constraint capture;
- ask only blocking or architecture-changing questions;
- preserve non-blocking unknowns;
- no recommendation, scoring, build tree, or invented exact value.

### Visual decomposition

- no screenshot-to-build-tree jump;
- preserve `observed`, `likely/inferred`, `unknown`, and `not_allowed_yet`;
- do not infer actual Elementor DOM or choose final implementation architecture.

### Architecture and scoring

- viable architecture families and coverage evidence before scoring;
- approved rubric;
- `?` for missing evidence;
- `N/A` only when genuinely non-applicable;
- no numeric conversion of unknowns;
- no hidden recommendation.

### Score Audit and recommendation

- `/recommend` is forbidden before accepted `/score-audit`;
- accepted audit state is `pass` or `pass_with_minor_flags` only when no material defect remains;
- selected candidate comes from the audited eligible set;
- `selected_candidate_id` becomes immutable after lock.

### Unknown lifecycle

An active unknown remains active until explicitly:

```text
resolved_with_evidence
not_applicable
stale after valid rerun
```

Omission is not resolution.

### Build and implementation fidelity

- `/build-tree` preserves the selected architecture;
- `/implementation` preserves the approved tree;
- no unsupported assets, values, breakpoints, interactions, Elementor paths, or hidden re-architecture.

### Final Audit

At minimum, handoff is blocked by:

```text
blocker finding
high-severity architecture drift
candidate-lock violation
unsupported exact value
missing required content
invalid responsive strategy
unresolved downstream-critical unknown
implementation/tree mismatch
```

### Final Project Gate boundary

The final Project Gate boundary remains fail-closed.

Preserve:

```text
canonical Architect Stage Payload
JSON Schema validation
semantic validation
locked identity validation
canonical serialization
provenance
digest/hash integrity
invalid-payload rejection
legacy-output non-substitution
```

## Partial rerun

Ordinary partial reruns use the latest valid Stage output and Stage Result. Start at the earliest Stage whose owned information changed, invalidate dependent downstream outputs, preserve unaffected evidence, and do not require Anchor or Bundle authorization.

## Repository repair separation

Routine Stage failure first returns a Run repair route. It does not automatically recommend or require repository repair.

Repository maintenance may still use branches, tests, CI, exact revision identity, review, and one bounded PR. That discipline must not leak into the user-facing project Run.

## Historical and optional sources

Historical experiment reports, old transaction fixtures, Anchors, Bundles, receipts, and profile statuses remain truthful evidence of their tested system. They must be labeled historical or optional when cited and cannot override this active alignment for normal Runs.

## Validation boundary

Repository tests may prove deterministic contract behavior at an exact revision. They do not by themselves prove:

```text
real ChatGPT/model-host enforcement
live Elementor rendering
real Elementor export JSON behavior
browser/device validity
downstream acceptance
release readiness
production readiness
```
