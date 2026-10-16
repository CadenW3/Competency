"""Verify that the repository's deliberately broken example still fails.

A linter whose "bad" example passes is not testing anything, and a README whose
example output is stale is worse than no README. This hook asserts the documented
exit code directly through the library, so it needs no subprocess and no shell.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_EXIT_CODE = 1


def main() -> int:
    """Check `examples/bad-card.json` fails with the documented exit code.

    Returns:
        0 when the example behaves as documented, 1 otherwise.
    """
    sys.path.insert(0, str(ROOT / "src"))
    from modelcard_lint.engine import EXIT_VIOLATIONS, exit_code, lint
    from modelcard_lint.manifest import load_manifest
    from modelcard_lint.policy import load_policy

    card = load_manifest(ROOT / "examples" / "bad-card.json")
    policy = load_policy(ROOT / "examples" / "policy.json")
    report = lint(card, policy)
    code = exit_code(report)

    if code != EXPECTED_EXIT_CODE:
        print(
            f"assert_example_fails: bad-card.json exited {code}, expected "
            f"{EXPECTED_EXIT_CODE} (EXIT_VIOLATIONS={EXIT_VIOLATIONS})",
            file=sys.stderr,
        )
        return 1

    print(f"assert_example_fails: bad-card.json still fails as documented ({report.summary()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
