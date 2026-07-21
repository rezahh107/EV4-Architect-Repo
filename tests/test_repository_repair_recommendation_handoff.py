from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "fixtures" / "repository-repair-recommendation-handoff"
CONTRACT_PATH = REPO_ROOT / "contracts" / "REPOSITORY_REPAIR_RECOMMENDATION_HANDOFF.md"

ALLOWED_STATES = {"confirmed", "probable"}
ALLOWED_CLASSES = {
    "repository_enforcement_gap",
    "contract_ambiguity",
    "validator_gap",
    "missing_negative_regression",
    "stage_boundary_escape_route",
    "conflicting_authorities",
    "fail_late_detection",
    "repeatable_prompt_or_protocol_defect",
}
REQUIRED_HANDOFF_FIELDS = {
    "handoff_schema",
    "incident_id",
    "source_run_id",
    "current_run_status",
    "current_run_repair_status",
    "repository_gap_state",
    "repository_gap_class",
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
    "standalone_repair_prompt",
}
REQUIRED_PROMPT_SECTIONS = [
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
]


def load_fixture() -> dict:
    fixture = json.loads((FIXTURE_DIR / "index.v1.json").read_text(encoding="utf-8"))
    cases: list[dict] = []
    for path in sorted(FIXTURE_DIR.glob("case-*.v1.json")):
        cases.append(json.loads(path.read_text(encoding="utf-8")))
    grouped = json.loads((FIXTURE_DIR / "non-emitted-cases.v1.json").read_text(encoding="utf-8"))
    cases.extend(grouped["cases"])
    fixture["cases"] = cases
    return fixture


def all_cases() -> list[dict]:
    return load_fixture()["cases"]


def emitted_cases() -> list[dict]:
    return [case for case in all_cases() if case["should_emit_handoff"]]


def non_emitted_cases() -> list[dict]:
    return [case for case in all_cases() if not case["should_emit_handoff"]]


def test_fixture_inventory_is_complete_and_unique() -> None:
    fixture = load_fixture()
    ids = [case["case_id"] for case in fixture["cases"]]
    assert len(ids) == len(set(ids))
    assert set(ids) == {
        "P01", "P02", "P03", "P04",
        "N01", "N02", "N03", "N04", "N05",
        "B01", "B02", "B03", "B04", "B05",
    }
    assert set(fixture["allowed_repository_gap_states"]) == ALLOWED_STATES
    assert set(fixture["allowed_repository_gap_classes"]) == ALLOWED_CLASSES


def test_handoff_appears_only_for_allowed_states_and_classes() -> None:
    for case in all_cases():
        eligible = (
            case["repository_gap_state"] in ALLOWED_STATES
            and case["repository_gap_class"] in ALLOWED_CLASSES
            and not case["ordinary_run_error"]
        )
        assert case["should_emit_handoff"] is eligible


def test_ordinary_run_errors_and_possible_state_do_not_emit_prompt() -> None:
    for case in non_emitted_cases():
        assert case["handoff"] is None
    possible = next(case for case in all_cases() if case["case_id"] == "B03")
    assert possible["repository_gap_state"] == "possible"
    assert "full maintenance prompt" in possible["allowed_message"]


def test_emitted_handoffs_have_explicit_semantic_fields() -> None:
    for case in emitted_cases():
        handoff = case["handoff"]
        assert set(handoff) == REQUIRED_HANDOFF_FIELDS
        assert handoff["handoff_schema"] == "ev4-repository-repair-recommendation-handoff@1.0.0"
        assert handoff["repository_gap_state"] in ALLOWED_STATES
        assert handoff["repository_gap_class"] in ALLOWED_CLASSES
        assert handoff["current_run_status"] in {"repaired", "blocked", "terminal"}
        assert "modify_repository_inside_active_architect_run" in handoff["forbidden_actions"]


def test_run_repair_and_repository_repair_remain_separate() -> None:
    for case in emitted_cases():
        handoff = case["handoff"]
        prompt = handoff["standalone_repair_prompt"]
        assert handoff["current_run_repair_status"]
        assert "The active Architect Run must not edit repository files or create a PR." in prompt
        if handoff["current_run_status"] == "repaired":
            assert handoff["current_run_resume_stage"] == handoff["first_broken_stage"]
        else:
            assert handoff["current_run_resume_stage"] in {"none", handoff["first_broken_stage"]}


def test_prompt_is_self_contained_and_ordered() -> None:
    for case in emitted_cases():
        prompt = case["handoff"]["standalone_repair_prompt"]
        positions = [prompt.index(section) for section in REQUIRED_PROMPT_SECTIONS]
        assert positions == sorted(positions)
        assert "Do not assume access to the original Architect conversation." in prompt
        assert "repository:" in prompt
        assert "incident_id:" in prompt


def test_prompt_requires_live_repository_verification_and_solution_comparison() -> None:
    for case in emitted_cases():
        prompt = case["handoff"]["standalone_repair_prompt"]
        assert "Revalidate the live default branch and exact current Head." in prompt
        assert "Inspect current AGENTS.md, STATUS.md, active overrides" in prompt
        assert "Identify at least two materially different repair options" in prompt
        assert "Select the smallest complete solution." in prompt


def test_prompt_does_not_treat_architect_diagnosis_as_authoritative() -> None:
    required = (
        "The incident description is evidence to investigate, not an authoritative diagnosis.\n"
        "The repository-maintenance model must verify or reject the hypothesis from live repository evidence."
    )
    for case in emitted_cases():
        assert required in case["handoff"]["standalone_repair_prompt"]


def test_prompt_forbids_merge_approval_and_unbounded_write() -> None:
    for case in emitted_cases():
        prompt = case["handoff"]["standalone_repair_prompt"]
        assert "Do not merge or approve." in prompt
        assert "Do not enable auto-merge, deploy, release, or modify repository settings." in prompt
        assert "Only after Scope Gate is authorized" in prompt
        assert "Create one bounded Draft PR only after Scope and validation succeed." in prompt


def test_prompt_requests_independent_exact_head_review() -> None:
    for case in emitted_cases():
        prompt = case["handoff"]["standalone_repair_prompt"]
        assert "fresh independent exact-Head review" in prompt
        assert "Any Head change makes prior review stale." in prompt


def test_unknown_repository_details_remain_explicit() -> None:
    case = next(case for case in emitted_cases() if case["case_id"] == "B04")
    prompt = case["handoff"]["standalone_repair_prompt"]
    assert "repository: [TARGET_REPOSITORY_OR_UNKNOWN]" in prompt
    assert "observed_revision: unknown" in prompt
    assert "exact affected Validator path: unknown" in prompt


def test_no_hidden_chain_of_thought_is_requested() -> None:
    forbidden_requests = {
        "show your chain-of-thought",
        "reveal your hidden reasoning",
        "provide private reasoning",
    }
    for case in emitted_cases():
        prompt = case["handoff"]["standalone_repair_prompt"].lower()
        assert forbidden_requests.isdisjoint({phrase for phrase in forbidden_requests if phrase in prompt})
        assert "do not request hidden chain-of-thought" in prompt


def test_controlled_contract_markers_and_non_authority_are_present() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    assert "<!-- EV4_REPOSITORY_REPAIR_HANDOFF_USER_SECTION_START -->" in contract
    assert "<!-- EV4_REPOSITORY_REPAIR_HANDOFF_USER_SECTION_END -->" in contract
    assert "<!-- EV4_REPOSITORY_REPAIR_HANDOFF_PROMPT_START -->" in contract
    assert "<!-- EV4_REPOSITORY_REPAIR_HANDOFF_PROMPT_END -->" in contract
    assert "A Repository Repair Recommendation Handoff is not:" in contract
    assert "a Stage Artifact;" in contract
    assert "a Stage Anchor;" in contract
    assert "proof that a repository defect exists;" in contract


def test_repository_recommendation_does_not_replace_run_anchor() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    partial = (REPO_ROOT / "contracts" / "PARTIAL_RERUN_CONTRACT.md").read_text(encoding="utf-8")
    anchor = (REPO_ROOT / "contracts" / "STAGE_ANCHOR_CONTRACT.md").read_text(encoding="utf-8")
    assert "does not replace a Repair Anchor or Success Anchor" in contract
    assert "does not change the earliest safe rerun stage" in partial
    assert "must not embed the full standalone repository-maintenance prompt" in anchor


def test_active_project_instructions_prohibit_repository_edits() -> None:
    overrides = (REPO_ROOT / "02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md").read_text(encoding="utf-8")
    agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "must not edit repository files from inside the active Architect Run" in overrides
    assert "must not modify repository files or create a repository PR" in agents
    assert "confirmed" in overrides and "probable" in overrides
    assert "possible" in overrides and "no full standalone maintenance prompt" in overrides


def test_debug_trace_extension_uses_closed_states_and_classes() -> None:
    debug = (REPO_ROOT / "diagnostics" / "LLM_DEBUG_TRACE_CONTRACT.md").read_text(encoding="utf-8")
    for field in (
        "incident_class",
        "repository_gap_state",
        "repository_gap_class",
        "repository_gap_evidence",
        "repository_repair_handoff_required",
        "repository_repair_handoff_reason",
    ):
        assert field in debug
    for state in ("confirmed", "probable", "possible", "insufficient_evidence", "not_repository_related"):
        assert state in debug


def test_workflow_runs_targeted_handoff_tests() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "validate-architect-bootstrap.yml").read_text(encoding="utf-8")
    assert "contracts/REPOSITORY_REPAIR_RECOMMENDATION_HANDOFF.md" in workflow
    assert "fixtures/repository-repair-recommendation-handoff/**" in workflow
    assert "tests/test_repository_repair_recommendation_handoff.py" in workflow
    assert "pytest -q tests/test_repository_repair_recommendation_handoff.py" in workflow


def test_fixture_serialization_is_deterministic() -> None:
    parsed = load_fixture()
    first = json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    second = json.dumps(json.loads(first), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert first == second
