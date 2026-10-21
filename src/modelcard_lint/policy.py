"""Project policy: the per-repository knobs for the built-in rule set.

A policy is the difference between "a linter with opinions" and "a linter that
enforces *this* organisation's model-card contract". It travels as JSON so that
no YAML parser (and therefore no runtime dependency) is required, and it is
validated strictly so that a typo in a CI config fails loudly instead of
silently disabling a rule.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from modelcard_lint.types import Severity

DEFAULT_REQUIRED_FIELDS: tuple[str, ...] = (
    "schema_version",
    "name",
    "version",
    "license",
    "owner.name",
    "owner.contact",
    "intended_use",
    "limitations",
    "training_data.source",
    "evaluation.metrics",
)
"""Dotted paths every model card must populate."""

DEFAULT_KNOWN_FIELDS: frozenset[str] = frozenset(
    {
        "schema_version",
        "name",
        "version",
        "description",
        "license",
        "owner",
        "intended_use",
        "out_of_scope_use",
        "limitations",
        "training_data",
        "evaluation",
        "review",
    }
)
"""Top-level keys MCL009 accepts without complaint."""

DEFAULT_KNOWN_LICENSES: frozenset[str] = frozenset(
    {
        "apache-2.0",
        "bsd-2-clause",
        "bsd-3-clause",
        "cc-by-4.0",
        "cc-by-sa-4.0",
        "creativeml-openrail-m",
        "gpl-3.0-only",
        "lgpl-3.0-only",
        "mit",
        "mpl-2.0",
        "proprietary",
        "unlicensed",
    }
)
"""SPDX-style license identifiers MCL004 recognises (compared lower-cased)."""

_POLICY_KEYS = frozenset(
    {
        "required_fields",
        "known_fields",
        "known_licenses",
        "required_metrics",
        "severity_overrides",
        "strict",
    }
)


class PolicyError(ValueError):
    """Raised when a policy file is unreadable or fails its own schema checks."""


def _string_tuple(value: Any, key: str, where: str) -> tuple[str, ...]:
    """Validate that ``value`` is a list of strings and return it as a tuple.

    Args:
        value: Candidate value from the policy document.
        key: Policy key being validated, used in error messages.
        where: Human-readable origin of the policy, used in error messages.

    Returns:
        The validated values.

    Raises:
        PolicyError: If the value is not a list of non-empty strings.
    """
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise PolicyError(f"{where}: '{key}' must be a list of non-empty strings")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class Policy:
    """Validation knobs for one organisation or repository.

    Attributes:
        required_fields: Dotted paths that must be present and non-empty.
        known_fields: Top-level keys that do not trigger MCL009.
        known_licenses: Lower-cased license ids that do not trigger MCL004.
        required_metrics: Metric names ``evaluation.metrics`` must include.
        severity_overrides: Per-rule severity replacements, keyed by rule id.
        strict: When ``True``, warnings are reported as errors.
    """

    required_fields: tuple[str, ...] = DEFAULT_REQUIRED_FIELDS
    known_fields: frozenset[str] = DEFAULT_KNOWN_FIELDS
    known_licenses: frozenset[str] = DEFAULT_KNOWN_LICENSES
    required_metrics: tuple[str, ...] = ()
    severity_overrides: Mapping[str, Severity] = field(default_factory=lambda: MappingProxyType({}))
    strict: bool = False

    def severity_for(self, rule_id: str, default: Severity) -> Severity:
        """Return the configured severity for ``rule_id``.

        Args:
            rule_id: Stable rule identifier such as ``"MCL004"``.
            default: Severity the rule declares for itself.

        Returns:
            The override when configured, otherwise ``default``.
        """
        return self.severity_overrides.get(rule_id, default)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Policy:
        """Build a validated policy from a parsed policy document.

        Args:
            data: Parsed policy object.

        Returns:
            The validated policy.

        Raises:
            PolicyError: If a key is unknown or a value has the wrong type.
        """
        unknown = sorted(set(data) - _POLICY_KEYS)
        if unknown:
            raise PolicyError(f"policy: unknown key(s) {', '.join(unknown)}")

        overrides: dict[str, Severity] = {}
        raw_overrides = data.get("severity_overrides", {})
        if not isinstance(raw_overrides, Mapping):
            raise PolicyError("policy: 'severity_overrides' must be an object")
        for rule_id, raw_severity in raw_overrides.items():
            if not isinstance(raw_severity, str):
                raise PolicyError(f"policy: severity for {rule_id!r} must be a string")
            try:
                overrides[str(rule_id)] = Severity.parse(raw_severity)
            except ValueError as exc:
                raise PolicyError(f"policy: {exc}") from exc

        strict = data.get("strict", False)
        if not isinstance(strict, bool):
            raise PolicyError("policy: 'strict' must be a boolean")

        default = cls()
        return cls(
            required_fields=_string_tuple(
                data.get("required_fields", list(default.required_fields)),
                "required_fields",
                "policy",
            ),
            known_fields=frozenset(
                _string_tuple(
                    data.get("known_fields", sorted(default.known_fields)), "known_fields", "policy"
                )
            ),
            known_licenses=frozenset(
                _string_tuple(
                    data.get("known_licenses", sorted(default.known_licenses)),
                    "known_licenses",
                    "policy",
                )
            ),
            required_metrics=_string_tuple(
                data.get("required_metrics", []), "required_metrics", "policy"
            ),
            severity_overrides=MappingProxyType(overrides),
            strict=strict,
        )


def load_policy(path: str | Path) -> Policy:
    """Read and validate a policy document.

    Args:
        path: Path to a JSON policy file.

    Returns:
        The validated policy.

    Raises:
        PolicyError: If the file is missing, unreadable, not valid JSON, not a
            JSON object, or fails :meth:`Policy.from_mapping`.
    """
    policy_path = Path(path)
    try:
        text = policy_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PolicyError(f"{policy_path}: policy not found") from exc
    except OSError as exc:
        raise PolicyError(f"{policy_path}: cannot read policy ({exc.strerror})") from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PolicyError(
            f"{policy_path}:{exc.lineno}:{exc.colno}: invalid JSON ({exc.msg})"
        ) from exc

    if not isinstance(data, dict):
        raise PolicyError(f"{policy_path}: policy must be a JSON object")
    return Policy.from_mapping(data)
