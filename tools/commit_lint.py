"""Validate a commit message against the Conventional Commits 1.0.0 spec.

Installed as a ``commit-msg`` hook by ``pre-commit``. The rules enforced here
are the ones written down in ``CONTRIBUTING.md``; the point of automating them
is that a convention nobody can remember is not a convention.

The validator is a pure function (:func:`validate`) plus a thin
:func:`main` wrapper, so the whole rule set is testable without spawning a
process or touching git.

Usage:
    python tools/commit_lint.py <commit-message-file>
"""

from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from pathlib import Path

ALLOWED_TYPES: tuple[str, ...] = (
    "build",
    "chore",
    "ci",
    "docs",
    "feat",
    "fix",
    "perf",
    "refactor",
    "revert",
    "style",
    "test",
)
"""Commit types from CONTRIBUTING.md, sorted for stable error messages."""

MAX_HEADER_LENGTH = 72
MAX_SUBJECT_LENGTH = 50

_HEADER = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[a-z0-9][a-z0-9._/-]*)\))?"
    r"(?P<breaking>!)?"
    r": (?P<subject>\S.*)$"
)
_GENERATED = re.compile(r"^(?:Merge |Revert \"|fixup! |squash! )")


def _meaningful_lines(message: str) -> list[str]:
    """Return the message lines git would actually keep.

    Args:
        message: Raw commit message, including ``#`` comment lines.

    Returns:
        Lines with comments dropped, trailing blank lines removed.
    """
    lines = [line for line in message.splitlines() if not line.startswith("#")]
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def validate(message: str) -> list[str]:
    """Check a commit message and return the problems found.

    Args:
        message: Raw commit message text.

    Returns:
        A list of human-readable problems; empty means the message is valid.
    """
    lines = _meaningful_lines(message)
    if not lines:
        return ["commit message is empty"]

    header = lines[0]
    if _GENERATED.match(header):
        return []

    problems: list[str] = []
    match = _HEADER.match(header)
    if match is None:
        problems.append(
            "header must look like 'type(scope): subject' "
            f"(allowed types: {', '.join(ALLOWED_TYPES)})"
        )
        return problems

    commit_type = match.group("type")
    subject = match.group("subject")

    if commit_type not in ALLOWED_TYPES:
        problems.append(f"unknown type '{commit_type}' (allowed: {', '.join(ALLOWED_TYPES)})")
    if len(header) > MAX_HEADER_LENGTH:
        problems.append(f"header is {len(header)} characters, limit is {MAX_HEADER_LENGTH}")
    if len(subject) > MAX_SUBJECT_LENGTH:
        problems.append(f"subject is {len(subject)} characters, limit is {MAX_SUBJECT_LENGTH}")
    if subject.endswith("."):
        problems.append("subject must not end with a period")
    if subject[0].isupper():
        problems.append("subject must start in lowercase (imperative mood)")

    body = lines[1:]
    if body and body[0].strip():
        problems.append("body must be separated from the header by a blank line")

    if match.group("breaking") and not any(
        line.startswith(("BREAKING CHANGE:", "BREAKING-CHANGE:")) for line in lines
    ):
        problems.append("a '!' header requires a 'BREAKING CHANGE:' footer")

    return problems


def main(argv: Sequence[str] | None = None) -> int:
    """Validate each commit-message file named on the command line.

    Args:
        argv: Arguments without the program name. Defaults to ``sys.argv[1:]``.

    Returns:
        0 when every message is valid, 1 otherwise.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("commit_lint: no commit message file given", file=sys.stderr)
        return 1

    status = 0
    for name in args:
        try:
            message = Path(name).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"commit_lint: {name}: cannot read ({exc.strerror})", file=sys.stderr)
            status = 1
            continue
        problems = validate(message)
        if problems:
            status = 1
            print(f"commit_lint: {name}: invalid commit message", file=sys.stderr)
            for problem in problems:
                print(f"  - {problem}", file=sys.stderr)
            print(
                "\nSee CONTRIBUTING.md for the commit message convention.",
                file=sys.stderr,
            )
    return status


if __name__ == "__main__":
    sys.exit(main())
