## What and why

<!-- One paragraph: the problem this pull request solves, not a restatement of the diff. -->

## Type of change

<!-- Match the commit type. Breaking changes need a BREAKING CHANGE: footer. -->

- [ ] `feat` -- new rule, flag or output format
- [ ] `fix` -- wrong result or crash
- [ ] `docs` -- documentation only
- [ ] `test` -- test-only change
- [ ] `refactor` -- behaviour-preserving restructuring
- [ ] `ci` / `build` -- tooling or packaging
- [ ] breaking change

## How it was verified

<!-- Commands you ran, plus anything a reviewer should try by hand. -->

```console
$ python -m pytest
$ ruff check . && ruff format --check . && mypy
```

## Checklist

- [ ] `ci` is green on every supported Python version.
- [ ] New behaviour has a test that fails without this change.
- [ ] Coverage is at or above the 95% branch gate.
- [ ] Public functions are annotated and documented (Google docstrings).
- [ ] `docs/rules.md` updated if a rule was added or changed.
- [ ] `CHANGELOG.md` has an entry under the right section.
- [ ] No new runtime dependency (see ADR 0001).
- [ ] Rule ids, exit codes or output formats unchanged -- or the change is
      explicitly flagged as breaking above.

## Related issues

<!-- Closes #, refs # -->
