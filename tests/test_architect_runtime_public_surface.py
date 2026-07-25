from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import architect_runtime_authority_manifest as authority

WRAPPER = SCRIPTS / "architect_quality_runtime.py"
SIDECAR = SCRIPTS / "architect_project_gate_runtime_api.py"
MANIFEST = ROOT / authority.MANIFEST_PATH
REQUIRED_FINALIZATION_PATHS = {
    "scripts/architect_project_gate_finalization.py",
    "scripts/architect_quality_runtime/history.py",
}


def _probe(mode: str) -> dict:
    source = f'''\
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
root = Path.cwd().resolve()
scripts = root / "scripts"
sys.path.insert(0, str(scripts))
manifest = json.loads((root / "manifests/architect-runtime-authority-manifest.v1.json").read_text(encoding="utf-8"))
required = next(item["symbols"] for item in manifest["public_entry_points"] if item["path"] == "scripts/architect_quality_runtime.py")
if {mode!r} == "package":
    import architect_quality_runtime as module
else:
    spec = importlib.util.spec_from_file_location("_g1_exact_wrapper_probe", scripts / "architect_quality_runtime.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
import architect_quality_runtime as package
print(json.dumps({{
    "present_symbols": sorted(name for name in required if hasattr(module, name)),
    "required_symbols": sorted(required),
    "runtime_interface_id": module.RUNTIME_INTERFACE_ID,
    "finalize_callable": callable(module.finalize_project_gate),
    "result_type_name": module.ProjectGateFinalizationResult.__qualname__,
    "result_type_module": module.ProjectGateFinalizationResult.__module__,
    "finalize_name": module.finalize_project_gate.__qualname__,
    "finalize_module": module.finalize_project_gate.__module__,
    "canonical_finalize_identity": module.finalize_project_gate is package.finalize_project_gate,
    "canonical_result_identity": module.ProjectGateFinalizationResult is package.ProjectGateFinalizationResult,
}}, sort_keys=True))
'''
    completed = subprocess.run(
        [sys.executable, "-I", "-c", source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def test_package_and_exact_wrapper_expose_one_canonical_api() -> None:
    package = _probe("package")
    wrapper = _probe("wrapper")
    assert package == wrapper
    assert package["present_symbols"] == package["required_symbols"]
    assert package["runtime_interface_id"] == (
        "ev4-architect-quality-runtime@2.0.0"
    )
    assert package["finalize_callable"] is True
    assert package["canonical_finalize_identity"] is True
    assert package["canonical_result_identity"] is True
    assert package["finalize_module"] == "architect_quality_runtime"
    assert package["result_type_module"] == "architect_quality_runtime"


def test_exact_wrapper_is_one_pure_reexport() -> None:
    assert WRAPPER.read_text(encoding="utf-8") == (
        "from architect_quality_runtime import *  # noqa: F401,F403\n"
    )


def test_compatibility_sidecar_delegates_without_bridge_installation() -> None:
    runtime = importlib.import_module("architect_quality_runtime")
    bridge = runtime.INTERNAL_EVALUATOR._evaluate_project_gate
    sidecar = importlib.import_module("architect_project_gate_runtime_api")
    repeated = importlib.import_module("architect_project_gate_runtime_api")
    reloaded = importlib.reload(sidecar)

    assert repeated is sidecar
    assert reloaded.finalize_project_gate is runtime.finalize_project_gate
    assert (
        reloaded.ProjectGateFinalizationResult
        is runtime.ProjectGateFinalizationResult
    )
    assert runtime.INTERNAL_EVALUATOR._evaluate_project_gate is bridge
    source = SIDECAR.read_text(encoding="utf-8")
    assert "_install_terminal_execution_bridge" not in source
    assert "def finalize_project_gate" not in source
    assert "_CALLER_AUTHORITY_FIELDS" not in source


def test_manifest_declares_canonical_finalization_closure_only() -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = set(document["python_authority_paths"])
    assert REQUIRED_FINALIZATION_PATHS <= paths
    assert "scripts/architect_project_gate_runtime_api.py" not in paths
    authority.validate_manifest_document(document, ROOT)


@pytest.mark.parametrize("removed", sorted(REQUIRED_FINALIZATION_PATHS))
def test_removing_required_finalization_authority_path_fails(
    removed: str,
) -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mutated = copy.deepcopy(document)
    mutated["python_authority_paths"].remove(removed)
    with pytest.raises(
        authority.RuntimeAuthorityManifestError,
        match="ENTRYPOINT_CLOSURE_UNDECLARED",
    ):
        authority.validate_manifest_document(mutated, ROOT)
