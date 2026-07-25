from __future__ import annotations

import copy
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import architect_quality_runtime as runtime
import architect_runtime_payload_assembler as assembler
from architect_project_gate_exporter import base, contracts

_legacy = importlib.import_module("_legacy_architect_runtime_truth_spine")

DIRECT_EXPORT_SCRIPT = ROOT / "scripts/export-architect-project-gate.py"
RAW_PAYLOAD = ROOT / (
    "fixtures/architect-stage-payload/valid/"
    "complete-with-unresolved-downstream-evidence.v1.json"
)
RETIRED_WRAPPERS = [
    ROOT / "EV4_ARCHITECT_EXPORT_PYTHON_v2/Generate-ArchitectProjectGate.py",
    ROOT / "EV4_ARCHITECT_EXPORT_PYTHON_v2/Run-ArchitectProjectGate.cmd",
    ROOT / "EV4_ARCHITECT_EXPORT_PYTHON_v2/RPR-PG-001_architect_stage_payload.json",
    ROOT / "EV4_ARCHITECT_EXPORT_PYTHON_v2/README_FA.md",
    ROOT / "EV4_ARCHITECT_EXPORT_PYTHON_v2/PACKAGE_SHA256SUMS.txt",
]


def raw_payload() -> dict:
    return json.loads(RAW_PAYLOAD.read_text(encoding="utf-8"))


def provenance() -> base.GitProvenance:
    return base.GitProvenance(
        repository=base.REPOSITORY,
        ref="caller-controlled",
        commit_sha="a" * 40,
    )


def direct_build(payload: dict) -> None:
    contracts.build_export(
        payload,
        provenance(),
        "caller-run",
        "quality_runtime:runtime_issued_payload",
    )


def live_runtime_outcome() -> dict:
    return runtime.evaluate_run(
        _legacy.full_outputs(),
        root=ROOT,
        run_context=_legacy.context("live_conversation"),
    )


def test_payload_cli_and_compatibility_entrypoint_are_absent(tmp_path: Path) -> None:
    assert not DIRECT_EXPORT_SCRIPT.exists()
    completed = subprocess.run(
        [sys.executable, str(DIRECT_EXPORT_SCRIPT), "--payload", str(RAW_PAYLOAD)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert not (tmp_path / "architect-project-gate.json").exists()


def test_windows_wsl_and_payload_example_wrappers_are_removed() -> None:
    assert all(not path.exists() for path in RETIRED_WRAPPERS)


def test_package_exposes_no_direct_export_alias() -> None:
    package = importlib.import_module("architect_project_gate_exporter")
    assert not hasattr(package, "run_export")
    assert not hasattr(package, "main")
    for name in (
        "architect_project_gate_exporter.runner",
        "architect_project_gate_exporter.arch02",
        "architect_project_gate_exporter.ancestry",
        "architect_project_gate_exporter.locking",
        "architect_project_gate_exporter.transaction",
    ):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(name)


def test_schema_valid_repository_payload_cannot_authorize_direct_export() -> None:
    with pytest.raises(contracts.ExportError) as caught:
        direct_build(raw_payload())
    assert caught.value.code == "ARCH_EXPORT_RUNTIME_PAYLOAD_AUTHORITY_REQUIRED"
    assert caught.value.report()["handoff_prohibited"] is True


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.__setitem__("payload_status", "complete"),
        lambda value: value.__setitem__("synthetic", False),
        lambda value: value.__setitem__("unresolved_evidence", []),
        lambda value: value.__setitem__("runtime_issued", True),
        lambda value: value.__setitem__("handoff_allowed", True),
        lambda value: value.__setitem__("project_gate_accepted", True),
        lambda value: value.__setitem__("ce_transition_authorized", True),
        lambda value: value.__setitem__("production_ready", True),
        lambda value: value.__setitem__(
            "producer_provenance",
            {"repository": base.REPOSITORY, "commit_sha": "b" * 40},
        ),
        lambda value: value.__setitem__("validator_identity", "fabricated-validator"),
        lambda value: value.__setitem__("source_digest", "sha256:" + "0" * 64),
    ],
)
def test_fabricated_raw_payload_fields_never_create_authority(mutate) -> None:
    payload = raw_payload()
    mutate(payload)
    with pytest.raises(contracts.ExportError) as caught:
        direct_build(payload)
    assert caught.value.code == "ARCH_EXPORT_RUNTIME_PAYLOAD_AUTHORITY_REQUIRED"


def test_external_history_replay_payload_is_non_authorizing() -> None:
    payload = assembler.assemble_architect_stage_payload(
        stage_outputs=_legacy.outputs(),
        source_kind="fixture",
        run_context=_legacy.context("fixture"),
        repository_root=ROOT,
        git_provider=_legacy.FixtureGitProvider(),
    )
    assert payload["payload_identity"]["created_by"] == "architect_quality_runtime"
    with pytest.raises(contracts.ExportError) as caught:
        direct_build(payload)
    assert caught.value.code == "ARCH_EXPORT_RUNTIME_PAYLOAD_AUTHORITY_REQUIRED"


def test_copied_or_mutated_runtime_payload_cannot_recreate_capability() -> None:
    replay = runtime._replay_outcome(
        _legacy.full_outputs(),
        run_context=_legacy.context("fixture"),
        repository_root=ROOT,
        require_terminal=True,
        git_provider=_legacy.FixtureGitProvider(),
    )
    assert replay.status == "valid"
    execution = replay.results[-1]["project_gate_export"]
    issued = execution.runtime_issued_payload
    copied = copy.deepcopy(issued)
    copied["synthetic"] = False
    copied["unresolved_evidence"] = []
    with pytest.raises(contracts.ExportError) as caught:
        direct_build(copied)
    assert caught.value.code == "ARCH_EXPORT_RUNTIME_PAYLOAD_AUTHORITY_REQUIRED"


def test_canonical_live_runtime_transaction_can_authorize_handoff() -> None:
    outcome = live_runtime_outcome()
    assert outcome["status"] == "valid", outcome["errors"]
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["canonical_payload_valid"] is True
    assert terminal["execution_context"] == {
        "source_kind": "live_conversation",
        "synthetic": False,
    }
    assert "runtime_issued_payload" not in terminal
    assert terminal["functional_eligibility"]["would_allow"] is True
    assert terminal["handoff_allowed"] is True


def test_canonical_synthetic_runtime_transaction_remains_blocked() -> None:
    outcome = _legacy.run(source_kind="fixture")
    assert outcome["status"] == "valid", outcome["errors"]
    terminal = outcome["results"][-1]["project_gate_export"]
    assert terminal["execution_context"] == {
        "source_kind": "fixture",
        "synthetic": True,
    }
    assert "runtime_issued_payload" not in terminal
    assert terminal["functional_eligibility"]["would_allow"] is True
    assert terminal["handoff_allowed"] is False


def test_pipeline_and_stage_output_contract_identity_are_unchanged() -> None:
    manifest = json.loads(
        (ROOT / "manifests/architect-pipeline-manifest.v1.json").read_text(
            encoding="utf-8"
        )
    )
    stages = manifest["project_execution_stages"]
    assert len(stages) == 12
    assert [item["stage_id"] for item in stages] == [
        "/intake",
        "/research",
        "/decompose",
        "/architectures",
        "/score-evidence",
        "/score-audit",
        "/recommend",
        "/build-tree",
        "/implementation",
        "/final-audit",
        "/handoff-export",
        "/project-gate-export",
    ]
    assert all(
        output["run_id"] == _legacy.outputs()[0]["run_id"]
        for output in _legacy.full_outputs()
    )


def test_active_docs_and_release_do_not_restore_direct_payload_export() -> None:
    required = (
        "Direct Project Gate export from a caller-supplied Payload file is "
        "unsupported and has been removed."
    )
    active_docs = [
        ROOT / "README.md",
        ROOT / "docs/ARCHITECT_PROJECT_GATE_EXPORTER.md",
        ROOT / "docs/ARCHITECT_PROJECT_GATE_EXPORTER_ARCH02.md",
        ROOT / "docs/PROJECT_GATE_PRODUCER_ADOPTION.md",
    ]
    assert all(required in path.read_text(encoding="utf-8") for path in active_docs)

    scanned: list[Path] = [*active_docs]
    for directory in (ROOT / "release", ROOT / ".github/workflows"):
        scanned.extend(path for path in directory.rglob("*") if path.is_file())
    forbidden = (
        "scripts/export-architect-project-gate.py",
        "Generate-ArchitectProjectGate.py",
        "Run-ArchitectProjectGate.cmd",
    )
    for path in scanned:
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert all(token not in text for token in forbidden), path
        assert "--payload path/to/architect-stage-payload.json" not in text, path
