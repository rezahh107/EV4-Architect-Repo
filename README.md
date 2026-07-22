# EV4 Architect Repo

Status: quality-first Architect runtime implemented on a review branch; canonical Project Gate export remains fail-closed; real non-synthetic handoff and production readiness remain `insufficient_evidence`.

Role: `architecture_decision_system`

## Purpose

EV4 Architect decides what should be built and preserves the selected candidate, approved structure, class intent, forbidden work, unknowns, and architecture handoff.

```text
Architect says what should be built.
CE proves how it can be safely built.
Builder executes proven strategy.
Responsive validates post-build responsive behavior.
```

Approved architecture is not automatically approved implementation strategy.

## Quick Start

In a new user-facing Architect session with the repository instructions loaded, send:

```text
شروع
```

If no screenshot, section description, active run, or resumable passed Stage Result is present, the assistant returns the fixed intake message from:

```text
manifests/architect-conversation-bootstrap.v1.json
```

If usable project input is supplied with the trigger, run `/intake` directly.

The controlled opening sequence is:

```text
/intake → /research → /decompose
```

## Canonical Pipeline

```text
/intake → /research → /decompose → /architectures
→ /score-evidence → /score-audit → /recommend
→ /build-tree → /implementation → /final-audit
→ /handoff-export → /project-gate-export
```

The canonical machine-readable authority is:

```text
manifests/architect-pipeline-manifest.v1.json
```

`/builder-feed-export` remains a legacy compatibility output, not canonical Project Gate Producer Export.

## Quality-First Continuation

Active runtime authority:

```text
contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md
contracts/ARCHITECT_STAGE_RESULT_V1.md
schemas/ev4-architect-stage-result.v1.schema.json
scripts/architect_quality_runtime.py
```

Every Stage returns:

```yaml
stage_status: pass | needs_input | blocked
blocking_issues: []
carried_unknowns: []
quality_checks: {}
next_stage: exact Manifest successor or null
```

The normal Run does not require internal Stage Anchors, Validation Bundles, independent Bundle regeneration, Validation Profile completeness, exact-head CI, PR review, Merge evidence, or repository maintenance.

Those artifacts and checks remain optional repository-audit and deterministic-regression tooling.

## Quality Boundaries Preserved

The runtime rejects:

- mandatory Stage skipping or non-successor continuation;
- screenshot-to-build-tree shortcuts;
- recommendation before accepted `/score-audit`;
- hidden recommendation during scoring;
- conversion of unknown evidence into exact values;
- `selected_candidate_id` drift after lock;
- re-architecture during `/build-tree`;
- implementation/tree mismatch;
- silent unknown disappearance;
- blocker/high final-audit findings at handoff;
- invalid canonical Project Gate payload;
- legacy Builder Feed substitution.

All detailed evidence, RAG/TUYA source-access, scoring, accessibility, responsive, performance, and Stage hardening controls remain active unless they conflict only on continuation authorization.

## Research Stage

`/research` remains mandatory and records one disposition:

```text
active_lookup_required
existing_evidence_sufficient
no_platform_question
blocked_by_missing_required_source
```

Only a genuinely required unavailable source blocks. Research establishes platform capability, not screenshot interpretation or architecture recommendation.

## EV4 Project Gate Workflow

```text
Architect output
→ EV4 Project Gate
→ accepted: CE Input Package
→ needs repair: Architect Repair Package
```

The final Architect → Project Gate boundary remains strongly fail-closed.

Canonical Architect payload identity:

```text
ev4-architect-stage-payload@1.0.0
```

## Official Project Gate Export Command

```bash
python scripts/export-architect-project-gate.py \
  --payload path/to/architect-stage-payload.json \
  --run-id <actual-architect-run-id> \
  --output architect-project-gate.json
```

Invalid, synthetic, blocked, or insufficient-evidence inputs cannot produce an allowed handoff.

## Optional Audit Tooling

The Stage Anchor/Bundle contracts, Validation Profiles Registry, and `architect_validation_*` modules remain preserved for repository audit, exact-byte deterministic regression, compatibility evidence, and historical readability.

They are not active user-facing transition tickets.

## Validation

```bash
python -m pip install 'jsonschema>=4.22.0' 'pytest>=8.0.0' 'PyYAML>=6.0.0'
python scripts/check-architect-quality-runtime.py
python scripts/check-architect-bootstrap.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p no:cacheprovider -q \
  tests/test_architect_quality_runtime.py \
  tests/test_architect_bootstrap_semantics.py
```

Existing payload, governance, release-pack, and optional transaction suites remain applicable.

## Boundaries

This repository does not perform interactive Elementor execution, prove constructability, complete responsive QA, or claim production readiness without downstream evidence.

## Companion Repositories

```text
https://github.com/rezahh107/EV4-Project-Gate
https://github.com/rezahh107/EV4-Constructability-Engineer-Repo
https://github.com/rezahh107/EV4-Builder-Assistant-Repo
https://github.com/rezahh107/EV4-Responsive-Architect
```

## Status Authority

Mutable project status is maintained only in `STATUS.md`. This README is orientation and does not override live repository evidence.
