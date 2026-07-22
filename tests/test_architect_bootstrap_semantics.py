from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from typing import Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "check-architect-bootstrap.py"
spec = importlib.util.spec_from_file_location("check_architect_bootstrap", VALIDATOR_PATH)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

CONTROLLED_PATHS = [
    Path("contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md"),
    Path("manifests/architect-conversation-bootstrap.v1.json"),
    Path("manifests/architect-pipeline-manifest.v1.json"),
    Path("schemas/architect-conversation-bootstrap.v1.schema.json"),
]


def copy_fixture(tmp_path: Path) -> Path:
    for relative in CONTROLLED_PATHS:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
    return tmp_path


def load_json(root: Path, relative: str) -> dict:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def write_json(root: Path, relative: str, value: dict) -> None:
    (root / relative).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def wrong_contract_version(root: Path) -> None:
    value = load_json(root, "manifests/architect-conversation-bootstrap.v1.json")
    value["contract_version"] = "1.1.0"
    write_json(root, "manifests/architect-conversation-bootstrap.v1.json", value)


def missing_stage_result_precondition(root: Path) -> None:
    value = load_json(root, "manifests/architect-conversation-bootstrap.v1.json")
    value["activation"]["preconditions"].pop(2)
    write_json(root, "manifests/architect-conversation-bootstrap.v1.json", value)


def restart_instead_of_continue(root: Path) -> None:
    value = load_json(root, "manifests/architect-conversation-bootstrap.v1.json")
    value["routing_rules"]["resumable_stage_result_present"]["action_id"] = "restart_from_intake"
    write_json(root, "manifests/architect-conversation-bootstrap.v1.json", value)


def manifest_requires_anchor(root: Path) -> None:
    value = load_json(root, "manifests/architect-pipeline-manifest.v1.json")
    value["normal_run_continuation"]["internal_anchor_required"] = True
    write_json(root, "manifests/architect-pipeline-manifest.v1.json", value)


def remove_research(root: Path) -> None:
    value = load_json(root, "manifests/architect-pipeline-manifest.v1.json")
    value["project_execution_stages"].pop(1)
    write_json(root, "manifests/architect-pipeline-manifest.v1.json", value)


def remove_alignment_boundary(root: Path) -> None:
    path = root / "contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md"
    path.write_text(path.read_text(encoding="utf-8").replace("authorization_role: none", "authorization_role: required", 1), encoding="utf-8")


MUTATIONS: list[tuple[str, Callable[[Path], None]]] = [
    ("wrong_contract_version", wrong_contract_version),
    ("missing_stage_result_precondition", missing_stage_result_precondition),
    ("restart_instead_of_continue", restart_instead_of_continue),
    ("manifest_requires_anchor", manifest_requires_anchor),
    ("remove_research", remove_research),
    ("remove_alignment_boundary", remove_alignment_boundary),
]


def test_canonical_repository_passes() -> None:
    result = validator.validate_repository(REPO_ROOT)
    assert result["continuation_model"] == "quality_driven"
    assert result["initial_sequence"] == "/intake → /research → /decompose"
    assert result["final_stage"] == "/project-gate-export"


@pytest.mark.parametrize(("name", "mutate"), MUTATIONS, ids=[name for name, _ in MUTATIONS])
def test_semantic_mutations_fail_closed(tmp_path: Path, name: str, mutate: Callable[[Path], None]) -> None:
    fixture_root = copy_fixture(tmp_path)
    mutate(fixture_root)
    with pytest.raises(validator.ValidationError):
        validator.validate_repository(fixture_root)
