"""Tests for the repository's helper scripts in `tools/`."""

from __future__ import annotations

from pathlib import Path

import assert_example_fails
import no_bare_todo

# Built with explicit concatenation so this file does not trip the rule it tests.
MARKER = "TO" + "DO"
FIX = "FIX" + "ME"


def test_example_still_fails_as_documented(capsys) -> None:
    assert assert_example_fails.main() == 0
    assert "still fails as documented" in capsys.readouterr().out


def test_bare_marker_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "module.py"
    path.write_text(f"# {MARKER}: write this later\n", encoding="utf-8")
    problems = no_bare_todo.check_file(path)
    assert len(problems) == 1
    assert "bare task marker" in problems[0]


def test_linked_marker_is_accepted(tmp_path: Path) -> None:
    path = tmp_path / "module.py"
    path.write_text(f"# {MARKER}(#12): add MCL012\n", encoding="utf-8")
    assert no_bare_todo.check_file(path) == []


def test_marker_without_separator_is_ignored(tmp_path: Path) -> None:
    path = tmp_path / "module.py"
    path.write_text(f"{MARKER}LIST = []\n", encoding="utf-8")
    assert no_bare_todo.check_file(path) == []


def test_exempt_file_is_skipped(tmp_path: Path) -> None:
    path = tmp_path / "no_bare_todo.py"
    path.write_text(f"{FIX}: self-reference\n", encoding="utf-8")
    assert no_bare_todo.check_file(path) == []


def test_unreadable_file_is_ignored(tmp_path: Path) -> None:
    assert no_bare_todo.check_file(tmp_path / "absent.py") == []


def test_directory_scan_and_exit_code(tmp_path: Path) -> None:
    module = tmp_path / "bad.py"
    module.write_text(f"{MARKER}: later\n", encoding="utf-8")
    assert no_bare_todo.main([str(tmp_path)]) == 1
    module.write_text(f"{MARKER}(#7): later\n", encoding="utf-8")
    assert no_bare_todo.main([str(tmp_path)]) == 0


def test_repository_tree_is_clean() -> None:
    # This is what CI asserts: no bare markers anywhere in the project sources.
    root = Path(__file__).resolve().parent.parent
    assert no_bare_todo.check_paths([root / "src", root / "tests", root / "tools"]) == []
