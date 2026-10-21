"""Tests for the shared value types."""

from __future__ import annotations

import pytest

from modelcard_lint.types import Finding, Report, Severity, sort_findings


def _finding(path: str, rule_id: str, severity: Severity, message: str = "problem") -> Finding:
    return Finding(path=path, rule_id=rule_id, severity=severity, message=message)


def test_severity_rank_orders_info_warning_error() -> None:
    assert Severity.INFO.rank < Severity.WARNING.rank < Severity.ERROR.rank


def test_severity_parse_is_case_and_space_insensitive() -> None:
    assert Severity.parse("  ERROR ") is Severity.ERROR
    assert Severity.parse("Warning") is Severity.WARNING


def test_severity_parse_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="unknown severity 'fatal'"):
        Severity.parse("fatal")


def test_finding_renders_root_location() -> None:
    assert str(_finding("", "MCL009", Severity.WARNING)) == "<root>: MCL009 [warning] problem"


def test_finding_renders_dotted_location() -> None:
    assert str(_finding("owner.contact", "MCL006", Severity.ERROR)) == (
        "owner.contact: MCL006 [error] problem"
    )


def test_sort_findings_is_deterministic() -> None:
    findings = [
        _finding("owner.contact", "MCL006", Severity.WARNING, "b"),
        _finding("license", "MCL004", Severity.WARNING, "a"),
        _finding("license", "MCL004", Severity.WARNING, "A"),
    ]
    assert [f.message for f in sort_findings(findings)] == ["A", "a", "b"]


def test_report_filters_by_severity() -> None:
    report = Report(
        source="card.json",
        findings=sort_findings(
            [
                _finding("version", "MCL003", Severity.ERROR),
                _finding("license", "MCL004", Severity.WARNING),
                _finding("name", "MCL012", Severity.INFO),
            ]
        ),
    )
    assert len(report.errors) == 1
    assert len(report.warnings) == 1
    assert len(report.of(Severity.INFO)) == 1


def test_report_counts_include_zero_entries() -> None:
    report = Report(source="card.json", findings=(_finding("version", "MCL003", Severity.ERROR),))
    counts = report.counts()
    assert counts[Severity.ERROR] == 1
    assert counts[Severity.WARNING] == 0
    assert counts[Severity.INFO] == 0


def test_report_worst_severity() -> None:
    assert Report(source="card.json").worst is None
    report = Report(
        source="card.json",
        findings=(
            _finding("license", "MCL004", Severity.WARNING),
            _finding("version", "MCL003", Severity.ERROR),
        ),
    )
    assert report.worst is Severity.ERROR


def test_report_summary_pluralisation() -> None:
    empty = Report(source="card.json")
    assert empty.summary() == "no findings"

    single = Report(source="card.json", findings=(_finding("version", "MCL003", Severity.ERROR),))
    assert single.summary() == "1 error"

    mixed = Report(
        source="card.json",
        findings=(
            _finding("version", "MCL003", Severity.ERROR),
            _finding("name", "MCL003", Severity.ERROR),
            _finding("license", "MCL004", Severity.WARNING),
            _finding("x", "MCL012", Severity.INFO),
        ),
    )
    assert mixed.summary() == "2 errors, 1 warning, 1 info"
