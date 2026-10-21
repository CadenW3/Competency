"""Entry point for ``python -m modelcard_lint``."""

from __future__ import annotations

import sys

from modelcard_lint.cli import main

if __name__ == "__main__":
    sys.exit(main())
