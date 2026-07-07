from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-architect-producer-gate-adoption.py"
spec = importlib.util.spec_from_file_location("adoption", SCRIPT)
adoption = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = adoption
spec.loader.exec_module(adoption)


def diagnostic_codes(diagnostics):
    return {item.code for item in diagnostics}


def test_full_adoption_validation_passes():
    result = adoption.AdoptionValidator(ROOT).validate_all()
    assert result["status"] == "passed", result["diagnostics"]


def test_build_tree_invalid_cases_emit_expected_codes():
    validator = adoption.AdoptionValidator(ROOT)
    cases = adoption.read_json(ROOT / "fixtures/build-tree/invalid/cases.v1.json")
    base = adoption.read_json((ROOT / "fixtures/build-tree/invalid" / cases["base_fixture"]).resolve())
    for case in cases["cases"]:
        mutated = adoption.apply_mutations(base, case.get("mutations", []))
        codes = {d.code for d in validator.validate_build_tree(mutated)}
        assert case["expected_diagnostic"] in codes, case["case_id"]


def test_export_invalid_cases_emit_expected_codes():
    validator = adoption.AdoptionValidator(ROOT)
    cases = adoption.read_json(ROOT / "fixtures/project-gate-export/invalid/cases.v1.json")
    base = adoption.read_json((ROOT / "fixtures/project-gate-export/invalid" / cases["base_fixture"]).resolve())
    for case in cases["cases"]:
        mutated = adoption.apply_mutations(base, case.get("mutations", []))
        codes = {d.code for d in validator.validate_export(mutated)}
        assert case["expected_diagnostic"] in codes, case["case_id"]


def test_canonical_serialization_rejects_non_finite_numbers():
    try:
        adoption.reject_non_finite({"bad": float("inf")})
    except ValueError as exc:
        assert "non-finite" in str(exc)
    else:
        raise AssertionError("non-finite number accepted")


def test_lock_null_nested_sections_return_diagnostics():
    validator = adoption.AdoptionValidator(ROOT)
    lock = {
        "lock_schema": "project-gate-common-contract-lock.v1",
        "contract_id": "producer-gate-export.v1",
        "canonical": None,
        "verification": None,
    }
    codes = diagnostic_codes(validator.validate_common_contract_lock(lock))
    assert "A_PG_LOCK_CANONICAL_NOT_OBJECT" in codes
    assert "A_PG_LOCK_VERIFICATION_NOT_OBJECT" in codes
    assert "A_PG_LOCK_MOVING_REF" in codes
    assert "A_PG_LOCK_MOVING_DEFAULT_FORBIDDEN" in codes


def test_manifest_non_object_stage_returns_diagnostics():
    validator = adoption.AdoptionValidator(ROOT)
    manifest = copy.deepcopy(adoption.read_json(ROOT / "manifests/architect-pipeline-manifest.v1.json"))
    manifest["project_execution_stages"].insert(1, None)
    codes = diagnostic_codes(validator.validate_manifest(manifest))
    assert "A_MANIFEST_STAGE_NOT_OBJECT" in codes


def test_manifest_null_ordinal_returns_diagnostics():
    validator = adoption.AdoptionValidator(ROOT)
    manifest = copy.deepcopy(adoption.read_json(ROOT / "manifests/architect-pipeline-manifest.v1.json"))
    manifest["project_execution_stages"][1]["ordinal"] = None
    codes = diagnostic_codes(validator.validate_manifest(manifest))
    assert "A_MANIFEST_STAGE_ORDINAL_INVALID" in codes


def test_manifest_string_ordinal_returns_diagnostics():
    validator = adoption.AdoptionValidator(ROOT)
    manifest = copy.deepcopy(adoption.read_json(ROOT / "manifests/architect-pipeline-manifest.v1.json"))
    manifest["project_execution_stages"][1]["ordinal"] = "2"
    codes = diagnostic_codes(validator.validate_manifest(manifest))
    assert "A_MANIFEST_STAGE_ORDINAL_INVALID" in codes
