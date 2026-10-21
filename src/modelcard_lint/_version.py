"""Single source of truth for the released version number.

``pyproject.toml`` and this module are kept in lock-step by
``tests/test_version.py``, so a release cannot ship a stale version string.
"""

__version__ = "0.2.0"
