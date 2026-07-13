from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-ai-governance.py"
spec = importlib.util.spec_from_file_location("ai_governance", SCRIPT)
ai_governance = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = ai_governance
spec.loader.exec_module(ai_governance)


def codes(diagnostics):
    return {item.code for item in diagnostics}


def test_repository_validation_passes():
    result = ai_governance.validate_repository()
    assert result["status"] == "passed", result["diagnostics"]


def test_valid_fixtures_are_accepted():
    schema = ai_governance.read_json(ROOT / "planning" / "ai-governance-coverage.schema.json")
    cases = ai_governance.read_json(ROOT / "fixtures" / "ai-governance" / "valid" / "cases.json")
    for index, case in enumerate(cases["cases"]):
        assert ai_governance.validate_fixture_case(schema, case, index) == [], case["case_id"]


def test_invalid_fixtures_emit_expected_diagnostics():
    schema = ai_governance.read_json(ROOT / "planning" / "ai-governance-coverage.schema.json")
    cases = ai_governance.read_json(ROOT / "fixtures" / "ai-governance" / "invalid" / "cases.json")
    for index, case in enumerate(cases["cases"]):
        assert case["expected_diagnostic"] in codes(
            ai_governance.validate_fixture_case(schema, case, index)
        ), case["case_id"]


def test_coverage_rule_set_is_fail_closed():
    coverage = copy.deepcopy(ai_governance.read_yaml(ROOT / "planning" / "AI_GOVERNANCE_COVERAGE.yml"))
    coverage["rules"] = coverage["rules"][:-1]
    assert "AIGOV-COVERAGE-001_RULE_SET_MISMATCH" in codes(
        ai_governance.validate_coverage_semantics(coverage)
    )


def test_coverage_status_cannot_exceed_carriers():
    coverage = copy.deepcopy(ai_governance.read_yaml(ROOT / "planning" / "AI_GOVERNANCE_COVERAGE.yml"))
    evidence_rule = next(item for item in coverage["rules"] if item["rule_id"] == "AIGOV-EVIDENCE-001")
    evidence_rule["carriers"]["CI_step"] = None
    assert "AIGOV-COVERAGE-001_OVERCLAIMED_STATUS" in codes(
        ai_governance.validate_coverage_semantics(coverage)
    )


def test_mutable_action_reference_is_rejected():
    workflow = """name: bad
on:
  pull_request:
permissions:
  contents: read
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""
    assert "AIGOV-SECURITY-PROFILE-001_MUTABLE_ACTION_REF" in codes(
        ai_governance.validate_workflow_text(".github/workflows/bad.yml", workflow)
    )


def test_checkout_without_exact_head_controls_is_rejected():
    workflow = """name: bad
on:
  pull_request:
permissions:
  contents: read
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5
"""
    result_codes = codes(ai_governance.validate_workflow_text(".github/workflows/bad.yml", workflow))
    assert "AIGOV-SECURITY-PROFILE-001_NOT_EXACT_HEAD" in result_codes
    assert "AIGOV-SECURITY-PROFILE-001_CREDENTIAL_PERSISTENCE" in result_codes
    assert "AIGOV-SECURITY-PROFILE-001_HEAD_ASSERTION_MISSING" in result_codes


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
