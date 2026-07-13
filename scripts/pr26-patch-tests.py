from pathlib import Path

P = Path("tests/test_ai_governance.py")
text = P.read_text(encoding="utf-8")
old = '''EXACT_ASSERTION = (
    'test "$(git rev-parse HEAD)" = '
    '"${{ github.event.pull_request.head.sha }}"'
)
'''
new = '''EXACT_ASSERTION = (
    "set -eu\\n"
    'test "$(git rev-parse HEAD)" = "${{ github.event.pull_request.head.sha }}"\\n'
    "git diff --exit-code -- .\\n"
    "git diff --cached --exit-code -- .\\n"
    'test -z "$(git status --porcelain=v1 --untracked-files=all)"\\n'
)
'''
if text.count(old) != 1:
    raise SystemExit("test assertion replacement mismatch")
text = text.replace(old, new, 1)
marker = "# PRF-002/003 trigger, dependency, runner, and workspace regressions"
if marker in text:
    raise SystemExit("test regression marker already exists")
text = text.rstrip() + r'''


# PRF-002/003 trigger, dependency, runner, and workspace regressions

def test_legacy_head_only_assertion_is_rejected():
    weak = (
        'test "$(git rev-parse HEAD)" = '
        '"${{ github.event.pull_request.head.sha }}"'
    )
    assert "AIGOV-SECURITY-PROFILE-001_HEAD_ASSERTION_MISSING" in codes(
        ai_governance.validate_workflow_text(
            "workflow.yml", workflow(assertion_run=weak)
        )
    )


def test_workspace_tamper_between_guard_and_carrier_invalidates_ci_proof(
    tmp_path,
):
    text = workflow().replace(
        "      - name: Validate\n",
        "      - name: Tamper with validator\n"
        "        shell: bash\n"
        "        run: echo '# tampered' >> scripts/check-ai-governance.py\n"
        "      - name: Validate\n",
    )
    passed, diagnostics = verify_temp_ci_step(tmp_path, text)
    assert passed is False
    assert "AIGOV-COVERAGE-001_CI_STEP_INVALID" in codes(diagnostics)


def test_workspace_tamper_between_checkout_and_guard_is_rejected():
    text = workflow().replace(
        "      - name: Assert exact pull request head\n",
        "      - name: Tamper before guard\n"
        "        shell: bash\n"
        "        run: echo '# tampered' >> scripts/check-ai-governance.py\n"
        "      - name: Assert exact pull request head\n",
    )
    assert "AIGOV-SECURITY-PROFILE-001_HEAD_ASSERTION_MISSING" in codes(
        ai_governance.validate_workflow_text("workflow.yml", text)
    )


@pytest.mark.parametrize(
    "trigger_block",
    [
        "on:\n  pull_request:\n    types: [closed]",
        "on:\n  pull_request:\n    branches: [invalid]",
        "on:\n  pull_request:\n    branches-ignore: [main]",
    ],
)
def test_restricted_pull_request_trigger_is_not_ci_enforced(
    tmp_path, trigger_block
):
    text = workflow().replace("on: pull_request", trigger_block)
    assert "AIGOV-SECURITY-PROFILE-001_PR_TRIGGER_RESTRICTED" in codes(
        ai_governance.validate_workflow_text("workflow.yml", text)
    )
    passed, diagnostics = verify_temp_ci_step(tmp_path, text)
    assert passed is False
    assert "AIGOV-COVERAGE-001_CI_STEP_INVALID" in codes(diagnostics)


def test_required_pull_request_activity_types_are_accepted(tmp_path):
    text = workflow().replace(
        "on: pull_request",
        "on:\n  pull_request:\n"
        "    types: [opened, reopened, synchronize]",
    )
    passed, diagnostics = verify_temp_ci_step(tmp_path, text)
    assert passed is True, diagnostics
    assert diagnostics == []


def test_carrier_job_with_needs_is_not_ci_enforced(tmp_path):
    text = workflow().replace(
        "  validate:\n    runs-on: ubuntu-latest",
        "  validate:\n    needs: skipped\n    runs-on: ubuntu-latest",
    )
    text += (
        "  skipped:\n"
        "    if: false\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        '      - run: "true"\n'
    )
    passed, diagnostics = verify_temp_ci_step(tmp_path, text)
    assert passed is False
    assert "AIGOV-COVERAGE-001_CI_STEP_INVALID" in codes(diagnostics)


def test_non_allowlisted_ubuntu_prefix_runner_is_rejected(tmp_path):
    text = workflow().replace("runs-on: ubuntu-latest", "runs-on: ubuntu-attacker")
    assert "AIGOV-SECURITY-PROFILE-001_UNTRUSTED_JOB_RUNTIME" in codes(
        ai_governance.validate_workflow_text("workflow.yml", text)
    )
    passed, diagnostics = verify_temp_ci_step(tmp_path, text)
    assert passed is False
    assert "AIGOV-COVERAGE-001_CI_STEP_INVALID" in codes(diagnostics)
''' + "\n"
P.write_text(text, encoding="utf-8")
