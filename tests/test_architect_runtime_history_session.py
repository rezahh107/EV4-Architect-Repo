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
from architect_project_gate_exporter import base

PREFINAL_DIR = REPO_ROOT / "fixtures/conversational-run/valid/minimal-complete-run"
TERMINAL_PATH = REPO_ROOT / "fixtures/conversational-run/valid/terminal/project-gate-export.json"


class FixtureGitProvider:
    def provenance(self, root: Path):
        return base.GitProvenance(
            "rezahh107/EV4-Architect-Repo", "fixture-history", "9" * 40
        )


def outputs() -> list[dict]:
    return [
        *conversational.load_output_files(PREFINAL_DIR, root=REPO_ROOT),
        json.loads(TERMINAL_PATH.read_text(encoding="utf-8")),
    ]


def context(kind: str = "fixture") -> runtime.RunContext:
    return runtime.RunContext(source_kind=kind)


def resume(items: list[dict]):
    return runtime.resume_run(
        items,
        run_context=context(),
        repository_root=REPO_ROOT,
        git_provider=FixtureGitProvider(),
    )


def state_fields(state: dict | None):
    assert state is not None
    return {
        key: copy.deepcopy(state.get(key))
        for key in (
            "run_id",
            "current_stage",
            "completed_stages",
            "unknown_ledger",
            "selected_candidate_id",
            "selected_candidate_locked",
            "build_tree_digest",
            "implementation_digest",
            "evaluated_stage_outputs",
            "derived_stage_results",
        )
    }


@pytest.mark.parametrize("count", [0, 1, 6, 11, 12])
def test_resume_equals_uninterrupted_session(count: int) -> None:
    items = outputs()
    uninterrupted = resume([])
    for item in items[:count]:
        result = uninterrupted.advance(item)
        assert result["accepted"] is True, result["diagnostics"]
    replayed = resume(items[:count])
    if count == 0:
        assert uninterrupted.run_state is None
        assert replayed.run_state is None
    else:
        assert state_fields(replayed.run_state) == state_fields(uninterrupted.run_state)
    assert replayed.accepted_stage_outputs == uninterrupted.accepted_stage_outputs
    assert replayed.derived_stage_results == uninterrupted.derived_stage_results


def test_session_failure_does_not_corrupt_prior_state() -> None:
    items = outputs()
    session = resume(items[:7])
    before = session.projection
    bad = copy.deepcopy(items[7])
    bad["canonical_content"]["nodes"].append(
        {"id": "orphan", "role": "editable_content", "children": []}
    )
    result = session.advance(bad)
    assert result["accepted"] is False
    assert session.projection == before


@pytest.mark.parametrize(
    "mutator, code",
    [
        (lambda items: items.pop(4), "RUNTIME_STAGE_ORDER_MISMATCH"),
        (lambda items: items.insert(2, copy.deepcopy(items[1])), "RUNTIME_STAGE_DUPLIATE"),
        (lambda items: items.__setitem__(slice(1, 3), [items[2], items[1]]), "RUNTIME_STAGE_ORDER_MISMATCH"),
        (lambda items: items[2].__setitem__("stage_id", "/unknown"), "RUNTIME_STAGE_ID_UNKNOWN"),
        (lambda items: items[2].__setitem__("run_id", "another-run"), "RUNTIME_RUN_HISTORY_MIXED"),
    ],
)
def test_invalid_history_is_rejected(mutator, code: str) -> None:
    items = copy.deepcopy(outputs()[:6])
    mutator(items)
    with pytest.raises(runtime.RunSequenceValidationError) as caught:
        resume(items)
    assert code in str(caught.value)


def test_caller_state_cannot_advance_or_forge_authority() -> None:
    items = outputs()
    forged = {
        "run_id": items[0]["run_id"],
        "current_stage": "/build-tree",
        "completed_stages": [item["stage_id"] for item in items[:7]],
        "derived_stage_results": [{"stage_id": "/recommend", "stage_status": "pass"}],
        "stage_result_digests": {"/recommend": "sha256:" + "a" * 64},
        "selected_candidate_id": "FORGED",
        "selected_candidate_locked": True,
        "unknown_ledger": [],
        "handoff_allowed": True,
        "evaluated_stage_outputs": [],
    }
    with pytest.raises(runtime.RunSequenceValidationError):
        runtime.evaluate_stage(
            "/build-tree",
            items[7],
            forged,
            root=REPO_ROOT,
            run_context=context(),
            git_provider=FixtureGitProvider(),
        )


def test_legacy_state_fields_are_ignored_when_history_is_valid() -> None:
    items = outputs()
    canonical = resume(items[:7])
    forged = canonical.run_state
    assert forged is not None
    forged["current_stage"] = "/project-gate-export"
    forged["completed_stages"] = [item["stage_id"] for item in items]
    forged["derived_stage_results"] = [{"stage_id": "/recommend", "stage_status": "pass"}]
    forged["selected_candidate_id"] = "FORGED"
    forged["selected_candidate_locked"] = True
    forged["unknown_ledger"] = [{"unknown_id": "FORGED", "status": "active"}]
    result, next_state = runtime.evaluate_stage(
        "/build-tree",
        items[7],
        forged,
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
     )
    assert result["stage_status"] == "pass"
    assert next_state["selected_candidate_id"] == "ARCH-FAM-C"
    assert all(item.get("unknown_id") != "FORGED" for item in next_state["unknown_ledger"])


def test_terminal_replay_ignores_stale_results_digests_locks_and_unknowns() -> None:
    items = outputs()
    baseline = runtime.evaluate_run(
        items,
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
     )
    assert baseline["status"] == "valid", baseline["errors"]
    forged = copy.deepcopy(baseline["run_state"])
    forged["evaluated_stage_outputs"] = forged["evaluated_stage_outputs"][:-1]
    forged["derived_stage_results"] = []
    forged["selected_candidate_id"] = "FORGED"
    forged["selected_candidate_locked"] = False
    forged["unknown_ledger"] = [{"unknown_id": "STALE", "status": "active"}]
    forged["build_tree_digest"] = "sha256:" + "0" * 64
    result, _ = runtime.evaluate_stage(
        "/project-gate-export",
        items[-1],
        forged,
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
    )
    assert result["stage_status"] == "pass"
    assert result["project_gate_export"] == baseline["results"][-1]["project_gate_export"]


def test_terminal_missing_intermediate_stage_never_issues_payload() -> None:
    items = outputs()
    invalid = items[:4] + items[5:]
    outcome = runtime.evaluate_run(
        invalid,
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
    )
    assert outcome["status"] == "invalid"
    assert not any(item.get("project_gate_export") for item in outcome["results"])


@pytest.mark.parametrize("boundary", ["/research", "/score-evidence", "/recommend", "/implementation", "/project-gate-export"])
def test_partial_rerun_is_history_truncation_and_fresh_replay(boundary: str) -> None:
    items = outputs()
    items[4]["unknown_introductions"] = [
        {
            "unknown_id": "U-at-boundary",
            "statement": "Introduced at score evidence.",
            "downstream_critical": False,
        }
    ]
    complete = runtime.evaluate_run(
        items,
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
    )
    assert complete["status"] == "valid", complete["errors"]
    rerun = runtime.apply_partial_rerun(
        complete["run_state"],
        boundary,
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
    )
    index = [item["stage_id"] for item in items].index(boundary)
    fresh = resume(items[:index])
    assert state_fields(rerun["preserved_state"]) == state_fields(
        fresh.run_state or runtime.initial_run_state(items[0]["run_id"], root=REPO_ROOT)
    )
    assert rerun["retained_outputs"] == items[:index]
    if index <= 4:
        assert "U-at-boundary" in rerun["discarded_unknowns"]
        assert all(
            item.get("unknown_id") != "U-at-boundary"
            for item in rerun["preserved_state"]["unknown_ledger"]
         )


def test_live_provider_injection_is_typed_and_rejected() -> None:
    outcome = runtime.evaluate_run(
        outputs(),
        root=REPO_ROOT,
        run_context=context("live_conversation"),
        git_provider=FixtureGitProvider(),
    )
    assert outcome["status"] == "invalid"
    assert any("RUNTIME_LIVE_GIT_PROVIDER_INJECTION_FORBIDDEN" in error for error in outcome["errors"])


def test_fixture_provider_injection_remains_supported() -> None:
    outcome = runtime.evaluate_run(
        outputs(),
        root=REPO_ROOT,
        run_context=context("fixture"),
        git_provider=FixtureGitProvider(),
    )
    assert outcome["status"] == "valid", outcome["errors"]
    assert outcome["results"][-1]["project_gate_export"]["handoff_allowed"] is False


def test_subprocess_provider_reports_actual_clean_checkout() -> None:
    provenance = runtime.SubprocessGitProvider().provenance(REPO_ROOT)
    expected = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    assert provenance.repository == "rezahh107/EV4-Architect-Repo"
    assert provenance.commit_sha == expected


def _git_repo(tmp_path: Path, remote: str) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "-C", str(root), "init"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Runtime test"], check=True)
    (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "initial"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin", remote], check=True)
    return root


def test_wrong_repository_identity_is_rejected(tmp_path: Path) -> None:
    root = _git_repo(tmp_path, "https://github.com/example/not-architect.git")
    with pytest.raises(runtime.RuntimeEnvironmentError) as caught:
        runtime.SubprocessGitProvider().provenance(root)
    assert "RUNTIME_GIT_REPOSITORY_MISMATCH" in str(caught.value)


def test_dirty_live_checkout_is_rejected(tmp_path: Path) -> None:
    root = _git_repo(tmp_path, "https://github.com/rezahh107/EV4-Architect-Repo.git")
    (root / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(runtime.RuntimeEnvironmentError) as caught:
        runtime.SubprocessGitProvider().provenance(root)
    assert "RUNTIME_GIT_CHECKOUT_DIRTY" in str(caught.value)
