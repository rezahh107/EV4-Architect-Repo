# EV4 Builder Companion Feed v1.1 Interactive Execution Patch

Status: active_patch_for_builder_companion_feed
Patch version: 1.1.0
Applies to: `release/EV4_PROJECT_RELEASE_PACK_v1/EV4_BUILDER_COMPANION_FEED_PROTOCOL.md`
Adds stage binding: `stages/11_BUILDER_FEED_EXPORT.md`
Language: Persian builder guidance, English technical identifiers allowed

---

## Purpose

This patch upgrades the Builder Companion Feed from a copy-ready handoff add-on into a stricter bridge for a separate interactive Elementor builder assistant chat.

It preserves the core rule of the v1.0 protocol:

```text
Create a builder feed from the audited handoff. Do not create a new design.
```

It adds operational guardrails extracted from the legacy interactive builder prompt that proved useful during real step-by-step Elementor work.

---

## Critic Findings Addressed

```yaml
critic_findings:
  - id: BCF-EXEC-001
    title: builder feed lacked explicit Approved Handoff Mode
    severity: medium
    resolution: added approved_handoff_mode contract

  - id: BCF-EXEC-002
    title: builder feed did not preserve live-interface precedence from legacy prompt
    severity: medium
    resolution: added live_interface_precedence and control_existence_failure_protocol

  - id: BCF-EXEC-003
    title: builder feed did not define session state for separate chats
    severity: medium
    resolution: added session_state_machine and Persian control triggers

  - id: BCF-EXEC-004
    title: builder feed did not constrain action batching for interactive execution
    severity: minor
    resolution: added step_size_contract with maximum six small related actions

  - id: BCF-EXEC-005
    title: builder feed needed stronger V3/V4 and Grid assumption guards
    severity: medium
    resolution: added v3_v4_separation_guard and no_grid_assumption
```

---

## Approved Handoff Mode

When a completed EV4 `/handoff-export` or `Builder_Context_Package` is supplied, the downstream assistant must start in `APPROVED_HANDOFF_MODE`.

```yaml
approved_handoff_mode:
  applies_when:
    - completed_handoff_export_available
    - Builder_Context_Package_available
  source_of_truth:
    - Builder_Context_Package
    - Handoff_Payload
    - Build_Tree_Payload
    - Implementation_Payload
    - Final_Audit_Payload
  must_not:
    - rerun_scoring
    - rerun_recommendation
    - redesign
    - change_selected_candidate
    - add_unapproved_classes
    - remove_approved_classes
    - reinterpret_medium_flags_as_resolved
    - resolve_unknowns_by_assumption
  may:
    - guide_interactive_elementor_build
    - apply_approved_classes
    - preserve_editability
    - ask_for_interface_screenshots
    - ask_for_frontend_validation
```

A completed handoff means the analysis stage has already occurred. The downstream assistant must not rerun first-response image analysis unless:

```text
- the user explicitly requests re-analysis;
- the reference image materially changed;
- the handoff is incompatible with current evidence;
- a confirmed Elementor interface limitation makes the approved implementation impossible.
```

---

## Live Interface Precedence

For the existence, name, location, or available values of an Elementor control, the downstream assistant must use this precedence:

```text
1. Latest user-provided Elementor interface screenshot
2. User direct statement about current interface behavior
3. Installed Elementor Core and Pro versions when provided
4. Official Elementor V4+ documentation applicable to that version
5. Current diagnostic evidence
6. Builder_Context_Package
7. Workbook or internal methodology
8. Previous assistant instruction
9. General CSS knowledge
10. Assumption
```

If the screenshot conflicts with documentation, the assistant must report:

```text
- what the current interface visibly shows;
- what the documentation says;
- the version or context difference, if established;
- the safe action for the user's installation.
```

The live interface is authoritative for what the builder can actually select.

---

## Control-Existence Failure Protocol

If the user reports that a control does not exist, or provides a screenshot that contradicts a builder instruction, the downstream assistant must stop and enter `CORRECTION_MODE`.

Required response:

```yaml
control_existence_failure_response:
  issue_status: confirmed
  unsupported_instruction:
  interface_evidence:
  dependent_later_actions:
  still_valid_work:
  revert_required:
  verified_replacement_path:
  wait_for_confirmation: true
```

Forbidden responses:

```text
- saying the control should exist;
- blaming cache, user error, or permissions without evidence;
- guessing a nearby control;
- continuing with downstream actions;
- silently changing the approved architecture.
```

---

## Session State Machine

The downstream builder chat must maintain exactly one current state:

```text
BUILD_ACTIVE
PAUSED
QUESTION_MODE
WAITING_FOR_CONFIRMATION
EVIDENCE_REQUIRED
CORRECTION_MODE
REVIEW_MODE
COMPLETED
```

It must also maintain a last verified checkpoint:

```yaml
last_verified_checkpoint:
  current_section:
  current_architecture_or_handoff:
  completed_elements:
  applied_classes:
  verified_settings:
  unconfirmed_settings:
  active_warnings:
  unresolved_evidence:
  last_completed_action:
  next_pending_action:
```

Questions, pauses, partial screenshots, or documentation discussion must not be treated as confirmation of the latest builder batch.

---

## Persian Control Triggers

The Builder Assistant must treat these Persian words as explicit session commands when they appear alone or at the beginning of a message followed by a colon.

```yaml
persian_control_triggers:
  توقف:
    state: PAUSED
    behavior: stop_new_builder_actions

  استارت:
    state: BUILD_ACTIVE
    behavior: resume_from_last_verified_checkpoint_if_safe

  ادامه:
    behavior: continue_next_uncompleted_builder_batch_only_if_previous_batch_confirmed_or_user_authorized

  تایید:
    behavior: mark_latest_completed_batch_as_user_confirmed_and_create_checkpoint

  اصلاح:
    state: CORRECTION_MODE
    behavior: stop_new_implementation_and_correct_only_affected_path

  بررسی:
    state: REVIEW_MODE
    behavior: inspect_only_provided_evidence_and_do_not_continue_automatically

  وضعیت:
    behavior: return_concise_state_report_only

  عقب:
    behavior: return_to_checkpoint_before_latest_unconfirmed_batch

  مستندات:
    behavior: verify_requested_behavior_using_official_Elementor_V4_plus_sources_only

  ریست:
    behavior: ask_reset_scope_before_resetting_anything

  خلاصه:
    behavior: return_continuation_oriented_summary_without_continuing
```

These commands are builder-session commands, not EV4 architecture pipeline stages.

---

## Step Size Contract

The default maximum implementation batch is six small actions.

```yaml
step_size_contract:
  default_max_actions: 6
  user_can_reduce_to: 1..6
  never_force_exactly_six: true
  stop_early_when_validation_needed: true
```

One action means one small UI operation or one tightly related setting group on the same selected element.

Allowed examples:

```text
- create one element;
- rename one element;
- apply one approved class;
- set Display and Direction together when both are verified and belong to the same element;
- add one child element and assign its content;
- duplicate one validated repeated item;
- update the page and inspect frontend.
```

Forbidden action compression:

```text
- build all cards, style them, make them responsive, and validate them in one action;
- create several nested structural levels and style them in one action;
- add an SVG, repair it, position it, and finalize accessibility in one action.
```

---

## Required Per-Element Instruction Contract

Whenever an element is created or edited, the downstream assistant must identify:

```text
1. Parent element
2. Elementor element type
3. V4/V3/shared/unverified category
4. Exact Structure Panel name
5. Exact active class
6. Whether the class is Local or Global
7. Exact panel path
8. Exact control name
9. Exact verified value or value evidence label
10. Properties that must remain unchanged
11. Expected position in the Structure Panel
```

Class-entry rule:

```text
Enter class names without a leading dot.
Correct: smart-home__feature-card--default
Wrong: .smart-home__feature-card--default
```

---

## Layout Completeness Checklist

For each layout element creation or edit, the downstream assistant should address each applicable item with one of these states: `Set to`, `Keep current default`, `Not applicable`, `Not visible in the current interface`, `Requires screenshot confirmation`, `Requires version confirmation`, or `Not yet determined`.

```text
Display
Direction
Wrap
Justify Content
Align Items
Width or Size
Height or Min Height
Position
Overflow
Gap
Padding
Margin
```

Do not assign a value merely to complete the list.

---

## V3/V4 Separation Guard

For every selected element, determine one of:

```text
V4 Atomic Element
V3 element
Shared compatibility element
Unverified element type
```

Forbidden:

```text
- using a V3 panel path for a V4 Atomic Element;
- using a V4 class workflow for a V3 element without compatibility evidence;
- calling a legacy Container an Atomic Flexbox;
- treating Div Block, Flexbox, Container, Section, Column, and Grid Container as interchangeable;
- assuming a control is shared between generations.
```

A hybrid page is valid. Preserve working V3 and V4 elements unless migration is explicitly requested.

---

## Explicit No-Grid Assumption

Do not instruct `Display: Grid` unless one of these is true:

```text
- Grid is visible in the current Elementor V4+ interface;
- the user explicitly confirms Grid is present;
- official V4+ documentation confirms Grid for the installed version and relevant element type.
```

The presence of a Grid concept, CSS Grid browser support, a legacy Grid Container, or an `e-grid` data node does not prove the current selected V4 element exposes a Grid option.

If Grid is unavailable, preserve the approved semantic architecture and request/inspect available V4+ layout controls before proposing a verified replacement.

---

## Numeric Value Evidence Labels

Every numeric recommendation must be labeled as one of:

```text
confirmed_implementation_value
explicit_reference_value
user_approved_value
official_documented_value
temporary_test_value
provisional_visual_recommendation
insufficient_evidence
```

Do not present an estimated screenshot measurement as an exact source value.

---

## Completion Gate Extension

Before declaring implementation complete, the downstream assistant must separately report:

```text
Structure completed
Classes applied
Desktop frontend checked
Tablet checked
Mobile checked
Accessibility semantics checked
SVG safety checked
Browser rendering checked
Real Elementor export checked
EDIS validation checked
Exact pixel matching checked
```

Use only:

```text
confirmed
not_checked
insufficient_evidence
not_applicable
```

Do not collapse these into a single generic completion claim.

---

## Patch Output Requirement

Any Builder Companion Feed generated after this patch must include:

```yaml
builder_companion_feed_v1_1_checks:
  approved_handoff_mode_exported: required
  live_interface_precedence_exported: required
  control_existence_failure_protocol_exported: required
  session_state_machine_exported: required
  persian_control_triggers_exported: required
  step_size_contract_exported: required
  per_element_instruction_contract_exported: required
  v3_v4_separation_guard_exported: required
  no_grid_assumption_exported: required
  completion_gate_extension_exported: required
```

If any required item is missing, the feed is incomplete and must be repaired before being used in a separate Builder Assistant chat.
