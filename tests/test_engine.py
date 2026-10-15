"""Tests for the rule runner and the exit-code contract."""

from __future__ import annotations

from datetime import date

from modelcard_lint.engine import EXIT_OK, EXIT_VIOLATIONS, exit_code, lint
from modelcard_lint.manifest import MISSING
from modelcard_lint.policy import Policy
from modelcard_lint.types import Finding, Report, Severity


def test_lint_uses_default_policy_and_wall_clock(make_card, card_data) -> None:
    report = lint(make_card(card_data))
    assert report.source == "card.json"
    assert report.findings == ()


def test_lint_honours_severity_override(make_card, card_data, mutate) -> None:
    card = make_card(mutate(card_data, "license", "Unknown-9.9"))
    policy = Policy(severity_overrides={"MCL004": Severity.ERROR})
    report = lint(card, policy, today=date(2026, 1, 15))
    assert [finding.severity for finding in report.findings] == [Severity.ERROR]
    assert len(report.errors) == 1


def test_lint_strict_promotes_warnings(make_card, card_data, mutate) -> None:
    card = make_card(mutate(card_data, "license", "Unknown-9.9"))
    report = lint(card, Policy(strict=True), today=date(2026, 1, 15))
    assert report.errors == report.findings
    assert not report.warnings


def test_lint_strict_keeps_errors(make_card, card_data, mutate) -> None:
    card = make_card(mutate(card_data, "version", "1.4"))
    report = lint(card, Policy(strict=True), today=date(2026, 1, 15))
    assert [finding.rule_id for finding in report.findings] == ["MCL003"]
    assert report.findings[0].severity is Severity.ERROR


def test_lint_output_is_deterministic(make_card, card_data, mutate) -> None:
    mutate(card_data, "version", "1.4")
    mutate(card_data, "license", "Unknown-9.9")
    mutate(card_data, "traning_data_version", "3")
    first = lint(make_card(card_data), today=date(2026, 1, 15))
    second = lint(make_card(card_data), today=date(2026, 1, 15))
    assert first.findings == second.findings
    # Findings sort by manifest path, not by rule id: license < traning... < version.
    assert [finding.rule_id for finding in first.findings] == ["MCL004", "MCL009", "MCL003"]


def test_lint_records_source_path(make_card, card_data) -> None:
    card = make_card(card_data, path="examples/good-card.json")
    assert lint(card).source == str(card.path)


def test_exit_code_clean_report() -> None:
    assert exit_code(Report(source="card.json")) == EXIT_OK


def test_exit_code_fails_on_errors() -> None:
    report = Report(
        source="card.json",
        findings=(
            Finding(path="version", rule_id="MCL003", severity=Severity.ERROR, message="bad"),
        ),
    )
    assert exit_code(report) == EXIT_VIOLATIONS


def test_exit_code_respects_warning_budget(make_card, card_data, mutate) -> None:
    card = make_card(mutate(card_data, "license", "Unknown-9.9"))
    report = lint(card, today=date(2026, 1, 15))
    assert exit_code(report) == EXIT_OK
    assert exit_code(report, max_warnings=1) == EXIT_OK
    assert exit_code(report, max_warnings=0) == EXIT_VIOLATIONS


def test_exit_code_ignores_missing_required_field_branch(make_card, card_data, mutate) -> None:
    card = make_card(mutate(card_data, "limitations", MISSING))
    report = lint(card, today=date(2026, 1, 15))
    assert exit_code(report) == EXIT_VIOLATIONS
    assert exit_code(report, max_warnings=100) == EXIT_VIOLATIONS
