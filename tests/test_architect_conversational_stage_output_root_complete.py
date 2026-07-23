from __future__ import annotations

import copy
import json
import shutil
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

PREFINAL_DIR = REPO_ROOT / "fixtures/conversational-run/valid/minimal-complete-run"
TERMINAL_PATH = REPO_ROOT / "fixtures/conversational-run/valid/terminal/project-gate-export.json"
UPLOAD_SET_PATH = REPO_ROOT / conversational.RELEASE_UPLOAD_SET_PATH
STAGE_RESULT_SCHEMA_PATH = REPO_ROOT / conversational.STAGE_RESULT_SCHEMA_PATH


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copy_release_tree(tmp_path: Path) -> Path:
    upload_set = read_json(UPLOAD_SET_PATH)
    paths = {
        *upload_set["minimum_upload_paths"],
        conversational.RELEASE_UPLOAD_SET_PATH.as_posix(),
        conversational.STAGE_RESULT_SCHEMA_PATH.as_posix(),
    }
    for relative in paths:
        source = REPO_ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def mutate_upload_set(root: Path, mutator) -> dict:
    path = root / conversational.RELEASE_UPLOAD_SET_PATH
    value = read_json(path)
    mutator(value)
    write_json(path, value)
    return value


def prefinal_outputs() -> list[dict]:
    return conversational.load_output_files(PREFINAL_DIR, root=REPO_ROOT)


def trusted_context() -> dict:
    sha = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return {
        "producer_provenance": {
            "repository": "rezahh107/EV4-Architect-Repo",
            "ref": "exact-head-root-complete-test",
            "commit_sha": sha,
        }
    }


def evaluate_prefix(outputs: list[dict], count: int):
    state = runtime.initial_run_state(outputs[0]["run_id"], root=REPO_ROOT)
    for output in outputs[:count]:
        result, state = runtime.evaluate_stage(
            output["stage_id"],
            output,
            state,
            root=REPO_ROOT,
        )
        assert result["stage_status"] == "pass", result["blocking_issues"]
    return state


def assert_structured_invalid(outcome: dict, text: str) -> None:
    assert outcome["status"] == "invalid"
    assert any(text in error for error in outcome["errors"]), outcome["errors"]


# Authority classification -------------------------------------------------


def test_authority_classification_is_derived_from_stage_result_schema() -> None:
    schema = read_json(STAGE_RESULT_SCHEMA_PATH)
    classification = runtime.derive_stage_result_authority(schema)

    expected_forbidden = {
        "stage_result_schema",
        "stage_status",
        "blocking_issues",
        "carried_unknowns",
        "quality_checks",
        "next_stage",
        "decision_state",
        "runtime_context",
        "project_gate_export",
        "evaluation_mode",
        "evaluated_stage_output_digest",
        "recommendation_made",
        "hidden_recommendation",
        "unknown_converted_to_exact",
        "selected_candidate_id",
        "selected_candidate_locked",
        "build_tree_digest",
        "approved_build_tree_digest",
        "implementation_tree_digest",
        "architecture_drift",
        "canonical_payload_valid",
        "legacy_export_substituted",
        "source_payload_digest",
        "export_digest",
        "validator_identity",
        "validation_result",
        "export_id",
        "status",
        "checks",
        "implementation_digest",
        "continuation_authorized",
        "official_pass",
        "official_digest",
    }
    assert expected_forbidden <= classification.forbidden_top_level_stage_output_fields
    assert classification.shared_stage_output_fields == {
        "run_id",
        "stage_id",
        "stage_version",
        "research_disposition",
        "final_audit_findings",
    }
    assert runtime.CALLER_AUTHORITY_FIELDS == (
        classification.forbidden_top_level_stage_output_fields
    )


def test_top_level_approved_build_tree_digest_is_rejected() -> None:
    output = copy.deepcopy(prefinal_outputs()[0])
    output["approved_build_tree_digest"] = "sha256:" + "a" * 64

    assert conversational.validate_base_structure(output, root=REPO_ROOT)
    result, _ = runtime.evaluate_stage(
        "/intake",
        output,
        runtime.initial_run_state(output["run_id"], root=REPO_ROOT),
        root=REPO_ROOT,
    )
    assert result["stage_status"] == "blocked"
    assert any(
        issue["issue_id"] == "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN"
        and "approved_build_tree_digest" in issue["reason"]
        for issue in result["blocking_issues"]
    )


@pytest.mark.parametrize(
    ("definition_name", "new_field"),
    [
        ("decision_state", "new_decision_state_authority"),
        ("project_gate_export", "new_project_gate_export_authority"),
        ("runtime_context", "new_runtime_context_authority"),
    ],
)
def test_new_nested_stage_result_property_requires_base_schema_mirror_update(
    tmp_path: Path,
    definition_name: str,
    new_field: str,
) -> None:
    root = copy_release_tree(tmp_path)
    schema_path = root / conversational.STAGE_RESULT_SCHEMA_PATH
    schema = read_json(schema_path)
    schema["$defs"][definition_name]["properties"][new_field] = {"type": "boolean"}
    write_json(schema_path, schema)

    with pytest.raises(ValueError, match="classification mirror update"):
        conversational.load_authority(root)


def test_runtime_and_base_schema_forbidden_sets_cannot_drift(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    schema_path = root / conversational.BASE_SCHEMA_PATH
    schema = read_json(schema_path)
    schema["$defs"]["caller_authority_field"]["enum"].remove(
        "approved_build_tree_digest"
    )
    write_json(schema_path, schema)

    with pytest.raises(ValueError, match="classification mirror update"):
        conversational.load_authority(root)


def test_legitimate_stage_extension_and_approved_tree_content_remain_allowed() -> None:
    output = copy.deepcopy(prefinal_outputs()[8])
    output["stage_specific_extension"] = {"allowed": True}
    assert conversational.validate_base_structure(output, root=REPO_ROOT) == []
    assert "approved_build_tree" in output["canonical_content"]

    state = evaluate_prefix(prefinal_outputs(), 8)
    result, _ = runtime.evaluate_stage(
        "/implementation",
        output,
        state,
        root=REPO_ROOT,
    )
    assert result["stage_status"] == "pass", result["blocking_issues"]


# Filesystem-owned example inventory --------------------------------------


def canonical_examples() -> list[str]:
    errors: list[str] = []
    paths = conversational.canonical_example_paths(root=REPO_ROOT, errors=errors)
    assert not errors
    assert paths
    return paths


@pytest.mark.parametrize("example_path", canonical_examples())
def test_each_example_omitted_from_mirror_is_rejected(
    tmp_path: Path,
    example_path: str,
) -> None:
    root = copy_release_tree(tmp_path)
    mutate_upload_set(
        root,
        lambda value: value["example_paths"].remove(example_path),
    )
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "example mirror omits canonical repository examples")


@pytest.mark.parametrize("example_path", canonical_examples())
def test_each_example_omitted_from_minimum_upload_paths_is_rejected(
    tmp_path: Path,
    example_path: str,
) -> None:
    root = copy_release_tree(tmp_path)
    mutate_upload_set(
        root,
        lambda value: value["minimum_upload_paths"].remove(example_path),
    )
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "minimum upload set omits required sources")


@pytest.mark.parametrize("example_path", canonical_examples())
def test_each_example_omitted_from_both_lists_is_rejected(
    tmp_path: Path,
    example_path: str,
) -> None:
    root = copy_release_tree(tmp_path)

    def remove_both(value: dict) -> None:
        value["example_paths"].remove(example_path)
        value["minimum_upload_paths"].remove(example_path)

    mutate_upload_set(root, remove_both)
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "example mirror omits canonical repository examples")
    assert_structured_invalid(outcome, "minimum upload set omits required sources")


def test_unknown_and_duplicate_example_paths_are_rejected(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    unknown = "examples/conversational-stage-output/unknown.example.json"

    def mutate(value: dict) -> None:
        value["example_paths"].append(unknown)
        value["example_paths"].append(value["example_paths"][0])

    mutate_upload_set(root, mutate)
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "duplicate paths are forbidden")
    assert_structured_invalid(outcome, "non-canonical examples")
    assert_structured_invalid(outcome, "listed example is missing on disk")


@pytest.mark.parametrize(
    "bad_value",
    ["", 7, "../outside.json", "contracts/not-an-example.json"],
)
def test_invalid_example_path_values_are_rejected(
    tmp_path: Path,
    bad_value: object,
) -> None:
    root = copy_release_tree(tmp_path)
    mutate_upload_set(
        root,
        lambda value: value["example_paths"].append(bad_value),
    )
    outcome = conversational.validate_release_upload_set(root=root)
    assert outcome["status"] == "invalid"
    assert any(
        marker in error
        for error in outcome["errors"]
        for marker in (
            "value must be a string",
            "value must be a non-empty string",
            "outside the canonical examples directory",
        )
    )


def test_deleted_listed_example_is_rejected(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    deleted = canonical_examples()[0]
    (root / deleted).unlink()
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "listed example is missing on disk")
    assert_structured_invalid(outcome, "non-canonical examples")


def test_new_repository_example_requires_upload_set_mirror_update(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    source = root / canonical_examples()[0]
    added = root / conversational.EXAMPLES_DIRECTORY / "new-repository.example.json"
    shutil.copy2(source, added)
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "example mirror omits canonical repository examples")
    assert_structured_invalid(outcome, "minimum upload set omits required sources")


def test_malformed_example_json_is_structured_invalid(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    path = root / canonical_examples()[0]
    path.write_text("{not-json", encoding="utf-8")
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "invalid JSON")


def test_example_wrong_stage_version_is_rejected(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    path = root / canonical_examples()[0]
    value = read_json(path)
    value["stage_version"] = "9.9.9"
    write_json(path, value)
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "stage_version")


def test_example_missing_or_cross_stage_check_is_rejected(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    path = root / canonical_examples()[0]
    value = read_json(path)
    value["check_evidence"].pop(next(iter(value["check_evidence"])))
    value["check_evidence"]["cross_stage_check"] = {
        "result": "pass",
        "reason": "Invalid cross-Stage key.",
    }
    write_json(path, value)
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "missing Manifest checks")
    assert_structured_invalid(outcome, "unknown or cross-Stage checks")


def test_canonical_repository_example_inventory_is_valid() -> None:
    outcome = conversational.validate_release_upload_set(root=REPO_ROOT)
    assert outcome["status"] == "valid", outcome["errors"]
    assert outcome["canonical_example_files"] == len(canonical_examples())
    assert outcome["examples_checked"] == len(canonical_examples())


# Structured required-source loading -------------------------------------


def test_missing_contract_returns_structured_invalid(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    (root / conversational.CONTRACT_PATH).unlink()
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "required source is missing")


def test_contract_directory_returns_structured_invalid(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    path = root / conversational.CONTRACT_PATH
    path.unlink()
    path.mkdir()
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "not a regular file")


def test_invalid_utf8_contract_returns_structured_invalid(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    (root / conversational.CONTRACT_PATH).write_bytes(b"\xff\xfe")
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "not valid UTF-8")


@pytest.mark.parametrize(
    "source_path",
    [
        conversational.BASE_SCHEMA_PATH,
        conversational.MANIFEST_PATH,
        conversational.STAGE_RESULT_SCHEMA_PATH,
    ],
)
def test_missing_required_json_source_returns_structured_invalid(
    tmp_path: Path,
    source_path: Path,
) -> None:
    root = copy_release_tree(tmp_path)
    (root / source_path).unlink()
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, f"{source_path.as_posix()}: required source is missing")


@pytest.mark.parametrize(
    "source_path",
    [
        conversational.BASE_SCHEMA_PATH,
        conversational.MANIFEST_PATH,
        conversational.STAGE_RESULT_SCHEMA_PATH,
    ],
)
def test_malformed_required_json_source_returns_structured_invalid(
    tmp_path: Path,
    source_path: Path,
) -> None:
    root = copy_release_tree(tmp_path)
    (root / source_path).write_text("{broken", encoding="utf-8")
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "invalid JSON")


def test_base_schema_json_root_must_be_object(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    write_json(root / conversational.BASE_SCHEMA_PATH, [])
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "JSON root must be an object")


def test_missing_upload_set_returns_structured_invalid(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    (root / conversational.RELEASE_UPLOAD_SET_PATH).unlink()
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "required source is missing")


def test_malformed_upload_set_returns_structured_invalid(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    (root / conversational.RELEASE_UPLOAD_SET_PATH).write_text(
        "{broken",
        encoding="utf-8",
    )
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "invalid JSON")


def test_upload_set_json_root_must_be_object(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    write_json(root / conversational.RELEASE_UPLOAD_SET_PATH, [])
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "JSON root must be an object")


def test_upload_set_required_object_field_type_is_validated(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    mutate_upload_set(root, lambda value: value.__setitem__("contract", []))
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "contract: required field must be an object")


def test_missing_registered_example_returns_structured_invalid(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    path = root / canonical_examples()[0]
    path.unlink()
    outcome = conversational.validate_release_upload_set(root=root)
    assert_structured_invalid(outcome, "listed example is missing on disk")


def run_cli(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "check-architect-conversational-stage-output.py"),
            "--root",
            str(root),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def assert_cli_structured_invalid(completed: subprocess.CompletedProcess[str]) -> None:
    assert completed.returncode != 0
    result = json.loads(completed.stdout)
    assert result["status"] == "invalid"
    assert "Traceback" not in completed.stderr


def test_actual_cli_missing_contract_is_structured_invalid(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    (root / conversational.CONTRACT_PATH).unlink()
    assert_cli_structured_invalid(run_cli(root))


def test_actual_cli_malformed_upload_set_is_structured_invalid(tmp_path: Path) -> None:
    root = copy_release_tree(tmp_path)
    (root / conversational.RELEASE_UPLOAD_SET_PATH).write_text(
        "{broken",
        encoding="utf-8",
    )
    assert_cli_structured_invalid(run_cli(root))


def test_unexpected_programming_error_is_not_silenced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def programming_defect(*, root: Path, errors: list[str]) -> list[str]:
        raise NameError("intentional programming defect")

    monkeypatch.setattr(conversational, "canonical_example_paths", programming_defect)
    with pytest.raises(NameError, match="intentional programming defect"):
        conversational.validate_release_upload_set(root=REPO_ROOT)


# Prior repair regression -------------------------------------------------


def test_terminal_runtime_and_core_release_regressions_remain_closed() -> None:
    outcome = conversational.validate_repository_vectors(root=REPO_ROOT)
    assert outcome["status"] == "valid", outcome["errors"]
    assert outcome["terminal_runtime_validated"] is True
    assert outcome["stages_visited"][-1] == "/project-gate-export"

    release = conversational.validate_release_upload_set(root=REPO_ROOT)
    assert release["status"] == "valid", release["errors"]
    upload_set = read_json(UPLOAD_SET_PATH)
    assert conversational.CORE_RELEASE_PATHS <= set(
        upload_set["minimum_upload_paths"]
    )
