"""Reporters: one report, three renderings.

Every renderer is a pure function of :class:`~modelcard_lint.types.Report`, so
adding a format cannot change lint behaviour. The three formats exist for three
audiences:

* ``text`` -- a human reading a terminal.
* ``json`` -- a script or dashboard consuming the result.
* ``github`` -- GitHub Actions, which turns ``::error file=...::`` lines into
  annotations on the pull request diff.
"""

from __future__ import annotations

import json

from modelcard_lint.types import Report, Severity

FORMATS: tuple[str, ...] = ("text", "json", "github")
"""Every format accepted by ``--format``."""

_STATUS = {Severity.ERROR: "error", Severity.WARNING: "warning", Severity.INFO: "notice"}


def _escape_annotation(value: str) -> str:
    """Escape a string for GitHub Actions workflow-command syntax.

    Args:
        value: Raw message text.

    Returns:
        Text safe to place in a ``::error file=...::message`` command.
    """
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def format_text(report: Report) -> str:
    """Render a report for a human reading a terminal.

    Args:
        report: Report to render.

    Returns:
        A multi-line string ending in a newline.
    """
    lines = [f"{report.source}: {report.summary()}"]
    for finding in report.findings:
        location = finding.path or "<root>"
        lines.append(
            f"  {finding.severity.value:<7} {finding.rule_id}  {location}: {finding.message}"
        )
    return "\n".join(lines) + "\n"


def format_json(report: Report) -> str:
    """Render a report as stable, machine-readable JSON.

    Args:
        report: Report to render.

    Returns:
        A JSON document with keys sorted so diffing two runs is meaningful.
    """
    counts = report.counts()
    payload = {
        "source": report.source,
        "summary": {severity.value: counts[severity] for severity in Severity},
        "findings": [
            {
                "path": finding.path,
                "rule_id": finding.rule_id,
                "severity": finding.severity.value,
                "message": finding.message,
            }
            for finding in report.findings
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def format_github(report: Report) -> str:
    """Render a report as GitHub Actions workflow commands.

    Args:
        report: Report to render.

    Returns:
        One ``::error``/``::warning``/``::notice`` line per finding.
    """
    lines = [
        f"::{_STATUS[finding.severity]} file={report.source}::{_escape_annotation(finding.rule_id)}"
        f" {_escape_annotation(finding.path or '<root>')}: {_escape_annotation(finding.message)}"
        for finding in report.findings
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def format_report(report: Report, style: str = "text") -> str:
    """Dispatch to the renderer named by ``style``.

    Args:
        report: Report to render.
        style: One of :data:`FORMATS`.

    Returns:
        The rendered report.

    Raises:
        ValueError: If ``style`` is not a known format.
    """
    renderers = {"text": format_text, "json": format_json, "github": format_github}
    try:
        renderer = renderers[style]
    except KeyError as exc:
        known = ", ".join(FORMATS)
        msg = f"unknown format {style!r}; expected one of: {known}"
        raise ValueError(msg) from exc
    return renderer(report)
