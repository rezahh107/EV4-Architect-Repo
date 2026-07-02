# AGENTS.md

## Scope

These instructions apply to the entire repository unless a closer nested `AGENTS.md` or `AGENTS.override.md` provides more specific guidance.

## Repository Role

`EV4-Architect-Repo` owns EV4 architecture decisions: visual intake, candidate generation and scoring, `selected_candidate_id`, approved structure and class intent, forbidden work, and the Architect handoff.

It does not prove constructability, execute Elementor actions, or claim responsive or production completion.

## Read First

1. `README.md`
2. `STATUS.md`
3. `02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md`
4. the relevant stage, contract, schema, fixture, and diagnostic files for the task

When sources conflict, follow the highest-authority current contract or explicit active override. Do not silently merge incompatible rules.

## Project Gate Handoff

```text
Architect output
→ EV4 Project Gate
→ accepted: CE Input Package
→ not accepted: Architect repair package
```

Project Gate integration is documented but the verifier and user interface are not implemented yet.

The gate may run this repository's official schemas and validators. It must not create missing architecture facts, change locked identity, or prove implementation strategy.

## Hard Boundaries

Do not:

- change `selected_candidate_id` after lock;
- present approved architecture as proven implementation strategy;
- invent geometry, assets, overlays, interactions, responsive behavior, Dynamic Loop behavior, accessibility evidence, or Elementor UI paths;
- claim Builder readiness, responsive completion, browser validation, or production readiness without downstream evidence;
- copy Architect schemas into Project Gate as competing canonical contracts.

## Change Rules

For changes affecting downstream CE intake:

- preserve public contract behavior unless a breaking change is explicitly approved;
- update the owning contract/schema and every affected fixture or example;
- state whether the change is compatible, breaking, proposed, or unverified;
- preserve locked identity fields and valid existing evidence;
- avoid unrelated refactoring;
- coordinate downstream adapter changes through reviewed pull requests.

## Validation

This repository currently has no root package or test command documented as a universal validation entry point. Use the exact validation instructions attached to the files or release package being changed, and do not claim repository-wide validation unless it was actually executed.

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
