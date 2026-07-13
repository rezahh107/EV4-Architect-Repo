from pathlib import Path

P = Path("scripts/check-ai-governance.py")
text = P.read_text(encoding="utf-8")
old = '''def _is_fail_closed_exact_head_command(run: Any) -> bool:
    line = _single_command_line(run)
    if line is None:
        return False
    words = tuple(_shell_words(line))
    return words in {
        tuple(EXACT_HEAD_WORDS),
        tuple(["[", *EXACT_HEAD_WORDS[1:], "]"]),
        tuple(["[[", *EXACT_HEAD_WORDS[1:], "]]" ]),
    }
'''
new = '''def _is_fail_closed_exact_head_command(run: Any) -> bool:
    lines = tuple(_meaningful_command_lines(run))
    if lines == WORKSPACE_GUARD_LINES:
        return True
    if len(lines) != 1:
        return False
    words = tuple(_shell_words(lines[0]))
    return words in {
        tuple(EXACT_HEAD_WORDS),
        tuple(["[", *EXACT_HEAD_WORDS[1:], "]"]),
        tuple(["[[", *EXACT_HEAD_WORDS[1:], "]]" ]),
    }
'''
if text.count(old) != 1:
    raise SystemExit("exact-head compatibility replacement mismatch")
P.write_text(text.replace(old, new, 1), encoding="utf-8")
