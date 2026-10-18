# modelcard-lint

[![ci](https://github.com/CadenW3/Competency/actions/workflows/ci.yml/badge.svg)](https://github.com/CadenW3/Competency/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A zero-dependency linter that turns an ML model card into a **CI gate**. Point it
at a JSON model-card manifest; it reports every field that is missing, mistyped
or quietly out of date, and exits non-zero so a broken card cannot be shipped.

This repository is the deliverable for the *Growing a Competency* assignment
(competency: GitHub workflow, code quality and professional engineering
practices). The learning log lives in [`docs/competency-log.md`](docs/competency-log.md).

## Why

A model you cannot describe is a model you cannot audit. Model cards are the
standard answer to that problem, but a card that lives outside CI rots the first
time somebody renames a field, forgets the license, or leaves the review date in
the past. `modelcard-lint` makes the card part of the build: 11 rules, stable
rule ids, one exit code, no runtime dependencies to audit.

## Quick start

```bash
python -m pip install -e ".[dev]"
modelcard-lint examples/good-card.json
```

Clean card:

```console
$ modelcard-lint examples/good-card.json
examples/good-card.json: no findings
$ echo $?
0
```

A card with problems (the repository's `examples/bad-card.json`):

```console
$ modelcard-lint examples/bad-card.json --policy examples/policy.json
examples/bad-card.json: 5 errors, 6 warnings
  warning MCL007  evaluation.metrics: required metric 'accuracy' is not reported
  warning MCL007  evaluation.metrics: required metric 'macro_f1' is not reported
  warning MCL004  license: 'PatentPending-1.0' is not a recognised license id; add it to the policy if intentional
  warning MCL011  limitations[0]: limitation entry is shorter than 10 characters
  warning MCL006  owner.contact: 'risk-team' is not an email address
  error   MCL008  review.due: model card review was due 2025-01-01 and is overdue
  error   MCL002  schema_version: expected string, got float
  error   MCL005  training_data.deidentification: contains_pii is true, so the de-identification process must be described
  warning MCL010  training_data.source: 'internal share drive' is neither a URL nor an 'org/dataset' identifier
  error   MCL009  traning_data_version: unknown top-level field 'traning_data_version' (typo, or add it to the policy)
  error   MCL003  version: 'v3' is not a semantic version (expected MAJOR.MINOR.PATCH)
$ echo $?
1
```

Findings are sorted by manifest path, so the same input always produces the same
output -- which is what makes the `json` and `github` formats safe to diff.

## Usage

```
modelcard-lint MANIFEST [MANIFEST ...] [options]

  --policy PATH        JSON policy file (default: built-in policy)
  --format FORMAT      text | json | github          (default: text)
  --strict             treat warnings as errors
  --max-warnings N     fail when more than N warnings are reported
  --today YYYY-MM-DD   reference date for review-expiry checks
  --list-rules         print the rule table and exit
  --version            print the version and exit
```

The `github` format emits [workflow commands](https://docs.github.com/actions/using-workflows/workflow-commands-for-github-actions),
so findings show up as annotations on the pull-request diff instead of as log
noise nobody scrolls to.

### Exit code contract

| Code | Meaning |
| ---- | ------- |
| `0` | No blocking findings. |
| `1` | At least one error, or more warnings than `--max-warnings` allows, or any warning under `--strict`. |
| `2` | Usage error: unreadable manifest, invalid policy, bad arguments. |

The contract is fixed and tested (`tests/test_engine.py`); see
[ADR 0002](docs/adr/0002-severity-and-exit-code-contract.md) for the reasoning.

## Rules

Eleven rules, stable ids, severity per rule. Full reference: [`docs/rules.md`](docs/rules.md).

| Id | Default severity | What it checks |
| -- | ---------------- | -------------- |
| MCL001 | error | required metadata is present and non-empty |
| MCL002 | error | fields match their declared JSON type |
| MCL003 | error | version is semantic (MAJOR.MINOR.PATCH) |
| MCL004 | warning | license is a recognised identifier |
| MCL005 | error | personal data has a documented de-identification step |
| MCL006 | warning | owner contact is an email address |
| MCL007 | warning | policy-required metrics are reported |
| MCL008 | error | review date is valid and not overdue |
| MCL009 | warning | no unknown top-level fields |
| MCL010 | warning | training data provenance is resolvable |
| MCL011 | warning | limitations entries are actionable |

## Policy

A policy is JSON, so the tool needs no YAML parser and no dependencies:

```json
{
  "required_metrics": ["accuracy", "macro_f1"],
  "known_licenses": ["apache-2.0", "mit", "proprietary"],
  "severity_overrides": { "MCL009": "error" },
  "strict": false
}
```

Unknown policy keys are a hard error: a typo in a CI config must not silently
disable a check.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest              # tests + coverage gate (95%)
ruff check . && ruff format --check .
mypy                          # strict, src only
```

Every contribution goes through a pull request, conventional commit messages and
a green `ci` run. The workflow, branch naming and review checklist are in
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Repository layout

```
src/modelcard_lint/   types -> manifest -> policy -> rules -> engine -> report -> cli
tests/                unit, CLI and documentation-sync tests
examples/             a clean card, a broken card, and a policy
docs/                 architecture, rule reference, ADRs, competency log
tools/                commit_lint.py (conventional-commit hook)
```

## Current release

0.2.0 -- see [`CHANGELOG.md`](CHANGELOG.md) and the
[releases page](https://github.com/CadenW3/Competency/releases).

## License

MIT -- see [`LICENSE`](LICENSE).
