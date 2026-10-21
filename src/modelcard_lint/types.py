"""Value types shared by every layer of the linter.

The package is built around three immutable records:

* :class:`Severity` -- an ordered verdict for a single finding.
* :class:`Finding` -- one rule violation, addressed by a stable rule id.
* :class:`Report` -- the ordered, immutable result of linting one manifest.

Keeping these in a dependency-free leaf module means ``rules``, ``engine`` and
``report`` can all import them without creating an import cycle.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class Severity(StrEnum):
    """How badly a rule violation breaks the model-card contract.

    Attributes:
        INFO: Context that never fails a run.
        WARNING: A smell that fails a run only under ``--strict`` or when
            ``--max-warnings`` is exceeded.
        ERROR: A violation that always fails a run.
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

    @property
    def rank(self) -> int:
        """Return the ordering weight used to compare severities."""
        return _SEVERITY_RANK[self]

    @classmethod
    def parse(cls, value: str) -> Severity:
        """Return the severity named by ``value``, ignoring case and padding.

        Args:
            value: Severity name such as ``"warning"``.

        Raises:
            ValueError: If ``value`` does not name a known severity.
        """
        try:
            return cls(value.strip().lower())
        except ValueError as exc:
            known = ", ".join(sorted(member.value for member in cls))
            msg = f"unknown severity {value!r}; expected one of: {known}"
            raise ValueError(msg) from exc


_SEVERITY_RANK: Mapping[Severity, int] = MappingProxyType(
    {Severity.INFO: 0, Severity.WARNING: 1, Severity.ERROR: 2}
)


@dataclass(frozen=True, slots=True)
class Finding:
    """One rule violation inside one manifest.

    Attributes:
        path: Dotted location in the manifest; ``""`` means the whole document.
        rule_id: Stable identifier such as ``MCL004``.
        severity: How badly this violation breaks the contract.
        message: Explanation written in the present tense, with no trailing period.
    """

    path: str
    rule_id: str
    severity: Severity
    message: str

    def __str__(self) -> str:
        """Render the finding as one stable, greppable line of text."""
        location = self.path or "<root>"
        return f"{location}: {self.rule_id} [{self.severity.value}] {self.message}"


def sort_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    """Return ``findings`` in a deterministic order.

    Ordering by ``(path, rule_id, message)`` keeps output byte-identical across
    runs, platforms and rule-registration order, which is what makes the JSON
    and GitHub-annotation formats safe to diff in CI.

    Args:
        findings: Findings in any order.

    Returns:
        A tuple sorted by location, then rule id, then message.
    """
    return tuple(
        sorted(findings, key=lambda finding: (finding.path, finding.rule_id, finding.message))
    )


@dataclass(frozen=True, slots=True)
class Report:
    """The complete result of linting one manifest.

    Attributes:
        source: The manifest path exactly as the user supplied it.
        findings: Findings already sorted by :func:`sort_findings`.
    """

    source: str
    findings: tuple[Finding, ...] = ()

    def of(self, severity: Severity) -> tuple[Finding, ...]:
        """Return every finding with exactly ``severity``.

        Args:
            severity: Severity to filter on.

        Returns:
            The matching findings, preserving report order.
        """
        return tuple(finding for finding in self.findings if finding.severity is severity)

    @property
    def errors(self) -> tuple[Finding, ...]:
        """Return the findings that always fail a run."""
        return self.of(Severity.ERROR)

    @property
    def warnings(self) -> tuple[Finding, ...]:
        """Return the findings that only fail a run under ``--strict``."""
        return self.of(Severity.WARNING)

    def counts(self) -> Mapping[Severity, int]:
        """Return the number of findings per severity, including zero counts."""
        tally = Counter(finding.severity for finding in self.findings)
        return MappingProxyType({severity: tally[severity] for severity in Severity})

    @property
    def worst(self) -> Severity | None:
        """Return the highest severity present, or ``None`` when the card is clean."""
        if not self.findings:
            return None
        return max((finding.severity for finding in self.findings), key=lambda found: found.rank)

    def summary(self) -> str:
        """Return a one-line, correctly pluralised count of the findings."""
        counts = self.counts()
        if not self.findings:
            return "no findings"
        parts = [
            f"{counts[severity]} {severity.value}{'' if counts[severity] == 1 else 's'}"
            for severity in (Severity.ERROR, Severity.WARNING, Severity.INFO)
            if counts[severity]
        ]
        return ", ".join(parts)
