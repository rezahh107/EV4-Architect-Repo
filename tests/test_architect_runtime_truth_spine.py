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
from architect_project_gate_exporter import base, contracts

PREFINAL_DIR = REPO_ROOT / "fixtures/conversational-run/valid/minimal-complete-run"
TERMINAL_PATH = REPO_ROOT / "fixtures/conversational-run/valid/terminal/project-gate-export.json"


def outputs() -> list[dict]:
    return conversational.load_output_files(PREFINAL_DIR, root=REPO_ROOT)


def terminal_output() -> dict:
    return json.loads(TERMINAL_PATH.read_text(encoding="utf-8"))


def evaluate_prefix(count: int):
    items = outputs()
    state = runtime.initial_run_state(items[0]["run_id"], root=REPO_ROOT)
    results = []
    for output in items[:count]:
        result, state = runtime.evaluate_stage(
            output["stage_id"], output, state, root=REPO_ROOT
        )
        assert result["stage_status"] == "pass", result["blocking_issues"]
        results.append(result)
    return items, results, state


@pytest.mark.parametrize(
    ("stage_index", "mutate"),
    [
        (0, lambda output: output.pop("canonical_content")),
        (3, lambda output: output.__setitem__("canonical_content", {"candidates": []})),
        (5, lambda output: output.__setitem__("canonical_content", {"audit_status": "pass", "eligible_candidates": [], "material_defects": ["contradiction"]})),
        (9, lambda output: output.__setitem__("canonical_content", {"accepted": True})),
        (10, lambda output: output.__setitem__("canonical_content", {})),
    ],
)
def test_model_authored_pass_cannot_advance_incomplete_stage(stage_index, mutate) -> None:
    items, _, state = evaluate_prefix(stage_index)
    output = copy.deepcopy(items[stage_index])
    for record in output["check_evidence"].values():
        record["result"] = "pass"
        record["reason"] = "FORMALITY_CANARY_MODEL_PASS"
    mutate(output)

    result, next_state = runtime.evaluate_stage(
        output["stage_id"], output, state, root=REPO_ROOT
    )

    assert result["stage_status"] == "blocked"
    assert result["next_stage"] is None
    assert next_state == state


def test_synthetic_false_boolean_cannot_enable_fixture_handoff() -> None:
    payload = terminal_output()["project_gate_payload"]
    assert payload["payload_identity"]["synthetic_fixture_notice"]
    payload["synthetic"] = False
    git = base.GitProvenance(
        "rezahh107/EV4-Architect-Repo",
        "agent/conversational-stage-output-v1",
        "1" * 40,
    )

    contracts.validate_payload(REPO_ROOT, payload)
    export, hashes = contracts.build_export(
        payload, git, "synthetic-bypass-reproduction", "fixture:test-vector"
    )
    contracts.validate_contracts(REPO_ROOT, export)
    contracts.verify_hashes(export, hashes)

    assert export["handoff"]["allowed"] is False


def test_caller_supplied_terminal_payload_is_rejected() -> None:
    items, _, state = evaluate_prefix(11)
    terminal = terminal_output()
    terminal["project_gate_payload"]["evidence_register"][0]["claim"] = (
        "CALLER-FABRICATED-LINEAGE"
    )

    result, next_state = runtime.evaluate_stage(
        "/project-gate-export", terminal, state, root=REPO_ROOT
    )

    assert result["stage_status"] == "blocked"
    assert any(
        issue["issue_id"] == "RUNTIME_CALLER_PROJECT_GATE_PAYLOAD_FORBIDDEN"
        for issue in result["blocking_issues"]
    )
    assert next_state == state


def test_direct_runtime_enforces_conversational_base_schema() -> None:
    item = outputs()[0]
    item.pop("unknown_introductions")
    item.pop("unknown_resolutions")
    item.pop("blockers")

    result, next_state = runtime.evaluate_stage(
        "/intake",
        item,
        runtime.initial_run_state(item["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
    )

    assert result["stage_status"] == "blocked"
    assert any(
        issue["issue_id"] == "RUNTIME_STAGE_OUTPUT_SCHEMA_INVALID"
        for issue in result["blocking_issues"]
    )
    assert next_state["current_stage"] == "/intake"
