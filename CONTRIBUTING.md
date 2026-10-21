# Contributing

Thanks for looking. This document is the contract for changes: follow it and a
pull request gets merged without a round of process feedback.

## Set up

```bash
git clone https://github.com/CadenW3/Competency.git
cd Competency
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
python -m pip install -e ".[dev]"
python -m pip install pre-commit
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

The second `--hook-type` matters: without it the Conventional Commits check never
runs, because git only invokes `commit-msg` hooks that exist.

## The five gates

| Gate | Command | Enforced by |
| ---- | ------- | ----------- |
| Lint | `ruff check .` | pre-commit + CI |
| Format | `ruff format --check .` | pre-commit + CI |
| Types | `mypy` (strict, `src` only) | pre-commit + CI |
| Tests | `python -m pytest` | CI (with a 95% branch-coverage gate) |
| Commit message | `python tools/commit_lint.py <file>` | `commit-msg` hook + CI |

Run all of them at once before pushing:

```bash
python -m pytest && ruff check . && ruff format --check . && mypy
```

`pre-commit run --all-files` runs the same tools over the whole tree and is what
CI does on a fresh checkout.

## Branches

`<type>/<short-slug>`, using the same types as commits:

```
feat/mcl012-provenance-rule
fix/mcl008-missing-review-block
docs/adr-0004-coverage-policy
ci/cache-pip-downloads
```

`main` is protected: no direct pushes, no force pushes, and the single `ci gate` check must pass on an up-to-date branch before a pull request can merge. Every
change arrives as a merge commit so the review boundary survives in history
(see [ADR 0003](docs/adr/0003-conventional-commits-and-merge-only-prs.md)).

## Commit messages

[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/),
checked by `tools/commit_lint.py`:

```
<type>(<optional scope>): <subject>

<optional body, wrapped at 72 columns>

<optional footer>
```

Rules the hook enforces:

- a type from the allowed list;
- an optional scope of lowercase letters, digits, `.`, `_`, `/`, `-`;
- a header of at most 72 characters, a subject of at most 50;
- a lowercase subject with no trailing period;
- a blank line between the header and the body;
- a `BREAKING CHANGE:` footer whenever the header carries `!`.

| Type | Use for |
| ---- | ------- |
| `feat` | a new rule, flag or format |
| `fix` | a wrong result or a crash |
| `docs` | README, docs, docstrings only |
| `test` | test-only changes |
| `refactor` | behaviour-preserving restructuring |
| `perf` | faster with the same behaviour |
| `build` | packaging, `pyproject.toml`, dependencies |
| `ci` | workflows, hooks, templates |
| `chore` | housekeeping that fits nowhere else |
| `style` | formatting only |
| `revert` | reverting an earlier commit |

## Adding a rule

1. Add a pure check function in `src/modelcard_lint/rules.py`.
2. Register it in `RULES` with the next free `MCLxxx` id.
3. Document it in `docs/rules.md` -- `tests/test_docs.py` fails if you skip this.
4. Test it in `tests/test_rules.py` by mutating exactly one field of the
   reference card from `examples/good-card.json`.
5. Add a `CHANGELOG.md` entry under `### Added`.

Rule ids are never renumbered or reused; a policy elsewhere may override one.

## Definition of done

A pull request is ready when all of these are true:

- [ ] `ci` is green on every supported Python version.
- [ ] New behaviour has a test that fails without the change.
- [ ] Coverage is at or above 95% (branch coverage) and new branches are covered.
- [ ] Public functions have type annotations and a Google-style docstring.
- [ ] `docs/` and `CHANGELOG.md` reflect the change.
- [ ] No new runtime dependency (see [ADR 0001](docs/adr/0001-zero-runtime-dependencies.md)).
- [ ] The PR description says *why*, not just *what*.

## Review checklist

Reviewers check, in order:

1. Does the change do what the description claims, and nothing else?
2. Are the failure modes defined (exit code, error message, empty input)?
3. Is the test the kind that would catch a regression, not just execute lines?
4. Does any rule, id or output format change in a way that breaks downstream
   policies? If so, is it called out as a breaking change?

## Code style

- `ruff` for lint and format, configured in `pyproject.toml` (100 columns).
- `mypy --strict` on `src`; tests and tools are exempt from strictness but are
  still annotated.
- Prefer pure functions and immutable dataclasses; keep I/O at the edges.
- Docstrings: Google convention, present tense, one-line summary first.

## Reporting bugs and security issues

Ordinary bugs: open an issue with the template. Security issues: **do not** open
an issue -- follow [`SECURITY.md`](SECURITY.md).
