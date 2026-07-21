from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export-architect-project-gate.py"
spec = importlib.util.spec_from_file_location("architect_project_gate_exporter_arch02", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = exporter
spec.loader.exec_module(exporter)


def git(ref: str = "main", sha: str = "a" * 40):
    return exporter.GitProvenance(exporter.REPOSITORY, ref, sha)


def provider(root, payload_path, output_path, allowed_paths):
    return git()


def fake_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    *,
    status: str = "successful",
    allowed: bool = True,
) -> None:
    monkeypatch.setattr(exporter, "validate_payload", lambda root, value: {"status": "valid"})
    monkeypatch.setattr(
        exporter,
        "build_export",
        lambda value, provenance, run_id, input_ref: (
            {
                "handoff": {"status": status, "allowed": allowed},
                "export_id": f"unit-export-{run_id}",
                "producer": {"commit_sha": provenance.commit_sha},
            },
            {
                "payload_hash": "payload",
                "bundle_hash": "bundle",
                "export_hash": run_id,
            },
        ),
    )
    monkeypatch.setattr(exporter, "validate_contracts", lambda root, value: None)
    monkeypatch.setattr(exporter, "verify_hashes", lambda value, hashes: None)


def run_unit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    run_id: str = "arch02",
    status: str = "successful",
    allowed: bool = True,
    receipt_emitter=None,
):
    fake_pipeline(monkeypatch, status=status, allowed=allowed)
    payload = tmp_path / f"payload-{run_id}.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / f"output-{run_id}.json"
    result = exporter.run_export(
        tmp_path,
        payload,
        output,
        run_id,
        provenance_provider=provider,
        receipt_emitter=receipt_emitter,
    )
    return result, output


def test_precommit_publication_failure_leaves_no_canonical_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "architect-project-gate.json"

    def fail_before_link(self):
        raise exporter.ExportError(
            "ARCH_EXPORT_TEST_PRECOMMIT_FAILURE",
            "atomic_write",
            "injected before publication",
            "operator",
        )

    monkeypatch.setattr(exporter.OutputTransaction, "publish", fail_before_link)
    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(
            tmp_path,
            payload,
            output,
            "precommit",
            provenance_provider=provider,
        )
    assert exc.value.code == "ARCH_EXPORT_TEST_PRECOMMIT_FAILURE"
    assert exc.value.output_committed is False
    assert not output.exists()


def test_postpublication_observation_failure_is_committed_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "architect-project-gate.json"
    real_publish = exporter.OutputTransaction.publish

    def publish_then_fail(self):
        real_publish(self)
        raise exporter.ExportError(
            "ARCH_EXPORT_TEST_POSTCOMMIT_FAILURE",
            "post_commit_observation",
            "injected after publication",
            "operator",
        )

    monkeypatch.setattr(exporter.OutputTransaction, "publish", publish_then_fail)
    result = exporter.run_export(
        tmp_path,
        payload,
        output,
        "postcommit",
        provenance_provider=provider,
    )
    assert result.artifact_committed is True
    assert result.output_committed is True
    assert result.receipt_emitted is False
    assert result.result_status == "SUCCESS_WITH_CLEANUP_WARNING"
    assert any(
        item
        == "ARCH_EXPORT_POST_COMMIT_OBSERVATION_WARNING:ARCH_EXPORT_TEST_POSTCOMMIT_FAILURE"
        for item in result.cleanup_warnings
    )
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["export_id"] == "unit-export-postcommit"


def test_receipt_failure_is_nonfatal_after_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def failing_receipt(result):
        raise OSError("injected")

    result, output = run_unit(
        tmp_path,
        monkeypatch,
        run_id="receipt-warning",
        receipt_emitter=failing_receipt,
    )
    assert result.artifact_committed is True
    assert result.receipt_emitted is False
    assert result.cleanup_complete is True
    assert result.result_status == "SUCCESS_WITH_RECEIPT_WARNING"
    assert "ARCH_EXPORT_RECEIPT_EMIT_FAILED:OSError" in result.cleanup_warnings
    assert output.exists()


def test_success_result_explicitly_reports_commit_receipt_and_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    emitted = []
    result, output = run_unit(
        tmp_path,
        monkeypatch,
        run_id="explicit-result",
        receipt_emitter=emitted.append,
    )
    assert result.result_status == "SUCCESS"
    assert result.artifact_committed is True
    assert result.receipt_emitted is True
    assert result.cleanup_complete is True
    assert result.handoff_allowed is True
    assert emitted and emitted[0] == result
    assert output.exists()


def test_cleanup_warning_after_commit_is_nonfatal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    real_close = exporter.OutputTransaction.close

    def close_with_warning(self):
        warnings = real_close(self)
        warnings.append("ARCH_EXPORT_OUTPUT_DESCRIPTOR_CLOSE_FAILED:Injected")
        return warnings

    monkeypatch.setattr(exporter.OutputTransaction, "close", close_with_warning)
    result, output = run_unit(tmp_path, monkeypatch, run_id="cleanup-warning")
    assert result.artifact_committed is True
    assert result.cleanup_complete is False
    assert result.result_status == "SUCCESS_WITH_CLEANUP_WARNING"
    assert output.exists()


@pytest.mark.parametrize(
    ("status", "run_id"),
    [("blocked", "blocked"), ("insufficient_evidence", "insufficient")],
)
def test_valid_nonhandoff_exports_are_committed_with_documented_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    status: str,
    run_id: str,
):
    result, output = run_unit(
        tmp_path,
        monkeypatch,
        run_id=run_id,
        status=status,
        allowed=False,
    )
    assert result.artifact_committed is True
    assert result.handoff_allowed is False
    assert output.exists()

    monkeypatch.setattr(exporter, "run_export", lambda *args, **kwargs: result)
    payload = tmp_path / f"cli-{run_id}.json"
    payload.write_text("{}\n", encoding="utf-8")
    exit_code = exporter.main(
        [
            "--repo-root",
            str(tmp_path),
            "--payload",
            str(payload),
            "--run-id",
            run_id,
            "--format",
            "json",
        ]
    )
    assert exit_code == 2
    assert "Traceback" not in capsys.readouterr().err


def test_existing_destination_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake_pipeline(monkeypatch)
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "architect-project-gate.json"
    output.write_bytes(b"unrelated\n")
    with pytest.raises(exporter.ExportError) as exc:
        exporter.run_export(
            tmp_path,
            payload,
            output,
            "existing",
            provenance_provider=provider,
        )
    assert exc.value.code == "ARCH_EXPORT_OUTPUT_EXISTS"
    assert output.read_bytes() == b"unrelated\n"


def test_input_path_is_intentional_content_identity_input():
    payload = {
        "payload_status": "complete",
        "synthetic": False,
        "payload_identity": {"created_by": "ev4_architect"},
        "evidence_register": [],
        "unresolved_evidence": [],
    }
    same_a, hashes_a = exporter.build_export(payload, git(), "run-1", "inputs/a.json")
    same_b, hashes_b = exporter.build_export(payload, git(), "run-1", "inputs/a.json")
    moved, moved_hashes = exporter.build_export(payload, git(), "run-1", "relocated/a.json")

    assert hashes_a == hashes_b
    assert same_a == same_b
    assert hashes_a["payload_hash"] == moved_hashes["payload_hash"]
    assert same_a["final_stage_bundle"]["bundle_id"] == moved["final_stage_bundle"]["bundle_id"]
    assert hashes_a["bundle_hash"] != moved_hashes["bundle_hash"]
    assert same_a["export_id"] != moved["export_id"]
    assert hashes_a["export_hash"] != moved_hashes["export_hash"]


def test_event_specific_workflows_assert_exact_pr_and_main_sha():
    root = Path(__file__).resolve().parents[1]
    pr_workflow = (
        root / ".github/workflows/validate-architect-producer-gate-adoption.yml"
    ).read_text(encoding="utf-8")
    main_workflow = (
        root / ".github/workflows/validate-architect-producer-gate-adoption-main.yml"
    ).read_text(encoding="utf-8")

    assert "pull_request:" in pr_workflow
    assert "push:" not in pr_workflow
    assert "ref: ${{ github.event.pull_request.head.sha }}" in pr_workflow
    assert (
        'test "$(git rev-parse HEAD)" = "${{ github.event.pull_request.head.sha }}"'
        in pr_workflow
    )

    assert "push:" in main_workflow
    assert "branches:" in main_workflow
    assert "- main" in main_workflow
    assert "github.event.pull_request.head.sha" not in main_workflow
    assert "ref: ${{ github.sha }}" in main_workflow
    assert 'test "$(git rev-parse HEAD)" = "${{ github.sha }}"' in main_workflow


def test_status_records_arch01_merge_and_arch02_repair_without_false_closure():
    status = (Path(__file__).resolve().parents[1] / "STATUS.md").read_text(encoding="utf-8")
    assert "pull_request: 28" in status
    assert "merge_commit: 5aed1358c8df98eb262986ef7bcddb3acaeaddcf" in status
    assert "implementation_status: merged" in status
    assert "audit_status: merged_observed_not_independently_accepted" in status
    assert "pull_request: 29" in status
    assert "final_pr_head: 05f9ba12d5d64d49280ca7e596fdeed6c0f37073" in status
    assert "merge_status: merged" in status
    assert "merge_commit: be9bdea9ae246b1587043f2582c1a950ea2a6ec5" in status
    assert "github_state_evidence: observed" in status
    assert "ARCH02-F01" in status
    assert "ARCH02-F03" in status
    assert "ARCH02-F05" in status
    assert "PATH_IS_INTENTIONAL_IDENTITY_INPUT" in status
    assert "real_run_evidence: pending" in status
    assert "exact_merged_main_validation: insufficient_evidence" in status
    assert "independent_acceptance: not_established" in status
    assert "audit_status: bounded_repair_pr_open" not in status
    assert "repair_pr_merge_status: unmerged" not in status
