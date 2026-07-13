from pathlib import Path

path = Path('.github/pr26_repair.py')
text = path.read_text(encoding='utf-8')

obsolete = '''rep(
    tests,
    '        run: "python scripts/check-ai-governance.py"\\n',
    '        run: "python -I -P scripts/check-ai-governance.py"\\n',
)
'''
if text.count(obsolete) != 1:
    raise SystemExit('fail-closed obsolete replacement mismatch')
text = text.replace(obsolete, '', 1)

marker = 'marker = "# PRF-002/003/004 execution-image and proof-surface regressions"'
normalization = '''legacy = tests.read_text(encoding="utf-8")
legacy = legacy.replace(
    "python scripts/check-ai-governance.py",
    "python -I -P scripts/check-ai-governance.py",
)
tests.write_text(legacy, encoding="utf-8")

''' + marker
if text.count(marker) != 1:
    raise SystemExit('fail-closed legacy fixture marker mismatch')
text = text.replace(marker, normalization, 1)

cleanup = '''    root / ".github/pr26_repair.py",
'''
replacement = cleanup + '''    root / ".github/pr26_repair_fix.py",
'''
if text.count(cleanup) != 1:
    raise SystemExit('fail-closed cleanup marker mismatch')
text = text.replace(cleanup, replacement, 1)

path.write_text(text, encoding='utf-8')
