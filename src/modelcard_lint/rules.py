"""The built-in rule set.

Every rule is a frozen :class:`Rule` record pairing a stable id with a pure
check function. Checks are pure in the strong sense: they take a manifest, the
policy and a reference date, and return findings -- they never read the wall
clock, the environment or the filesystem. That is what lets the whole rule set
be unit-tested without mocks, and what makes CI output reproducible.

Adding a rule means appending one :class:`Rule` to :data:`RULES`; the engine,
the reporters and ``--list-rules`` pick it up automatically.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Any

from modelcard_lint.manifest import MISSING, ModelCard
from modelcard_lint.policy import Policy
from modelcard_lint.types import Finding, Severity

RuleCheck = Callable[[ModelCard, Policy, date], Iterable[Finding]]
"""Signature every rule check must implement."""

_SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
_SOURCE_REFERENCE = re.compile(r"^(?:[a-z][a-z0-9+.\-]*://\S+|[A-Za-z0-9_.\-]+/[\w.\-]+)$")
_MIN_LIMITATION_CHARS = 10

TYPE_CONTRACT: tuple[tuple[str, str], ...] = (
    ("schema_version", "string"),
    ("name", "string"),
    ("version", "string"),
    ("license", "string"),
    ("description", "string"),
    ("owner", "object"),
    ("intended_use", "string"),
    ("out_of_scope_use", "array"),
    ("limitations", "array"),
    ("training_data", "object"),
    ("evaluation", "object"),
    ("review", "object"),
)
"""Dotted path to expected JSON kind, enforced by MCL002."""

_JSON_KINDS: Mapping[str, tuple[type[Any], ...]] = MappingProxyType(
    {
        "string": (str,),
        "object": (dict,),
        "array": (list,),
        "boolean": (bool,),
        "number": (int, float),
    }
)


@dataclass(frozen=True, slots=True)
class Rule:
    """One declarative rule in the built-in set.

    Attributes:
        id: Stable identifier; never renumbered once released.
        summary: One-line description used by ``--list-rules`` and the docs.
        severity: Default severity, overridable per policy.
        check: Pure function that reports violations.
    """

    id: str
    summary: str
    severity: Severity
    check: RuleCheck


def _is_blank(value: Any) -> bool:
    """Return whether ``value`` counts as an empty value for MCL001.

    Args:
        value: Candidate value from the manifest.

    Returns:
        ``True`` for missing, ``None``, or empty string/list/dict values.
    """
    if value is MISSING or value is None:
        return True
    if isinstance(value, (str, list, dict, tuple)):
        return not value
    return False


def required_metadata(card: ModelCard, policy: Policy, _today: date) -> Iterable[Finding]:
    """MCL001: every policy-required field must be present and non-empty.

    Args:
        card: Manifest being linted.
        policy: Policy supplying the required field list.
        _today: Reference date (unused).

    Yields:
        One finding per missing or empty required field.
    """
    for field_name in policy.required_fields:
        if _is_blank(card.get(field_name)):
            yield Finding(
                path=field_name,
                rule_id="MCL001",
                severity=Severity.ERROR,
                message=f"required field '{field_name}' is missing or empty",
            )


def type_contract(card: ModelCard, _policy: Policy, _today: date) -> Iterable[Finding]:
    """MCL002: present fields must have the JSON kind the schema expects.

    Args:
        card: Manifest being linted.
        _policy: Policy (unused).
        _today: Reference date (unused).

    Yields:
        One finding per field whose value has the wrong JSON kind.
    """
    for field_name, kind in TYPE_CONTRACT:
        value = card.get(field_name)
        if value is MISSING or value is None:
            continue
        expected = _JSON_KINDS[kind]
        if isinstance(value, bool) and kind != "boolean":
            actual = "boolean"
        elif isinstance(value, expected):
            continue
        else:
            actual = type(value).__name__
        yield Finding(
            path=field_name,
            rule_id="MCL002",
            severity=Severity.ERROR,
            message=f"expected {kind}, got {actual}",
        )


def semantic_version(card: ModelCard, _policy: Policy, _today: date) -> Iterable[Finding]:
    """MCL003: ``version`` must be a SemVer 2.0.0 string.

    Args:
        card: Manifest being linted.
        _policy: Policy (unused).
        _today: Reference date (unused).

    Yields:
        A finding when ``version`` is present and not SemVer-shaped.
    """
    value = card.get("version")
    if isinstance(value, str) and value and not _SEMVER.match(value):
        yield Finding(
            path="version",
            rule_id="MCL003",
            severity=Severity.ERROR,
            message=f"'{value}' is not a semantic version (expected MAJOR.MINOR.PATCH)",
        )


def known_license(card: ModelCard, policy: Policy, _today: date) -> Iterable[Finding]:
    """MCL004: ``license`` should be a recognised SPDX-style identifier.

    Args:
        card: Manifest being linted.
        policy: Policy listing the accepted identifiers.
        _today: Reference date (unused).

    Yields:
        A finding when the license is unknown to the policy.
    """
    value = card.get("license")
    if isinstance(value, str) and value and value.lower() not in policy.known_licenses:
        yield Finding(
            path="license",
            rule_id="MCL004",
            severity=Severity.WARNING,
            message=(
                f"'{value}' is not a recognised license id; add it to the policy if intentional"
            ),
        )


def pii_deidentification(card: ModelCard, _policy: Policy, _today: date) -> Iterable[Finding]:
    """MCL005: personal data in the training set requires a documented process.

    Args:
        card: Manifest being linted.
        _policy: Policy (unused).
        _today: Reference date (unused).

    Yields:
        A finding when ``contains_pii`` is true but de-identification is silent.
    """
    if card.get("training_data.contains_pii") is not True:
        return
    deidentification = card.get("training_data.deidentification")
    if _is_blank(deidentification) or not isinstance(deidentification, str):
        yield Finding(
            path="training_data.deidentification",
            rule_id="MCL005",
            severity=Severity.ERROR,
            message="contains_pii is true, so the de-identification process must be described",
        )


def contact_format(card: ModelCard, _policy: Policy, _today: date) -> Iterable[Finding]:
    """MCL006: ``owner.contact`` must look like an email address.

    Args:
        card: Manifest being linted.
        _policy: Policy (unused).
        _today: Reference date (unused).

    Yields:
        A finding when the contact value is present but not email-shaped.
    """
    value = card.get("owner.contact")
    if isinstance(value, str) and value and not _EMAIL.match(value):
        yield Finding(
            path="owner.contact",
            rule_id="MCL006",
            severity=Severity.WARNING,
            message=f"'{value}' is not an email address",
        )


def required_metrics(card: ModelCard, policy: Policy, _today: date) -> Iterable[Finding]:
    """MCL007: every policy-required metric must be reported.

    Args:
        card: Manifest being linted.
        policy: Policy listing the mandatory metric names.
        _today: Reference date (unused).

    Yields:
        One finding per metric missing from ``evaluation.metrics``.
    """
    reported = card.get("evaluation.metrics")
    if not isinstance(reported, list):
        return
    normalised = {item.strip().lower() for item in reported if isinstance(item, str)}
    for metric in policy.required_metrics:
        if metric.lower() not in normalised:
            yield Finding(
                path="evaluation.metrics",
                rule_id="MCL007",
                severity=Severity.WARNING,
                message=f"required metric '{metric}' is not reported",
            )


def review_expiry(card: ModelCard, _policy: Policy, today: date) -> Iterable[Finding]:
    """MCL008: an overdue review date means the card's claims are stale.

    Args:
        card: Manifest being linted.
        _policy: Policy (unused).
        today: Reference date, injected by the engine.

    Yields:
        A finding when ``review.due`` is malformed or already in the past.
    """
    value = card.get("review.due")
    if not isinstance(value, str) or not value:
        return
    try:
        due = date.fromisoformat(value)
    except ValueError:
        yield Finding(
            path="review.due",
            rule_id="MCL008",
            severity=Severity.ERROR,
            message=f"'{value}' is not an ISO-8601 date (expected YYYY-MM-DD)",
        )
        return
    if due < today:
        yield Finding(
            path="review.due",
            rule_id="MCL008",
            severity=Severity.ERROR,
            message=f"model card review was due {due.isoformat()} and is overdue",
        )


def unknown_fields(card: ModelCard, policy: Policy, _today: date) -> Iterable[Finding]:
    """MCL009: unknown top-level keys are usually typos that silently do nothing.

    Args:
        card: Manifest being linted.
        policy: Policy listing the known top-level keys.
        _today: Reference date (unused).

    Yields:
        One finding per unrecognised top-level key.
    """
    for key in sorted(set(card.raw) - policy.known_fields):
        yield Finding(
            path=key,
            rule_id="MCL009",
            severity=Severity.WARNING,
            message=f"unknown top-level field '{key}' (typo, or add it to the policy)",
        )


def provenance_source(card: ModelCard, _policy: Policy, _today: date) -> Iterable[Finding]:
    """MCL010: ``training_data.source`` must be a resolvable URL or dataset id.

    Args:
        card: Manifest being linted.
        _policy: Policy (unused).
        _today: Reference date (unused).

    Yields:
        A finding when the source cannot be resolved by a reviewer.
    """
    value = card.get("training_data.source")
    if isinstance(value, str) and value and not _SOURCE_REFERENCE.match(value):
        yield Finding(
            path="training_data.source",
            rule_id="MCL010",
            severity=Severity.WARNING,
            message=f"'{value}' is neither a URL nor an 'org/dataset' identifier",
        )


def limitation_detail(card: ModelCard, _policy: Policy, _today: date) -> Iterable[Finding]:
    """MCL011: a limitation has to say something to be actionable.

    Args:
        card: Manifest being linted.
        _policy: Policy (unused).
        _today: Reference date (unused).

    Yields:
        One finding per limitation entry that is too short to inform a reader.
    """
    limitations = card.get("limitations")
    if not isinstance(limitations, list):
        return
    for index, entry in enumerate(limitations):
        if isinstance(entry, str) and len(entry.strip()) < _MIN_LIMITATION_CHARS:
            yield Finding(
                path=f"limitations[{index}]",
                rule_id="MCL011",
                severity=Severity.WARNING,
                message=f"limitation entry is shorter than {_MIN_LIMITATION_CHARS} characters",
            )


RULES: tuple[Rule, ...] = (
    Rule("MCL001", "required metadata is present and non-empty", Severity.ERROR, required_metadata),
    Rule("MCL002", "fields match their declared JSON type", Severity.ERROR, type_contract),
    Rule("MCL003", "version is semantic (MAJOR.MINOR.PATCH)", Severity.ERROR, semantic_version),
    Rule("MCL004", "license is a recognised identifier", Severity.WARNING, known_license),
    Rule(
        "MCL005",
        "personal data has a documented de-identification step",
        Severity.ERROR,
        pii_deidentification,
    ),
    Rule("MCL006", "owner contact is an email address", Severity.WARNING, contact_format),
    Rule("MCL007", "policy-required metrics are reported", Severity.WARNING, required_metrics),
    Rule("MCL008", "review date is valid and not overdue", Severity.ERROR, review_expiry),
    Rule("MCL009", "no unknown top-level fields", Severity.WARNING, unknown_fields),
    Rule("MCL010", "training data provenance is resolvable", Severity.WARNING, provenance_source),
    Rule("MCL011", "limitations entries are actionable", Severity.WARNING, limitation_detail),
)
"""The built-in rule set, in reporting order."""

RULES_BY_ID: Mapping[str, Rule] = MappingProxyType({rule.id: rule for rule in RULES})
"""Rule lookup by id, used by ``--list-rules`` and the documentation tests."""
