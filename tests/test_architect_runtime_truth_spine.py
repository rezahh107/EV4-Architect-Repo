from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import architect_conversational_stage_output as conversational
import architect_quality_runtime as runtime
import architect_stage_claim_guard as claim_guard
from architect_project_gate_exporter import base

PREFINAL_DIR = REPO_ROOT / "fixtures/conversational-run/valid/minimal-complete-run"
TERMINAL_PATH = REPO_ROOT / "fixtures/conversational-run/valid/terminal/project-gate-export.json"


class FixtureGitProvider:
    def provenance(self, root: Path):
        assert root == REPO_ROOT
        return base.GitProvenance(
            "rezahh107/EV4-Architect-Repo",
            "fixture-exact-head",
            "2" * 40,
        )


def outputs() -> list[dict]:
    return conversational.load_output_files(PREFINAL_DIR, root=REPO_ROOT)


def terminal_output() -> dict:
    return json.loads(TERMINAL_PATH.read_text(encoding="utf-8"))


def full_outputs() -> list[dict]:
    return [*outputs(), terminal_output()]


def context(source_kind: str = "fixture") -> runtime.RunContext:
    return runtime.RunContext(source_kind=source_kind)


def evaluate_prefix(count: int, *, source_kind: str = "fixture"):
    items = outputs()
    state = runtime.initial_run_state(items[0]["run_id"], root=REPO_ROOT)
    results = []
    for output in items[:count]:
        result, state = runtime.evaluate_stage(
            output["stage_id"],
            output,
            state,
            root=REPO_ROOT,
            run_context=context(source_kind),
            git_provider=FixtureGitProvider(),
        )
        assert result["stage_status"] == "pass", result["blocking_issues"]
        results.append(result)
    return items, results, state


def run(items: list[dict] | None = None, *, source_kind: str = "fixture"):
    return runtime.evaluate_run(
        items or full_outputs(),
        root=REPO_ROOT,
        run_context=context(source_kind),
        git_provider=FixtureGitProvider(),
    )


@pytest.mark.parametrize(
    ("stage_index", "mutate"),
    [
        (0, lambda output: output.pop("canonical_content")),
        (3, lambda output: output.__setitem__("canonical_content", {"candidates": []})),
        (
            5,
            lambda output: output.__setitem__(
                "canonical_content",
                {
                    "audit_status": "pass",
                    "eligible_candidates": [],
                    "material_defects": ["contradiction"],
                },
            ),
        ),
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
        output["stage_id"],
        output,
        state,
        root=REPO_ROOT,
        run_context=context(),
    )

    assert result["stage_status"] == "blocked"
    assert result["next_stage"] is None
    assert next_state == state
    assert any(
        issue["issue_id"] == "RUNTIME_STAGE_PREDICATE_FAILED"
        for issue in result["blocking_issues"]
    )


def test_reasoning_complete_does_not_claim_machine_proof() -> None:
    result, _ = runtime.evaluate_stage(
        "/intake",
        outputs()[0],
        runtime.initial_run_state(outputs()[0]["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
        run_context=context(),
    )
    assert result["stage_status"] == "pass"
    assert result["completion_class"] == "reasoning_complete"
    assert "ATTRIBUTED_REASONING_ONLY" in result["quality_check_basis"].values()


def test_every_manifest_check_has_explicit_evaluation_basis() -> None:
    manifest, _ = runtime.load_authority(REPO_ROOT)
    claim_guard.validate_manifest_check_classification(manifest)
    for row in manifest["project_execution_stages"]:
        assert set(row["required_quality_checks"]) == set(
            claim_guard.CHECK_EVALUATION_BASIS[row["stage_id"]]
        )


def test_caller_supplied_terminal_payload_is_rejected() -> None:
    items, _, state = evaluate_prefix(11)
    terminal = terminal_output()
    terminal["project_gate_payload"] = {
        "schema_id": "ev4-architect-stage-payload@1.0.0",
        "synthetic": False,
        "fabricated_lineage": "CALLER-FABRICATED-LINEAGE",
    }

    result, next_state = runtime.evaluate_stage(
        "/project-gate-export",
        terminal,
        state,
        root=REPO_ROOT,
        run_context=context("fixture"),
        git_provider=FixtureGitProvider(),
    )

    assert result["stage_status"] == "blocked"
    assert any(
        issue["issue_id"] == "RUNTIME_CALLER_PROJECT_GATE_PAYLOAD_FORBIDDEN"
        for issue in result["blocking_issues"]
    )
    assert next_state == state


def test_fixture_context_cannot_be_overridden_by_synthetic_false() -> None:
    items, _, state = evaluate_prefix(11)
    terminal = terminal_output()
    terminal["synthetic"] = False
    result, next_state = runtime.evaluate_stage(
        "/project-gate-export",
        terminal,
        state,
        root=REPO_ROOT,
        run_context=context("fixture"),
        git_provider=FixtureGitProvider(),
    )
    assert result["stage_status"] == "blocked"
    assert result["project_gate_export"] is None
    assert next_state == state
    assert any(
        issue["issue_id"] == "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN"
        for issue in result["blocking_issues"]
    )


def test_fixture_context_would_allow_but_actual_handoff_is_false() -> None:
    outcome = run(source_kind="fixture")
    assert outcome["status"] == "valid", outcome["errors"]
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["runtime_issued_payload"]["synthetic"] is True
    assert terminal["functional_eligibility"] == {"would_allow": True, "blockers": []}
    assert terminal["handoff_allowed"] is False
    assert terminal["execution_context"] == {
        "source_kind": "fixture",
        "synthetic": True,
    }


def test_live_context_valid_run_can_reach_allowed_handoff() -> None:
    outcome = run(source_kind="live_conversation")
    assert outcome["status"] == "valid", outcome["errors"]
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["runtime_issued_payload"]["synthetic"] is False
    assert terminal["functional_eligibility"]["would_allow"] is True
    assert terminal["handoff_allowed"] is True


def test_model_cannot_author_run_context_source_kind() -> None:
    item = copy.deepcopy(outputs()[0])
    item["source_kind"] = "live_conversation"
    result, _ = runtime.evaluate_stage(
        "/intake",
        item,
        runtime.initial_run_state(item["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
        run_context=context("fixture"),
    )
    assert result["stage_status"] == "blocked"
    assert any(
        issue["issue_id"] == "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN"
        for issue in result["blocking_issues"]
    )


def test_runtime_assembles_terminal_payload_from_actual_lineage() -> None:
    outcome = run()
    payload = outcome["results"][-1]["project_gate_export"]["runtime_issued_payload"]
    expected = [item["stage_id"] for item in outputs()]
    assert [item["stage"] for item in payload["source_stage_lineage"]] == expected
    assert payload["architecture_identity"]["selected_candidate_id"] == outcome[
        "run_state"
    ]["selected_candidate_id"]
    runtime_data = payload["extension_records"][0]["data"]
    assert set(runtime_data["stage_output_digests"]) == set(expected)
    assert set(runtime_data["stage_result_digests"]) == set(expected)


def test_stage_output_digest_mutation_changes_payload_identity() -> None:
    baseline = run()
    changed = full_outputs()
    changed[0]["check_evidence"]["required_input_captured"]["reason"] += " Mutation."
    mutated = run(changed)
    baseline_terminal = baseline["results"][-1]["project_gate_export"]
    mutated_terminal = mutated["results"][-1]["project_gate_export"]
    assert baseline_terminal["source_payload_digest"] != mutated_terminal[
        "source_payload_digest"
    ]


def test_unresolved_payload_evidence_is_derived_from_unknown_ledger() -> None:
    items = full_outputs()
    items[0]["unknown_introductions"] = [
        {
            "unknown_id": "U-responsive",
            "statement": "Responsive behavior remains unverified.",
            "downstream_critical": False,
        }
    ]
    outcome = run(items)
    assert outcome["status"] == "valid", outcome["errors"]
    payload = outcome["results"][-1]["project_gate_export"]["runtime_issued_payload"]
    assert any(
        item["unresolved_id"] == "U-responsive"
        for item in payload["unresolved_evidence"]
    )


def test_direct_runtime_enforces_conversational_base_schema() -> None:
    item = copy.deepcopy(outputs()[0])
    item.pop("unknown_introductions")
    item.pop("unknown_resolutions")
    item.pop("blockers")

    result, next_state = runtime.evaluate_stage(
        "/intake",
        item,
        runtime.initial_run_state(item["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
        run_context=context(),
    )

    assert result["stage_status"] == "blocked"
    assert any(
        issue["issue_id"] == "RUNTIME_STAGE_OUTPUT_SCHEMA_INVALID"
        for issue in result["blocking_issues"]
    )
    assert next_state["current_stage"] == "/intake"


def test_malformed_prefinal_fixture_returns_structured_diagnostic(tmp_path: Path) -> None:
    directory = tmp_path / "sequence"
    directory.mkdir()
    (directory / "01-intake.json").write_text("{broken", encoding="utf-8")
    errors: list[str] = []
    loaded = conversational.load_output_files(directory, root=REPO_ROOT, errors=errors)
    assert loaded == []
    assert any("invalid JSON" in error for error in errors)


def test_caller_producer_mapping_is_rejected() -> None:
    item = copy.deepcopy(outputs()[0])
    item["producer_provenance"] = {
        "repository": "attacker/repo",
        "ref": "fake",
        "commit_sha": "f" * 40,
    }
    result, _ = runtime.evaluate_stage(
        "/intake",
        item,
        runtime.initial_run_state(item["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
        run_context=context(),
    )
    assert result["stage_status"] == "blocked"
    assert any(
        issue["issue_id"] == "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN"
        for issue in result["blocking_issues"]
    )


def test_subprocess_git_provider_reads_actual_checkout(monkeypatch) -> None:
    responses = {
        ("rev-parse", "--show-toplevel"): (0, str(REPO_ROOT), ""),
        ("remote", "get-url", "origin"): (
            0,
            "https://github.com/rezahh107/EV4-Architect-Repo",
            "",
        ),
        ("symbolic-ref", "--quiet", "--short", "HEAD"): (1, "", ""),
        ("rev-parse", "HEAD"): (0, "a" * 40, ""),
        (
            "-c",
            "core.quotepath=false",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ): (0, "", ""),
    }

    def fake_run(root: Path, *args: str):
        code, stdout, stderr = responses[args]
        return subprocess.CompletedProcess(["git", *args], code, stdout, stderr)

    provider = runtime.SubprocessGitProvider()
    monkeypatch.setattr(provider, "_run", fake_run)
    provenance = provider.provenance(REPO_ROOT)
    assert provenance.repository == "rezahh107/EV4-Architect-Repo"
    assert provenance.ref == "detached-exact-head"
    assert provenance.commit_sha == "a" * 40
