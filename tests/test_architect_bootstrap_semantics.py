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
    Path("02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md"),
    Path("contracts/QUALITY_FIRST_RUNTIME_ALIGNMENT.md"),
    Path("contracts/ARCHITECT_STAGE_RESULT_V1.md"),
    Path("manifests/architect-conversation-bootstrap.v1.json"),
    Path("manifests/architect-pipeline-manifest.v1.json"),
    Path("schemas/architect-conversation-bootstrap.v1.schema.json"),
    Path("release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FIRST_RUN_GUIDE.md"),
    Path("release/EV4_PROJECT_RELEASE_PACK_v1/PROJECT_INSTRUCTIONS_FINAL.md"),
    Path("release/EV4_PROJECT_RELEASE_PACK_v1/EV4_CORE_CONTRACTS_BUNDLE.md"),
    Path("release/EV4_PROJECT_RELEASE_PACK_v1/EV4_STAGE_PROTOCOLS_BUNDLE.md"),
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


def append(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


def replace_once(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_all(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new), encoding="utf-8")


def manifest_requires_anchor(root: Path) -> None:
    value = load_json(root, "manifests/architect-pipeline-manifest.v1.json")
    value["normal_run_continuation"]["internal_anchor_required"] = True
    write_json(root, "manifests/architect-pipeline-manifest.v1.json", value)


def serialized_result_authorizes(root: Path) -> None:
    value = load_json(root, "manifests/architect-pipeline-manifest.v1.json")
    value["normal_run_continuation"]["serialized_stage_result_authorizes"] = True
    write_json(root, "manifests/architect-pipeline-manifest.v1.json", value)


def remove_research(root: Path) -> None:
    value = load_json(root, "manifests/architect-pipeline-manifest.v1.json")
    value["project_execution_stages"].pop(1)
    write_json(root, "manifests/architect-pipeline-manifest.v1.json", value)


def terminal_evaluation_mode_drift(root: Path) -> None:
    value = load_json(root, "manifests/architect-pipeline-manifest.v1.json")
    value["project_execution_stages"][-1]["evaluation_mode"] = "model_assessed"
    write_json(root, "manifests/architect-pipeline-manifest.v1.json", value)


def build_tree_evaluation_mode_drift(root: Path) -> None:
    value = load_json(root, "manifests/architect-pipeline-manifest.v1.json")
    for stage in value["project_execution_stages"]:
        if stage["stage_id"] == "/build-tree":
            stage["evaluation_mode"] = "model_assessed"
            break
    write_json(root, "manifests/architect-pipeline-manifest.v1.json", value)


def remove_not_evaluated_claim_rule(root: Path) -> None:
    replace_all(
        root,
        "02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md",
        "stage_status: not_evaluated",
        "stage_status: pass",
    )


def remove_self_audit_boundary(root: Path) -> None:
    replace_once(
        root,
        "contracts/ARCHITECT_STAGE_RESULT_V1.md",
        "same-context self-audit is not independent review",
        "same-context self-audit may be independent review",
    )


def active_intake_shortcut(root: Path) -> None:
    append(root, "02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md", "\n## Active shortcut\nUse /intake → /decompose.\n")


def active_research_skip(root: Path) -> None:
    append(root, "release/EV4_PROJECT_RELEASE_PACK_v1/EV4_FIRST_RUN_GUIDE.md", "\n## Active shortcut\nSkip /research.\n")


def remove_arch02_audit_status(root: Path) -> None:
    path = root / "STATUS.md"
    path.write_text(path.read_text(encoding="utf-8").replace("  audit_status: merged_observed_not_independently_accepted\n", "", 1), encoding="utf-8")


FAILING_MUTATIONS: list[tuple[str, Callable[[Path], None]]] = [
    ("manifest_requires_anchor", manifest_requires_anchor),
    ("serialized_result_authorizes", serialized_result_authorizes),
    ("remove_research", remove_research),
    ("terminal_evaluation_mode_drift", terminal_evaluation_mode_drift),
    ("build_tree_evaluation_mode_drift", build_tree_evaluation_mode_drift),
    ("remove_not_evaluated_claim_rule", remove_not_evaluated_claim_rule),
    ("remove_self_audit_boundary", remove_self_audit_boundary),
    ("active_intake_shortcut", active_intake_shortcut),
    ("active_research_skip", active_research_skip),
    ("remove_arch02_audit_status", remove_arch02_audit_status),
]


def test_canonical_repository_passes() -> None:
    result = validator.validate_repository(REPO_ROOT)
    assert result["continuation_model"] == "quality_driven"
    assert result["initial_sequence"] == "/intake → /research → /decompose"
    assert result["final_stage"] == "/project-gate-export"
    assert result["controlled_runtime_docs"] == 8
    assert result["claim_truth_docs"] == 3


@pytest.mark.parametrize(("name", "mutate"), FAILING_MUTATIONS, ids=[name for name, _ in FAILING_MUTATIONS])
def test_active_semantic_mutations_fail_closed(tmp_path: Path, name: str, mutate: Callable[[Path], None]) -> None:
    fixture_root = copy_fixture(tmp_path)
    mutate(fixture_root)
    with pytest.raises(validator.ValidationError):
        validator.validate_repository(fixture_root)


def test_explicit_shortcut_prohibition_is_accepted(tmp_path: Path) -> None:
    fixture_root = copy_fixture(tmp_path)
    append(
        fixture_root,
        "02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md",
        "\n## Active protection\nDo not use /intake → /decompose.\nSkipping /research is forbidden.\n",
    )
    validator.validate_repository(fixture_root)


def test_historical_quotation_does_not_become_active_authority(tmp_path: Path) -> None:
    fixture_root = copy_fixture(tmp_path)
    append(
        fixture_root,
        "02_PROJECT_INSTRUCTIONS_ACTIVE_OVERRIDES.md",
        "\n## Historical evidence\n> A retired draft said: Use /intake → /decompose.\n> A retired draft also said: Skip /research.\n",
    )
    validator.validate_repository(fixture_root)
