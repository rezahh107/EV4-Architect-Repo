from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "repository_repair_handoff.py"
FIXTURE_DIR = REPO_ROOT / "fixtures" / "repository-repair-recommendation-handoff"
GOLDEN_PATH = FIXTURE_DIR / "golden-P01.prompt.txt"

spec = importlib.util.spec_from_file_location("repository_repair_handoff", MODULE_PATH)
assert spec and spec.loader
handoff = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = handoff
spec.loader.exec_module(handoff)


def load_cases() -> list[dict]:
    index = json.loads((FIXTURE_DIR / "index.v1.json").read_text(encoding="utf-8"))
    cases: list[dict] = []
    for filename in index["case_files"]:
        payload = json.loads((FIXTURE_DIR / filename).read_text(encoding="utf-8"))
        cases.extend(payload["cases"])
    by_id = {case["case_id"]: case for case in cases}
    assert set(by_id) == set(index["case_ids"])
    return [by_id[case_id] for case_id in index["case_ids"]]


def case_by_id(case_id: str) -> dict:
    return next(case for case in load_cases() if case["case_id"] == case_id)


def validated_record(case_id: str):
    result = handoff.validate_repository_repair_handoff_record(case_by_id(case_id)["record"])
    assert result.status == "valid", result.reason_code
    assert result.record is not None
    return result.record


def test_fixture_inventory_is_complete_and_data_first() -> None:
    cases = load_cases()
    assert [case["case_id"] for case in cases] == [
        "P01", "P02", "P03", "P04",
        "N01", "N02", "N03", "N04", "N05",
        "B01", "B02", "B03", "B04", "B05",
    ]
    serialized = json.dumps(cases, sort_keys=True)
    for competing_key in (
        "should_emit_handoff",
        "standalone_repair_prompt",
        "eligibility_predicate",
        "allowed_repository_gap_states",
        "allowed_repository_gap_classes",
    ):
        assert competing_key not in serialized


@pytest.mark.parametrize("case", load_cases(), ids=lambda case: case["case_id"])
def test_canonical_evaluator_matches_fixture_expectation(case: dict) -> None:
    result = handoff.evaluate_repository_repair_handoff_eligibility(case["record"])
    assert result.status == case["expected"]["eligibility_status"]
    assert result.reason_code == case["expected"]["reason_code"]


def test_closed_run_and_repair_status_relationships() -> None:
    assert handoff._ALLOWED_REPAIR_STATUS_BY_RUN_STATUS == {
        "in_progress": frozenset({"pending"}),
        "repairing": frozenset({"pending"}),
        "repaired": frozenset({"validated"}),
        "blocked": frozenset({"failed"}),
        "terminal": frozenset({"not_applicable"}),
    }
    for case_id in ("N03", "B05"):
        validation = handoff.validate_repository_repair_handoff_record(case_by_id(case_id)["record"])
        assert validation.status == "invalid_input"
        assert validation.reason_code == "contradictory_run_repair_status"
        eligibility = handoff.evaluate_repository_repair_handoff_eligibility(case_by_id(case_id)["record"])
        assert eligibility.status == "not_eligible"


@pytest.mark.parametrize("case_id", ["P01", "P02", "P03", "P04"])
def test_eligible_records_validate_and_render(case_id: str) -> None:
    record = validated_record(case_id)
    eligibility = handoff.evaluate_repository_repair_handoff_eligibility(case_by_id(case_id)["record"])
    assert eligibility.status == "eligible"
    prompt = handoff.render_repository_maintenance_prompt(record)
    assert handoff.validate_rendered_repository_maintenance_prompt(prompt).status == "valid"
    positions = [prompt.index(section) for section in handoff.REQUIRED_PROMPT_SECTIONS]
    assert positions == sorted(positions)
    for value in (
        record.incident_id,
        record.source_run_id,
        record.current_run_status,
        record.current_run_repair_status,
        record.first_broken_stage,
        record.first_detection_stage,
        record.repository_gap_state,
        record.repository_gap_class,
        record.repository_gap_hypothesis,
        record.current_run_resume_stage,
    ):
        assert value in prompt


def test_renderer_is_deterministic_and_matches_single_golden_snapshot() -> None:
    record = validated_record("P01")
    first = handoff.render_repository_maintenance_prompt(record)
    second = handoff.render_repository_maintenance_prompt(record)
    assert first == second
    assert first == GOLDEN_PATH.read_text(encoding="utf-8")


def test_renderer_requires_validated_record_and_rejects_fixture_authored_prompt() -> None:
    raw = dict(case_by_id("P01")["record"])
    with pytest.raises(TypeError):
        handoff.render_repository_maintenance_prompt(raw)
    raw["standalone_repair_prompt"] = "arbitrary fixture prompt"
    result = handoff.validate_repository_repair_handoff_record(raw)
    assert result.status == "invalid_input"
    assert result.reason_code == "pre_rendered_prompt_forbidden"


@pytest.mark.parametrize(
    ("case_id", "expected_status", "expected_reason"),
    [
        ("N01", "not_eligible", "current_run_not_stable"),
        ("N02", "not_eligible", "current_run_not_stable"),
        ("N03", "not_eligible", "contradictory_run_repair_status"),
        ("B05", "not_eligible", "contradictory_run_repair_status"),
        ("N04", "not_eligible", "possible_review_suggestion_only"),
        ("N05", "not_eligible", "insufficient_repository_evidence"),
        ("B01", "not_eligible", "not_repository_related"),
        ("B02", "not_eligible", "ordinary_run_error"),
        ("B03", "invalid_input", "unknown_repository_gap_class"),
        ("B04", "invalid_input", "missing_required_field:source_run_id"),
    ],
)
def test_fail_closed_non_emission_cases(case_id: str, expected_status: str, expected_reason: str) -> None:
    result = handoff.evaluate_repository_repair_handoff_eligibility(case_by_id(case_id)["record"])
    assert (result.status, result.reason_code) == (expected_status, expected_reason)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda prompt: prompt.replace("source_run_id: RUN-P01\n", "", 1),
        lambda prompt: prompt.replace("current_run_repair_status: validated\n", "", 1),
        lambda prompt: prompt.replace("repository_gap_state: probable\n", "", 1),
        lambda prompt: prompt.replace("repository_gap_class: fail_late_detection\n", "", 1),
        lambda prompt: prompt.replace("Evaluate the Scope Gate from current repository evidence.", "Evaluate scope from evidence.", 1),
        lambda prompt: prompt.replace("Revalidate the live default branch", "Review the branch", 1),
        lambda prompt: prompt.replace("Verify the exact current Head", "Review the current revision", 1),
        lambda prompt: prompt.replace("fresh independent exact-Head review", "independent review", 1),
        lambda prompt: prompt.replace("merge_performed: false\n", "", 1),
        lambda prompt: prompt.replace("approval_performed: false\n", "", 1),
        lambda prompt: prompt.replace("deployment_performed: false\n", "", 1),
        lambda prompt: prompt.replace("[STOP CONDITIONS]", "[END]", 1),
    ],
)
def test_prompt_mutations_fail_contract_validation(mutation) -> None:
    prompt = handoff.render_repository_maintenance_prompt(validated_record("P01"))
    mutated = mutation(prompt)
    assert mutated != prompt
    result = handoff.validate_rendered_repository_maintenance_prompt(mutated)
    assert result.status == "invalid_prompt"


def test_unknown_repository_facts_remain_visible() -> None:
    prompt = handoff.render_repository_maintenance_prompt(validated_record("P04"))
    assert "repository: unknown" in prompt
    assert "default_branch: unknown" in prompt
    assert "observed_revision: unknown" in prompt
    assert "target repository identity is unknown" in prompt


def test_prompt_preserves_bounded_authority_and_false_action_results() -> None:
    prompt = handoff.render_repository_maintenance_prompt(validated_record("P01"))
    for text in (
        "Create at most one bounded Draft PR.",
        "Do not merge or approve.",
        "Do not deploy or modify repository settings.",
        "merge_performed: false",
        "approval_performed: false",
        "deployment_performed: false",
    ):
        assert text in prompt


def test_tests_use_production_module_as_authority() -> None:
    assert handoff.evaluate_repository_repair_handoff_eligibility.__module__ == "repository_repair_handoff"
    assert handoff.validate_repository_repair_handoff_record.__module__ == "repository_repair_handoff"
    assert handoff.render_repository_maintenance_prompt.__module__ == "repository_repair_handoff"
    source = Path(__file__).read_text(encoding="utf-8")
    assert ("ALLOWED_" + "REPOSITORY_GAP_CLASSES =") not in source
    assert ("emit_full_" + "handoff =") not in source


def test_material_authorities_reference_executable_module_without_competing_predicate() -> None:
    paths = (
        REPO_ROOT / "contracts" / "REPOSITORY_REPAIR_RECOMMENDATION_HANDOFF.md",
        REPO_ROOT / "02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "diagnostics" / "LLM_DEBUG_TRACE_CONTRACT.md",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "scripts/repository_repair_handoff.py" in text
    for path in paths[1:]:
        assert "should_emit_handoff" not in path.read_text(encoding="utf-8")
    debug = paths[-1].read_text(encoding="utf-8")
    assert "repository_repair_handoff_required:" not in debug


def test_contract_names_canonical_functions_and_renderer_authority() -> None:
    contract = (REPO_ROOT / "contracts" / "REPOSITORY_REPAIR_RECOMMENDATION_HANDOFF.md").read_text(encoding="utf-8")
    for function_name in (
        "validate_repository_repair_handoff_record(record)",
        "evaluate_repository_repair_handoff_eligibility(record)",
        "render_repository_maintenance_prompt(validated_record)",
        "validate_rendered_repository_maintenance_prompt(prompt)",
    ):
        assert function_name in contract
    assert "sole executable source for emitted standalone prompt bodies" in contract


def test_run_anchor_and_partial_rerun_authorities_remain_unchanged() -> None:
    partial = (REPO_ROOT / "contracts" / "PARTIAL_RERUN_CONTRACT.md").read_text(encoding="utf-8")
    anchor = (REPO_ROOT / "contracts" / "STAGE_ANCHOR_CONTRACT.md").read_text(encoding="utf-8")
    assert "does not change the earliest safe rerun stage" in partial
    assert "must not embed the full standalone repository-maintenance prompt" in anchor


def test_existing_workflow_runs_targeted_module_and_tests_with_minimum_permissions() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "validate-architect-bootstrap.yml").read_text(encoding="utf-8")
    assert "scripts/repository_repair_handoff.py" in workflow
    assert "python -m py_compile scripts/repository_repair_handoff.py tests/test_repository_repair_recommendation_handoff.py" in workflow
    assert "pytest -q tests/test_repository_repair_recommendation_handoff.py" in workflow
    assert "ref: ${{ github.event.pull_request.head.sha }}" in workflow
    assert "persist-credentials: false" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "contents: write" not in workflow
