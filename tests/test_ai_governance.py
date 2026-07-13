from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-ai-governance.py"
spec = importlib.util.spec_from_file_location("ai_governance", SCRIPT)
ai_governance = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = ai_governance
spec.loader.exec_module(ai_governance)


def codes(diagnostics):
    return {item.code for item in diagnostics}


def secure_checkout_steps() -> str:
    return """
      - name: Checkout exact pull request head
        uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          persist-credentials: false
      - name: Assert exact pull request head
        shell: bash
        run: test "$(git rev-parse HEAD)" = "${{ github.event.pull_request.head.sha }}"
"""


def workflow(trigger: str = "pull_request", permissions: str = "  contents: read") -> str:
    return f"""name: test
on: {trigger}
permissions:
{permissions}
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
{secure_checkout_steps()}
      - name: Validate
        run: python scripts/check-ai-governance.py
"""


def test_repository_validation_passes():
    result = ai_governance.validate_repository()
    assert result["status"] == "passed", result["diagnostics"]


def test_valid_fixtures_are_accepted():
    schema = ai_governance.read_json(
        ROOT / "planning" / "ai-governance-coverage.schema.json"
    )
    cases = ai_governance.read_json(
        ROOT / "fixtures" / "ai-governance" / "valid" / "cases.json"
    )
    for index, case in enumerate(cases["cases"]):
        assert ai_governance.validate_fixture_case(schema, case, index) == [], case[
            "case_id"
        ]


def test_invalid_fixtures_emit_expected_diagnostics():
    schema = ai_governance.read_json(
        ROOT / "planning" / "ai-governance-coverage.schema.json"
    )
    cases = ai_governance.read_json(
        ROOT / "fixtures" / "ai-governance" / "invalid" / "cases.json"
    )
    for index, case in enumerate(cases["cases"]):
        assert case["expected_diagnostic"] in codes(
            ai_governance.validate_fixture_case(schema, case, index)
        ), case["case_id"]


@pytest.mark.parametrize(
    ("source_type", "state", "claim_kind"),
    [
        ("repository", "REPOSITORY_CONFIRMED", "merge_status"),
        ("tool", "TOOL_CONFIRMED", "repository_state"),
        ("source", "SOURCE_CONFIRMED", "readiness"),
        ("test", "TEST_CONFIRMED", "readiness"),
        ("ci", "CI_CONFIRMED", "ci_status"),
        ("runtime", "RUNTIME_CONFIRMED", "runtime_status"),
        ("publication_receipt", "PUBLICATION_RECEIPT_CONFIRMED", "readiness"),
        ("performance_receipt", "PERFORMANCE_RECEIPT_CONFIRMED", "readiness"),
    ],
)
def test_self_asserted_outcome_is_rejected_for_every_source_label(
    source_type, state, claim_kind
):
    payload = {
        "artifact_type": "evidence_claim",
        "claim_id": "SELF-ASSERTED",
        "claim_kind": claim_kind,
        "claim_text": "Outcome claimed by the implementation model.",
        "evidence_state": state,
        "source_type": source_type,
        "source_reference": "claimed/source",
        "unknown_input": False,
        "self_asserted_outcome": True,
    }
    assert "AIGOV-EVIDENCE-001_SELF_ASSERTED_OUTCOME" in codes(
        ai_governance.validate_evidence_claim(payload)
    )


@pytest.mark.parametrize(
    ("source_type", "state", "claim_kind"),
    [
        ("repository", "REPOSITORY_CONFIRMED", "merge_status"),
        ("ci", "CI_CONFIRMED", "ci_status"),
        ("runtime", "RUNTIME_CONFIRMED", "runtime_status"),
    ],
)
def test_external_outcome_with_matching_evidence_is_accepted(
    source_type, state, claim_kind
):
    payload = {
        "artifact_type": "evidence_claim",
        "claim_id": "EXTERNAL-OUTCOME",
        "claim_kind": claim_kind,
        "claim_text": "Externally evidenced outcome.",
        "evidence_state": state,
        "source_type": source_type,
        "source_reference": "immutable/evidence/reference",
        "unknown_input": False,
        "self_asserted_outcome": False,
    }
    assert ai_governance.validate_evidence_claim(payload) == []


def test_external_outcome_requires_factual_state_and_source_reference():
    payload = {
        "artifact_type": "evidence_claim",
        "claim_id": "BAD-EXTERNAL-OUTCOME",
        "claim_kind": "merge_status",
        "claim_text": "Merge outcome without evidence.",
        "evidence_state": "AI_TECHNICAL_DECISION",
        "source_type": "ai_technical_decision",
        "source_reference": None,
        "unknown_input": False,
        "self_asserted_outcome": False,
    }
    found = codes(ai_governance.validate_evidence_claim(payload))
    assert "AIGOV-EVIDENCE-001_OUTCOME_NOT_FACTUAL" in found
    assert "AIGOV-EVIDENCE-001_MISSING_SOURCE_REFERENCE" in found


def test_github_actions_loader_preserves_yaml_11_boolean_words():
    document = ai_governance.load_actions_yaml(
        "on: pull_request\nenv:\n  ON_WORD: on\n  OFF_WORD: off\n  YES_WORD: yes\n  NO_WORD: no\njobs: {}\n"
    )
    assert document["on"] == "pull_request"
    assert document["env"] == {
        "ON_WORD": "on",
        "OFF_WORD": "off",
        "YES_WORD": "yes",
        "NO_WORD": "no",
    }


@pytest.mark.parametrize(
    "trigger",
    [
        "pull_request",
        "[pull_request]",
    ],
)
def test_scalar_and_list_pr_triggers_are_inspected(trigger):
    text = workflow(
        trigger=trigger,
        permissions="  contents: read\n  pull-requests: write",
    )
    assert "AIGOV-SECURITY-PROFILE-001_PERMISSIONS_NOT_MINIMAL" in codes(
        ai_governance.validate_workflow_text("workflow.yml", text)
    )


def test_mapping_pr_trigger_is_inspected():
    text = workflow().replace(
        "on: pull_request",
        "on:\n  pull_request:",
    ).replace(
        "  contents: read",
        "  contents: write",
    )
    assert "AIGOV-SECURITY-PROFILE-001_PERMISSIONS_NOT_MINIMAL" in codes(
        ai_governance.validate_workflow_text("workflow.yml", text)
    )


def test_pull_request_target_is_rejected_fail_closed():
    text = workflow(trigger="pull_request_target")
    assert "AIGOV-SECURITY-PROFILE-001_PULL_REQUEST_TARGET_FORBIDDEN" in codes(
        ai_governance.validate_workflow_text("workflow.yml", text)
    )


def test_extra_write_permission_is_rejected():
    text = workflow(
        permissions="  contents: read\n  pull-requests: write",
    )
    assert "AIGOV-SECURITY-PROFILE-001_PERMISSIONS_NOT_MINIMAL" in codes(
        ai_governance.validate_workflow_text("workflow.yml", text)
    )


def test_secure_checkout_does_not_mask_later_insecure_checkout():
    text = workflow().replace(
        "      - name: Validate\n        run: python scripts/check-ai-governance.py",
        """      - name: Insecure second checkout
        uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5
      - name: Validate
        run: python scripts/check-ai-governance.py""",
    )
    found = codes(ai_governance.validate_workflow_text("workflow.yml", text))
    assert "AIGOV-SECURITY-PROFILE-001_NOT_EXACT_HEAD" in found
    assert "AIGOV-SECURITY-PROFILE-001_CREDENTIAL_PERSISTENCE" in found
    assert "AIGOV-SECURITY-PROFILE-001_HEAD_ASSERTION_MISSING" in found


def test_inline_yaml_checkout_mapping_is_inspected():
    text = """name: inline
on: [pull_request]
permissions: {contents: read}
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - {name: Inline checkout, uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5, with: {ref: "${{ github.event.pull_request.head.sha }}", persist-credentials: true}}
      - {name: Assert, shell: bash, run: 'test "$(git rev-parse HEAD)" = "${{ github.event.pull_request.head.sha }}"'}
"""
    assert "AIGOV-SECURITY-PROFILE-001_CREDENTIAL_PERSISTENCE" in codes(
        ai_governance.validate_workflow_text("workflow.yml", text)
    )


def test_mutable_step_and_reusable_workflow_actions_are_rejected():
    step_text = workflow().replace(
        "actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5",
        "actions/checkout@v4",
    )
    assert "AIGOV-SECURITY-PROFILE-001_MUTABLE_ACTION_REF" in codes(
        ai_governance.validate_workflow_text("step.yml", step_text)
    )
    reusable = """name: reusable
on: pull_request
permissions:
  contents: read
jobs:
  call:
    uses: owner/repo/.github/workflows/check.yml@main
"""
    assert "AIGOV-SECURITY-PROFILE-001_MUTABLE_ACTION_REF" in codes(
        ai_governance.validate_workflow_text("reusable.yml", reusable)
    )


@pytest.mark.parametrize(
    "secret_value",
    [
        "${{ secrets.NAME }}",
        "${{ secrets['NAME'] }}",
        '${{ secrets["NAME"] }}',
        "${{ toJSON(secrets) }}",
    ],
)
def test_direct_secret_reference_forms_are_rejected(secret_value):
    text = workflow().replace(
        "      - name: Validate\n        run: python scripts/check-ai-governance.py",
        f"""      - name: Validate
        env:
          TOKEN: {json.dumps(secret_value)}
        run: python scripts/check-ai-governance.py""",
    )
    assert "AIGOV-SECURITY-PROFILE-001_PR_SECRET_EXPOSURE" in codes(
        ai_governance.validate_workflow_text("workflow.yml", text)
    )


def test_secrets_inherit_is_rejected():
    text = """name: reusable
on: pull_request
permissions:
  contents: read
jobs:
  call:
    uses: owner/repo/.github/workflows/check.yml@0123456789abcdef0123456789abcdef01234567
    secrets: inherit
"""
    assert "AIGOV-SECURITY-PROFILE-001_PR_SECRET_EXPOSURE" in codes(
        ai_governance.validate_workflow_text("workflow.yml", text)
    )


def test_unsupported_public_profile_is_rejected():
    payload = {
        "repository_visibility": "public",
        "active_profile": "unknown_public_profile",
        "minimum_controls": list(ai_governance.MIN_CONTROLS),
        "enterprise_controls_status": "intentionally_out_of_scope",
    }
    assert "AIGOV-SECURITY-PROFILE-001_UNSUPPORTED_PROFILE" in codes(
        ai_governance.validate_security_profile(payload)
    )


def test_coverage_rule_set_is_fail_closed():
    coverage = copy.deepcopy(
        ai_governance.read_yaml(ROOT / "planning" / "AI_GOVERNANCE_COVERAGE.yml")
    )
    coverage["rules"] = coverage["rules"][:-1]
    assert "AIGOV-COVERAGE-001_RULE_SET_MISMATCH" in codes(
        ai_governance.validate_coverage_semantics(coverage)
    )


def test_coverage_status_cannot_exceed_verified_carriers():
    coverage = copy.deepcopy(
        ai_governance.read_yaml(ROOT / "planning" / "AI_GOVERNANCE_COVERAGE.yml")
    )
    evidence_rule = next(
        item for item in coverage["rules"] if item["rule_id"] == "AIGOV-EVIDENCE-001"
    )
    evidence_rule["carriers"]["CI_step"] = None
    assert "AIGOV-COVERAGE-001_OVERCLAIMED_STATUS" in codes(
        ai_governance.validate_coverage_semantics(coverage)
    )


def test_nonexistent_validator_symbol_is_not_a_verified_carrier():
    coverage = copy.deepcopy(
        ai_governance.read_yaml(ROOT / "planning" / "AI_GOVERNANCE_COVERAGE.yml")
    )
    rule = next(
        item for item in coverage["rules"] if item["rule_id"] == "AIGOV-EVIDENCE-001"
    )
    rule["carriers"]["validator_rule"] = "README.md::nonexistent_function"
    assert "AIGOV-COVERAGE-001_VALIDATOR_SYMBOL_MISSING" in codes(
        ai_governance.validate_coverage_semantics(coverage)
    )


def test_nonexistent_ci_job_and_step_are_not_verified_carriers():
    coverage = copy.deepcopy(
        ai_governance.read_yaml(ROOT / "planning" / "AI_GOVERNANCE_COVERAGE.yml")
    )
    rule = next(
        item for item in coverage["rules"] if item["rule_id"] == "AIGOV-EVIDENCE-001"
    )
    rule["carriers"]["CI_step"] = (
        "README.md / nonexistent_job / nonexistent_step"
    )
    assert "AIGOV-COVERAGE-001_CI_STEP_INVALID" in codes(
        ai_governance.validate_coverage_semantics(coverage)
    )


def test_nonexistent_schema_pointer_is_not_a_verified_carrier():
    coverage = copy.deepcopy(
        ai_governance.read_yaml(ROOT / "planning" / "AI_GOVERNANCE_COVERAGE.yml")
    )
    rule = next(
        item for item in coverage["rules"] if item["rule_id"] == "AIGOV-EVIDENCE-001"
    )
    rule["carriers"]["schema_carrier"] = (
        "planning/ai-governance-coverage.schema.json#/nonexistent"
    )
    assert "AIGOV-COVERAGE-001_SCHEMA_POINTER_INVALID" in codes(
        ai_governance.validate_coverage_semantics(coverage)
    )


def test_ci_path_filters_must_cover_authoritative_carriers(tmp_path):
    workflow_path = tmp_path / ".github" / "workflows" / "validate.yml"
    workflow_path.parent.mkdir(parents=True)
    workflow_path.write_text(
        workflow().replace(
            "on: pull_request",
            "on:\n  pull_request:\n    paths:\n      - 'README.md'",
        ),
        encoding="utf-8",
    )
    rule = {
        "rule_id": "AIGOV-EVIDENCE-001",
        "carriers": {
            "prose_source": "docs/governance/AI_AUTHORITY_GOVERNANCE_ADOPTION.md#Evidence States",
            "schema_carrier": "planning/ai-governance-coverage.schema.json#/$defs/evidence_claim",
            "validator_rule": "scripts/check-ai-governance.py::validate_evidence_claim",
            "valid_fixture": "fixtures/ai-governance/valid/cases.json",
            "invalid_fixture": "fixtures/ai-governance/invalid/cases.json",
            "CI_step": ".github/workflows/validate.yml / validate / Validate",
        },
    }
    passed, diagnostics = ai_governance._verify_ci_step(
        rule["carriers"]["CI_step"], tmp_path, rule
    )
    assert passed is False
    assert "AIGOV-COVERAGE-001_CI_PATH_FILTER_MISSING" in codes(diagnostics)


def test_human_approval_and_coach_truth_are_rejected():
    approval = {
        "human_technical_approval_required": True,
        "owner_acknowledgement_used_as_evidence": True,
        "user_merge_action_role": "technical_approval",
    }
    critique = {
        "evidence_state": "REPOSITORY_CONFIRMED",
        "claims_technical_truth": True,
        "claims_real_world_outcome": True,
    }
    assert "AIGOV-HUMAN-001_APPROVAL_AS_EVIDENCE" in codes(
        ai_governance.validate_approval_contract(approval)
    )
    assert "AIGOV-COACH-001_CRITIQUE_AS_FACT" in codes(
        ai_governance.validate_coach_critique(critique)
    )
