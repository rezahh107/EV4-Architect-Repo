from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

HANDOFF_SCHEMA = "ev4-repository-repair-recommendation-handoff@1.0.0"

ALLOWED_REPOSITORY_GAP_CLASSES = frozenset(
    {
        "repository_enforcement_gap",
        "contract_ambiguity",
        "validator_gap",
        "missing_negative_regression",
        "stage_boundary_escape_route",
        "conflicting_authorities",
        "fail_late_detection",
        "repeatable_prompt_or_protocol_defect",
    }
)
REPOSITORY_GAP_STATES = frozenset(
    {"confirmed", "probable", "possible", "insufficient_evidence", "not_repository_related"}
)
CURRENT_RUN_STATUSES = frozenset({"in_progress", "repairing", "repaired", "blocked", "terminal"})
CURRENT_RUN_REPAIR_STATUSES = frozenset({"validated", "pending", "failed", "not_applicable"})

# Closed compatibility relation. A stable repaired run is usable only after validation.
# A blocked run represents a failed repair; a terminal run has no applicable repair route.
_ALLOWED_REPAIR_STATUS_BY_RUN_STATUS = {
    "in_progress": frozenset({"pending"}),
    "repairing": frozenset({"pending"}),
    "repaired": frozenset({"validated"}),
    "blocked": frozenset({"failed"}),
    "terminal": frozenset({"not_applicable"}),
}

_REQUIRED_FIELDS = (
    "handoff_schema",
    "incident_id",
    "source_run_id",
    "current_run_status",
    "current_run_repair_status",
    "repository_gap_state",
    "repository_gap_class",
    "ordinary_run_error",
    "first_broken_stage",
    "first_detection_stage",
    "root_cause_summary",
    "repository_gap_hypothesis",
    "evidence_summary",
    "violated_or_weak_authorities",
    "recurrence_risk",
    "current_run_resume_stage",
    "repository_maintenance_scope",
    "forbidden_actions",
)

_REQUIRED_FORBIDDEN_ACTIONS = frozenset(
    {
        "modify_repository_inside_active_architect_run",
        "merge",
        "approve",
        "deploy",
        "modify_repository_settings",
    }
)

REQUIRED_PROMPT_SECTIONS = (
    "[ROLE]",
    "[TARGET REPOSITORY]",
    "[OBSERVED INCIDENT]",
    "[CURRENT-RUN EVIDENCE]",
    "[SUSPECTED REPOSITORY GAP]",
    "[UNCERTAINTIES]",
    "[REQUIRED LIVE REPOSITORY REVIEW]",
    "[SOLUTION COMPARISON REQUIREMENT]",
    "[SELECTION CRITERIA]",
    "[BOUNDED IMPLEMENTATION AUTHORITY]",
    "[NON-GOALS]",
    "[VALIDATION REQUIREMENTS]",
    "[DRAFT PR REQUIREMENT]",
    "[INDEPENDENT REVIEW REQUIREMENT]",
    "[FINAL RESPONSE FORMAT]",
    "[STOP CONDITIONS]",
)

_REQUIRED_PROMPT_MARKERS = (
    "source_run_id:",
    "current_run_repair_status:",
    "repository_gap_state:",
    "repository_gap_class:",
    "Evaluate the Scope Gate from current repository evidence.",
    "Revalidate the live default branch",
    "Verify the exact current Head",
    "fresh independent exact-Head review",
    "merge_performed: false",
    "approval_performed: false",
    "deployment_performed: false",
)


@dataclass(frozen=True)
class ValidatedHandoffRecord:
    handoff_schema: str
    incident_id: str
    source_run_id: str
    current_run_status: str
    current_run_repair_status: str
    repository_gap_state: str
    repository_gap_class: str
    ordinary_run_error: bool
    first_broken_stage: str
    first_detection_stage: str
    root_cause_summary: str
    repository_gap_hypothesis: str
    evidence_summary: tuple[str, ...]
    violated_or_weak_authorities: tuple[str, ...]
    recurrence_risk: str
    current_run_resume_stage: str
    repository_maintenance_scope: str
    forbidden_actions: tuple[str, ...]
    target_repository: str
    default_branch: str
    observed_revision: str
    uncertainties: tuple[str, ...]


@dataclass(frozen=True)
class RecordValidationResult:
    status: str
    reason_code: str
    record: ValidatedHandoffRecord | None = None


@dataclass(frozen=True)
class EligibilityResult:
    status: str
    reason_code: str
    record: ValidatedHandoffRecord | None = None


@dataclass(frozen=True)
class PromptValidationResult:
    status: str
    reason_code: str


class HandoffValidationError(ValueError):
    pass


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> tuple[str, ...] | None:
    if not isinstance(value, list) or not value:
        return None
    if not all(_nonempty_string(item) for item in value):
        return None
    return tuple(item.strip() for item in value)


def validate_repository_repair_handoff_record(record: Mapping[str, Any]) -> RecordValidationResult:
    if not isinstance(record, Mapping):
        return RecordValidationResult("invalid_input", "record_not_mapping")

    if "standalone_repair_prompt" in record:
        return RecordValidationResult("invalid_input", "pre_rendered_prompt_forbidden")

    for field in _REQUIRED_FIELDS:
        if field not in record:
            return RecordValidationResult("invalid_input", f"missing_required_field:{field}")

    if record["handoff_schema"] != HANDOFF_SCHEMA:
        return RecordValidationResult("invalid_input", "invalid_handoff_schema")

    scalar_fields = (
        "incident_id",
        "source_run_id",
        "first_broken_stage",
        "first_detection_stage",
        "root_cause_summary",
        "repository_gap_hypothesis",
        "recurrence_risk",
        "current_run_resume_stage",
        "repository_maintenance_scope",
    )
    for field in scalar_fields:
        if not _nonempty_string(record[field]):
            return RecordValidationResult("invalid_input", f"invalid_string_field:{field}")

    run_status = record["current_run_status"]
    repair_status = record["current_run_repair_status"]
    gap_state = record["repository_gap_state"]
    gap_class = record["repository_gap_class"]

    if run_status not in CURRENT_RUN_STATUSES:
        return RecordValidationResult("invalid_input", "unknown_current_run_status")
    if repair_status not in CURRENT_RUN_REPAIR_STATUSES:
        return RecordValidationResult("invalid_input", "unknown_current_run_repair_status")
    if repair_status not in _ALLOWED_REPAIR_STATUS_BY_RUN_STATUS[run_status]:
        return RecordValidationResult("invalid_input", "contradictory_run_repair_status")
    if gap_state not in REPOSITORY_GAP_STATES:
        return RecordValidationResult("invalid_input", "unknown_repository_gap_state")

    if gap_state in {"confirmed", "probable", "possible"}:
        if gap_class not in ALLOWED_REPOSITORY_GAP_CLASSES:
            return RecordValidationResult("invalid_input", "unknown_repository_gap_class")
    elif gap_class != "unknown":
        return RecordValidationResult("invalid_input", "gap_class_must_be_unknown_for_non_repository_state")

    if not isinstance(record["ordinary_run_error"], bool):
        return RecordValidationResult("invalid_input", "ordinary_run_error_not_boolean")

    evidence_summary = _string_list(record["evidence_summary"])
    if evidence_summary is None:
        return RecordValidationResult("invalid_input", "invalid_evidence_summary")
    weak_authorities = _string_list(record["violated_or_weak_authorities"])
    if weak_authorities is None:
        return RecordValidationResult("invalid_input", "invalid_violated_or_weak_authorities")
    forbidden_actions = _string_list(record["forbidden_actions"])
    if forbidden_actions is None:
        return RecordValidationResult("invalid_input", "invalid_forbidden_actions")
    if not _REQUIRED_FORBIDDEN_ACTIONS.issubset(forbidden_actions):
        return RecordValidationResult("invalid_input", "missing_required_forbidden_action")

    resume_stage = record["current_run_resume_stage"].strip()
    if run_status == "repaired" and resume_stage == "none":
        return RecordValidationResult("invalid_input", "repaired_run_requires_resume_stage")
    if run_status in {"blocked", "terminal"} and resume_stage != "none":
        return RecordValidationResult("invalid_input", "non_resumable_run_requires_none_resume_stage")

    target_repository = record.get("target_repository", "unknown")
    default_branch = record.get("default_branch", "unknown")
    observed_revision = record.get("observed_revision", "unknown")
    for field, value in (
        ("target_repository", target_repository),
        ("default_branch", default_branch),
        ("observed_revision", observed_revision),
    ):
        if not _nonempty_string(value):
            return RecordValidationResult("invalid_input", f"invalid_string_field:{field}")

    uncertainties_value = record.get("uncertainties", ["unknown repository details must be revalidated"])
    uncertainties = _string_list(uncertainties_value)
    if uncertainties is None:
        return RecordValidationResult("invalid_input", "invalid_uncertainties")

    validated = ValidatedHandoffRecord(
        handoff_schema=HANDOFF_SCHEMA,
        incident_id=record["incident_id"].strip(),
        source_run_id=record["source_run_id"].strip(),
        current_run_status=run_status,
        current_run_repair_status=repair_status,
        repository_gap_state=gap_state,
        repository_gap_class=gap_class,
        ordinary_run_error=record["ordinary_run_error"],
        first_broken_stage=record["first_broken_stage"].strip(),
        first_detection_stage=record["first_detection_stage"].strip(),
        root_cause_summary=record["root_cause_summary"].strip(),
        repository_gap_hypothesis=record["repository_gap_hypothesis"].strip(),
        evidence_summary=evidence_summary,
        violated_or_weak_authorities=weak_authorities,
        recurrence_risk=record["recurrence_risk"].strip(),
        current_run_resume_stage=resume_stage,
        repository_maintenance_scope=record["repository_maintenance_scope"].strip(),
        forbidden_actions=forbidden_actions,
        target_repository=target_repository.strip(),
        default_branch=default_branch.strip(),
        observed_revision=observed_revision.strip(),
        uncertainties=uncertainties,
    )
    return RecordValidationResult("valid", "record_valid", validated)


def _evaluate_validated_record(record: ValidatedHandoffRecord) -> EligibilityResult:
    if record.current_run_status not in {"repaired", "blocked", "terminal"}:
        return EligibilityResult("not_eligible", "current_run_not_stable", record)
    if record.ordinary_run_error:
        return EligibilityResult("not_eligible", "ordinary_run_error", record)
    if record.repository_gap_state == "possible":
        return EligibilityResult("not_eligible", "possible_review_suggestion_only", record)
    if record.repository_gap_state == "insufficient_evidence":
        return EligibilityResult("not_eligible", "insufficient_repository_evidence", record)
    if record.repository_gap_state == "not_repository_related":
        return EligibilityResult("not_eligible", "not_repository_related", record)
    return EligibilityResult("eligible", "full_handoff_allowed", record)


def evaluate_repository_repair_handoff_eligibility(record: Mapping[str, Any]) -> EligibilityResult:
    validation = validate_repository_repair_handoff_record(record)
    if validation.status != "valid" or validation.record is None:
        if validation.reason_code == "contradictory_run_repair_status":
            return EligibilityResult("not_eligible", validation.reason_code)
        return EligibilityResult("invalid_input", validation.reason_code)
    return _evaluate_validated_record(validation.record)


def _bullet_lines(values: tuple[str, ...]) -> str:
    return "\n".join(f"- {value}" for value in values)


def render_repository_maintenance_prompt(record: ValidatedHandoffRecord) -> str:
    if not isinstance(record, ValidatedHandoffRecord):
        raise TypeError("render_repository_maintenance_prompt requires ValidatedHandoffRecord")

    eligibility = _evaluate_validated_record(record)
    if eligibility.status != "eligible":
        raise HandoffValidationError(f"handoff not eligible: {eligibility.reason_code}")

    prompt = f"""[ROLE]
Act as the bounded repository-maintenance implementer and independent root-cause verifier for the target repository.

[TARGET REPOSITORY]
repository: {record.target_repository}
default_branch: {record.default_branch}
observed_revision: {record.observed_revision}

[OBSERVED INCIDENT]
incident_id: {record.incident_id}
source_run_id: {record.source_run_id}
current_run_status: {record.current_run_status}
current_run_repair_status: {record.current_run_repair_status}
first_broken_stage: {record.first_broken_stage}
first_detection_stage: {record.first_detection_stage}
root_cause_summary: {record.root_cause_summary}

[CURRENT-RUN EVIDENCE]
evidence_summary:
{_bullet_lines(record.evidence_summary)}
violated_or_weak_authorities:
{_bullet_lines(record.violated_or_weak_authorities)}
current_run_resume_stage: {record.current_run_resume_stage}
Do not request hidden chain-of-thought and do not assume access to the original Architect conversation.

[SUSPECTED REPOSITORY GAP]
repository_gap_state: {record.repository_gap_state}
repository_gap_class: {record.repository_gap_class}
repository_gap_hypothesis: {record.repository_gap_hypothesis}
recurrence_risk: {record.recurrence_risk}
The incident description is evidence to investigate, not an authoritative diagnosis. Verify or reject it from live repository evidence.

[UNCERTAINTIES]
{_bullet_lines(record.uncertainties)}
Unknown repository facts must remain unknown or visible placeholders. Do not invent repository names, SHAs, PR numbers, paths, Schema IDs, Validator IDs, Workflow names, tests, or evidence.

[REQUIRED LIVE REPOSITORY REVIEW]
1. Revalidate the live default branch.
2. Verify the exact current Head before modifying anything.
3. Inspect current AGENTS.md, STATUS.md, active overrides, governance files, contracts, schemas, validators, diagnostics, fixtures, tests, workflows, and open pull requests.
4. Evaluate the Scope Gate from current repository evidence.
5. Stop for conflicting authorities, materially equivalent open work, insufficient Scope evidence, unknown repository identity, or required broad redesign.

[SOLUTION COMPARISON REQUIREMENT]
Identify at least two materially different repair options when credible alternatives exist. Do not blindly implement the incident hypothesis.

[SELECTION CRITERIA]
Compare effectiveness, failure-detection timing, determinism, scope, compatibility, implementation cost, maintenance burden, AIGOV alignment, and overengineering risk. Select the smallest complete solution supported by live evidence.

[BOUNDED IMPLEMENTATION AUTHORITY]
Only after the Scope Gate is authorized, implement the bounded repair on one focused branch. Preserve existing roles, Stage IDs, contracts, historical evidence, and downstream boundaries. Create at most one bounded Draft PR. Do not merge or approve. Do not deploy or modify repository settings.
repository_maintenance_scope: {record.repository_maintenance_scope}
forbidden_actions:
{_bullet_lines(record.forbidden_actions)}

[NON-GOALS]
Do not redesign the pipeline, add self-healing behavior, add automatic diagnosis or repository repair, create a new Stage or repair mode, introduce a generalized orchestration framework, or alter unrelated repositories.

[VALIDATION REQUIREMENTS]
Run targeted tests, relevant regressions, deterministic negative cases, git diff --check, and applicable Python/JSON/YAML validation. Report exact commands and exact observed results. Do not claim runtime enforcement from prose, fixtures, or CI alone.

[DRAFT PR REQUIREMENT]
If implementation is authorized and validated, update or open at most one bounded Draft PR. Never merge, approve, enable auto-merge, deploy, release, or modify repository settings.

[INDEPENDENT REVIEW REQUIREMENT]
After the final Head is known, request a fresh independent exact-Head review. Any Head change makes the earlier review stale.

[FINAL RESPONSE FORMAT]
Return repository and live base SHA, resulting Head SHA, Scope Gate result, selected solution, rejected alternatives, files changed, exact validation commands/results, Draft PR, enforcement achieved/not achieved, remaining evidence gaps, and:
merge_performed: false
approval_performed: false
deployment_performed: false

[STOP CONDITIONS]
Stop without repository modification for conflicting authorities, overlapping equivalent work, unauthorized or insufficient Scope, unknown repository identity, a required new Stage or downstream contract, a generalized orchestration requirement, automatic repository editing, or any proposal that authorizes the active Architect Run to edit its own repository.
"""

    validation = validate_rendered_repository_maintenance_prompt(prompt)
    if validation.status != "valid":
        raise AssertionError(f"renderer produced invalid prompt: {validation.reason_code}")
    return prompt


def validate_rendered_repository_maintenance_prompt(prompt: str) -> PromptValidationResult:
    if not isinstance(prompt, str) or not prompt:
        return PromptValidationResult("invalid_prompt", "prompt_empty")

    positions: list[int] = []
    for section in REQUIRED_PROMPT_SECTIONS:
        position = prompt.find(section)
        if position < 0:
            return PromptValidationResult("invalid_prompt", f"missing_section:{section}")
        positions.append(position)
    if positions != sorted(positions):
        return PromptValidationResult("invalid_prompt", "section_order_invalid")

    for marker in _REQUIRED_PROMPT_MARKERS:
        if marker not in prompt:
            return PromptValidationResult("invalid_prompt", f"missing_marker:{marker}")

    return PromptValidationResult("valid", "prompt_valid")
