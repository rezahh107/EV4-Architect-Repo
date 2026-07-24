from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SPEC = importlib.util.spec_from_file_location(
    "_architect_quality_runtime_public_finalization_test",
    SCRIPTS / "architect_quality_runtime.py",
)
assert SPEC is not None and SPEC.loader is not None
runtime = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runtime
SPEC.loader.exec_module(runtime)
runtime_internal = importlib.import_module("architect_quality_runtime")
assembler = importlib.import_module("architect_runtime_payload_assembler")
contracts = importlib.import_module("architect_project_gate_exporter.contracts")
legacy = importlib.import_module("_legacy_architect_runtime_truth_spine")


def finalize(directory: Path, *, items=None, kind: str = "fixture"):
    return runtime.finalize_project_gate(
        items or legacy.full_outputs(),
        run_context=legacy.context(kind),
        repository_root=ROOT,
        output_directory=directory,
        git_provider=None if kind == "live_conversation" else legacy.FixtureGitProvider(),
    )


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_not_published(result, directory: Path) -> None:
    assert result.finalization_succeeded is False
    assert result.handoff_allowed is False
    assert result.publication_status == "not_published"
    assert not (directory / "architect-project-gate.json").exists()
    assert not (directory / "architect-project-gate-receipt.json").exists()


def test_public_finalization_signature_accepts_stage_history_only() -> None:
    signature = inspect.signature(runtime.finalize_project_gate)
    assert list(signature.parameters) == [
        "stage_outputs",
        "run_context",
        "repository_root",
        "output_directory",
        "git_provider",
    ]
    forbidden = {
        "payload", "payload_path", "stage_results", "run_state", "eligibility",
        "handoff_allowed", "provenance", "digests", "validator_result", "capability",
    }
    assert forbidden.isdisjoint(signature.parameters)
    assert runtime.RUNTIME_INTERFACE_ID == "ev4-architect-quality-runtime@2.0.0"


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "reordered", "mixed", "version"])
def test_invalid_complete_history_never_publishes(tmp_path: Path, mutation: str) -> None:
    items = legacy.full_outputs()
    if mutation == "missing":
        items = items[:-1]
    elif mutation == "duplicate":
        items.insert(5, copy.deepcopy(items[4]))
    elif mutation == "reordered":
        items[4], items[5] = items[5], items[4]
    elif mutation == "mixed":
        items[7]["run_id"] = "OTHER-RUN"
    else:
        items[6]["stage_version"] = "999.0.0"
    assert_not_published(finalize(tmp_path, items=items), tmp_path)


def test_caller_authority_fields_never_publish(tmp_path: Path) -> None:
    for field, value in (
        ("project_gate_payload", {"fabricated": True}),
        ("stage_results", [{"stage_status": "pass"}]),
        ("run_state", {"completed_stages": ["/project-gate-export"]}),
        ("producer_provenance", {"repository": "caller/repo"}),
        ("handoff_allowed", True),
    ):
        items = legacy.full_outputs()
        items[-1][field] = value
        directory = tmp_path / field
        assert_not_published(finalize(directory, items=items), directory)


def test_public_stage_result_contains_only_existing_summary() -> None:
    outcome = runtime.evaluate_run(
        legacy.full_outputs(),
        root=ROOT,
        run_context=legacy.context("fixture"),
        git_provider=legacy.FixtureGitProvider(),
    )
    assert outcome["status"] == "valid", outcome["errors"]
    summary = outcome["results"][-1]["project_gate_export"]
    assert summary["canonical_payload_valid"] is True
    assert "runtime_issued_payload" not in summary
    assert "project_gate_artifact" not in summary
    assert "hashes" not in summary


def test_single_replay_assembly_issue_and_consumption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    counts = {"stage": 0, "assemble": 0, "issue": 0, "consume": 0}
    call_stage = runtime_internal._call_internal_stage
    assemble = assembler.assemble_architect_stage_payload
    issue = assembler._issue_runtime_terminal_payload
    consume = contracts._consume_runtime_terminal_payload

    def counted(name, function):
        def wrapper(*args, **kwargs):
            counts[name] += 1
            return function(*args, **kwargs)
        return wrapper

    monkeypatch.setattr(runtime_internal, "_call_internal_stage", counted("stage", call_stage))
    monkeypatch.setattr(assembler, "assemble_architect_stage_payload", counted("assemble", assemble))
    monkeypatch.setattr(assembler, "_issue_runtime_terminal_payload", counted("issue", issue))
    monkeypatch.setattr(contracts, "_consume_runtime_terminal_payload", counted("consume", consume))

    result = finalize(tmp_path)
    assert result.finalization_succeeded is True
    assert counts == {"stage": 12, "assemble": 1, "issue": 1, "consume": 1}


def test_live_and_synthetic_publication_semantics(tmp_path: Path) -> None:
    live = finalize(tmp_path / "live", kind="live_conversation")
    assert live.finalization_succeeded is True
    assert live.handoff_allowed is True
    assert live.publication_status == "published_allowed"
    assert live.synthetic is False
    assert live.artifact_sha256 == sha256(live.artifact_path)
    assert live.receipt_sha256 == sha256(live.receipt_path)
    assert read_json(live.artifact_path)["handoff"]["allowed"] is True
    assert read_json(live.receipt_path)["finalization"]["status"] == "published_allowed"

    synthetic = finalize(tmp_path / "synthetic")
    assert synthetic.finalization_succeeded is True
    assert synthetic.handoff_allowed is False
    assert synthetic.publication_status == "published_blocked"
    receipt = read_json(synthetic.receipt_path)
    assert receipt["handoff"]["functional_eligibility_would_allow"] is True
    assert receipt["finalization"]["status"] == "published_blocked"


def test_artifact_and_receipt_are_deterministic_and_verified(tmp_path: Path) -> None:
    first = finalize(tmp_path / "first")
    second = finalize(tmp_path / "second")
    assert first.finalization_succeeded and second.finalization_succeeded
    assert first.artifact_path.read_bytes() == second.artifact_path.read_bytes()
    assert first.receipt_path.read_bytes() == second.receipt_path.read_bytes()
    assert first.artifact_sha256 == second.artifact_sha256
    assert first.receipt_sha256 == second.receipt_sha256
    receipt = read_json(first.receipt_path)
    assert receipt["stage_history"]["stage_count"] == 12
    assert receipt["stage_history"]["terminal_stage"] == "/project-gate-export"
    assert receipt["payload"]["runtime_issued"] is True
    assert receipt["artifact"]["committed"] is True
