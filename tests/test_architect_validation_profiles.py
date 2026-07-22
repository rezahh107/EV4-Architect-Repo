import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from architect_validation_common import ALL_ORDER, EXECUTABLE_STAGES, successor_stage


def test_manifest_registry_and_validator_topology_are_consistent():
    manifest = json.loads((ROOT / "manifests/architect-pipeline-manifest.v1.json").read_text())
    registry = json.loads((ROOT / "manifests/architect-stage-validation-profiles.v1.json").read_text())
    stages = manifest["project_execution_stages"]
    assert ALL_ORDER == [stage["stage_id"] for stage in stages]
    assert {profile["stage_id"] for profile in registry["profiles"]} == set(ALL_ORDER)
    assert all(successor_stage(stage["stage_id"]) == stage["next_stage"] for stage in stages)
    assert EXECUTABLE_STAGES == ("/decompose", "/architectures", "/score-evidence", "/score-audit")


def test_blocked_profiles_never_authorize_continuation():
    registry = json.loads((ROOT / "manifests/architect-stage-validation-profiles.v1.json").read_text())
    for profile in registry["profiles"]:
        validation = profile["validation"]
        if not validation["executable"]:
            assert validation["authorization_capable"] is False
