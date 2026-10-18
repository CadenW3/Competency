# ADR 0003 -- Conventional Commits, short-lived branches, merge-only history

- **Status:** accepted
- **Date:** 2026-10-16
- **Deciders:** Caden Wate

## Context

The repository is judged as much on how changes arrive as on what the code does.
Three habits cause most of the damage in student and small-team repositories:

1. Commit messages that are a diary of keystrokes (`update`, `fix`, `more`), so
   history cannot be searched, reverted or turned into release notes.
2. Work landing directly on `main`, so nothing has a review boundary and
   nothing is easy to revert as a unit.
3. Merge noise (or worse, rebase-rewritten shared history) that makes the graph
   illegible.

## Decision

1. **Conventional Commits 1.0.0** for every message, enforced by a `commit-msg`
   hook (`tools/commit_lint.py`) rather than by good intentions.
   Types: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`,
   `revert`, `style`, `test`.
2. **Short-lived branches** named `<type>/<slug>` (`feat/mcl012-provenance`).
   Direct pushes to `main` are disallowed by branch protection.
3. **Pull requests are the only way into `main`**, merged with a merge commit so
   the feature's commits and the review decision both survive in history.
4. **Tags carry releases** (`vMAJOR.MINOR.PATCH`), and the release workflow
   publishes a GitHub Release with built artifacts.
5. **Squash only for messy WIP branches**, and only when the resulting message
   still satisfies rule 1.

The validator is deliberately narrow: it checks the parts of the convention that
are objectively verifiable (type, scope shape, subject case, length, blank-line
separator, breaking-change footer) and nothing about taste.

## Consequences

**Good**

- `git log --oneline` is a readable changelog, and `CHANGELOG.md` is generated
  from the same vocabulary rather than from memory.
- Every change has a review boundary: a branch, a PR, a CI run, a merge commit.
- Reverting a feature is one `git revert -m 1 <merge-sha>`.
- The convention is machine-checked, so it does not depend on reviewer energy.

**Bad**

- Two extra keystrokes per commit, and one more thing to install
  (`pre-commit install --hook-type commit-msg`).
- Merge commits make the graph wider than a linear rebase history. Accepted:
  the review boundary is worth more than a straight line.
- A solo project pays the PR overhead with no second reviewer. Accepted: the PR
  is where the CI evidence and the reasoning for a change get attached.

## Alternatives considered

| Option | Rejected because |
| ------ | ---------------- |
| Free-form commit messages | History stops being queryable; `feat:`/`fix:` also drive release notes. |
| Commitlint (Node) | Adds a JavaScript toolchain to a Python repository for one regex table. |
| Rebase-merge only | Loses the "this arrived as one reviewed unit" signal. |
| Squash-merge everything | Throws away intermediate reasoning; fine for WIP, wrong as a default. |
| Enforce by convention only | The whole point of a hook is that nobody has to remember. |
