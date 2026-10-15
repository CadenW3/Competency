"""modelcard-lint: a zero-dependency CI gate for ML model-card manifests.

The public API is intentionally tiny -- three functions and their result types:

>>> from modelcard_lint import lint, load_manifest
>>> report = lint(load_manifest("examples/good-card.json"))  # doctest: +SKIP
>>> report.summary()  # doctest: +SKIP
'no findings'

See :mod:`modelcard_lint.cli` for the command-line entry point and
``docs/architecture.md`` for the layering rules.
"""

from __future__ import annotations

from modelcard_lint._version import __version__
from modelcard_lint.engine import EXIT_OK, EXIT_USAGE, EXIT_VIOLATIONS, exit_code, lint
from modelcard_lint.manifest import ManifestError, ModelCard, load_manifest
from modelcard_lint.policy import Policy, PolicyError, load_policy
from modelcard_lint.report import format_json, format_report, format_text
from modelcard_lint.rules import RULES, Rule
from modelcard_lint.types import Finding, Report, Severity

__all__ = [
    "EXIT_OK",
    "EXIT_USAGE",
    "EXIT_VIOLATIONS",
    "RULES",
    "Finding",
    "ManifestError",
    "ModelCard",
    "Policy",
    "PolicyError",
    "Report",
    "Rule",
    "Severity",
    "__version__",
    "exit_code",
    "format_json",
    "format_report",
    "format_text",
    "lint",
    "load_manifest",
    "load_policy",
]
