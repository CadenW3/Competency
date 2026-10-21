# ADR 0002 -- Severity model and the exit-code contract

- **Status:** accepted
- **Date:** 2026-10-15
- **Deciders:** Caden Wate

## Context

A linter that gates CI has to answer one question unambiguously: *when does this
run fail?* The naive answer ("any finding fails") makes the tool unusable on a
real codebase, because every new rule immediately breaks everybody. The other
extreme ("report only") makes it decorative.

The tool also has to distinguish "your card has problems" from "I could not do
my job" -- a CI gate that fails the same way for a missing file and for a real
violation sends people to the wrong log line.

## Decision

Three severities, one exit code per outcome:

| Severity | Meaning | Blocks by default |
| -------- | ------- | ----------------- |
| `error` | The card cannot be relied on. Always blocking. | yes |
| `warning` | A smell or an unknown; blocking only when the caller asks. | no |
| `info` | Context for a human. Never blocks. | no |

Exit codes (owned by `engine.exit_code`, not by the CLI):

| Code | Meaning |
| ---- | ------- |
| `0` | No blocking findings. |
| `1` | A blocking finding exists (error, warning under `--strict`, or warnings over `--max-warnings`). |
| `2` | Usage error: unreadable manifest, invalid policy, bad arguments. |

Two escalation switches, both explicit:

- `--strict` promotes every warning to an error before evaluation. It is the
  "we are adopting this on a clean project" switch.
- `--max-warnings N` allows a warning budget, then blocks. It is the
  "ratchet this down over time" switch -- the same shape as `eslint`'s flag, so
  it needs no explanation.

`info` is reserved and currently unused: it exists so a future rule can add
context without forcing a decision about blocking.

## Consequences

**Good**

- A new rule can ship at `warning` and be promoted later, which makes adoption
  incremental instead of a flag day.
- `2` for usage errors means a broken pipeline is obvious from the exit code
  alone, before reading any output.
- The contract is a pure function, so it is tested directly
  (`tests/test_engine.py`) and documented once, here and in the README.

**Bad**

- Three severities plus two escalation switches is more configuration than a
  single boolean. It is the minimum that supports incremental adoption.
- Tooling that only understands "non-zero means findings" will read `2` as
  findings. Documented in the README exit-code table so nobody is surprised.

## Alternatives considered

| Option | Rejected because |
| ------ | ---------------- |
| Fail on any finding | Unusable for adoption; every new rule is a breaking change. |
| Never fail (report only) | Not a gate; the card would still rot. |
| Exit `1` for usage errors too | Loses the distinction between "bad card" and "bad invocation" that CI logs rely on. |
| Numeric severity levels | Familiar from logging, but invites "severity 7 of 10" bikeshedding; three named levels map to a decision. |
