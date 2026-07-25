from __future__ import annotations

import ast
import copy
import importlib
import importlib.util
import inspect
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SPEC = importlib.util.spec_from_file_location(
    "_architect_quality_runtime_public_failure_test",
    SCRIPTS / "architect_quality_runtime.py",
)
assert SPEC is not None and SPEC.loader is not None
runtime = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runtime
SPEC.loader.exec_module(runtime)
legacy = importlib.import_module("_legacy_architect_runtime_truth_spine")
finalization = importlib.import_module("architect_project_gate_finalization")
assembler = importlib.import_module("architect_runtime_payload_assembler")
contracts = importlib.import_module("architect_project_gate_exporter.contracts")


REQUEST_DIAGNOSTIC = "RUNTIME_PROJECT_GATE_EXPORT_REQUEST_INVALID"


def finalize(directory: Path, *, items=None, kind: str = "fixture"):
    return runtime.finalize_project_gate(
        items or legacy.full_outputs(),
        run_context=legacy.context(kind),
        repository_root=ROOT,
        output_directory=directory,
        git_provider=None if kind == "live_conversation" else legacy.FixtureGitProvider(),
    )


def assert_not_published(result, directory: Path) -> None:
    assert result.finalization_succeeded is False
    assert result.handoff_allowed is False
    assert result.publication_status == "not_published"
    assert result.artifact_path is None
    assert result.receipt_path is None
    assert not (directory / "architect-project-gate.json").exists()
    assert not (directory / "architect-project-gate-receipt.json").exists()


def _preterminal_state() -> dict:
    _, _, state = legacy.evaluate_prefix(11)
    return copy.deepcopy(state)


def _terminal_call_spies(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    counts = {"assembler": 0, "capability": 0, "exporter": 0}

    def forbidden(name: str):
        def fail(*args, **kwargs):
            counts[name] += 1
            raise AssertionError(f"{name} must not run for invalid terminal input")

        return fail

    monkeypatch.setattr(
        assembler,
        "assemble_architect_stage_payload",
        forbidden("assembler"),
    )
    monkeypatch.setattr(
        assembler,
        "_issue_runtime_terminal_payload",
        forbidden("capability"),
    )
    monkeypatch.setattr(contracts, "build_export", forbidden("exporter"))
    return counts


def _mutate_terminal(case: str) -> tuple[list[dict], str]:
    items = legacy.full_outputs()
    terminal = items[-1]
    if case == "missing_request":
        terminal.pop("export_request", None)
        terminal.pop("presentation_note", None)
        return items, "export_request"
    if case == "empty_request":
        terminal["export_request"] = {}
        return items, "export_request"
    if case == "null_request":
        terminal["export_request"] = None
        return items, "export_request"
    if case == "string_request":
        terminal["export_request"] = "producer-gate-export.v1"
        return items, "export_request"
    if case == "missing_format":
        terminal["export_request"] = {"presentation_note": "Present the export."}
        return items, "export_request.format"
    if case == "wrong_format":
        terminal["export_request"] = {"format": "unsupported-export.v9"}
        return items, "export_request.format"
    if case == "nested_note_empty":
        terminal["export_request"] = {
            "format": "producer-gate-export.v1",
            "presentation_note": "",
        }
        return items, "export_request.presentation_note"
    if case == "nested_note_whitespace":
        terminal["export_request"] = {
            "format": "producer-gate-export.v1",
            "presentation_note": "   \t",
        }
        return items, "export_request.presentation_note"
    if case == "top_note_empty":
        terminal.pop("export_request", None)
        terminal["presentation_note"] = ""
        return items, "presentation_note"
    if case == "top_note_whitespace":
        terminal.pop("export_request", None)
        terminal["presentation_note"] = "  \n"
        return items, "presentation_note"
    if case == "canonical_content_empty":
        terminal["canonical_content"] = {}
        return items, "canonical_content"
    if case == "canonical_content_arbitrary":
        terminal["canonical_content"] = {"replace_request": True}
        return items, "canonical_content"
    if case == "check_evidence_only":
        terminal.pop("export_request", None)
        terminal.pop("presentation_note", None)
        assert terminal["check_evidence"]
        return items, "export_request"
    if case == "unsupported_terminal_content":
        terminal.pop("export_request", None)
        terminal["handoff_package"] = {"format": "producer-gate-export.v1"}
        return items, "handoff_package"
    raise AssertionError(f"Unknown case: {case}")


def test_request_validation_is_first_executable_boundary_statement() -> None:
    source = textwrap.dedent(inspect.getsource(finalization.evaluate_project_gate_execution))
    function = ast.parse(source).body[0]
    assert isinstance(function, ast.FunctionDef)
    statements = function.body
    assert isinstance(statements[0], ast.Expr)
    assert isinstance(statements[0].value, ast.Constant)
    first = statements[1]
    assert isinstance(first, ast.Expr)
    assert isinstance(first.value, ast.Call)
    assert isinstance(first.value.func, ast.Name)
    assert first.value.func.id == "_validate_terminal_export_request"


@pytest.mark.parametrize(
    "case",
    [
        "missing_request",
        "empty_request",
        "null_request",
        "string_request",
        "missing_format",
        "wrong_format",
        "nested_note_empty",
        "nested_note_whitespace",
        "top_note_empty",
        "top_note_whitespace",
        "canonical_content_empty",
        "canonical_content_arbitrary",
        "check_evidence_only",
        "unsupported_terminal_content",
    ],
)
def test_invalid_terminal_request_fails_before_payload_authority_and_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    items, expected_path = _mutate_terminal(case)
    before = _preterminal_state()
    counts = _terminal_call_spies(monkeypatch)
    directory = tmp_path / case

    result = finalize(directory, items=items)

    assert_not_published(result, directory)
    assert result.run_state == before
    assert len(result.stage_results) == 11
    assert counts == {"assembler": 0, "capability": 0, "exporter": 0}
    assert any(
        diagnostic["code"] == REQUEST_DIAGNOSTIC
        and diagnostic["path"] == expected_path
        for diagnostic in result.diagnostics
    )
    assert [
        (item.get("path") or "", item.get("message") or "")
        for item in result.diagnostics
    ] == sorted(
        (item.get("path") or "", item.get("message") or "")
        for item in result.diagnostics
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("project_gate_payload", {"fabricated": True}),
        ("handoff_allowed", True),
        ("stage_results", [{"stage_status": "pass"}]),
        ("run_state", {"completed_stages": ["/project-gate-export"]}),
    ],
)
def test_valid_request_with_caller_authority_fails_before_terminal_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value,
) -> None:
    items = legacy.full_outputs()
    items[-1][field] = value
    observed_input = copy.deepcopy(items)
    counts = _terminal_call_spies(monkeypatch)
    directory = tmp_path / field

    result = finalize(directory, items=items)

    assert_not_published(result, directory)
    assert items == observed_input
    assert result.run_state is None
    assert result.stage_results == ()
    assert counts == {"assembler": 0, "capability": 0, "exporter": 0}
    assert any(
        item["code"] == "RUNTIME_CALLER_FINALIZATION_AUTHORITY_FIELD_FORBIDDEN"
        and item["path"] == f"history[11].{field}"
        for item in result.diagnostics
    )


def test_caller_authority_diagnostic_order_is_deterministic(tmp_path: Path) -> None:
    items = legacy.full_outputs()
    items[-1]["stage_results"] = []
    items[-1]["handoff_allowed"] = True
    items[-1]["run_state"] = {}

    result = finalize(tmp_path, items=items)

    assert_not_published(result, tmp_path)
    paths = [item["path"] for item in result.diagnostics]
    assert paths == sorted(paths)


@pytest.mark.parametrize(
    "terminal",
    [
        {"export_request": {"format": "producer-gate-export.v1"}},
        {
            "export_request": {
                "format": "producer-gate-export.v1",
                "presentation_note": "Publish the official export.",
            }
        },
        {"presentation_note": "Publish the official Project Gate export."},
    ],
)
def test_supported_terminal_request_forms_finalize_successfully(
    tmp_path: Path,
    terminal: dict,
) -> None:
    items = legacy.full_outputs()
    items[-1].pop("export_request", None)
    items[-1].pop("presentation_note", None)
    items[-1].update(copy.deepcopy(terminal))

    result = finalize(tmp_path / str(len(str(terminal))), items=items)

    assert result.finalization_succeeded is True
    assert result.handoff_allowed is False
    assert result.publication_status == "published_blocked"
    assert result.artifact_path and result.artifact_path.exists()
    assert result.receipt_path and result.receipt_path.exists()


def test_publication_inside_architect_repository_is_forbidden(tmp_path: Path) -> None:
    directory = ROOT / ".test-project-gate-publication"
    try:
        assert_not_published(finalize(directory), directory)
    finally:
        for path in (
            directory / "architect-project-gate.json",
            directory / "architect-project-gate-receipt.json",
        ):
            path.unlink(missing_ok=True)
        directory.rmdir() if directory.exists() else None


def test_contract_or_hash_failure_prevents_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args, **kwargs):
        raise contracts.ExportError(
            "ARCH_EXPORT_TEST_HASH_FAILURE", "hash_self_verification",
            "Injected hash failure.", "repository_owner"
        )

    monkeypatch.setattr(contracts, "verify_hashes", fail)
    assert_not_published(finalize(tmp_path), tmp_path)


def test_artifact_write_failure_does_not_publish_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        finalization,
        "_publish_no_replace",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("artifact failed")),
    )
    assert_not_published(finalize(tmp_path), tmp_path)


def test_receipt_write_failure_removes_owned_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = finalization._publish_no_replace
    calls = 0

    def fail_second(staged: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("receipt failed")
        original(staged, destination)

    monkeypatch.setattr(finalization, "_publish_no_replace", fail_second)
    assert_not_published(finalize(tmp_path), tmp_path)


def test_existing_destination_fails_closed(tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    artifact = tmp_path / "architect-project-gate.json"
    artifact.write_text("caller-owned", encoding="utf-8")
    result = finalize(tmp_path)
    assert result.finalization_succeeded is False
    assert artifact.read_text(encoding="utf-8") == "caller-owned"
    assert not (tmp_path / "architect-project-gate-receipt.json").exists()
