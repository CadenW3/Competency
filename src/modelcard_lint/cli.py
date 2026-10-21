"""The command-line interface.

``main`` returns an exit code instead of calling ``sys.exit`` so the whole CLI
surface is testable in-process. Argument errors, unreadable manifests and
invalid policies all collapse onto exit code 2, which is the POSIX convention
for "you asked for something I cannot do".
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from pathlib import Path

from modelcard_lint import __version__
from modelcard_lint.engine import EXIT_OK, EXIT_USAGE, exit_code, lint
from modelcard_lint.manifest import ManifestError, load_manifest
from modelcard_lint.policy import Policy, PolicyError, load_policy
from modelcard_lint.report import FORMATS, format_report
from modelcard_lint.rules import RULES
from modelcard_lint.types import Report

_EPILOG = """\
exit codes:
  0  no blocking findings
  1  findings at or above the configured threshold (see --strict, --max-warnings)
  2  usage error: unreadable manifest, invalid policy, or bad arguments
"""


def _iso_date(value: str) -> date:
    """Parse an ISO-8601 date for ``--today``.

    Args:
        value: Date string in ``YYYY-MM-DD`` form.

    Returns:
        The parsed date.

    Raises:
        argparse.ArgumentTypeError: If ``value`` is not an ISO-8601 date.
    """
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not an ISO date (YYYY-MM-DD)") from None


def _count(value: str) -> int:
    """Parse a non-negative integer for ``--max-warnings``.

    Args:
        value: Raw command-line value.

    Returns:
        The parsed integer.

    Raises:
        argparse.ArgumentTypeError: If ``value`` is not a non-negative integer.
    """
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not an integer") from None
    if number < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return number


def build_parser(prog: str = "modelcard-lint") -> argparse.ArgumentParser:
    """Build the argument parser.

    Args:
        prog: Program name shown in usage and error messages.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Lint ML model-card manifests and fail CI when they are incomplete.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "manifests", nargs="*", metavar="MANIFEST", help="JSON model-card manifest to lint"
    )
    parser.add_argument(
        "--policy", type=Path, default=None, help="JSON policy file (default: built-in policy)"
    )
    parser.add_argument(
        "--format", choices=FORMATS, default="text", help="output format (default: text)"
    )
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument(
        "--max-warnings",
        type=_count,
        default=None,
        metavar="N",
        help="fail when more than N warnings are reported",
    )
    parser.add_argument(
        "--today",
        type=_iso_date,
        default=None,
        metavar="YYYY-MM-DD",
        help="reference date for review-expiry checks (default: today)",
    )
    parser.add_argument(
        "--list-rules", action="store_true", help="list the built-in rules and exit"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _print_rules() -> None:
    """Write the built-in rule table to standard output."""
    width = max(len(rule.id) for rule in RULES)
    for rule in RULES:
        print(f"{rule.id:<{width}}  {rule.severity.value:<7}  {rule.summary}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the linter.

    Args:
        argv: Arguments without the program name. Defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code described in the module docstring.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_rules:
        _print_rules()
        return EXIT_OK

    if not args.manifests:
        parser.print_usage(sys.stderr)
        print(f"{parser.prog}: error: at least one MANIFEST is required", file=sys.stderr)
        return EXIT_USAGE

    try:
        policy = load_policy(args.policy) if args.policy is not None else Policy()
    except PolicyError as exc:
        print(f"{parser.prog}: error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.strict:
        policy = replace(policy, strict=True)

    status = EXIT_OK
    reports: list[Report] = []
    for manifest in args.manifests:
        try:
            card = load_manifest(manifest)
        except ManifestError as exc:
            print(f"{parser.prog}: error: {exc}", file=sys.stderr)
            status = EXIT_USAGE
            continue
        report = lint(card, policy, today=args.today)
        reports.append(report)
        sys.stdout.write(format_report(report, args.format))
        status = max(status, exit_code(report, max_warnings=args.max_warnings))

    if len(reports) > 1 and args.format == "text":
        errors = sum(len(report.errors) for report in reports)
        warnings = sum(len(report.warnings) for report in reports)
        sys.stdout.write(
            f"\n{len(reports)} manifests checked: {errors} error(s), {warnings} warning(s)\n"
        )
    return status
