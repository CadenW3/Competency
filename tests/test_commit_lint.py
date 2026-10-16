"""Tests for the Conventional Commits validator hook."""

from __future__ import annotations

from pathlib import Path

import commit_lint


def test_valid_feature_message() -> None:
    assert commit_lint.validate("feat(cli): add --format github") == []


def test_valid_message_with_body() -> None:
    message = (
        "fix(rules): stop flagging optional review dates\n"
        "\n"
        "MCL008 treated a missing review block as an override.\n"
    )
    assert commit_lint.validate(message) == []


def test_unknown_type_is_rejected() -> None:
    problems = commit_lint.validate("wip: add stuff")
    assert any("unknown type 'wip'" in problem for problem in problems)


def test_header_without_colon_is_rejected() -> None:
    problems = commit_lint.validate("add the linter")
    assert any("header must look like" in problem for problem in problems)


def test_body_must_be_separated_by_blank_line() -> None:
    problems = commit_lint.validate("feat: add rule\nmore text here")
    assert any("blank line" in problem for problem in problems)


def test_subject_must_not_end_with_period() -> None:
    problems = commit_lint.validate("docs: update the readme.")
    assert any("period" in problem for problem in problems)


def test_subject_must_start_lowercase() -> None:
    problems = commit_lint.validate("docs: Update the readme")
    assert any("lowercase" in problem for problem in problems)


def test_header_length_is_enforced() -> None:
    problems = commit_lint.validate("feat: " + "a" * 80)
    assert any("limit is 72" in problem for problem in problems)


def test_subject_length_is_enforced() -> None:
    problems = commit_lint.validate("feat: " + "a" * 55)
    assert any("limit is 50" in problem for problem in problems)


def test_breaking_change_requires_footer() -> None:
    problems = commit_lint.validate("feat(api)!: drop the v1 flag")
    assert any("BREAKING CHANGE" in problem for problem in problems)


def test_breaking_change_with_footer_is_valid() -> None:
    message = "feat(api)!: drop the v1 flag\n\nBREAKING CHANGE: --v1 is gone.\n"
    assert commit_lint.validate(message) == []


def test_merge_commits_are_allowed() -> None:
    assert commit_lint.validate('Merge branch "feat/x" into main') == []


def test_generated_squash_commits_are_allowed() -> None:
    assert commit_lint.validate("squash! feat: add rule") == []


def test_comment_lines_are_ignored() -> None:
    message = "feat: add rule\n\n# Please enter the commit message\n#\n"
    assert commit_lint.validate(message) == []


def test_empty_message_is_rejected() -> None:
    assert commit_lint.validate("# only comments\n") == ["commit message is empty"]


def test_main_accepts_valid_file(tmp_path: Path) -> None:
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text("feat: add rule\n", encoding="utf-8")
    assert commit_lint.main([str(path)]) == 0


def test_main_reports_invalid_file(tmp_path: Path, capsys) -> None:
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text("nope\n", encoding="utf-8")
    assert commit_lint.main([str(path)]) == 1
    captured = capsys.readouterr()
    assert "invalid commit message" in captured.err
    assert "CONTRIBUTING.md" in captured.err


def test_main_requires_a_file(capsys) -> None:
    assert commit_lint.main([]) == 1
    assert "no commit message file given" in capsys.readouterr().err


def test_main_reports_unreadable_file(tmp_path: Path, capsys) -> None:
    assert commit_lint.main([str(tmp_path / "absent")]) == 1
    assert "cannot read" in capsys.readouterr().err
