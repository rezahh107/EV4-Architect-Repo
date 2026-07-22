#!/usr/bin/env python3
"""Fail-closed consistency check for canonical pipeline validation profiles."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "manifests/architect-pipeline-manifest.v1.json").read_text())
registry = json.loads((ROOT / "manifests/architect-stage-validation-profiles.v1.json").read_text())
stages = manifest["project_execution_stages"]
profiles = {item["stage_id"]: item for item in registry["profiles"]}
ids = [item["stage_id"] for item in stages]
errors = []
if len(ids) != len(set(ids)) or set(ids) != set(profiles):
    errors.append("ASB-VALIDATION-PROFILE-TOPOLOGY-DRIFT")
for stage in stages:
    profile = profiles.get(stage["stage_id"], {})
    validation = profile.get("validation", {})
    if validation.get("status") == "full_transaction_implemented":
        required = ("artifact", "receipt", "bundle", "repair")
        if any(key not in profile for key in required) or not validation.get("authorization_capable"):
            errors.append(f"ASB-IMPLEMENTED-PROFILE-INCOMPLETE:{stage['stage_id']}")
    if validation.get("executable") and validation.get("status") != "full_transaction_implemented":
        errors.append(f"ASB-EXECUTABLE-PROFILE-STATUS-MISMATCH:{stage['stage_id']}")
    if not validation.get("executable") and validation.get("authorization_capable"):
        errors.append(f"ASB-BLOCKED-PROFILE-AUTHORIZATION:{stage['stage_id']}")
if errors:
    raise SystemExit("\n".join(errors))
print("Architect validation profiles: valid")
