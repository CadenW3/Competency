# Rule reference

Every rule has a **stable id**. Ids are never renumbered or reused: a downstream
policy that overrides `MCL004` must keep meaning the same thing forever. The
`--list-rules` flag prints this table from the code, and
`tests/test_docs.py` fails if this page drifts from it.

| Id | Default severity | Summary | Fires when | Field(s) |
| -- | ---------------- | ------- | ---------- | -------- |
| MCL001 | error | required metadata is present and non-empty | a policy-required dotted path is absent, `null`, or an empty string/list/object | any `required_fields` entry |
| MCL002 | error | fields match their declared JSON type | a present field has the wrong JSON kind (for example `version: 1.4` is a number, not a string) | `schema_version`, `name`, `version`, `license`, `description`, `owner`, `intended_use`, `out_of_scope_use`, `limitations`, `training_data`, `evaluation`, `review` |
| MCL003 | error | version is semantic (MAJOR.MINOR.PATCH) | `version` is not SemVer 2.0.0 (`1.4.2`, `1.4.2-rc.1` and `1.4.2+build.5` are accepted) | `version` |
| MCL004 | warning | license is a recognised identifier | the license id is not in the policy's `known_licenses` (case-insensitive) | `license` |
| MCL005 | error | personal data has a documented de-identification step | `training_data.contains_pii` is `true` and `training_data.deidentification` is missing or empty | `training_data.contains_pii`, `training_data.deidentification` |
| MCL006 | warning | owner contact is an email address | `owner.contact` is present but is not email-shaped | `owner.contact` |
| MCL007 | warning | policy-required metrics are reported | a metric listed in the policy's `required_metrics` is missing from `evaluation.metrics` | `evaluation.metrics` |
| MCL008 | error | review date is valid and not overdue | `review.due` is not an ISO-8601 date, or falls before the reference date | `review.due` |
| MCL009 | warning | no unknown top-level fields | a top-level key is not in the policy's `known_fields` (usually a typo that silently does nothing) | document root |
| MCL010 | warning | training data provenance is resolvable | `training_data.source` is neither a URL (`https://`, `s3://`, ...) nor an `org/dataset` identifier | `training_data.source` |
| MCL011 | warning | limitations entries are actionable | a `limitations` entry is shorter than 10 characters, so it cannot inform a reviewer | `limitations[]` |

## Severity vocabulary

| Severity | Fails CI by default | Fails under `--strict` | Fails under `--max-warnings` |
| -------- | ------------------ | ---------------------- | ---------------------------- |
| `error` | yes | yes | yes |
| `warning` | no | yes | yes, once the budget is exceeded |
| `info` | no | no | no |

`info` exists so future rules can report context (for example "this card is 18
months old") without breaking anyone's build. No rule emits `info` today.

## Overriding severity

```json
{
  "severity_overrides": {
    "MCL009": "error",
    "MCL011": "info"
  }
}
```

Overrides are applied per rule, before `--strict` is considered, so
`--strict` still means "everything blocks" regardless of policy.

## Reference date

MCL008 compares `review.due` against "today". CI must be reproducible, so the
reference date is injectable: the library takes `today=` and the CLI takes
`--today YYYY-MM-DD`. Pinning it means a card cannot start failing at midnight
in a different timezone.
