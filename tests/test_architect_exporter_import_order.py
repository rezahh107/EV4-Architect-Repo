from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_exporter_entrypoint_preserves_package_submodule_imports() -> None:
    script = """
import importlib
import importlib.util
import sys
from pathlib import Path

root = Path(sys.argv[1])
entrypoint = root / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter", entrypoint)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
eligibility = importlib.import_module("architect_project_gate_exporter.eligibility")
assert callable(eligibility.derive_handoff_eligibility)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script, str(REPO_ROOT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
