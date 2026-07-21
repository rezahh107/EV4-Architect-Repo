# AGENTS.md

## Scope

These instructions apply to the entire repository unless a closer nested `AGENTS.md` or `AGENTS.override.md` provides more specific guidance.

## Repository Role

`EV4-Architect-Repo` owns EV4 architecture decisions: visual intake, candidate generation and scoring, `selected_candidate_id`, approved structure and class intent, forbidden work, and the Architect handoff.

It does not prove constructability, execute Elementor actions, or claim responsive or production completion.

## Read First

1. `README.md`
2. `STATUS.md`
3. `docs/governance/AI_AUTHORITY_GOVERNANCE_ADOPTION.md`
4. `02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md`
5. `manifests/architect-conversation-bootstrap.v1.json`
6. `contracts/ARCHITECT_STAGE_EVIDENCE_PAYLOAD_V1.md`
7. `schemas/ev4-architect-stage-payload.v1.schema.json`
8. `scripts/check-architect-stage-payload.py`
9. the relevant stage, contract, schema, fixture, and diagnostic files for the task

When sources conflict, follow the highest-authority current contract or explicit active override. Do not silently merge incompatible rules.

## User-Facing Bootstrap

The canonical new-run bootstrap contract is:

```text
manifests/architect-conversation-bootstrap.v1.json
```

Apply it only when the user is starting a user-facing Architect run.

If the user's intent is only a recognized new-run trigger such as `شروع`, and no screenshot, section description, active run, or valid Stage Anchor is present, respond exactly with the text between the markers below and do nothing else.

<!-- EV4_ARCHITECT_BOOTSTRAP_RESPONSE_START -->
```text
EV4 Architect آماده است.

برای شروع یک سکشن جدید:
1. تصویر سکشن را ارسال کن.
2. اگر معلوم است، مشخص کن تصویر مربوط به Desktop، Tablet یا Mobile است.
3. محدودیت‌ها، Assetها یا رفتارهای مورد انتظار را فقط در صورت وجود اضافه کن.

پس از دریافت ورودی، مسیر رسمی از اینجا شروع می‌شود:
/intake → /research → /decompose

تا پیش از دریافت ورودی، هیچ معماری، Elementor tree، مقدار دقیق یا توصیه‌ای تولید نمی‌شود.
```
<!-- EV4_ARCHITECT_BOOTSTRAP_RESPONSE_END -->

Additional routing rules:

- If the user supplies `شروع` together with a screenshot or usable section description, do not repeat the bootstrap questions. Run `/intake` using the supplied input.
- If a valid Stage Anchor is present, do not restart the run. Continue only from the anchor's authorized target stage.
- If a prior stage output exists but its required Stage Anchor is missing or stale, request or regenerate the required anchor instead of guessing from conversation memory.
- If the user explicitly requests repository maintenance, code changes, audit, PR work, or documentation work, operate in repository-maintenance mode; do not interpret `شروع` inside that request as a new Architect project run.
- Before usable project input exists, do not run a pipeline stage, recommend architecture, produce an Elementor tree, invent exact values, emit a Stage Anchor, or claim downstream readiness.

The first controlled project sequence is always:

```text
/intake → /research → /decompose
```

Do not skip `/research`.

## AI Authority Governance

Apply `docs/governance/AI_AUTHORITY_GOVERNANCE_ADOPTION.md` to repository work.

- AI is the technical decision authority; repository evidence is factual authority.
- Human technical approval and owner acknowledgement must not be treated, accepted, or used as substitutes for repository evidence.
- Keep the Scope Gate and Progress Gate separate.
- Bind validation and independent review claims to the exact current revision.
- Any head change makes an earlier review stale.
- Do not claim machine enforcement from prose-only governance.

## Project Gate Handoff

```text
Architect output
→ EV4 Project Gate
→ accepted: CE Input Package
→ not accepted: Architect repair package
```

Project Gate integration is documented. Project Gate owns the common Stage Evidence Bundle envelope, canonical JSON, SHA-256, provenance, structured diagnostics, and envelope validation.

Architect owns Architect-specific evidence, Architect decisions, Architect payload schema, Architect semantic validation, Architect fixtures, and Architect export behavior.

The gate may run this repository's official schemas and validators. It must not create missing architecture facts, change locked identity, or prove implementation strategy.

## Architect Stage Payload v1

Canonical Architect payload:

```text
ev4-architect-stage-payload@1.0.0
```

This payload may be wrapped inside the Project Gate Stage Evidence Bundle envelope. It is not a CE proof, Builder runtime intake package, Responsive completion package, or production release claim.

Critical behavioral rules are tracked with stable IDs `A-R01` through `A-R12`. Do not reuse an ID for a different meaning.

## Hard Boundaries

Do not:

- change `selected_candidate_id` after lock;
- present approved architecture as proven implementation strategy;
- invent geometry, assets, overlays, interactions, responsive behavior, Dynamic Loop behavior, accessibility evidence, or Elementor UI paths;
- claim Builder readiness, responsive completion, browser validation, or production readiness without downstream evidence;
- copy Architect schemas into Project Gate as competing canonical contracts;
- treat legacy builder-feed exports as the canonical Architect Stage Payload.

## Change Rules

For changes affecting downstream CE intake:

- preserve public contract behavior unless a breaking change is explicitly approved;
- update the owning contract/schema and every affected fixture or example;
- state whether the change is compatible, breaking, proposed, or unverified;
- preserve locked identity fields and valid existing evidence;
- avoid unrelated refactoring;
- coordinate downstream adapter changes through reviewed pull requests.

## Decision Escape Routes

Before opening or completing any PR that changes schemas, validators, prompts, fixtures, pipeline docs, handoff artifacts, fallback behavior, or decision-bearing outputs, review `planning/DECISION_ESCAPE_ROUTES.yml`.

Do not mark an escape route as resolved unless its `enforcement_status` meets the required threshold for its risk and `session_scope`. Do not mark a Critical cross-turn rule as resolved with single-artifact `ci_enforced`.

Do not add authored `resolved` or `production_ready` fields; those are derived audit conclusions.

## Validation

For Architect Stage Payload v1 changes, run:

```bash
python -m pip install 'jsonschema>=4.22.0' 'pytest>=8.0.0'
python scripts/check-architect-stage-payload.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_architect_stage_payload_validator.py
```

For bootstrap or first-run changes, run:

```bash
python scripts/check-architect-bootstrap.py
```

This repository does not yet have a universal validation entry point for every historical prompt-pack contract. Do not claim repository-wide validation unless it was actually executed.

For documentation-only changes, verify links, repository names, file paths, status labels, and cross-repository role descriptions against the current repository contents.

## Evidence and Reporting

Use explicit states such as:

```text
observed
validated
resolved
derived
proposed
unverified
insufficient_evidence
```

User-facing explanations may be Persian. Technical identifiers, paths, schema IDs, rule IDs, and diagnostic codes remain in English.

## Pull Requests

A PR should explain:

- the problem or contract change;
- files and boundaries affected;
- compatibility impact;
- validation actually executed;
- remaining unverified behavior or missing evidence.
