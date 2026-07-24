from __future__ import annotations

import copy
import json
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
from architect_project_gate_exporter import base
from architect_runtime_authority_manifest import (
    MANIFEST_PATH,
    REQUIRED_PUBLIC_SYMBOLS,
    RuntimeAuthorityManifestError,
    load_runtime_authority_manifest,
    validate_manifest_document,
)

PREFINAL_DIR = REPO_ROOT / "fixtures/conversational-run/valid/minimal-complete-run"
TERMINAL_PATH = REPO_ROOT / "fixtures/conversational-run/valid/terminal/project-gate-export.json"


class FixtureGitProvider:
    def provenance(self, root: Path):
        assert root == REPO_ROOT
        return base.GitProvenance(
            "rezahh107/EV4-Architect-Repo", "fixture-authority", "7" * 40
        )


def outputs() -> list[dict]:
    return [
        *conversational.load_output_files(PREFINAL_DIR, root=REPO_ROOT),
        json.loads(TERMINAL_PATH.read_text(encoding="utf-8")),
    ]


def context(kind: str = "fixture") -> runtime.RunContext:
    return runtime.RunContext(source_kind=kind)


def _manifest() -> dict:
    return json.loads((REPO_ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))


def _fresh_process_closure() -> dict[str, list[str]]:
    code = r'''
import json
import sys
from pathlib import Path

root = Path.cwd().resolve()
scripts = root / "scripts"
sys.path.insert(0, str(scripts))
order = [
    "/intake", "/research", "/decompose", "/architectures",
    "/score-evidence", "/score-audit", "/recommend", "/build-tree",
    "/implementation", "/final-audit", "/handoff-export",
    "/project-gate-export",
]
prefinal_dir = root / "fixtures/conversational-run/valid/minimal-complete-run"
values = [json.loads(path.read_text(encoding="utf-8")) for path in prefinal_dir.glob("*.json")]
by_stage = {item["stage_id"]: item for item in values}
outputs = [by_stage[stage] for stage in order[:-1]]
outputs.append(json.loads((root / "fixtures/conversational-run/valid/terminal/project-gate-export.json").read_text(encoding="utf-8")))
opened = set()
def audit(event, args):
    if event != "open" or not args:
        return
    raw = args[0]
    if not isinstance(raw, (str, bytes)):
        return
    try:
        path = Path(raw.decode() if isinstance(raw, bytes) else raw).resolve()
        rel = path.relative_to(root).as_posix()
    except Exception:
        return
    if "/__pycache__/" in f"/{rel}" or rel.endswith((".pyc", ".pyo", ".py")):
        return
    opened.add(rel)
sys.addaudithook(audit)
import architect_quality_runtime as runtime
from architect_project_gate_exporter import base
class FixtureGitProvider:
    def provenance(self, repository_root):
        return base.GitProvenance(
            "rezahh107/EV4-Architect-Repo", "fixture-subprocess", "8" * 40
        )
ctx = runtime.RunContext(source_kind="fixture")
manifest, schema = runtime.load_authority(root)
assert runtime.RUNTIME_INTERFACE_ID == "ev4-architect-quality-runtime@2.0.0"
prefinal = runtime.evaluate_run(
    outputs[:-1], root=root, require_terminal=False,
    run_context=ctx, git_provider=FixtureGitProvider()
)
assert prefinal["status"] == "valid", prefinal
complete = runtime.evaluate_run(
    outputs, root=root, require_terminal=True,
    run_context=ctx, git_provider=FixtureGitProvider()
)
assert complete["status"] == "valid", complete
terminal = complete["results"][-1]["project_gate_export"]
assert terminal["runtime_issued_payload"]["synthetic"] is True
assert terminal["canonical_payload_valid"] is True
assert terminal["functional_eligibility"]["would_allow"] is True
assert terminal["handoff_allowed"] is False
python_paths = set()
for module in tuple(sys.modules.values()):
    raw = getattr(module, "__file__", None)
    if not raw:
        continue
    try:
        path = Path(raw).resolve()
        rel = path.relative_to(root).as_posix()
    except Exception:
        continue
    if rel.startswith("tests/") or not rel.endswith(".py"):
        continue
    python_paths.add(rel)
print("RUNTIME_CLOSURE=" + json.dumps({"python": sorted(python_paths), "data": sorted(opened)}, sort_keys=True))
'''
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    marker = next(
        line for line in completed.stdout.splitlines() if line.startswith("RUNTIME_CLOSURE=")
    )
    return json.loads(marker.split("=", 1)[1])


def test_manifest_identity_paths_and_public_symbols() -> None:
    manifest = load_runtime_authority_manifest(REPO_ROOT)
    assert manifest["runtime_interface_id"] == runtime.RUNTIME_INTERFACE_ID
    assert all(hasattr(runtime, name) for name in REQUIRED_PUBLIC_SYMBOLS)
    assert manifest["python_authority_paths"] == sorted(
        manifest["python_authority_paths"]
    )
    assert manifest["data_authority_paths"] == sorted(manifest["data_authority_paths"])


def test_fresh_process_runtime_closure_is_exact() -> None:
    closure = _fresh_process_closure()
    validate_manifest_document(
        _manifest(),
        REPO_ROOT,
        observed_python_paths=closure["python"],
        observed_data_paths=closure["data"],
    )


@pytest.mark.parametrize("key", ["python_authority_paths", "data_authority_paths"])
def test_duplicate_and_unsorted_paths_fail(key: str) -> None:
    duplicate = _manifest()
    duplicate[key].append(duplicate[key][0])
    with pytest.raises(RuntimeAuthorityManifestError):
        validate_manifest_document(duplicate, REPO_ROOT, check_public_symbols=False)

    unsorted = _manifest()
    unsorted[key] = list(reversed(unsorted[key]))
    with pytest.raises(RuntimeAuthorityManifestError):
        validate_manifest_document(unsorted, REPO_ROOT, check_public_symbols=False)


def test_missing_declared_path_fails() -> None:
    document = _manifest()
    document["python_authority_paths"][0] = "scripts/does_not_exist.py"
    document["python_authority_paths"].sort()
    with pytest.raises(RuntimeAuthorityManifestError, match="missing"):
        validate_manifest_document(document, REPO_ROOT, check_public_symbols=False)


def test_undeclared_loaded_and_stale_declared_paths_fail() -> None:
    closure = _fresh_process_closure()
    undeclared = _manifest()
    removed = closure["python"][0]
    undeclared["python_authority_paths"].remove(removed)
    with pytest.raises(RuntimeAuthorityManifestError, match="undeclared"):
        validate_manifest_document(
            undeclared,
            REPO_ROOT,
            observed_python_paths=closure["python"],
            observed_data_paths=closure["data"],
            check_public_symbols=False,
        )

    stale = _manifest()
    stale["python_authority_paths"].append("scripts/repository_repair_handoff.py")
    stale["python_authority_paths"].sort()
    with pytest.raises(RuntimeAuthorityManifestError, match="stale"):
        validate_manifest_document(
            stale,
            REPO_ROOT,
            observed_python_paths=closure["python"],
            observed_data_paths=closure["data"],
            check_public_symbols=False,
        )


def _terminal_state() -> tuple[list[dict], dict]:
    items = outputs()
    run = runtime.evaluate_run(
        items[:-1],
        root=REPO_ROOT,
        require_terminal=False,
        run_context=context(),
        git_provider=FixtureGitProvider(),
    )
    assert run["status"] == "valid", run["errors"]
    assert run["run_state"] is not None
    return items, run["run_state"]


@pytest.mark.parametrize(
    "field, expected_code",
    [
        ("synthetic", "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN"),
        ("project_gate_payload", "RUNTIME_CALLER_PROJECT_GATE_PAYLOAD_FORBIDDEN"),
        ("stage_status", "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN"),
    ],
)
def test_direct_terminal_diagnostics_preserve_typed_metadata(
    field: str, expected_code: str
) -> None:
    items, state = _terminal_state()
    terminal = copy.deepcopy(items[-1])
    terminal[field] = False if field == "synthetic" else {}
    with pytest.raises(runtime.StageOutputValidationError) as caught:
        runtime.evaluate_stage(
            "/project-gate-export",
            terminal,
            state,
            root=REPO_ROOT,
            run_context=context(),
            git_provider=FixtureGitProvider(),
        )
    diagnostic = next(
        item for item in caught.value.diagnostics if item.code == expected_code
    )
    assert diagnostic.path == field
    assert diagnostic.stage_id == "/project-gate-export"
    assert diagnostic.message


def test_session_and_evaluate_run_serialize_original_diagnostic_metadata() -> None:
    items = outputs()
    terminal = copy.deepcopy(items[-1])
    terminal["synthetic"] = False
    session = runtime.resume_run(
        items[:-1],
        run_context=context(),
        repository_root=REPO_ROOT,
        git_provider=FixtureGitProvider(),
    )
    before = session.projection
    rejected = session.advance(terminal)
    assert rejected["accepted"] is False
    assert session.projection == before
    detail = next(
        item
        for item in rejected["diagnostic_details"]
        if item["code"] == "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN"
    )
    assert detail == {
        "code": "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN",
        "message": detail["message"],
        "path": "synthetic",
        "stage_id": "/project-gate-export",
    }

    run = runtime.evaluate_run(
        [*items[:-1], terminal],
        root=REPO_ROOT,
        run_context=context(),
        git_provider=FixtureGitProvider(),
    )
    assert run["status"] == "invalid"
    assert any(
        item["code"] == "RUNTIME_CALLER_AUTHORITY_FIELD_FORBIDDEN"
        and item["path"] == "synthetic"
        and item["stage_id"] == "/project-gate-export"
        for item in run["diagnostics"]
    )


def test_finalize_and_identity_source_and_provider_diagnostics_are_structured() -> None:
    items = outputs()
    session = runtime.resume_run(
        items[:-1],
        run_context=context(),
        repository_root=REPO_ROOT,
        git_provider=FixtureGitProvider(),
    )
    finalized = session.finalize()
    assert finalized["status"] == "invalid"
    assert any(
        item["code"] == "RUNTIME_STAGE_ORDER_MISMATCH"
        and item["path"] == "history"
        for item in finalized["diagnostics"]
    )

    with pytest.raises(runtime.RunSequenceValidationError) as mismatch:
        runtime.evaluate_stage(
            "/research",
            items[0],
            None,
            root=REPO_ROOT,
            run_context=context(),
            git_provider=FixtureGitProvider(),
        )
    identity = mismatch.value.diagnostics[0]
    assert identity.code == "RUNTIME_STAGE_OUTPUT_IDENTITY_MISMATCH"
    assert identity.path == "stage_output.stage_id"
    assert identity.stage_id == "/research"

    with pytest.raises(runtime.RuntimeEnvironmentError) as invalid_kind:
        runtime.RunContext(source_kind="invalid")
    source = invalid_kind.value.diagnostics[0]
    assert source.code == "RUNTIME_SOURCE_KIND_INVALID"
    assert source.path == "RunContext.source_kind"

    provider = runtime.evaluate_run(
        items,
        root=REPO_ROOT,
        run_context=context("live_conversation"),
        git_provider=FixtureGitProvider(),
    )
    assert provider["status"] == "invalid"
    assert provider["diagnostics"] == [
        {
            "code": "RUNTIME_LIVE_GIT_PROVIDER_INJECTION_FORBIDDEN",
            "message": "live_conversation provenance is resolved only from the actual checkout",
            "path": "git_provider",
            "stage_id": None,
        }
    ]


def test_base_schema_diagnostic_preserves_path_and_stage() -> None:
    item = copy.deepcopy(outputs()[0])
    del item["run_id"]
    with pytest.raises(runtime.StageOutputValidationError) as caught:
        runtime.evaluate_stage(
            "/intake",
            item,
            None,
            root=REPO_ROOT,
            run_context=context(),
            git_provider=FixtureGitProvider(),
        )
    diagnostic = next(
        item
        for item in caught.value.diagnostics
        if item.code == "RUNTIME_STAGE_OUTPUT_SCHEMA_INVALID"
    )
    assert diagnostic.path == "<root>"
    assert diagnostic.stage_id == "/intake"
