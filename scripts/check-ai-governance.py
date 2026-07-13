#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import re
import shlex
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "planning/ai-governance-coverage.schema.json"
COVERAGE = ROOT / "planning/AI_GOVERNANCE_COVERAGE.yml"
VALID = ROOT / "fixtures/ai-governance/valid/cases.json"
INVALID = ROOT / "fixtures/ai-governance/invalid/cases.json"
WORKFLOWS = ROOT / ".github/workflows"

EXPECTED = {
    "AIGOV-START-001": ("Critical", "per_session", "validator_backed"),
    "AIGOV-EVIDENCE-001": ("Critical", "per_artifact", "ci_enforced"),
    "AIGOV-SECURITY-PROFILE-001": ("High", "cross_turn", "validator_backed"),
    "AIGOV-HUMAN-001": ("High", "per_artifact", "validator_backed"),
    "AIGOV-COACH-001": ("High", "per_artifact", "validator_backed"),
}
RULE_FIXTURE_TYPES = {
    "AIGOV-START-001": "startup_session",
    "AIGOV-EVIDENCE-001": "evidence_claim",
    "AIGOV-SECURITY-PROFILE-001": "security_profile_fixture",
    "AIGOV-HUMAN-001": "approval_contract",
    "AIGOV-COACH-001": "coach_critique",
}
LADDER = [
    "prose_only",
    "schema_backed",
    "validator_backed",
    "fixture_tested",
    "advisory_ci_observed",
    "ci_enforced",
    "sequence_ci_enforced",
    "runtime_monitor_enforced",
    "os_harness_enforced",
    "downstream_contract_enforced",
]
FACTUAL = {
    "REPOSITORY_CONFIRMED",
    "TOOL_CONFIRMED",
    "SOURCE_CONFIRMED",
    "TEST_CONFIRMED",
    "CI_CONFIRMED",
    "RUNTIME_CONFIRMED",
    "PUBLICATION_RECEIPT_CONFIRMED",
    "PERFORMANCE_RECEIPT_CONFIRMED",
}
OUTCOME_KINDS = {
    "readiness",
    "repository_state",
    "merge_status",
    "ci_status",
    "runtime_status",
}
STATE_FOR_SOURCE = {
    "repository": "REPOSITORY_CONFIRMED",
    "tool": "TOOL_CONFIRMED",
    "source": "SOURCE_CONFIRMED",
    "test": "TEST_CONFIRMED",
    "ci": "CI_CONFIRMED",
    "runtime": "RUNTIME_CONFIRMED",
    "publication_receipt": "PUBLICATION_RECEIPT_CONFIRMED",
    "performance_receipt": "PERFORMANCE_RECEIPT_CONFIRMED",
    "ai_review_signal": "AI_REVIEW_SIGNAL",
    "coach_critique": "AI_REVIEW_SIGNAL",
    "ai_technical_decision": "AI_TECHNICAL_DECISION",
    "user_stated_input": "USER_STATED_INPUT",
    "assumption": "ASSUMED",
    "unknown": "UNKNOWN",
}
MIN_CONTROLS = {
    "immutable_action_pins",
    "minimum_explicit_permissions",
    "exact_head_checkout_when_repository_is_checked_out",
    "persist_credentials_false",
    "fail_closed_head_identity",
    "no_pull_request_secret_exposure",
}
ACCEPTED_PUBLIC_PROFILE = "personal_public_repository_minimum"
HUMAN_INVARIANT = (
    "Human technical approval and owner acknowledgement must not be treated, "
    "accepted, or used as substitutes for repository evidence."
)
MERGE_INVARIANT = (
    "The user may perform the administrative Merge action after a valid technical "
    "recommendation; that action is not technical approval and does not prove correctness."
)
EXACT_HEAD_REF = "${{ github.event.pull_request.head.sha }}"
EXACT_HEAD_WORDS = ["test", "$(git rev-parse HEAD)", "=", EXACT_HEAD_REF]
REMOTE_ACTION_SHA = re.compile(r"^[^@\s]+@[0-9a-fA-F]{40}$")
DOCKER_ACTION_DIGEST = re.compile(r"^docker://[^@\s]+@sha256:[0-9a-fA-F]{64}$")
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$", re.DOTALL)
SAFE_PROOF_SHELLS = {"bash", "sh"}
GITHUB_WORKSPACE_REF = "$" + "{{ github.workspace }}"
SAFE_ROOT_WORKING_DIRECTORIES = {".", "./", GITHUB_WORKSPACE_REF}
SAFE_TEST_INLINE_ENV = {
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    "PYTEST_ADDOPTS": "",
    "PYTEST_PLUGINS": "",
}
CI_PROOF_SURFACE_PATHS = {
    "scripts/_proof_surface_probe.py",
    "tests/_proof_surface_probe.py",
    ".github/actions/_proof_surface/action.yml",
    "pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini", "conftest.py",
}
FORBIDDEN_PROOF_ENV_KEYS = {
    "PATH",
    "PYTHONPATH",
    "BASH_ENV",
    "ENV",
}
SECRET_REFERENCE = re.compile(
    r"(?:\bsecrets\.[A-Za-z_][A-Za-z0-9_]*"
    r"|\bsecrets\s*\[\s*['\"][^'\"]+['\"]\s*\]"
    r"|\btoJSON\s*\(\s*secrets\s*\))",
    re.IGNORECASE,
)
FORBIDDEN_SHELL_SYNTAX = (
    "&&",
    "||",
    ";",
    "|",
    "<<",
    ">>",
    "`",
    "$(",
    "${",
    "(",
    ")",
    "{",
    "}",
    "<",
    ">",
    "&",
)


class GitHubActionsLoader(yaml.SafeLoader):
    """YAML loader that preserves GitHub Actions keys such as `on` as strings."""


GitHubActionsLoader.yaml_implicit_resolvers = {
    key: list(value) for key, value in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
for first_char, resolvers in list(GitHubActionsLoader.yaml_implicit_resolvers.items()):
    GitHubActionsLoader.yaml_implicit_resolvers[first_char] = [
        (tag, expression)
        for tag, expression in resolvers
        if tag != "tag:yaml.org,2002:bool"
    ]
GitHubActionsLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|false)$", re.IGNORECASE),
    list("tTfF"),
)


@dataclass(frozen=True)
class Diagnostic:
    code: str
    path: str
    message: str


def j(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def y(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


read_json = j
read_yaml = y


def ep(error: Any) -> str:
    output = "$"
    for part in error.absolute_path:
        output += f"[{part}]" if isinstance(part, int) else f".{part}"
    return output


def artifact_schema(schema: dict[str, Any], kind: str) -> dict[str, Any]:
    names = {
        "startup_session": "startup_session",
        "evidence_claim": "evidence_claim",
        "security_profile_fixture": "security_profile_fixture",
        "approval_contract": "approval_contract",
        "coach_critique": "coach_critique",
    }
    if kind not in names:
        raise KeyError(f"unknown fixture_type: {kind}")
    return {
        "$schema": schema["$schema"],
        "$ref": f"#/$defs/{names[kind]}",
        "$defs": schema["$defs"],
    }


def validate_startup_session(
    payload: dict[str, Any], path: str = "$"
) -> list[Diagnostic]:
    required = {
        "README.md",
        "STATUS.md",
        "docs/governance/AI_AUTHORITY_GOVERNANCE_ADOPTION.md",
        "02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md",
    }
    output: list[Diagnostic] = []
    if not required.issubset(set(payload.get("authority_files_inspected") or [])):
        output.append(
            Diagnostic(
                "AIGOV-START-001_MISSING_AUTHORITY_EVIDENCE",
                path,
                "startup evidence must include the required repository authorities",
            )
        )
    if not payload.get("authorized_work") or payload.get("dependencies_checked") is not True:
        output.append(
            Diagnostic(
                "AIGOV-START-001_INCOMPLETE_STARTUP_GATE",
                path,
                "authorized work and dependency verification are required",
            )
        )
    return output


def validate_evidence_claim(
    payload: dict[str, Any], path: str = "$"
) -> list[Diagnostic]:
    output: list[Diagnostic] = []
    state = payload.get("evidence_state")
    source = payload.get("source_type")
    source_reference = payload.get("source_reference")
    self_asserted = payload.get("self_asserted_outcome") is True

    if payload.get("unknown_input") is True and state not in {
        "UNKNOWN",
        "BLOCKED_INSUFFICIENT_EVIDENCE",
    }:
        output.append(
            Diagnostic(
                "AIGOV-EVIDENCE-001_UNKNOWN_AS_FACT",
                path,
                "unknown input must remain unknown",
            )
        )
    if source in {"ai_review_signal", "coach_critique"} and state in FACTUAL:
        output.append(
            Diagnostic(
                "AIGOV-EVIDENCE-001_AI_SIGNAL_AS_FACT",
                path,
                "AI critique cannot be factual proof",
            )
        )
    if self_asserted:
        output.append(
            Diagnostic(
                "AIGOV-EVIDENCE-001_SELF_ASSERTED_OUTCOME",
                path,
                "self-authored outcomes are invalid regardless of source label",
            )
        )

    expected_state = STATE_FOR_SOURCE.get(source)
    if expected_state and state not in {
        expected_state,
        "BLOCKED_INSUFFICIENT_EVIDENCE",
        "NOT_APPLICABLE",
    }:
        output.append(
            Diagnostic(
                "AIGOV-EVIDENCE-001_SOURCE_STATE_MISMATCH",
                path,
                f"{source!r} is incompatible with {state!r}",
            )
        )

    has_reference = isinstance(source_reference, str) and bool(source_reference.strip())
    if state in FACTUAL and not has_reference:
        output.append(
            Diagnostic(
                "AIGOV-EVIDENCE-001_MISSING_SOURCE_REFERENCE",
                path,
                "factual states require a non-empty source reference",
            )
        )

    if payload.get("claim_kind") in OUTCOME_KINDS and not self_asserted:
        if state not in FACTUAL:
            output.append(
                Diagnostic(
                    "AIGOV-EVIDENCE-001_OUTCOME_NOT_FACTUAL",
                    path,
                    "externally evidenced outcomes require a compatible factual evidence state",
                )
            )
        if not has_reference and not any(
            item.code == "AIGOV-EVIDENCE-001_MISSING_SOURCE_REFERENCE"
            for item in output
        ):
            output.append(
                Diagnostic(
                    "AIGOV-EVIDENCE-001_MISSING_SOURCE_REFERENCE",
                    path,
                    "externally evidenced outcomes require a non-empty source reference",
                )
            )
    return output


def validate_security_profile(
    payload: dict[str, Any], path: str = "$"
) -> list[Diagnostic]:
    output: list[Diagnostic] = []
    if payload.get("repository_visibility") == "public":
        profile = payload.get("active_profile")
        if not profile:
            return [
                Diagnostic(
                    "AIGOV-SECURITY-PROFILE-001_MISSING_PROFILE",
                    path,
                    "public repository requires an active profile",
                )
            ]
        if profile != ACCEPTED_PUBLIC_PROFILE:
            return [
                Diagnostic(
                    "AIGOV-SECURITY-PROFILE-001_UNSUPPORTED_PROFILE",
                    path,
                    f"unsupported public-repository profile: {profile!r}",
                )
            ]
        if not MIN_CONTROLS.issubset(set(payload.get("minimum_controls") or [])):
            output.append(
                Diagnostic(
                    "AIGOV-SECURITY-PROFILE-001_MINIMUM_CONTROL_MISSING",
                    path,
                    "minimum control missing",
                )
            )
        if payload.get("enterprise_controls_status") != "intentionally_out_of_scope":
            output.append(
                Diagnostic(
                    "AIGOV-SECURITY-PROFILE-001_ENTERPRISE_SCOPE_AMBIGUOUS",
                    path,
                    "enterprise scope must be explicit",
                )
            )
    return output


def validate_approval_contract(
    payload: dict[str, Any], path: str = "$"
) -> list[Diagnostic]:
    invalid = (
        payload.get("human_technical_approval_required") is True
        or payload.get("owner_acknowledgement_used_as_evidence") is True
        or payload.get("user_merge_action_role") != "administrative_action"
    )
    if invalid:
        return [
            Diagnostic(
                "AIGOV-HUMAN-001_APPROVAL_AS_EVIDENCE",
                path,
                "human approval cannot substitute for evidence",
            )
        ]
    return []


def validate_coach_critique(
    payload: dict[str, Any], path: str = "$"
) -> list[Diagnostic]:
    invalid = (
        payload.get("evidence_state") != "AI_REVIEW_SIGNAL"
        or payload.get("claims_technical_truth") is True
        or payload.get("claims_real_world_outcome") is True
    )
    if invalid:
        return [
            Diagnostic(
                "AIGOV-COACH-001_CRITIQUE_AS_FACT",
                path,
                "coach critique must remain an AI_REVIEW_SIGNAL",
            )
        ]
    return []


FIXTURE_VALIDATORS = {
    "startup_session": validate_startup_session,
    "evidence_claim": validate_evidence_claim,
    "security_profile_fixture": validate_security_profile,
    "approval_contract": validate_approval_contract,
    "coach_critique": validate_coach_critique,
}


def carrier_path(value: str | None) -> str | None:
    if value is None:
        return None
    return value.split(" / ", 1)[0].split("::", 1)[0].split("#", 1)[0]


def load_actions_yaml(text: str) -> dict[str, Any]:
    document = yaml.load(text, Loader=GitHubActionsLoader)
    if not isinstance(document, dict):
        raise ValueError("workflow must be a YAML mapping")
    return document


def workflow_events(document: dict[str, Any]) -> set[str]:
    trigger = document.get("on")
    if isinstance(trigger, str):
        return {trigger}
    if isinstance(trigger, list):
        return {item for item in trigger if isinstance(item, str)}
    if isinstance(trigger, dict):
        return {str(item) for item in trigger}
    return set()


def workflow_event_configuration(
    document: dict[str, Any], event: str
) -> dict[str, Any] | None:
    trigger = document.get("on")
    if not isinstance(trigger, dict) or event not in trigger:
        return None
    configuration = trigger[event]
    return configuration if isinstance(configuration, dict) else None


def is_pr_workflow(text: str) -> bool:
    try:
        events = workflow_events(load_actions_yaml(text))
    except (yaml.YAMLError, ValueError):
        return False
    return bool({"pull_request", "pull_request_target"} & events)


def _permission_is_minimal(value: Any) -> bool:
    return isinstance(value, dict) and value == {"contents": "read"}


def _is_remote_action(target: str) -> bool:
    return not target.startswith(("./", "docker://"))


def _is_docker_action(target: str) -> bool:
    return target.startswith("docker://")


def _is_local_action(target: str) -> bool:
    return target.startswith("./")


def _proof_job_execution_context_is_trusted(job: Any) -> bool:
    return isinstance(job, dict) and "container" not in job and "services" not in job


def _is_checkout(target: str) -> bool:
    return target.split("@", 1)[0].lower() == "actions/checkout"


def _persist_credentials_disabled(value: Any) -> bool:
    return value is False or (
        isinstance(value, str) and value.strip().lower() == "false"
    )


def _condition_is_provably_active(value: Any) -> bool:
    if value is None or value is True:
        return True
    if not isinstance(value, str):
        return False
    normalized = " ".join(value.strip().split()).lower()
    return normalized in {"true", "${{ true }}"}


def _continue_on_error_disabled(value: Any) -> bool:
    if value is None or value is False:
        return True
    return isinstance(value, str) and value.strip().lower() == "false"


def _proof_node_is_blocking(node: Any) -> bool:
    return (
        isinstance(node, dict)
        and _condition_is_provably_active(node.get("if"))
        and _continue_on_error_disabled(node.get("continue-on-error"))
    )


def _shell_is_posix(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = " ".join(value.strip().split())
    return normalized in SAFE_PROOF_SHELLS


def _run_defaults(node: Any) -> dict[str, Any]:
    if not isinstance(node, dict):
        return {}
    defaults = node.get("defaults")
    if not isinstance(defaults, dict):
        return {}
    run = defaults.get("run")
    return run if isinstance(run, dict) else {}


def _proof_step_shell_is_supported(
    step: Any, job: dict[str, Any], document: dict[str, Any]
) -> bool:
    if not isinstance(step, dict):
        return False
    explicit = step.get("shell")
    if explicit is not None:
        return _shell_is_posix(explicit)
    inherited = _run_defaults(job).get(
        "shell", _run_defaults(document).get("shell")
    )
    if inherited is not None:
        return _shell_is_posix(inherited)
    runs_on = job.get("runs-on")
    return isinstance(runs_on, str) and runs_on.startswith("ubuntu-")


def _proof_working_directory_is_root(
    step: Any, job: dict[str, Any], document: dict[str, Any]
) -> bool:
    if not isinstance(step, dict):
        return False
    inherited = _run_defaults(job).get(
        "working-directory",
        _run_defaults(document).get("working-directory"),
    )
    effective = step.get("working-directory", inherited)
    if effective is None:
        return True
    return (
        isinstance(effective, str)
        and effective.strip() in SAFE_ROOT_WORKING_DIRECTORIES
    )


def _normalized_env_mapping(value: Any) -> dict[str, str] | None:
    if value is None:
        return {}
    if not isinstance(value, dict):
        return None
    output: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(
            item, (str, int, float, bool)
        ):
            return None
        output[key] = str(item)
    return output


def _proof_yaml_environment_is_empty(
    step: Any, job: dict[str, Any], document: dict[str, Any]
) -> bool:
    for node in (document, job, step):
        if not isinstance(node, dict):
            return False
        environment = _normalized_env_mapping(node.get("env"))
        if environment is None or environment:
            return False
    return True


def _shell_words(line: str) -> list[str]:
    try:
        return shlex.split(line, comments=True, posix=True)
    except ValueError:
        return []


def _meaningful_command_lines(run: Any) -> list[str]:
    if not isinstance(run, str):
        return []
    return [
        line.strip()
        for line in run.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _single_command_line(run: Any) -> str | None:
    lines = _meaningful_command_lines(run)
    if len(lines) != 1:
        return None
    return lines[0]


def _is_fail_closed_exact_head_command(run: Any) -> bool:
    line = _single_command_line(run)
    if line is None:
        return False
    words = tuple(_shell_words(line))
    return words in {
        tuple(EXACT_HEAD_WORDS),
        tuple(["[", *EXACT_HEAD_WORDS[1:], "]"]),
        tuple(["[[", *EXACT_HEAD_WORDS[1:], "]]" ]),
    }


def _contains_exact_head_assertion(
    step: Any, job: dict[str, Any], document: dict[str, Any]
) -> bool:
    return (
        _proof_node_is_blocking(step)
        and _proof_job_execution_context_is_trusted(job)
        and isinstance(step, dict)
        and _proof_step_shell_is_supported(step, job, document)
        and _proof_working_directory_is_root(step, job, document)
        and _proof_yaml_environment_is_empty(step, job, document)
        and _is_fail_closed_exact_head_command(step.get("run"))
    )


def _secret_exposure_paths(value: Any, path: str = "$") -> list[str]:
    output: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if str(key).lower() == "secrets" and isinstance(item, str):
                if item.strip().lower() == "inherit":
                    output.append(child_path)
            output.extend(_secret_exposure_paths(item, child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            output.extend(_secret_exposure_paths(item, f"{path}[{index}]"))
    elif isinstance(value, str) and SECRET_REFERENCE.search(value):
        output.append(path)
    return output


def _resolve_local_workflow(target: str, root: Path) -> tuple[Path, str] | None:
    if not target.startswith("./") or "@" in target:
        return None
    candidate = (root / target[2:]).resolve()
    root_resolved = root.resolve()
    try:
        relative = candidate.relative_to(root_resolved).as_posix()
    except ValueError:
        return None
    if not relative.startswith(".github/workflows/"):
        return None
    if candidate.suffix not in {".yml", ".yaml"}:
        return None
    return candidate, relative


def _resolve_local_action(target: str, root: Path) -> tuple[Path, str] | None:
    if not _is_local_action(target) or "@" in target:
        return None
    directory = (root / target[2:]).resolve()
    try:
        relative_dir = directory.relative_to(root.resolve()).as_posix()
    except ValueError:
        return None
    if not relative_dir.startswith(".github/actions/") or not directory.is_dir():
        return None
    candidates = [p for p in (directory / "action.yml", directory / "action.yaml") if p.is_file()]
    if len(candidates) != 1:
        return None
    return candidates[0], candidates[0].relative_to(root.resolve()).as_posix()


def _validate_action_reference(
    target: str, path: str, root: Path, stack: tuple[str, ...] = ()
) -> list[Diagnostic]:
    if _is_docker_action(target):
        if DOCKER_ACTION_DIGEST.fullmatch(target):
            return []
        return [Diagnostic(
            "AIGOV-SECURITY-PROFILE-001_MUTABLE_DOCKER_ACTION", path,
            f"Docker action must use an immutable sha256 digest: {target}",
        )]
    if _is_remote_action(target):
        if REMOTE_ACTION_SHA.fullmatch(target):
            return []
        return [Diagnostic(
            "AIGOV-SECURITY-PROFILE-001_MUTABLE_ACTION_REF", path,
            f"mutable action ref: {target}",
        )]
    resolved = _resolve_local_action(target, root)
    if resolved is None:
        return [Diagnostic(
            "AIGOV-SECURITY-PROFILE-001_LOCAL_ACTION_INVALID", path,
            f"unsupported or missing local action: {target}",
        )]
    action_file, relative = resolved
    if relative in stack:
        return [Diagnostic(
            "AIGOV-SECURITY-PROFILE-001_LOCAL_ACTION_CYCLE", path,
            f"local action cycle detected: {' -> '.join((*stack, relative))}",
        )]
    try:
        document = load_actions_yaml(action_file.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError, ValueError) as exc:
        return [Diagnostic(
            "AIGOV-SECURITY-PROFILE-001_LOCAL_ACTION_INVALID", path,
            f"local action cannot be parsed: {exc}",
        )]
    output = [
        Diagnostic(
            "AIGOV-SECURITY-PROFILE-001_PR_SECRET_EXPOSURE",
            f"{relative}:{secret_path}",
            "direct PR secret exposure is forbidden in local actions",
        )
        for secret_path in _secret_exposure_paths(document)
    ]
    runs = document.get("runs")
    if not isinstance(runs, dict) or runs.get("using") != "composite":
        return output + [Diagnostic(
            "AIGOV-SECURITY-PROFILE-001_LOCAL_ACTION_INVALID", relative,
            "local PR actions must be composite actions",
        )]
    action_steps = runs.get("steps")
    if not isinstance(action_steps, list):
        return output + [Diagnostic(
            "AIGOV-SECURITY-PROFILE-001_LOCAL_ACTION_INVALID", relative,
            "local composite action must define a steps list",
        )]
    current = (*stack, relative)
    for index, step in enumerate(action_steps):
        step_path = f"{relative}::runs.steps[{index}]"
        if not isinstance(step, dict):
            output.append(Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_LOCAL_ACTION_INVALID", step_path,
                "local composite step must be a mapping",
            ))
            continue
        nested = step.get("uses")
        if isinstance(nested, str):
            if _is_checkout(nested):
                output.append(Diagnostic(
                    "AIGOV-SECURITY-PROFILE-001_LOCAL_ACTION_INVALID", step_path,
                    "repository checkout must remain a direct workflow step",
                ))
            output.extend(_validate_action_reference(nested, f"{step_path}.uses", root, current))
        elif "run" in step:
            output.append(Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_LOCAL_ACTION_RUN_UNBOUNDED", step_path,
                "local composite run steps are outside the active bounded profile",
            ))
        else:
            output.append(Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_LOCAL_ACTION_INVALID", step_path,
                "local composite step must contain a uses reference",
            ))
    return output


def validate_workflow_document(
    path: str,
    document: dict[str, Any],
    root: Path = ROOT,
    *,
    inherited_pr_context: bool = False,
    inherited_permissions: Any = None,
    stack: tuple[str, ...] = (),
) -> list[Diagnostic]:
    events = workflow_events(document)
    pr_context = inherited_pr_context or bool(
        {"pull_request", "pull_request_target"} & events
    )
    if not pr_context:
        return []

    normalized_path = Path(path).as_posix()
    if normalized_path in stack:
        return [
            Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_REUSABLE_WORKFLOW_CYCLE",
                normalized_path,
                f"local reusable workflow cycle detected: {' -> '.join((*stack, normalized_path))}",
            )
        ]
    current_stack = (*stack, normalized_path)
    output: list[Diagnostic] = []

    if inherited_pr_context and "workflow_call" not in events:
        output.append(
            Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_LOCAL_REUSABLE_WORKFLOW_INVALID",
                normalized_path,
                "a local reusable workflow reached from a PR job must declare workflow_call",
            )
        )
    if "pull_request_target" in events:
        output.append(
            Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_PULL_REQUEST_TARGET_FORBIDDEN",
                normalized_path,
                "pull_request_target is unsupported by the active public-repository profile",
            )
        )

    jobs = document.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        return output + [
            Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_WORKFLOW_STRUCTURE_INVALID",
                normalized_path,
                "PR-context workflow must define jobs",
            )
        ]

    workflow_permissions = document.get("permissions", inherited_permissions)
    for job_id, job in jobs.items():
        job_path = f"{normalized_path}::jobs.{job_id}"
        if not isinstance(job, dict):
            output.append(
                Diagnostic(
                    "AIGOV-SECURITY-PROFILE-001_WORKFLOW_STRUCTURE_INVALID",
                    job_path,
                    "job must be a mapping",
                )
            )
            continue

        effective_permissions = job.get("permissions", workflow_permissions)
        if not _permission_is_minimal(effective_permissions):
            output.append(
                Diagnostic(
                    "AIGOV-SECURITY-PROFILE-001_PERMISSIONS_NOT_MINIMAL",
                    job_path,
                    "effective permissions must be exactly contents: read",
                )
            )

        if not _proof_job_execution_context_is_trusted(job):
            output.append(Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_UNTRUSTED_JOB_RUNTIME", job_path,
                "PR proof jobs must not declare container or services",
            ))

        reusable_target = job.get("uses")
        if isinstance(reusable_target, str):
            if not _proof_node_is_blocking(job):
                output.append(
                    Diagnostic(
                        "AIGOV-SECURITY-PROFILE-001_PROOF_NOT_BLOCKING",
                        job_path,
                        "a PR-context reusable-workflow job must be unconditionally active and blocking",
                    )
                )
            if _is_remote_action(reusable_target):
                if not REMOTE_ACTION_SHA.fullmatch(reusable_target):
                    output.append(
                        Diagnostic(
                            "AIGOV-SECURITY-PROFILE-001_MUTABLE_ACTION_REF",
                            f"{job_path}.uses",
                            f"mutable reusable workflow ref: {reusable_target}",
                        )
                    )
            else:
                resolved = _resolve_local_workflow(reusable_target, root)
                if resolved is None:
                    output.append(
                        Diagnostic(
                            "AIGOV-SECURITY-PROFILE-001_LOCAL_REUSABLE_WORKFLOW_INVALID",
                            f"{job_path}.uses",
                            f"unsupported local reusable workflow target: {reusable_target}",
                        )
                    )
                else:
                    local_path, relative = resolved
                    if not local_path.is_file():
                        output.append(
                            Diagnostic(
                                "AIGOV-SECURITY-PROFILE-001_LOCAL_REUSABLE_WORKFLOW_INVALID",
                                f"{job_path}.uses",
                                f"local reusable workflow not found: {relative}",
                            )
                        )
                    else:
                        try:
                            local_document = load_actions_yaml(
                                local_path.read_text(encoding="utf-8")
                            )
                        except (OSError, yaml.YAMLError, ValueError) as exc:
                            output.append(
                                Diagnostic(
                                    "AIGOV-SECURITY-PROFILE-001_LOCAL_REUSABLE_WORKFLOW_INVALID",
                                    f"{job_path}.uses",
                                    f"local reusable workflow cannot be parsed: {exc}",
                                )
                            )
                        else:
                            output.extend(
                                validate_workflow_document(
                                    relative,
                                    local_document,
                                    root,
                                    inherited_pr_context=True,
                                    inherited_permissions=effective_permissions,
                                    stack=current_stack,
                                )
                            )

        steps = job.get("steps")
        if steps is None:
            continue
        if not isinstance(steps, list):
            output.append(
                Diagnostic(
                    "AIGOV-SECURITY-PROFILE-001_WORKFLOW_STRUCTURE_INVALID",
                    f"{job_path}.steps",
                    "steps must be a list",
                )
            )
            continue

        checkout_indexes: list[int] = []
        for index, step in enumerate(steps):
            step_path = f"{job_path}.steps[{index}]"
            if not isinstance(step, dict):
                output.append(
                    Diagnostic(
                        "AIGOV-SECURITY-PROFILE-001_WORKFLOW_STRUCTURE_INVALID",
                        step_path,
                        "step must be a mapping",
                    )
                )
                continue
            target = step.get("uses")
            if isinstance(target, str):
                output.extend(_validate_action_reference(target, f"{step_path}.uses", root))
                if _is_checkout(target):
                    checkout_indexes.append(index)
                    with_values = (
                        step.get("with")
                        if isinstance(step.get("with"), dict)
                        else {}
                    )
                    if with_values.get("ref") != EXACT_HEAD_REF:
                        output.append(
                            Diagnostic(
                                "AIGOV-SECURITY-PROFILE-001_NOT_EXACT_HEAD",
                                step_path,
                                "every repository checkout must use the exact PR head",
                            )
                        )
                    if not _persist_credentials_disabled(
                        with_values.get("persist-credentials")
                    ):
                        output.append(
                            Diagnostic(
                                "AIGOV-SECURITY-PROFILE-001_CREDENTIAL_PERSISTENCE",
                                step_path,
                                "every repository checkout must disable credential persistence",
                            )
                        )

        if checkout_indexes and not _proof_node_is_blocking(job):
            output.append(
                Diagnostic(
                    "AIGOV-SECURITY-PROFILE-001_PROOF_NOT_BLOCKING",
                    job_path,
                    "a checkout-bearing PR job must be unconditionally active and blocking",
                )
            )

        for position, checkout_index in enumerate(checkout_indexes):
            next_checkout = (
                checkout_indexes[position + 1]
                if position + 1 < len(checkout_indexes)
                else len(steps)
            )
            if not any(
                _contains_exact_head_assertion(step, job, document)
                for step in steps[checkout_index + 1 : next_checkout]
            ):
                output.append(
                    Diagnostic(
                        "AIGOV-SECURITY-PROFILE-001_HEAD_ASSERTION_MISSING",
                        f"{job_path}.steps[{checkout_index}]",
                        "each checkout requires a later unconditional blocking exact-head assertion before another checkout",
                    )
                )

    for secret_path in _secret_exposure_paths(document):
        output.append(
            Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_PR_SECRET_EXPOSURE",
                f"{normalized_path}:{secret_path}",
                "direct PR secret exposure is forbidden",
            )
        )
    return output


def validate_workflow_text(
    path: str, text: str, root: Path = ROOT
) -> list[Diagnostic]:
    try:
        document = load_actions_yaml(text)
    except (yaml.YAMLError, ValueError) as exc:
        return [
            Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_WORKFLOW_YAML_INVALID",
                path,
                str(exc),
            )
        ]
    return validate_workflow_document(path, document, root)


def validate_workflows(root: Path = ROOT) -> list[Diagnostic]:
    workflows = root / ".github/workflows"
    if not workflows.exists():
        return [
            Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_WORKFLOW_DIRECTORY_MISSING",
                str(workflows.relative_to(root)),
                "workflow directory missing",
            )
        ]
    output: list[Diagnostic] = []
    for path in sorted(workflows.glob("*.y*ml")):
        output.extend(
            validate_workflow_text(
                str(path.relative_to(root)),
                path.read_text(encoding="utf-8"),
                root,
            )
        )
    return output


def _resolve_json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise KeyError("JSON Pointer must start with '/'")
    current = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise KeyError(part)
    return current


def _verify_schema_carrier(
    value: Any, root: Path
) -> tuple[bool, list[Diagnostic]]:
    if not isinstance(value, str) or "#" not in value:
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_SCHEMA_POINTER_INVALID",
                "$",
                "schema carrier must include a JSON Pointer",
            )
        ]
    file_name, pointer = value.split("#", 1)
    path = root / file_name
    if not path.is_file():
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_MISSING_CARRIER",
                "$",
                f"missing {file_name}",
            )
        ]
    try:
        _resolve_json_pointer(j(path), pointer)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        json.JSONDecodeError,
    ) as exc:
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_SCHEMA_POINTER_INVALID",
                "$",
                f"invalid schema carrier {value!r}: {exc}",
            )
        ]
    return True, []


def _module_symbols(tree: ast.AST) -> dict[str, ast.AST]:
    symbols: dict[str, ast.AST] = {}
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols[node.name] = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    symbols[target.id] = node
    return symbols


def _symbol_exists(tree: ast.AST, symbol: str) -> bool:
    parts = symbol.split(".")
    current = _module_symbols(tree).get(parts[0])
    if current is None:
        return False
    for part in parts[1:]:
        if not isinstance(current, ast.ClassDef):
            return False
        current = _module_symbols(current).get(part)
        if current is None:
            return False
    return True


def _verify_validator_rule(
    value: Any, root: Path
) -> tuple[bool, list[Diagnostic]]:
    if not isinstance(value, str) or "::" not in value:
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_VALIDATOR_SYMBOL_MISSING",
                "$",
                "validator rule must use path::symbol",
            )
        ]
    file_name, symbol = value.split("::", 1)
    path = root / file_name
    if path.suffix != ".py" or not path.is_file():
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_VALIDATOR_SYMBOL_MISSING",
                "$",
                f"validator Python file missing: {file_name}",
            )
        ]
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_VALIDATOR_SYMBOL_MISSING",
                "$",
                f"validator cannot be inspected: {exc}",
            )
        ]
    if not symbol or not _symbol_exists(tree, symbol):
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_VALIDATOR_SYMBOL_MISSING",
                "$",
                f"validator symbol not found: {value}",
            )
        ]
    return True, []


def validate_fixture_case(
    schema: dict[str, Any], case: dict[str, Any], index: int
) -> list[Diagnostic]:
    kind = case.get("fixture_type")
    payload = case.get("payload")
    path = f"$.cases[{index}]"
    try:
        validator = Draft202012Validator(artifact_schema(schema, kind))
    except KeyError as exc:
        return [Diagnostic("AIGOV-FIXTURE-001_UNKNOWN_TYPE", path, str(exc))]
    output = [
        Diagnostic(
            "AIGOV-FIXTURE-001_SCHEMA_INVALID",
            f"{path}{ep(error)[1:]}",
            error.message,
        )
        for error in sorted(
            validator.iter_errors(payload),
            key=lambda item: (ep(item), item.message),
        )
    ]
    return output if output else FIXTURE_VALIDATORS[kind](payload, path)


def _verify_fixture_carrier(
    value: Any,
    root: Path,
    schema: dict[str, Any],
    rule_id: str,
    expect_invalid: bool,
) -> tuple[bool, list[Diagnostic]]:
    if not isinstance(value, str):
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_FIXTURE_CASE_MISSING",
                "$",
                "fixture carrier is missing",
            )
        ]
    path = root / value
    if not path.is_file():
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_MISSING_CARRIER",
                "$",
                f"missing {value}",
            )
        ]
    try:
        cases = j(path).get("cases")
    except (OSError, AttributeError, json.JSONDecodeError) as exc:
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_FIXTURE_CASE_MISSING",
                "$",
                f"fixture file cannot be inspected: {exc}",
            )
        ]
    fixture_type = RULE_FIXTURE_TYPES[rule_id]
    applicable = [
        (index, case)
        for index, case in enumerate(cases or [])
        if isinstance(case, dict) and case.get("fixture_type") == fixture_type
    ]
    if expect_invalid:
        applicable = [
            (index, case)
            for index, case in applicable
            if case.get("expected_diagnostic", "").startswith(rule_id)
        ]
        verified = any(
            case.get("expected_diagnostic")
            in {
                item.code
                for item in validate_fixture_case(schema, case, index)
            }
            for index, case in applicable
        )
    else:
        verified = any(
            not validate_fixture_case(schema, case, index)
            for index, case in applicable
        )
    if not verified:
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_FIXTURE_CASE_MISSING",
                "$",
                f"{value} lacks an applicable {'invalid' if expect_invalid else 'valid'} case for {rule_id}",
            )
        ]
    return True, []


def _workflow_paths_cover(
    document: dict[str, Any],
    event: str,
    authoritative_paths: set[str],
) -> tuple[bool, set[str]]:
    configuration = workflow_event_configuration(document, event)
    if configuration is None:
        return True, set()
    raw_paths = configuration.get("paths")
    ignored = configuration.get("paths-ignore")
    ignored_patterns = (
        [ignored] if isinstance(ignored, str) else list(ignored or [])
    )
    if raw_paths is None:
        missed = {
            path
            for path in authoritative_paths
            if any(fnmatch.fnmatch(path, pattern) for pattern in ignored_patterns)
        }
        return not missed, missed
    patterns = [raw_paths] if isinstance(raw_paths, str) else list(raw_paths or [])
    missed = {
        path
        for path in authoritative_paths
        if not any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
    }
    return not missed, missed


def _split_environment_assignments(
    words: list[str],
) -> tuple[dict[str, str] | None, list[str]]:
    assignments: dict[str, str] = {}
    index = 0
    while index < len(words) and ENV_ASSIGNMENT.fullmatch(words[index]):
        key, value = words[index].split("=", 1)
        if key in assignments:
            return None, []
        assignments[key] = value
        index += 1
    return assignments, words[index:]


def _simple_shell_command(
    run: Any,
) -> tuple[dict[str, str] | None, list[str]]:
    line = _single_command_line(run)
    if line is None:
        return None, []
    if any(token in line for token in FORBIDDEN_SHELL_SYNTAX):
        return None, []
    return _split_environment_assignments(_shell_words(line))


def _inline_environment_is_safe(
    assignments: dict[str, str] | None, *, for_tests: bool
) -> bool:
    if assignments is None:
        return False
    if FORBIDDEN_PROOF_ENV_KEYS & set(assignments):
        return False
    if not assignments:
        return True
    return for_tests and assignments == SAFE_TEST_INLINE_ENV


def _words_execute_validator(words: list[str], validator_file: str) -> bool:
    return (
        len(words) == 4
        and Path(words[0]).name in {"python", "python3"}
        and words[1:3] == ["-I", "-P"]
        and words[3] == validator_file
    )


def _words_execute_tests(
    words: list[str], test_file: str = "tests/test_ai_governance.py"
) -> bool:
    if not words or Path(words[0]).name not in {"python", "python3"}:
        return False
    return tuple(words[1:]) in {
        ("-I", "-P", "-m", "pytest", "-c", "/dev/null", "--noconftest", "-q", test_file),
        ("-I", "-P", "-m", "pytest", "-c", "/dev/null", "--noconftest", "--quiet", test_file),
    }


def _step_executes_applicable_command(
    step: dict[str, Any],
    validator_file: str,
    job: dict[str, Any] | None = None,
    document: dict[str, Any] | None = None,
) -> bool:
    if not _proof_node_is_blocking(step):
        return False
    if job is None or document is None:
        return False
    if not _proof_job_execution_context_is_trusted(job):
        return False
    if not _proof_step_shell_is_supported(step, job, document):
        return False
    if not _proof_working_directory_is_root(step, job, document):
        return False
    if not _proof_yaml_environment_is_empty(step, job, document):
        return False
    assignments, words = _simple_shell_command(step.get("run"))
    if _words_execute_validator(words, validator_file):
        return _inline_environment_is_safe(assignments, for_tests=False)
    if _words_execute_tests(words):
        return _inline_environment_is_safe(assignments, for_tests=True)
    return False


def _verify_ci_step(
    value: Any,
    root: Path,
    rule: dict[str, Any],
) -> tuple[bool, list[Diagnostic]]:
    if not isinstance(value, str):
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                "CI step is missing",
            )
        ]
    parts = value.split(" / ")
    if len(parts) != 3:
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                "CI step must use workflow / job / step",
            )
        ]
    workflow_name, job_name, step_name = parts
    workflow_path = root / workflow_name
    if not workflow_path.is_file():
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                f"workflow missing: {workflow_name}",
            )
        ]
    try:
        document = load_actions_yaml(workflow_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError, ValueError) as exc:
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                f"workflow cannot be parsed: {exc}",
            )
        ]

    if validate_workflow_document(workflow_name, document, root):
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                "CI workflow fails structural security validation",
            )
        ]
    if "pull_request" not in workflow_events(document):
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                "CI workflow must have a pull_request trigger",
            )
        ]

    jobs = document.get("jobs") or {}
    job = jobs.get(job_name) if isinstance(jobs, dict) else None
    if not isinstance(job, dict):
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                f"job not found: {job_name}",
            )
        ]
    if not _proof_node_is_blocking(job):
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                "CI carrier job must be unconditionally active and blocking",
            )
        ]

    steps = job.get("steps")
    step = next(
        (
            item
            for item in steps or []
            if isinstance(item, dict) and item.get("name") == step_name
        ),
        None,
    )
    if not isinstance(step, dict):
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                f"step not found: {step_name}",
            )
        ]
    if not _proof_node_is_blocking(step):
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                "CI carrier step must be unconditionally active and blocking",
            )
        ]

    validator_reference = (rule.get("carriers") or {}).get("validator_rule")
    validator_file = (
        validator_reference.split("::", 1)[0]
        if isinstance(validator_reference, str)
        else ""
    )
    if not validator_file or not _step_executes_applicable_command(
        step, validator_file, job, document
    ):
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                "named CI step does not execute an allowed blocking validator or test command",
            )
        ]

    carriers = rule.get("carriers") or {}
    authoritative_paths = {
        "planning/AI_GOVERNANCE_COVERAGE.yml",
        "tests/test_ai_governance.py",
    } | CI_PROOF_SURFACE_PATHS
    for carrier_value in carriers.values():
        path_value = carrier_path(carrier_value)
        if path_value:
            authoritative_paths.add(path_value)
    covered, missed = _workflow_paths_cover(
        document,
        "pull_request",
        authoritative_paths,
    )
    if not covered:
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_PATH_FILTER_MISSING",
                "$",
                f"CI path filters do not cover: {sorted(missed)}",
            )
        ]
    return True, []


def _verify_prose_source(
    value: Any, root: Path
) -> tuple[bool, list[Diagnostic]]:
    path_value = carrier_path(value) if isinstance(value, str) else None
    if path_value and (root / path_value).is_file():
        return True, []
    return False, [
        Diagnostic(
            "AIGOV-COVERAGE-001_MISSING_CARRIER",
            "$",
            f"missing {path_value or value}",
        )
    ]


def verify_rule_carriers(
    rule: dict[str, Any],
    schema: dict[str, Any],
    root: Path = ROOT,
) -> tuple[set[str], list[Diagnostic]]:
    rule_id = rule.get("rule_id")
    carriers = rule.get("carriers") or {}
    verified: set[str] = set()
    diagnostics: list[Diagnostic] = []
    checks = {
        "prose_source": lambda value: _verify_prose_source(value, root),
        "schema_carrier": lambda value: _verify_schema_carrier(value, root),
        "validator_rule": lambda value: _verify_validator_rule(value, root),
        "valid_fixture": lambda value: _verify_fixture_carrier(
            value,
            root,
            schema,
            rule_id,
            False,
        ),
        "invalid_fixture": lambda value: _verify_fixture_carrier(
            value,
            root,
            schema,
            rule_id,
            True,
        ),
        "CI_step": lambda value: _verify_ci_step(value, root, rule),
    }
    for name, check in checks.items():
        value = carriers.get(name)
        if value is None:
            continue
        passed, found = check(value)
        if passed:
            verified.add(name)
        else:
            diagnostics.extend(
                Diagnostic(item.code, f"$.carriers.{name}", item.message)
                for item in found
            )
    return verified, diagnostics


def max_status(carriers: dict[str, Any], verified_carriers: set[str]) -> str:
    if "downstream_contract" in verified_carriers:
        return "downstream_contract_enforced"
    if "sequence_test" in verified_carriers:
        return "sequence_ci_enforced"
    if "CI_step" in verified_carriers:
        return "ci_enforced"
    if {"valid_fixture", "invalid_fixture"}.issubset(verified_carriers):
        return "fixture_tested"
    if "validator_rule" in verified_carriers:
        return "validator_backed"
    if "schema_carrier" in verified_carriers:
        return "schema_backed"
    return "prose_only"


def validate_coverage_semantics(
    coverage: dict[str, Any],
    schema: dict[str, Any] | None = None,
    root: Path = ROOT,
) -> list[Diagnostic]:
    output: list[Diagnostic] = []
    rules = coverage.get("rules") or []
    by_id = {
        rule.get("rule_id"): (index, rule)
        for index, rule in enumerate(rules)
        if isinstance(rule, dict)
    }
    if set(by_id) != set(EXPECTED):
        output.append(
            Diagnostic(
                "AIGOV-COVERAGE-001_RULE_SET_MISMATCH",
                "$.rules",
                "required rule set mismatch",
            )
        )
    if schema is None:
        schema = j(root / "planning/ai-governance-coverage.schema.json")

    for rule_id, (risk, session_scope, minimum) in EXPECTED.items():
        found = by_id.get(rule_id)
        if not found:
            continue
        index, rule = found
        path = f"$.rules[{index}]"
        for field, expected_value in (
            ("risk", risk),
            ("session_scope", session_scope),
            ("minimum_required_status", minimum),
        ):
            if rule.get(field) != expected_value:
                output.append(
                    Diagnostic(
                        "AIGOV-COVERAGE-001_RULE_IDENTITY_MISMATCH",
                        path,
                        f"{field} must be {expected_value!r}",
                    )
                )

        status = (rule.get("status") or {}).get("enforcement_status")
        if status in LADDER and LADDER.index(status) < LADDER.index(minimum):
            output.append(
                Diagnostic(
                    "AIGOV-COVERAGE-001_BELOW_MINIMUM",
                    path,
                    f"{status} below {minimum}",
                )
            )

        verified, carrier_diagnostics = verify_rule_carriers(rule, schema, root)
        output.extend(
            Diagnostic(
                item.code,
                f"{path}{item.path[1:]}" if item.path.startswith("$") else path,
                item.message,
            )
            for item in carrier_diagnostics
        )
        proven = max_status(rule.get("carriers") or {}, verified)
        if status in LADDER and LADDER.index(status) > LADDER.index(proven):
            output.append(
                Diagnostic(
                    "AIGOV-COVERAGE-001_OVERCLAIMED_STATUS",
                    path,
                    f"{status} exceeds verified carrier status {proven}",
                )
            )

    profile = coverage.get("security_profile") or {}
    output.extend(
        validate_security_profile(
            {
                "repository_visibility": profile.get("repository_visibility"),
                "active_profile": profile.get("profile_id"),
                "minimum_controls": profile.get("minimum_controls") or [],
                "enterprise_controls_status": (
                    profile.get("enterprise_controls") or {}
                ).get("status"),
            },
            "$.security_profile",
        )
    )
    return output


def validate_authority_sources(root: Path = ROOT) -> list[Diagnostic]:
    agents_path = root / "AGENTS.md"
    policy_path = root / "docs/governance/AI_AUTHORITY_GOVERNANCE_ADOPTION.md"
    agents = agents_path.read_text(encoding="utf-8")
    policy = policy_path.read_text(encoding="utf-8")
    order = [
        "`README.md`",
        "`STATUS.md`",
        "`docs/governance/AI_AUTHORITY_GOVERNANCE_ADOPTION.md`",
        "`02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md`",
    ]
    positions = [agents.find(item) for item in order]
    output: list[Diagnostic] = []
    if any(position < 0 for position in positions) or positions != sorted(
        positions
    ):
        output.append(
            Diagnostic(
                "AIGOV-START-001_AUTHORITY_ORDER_INVALID",
                "AGENTS.md#Read First",
                "authority startup order invalid",
            )
        )
    for source_path, text in ((agents_path, agents), (policy_path, policy)):
        if HUMAN_INVARIANT not in text:
            output.append(
                Diagnostic(
                    "AIGOV-HUMAN-001_INVARIANT_MISSING",
                    str(source_path.relative_to(root)),
                    "human evidence invariant missing",
                )
            )
    if MERGE_INVARIANT not in policy:
        output.append(
            Diagnostic(
                "AIGOV-HUMAN-001_MERGE_BOUNDARY_MISSING",
                str(policy_path.relative_to(root)),
                "administrative Merge boundary missing",
            )
        )
    return output


def validate_fixtures(
    schema: dict[str, Any], root: Path = ROOT
) -> list[Diagnostic]:
    valid_path = root / "fixtures/ai-governance/valid/cases.json"
    invalid_path = root / "fixtures/ai-governance/invalid/cases.json"
    output: list[Diagnostic] = []
    for index, case in enumerate(j(valid_path).get("cases", [])):
        found = validate_fixture_case(schema, case, index)
        if found:
            output.append(
                Diagnostic(
                    "AIGOV-FIXTURE-001_VALID_CASE_REJECTED",
                    f"{valid_path.relative_to(root)}::{case.get('case_id')}",
                    "; ".join(item.code for item in found),
                )
            )
    for index, case in enumerate(j(invalid_path).get("cases", [])):
        found_codes = {
            item.code for item in validate_fixture_case(schema, case, index)
        }
        if case.get("expected_diagnostic") not in found_codes:
            output.append(
                Diagnostic(
                    "AIGOV-FIXTURE-001_INVALID_CASE_NOT_REJECTED",
                    f"{invalid_path.relative_to(root)}::{case.get('case_id')}",
                    f"got {sorted(found_codes)}",
                )
            )
    return output


def validate_repository(root: Path = ROOT) -> dict[str, Any]:
    schema_path = root / "planning/ai-governance-coverage.schema.json"
    coverage_path = root / "planning/AI_GOVERNANCE_COVERAGE.yml"
    schema = j(schema_path)
    coverage = y(coverage_path)
    Draft202012Validator.check_schema(schema)
    output = [
        Diagnostic(
            "AIGOV-COVERAGE-001_SCHEMA_INVALID",
            ep(error),
            error.message,
        )
        for error in sorted(
            Draft202012Validator(schema).iter_errors(coverage),
            key=lambda item: (ep(item), item.message),
        )
    ]
    if not output:
        output.extend(validate_coverage_semantics(coverage, schema, root))
    output.extend(validate_authority_sources(root))
    output.extend(validate_workflows(root))
    output.extend(validate_fixtures(schema, root))
    workflows = root / ".github/workflows"
    return {
        "status": "passed" if not output else "failed",
        "diagnostics": [asdict(item) for item in output],
        "validated_rules": sorted(EXPECTED),
        "workflow_count": (
            len(list(workflows.glob("*.y*ml")))
            if workflows.exists()
            else 0
        ),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = validate_repository()
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif result["status"] == "passed":
        print(f"ok: {COVERAGE.relative_to(ROOT)}")
        print(f"validated_rules: {len(result['validated_rules'])}")
        print(f"workflows_inspected: {result['workflow_count']}")
        print("fixture_failures: 0")
    else:
        for item in result["diagnostics"]:
            print(
                f"{item['code']}: {item['path']}: {item['message']}",
                file=sys.stderr,
            )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
