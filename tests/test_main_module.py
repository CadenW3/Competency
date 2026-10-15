"""Test the ``python -m modelcard_lint`` entry point.

``__main__.py`` is trivial, but "trivial" is exactly the kind of module that
silently rots when the CLI is refactored, and it is the invocation the README
and the pre-commit hooks use.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_main_module_lints_a_clean_card(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["modelcard_lint", str(EXAMPLES / "good-card.json")])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("modelcard_lint", run_name="__main__")
    assert excinfo.value.code == 0
    assert "no findings" in capsys.readouterr().out


def test_main_module_propagates_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["modelcard_lint", str(EXAMPLES / "bad-card.json")])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("modelcard_lint", run_name="__main__")
    assert excinfo.value.code == 1
    assert "MCL003" in capsys.readouterr().out
