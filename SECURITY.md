# Security policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.2.x   | yes       |
| 0.1.x   | security fixes only |
| < 0.1   | no        |

## Reporting a vulnerability

Please **do not** open a public issue for a security problem.

1. Open a private advisory:
   <https://github.com/CadenW3/Competency/security/advisories/new>
2. Or email the maintainer listed in `pyproject.toml`.

Include the version, a minimal manifest that reproduces the problem, and what
you expected to happen. You can expect an acknowledgement within 72 hours and a
decision (accept / needs-info / decline) within seven days.

## Scope

`modelcard-lint` is a static reader. It parses JSON, compares strings and
numbers, and writes a report. Its security posture rests on that being all it
does.

**In scope**

- Any input that makes the linter crash, hang, or exit with a code outside the
  documented `0`/`1`/`2` contract.
- Any path where a manifest causes code execution, file writes outside the
  manifest it was given, or a network request.
- A policy file that can silently disable a rule without an error.
- Report output that can be used to inject terminal escape sequences or GitHub
  Actions workflow commands (for example a crafted `message` containing `::error`).
- Supply-chain issues: the published package having a runtime dependency it
  should not have.

**Out of scope**

- A malicious model card being *reported* as clean when it is semantically
  dishonest. The linter checks structure and metadata, not truthfulness.
- Findings that are merely inconvenient, or a rule you disagree with (open an
  issue instead).
- Denial of service against your own machine from a pathologically large
  manifest beyond what a normal CI timeout handles.

## Design guarantees

1. **No deserialisation.** The tool never `eval`s, `exec`s, imports or unpickles
   anything. JSON parsing is the only input path.
2. **No network access.** Nothing in `src/modelcard_lint` opens a socket.
3. **No writes.** The linter only writes to stdout and stderr.
4. **Escaped output.** The GitHub reporter escapes `%`, CR and LF before emitting
   workflow commands, and `tests/test_report.py` pins that behaviour.

## Dependency policy

There are no runtime dependencies by design
([ADR 0001](docs/adr/0001-zero-runtime-dependencies.md)). Development
dependencies are pinned to major ranges and updated by Dependabot, so a
compromised lint tool cannot reach users of the wheel.
