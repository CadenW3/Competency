"""Shared fixtures for the modelcard-lint test suite.

The reference fixture is ``examples/good-card.json`` itself rather than a copy,
so the examples shipped in the repository are guaranteed to be lint-clean: if
someone edits the example into an invalid state, the suite goes red.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable, Mapping
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from modelcard_lint.engine import lint
from modelcard_lint.manifest import MISSING, ModelCard
from modelcard_lint.policy import Policy
from modelcard_lint.types import Report

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
TODAY = date(2026, 1, 15)


def _load_example(name: str) -> dict[str, Any]:
    """Read one of the repository's example JSON documents."""
    raw: dict[str, Any] = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
    return raw


@pytest.fixture
def card_data() -> dict[str, Any]:
    """Return a mutable copy of the reference model card."""
    return copy.deepcopy(_load_example("good-card.json"))


@pytest.fixture
def make_card() -> Callable[..., ModelCard]:
    """Return a factory that wraps a raw mapping in a :class:`ModelCard`."""

    def factory(data: Mapping[str, Any], path: str = "card.json") -> ModelCard:
        return ModelCard(path=Path(path), raw=data)

    return factory


@pytest.fixture
def mutate() -> Callable[[dict[str, Any], str, Any], dict[str, Any]]:
    """Return a helper that sets or deletes a dotted path in a card mapping."""

    def apply(data: dict[str, Any], dotted: str, value: Any) -> dict[str, Any]:
        parts = dotted.split(".")
        node: dict[str, Any] = data
        for part in parts[:-1]:
            child = node.get(part)
            if not isinstance(child, dict):
                child = {}
                node[part] = child
            node = child
        if value is MISSING:
            node.pop(parts[-1], None)
        else:
            node[parts[-1]] = value
        return data

    return apply


@pytest.fixture
def lint_card() -> Callable[..., Report]:
    """Return a helper that lints a card with a pinned reference date."""

    def run(card: ModelCard, policy: Policy | None = None, today: date = TODAY) -> Report:
        return lint(card, policy, today=today)

    return run


@pytest.fixture
def policy() -> Policy:
    """Return the stock policy."""
    return Policy()
