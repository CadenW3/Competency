"""Tests that keep metadata and documentation in lock-step with the code."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from modelcard_lint import __version__
from modelcard_lint.rules import RULES

ROOT = Path(__file__).resolve().parent.parent


def _pyproject() -> dict:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_version_matches_pyproject() -> None:
    assert _pyproject()["project"]["version"] == __version__


def test_version_is_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)


def test_rules_document_lists_every_rule() -> None:
    doc = (ROOT / "docs" / "rules.md").read_text(encoding="utf-8")
    for rule in RULES:
        assert rule.id in doc, f"{rule.id} is missing from docs/rules.md"
        assert rule.summary in doc, f"summary for {rule.id} is out of date in docs/rules.md"


def test_readme_mentions_exit_codes() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for token in ("exit code", "modelcard-lint", "0.2.0"):
        assert token.lower() in readme.lower() or token in readme


def test_changelog_has_version_section() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"[{__version__}]" in changelog


def test_expected_docs_exist() -> None:
    for relative in (
        "README.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "LICENSE",
        "docs/architecture.md",
        "docs/rules.md",
        "docs/adr/0001-zero-runtime-dependencies.md",
    ):
        assert (ROOT / relative).is_file(), f"{relative} is missing"
