# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Commit types map onto sections: `feat` -> Added, `fix` -> Fixed, `perf` -> Changed,
`refactor`/`docs` -> Changed, `ci`/`build`/`chore` -> omitted unless user-visible.

## [Unreleased]

Nothing yet.

## [0.2.0] - 2026-10-19

First tagged release. The work below arrived in three reviewed pull requests:
the core pipeline, the professional-tooling layer, and the documentation set.

### Added

- `modelcard-lint` CLI with the documented exit-code contract (`0` run clean,
  `1` blocking findings, `2` usage error).
- Eleven rules (`MCL001`-`MCL011`) covering required metadata, JSON types,
  semantic versions, license identifiers, PII de-identification, contact format,
  required metrics, review expiry, unknown fields, provenance and limitation
  quality. Reference: [`docs/rules.md`](docs/rules.md).
- Three output formats: `text` for humans, `json` for machines, and `github` for
  Actions workflow commands, so findings annotate the pull-request diff.
- `--strict` (warnings block), `--max-warnings N` (warning budget) and
  `--today YYYY-MM-DD` (pin the reference date for reproducible runs).
- JSON policy documents with `required_fields`, `known_fields`, `known_licenses`,
  `required_metrics`, `severity_overrides` and `strict`; unknown keys are a hard
  error so a typo cannot silently disable a rule.
- Continuous integration: `ruff` lint and format, `mypy --strict`, and a pytest
  matrix over Linux, Windows and macOS with a 95% branch-coverage gate, plus a
  single `ci gate` job for branch protection.
- Pre-commit hooks including a `commit-msg` stage that enforces Conventional
  Commits via `tools/commit_lint.py`.
- Tagged release workflow that builds the sdist and wheel, asserts the tag
  matches the package version, asserts the wheel has no runtime dependencies, and
  publishes a GitHub Release with the artifacts.
- Repository furniture: PR template with a definition-of-done checklist, issue
  forms, `CODEOWNERS`, Dependabot groups, code of conduct, security policy and
  contribution guide.
- Architecture Decision Records 0001-0003, an architecture overview, a rule
  reference and the competency learning log.

### Changed

- Findings are sorted deterministically by `(path, rule_id, message)`, making all
  three output formats byte-identical between runs.
- Rule checks take an injected reference date instead of reading the wall clock.
- `Policy` is an immutable dataclass whose `severity_overrides` are validated at
  load time.

### Fixed

- `MCL008` no longer fires for a card that omits the `review` block entirely.
- `MCL002` no longer reports `true`/`false` as `number`.

### Security

- The linter never deserialises, imports, executes or fetches anything: JSON
  parsing is the only input path and there are no runtime dependencies. See
  [ADR 0001](docs/adr/0001-zero-runtime-dependencies.md) and
  [`SECURITY.md`](SECURITY.md).

Earlier commits in this repository were unbranched milestones and were never
tagged; `0.2.0` is the first released version.
