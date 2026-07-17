from pathlib import Path

script_path = Path("scripts/export-architect-project-gate.py")
text = script_path.read_text(encoding="utf-8")

imports_old = "import tempfile\nfrom dataclasses import asdict, dataclass, field\n"
imports_new = """import tempfile

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX fallback
    msvcrt = None
from dataclasses import asdict, dataclass, field
"""
if imports_old not in text:
    raise SystemExit("import marker not found")
text = text.replace(imports_old, imports_new, 1)

result_old = "    output_written: bool = True\n\n\nclass ExportError"
result_new = "    output_written: bool = True\n    cleanup_warnings: list[str] = field(default_factory=list)\n\n\nclass ExportError"
if result_old not in text:
    raise SystemExit("ExportResult marker not found")
text = text.replace(result_old, result_new, 1)

marker = "def _identity(path: Path) -> tuple[int, int] | None:\n"
if marker not in text:
    raise SystemExit("transaction marker not found")
prefix = text[:text.index(marker)]
tail = Path(".github/prf003/exporter_tail.pyfrag").read_text(encoding="utf-8")
script_path.write_text(prefix + tail, encoding="utf-8")
