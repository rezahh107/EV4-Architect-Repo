from __future__ import annotations
import re
from pathlib import Path

P = Path("scripts/check-ai-governance.py")

def rep(old: str, new: str) -> None:
    text = P.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"core replacement mismatch: {count}: {old[:100]!r}")
    P.write_text(text.replace(old, new, 1), encoding="utf-8")

def sub(pattern: str, new: str) -> None:
    text = P.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, new, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit(f"core regex mismatch: {count}: {pattern[:100]!r}")
    P.write_text(updated, encoding="utf-8")

rep(
'''EXACT_HEAD_REF = "${{ github.event.pull_request.head.sha }}"
EXACT_HEAD_WORDS = ["test", "$(git rev-parse HEAD)", "=", EXACT_HEAD_REF]
REMOTE_ACTION_SHA = re.compile(r"^[^@\\s]+@[0-9a-fA-F]{40}$")
''',
'''EXACT_HEAD_REF = "${{ github.event.pull_request.head.sha }}"
WORKSPACE_GUARD_LINES = (
    "set -eu",
    'test "$(git rev-parse HEAD)" = "${{ github.event.pull_request.head.sha }}"',
    "git diff --exit-code -- .",
    "git diff --cached --exit-code -- .",
    'test -z "$(git status --porcelain=v1 --untracked-files=all)"',
)
SAFE_PROOF_RUNNERS = {"ubuntu-latest"}
REQUIRED_PR_ACTIVITY_TYPES = {"opened", "reopened", "synchronize"}
REMOTE_ACTION_SHA = re.compile(r"^[^@\\s]+@[0-9a-fA-F]{40}$")
''')

rep(
'''    configuration = trigger[event]
    return configuration if isinstance(configuration, dict) else None


def is_pr_workflow''',
'''    configuration = trigger[event]
    return configuration if isinstance(configuration, dict) else None


def _normalized_string_set(value: Any) -> set[str] | None:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return set(value)
    return None


def _pull_request_trigger_is_proof_capable(
    document: dict[str, Any],
) -> bool:
    configuration = workflow_event_configuration(document, "pull_request")
    if configuration is None:
        return True
    if "branches" in configuration or "branches-ignore" in configuration:
        return False
    raw_types = configuration.get("types")
    if raw_types is None:
        return True
    activity_types = _normalized_string_set(raw_types)
    return (
        activity_types is not None
        and REQUIRED_PR_ACTIVITY_TYPES.issubset(activity_types)
    )


def is_pr_workflow''')

rep(
'''def _proof_job_execution_context_is_trusted(job: Any) -> bool:
    return isinstance(job, dict) and "container" not in job and "services" not in job
''',
'''def _proof_job_execution_context_is_trusted(job: Any) -> bool:
    if not isinstance(job, dict):
        return False
    if "container" in job or "services" in job:
        return False
    if isinstance(job.get("uses"), str):
        return True
    return job.get("runs-on") in SAFE_PROOF_RUNNERS
''')

rep(
'''def _proof_node_is_blocking(node: Any) -> bool:
    return (
        isinstance(node, dict)
        and _condition_is_provably_active(node.get("if"))
        and _continue_on_error_disabled(node.get("continue-on-error"))
    )
''',
'''def _proof_node_is_blocking(node: Any) -> bool:
    return (
        isinstance(node, dict)
        and "needs" not in node
        and _condition_is_provably_active(node.get("if"))
        and _continue_on_error_disabled(node.get("continue-on-error"))
    )
''')

rep(
'''    runs_on = job.get("runs-on")
    return isinstance(runs_on, str) and runs_on.startswith("ubuntu-")
''',
'''    runs_on = job.get("runs-on")
    return runs_on in SAFE_PROOF_RUNNERS
''')

sub(
r'''def _is_fail_closed_exact_head_command\(run: Any\) -> bool:
.*?
(?=def _contains_exact_head_assertion)''',
'''def _is_fail_closed_exact_head_command(run: Any) -> bool:
    return tuple(_meaningful_command_lines(run)) == WORKSPACE_GUARD_LINES


''')

rep(
'''    if "pull_request_target" in events:
        output.append(
            Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_PULL_REQUEST_TARGET_FORBIDDEN",
                normalized_path,
                "pull_request_target is unsupported by the active public-repository profile",
            )
        )

    jobs = document.get("jobs")
''',
'''    if "pull_request_target" in events:
        output.append(
            Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_PULL_REQUEST_TARGET_FORBIDDEN",
                normalized_path,
                "pull_request_target is unsupported by the active public-repository profile",
            )
        )
    if (
        "pull_request" in events
        and not _pull_request_trigger_is_proof_capable(document)
    ):
        output.append(
            Diagnostic(
                "AIGOV-SECURITY-PROFILE-001_PR_TRIGGER_RESTRICTED",
                normalized_path,
                "pull_request proof must run for opened, reopened, and synchronize without branch exclusions",
            )
        )

    jobs = document.get("jobs")
''')

rep(
'''                "AIGOV-SECURITY-PROFILE-001_UNTRUSTED_JOB_RUNTIME", job_path,
                "PR proof jobs must not declare container or services",
''',
'''                "AIGOV-SECURITY-PROFILE-001_UNTRUSTED_JOB_RUNTIME", job_path,
                "PR proof jobs must use an allowlisted runner and must not declare container or services",
''')

sub(
r'''        for position, checkout_index in enumerate\(checkout_indexes\):
.*?
(?=    for secret_path in _secret_exposure_paths\(document\):)''',
'''        for checkout_index in checkout_indexes:
            guard_index = checkout_index + 1
            if (
                guard_index >= len(steps)
                or not _contains_exact_head_assertion(
                    steps[guard_index], job, document
                )
            ):
                output.append(
                    Diagnostic(
                        "AIGOV-SECURITY-PROFILE-001_HEAD_ASSERTION_MISSING",
                        f"{job_path}.steps[{checkout_index}]",
                        "each checkout must be immediately followed by an unconditional clean-worktree exact-head guard",
                    )
                )

''')

rep(
'''    configuration = workflow_event_configuration(document, event)
    if configuration is None:
        return True, set()
''',
'''    if (
        event == "pull_request"
        and not _pull_request_trigger_is_proof_capable(document)
    ):
        return False, set(authoritative_paths)
    configuration = workflow_event_configuration(document, event)
    if configuration is None:
        return True, set()
''')

rep(
'''    if _words_execute_tests(words):
        return _inline_environment_is_safe(assignments, for_tests=True)
    return False


def _verify_ci_step(
''',
'''    if _words_execute_tests(words):
        return _inline_environment_is_safe(assignments, for_tests=True)
    return False


def _is_exact_checkout_step(step: Any) -> bool:
    if not isinstance(step, dict) or not _proof_node_is_blocking(step):
        return False
    target = step.get("uses")
    if not isinstance(target, str) or not _is_checkout(target):
        return False
    if not REMOTE_ACTION_SHA.fullmatch(target):
        return False
    with_values = step.get("with")
    if not isinstance(with_values, dict):
        return False
    return (
        with_values.get("ref") == EXACT_HEAD_REF
        and _persist_credentials_disabled(
            with_values.get("persist-credentials")
        )
    )


def _carrier_has_fresh_checkout_guard(
    steps: list[Any],
    carrier_index: int,
    job: dict[str, Any],
    document: dict[str, Any],
) -> bool:
    if carrier_index < 2:
        return False
    return (
        _is_exact_checkout_step(steps[carrier_index - 2])
        and _contains_exact_head_assertion(
            steps[carrier_index - 1], job, document
        )
    )


def _verify_ci_step(
''')

rep(
'''    steps = job.get("steps")
    step = next(
        (
            item
            for item in steps or []
            if isinstance(item, dict) and item.get("name") == step_name
        ),
        None,
    )
    if not isinstance(step, dict):
''',
'''    steps = job.get("steps")
    step_index = next(
        (
            index
            for index, item in enumerate(steps or [])
            if isinstance(item, dict) and item.get("name") == step_name
        ),
        None,
    )
    step = (
        steps[step_index]
        if isinstance(steps, list) and step_index is not None
        else None
    )
    if not isinstance(step, dict):
''')

rep(
'''    validator_reference = (rule.get("carriers") or {}).get("validator_rule")
''',
'''    if (
        not isinstance(steps, list)
        or step_index is None
        or not _carrier_has_fresh_checkout_guard(
            steps, step_index, job, document
        )
    ):
        return False, [
            Diagnostic(
                "AIGOV-COVERAGE-001_CI_STEP_INVALID",
                "$",
                "CI carrier must be immediately preceded by a clean-worktree exact-head guard and a fresh exact-head checkout",
            )
        ]

    validator_reference = (rule.get("carriers") or {}).get("validator_rule")
''')
