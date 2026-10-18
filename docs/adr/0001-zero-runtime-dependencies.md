# ADR 0001 -- Zero runtime dependencies

- **Status:** accepted
- **Date:** 2026-10-14
- **Deciders:** Caden Wate

## Context

`modelcard-lint` is meant to be dropped into somebody else's CI pipeline as a
gate. Every dependency it declares becomes:

- a supply-chain surface in a pipeline that already worries about supply chains;
- a conflict risk with the project's own pinned versions;
- a reason a security review has to re-approve the tool.

The obvious conveniences on offer were a YAML parser (for policies), a schema
library (for the model-card contract) and a CLI framework (for the interface).

## Decision

Ship with **zero runtime dependencies**. Specifically:

- Policies are JSON, not YAML. JSON is in the standard library and, unlike YAML,
  cannot execute anything while being parsed.
- The schema lives in a hand-written `TYPE_CONTRACT` table plus a dozen small
  rule functions. The contract is ~30 lines of data; a schema library would be
  more code, more indirection and a new failure mode.
- The CLI is `argparse`. Its help text, exit codes and error messages are
  adequate, and it is the one interface every Python environment already has.

Development dependencies (`pytest`, `pytest-cov`, `ruff`, `mypy`, `build`) stay
in the `dev` extra, so `pip install modelcard-lint` in a locked-down CI image
pulls nothing.

## Consequences

**Good**

- Installation is a single wheel with no resolver work; the tool runs on any
  Python 3.11+ interpreter, including slim containers.
- The whole audit surface is this repository. A reviewer can read every line the
  gate executes.
- Tests have no third-party test doubles to keep current.

**Bad**

- Hand-rolled validation means the JSON type table is maintained by hand; a new
  field is a one-line edit, but nothing generates it automatically.
- Users who would prefer YAML policies have to convert. This was accepted: a
  policy is a dozen lines and JSON is valid everywhere YAML is expected in CI.
- No CLI sugar (subcommands, colour, shell completion) comes for free.

## Alternatives considered

| Option | Rejected because |
| ------ | ---------------- |
| `pyyaml` for policies | Adds a dependency (and a parser class of bug) to read a dozen keys. |
| `jsonschema` for the contract | Powerful, but the contract is a flat table; the library would be larger than the rules it validates. |
| `click`/`typer` for the CLI | Comfort, not correctness; `argparse` already satisfies the exit-code contract. |
| `pydantic` for manifest parsing | Runtime validation is our job, and we want findings as data, not exceptions. |

## Follow-up

Revisit only if the rule set grows to the point where the type table stops being
reviewable by hand -- at that point a schema *generator* (dev-time, not runtime)
becomes the better answer.
