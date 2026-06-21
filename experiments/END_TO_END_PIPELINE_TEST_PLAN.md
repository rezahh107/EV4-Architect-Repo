# End-to-End Pipeline Test Plan

Status: draft_active
Version: 0.1.0
Applies to: validation before hardening later stages and before release packaging

---

## Purpose

The EV4 pipeline is now complex enough that theoretical hardening is not sufficient.

This test plan validates whether Stage Anchors, payloads, unknown propagation, scoring, audit, recommendation, and build-tree handoff work together on a real section.

Core rule:

```text
Do not trust the full pipeline until one real visual section completes a traceable run.
```

---

## Test Scope

Minimum first test:

```text
/intake
/decompose
/architectures
/score-evidence
/score-audit
/recommend
/build-tree
```

Optional extended test:

```text
/implementation
/final-audit
/handoff-export
```

---

## Required Test Inputs

Use one realistic section screenshot or mockup with:

- at least one repeated component group;
- at least one meaningful image or visual core;
- at least one decorative layer;
- at least one responsive risk;
- at least one unknown that should be carried forward.

A smart-home connector section is a good first stress test because it exercises content, visual core, connector decoration, overlay containment, and responsive risk.

---

## What To Measure

### 1. Anchor Quality

Check whether each Stage Anchor preserves:

- critical unknowns;
- blocking items;
- gate results;
- selected or active candidates;
- required user confirmations;
- target stage hardening status;
- confidence deltas.

### 2. Drift Control

Check whether Stage 5 and Stage 6 still reference Stage 2 unknowns correctly.

### 3. Repair Loop Cost

Track:

- number of reruns;
- where the first failure happened;
- whether repair routing identified the correct stage;
- whether partial rerun could avoid full restart.

### 4. Output Usability

Check whether Stage 7 produces a build tree that is:

- readable in Elementor Structure Panel;
- editable;
- normal-flow safe;
- wrapper-budget compliant;
- overlay-contained;
- ready for Stage 8.

---

## Test Output

Each test should produce:

```text
E2E TEST REPORT
- test_id:
- input_section_type:
- stages_completed:
- first_failure_stage:
- anchor_failures:
- unknown_propagation_result:
- scoring_audit_result:
- recommendation_result:
- build_tree_result:
- required_contract_changes:
- go_to_next_hardening_stage: yes | no
```

---

## Pass Criteria

The first end-to-end test passes only if:

- no stage starts without a valid anchor;
- unknowns do not disappear silently;
- Stage 4 does not convert `?` into numeric score;
- Stage 5 detects any scoring or gate issues;
- Stage 6 does not force a recommendation when tie/user input is required;
- Stage 7 keeps meaningful content editable and overlays contained;
- failure cases produce minimal repair routes instead of vague advice.

---

## Recommended Timing

Run the first test before finalizing Stage 8.

If Stage 8 is hardened before the test, run the test immediately after Stage 8 and before Stage 9.
