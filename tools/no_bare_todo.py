"""Reject bare task markers so work is tracked in issues instead of comments.

``TODO(#12): ...`` is allowed because it points at a real issue. A bare
``TODO: ...`` is not: it is work that will be forgotten, and the whole point of
this repository's workflow is that nothing depends on somebody's memory.

Usage:
    python tools/no_bare_todo.py [paths ...]
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

SUMMARY = re.compile(r"^\s*(?:[rubfRUBF]*\"\"\"|''')")
MARKER = re.compile(r"\b(TODO|FIXME|XXX)\b(?!\()")
LINKED = re.compile(r"\b(TODO|FIXME|XXX)\(#\d+\)")
EXEMPT_NAMES = frozenset({"no_bare_todo.py"})
SKIP_DIRS = frozenset(
    {".git", ".venv", "venv", "__pycache__", "build", "dist", "node_modules", ".pytest_cache"}
)


def check_file(path: Path) -> list[str]:
    """Return one problem line per bare marker in ``path``.

    Args:
        path: File to scan.

    Returns:
        Problems formatted as ``path:line: marker``.
    """
    if path.name in EXEMPT_NAMES:
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    problems: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if LINKED.search(line):
            continue
        if MARKER.search(line):
            problems.append(
                f"{path}:{number}: bare task marker; use 'TODO(#issue)' or open an issue"
            )
    return problems


def check_paths(paths: Iterable[str | Path]) -> list[str]:
    """Return every problem found across ``paths``.

    Directories are walked for ``*.py`` files, skipping virtual environments and
    build caches so a repository-root scan stays fast and does not report on
    vendored third-party code.

    Args:
        paths: Files or directories to scan.

    Returns:
        A flat list of problem descriptions.
    """
    problems: list[str] = []
    for entry in paths:
        path = Path(entry)
        if path.is_dir():
            for child in sorted(path.rglob("*.py")):
                if SKIP_DIRS.intersection(child.parts):
                    continue
                problems.extend(check_file(child))
        else:
            problems.extend(check_file(path))
    return problems


def main(argv: Sequence[str] | None = None) -> int:
    """Scan the files named on the command line (or the current directory).

    Args:
        argv: Arguments without the program name.

    Returns:
        0 when clean, 1 when bare markers were found.
    """
    targets = list(sys.argv[1:] if argv is None else argv) or ["."]
    problems = check_paths(targets)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
