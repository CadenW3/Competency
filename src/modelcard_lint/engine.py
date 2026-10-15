"""The rule runner and the exit-code contract.

The engine is the single place that turns "a manifest plus a policy" into "a
report plus a process exit code". Keeping the exit-code contract here -- rather
than scattering ``sys.exit`` calls through the CLI -- means the gate behaviour
is unit-testable and documented in exactly one place (ADR 0002).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from modelcard_lint.manifest import ModelCard
from modelcard_lint.policy import Policy
from modelcard_lint.rules import RULES
from modelcard_lint.types import Finding, Report, Severity, sort_findings

EXIT_OK = 0
"""No blocking findings."""

EXIT_VIOLATIONS = 1
"""At least one blocking finding (error, or warning under ``--strict``)."""

EXIT_USAGE = 2
"""Bad input: unreadable manifest, invalid policy, or bad arguments."""


def lint(card: ModelCard, policy: Policy | None = None, *, today: date | None = None) -> Report:
    """Evaluate every registered rule against ``card``.

    Args:
        card: Manifest loaded by :func:`modelcard_lint.manifest.load_manifest`.
        policy: Project policy. Defaults to a policy with stock settings.
        today: Reference date for time-sensitive rules. Injecting it keeps runs
            reproducible; production callers can leave it ``None`` to use the
            wall clock.

    Returns:
        A report whose findings are sorted deterministically.

    Examples:
        >>> from pathlib import Path
        >>> from modelcard_lint.manifest import ModelCard
        >>> card = ModelCard(path=Path("card.json"), raw={"name": "demo"})
        >>> [finding.rule_id for finding in lint(card).findings][:1]
        ['MCL001']
    """
    active_policy = Policy() if policy is None else policy
    reference_day = date.today() if today is None else today

    findings: list[Finding] = []
    for rule in RULES:
        severity = active_policy.severity_for(rule.id, rule.severity)
        if active_policy.strict and severity is Severity.WARNING:
            severity = Severity.ERROR
        for finding in rule.check(card, active_policy, reference_day):
            findings.append(replace(finding, severity=severity))

    return Report(source=str(card.path), findings=sort_findings(findings))


def exit_code(report: Report, *, max_warnings: int | None = None) -> int:
    """Map a report onto the documented exit-code contract.

    Args:
        report: Report produced by :func:`lint`.
        max_warnings: Optional budget; a run fails once warnings exceed it.

    Returns:
        :data:`EXIT_OK` or :data:`EXIT_VIOLATIONS`.
    """
    if report.errors:
        return EXIT_VIOLATIONS
    if max_warnings is not None and len(report.warnings) > max_warnings:
        return EXIT_VIOLATIONS
    return EXIT_OK
