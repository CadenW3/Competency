"""Tests for the text, JSON and GitHub-annotation reporters."""

from __future__ import annotations

import json
from datetime import date

import pytest

from modelcard_lint.engine import lint
from modelcard_lint.report import FORMATS, format_github, format_json, format_report, format_text
from modelcard_lint.types import Finding, Report, Severity, sort_findings


def _report(*findings: Finding, source: str = "card.json") -> Report:
    return Report(source=source, findings=sort_findings(findings))


def _finding(severity: Severity, message: str = "problem", path: str = "version") -> Finding:
    return Finding(path=path, rule_id="MCL003", severity=severity, message=message)


def test_formats_are_advertised() -> None:
    assert FORMATS == ("text", "json", "github")


def test_text_reports_no_findings() -> None:
    assert format_text(_report()) == "card.json: no findings\n"


def test_text_lists_findings_with_aligned_severity() -> None:
    output = format_text(_report(_finding(Severity.ERROR), _finding(Severity.WARNING, "warn")))
    lines = output.splitlines()
    assert lines[0] == "card.json: 1 error, 1 warning"
    assert lines[1].startswith("  error   MCL003  version: ")
    assert lines[2].startswith("  warning MCL003  version: warn")


def test_text_renders_root_location() -> None:
    output = format_text(_report(_finding(Severity.INFO, path="")))
    assert "<root>: problem" in output


def test_json_is_parseable_and_stable() -> None:
    payload = json.loads(format_json(_report(_finding(Severity.ERROR), _finding(Severity.INFO))))
    assert payload["source"] == "card.json"
    assert payload["summary"] == {"error": 1, "info": 1, "warning": 0}
    assert payload["findings"][0] == {
        "message": "problem",
        "path": "version",
        "rule_id": "MCL003",
        "severity": "error",
    }
    assert format_json(_report()) == format_json(_report())


def test_github_annotations_use_workflow_commands() -> None:
    output = format_github(_report(_finding(Severity.ERROR), _finding(Severity.WARNING)))
    lines = output.splitlines()
    assert lines[0].startswith("::error file=card.json::MCL003 version: problem")
    assert lines[1].startswith("::warning file=card.json::")


def test_github_annotations_are_escaped() -> None:
    output = format_github(_report(_finding(Severity.ERROR, "50% broken\nsecond line")))
    assert "%25" in output
    assert "%0A" in output
    assert output.count("\n") == 1


def test_github_output_is_empty_when_clean() -> None:
    assert format_github(_report()) == ""


def test_format_report_dispatches() -> None:
    report = _report(_finding(Severity.ERROR))
    assert format_report(report, "text") == format_text(report)
    assert format_report(report, "json") == format_json(report)
    assert format_report(report, "github") == format_github(report)


def test_format_report_defaults_to_text() -> None:
    report = _report()
    assert format_report(report) == format_text(report)


def test_format_report_rejects_unknown_style() -> None:
    with pytest.raises(ValueError, match="unknown format 'yaml'"):
        format_report(_report(), "yaml")


def test_reporter_output_matches_engine_report(make_card, card_data, mutate) -> None:
    card = make_card(mutate(card_data, "version", "1.4"))
    report = lint(card, today=date(2026, 1, 15))
    assert "MCL003" in format_text(report)
