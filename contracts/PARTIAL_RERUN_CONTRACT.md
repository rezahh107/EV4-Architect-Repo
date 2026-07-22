# Partial Rerun Contract

Status: active
Version: 1.1.0
Applies to: EV4 Architect stages after the first complete run, repair runs, and changed-input reruns

---

## Purpose

The pipeline must not require a full restart when only one input, constraint, candidate, score, or implementation detail changes.

A `PARTIAL RERUN` defines the earliest safe stage to restart from and the downstream stages that must be invalidated.

Core rule:

```text
Rerun from the earliest stage whose owned information changed.
Never reuse downstream payloads that depend on stale upstream facts.
```

---

## Required Inputs

A partial rerun may start only when these inputs are available:

- previous `STAGE ANCHOR`
- latest valid payload from the last completed stage
- changed input description
- affected scope
- requested target stage
- list of payloads the user wants to reuse

If the changed input is ambiguous, stop and ask one minimal clarifying question.

---

## Change Impact Matrix

| Changed item | Earliest safe rerun stage | Invalidates |
|---|---|---|
| New screenshot or visual reference | `/decompose` | `/architectures` onward |
| Meaningful content changes only | `/decompose` or `/build-tree` depending on whether visual grouping changes | downstream dependent stages |
| Project defaults or hard constraints change | `/intake` or `/architectures` depending on scope | downstream dependent stages |
| User approves or rejects third-party plugin | `/architectures` | `/score-evidence` onward |
| Stage 2 unknown resolved | `/architectures` if architecture affected; otherwise `/score-evidence` | affected downstream stages |
| Candidate architecture added/removed/edited | `/architectures` | `/score-evidence` onward |
| Rubric or scoring rule changes | `/score-evidence` | `/score-audit` onward |
| Arithmetic or scoring bug found | `/score-evidence` | `/score-audit` onward |
| Audit rule changes | `/score-audit` | `/recommend` onward |
| Tie preference or user priority changes | `/recommend` | `/build-tree` onward |
| Naming convention changes | `/build-tree` | `/implementation` onward |
| Widget implementation constraint changes | `/implementation` | `/final-audit` onward |

---

## Rerun Modes

### 1. Forward Rerun

Use when an upstream fact changed and downstream outputs must be regenerated.

```text
rerun_mode: forward_rerun
start_stage: [earliest affected stage]
invalidate_downstream: yes
```

### 2. Local Repair

Use when a stage output violated its own contract but upstream facts remain valid.

```text
rerun_mode: local_repair
start_stage: [failed stage]
invalidate_downstream: conditional
```

### 3. Score-Only Rerun

Use when architecture candidates are unchanged but scoring rules or arithmetic changed.

```text
rerun_mode: score_only_rerun
start_stage: /score-evidence
invalidate_downstream: /score-audit onward
```

### 4. Build-Only Rerun

Use when recommendation is stable but tree naming or structure output needs repair.

```text
rerun_mode: build_only_rerun
start_stage: /build-tree
invalidate_downstream: /implementation onward
```

---

## Repository Repair Escalation Boundary

Run repair and repository root-cause repair are separate.

Sequence:

```text
determine current Run repair route
→ invalidate dependent Run outputs
→ repair or stabilize the current Run
→ validate the current Run repair
→ classify repository recurrence risk
→ emit a separate Repository Repair Recommendation only when allowed
→ continue only from the valid repaired Anchor
```

Rules:

- A repository recommendation is evaluated only after the current Run repair plan is determined and the Run is stable as `repaired`, `blocked`, or `terminal`.
- Downstream outputs remain invalid until the current Run repair is validated.
- The repository recommendation does not change the earliest safe rerun stage.
- The repository recommendation does not replace a Repair Anchor, Success Anchor, Validation Bundle, or Partial Rerun plan.
- The active Architect Run must not edit repository files, create a repository branch, commit, push, or open a repository PR.
- A separate maintenance prompt may be emitted only under `contracts/REPOSITORY_REPAIR_RECOMMENDATION_HANDOFF.md`.
- The presence of a repository recommendation does not block a repaired and validated Run from continuing through its valid Anchor.
- A blocked Run remains blocked even when a repository recommendation is emitted.

---

## Reuse Rules

Allowed reuse:

- prior Stage 2 decomposition may be reused only if visual input and content semantics are unchanged;
- prior Stage 3 candidates may be reused only if Stage 2 unknowns and architecture constraints are unchanged;
- prior Stage 4 scores may be reused only if candidates, rubric, weights, N/A rules, and evidence labels are unchanged;
- prior Stage 5 audit may be reused only if Stage 4 payload and Stage 5 audit rules are unchanged;
- prior Stage 6 recommendation may be reused only if audit status, tie state, user priorities, and eligible candidate set are unchanged.

Forbidden reuse:

- do not reuse Stage 4 if Stage 3 changed;
- do not reuse Stage 5 if Stage 4 changed;
- do not reuse Stage 6 if Stage 5 changed;
- do not reuse Stage 7 if the selected candidate changed;
- do not reuse any stage output when the relevant payload schema changed.

---

## Required Partial Rerun Output

When a partial rerun is requested, output this before doing the rerun:

```text
PARTIAL RERUN PLAN

changed_input:
impact_class:
earliest_safe_start_stage:
stages_to_reuse:
stages_to_invalidate:
required_anchor:
required_payloads:
user_confirmation_required: yes | no
reason:
```

If `user_confirmation_required: yes`, stop after the plan and wait.

---

## Stage Anchor and Bundle Integration

The current `ev4-stage-anchor@1.4.0` carries this state under `handoff_state`:

```text
partial_rerun_state:
- reusable_until:
- invalidation_triggers:
- earliest_safe_rerun_stage:
- downstream_payloads_dependent_on_this_stage:
```

The Anchor is non-authorizing by itself. Its source Stage must be `full_transaction_implemented`, and the Anchor must be contained in an independently regenerated `ev4-architect-validation-bundle@1.2.0`. A blocked Validation Profile produces no Bundle and no continuation.

---

## Pass Criteria

A partial rerun plan passes only if:

- it identifies the earliest safe rerun stage;
- it names every downstream invalidated stage;
- it does not reuse stale payloads;
- it respects schema versions;
- it gives one minimal confirmation question when needed;
- it preserves Stage Anchor and Debug Trace continuity;
- it does not treat repository repair escalation as Run-repair authorization.
