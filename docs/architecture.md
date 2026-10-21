# Architecture

## Layering

```
types.py     Severity, Finding, Report          (leaf: no internal imports)
manifest.py  ModelCard, load_manifest           (I/O: JSON only)
policy.py    Policy, load_policy                (I/O: JSON only)
rules.py     Rule records + pure checks         (depends on manifest, policy, types)
engine.py    lint(), exit_code()                (depends on rules, types)
report.py    text / json / github renderers     (depends on types only)
cli.py       argparse, wiring, exit codes       (depends on everything above)
```

Dependencies point one way only: `types` <- `manifest`/`policy`/`report` <-
`rules` <- `engine` <- `cli`. There are no cycles, and `types.py` imports nothing
from the package, which is what lets every other module share the value records.

## Data flow

```
manifest file --load_manifest--> ModelCard --lint(policy, today)--> Report --format_*--> stdout
                                     ^                                  |
                                rules RULES                       exit_code()
```

1. `load_manifest` parses JSON and preserves the raw mapping. It does **not**
   validate the schema -- that is the rules' job.
2. `lint` runs every rule in `RULES`, applies per-rule severity overrides and
   `--strict`, then sorts findings deterministically.
3. A reporter renders the report. Reporters are pure functions of `Report`.
4. `exit_code` maps the report onto `0 / 1 / 2`.

## Invariants

These are the properties the test suite exists to protect.

1. **Rules are pure.** A rule receives `(ModelCard, Policy, date)` and returns
   findings. It never reads the clock, the environment or the filesystem, so the
   whole rule set is testable without mocks and CI output is reproducible.
2. **Output is deterministic.** Findings are sorted by `(path, rule_id, message)`
   before they reach a reporter. Two runs over the same input produce
   byte-identical output, which is what makes `--format github` safe in CI.
3. **Ids are stable.** `MCL00N` never changes meaning. Policies in other
   repositories depend on this.
4. **No execution, no network.** The tool parses JSON and nothing else. It never
   imports, deserialises or runs anything referenced by a manifest.
5. **The exit code is owned by `engine.exit_code`.** No module calls `sys.exit`
   except the `__main__` entry point, so every gate decision is unit-testable.

## Adding a rule

1. Write a check function with the `RuleCheck` signature in `rules.py`. Keep it
   pure and give it a docstring naming its rule id and the field it reads.
2. Append a `Rule(...)` entry to `RULES` with the next free id.
3. Add the row to `docs/rules.md` (a test fails if you forget).
4. Add a test in `tests/test_rules.py` that mutates exactly one field of the
   reference card.
5. Add a CHANGELOG entry under `### Added`.

## Testing strategy

| Layer | Test file | Approach |
| ----- | --------- | -------- |
| types | `test_types.py` | pure unit tests, no I/O |
| manifest / policy | `test_manifest.py`, `test_policy.py` | `tmp_path` files plus every error branch |
| rules | `test_rules.py` | one mutation per test, reference card from `examples/good-card.json` |
| engine | `test_engine.py` | ordering, overrides, strict mode, exit-code contract |
| reporters | `test_report.py` | exact strings, JSON round-trip, annotation escaping |
| CLI | `test_cli.py` | in-process `main([...])`, asserted exit codes and streams |
| docs | `test_docs.py` | metadata and documentation must not drift from code |

Coverage gate: 95% with branch coverage, enforced locally and in CI by the same
`pyproject.toml` options so the two cannot drift either.
