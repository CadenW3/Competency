# Competency log

Working log for the *Growing a Competency* assignment.
Competency: **GitHub workflow, code quality and professional engineering practices.**
Target: 5-10 hours. Recorded hours: **8.5**.

I kept this log while I worked rather than reconstructing it afterwards, because
the honest version of "how long did this take" is the interesting part of the
assignment.

## Starting point

Before this competency I could do exactly four git commands: `add`, `commit`,
`push`, and `clone`. My previous repositories had one branch (`main`), commits
called `update` and `stuff`, no tests, no README, no license, and no CI. If two
things broke at once I could not tell which commit caused which. "Code quality"
to me meant "it runs". I had never opened a pull request, never used a linter,
never written a type hint on purpose, and never tagged a release.

## Hour-by-hour

| # | Hours | What I actually did | Source |
| - | ----- | ------------------- | ------ |
| 1 | 1.0 | GitHub Skills *Introduction to GitHub* and *Review pull requests* -- branching, opening a PR, requesting and applying a review, resolving a conversation | GitHub Skills |
| 2 | 1.0 | Read the Pro Git "Git Branching" and "Distributed Git" chapters for the mental model behind `HEAD`, fast-forwards and merge commits | Pro Git (Chacon & Straub) |
| 3 | 1.0 | GitHub Docs: branch protection rules, protected branches, `GITHUB_TOKEN` permissions, workflow syntax, cache action | GitHub Docs |
| 4 | 1.0 | Conventional Commits 1.0.0 spec and Keep a Changelog / Semantic Versioning -- decided on types and on how a type maps to a changelog section | conventionalcommits.org, keepachangelog.com, semver.org |
| 5 | 1.5 | Ruff docs + configuration reference; wrote the `pyproject.toml` lint/format/type/test configuration and fixed every finding in the package | docs.astral.sh/ruff |
| 6 | 1.0 | mypy in strict mode; read the "Getting started" and "Common issues" pages; added annotations until strict mode passed | mypy.readthedocs.io |
| 7 | 1.0 | pytest fixtures, parametrisation, coverage branch reporting, `--cov-fail-under`; wrote the twelve test modules | pytest + coverage docs |
| 8 | 1.0 | pre-commit framework, writing a `local` hook, `commit-msg` stage; wrote `tools/commit_lint.py` and its tests | pre-commit.com |
| 9 | 0.5 | GitHub Actions: matrix builds, `concurrency`, least-privilege `permissions`, `gh release create` on tag | GitHub Docs, Actions marketplace |
| 10 | 0.5 | ADR practice and commit-message hygiene; wrote ADRs 0001-0003 | Michael Nygard, "Documenting architecture decisions" |

## What changed in how I work

1. **Work is a branch, not an edit.** Every change starts on `<type>/<slug>`,
   goes through a PR, and lands as a merge commit.
2. **The gate is automated, not remembered.** Lint, format, types, tests,
   coverage and the commit message are all checked by machines. `pre-commit`
   runs them locally; CI runs them again on a clean checkout.
3. **Commit messages are data.** `feat:`/`fix:`/`docs:` classify the change, so
   the changelog and the release notes can be written from history instead of
   memory.
4. **Decisions get written down before the code.** Three ADRs stopped me from
   re-litigating "why zero dependencies" in every later commit.
5. **Public behaviour is a contract.** The exit codes, rule ids and output
   formats are documented and tested, because other people's CI depends on them.

## Evidence collected

- Repository: <https://github.com/CadenW3/Competency>
- 11 rules, 12 test modules, 155 tests, coverage gate at 95% (branch) with the
  actual figure at 99.8%.
- Three reviewed pull requests, each with a green `ci` run on its head commit.
- Release `v0.2.0`, cut from a tag by the release workflow with the sdist and
  wheel attached.
- Pre-commit rejecting a badly formed commit message, in the screenshot set
  attached to the assignment PDF.
