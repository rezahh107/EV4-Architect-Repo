#!/usr/bin/env python3
"""Windows Python wrapper for the official EV4 Architect Project Gate exporter."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_VERSION = "2.0.0"
DEFAULT_ACCEPTED_COMMIT = "be9bdea9ae246b1587043f2582c1a950ea2a6ec5"
DEFAULT_RUN_ID = "EV4-RUN-VOICE-ASSISTANT-SECTION-001"
DEFAULT_PAYLOAD = "RPR-PG-001_architect_stage_payload.json"
BASH_SCRIPT = '#!/usr/bin/env bash\nset -Eeuo pipefail\numask 077\nexport LC_ALL=C\nexport LANG=C\nexport TZ=UTC\nexport GIT_CONFIG_NOSYSTEM=1\nexport GIT_CONFIG_GLOBAL=/dev/null\nexport GIT_TERMINAL_PROMPT=0\nexport PYTHONDONTWRITEBYTECODE=1\nexport PYTHONNOUSERSITE=1\n\nEXPECTED_REPOSITORY="rezahh107/EV4-Architect-Repo"\n\nPAYLOAD_PATH=""\nOUTPUT_DIR=""\nLOCAL_REPO=""\nRUN_ID=""\nACCEPTED_COMMIT=""\nKEEP_DIAGNOSTICS=0\n\nfail() {\n    local code="$1"\n    shift\n    printf \'ERROR[%s]: %s\\n\' "$code" "$*" >&2\n    exit "$code"\n}\n\nnormalize_repo_url() {\n    local url="$1"\n    case "$url" in\n        https://github.com/*) url="${url#https://github.com/}" ;;\n        http://github.com/*) url="${url#http://github.com/}" ;;\n        git@github.com:*) url="${url#git@github.com:}" ;;\n        ssh://git@github.com/*) url="${url#ssh://git@github.com/}" ;;\n        *) printf \'%s\' "$url"; return ;;\n    esac\n    url="${url%.git}"\n    printf \'%s\' "$url"\n}\n\nwhile (($#)); do\n    case "$1" in\n        --payload)\n            (($# >= 2)) || fail 2 "--payload requires a value"\n            PAYLOAD_PATH="$2"\n            shift 2\n            ;;\n        --output-dir)\n            (($# >= 2)) || fail 2 "--output-dir requires a value"\n            OUTPUT_DIR="$2"\n            shift 2\n            ;;\n        --local-repo)\n            (($# >= 2)) || fail 2 "--local-repo requires a value"\n            LOCAL_REPO="$2"\n            shift 2\n            ;;\n        --run-id)\n            (($# >= 2)) || fail 2 "--run-id requires a value"\n            RUN_ID="$2"\n            shift 2\n            ;;\n        --accepted-commit)\n            (($# >= 2)) || fail 2 "--accepted-commit requires a value"\n            ACCEPTED_COMMIT="${2,,}"\n            shift 2\n            ;;\n        --keep-diagnostics)\n            KEEP_DIAGNOSTICS=1\n            shift\n            ;;\n        *)\n            fail 2 "unknown argument: $1"\n            ;;\n    esac\ndone\n\n[[ -n "$PAYLOAD_PATH" ]] || fail 2 "missing --payload"\n[[ -n "$OUTPUT_DIR" ]] || fail 2 "missing --output-dir"\n[[ -n "$LOCAL_REPO" ]] || fail 2 "missing --local-repo"\n[[ -n "$RUN_ID" ]] || fail 2 "missing --run-id"\n[[ "$RUN_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$ ]] || fail 2 "invalid run ID"\n[[ "$ACCEPTED_COMMIT" =~ ^[0-9a-f]{40}$ ]] || fail 2 "accepted commit must be a full hexadecimal SHA"\n\ncommand -v git >/dev/null 2>&1 || fail 10 "git is not installed in WSL"\ncommand -v python3 >/dev/null 2>&1 || fail 11 "python3 is not installed in WSL"\ncommand -v sha256sum >/dev/null 2>&1 || fail 12 "sha256sum is not installed in WSL"\n\n[[ -f "$PAYLOAD_PATH" ]] || fail 13 "payload is not visible in WSL: $PAYLOAD_PATH"\n[[ -d "$OUTPUT_DIR" ]] || fail 14 "output directory is not visible in WSL: $OUTPUT_DIR"\n[[ -d "$LOCAL_REPO" ]] || fail 15 "Architect repository is not visible in WSL: $LOCAL_REPO"\n\nexec > >(tee -a "$OUTPUT_DIR/driver.stdout.log") \\\n     2> >(tee -a "$OUTPUT_DIR/driver.stderr.log" >&2)\n\nREPO_DIR=""\nLOG_DIR=""\nSUCCESS=0\n\ncleanup() {\n    local rc=$?\n    if [[ "$KEEP_DIAGNOSTICS" -eq 1 && "$SUCCESS" -ne 1 ]]; then\n        printf \'Linux checkout retained: %s\\n\' "${REPO_DIR:-<not-created>}" >&2\n        printf \'Linux log directory retained: %s\\n\' "${LOG_DIR:-<not-created>}" >&2\n    else\n        [[ -z "$REPO_DIR" ]] || rm -rf -- "$REPO_DIR"\n        [[ -z "$LOG_DIR" ]] || rm -rf -- "$LOG_DIR"\n    fi\n    return "$rc"\n}\ntrap cleanup EXIT\n\ngit -C "$LOCAL_REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1 \\\n    || fail 16 "local Architect path is not a Git worktree"\n\nORIGIN_RAW="$(git -C "$LOCAL_REPO" remote get-url origin 2>/dev/null)" \\\n    || fail 17 "local Architect repository has no readable origin"\nORIGIN_NORMALIZED="$(normalize_repo_url "$ORIGIN_RAW")"\n[[ "$ORIGIN_NORMALIZED" == "$EXPECTED_REPOSITORY" ]] \\\n    || fail 17 "local Architect origin mismatch: $ORIGIN_RAW"\n\ngit -C "$LOCAL_REPO" cat-file -e "$ACCEPTED_COMMIT^{commit}" 2>/dev/null \\\n    || fail 18 "accepted commit is absent from the local Architect object database"\n\nRESOLVED_COMMIT="$(git -C "$LOCAL_REPO" rev-parse "$ACCEPTED_COMMIT^{commit}")"\n[[ "$RESOLVED_COMMIT" == "$ACCEPTED_COMMIT" ]] \\\n    || fail 18 "accepted commit did not resolve exactly"\n\nREPO_DIR="$(mktemp -d -p "$HOME" ev4-architect-export.XXXXXX)"\nLOG_DIR="$(mktemp -d -p "$HOME" ev4-architect-export-logs.XXXXXX)"\n\ngit -c protocol.file.allow=always clone \\\n    --quiet \\\n    --no-local \\\n    --no-checkout \\\n    "$LOCAL_REPO" \\\n    "$REPO_DIR"\n\n[[ ! -e "$REPO_DIR/.git/objects/info/alternates" ]] \\\n    || fail 19 "temporary clone unexpectedly uses object alternates"\n\ngit -C "$REPO_DIR" remote set-url origin \\\n    https://github.com/rezahh107/EV4-Architect-Repo.git\n\nBRANCH_NAME="export/official-$(date -u +%Y%m%d%H%M%S)-$$"\ngit -C "$REPO_DIR" -c core.autocrlf=false checkout \\\n    --quiet \\\n    -b "$BRANCH_NAME" \\\n    "$ACCEPTED_COMMIT"\n\nACTUAL_HEAD="$(git -C "$REPO_DIR" rev-parse HEAD)"\n[[ "$ACTUAL_HEAD" == "$ACCEPTED_COMMIT" ]] \\\n    || fail 20 "temporary checkout HEAD mismatch"\n\n[[ "$(git -C "$REPO_DIR" symbolic-ref --quiet --short HEAD)" == "$BRANCH_NAME" ]] \\\n    || fail 20 "temporary checkout is not on the expected named branch"\n\n[[ -z "$(git -C "$REPO_DIR" status --porcelain=v1 --untracked-files=all)" ]] \\\n    || fail 20 "temporary checkout is not initially clean"\n\nmkdir -p "$REPO_DIR/operator-input"\nPAYLOAD_COPY="$REPO_DIR/operator-input/RPR-PG-001_architect_stage_payload.json"\ninstall -m 600 "$PAYLOAD_PATH" "$PAYLOAD_COPY"\n\nSOURCE_PAYLOAD_SHA="$(sha256sum "$PAYLOAD_PATH" | awk \'{print $1}\')"\nCOPIED_PAYLOAD_SHA="$(sha256sum "$PAYLOAD_COPY" | awk \'{print $1}\')"\n[[ "$SOURCE_PAYLOAD_SHA" == "$COPIED_PAYLOAD_SHA" ]] \\\n    || fail 21 "payload copy hash mismatch"\n\nPYTHON_BIN="python3"\nJSONSCHEMA_VERSION="$(python3 - <<\'PY\' 2>/dev/null || true\nimport importlib.metadata\nimport re\n\nversion = importlib.metadata.version("jsonschema")\nparts = tuple(int(x) for x in re.findall(r"\\d+", version)[:3])\nif parts < (4, 22, 0) or parts >= (5, 0, 0):\n    raise SystemExit(1)\nprint(version)\nPY\n)"\n\nif [[ -z "$JSONSCHEMA_VERSION" ]]; then\n    VENV_DIR="$LOG_DIR/venv"\n    python3 -m venv "$VENV_DIR" \\\n        || fail 22 "python3-venv is unavailable"\n    PYTHON_BIN="$VENV_DIR/bin/python"\n    "$PYTHON_BIN" -m pip install \\\n        --disable-pip-version-check \\\n        --no-input \\\n        --quiet \\\n        \'jsonschema>=4.22,<5\' \\\n        || fail 22 "jsonschema installation failed"\n    JSONSCHEMA_VERSION="$("$PYTHON_BIN" -c \'import importlib.metadata; print(importlib.metadata.version("jsonschema"))\')"\nfi\n\nPYTHON_VERSION="$("$PYTHON_BIN" --version 2>&1)"\n\ncd "$REPO_DIR"\n\ngit status --porcelain=v1 --untracked-files=all \\\n    > "$LOG_DIR/pre-export-git-status.txt"\n\nset +e\n"$PYTHON_BIN" scripts/export-architect-project-gate.py \\\n    --payload operator-input/RPR-PG-001_architect_stage_payload.json \\\n    --run-id "$RUN_ID" \\\n    --output architect-project-gate.json \\\n    --format json \\\n    > "$LOG_DIR/architect-project-gate.receipt.json" \\\n    2> "$LOG_DIR/architect-project-gate.stderr.log"\nEXPORT_RC=$?\nset -e\n\ngit status --porcelain=v1 --untracked-files=all \\\n    > "$LOG_DIR/post-export-git-status.txt" || true\n\ncp "$LOG_DIR/pre-export-git-status.txt" \\\n   "$OUTPUT_DIR/pre-export-git-status.txt"\ncp "$LOG_DIR/post-export-git-status.txt" \\\n   "$OUTPUT_DIR/post-export-git-status.txt"\ncp "$LOG_DIR/architect-project-gate.receipt.json" \\\n   "$OUTPUT_DIR/architect-project-gate.receipt.json"\ncp "$LOG_DIR/architect-project-gate.stderr.log" \\\n   "$OUTPUT_DIR/architect-project-gate.stderr.log"\n\nif [[ "$EXPORT_RC" -ne 0 ]]; then\n    python3 - "$OUTPUT_DIR/export-failure.json" "$EXPORT_RC" "$ACCEPTED_COMMIT" <<\'PY\'\nimport json\nimport sys\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\npath, rc, commit = sys.argv[1:]\ndata = {\n    "schema_version": "ev4-python-wrapper-failure.v1",\n    "generated_at_utc": datetime.now(timezone.utc).isoformat(),\n    "export_exit_code": int(rc),\n    "accepted_commit": commit,\n}\nPath(path).write_text(\n    json.dumps(data, indent=2, sort_keys=True) + "\\n",\n    encoding="utf-8",\n)\nPY\n    fail "$EXPORT_RC" "official exporter failed; inspect receipt and stderr logs"\nfi\n\n[[ -f architect-project-gate.json ]] \\\n    || fail 23 "official exporter returned success without an artifact"\n\n"$PYTHON_BIN" - \\\n    "$LOG_DIR/architect-project-gate.receipt.json" \\\n    architect-project-gate.json \\\n    "$ACCEPTED_COMMIT" \\\n    "$RUN_ID" <<\'PY\'\nimport json\nimport sys\nfrom pathlib import Path\n\nreceipt_path, artifact_path, commit, run_id = sys.argv[1:]\n\nwith Path(receipt_path).open("r", encoding="utf-8") as handle:\n    receipt = json.load(handle)\nwith Path(artifact_path).open("r", encoding="utf-8") as handle:\n    artifact = json.load(handle)\n\nassert receipt["output_committed"] is True\nassert receipt["handoff_allowed"] is True\nassert receipt["receipt_scope"] == "historical_commit"\nassert receipt["producer_commit"] == commit\n\nassert artifact["schema_version"] == "producer-gate-export.v1"\nassert artifact["run_id"] == run_id\nassert artifact["producer"]["repository"] == "rezahh107/EV4-Architect-Repo"\nassert artifact["producer"]["commit_sha"] == commit\nassert artifact["handoff"]["allowed"] is True\nassert artifact["validation"]["schema_valid"] is True\nassert artifact["validation"]["semantic_valid"] is True\n\nbundle = artifact["final_stage_bundle"]\nassert bundle["schema_version"] == "stage-evidence-bundle.v1"\nassert bundle["synthetic"] is False\nassert bundle["produced_by"]["repository"] == "rezahh107/EV4-Architect-Repo"\nassert bundle["produced_by"]["commit_sha"] == commit\nPY\n\ncp architect-project-gate.json "$OUTPUT_DIR/architect-project-gate.json"\n\nARTIFACT_SHA="$(sha256sum "$OUTPUT_DIR/architect-project-gate.json" | awk \'{print $1}\')"\nRECEIPT_SHA="$(sha256sum "$OUTPUT_DIR/architect-project-gate.receipt.json" | awk \'{print $1}\')"\n\npython3 - \\\n    "$OUTPUT_DIR/export-metadata.json" \\\n    "$ACCEPTED_COMMIT" \\\n    "$RUN_ID" \\\n    "$ACTUAL_HEAD" \\\n    "$BRANCH_NAME" \\\n    "$SOURCE_PAYLOAD_SHA" \\\n    "$ARTIFACT_SHA" \\\n    "$RECEIPT_SHA" \\\n    "$PYTHON_VERSION" \\\n    "$JSONSCHEMA_VERSION" \\\n    "$ORIGIN_RAW" <<\'PY\'\nimport json\nimport sys\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\n(\n    output_path,\n    commit,\n    run_id,\n    actual_head,\n    branch,\n    payload_sha,\n    artifact_sha,\n    receipt_sha,\n    python_version,\n    jsonschema_version,\n    origin,\n) = sys.argv[1:]\n\ndata = {\n    "schema_version": "ev4-python-wrapper-export-metadata.v1",\n    "generated_at_utc": datetime.now(timezone.utc).isoformat(),\n    "repository": "rezahh107/EV4-Architect-Repo",\n    "accepted_commit": commit,\n    "pin_source": "embedded_current_project_gate_lock",\n    "run_id": run_id,\n    "actual_head": actual_head,\n    "named_branch": branch,\n    "source_payload_sha256": payload_sha,\n    "artifact_sha256": artifact_sha,\n    "receipt_sha256": receipt_sha,\n    "python_version": python_version,\n    "jsonschema_version": jsonschema_version,\n    "source_origin": origin,\n}\nPath(output_path).write_text(\n    json.dumps(data, indent=2, sort_keys=True) + "\\n",\n    encoding="utf-8",\n)\nPY\n\n(\n    cd "$OUTPUT_DIR"\n    sha256sum \\\n        architect-project-gate.json \\\n        architect-project-gate.receipt.json \\\n        export-metadata.json \\\n        > SHA256SUMS.txt\n)\n\nSUCCESS=1\nprintf \'\\nOfficial Architect export completed and verified.\\n\'\nprintf \'Accepted commit: %s\\n\' "$ACCEPTED_COMMIT"\nprintf \'Artifact: %s/architect-project-gate.json\\n\' "$OUTPUT_DIR"\n'


class WrapperError(RuntimeError):
    """Expected operator-facing wrapper failure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def windows_to_wsl(path: Path) -> str:
    resolved = path.resolve()
    text = str(resolved)
    match = re.fullmatch(r"([A-Za-z]):\\(.*)", text)
    if match is None:
        raise WrapperError(
            "Only absolute Windows drive-letter paths are supported; "
            f"received: {resolved}"
        )
    drive = match.group(1).lower()
    tail = match.group(2).replace("\\", "/")
    return f"/mnt/{drive}/{tail}"


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WrapperError(f"Could not read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WrapperError(f"Expected a JSON object in {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_success(
    *,
    output_dir: Path,
    accepted_commit: str,
    run_id: str,
) -> None:
    artifact_path = output_dir / "architect-project-gate.json"
    receipt_path = output_dir / "architect-project-gate.receipt.json"

    for required in (artifact_path, receipt_path):
        if not required.is_file():
            raise WrapperError(
                "WSL returned success but a required file is missing: "
                f"{required}"
            )

    receipt = load_json(receipt_path)
    artifact = load_json(artifact_path)

    checks = [
        (receipt.get("output_committed") is True, "receipt.output_committed"),
        (receipt.get("handoff_allowed") is True, "receipt.handoff_allowed"),
        (
            receipt.get("receipt_scope") == "historical_commit",
            "receipt.receipt_scope",
        ),
        (
            receipt.get("producer_commit") == accepted_commit,
            "receipt.producer_commit",
        ),
        (
            artifact.get("schema_version") == "producer-gate-export.v1",
            "artifact.schema_version",
        ),
        (artifact.get("run_id") == run_id, "artifact.run_id"),
        (
            artifact.get("producer", {}).get("commit_sha") == accepted_commit,
            "artifact.producer.commit_sha",
        ),
        (
            artifact.get("handoff", {}).get("allowed") is True,
            "artifact.handoff.allowed",
        ),
        (
            artifact.get("validation", {}).get("schema_valid") is True,
            "artifact.validation.schema_valid",
        ),
        (
            artifact.get("validation", {}).get("semantic_valid") is True,
            "artifact.validation.semantic_valid",
        ),
        (
            artifact.get("final_stage_bundle", {}).get("synthetic") is False,
            "artifact.final_stage_bundle.synthetic",
        ),
        (
            artifact.get("final_stage_bundle", {})
            .get("produced_by", {})
            .get("commit_sha")
            == accepted_commit,
            "artifact.final_stage_bundle.produced_by.commit_sha",
        ),
    ]

    failures = [name for passed, name in checks if not passed]
    if failures:
        raise WrapperError(
            "Post-export verification failed for: " + ", ".join(failures)
        )

    write_json(
        output_dir / "windows-verification.json",
        {
            "schema_version": "ev4-python-wrapper-windows-verification.v1",
            "verified_at_utc": utc_now(),
            "accepted_commit": accepted_commit,
            "run_id": run_id,
            "artifact_sha256": sha256_file(artifact_path),
            "receipt_sha256": sha256_file(receipt_path),
            "status": "pass",
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the official EV4 Architect Project Gate exporter inside "
            "a clean Linux checkout in WSL."
        )
    )
    parser.add_argument("--payload", default=DEFAULT_PAYLOAD)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument(
        "--accepted-commit",
        default=DEFAULT_ACCEPTED_COMMIT,
        help=(
            "Full Architect commit accepted by Project Gate. "
            "The bundled default was verified against the live lock."
        ),
    )
    parser.add_argument(
        "--local-repo",
        default=None,
        help=(
            "Windows path to EV4-Architect-Repo. "
            "Default: parent directory of this bundle."
        ),
    )
    parser.add_argument("--wsl-distro", default=None)
    parser.add_argument(
        "--keep-linux-diagnostics",
        action="store_true",
        help="Retain temporary Linux directories only after failure.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if os.name != "nt":
        raise WrapperError("This wrapper must be launched from Windows Python.")

    if not re.fullmatch(r"[0-9a-fA-F]{40}", args.accepted_commit):
        raise WrapperError("--accepted-commit must be a full 40-character SHA.")
    accepted_commit = args.accepted_commit.lower()

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", args.run_id):
        raise WrapperError("Invalid --run-id format.")

    script_dir = Path(__file__).resolve().parent
    payload_path = Path(args.payload)
    if not payload_path.is_absolute():
        payload_path = script_dir / payload_path
    payload_path = payload_path.resolve()

    if args.local_repo:
        local_repo = Path(args.local_repo).resolve()
    else:
        local_repo = script_dir.parent.resolve()

    if not payload_path.is_file():
        raise WrapperError(f"Payload file was not found: {payload_path}")
    if not local_repo.is_dir():
        raise WrapperError(f"Architect repository was not found: {local_repo}")

    wsl_executable = shutil.which("wsl.exe")
    if wsl_executable is None:
        raise WrapperError("wsl.exe was not found. Install or enable WSL first.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_dir = (
        script_dir
        / f"architect-project-gate-output-{timestamp}-{uuid.uuid4().hex[:8]}"
    )
    output_dir.mkdir(parents=False, exist_ok=False)

    driver_metadata_path = output_dir / "driver-metadata.json"
    driver_metadata: dict[str, Any] = {
        "schema_version": "ev4-python-wrapper-driver-metadata.v1",
        "script_version": SCRIPT_VERSION,
        "started_at_utc": utc_now(),
        "completed_at_utc": None,
        "status": "running",
        "exit_code": None,
        "payload_path": str(payload_path),
        "local_repo": str(local_repo),
        "accepted_commit": accepted_commit,
        "accepted_commit_source": "live_project_gate_lock_checked_2026-07-22",
        "bytecode_write_policy": "disabled_in_linux_export_process",
        "run_id": args.run_id,
        "wsl_distro": args.wsl_distro,
    }
    write_json(driver_metadata_path, driver_metadata)

    temp_script_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            suffix=".sh",
            prefix=".ev4-architect-export-",
            dir=script_dir,
            delete=False,
        ) as handle:
            handle.write(BASH_SCRIPT)
            temp_script_path = Path(handle.name)

        command = [wsl_executable]
        if args.wsl_distro:
            command.extend(["-d", args.wsl_distro])
        command.extend(
            [
                "--exec",
                "bash",
                windows_to_wsl(temp_script_path),
                "--payload",
                windows_to_wsl(payload_path),
                "--output-dir",
                windows_to_wsl(output_dir),
                "--local-repo",
                windows_to_wsl(local_repo),
                "--run-id",
                args.run_id,
                "--accepted-commit",
                accepted_commit,
            ]
        )
        if args.keep_linux_diagnostics:
            command.append("--keep-diagnostics")

        print()
        print("EV4 Architect official exporter — Python wrapper")
        print(f"Payload:   {payload_path}")
        print(f"Repository: {local_repo}")
        print(f"Output:    {output_dir}")
        print(f"Commit:    {accepted_commit}")
        print()

        completed = subprocess.run(command, check=False)
        exit_code = completed.returncode

        driver_metadata["completed_at_utc"] = utc_now()
        driver_metadata["exit_code"] = exit_code
        driver_metadata["status"] = (
            "wsl_completed" if exit_code == 0 else "wsl_failed"
        )
        write_json(driver_metadata_path, driver_metadata)

        if exit_code != 0:
            print()
            print(f"FAILED with exit code {exit_code}")
            print(f"Diagnostic directory: {output_dir}")
            return exit_code

        validate_success(
            output_dir=output_dir,
            accepted_commit=accepted_commit,
            run_id=args.run_id,
        )

        driver_metadata["completed_at_utc"] = utc_now()
        driver_metadata["status"] = "verified_success"
        driver_metadata["artifact_sha256"] = sha256_file(
            output_dir / "architect-project-gate.json"
        )
        write_json(driver_metadata_path, driver_metadata)

        print()
        print("PASS")
        print(
            "Generated artifact: "
            f"{output_dir / 'architect-project-gate.json'}"
        )
        return 0

    finally:
        if temp_script_path is not None:
            try:
                temp_script_path.unlink(missing_ok=True)
            except OSError:
                pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WrapperError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
