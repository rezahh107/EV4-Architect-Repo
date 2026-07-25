from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import architect_conversational_stage_output as conversational
import architect_quality_runtime as runtime
from architect_project_gate_exporter import base

PREFINAL_DIR = REPO_ROOT / "fixtures/conversational-run/valid/minimal-complete-run"
TERMINAL_PATH = REPO_ROOT / "fixtures/conversational-run/valid/terminal/project-gate-export.json"


class FixtureGitProvider:
    def provenance(self, root: Path):
        assert root == REPO_ROOT
        return base.GitProvenance(
            "rezahh107/EV4-Architect-Repo",
            "fixture-exact-head",
            "1" * 40,
        )


def outputs() -> list[dict]:
    return [
        *conversational.load_output_files(PREFINAL_DIR, root=REPO_ROOT),
        json.loads(TERMINAL_PATH.read_text(encoding="utf-8")),
    ]


def context(source_kind: str = "fixture", refs: frozenset[str] = frozenset()):
    return runtime.RunContext(source_kind=source_kind, verified_evidence_refs=refs)


def evaluate_prefix(items: list[dict], count: int, *, run_context=None):
    ctx = run_context or context()
    state = runtime.initial_run_state(items[0]["run_id"], root=REPO_ROOT)
    results = []
    for output in items[:count]:
        result, state = runtime.evaluate_stage(
            output["stage_id"],
            output,
            state,
            root=REPO_ROOT,
            run_context=ctx,
            git_provider=FixtureGitProvider(),
        )
        results.append(result)
        assert result["stage_status"] == "pass", result["blocking_issues"]
    return results, state


def test_full_pipeline_is_evaluator_derived_and_passes() -> None:
    outcome = runtime.evaluate_run(
        outputs(),
        root=REPO_ROOT,
        run_context=context("fixture"),
        git_provider=FixtureGitProvider(),
    )
    assert outcome["status"] == "valid", outcome["errors"]
    assert outcome["all_required_stages_visited"] is True
    assert all(
        item["evaluated_stage_output_digest"].startswith("sha256:")
        for item in outcome["results"]
    )
    assert [item["completion_class"] for item in outcome["results"][:5]] == [
        "reasoning_complete"
    ] * 5
    assert all(
        item["completion_class"] == "validated_pass"
        for item in outcome["results"][5:]
    )
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["source_payload_digest"].startswith("sha256:")
    assert terminal["export_digest"].startswith("sha256:")
    assert terminal["legacy_export_substituted"] is False
    assert terminal["runtime_issued_payload"]["synthetic"] is True
    assert terminal["functional_eligibility"]["would_allow"] is True
    assert terminal["handoff_allowed"] is False


def test_serialized_stage_result_is_informational_only() -> None:
    results, _ = evaluate_prefix(outputs(), 1)
    errors = runtime.validate_stage_result(results[0], root=REPO_ROOT)
    assert any("informational only" in error for error in errors)


@pytest.mark.parametrize(
    "field",
    [
        "status",
        "stage_status",
        "checks",
        "quality_checks",
        "next_stage",
        "build_tree_digest",
        "synthetic",
        "source_kind",
        "producer_provenance",
    ],
)
def test_caller_authority_fields_cannot_grant_pass(field: str) -> None:
    item = copy.deepcopy(outputs()[0])
    item[field] = "pass"
    state = runtime.initial_run_state(item["run_id"], root=REPO_ROOT)
    with pytest.raises(runtime.StageOutputValidationError) as caught:
        runtime.evaluate_stage(
            "/intake", item, state, root=REPO_ROOT, run_context=context()
        )
    assert any(
        diagnostic.code == "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN"
        and diagnostic.path == field
        for diagnostic in caught.value.diagnostics
    )
    assert state["completed_stages"] == []


def test_unknown_and_missing_stage_checks_fail_closed() -> None:
    item = copy.deepcopy(outputs()[0])
    item["check_evidence"]["anything"] = {
        "claim": "Invented check.",
        "reason": "Invented check.",
    }
    item["check_evidence"].pop("required_input_captured")
    result, _ = runtime.evaluate_stage(
        "/intake",
        item,
        runtime.initial_run_state(item["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
        run_context=context(),
    )
    ids = {issue["issue_id"] for issue in result["blocking_issues"]}
    assert "RUNTIME_UNKNOWN_CHECK" in ids
    assert "RUNTIME_REQUIRED_CHECK_CLAIM_MISSING" in ids
    assert "completion_class" not in result


def test_model_authored_result_is_ignored() -> None:
    item = copy.deepcopy(outputs()[0])
    for record in item["check_evidence"].values():
        record["result"] = "fail"
    result, _ = runtime.evaluate_stage(
        "/intake",
        item,
        runtime.initial_run_state(item["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
        run_context=context(),
    )
    assert result["stage_status"] == "pass"
    assert all(value == "pass" for value in result["quality_checks"].values())
    assert set(result["runtime_context"]["legacy_check_results_ignored"]) == set(
        item["check_evidence"]
    )


def test_no_platform_question_is_valid_research_noop() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 1)
    result, _ = runtime.evaluate_stage(
        "/research", items[1], state, root=REPO_ROOT, run_context=context()
    )
    assert result["stage_status"] == "pass"
    assert result["research_disposition"] == "no_platform_question"
    assert result["completion_class"] == "reasoning_complete"


def test_active_unknown_is_preserved_without_repetition() -> None:
    items = outputs()
    items[0]["unknown_introductions"] = [
        {
            "unknown_id": "U-test",
            "statement": "Needs later evidence.",
            "downstream_critical": False,
        }
    ]
    _, state = evaluate_prefix(items, 1)
    assert state["unknown_ledger"][0]["status"] == "active"
    result, next_state = runtime.evaluate_stage(
        "/research", items[1], state, root=REPO_ROOT, run_context=context()
    )
    assert result["stage_status"] == "pass"
    assert next_state["unknown_ledger"][0]["status"] == "active"


def test_unknown_resolution_requires_explicit_note() -> None:
    items = outputs()
    items[0]["unknown_introductions"] = [
        {
            "unknown_id": "U-test",
            "statement": "Needs resolution.",
            "downstream_critical": False,
        }
    ]
    _, state = evaluate_prefix(items, 4)
    bad = copy.deepcopy(items[4])
    bad["unknown_resolutions"] = [
        {
            "unknown_id": "U-test",
            "resolution_type": "user_confirmation",
            "note": "",
        }
    ]
    with pytest.raises(runtime.StageOutputValidationError) as caught:
        runtime.evaluate_stage(
            "/score-evidence", bad, state, root=REPO_ROOT, run_context=context()
        )
    assert any(
        diagnostic.code == "RUNTIME_STAGE_OUTPUT_SCHEMA_INVALID"
        and diagnostic.path == "unknown_resolutions.0.note"
        for diagnostic in caught.value.diagnostics
    )
    assert state["current_stage"] == "/score-evidence"


def test_downstream_critical_unknown_rejects_arbitrary_evidence() -> None:
    items = outputs()
    items[0]["unknown_introductions"] = [
        {
            "unknown_id": "U-critical",
            "statement": "Required evidence is missing.",
            "downstream_critical": True,
        }
    ]
    _, state = evaluate_prefix(items, 4)
    bad = copy.deepcopy(items[4])
    bad["unknown_resolutions"] = [
        {
            "unknown_id": "U-critical",
            "resolution_type": "validated_artifact",
            "note": "Caller claims evidence exists.",
            "evidence_ref": "arbitrary-string",
        }
    ]
    result, _ = runtime.evaluate_stage(
        "/score-evidence", bad, state, root=REPO_ROOT, run_context=context()
    )
    assert result["stage_status"] == "blocked"
    assert "completion_class" not in result
    assert any(
        issue["issue_id"] == "RUNTIME_CRITICAL_UNKNOWN_EVIDENCE_REQUIRED"
        for issue in result["blocking_issues"]
    )


def test_candidate_lock_rejects_downstream_substitution() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 7)
    bad = copy.deepcopy(items[7])
    bad["decision_input"]["selected_candidate_id"] = "ARCH-FAM-X"
    result, _ = runtime.evaluate_stage(
        "/build-tree", bad, state, root=REPO_ROOT, run_context=context()
    )
    assert result["stage_status"] == "blocked"
    assert "completion_class" not in result
    assert any(
        issue["issue_id"] == "RUNTIME_CANDIDATE_DRIFT"
        for issue in result["blocking_issues"]
    )


def test_build_tree_digest_is_computed_from_real_content() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 7)
    result, _ = runtime.evaluate_stage(
        "/build-tree", items[7], state, root=REPO_ROOT, run_context=context()
    )
    assert result["decision_state"]["build_tree_digest"] == runtime._digest(
        items[7]["canonical_content"]
    )


def test_implementation_null_or_fabricated_fidelity_cannot_pass() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 8)

    missing = copy.deepcopy(items[8])
    missing["canonical_content"].pop("approved_build_tree")
    result, next_state = runtime.evaluate_stage(
        "/implementation", missing, state, root=REPO_ROOT, run_context=context()
    )
    assert result["stage_status"] == "blocked"
    assert "completion_class" not in result
    assert any(
        issue["issue_id"] == "RUNTIME_STAGE_PREDICATE_FAILED"
        for issue in result["blocking_issues"]
    )
    assert next_state == state

    fabricated = copy.deepcopy(items[8])
    fabricated["implementation_tree_digest"] = "sha256:" + "a" * 64
    with pytest.raises(runtime.StageOutputValidationError) as caught:
        runtime.evaluate_stage(
            "/implementation", fabricated, state, root=REPO_ROOT, run_context=context()
        )
    assert any(
        diagnostic.code == "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN"
        and diagnostic.path == "implementation_tree_digest"
        for diagnostic in caught.value.diagnostics
    )


def test_project_gate_boolean_and_payload_cannot_pass() -> None:
    items = outputs()
    _, state = evaluate_prefix(items, 11)
    bad = copy.deepcopy(items[11])
    bad["canonical_payload_valid"] = True
    bad["legacy_export_substituted"] = False
    bad["project_gate_payload"] = {"fabricated": True}
    with pytest.raises(runtime.StageOutputValidationError) as caught:
        runtime.evaluate_stage(
            "/project-gate-export",
            bad,
            state,
            root=REPO_ROOT,
            run_context=context("fixture"),
            git_provider=FixtureGitProvider(),
        )
    codes = {diagnostic.code for diagnostic in caught.value.diagnostics}
    assert "RUNTIME_CALLER_PROJECT_GATE_PAYLOAD_FORBIDDEN" in codes
    assert "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN" in codes


def test_runtime_issued_candidate_matches_run_state() -> None:
    outcome = runtime.evaluate_run(
        outputs(),
        root=REPO_ROOT,
        run_context=context("fixture"),
        git_provider=FixtureGitProvider(),
    )
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["runtime_issued_payload"]["architecture_identity"][
        "selected_candidate_id"
    ] == outcome["run_state"]["selected_candidate_id"]


def test_partial_rerun_reactivates_unknown_and_invalidates_lock() -> None:
    items = outputs()
    items[0]["unknown_introductions"] = [
        {
            "unknown_id": "U-mobile-behavior",
            "statement": "Mobile behavior remains unknown.",
            "downstream_critical": False,
        }
    ]
    items[4]["unknown_resolutions"] = [
        {
            "unknown_id": "U-mobile-behavior",
            "resolution_type": "user_confirmation",
            "note": "Temporary confirmation for this run.",
        }
    ]
    outcome = runtime.evaluate_run(
        items,
        root=REPO_ROOT,
        run_context=context("fixture"),
        git_provider=FixtureGitProvider(),
    )
    rerun = runtime.apply_partial_rerun(
        outcome["run_state"], "/score-evidence", root=REPO_ROOT
    )
    assert "U-mobile-behavior" in rerun["reactivated_unknowns"]
    assert rerun["candidate_lock_invalidated"] is True
    assert rerun["preserved_state"]["selected_candidate_locked"] is False
