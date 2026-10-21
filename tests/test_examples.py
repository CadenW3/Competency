"""Tests that pin the shipped example documents to the documented behaviour.

These tests are the reason the examples can be screenshotted in the README or a
class report without going stale: if a rule changes, the example output changes
here first.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from modelcard_lint.engine import EXIT_VIOLATIONS, exit_code, lint
from modelcard_lint.manifest import load_manifest
from modelcard_lint.policy import load_policy

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
TODAY = date(2026, 1, 15)

DEFAULT_POLICY_RULES = {
    "MCL002",
    "MCL003",
    "MCL004",
    "MCL005",
    "MCL006",
    "MCL008",
    "MCL009",
    "MCL010",
    "MCL011",
}


def test_good_example_is_clean_with_default_policy() -> None:
    report = lint(load_manifest(EXAMPLES / "good-card.json"), today=TODAY)
    assert report.findings == ()
    assert exit_code(report) == 0


def test_good_example_is_clean_with_repository_policy() -> None:
    report = lint(
        load_manifest(EXAMPLES / "good-card.json"),
        load_policy(EXAMPLES / "policy.json"),
        today=TODAY,
    )
    assert report.findings == ()


def test_bad_example_trips_the_default_rule_set() -> None:
    report = lint(load_manifest(EXAMPLES / "bad-card.json"), today=TODAY)
    rule_ids = {finding.rule_id for finding in report.findings}
    assert rule_ids >= DEFAULT_POLICY_RULES
    assert exit_code(report) == EXIT_VIOLATIONS


def test_bad_example_trips_policy_rule_mcl007() -> None:
    report = lint(
        load_manifest(EXAMPLES / "bad-card.json"),
        load_policy(EXAMPLES / "policy.json"),
        today=TODAY,
    )
    missing_metrics = [finding for finding in report.findings if finding.rule_id == "MCL007"]
    assert len(missing_metrics) == 2


def test_bad_example_reports_errors_and_warnings() -> None:
    report = lint(load_manifest(EXAMPLES / "bad-card.json"), today=TODAY)
    assert report.errors
    assert report.warnings
    assert "warning" in report.summary()
