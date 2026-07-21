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
    Path("AGENTS.md"),
    Path("README.md"),
    Path("STATUS.md"),
    Path("manifests/architect-conversation-bootstrap.v1.json"),
    Path("manifests/architect-pipeline-manifest.v1.json"),
    Path("schemas/architect-conversation-bootstrap.v1.schema.json"),
    Path("release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FIRST_RUN_GUIDE.md"),
]


def copy_fixture(tmp_path: Path) -> Path:
    for relative in CONTROLLED_PATHS:
        source = REPO_ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return tmp_path


def load_json(root: Path, relative: str) -> dict:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def write_json(root: Path, relative: str, value: dict) -> None:
    (root / relative).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def mutate_manifest(root: Path, mutation: Callable[[dict], None]) -> None:
    path = "manifests/architect-conversation-bootstrap.v1.json"
    data = load_json(root, path)
    mutation(data)
    write_json(root, path, data)


def replace_text(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def wrong_contract_id(root: Path) -> None:
    mutate_manifest(root, lambda data: data.__setitem__("contract_id", "wrong-contract"))


def wrong_contract_version(root: Path) -> None:
    mutate_manifest(root, lambda data: data.__setitem__("contract_version", "9.9.9"))


def wrong_owner_repository(root: Path) -> None:
    mutate_manifest(root, lambda data: data.__setitem__("owner_repository", "someone/else"))


def wrong_activation_mode(root: Path) -> None:
    mutate_manifest(root, lambda data: data["activation"].__setitem__("mode", "repository_maintenance"))


def missing_precondition(root: Path) -> None:
    mutate_manifest(root, lambda data: data["activation"]["preconditions"].pop())


def missing_canonical_trigger(root: Path) -> None:
    mutate_manifest(root, lambda data: data["activation"]["accepted_triggers"].remove("شروع"))


def non_string_trigger(root: Path) -> None:
    mutate_manifest(root, lambda data: data["activation"]["accepted_triggers"].__setitem__(0, 123))


def reversed_screenshot_behavior(root: Path) -> None:
    mutate_manifest(
        root,
        lambda data: data["input_present_behavior"]["trigger_with_screenshot_or_section_description"].__setitem__(
            "action_id", "repeat_bootstrap_questions_before_intake"
        ),
    )


def restart_instead_of_anchor_continuation(root: Path) -> None:
    mutate_manifest(
        root,
        lambda data: data["routing_rules"]["valid_stage_anchor_present"].__setitem__(
            "action_id", "restart_from_intake"
        ),
    )


def project_run_for_repository_maintenance(root: Path) -> None:
    mutate_manifest(
        root,
        lambda data: data["routing_rules"]["explicit_repository_maintenance_request"].__setitem__(
            "action_id", "new_architect_project_run"
        ),
    )


def invented_forbidden_identifier(root: Path) -> None:
    mutate_manifest(
        root,
        lambda data: data["before_input_forbidden"][0].__setitem__(
            "operation_id", "run_pipeline_if_convenient"
        ),
    )


def contradictory_agents_routing(root: Path) -> None:
    replace_text(
        root,
        "AGENTS.md",
        "If a valid Stage Anchor is present, do not restart the run. Continue only from the anchor's authorized target stage.",
        "If a valid Stage Anchor is present, restart the run from /intake.",
    )


def negated_project_gate_instruction(root: Path) -> None:
    replace_text(
        root,
        "release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FIRST_RUN_GUIDE.md",
        "Run /project-gate-export.",
        "Do not run /project-gate-export.",
    )


def missing_final_project_gate_stage(root: Path) -> None:
    path = "manifests/architect-pipeline-manifest.v1.json"
    data = load_json(root, path)
    data["project_execution_stages"].pop()
    data["final_project_gate_export_stage"] = None
    write_json(root, path, data)


def stale_intake_decompose_sequence(root: Path) -> None:
    replace_text(
        root,
        "release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FIRST_RUN_GUIDE.md",
        "The canonical machine-readable source for this response is:",
        "Start with /intake and /decompose only.\n\nThe canonical machine-readable source for this response is:",
    )


MUTATIONS = [
    ("wrong_contract_id", wrong_contract_id),
    ("wrong_contract_version", wrong_contract_version),
    ("wrong_owner_repository", wrong_owner_repository),
    ("wrong_activation_mode", wrong_activation_mode),
    ("missing_or_altered_precondition", missing_precondition),
    ("missing_canonical_trigger", missing_canonical_trigger),
    ("non_string_trigger", non_string_trigger),
    ("reversed_screenshot_present_behavior", reversed_screenshot_behavior),
    ("restart_instead_of_stage_anchor_continuation", restart_instead_of_anchor_continuation),
    ("project_run_for_repository_maintenance", project_run_for_repository_maintenance),
    ("invented_forbidden_operation_identifier", invented_forbidden_identifier),
    ("contradictory_agents_routing", contradictory_agents_routing),
    ("negated_project_gate_instruction", negated_project_gate_instruction),
    ("missing_final_project_gate_stage", missing_final_project_gate_stage),
    ("stale_intake_decompose_sequence", stale_intake_decompose_sequence),
]


def test_canonical_repository_passes() -> None:
    result = validator.validate_repository(REPO_ROOT)
    assert result["final_stage"] == "/project-gate-export"
    assert result["recognized_triggers"] == 6


@pytest.mark.parametrize(("mutation_name", "mutate"), MUTATIONS, ids=[name for name, _ in MUTATIONS])
def test_semantic_mutations_fail_closed(
    tmp_path: Path,
    mutation_name: str,
    mutate: Callable[[Path], None],
) -> None:
    fixture_root = copy_fixture(tmp_path)
    mutate(fixture_root)
    with pytest.raises(validator.ValidationError):
        validator.validate_repository(fixture_root)
