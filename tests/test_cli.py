"""Tests for the command-line interface.

Everything runs in-process through :func:`modelcard_lint.cli.main`, so the suite
does not depend on the console script being installed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modelcard_lint import __version__
from modelcard_lint.cli import build_parser, main
from modelcard_lint.engine import EXIT_OK, EXIT_USAGE, EXIT_VIOLATIONS


@pytest.fixture
def good_path(tmp_path: Path, card_data) -> Path:
    path = tmp_path / "good.json"
    path.write_text(json.dumps(card_data), encoding="utf-8")
    return path


@pytest.fixture
def warn_path(tmp_path: Path, card_data, mutate) -> Path:
    mutate(card_data, "license", "PatentPending-1.0")
    path = tmp_path / "warn.json"
    path.write_text(json.dumps(card_data), encoding="utf-8")
    return path


@pytest.fixture
def bad_path(tmp_path: Path, card_data, mutate) -> Path:
    mutate(card_data, "version", "1.4")
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(card_data), encoding="utf-8")
    return path


def test_clean_manifest_exits_zero(good_path: Path, capsys) -> None:
    assert main([str(good_path)]) == EXIT_OK
    out = capsys.readouterr().out
    assert "no findings" in out


def test_flagged_manifest_exits_one(bad_path: Path, capsys) -> None:
    assert main([str(bad_path)]) == EXIT_VIOLATIONS
    assert "MCL003" in capsys.readouterr().out


def test_missing_manifest_exits_two(tmp_path: Path, capsys) -> None:
    assert main([str(tmp_path / "absent.json")]) == EXIT_USAGE
    assert "manifest not found" in capsys.readouterr().err


def test_no_arguments_prints_usage(capsys) -> None:
    assert main([]) == EXIT_USAGE
    captured = capsys.readouterr()
    assert "usage:" in captured.err
    assert "at least one MANIFEST is required" in captured.err


def test_json_format_is_machine_readable(bad_path: Path, capsys) -> None:
    main([str(bad_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["error"] >= 1
    assert any(finding["rule_id"] == "MCL003" for finding in payload["findings"])


def test_github_format_emits_annotations(bad_path: Path, capsys) -> None:
    main([str(bad_path), "--format", "github"])
    assert capsys.readouterr().out.startswith("::error file=")


def test_strict_promotes_warnings(warn_path: Path, capsys) -> None:
    assert main([str(warn_path)]) == EXIT_OK
    assert main([str(warn_path), "--strict"]) == EXIT_VIOLATIONS
    assert "MCL004" in capsys.readouterr().out


def test_max_warnings_budget(warn_path: Path) -> None:
    assert main([str(warn_path), "--max-warnings", "1"]) == EXIT_OK
    assert main([str(warn_path), "--max-warnings", "0"]) == EXIT_VIOLATIONS


def test_today_flag_controls_expiry(tmp_path: Path, card_data, mutate) -> None:
    mutate(card_data, "review.due", "2026-06-01")
    path = tmp_path / "review.json"
    path.write_text(json.dumps(card_data), encoding="utf-8")
    assert main([str(path), "--today", "2026-01-01"]) == EXIT_OK
    assert main([str(path), "--today", "2026-12-31"]) == EXIT_VIOLATIONS


def test_policy_flag_applies_required_metrics(good_path: Path, tmp_path: Path, capsys) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps({"required_metrics": ["roc_auc"]}), encoding="utf-8")
    assert main([str(good_path), "--policy", str(policy_path), "--strict"]) == EXIT_VIOLATIONS
    assert "MCL007" in capsys.readouterr().out


def test_invalid_policy_exits_two(good_path: Path, tmp_path: Path, capsys) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text('{"required_feilds": []}', encoding="utf-8")
    assert main([str(good_path), "--policy", str(policy_path)]) == EXIT_USAGE
    assert "unknown key" in capsys.readouterr().err


def test_list_rules_prints_table(capsys) -> None:
    assert main(["--list-rules"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "MCL001" in out
    assert "MCL011" in out


def test_multiple_manifests_are_summarised(good_path: Path, bad_path: Path, capsys) -> None:
    assert main([str(good_path), str(bad_path)]) == EXIT_VIOLATIONS
    out = capsys.readouterr().out
    assert "2 manifests checked" in out


def test_version_flag_prints_version(capsys) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--version"])
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_bad_today_argument_is_rejected() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--today", "yesterday", "card.json"])
    assert excinfo.value.code == EXIT_USAGE


def test_negative_max_warnings_is_rejected() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--max-warnings", "-1", "card.json"])
    assert excinfo.value.code == EXIT_USAGE


def test_non_integer_max_warnings_is_rejected() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--max-warnings", "many", "card.json"])
    assert excinfo.value.code == EXIT_USAGE
