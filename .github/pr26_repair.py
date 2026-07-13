from pathlib import Path
import re

root = Path.cwd()
src = root / "scripts/check-ai-governance.py"
tests = root / "tests/test_ai_governance.py"
workflow = root / ".github/workflows/validate-ai-governance.yml"

def rep(path, old, new, count=1):
    text = path.read_text(encoding="utf-8")
    found = text.count(old)
    if found != count:
        raise SystemExit(f"{path}: expected {count} copies, found {found}: {old[:120]!r}")
    path.write_text(text.replace(old, new, count), encoding="utf-8")

def sub(path, pattern, repl):
    text = path.read_text(encoding="utf-8")
    new, n = re.subn(pattern, repl, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"{path}: regex mismatch: {pattern[:120]!r}")
    path.write_text(new, encoding="utf-8")

rep(
    src,
    'REMOTE_ACTION_SHA = re.compile(r"^[^@\\s]+@[0-9a-fA-F]{40}$")\n',
    'REMOTE_ACTION_SHA = re.compile(r"^[^@\\s]+@[0-9a-fA-F]{40}$")\n'
    'DOCKER_ACTION_DIGEST = re.compile(r"^docker://[^@\\s]+@sha256:[0-9a-fA-F]{64}$")\n',
)
rep(
    src,
    'SAFE_TEST_INLINE_ENV = {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}\n'
    'FORBIDDEN_PROOF_ENV_KEYS = {\n'
    '    "PYTEST_ADDOPTS",\n',
    'SAFE_TEST_INLINE_ENV = {\n'
    '    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",\n'
    '    "PYTEST_ADDOPTS": "",\n'
    '    "PYTEST_PLUGINS": "",\n'
    '}\n'
    'CI_PROOF_SURFACE_PATHS = {\n'
    '    "scripts/_proof_surface_probe.py",\n'
    '    "tests/_proof_surface_probe.py",\n'
    '    ".github/actions/_proof_surface/action.yml",\n'
    '    "pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini", "conftest.py",\n'
    '}\n'
    'FORBIDDEN_PROOF_ENV_KEYS = {\n',
)
rep(
    src,
    'def _is_checkout(target: str) -> bool:\n',
    '''def _is_docker_action(target: str) -> bool:
    return target.startswith("docker://")


def _is_local_action(target: str) -> bool:
    return target.startswith("./")


def _proof_job_execution_context_is_trusted(job: Any) -> bool:
    return isinstance(job, dict) and "container" not in job and "services" not in job


def _is_checkout(target: str) -> bool:
''',
)
rep(
    src,
    '        _proof_node_is_blocking(step)\n'
    '        and isinstance(step, dict)\n',
    '        _proof_node_is_blocking(step)\n'
    '        and _proof_job_execution_context_is_trusted(job)\n'
    '        and isinstance(step, dict)\n',
)

local = r'''
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
'''.strip()
rep(
    src,
    '    return candidate, relative\n\n\ndef validate_workflow_document(\n',
    '    return candidate, relative\n\n\n' + local + '\n\n\ndef validate_workflow_document(\n',
)
rep(
    src,
    '        reusable_target = job.get("uses")\n',
    '        if not _proof_job_execution_context_is_trusted(job):\n'
    '            output.append(Diagnostic(\n'
    '                "AIGOV-SECURITY-PROFILE-001_UNTRUSTED_JOB_RUNTIME", job_path,\n'
    '                "PR proof jobs must not declare container or services",\n'
    '            ))\n\n'
    '        reusable_target = job.get("uses")\n',
)
sub(
    src,
    r'            if isinstance\(target, str\):\n'
    r'                if _is_remote_action\(target\).*?'
    r'                if _is_checkout\(target\):\n',
    '            if isinstance(target, str):\n'
    '                output.extend(_validate_action_reference(target, f"{step_path}.uses", root))\n'
    '                if _is_checkout(target):\n',
)
sub(
    src,
    r'def _words_execute_validator\(.*?\n\n\ndef _step_executes_applicable_command\(',
    '''def _words_execute_validator(words: list[str], validator_file: str) -> bool:
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


def _step_executes_applicable_command(''',
)
rep(
    src,
    '    if job is None or document is None:\n'
    '        return False\n'
    '    if not _proof_step_shell_is_supported(step, job, document):\n',
    '    if job is None or document is None:\n'
    '        return False\n'
    '    if not _proof_job_execution_context_is_trusted(job):\n'
    '        return False\n'
    '    if not _proof_step_shell_is_supported(step, job, document):\n',
)
rep(
    src,
    '    authoritative_paths = {\n'
    '        "planning/AI_GOVERNANCE_COVERAGE.yml",\n'
    '        "tests/test_ai_governance.py",\n'
    '    }\n',
    '    authoritative_paths = {\n'
    '        "planning/AI_GOVERNANCE_COVERAGE.yml",\n'
    '        "tests/test_ai_governance.py",\n'
    '    } | CI_PROOF_SURFACE_PATHS\n',
)

rep(
    tests,
    '    validation_run: str = "python scripts/check-ai-governance.py",\n',
    '    validation_run: str = "python -I -P scripts/check-ai-governance.py",\n',
)
rep(
    tests,
    '        run: "python scripts/check-ai-governance.py"\n',
    '        run: "python -I -P scripts/check-ai-governance.py"\n',
)
sub(
    tests,
    r'    \[\n'
    r'        "python scripts/check-ai-governance\.py",.*?'
    r'    \],\n',
    r'''    [
        "python -I -P scripts/check-ai-governance.py",
        "python3 -I -P scripts/check-ai-governance.py",
        (
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_ADDOPTS= "
            "PYTEST_PLUGINS= python -I -P -m pytest -c /dev/null "
            "--noconftest -q tests/test_ai_governance.py"
        ),
        (
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_ADDOPTS= "
            "PYTEST_PLUGINS= python3 -I -P -m pytest -c /dev/null "
            "--noconftest --quiet tests/test_ai_governance.py"
        ),
    ],
''',
)

marker = "# PRF-002/003/004 execution-image and proof-surface regressions"
test_text = tests.read_text(encoding="utf-8")
if marker in test_text:
    raise SystemExit("regression marker already exists")
test_text += r'''

# PRF-002/003/004 execution-image and proof-surface regressions

def test_job_container_and_services_are_rejected(tmp_path):
    for fragment in (
        "    container:\n      image: attacker/fake-tools:latest\n",
        "    services:\n      fake:\n        image: attacker/service:latest\n",
    ):
        text = workflow().replace(
            "    runs-on: ubuntu-latest\n",
            "    runs-on: ubuntu-latest\n" + fragment,
        )
        assert "AIGOV-SECURITY-PROFILE-001_UNTRUSTED_JOB_RUNTIME" in codes(
            ai_governance.validate_workflow_text("workflow.yml", text)
        )
        passed, diagnostics = verify_temp_ci_step(tmp_path, text)
        assert passed is False
        assert "AIGOV-COVERAGE-001_CI_STEP_INVALID" in codes(diagnostics)


def test_nonisolated_python_and_open_pytest_surfaces_are_rejected(tmp_path):
    commands = (
        "python scripts/check-ai-governance.py",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_ai_governance.py",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_ADDOPTS= PYTEST_PLUGINS= "
        "python -I -P -m pytest -q tests/test_ai_governance.py",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_ADDOPTS= PYTEST_PLUGINS= "
        "python -I -P -m pytest -c pytest.ini --noconftest -q "
        "tests/test_ai_governance.py",
    )
    for command in commands:
        passed, diagnostics = verify_temp_ci_step(
            tmp_path, workflow(validation_run=command)
        )
        assert passed is False
        assert "AIGOV-COVERAGE-001_CI_STEP_INVALID" in codes(diagnostics)


def _workflow_with_extra_uses(target: str) -> str:
    return workflow().replace(
        "      - name: Validate\n",
        f"      - name: Extra action\n        uses: {target}\n"
        "      - name: Validate\n",
    )


def test_mutable_docker_action_is_rejected():
    assert "AIGOV-SECURITY-PROFILE-001_MUTABLE_DOCKER_ACTION" in codes(
        ai_governance.validate_workflow_text(
            "workflow.yml",
            _workflow_with_extra_uses("docker://attacker/image:latest"),
        )
    )


def test_digest_pinned_docker_action_is_accepted():
    target = "docker://registry.example/tool@sha256:" + ("a" * 64)
    assert ai_governance.validate_workflow_text(
        "workflow.yml", _workflow_with_extra_uses(target)
    ) == []


def _write_local_action(tmp_path: Path, body: str) -> None:
    path = tmp_path / ".github/actions/untrusted/action.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_local_action_mutable_nested_use_and_run_are_rejected(tmp_path):
    cases = (
        (
            "name: x\nruns:\n  using: composite\n  steps:\n"
            "    - uses: owner/repo/action@main\n",
            "AIGOV-SECURITY-PROFILE-001_MUTABLE_ACTION_REF",
        ),
        (
            "name: x\nruns:\n  using: composite\n  steps:\n"
            "    - shell: bash\n      run: echo bypass\n",
            "AIGOV-SECURITY-PROFILE-001_LOCAL_ACTION_RUN_UNBOUNDED",
        ),
    )
    for body, expected in cases:
        _write_local_action(tmp_path, body)
        found = codes(ai_governance.validate_workflow_text(
            "workflow.yml",
            _workflow_with_extra_uses("./.github/actions/untrusted"),
            root=tmp_path,
        ))
        assert expected in found


def test_ci_filters_must_cover_all_proof_surfaces(tmp_path):
    text = workflow().replace(
        "on: pull_request",
        "on:\n  pull_request:\n    paths:\n"
        "      - 'scripts/**'\n"
        "      - 'tests/**'\n"
        "      - '.github/workflows/**'",
    )
    passed, diagnostics = verify_temp_ci_step(tmp_path, text)
    assert passed is False
    assert "AIGOV-COVERAGE-001_CI_PATH_FILTER_MISSING" in codes(diagnostics)
'''
tests.write_text(test_text, encoding="utf-8")

head = "$" + "{{ github.event.pull_request.head.sha }}"
workflow.write_text(
    f'''name: validate-ai-governance

on:
  pull_request:
    paths:
      - 'planning/AI_GOVERNANCE_COVERAGE.yml'
      - 'planning/ai-governance-coverage.schema.json'
      - 'fixtures/ai-governance/**'
      - 'scripts/**'
      - 'tests/**'
      - 'pytest.ini'
      - 'pyproject.toml'
      - 'setup.cfg'
      - 'tox.ini'
      - 'conftest.py'
      - 'AGENTS.md'
      - 'docs/governance/AI_AUTHORITY_GOVERNANCE_ADOPTION.md'
      - '.github/actions/**'
      - '.github/workflows/**'

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout exact pull request head
        uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5
        with:
          ref: {head}
          persist-credentials: false
      - name: Assert exact pull request head
        shell: bash
        run: test "$(git rev-parse HEAD)" = "{head}"
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
        with:
          python-version: '3.11'
      - name: Install validation dependencies
        run: python -I -P -m pip install 'jsonschema>=4.22.0' 'PyYAML>=6.0' 'pytest>=8.0.0'
      - name: Validate AI governance coverage and fixtures
        run: python -I -P scripts/check-ai-governance.py
      - name: Run AI governance regression tests
        run: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_ADDOPTS= PYTEST_PLUGINS= python -I -P -m pytest -c /dev/null --noconftest -q tests/test_ai_governance.py
''',
    encoding="utf-8",
)

for path in (
    root / ".github/workflows/pr26-repair-proof-surface.yml",
    root / ".github/workflows/pr26-trigger-temp.yml",
    root / ".github/pr26_repair.py",
):
    if path.exists():
        path.unlink()
