"""Rule-level tests.

Each test mutates exactly one field of the reference card and asserts on the
findings for a single rule id, which keeps a failure unambiguous about which
rule regressed.
"""

from __future__ import annotations

from datetime import date

import pytest

from modelcard_lint.manifest import MISSING
from modelcard_lint.policy import Policy
from modelcard_lint.rules import RULES, RULES_BY_ID
from modelcard_lint.types import Severity


def findings_for(report, rule_id: str):
    return [finding for finding in report.findings if finding.rule_id == rule_id]


def test_reference_card_is_clean(make_card, card_data, lint_card) -> None:
    assert lint_card(make_card(card_data)).findings == ()


def test_rule_registry_is_well_formed() -> None:
    ids = [rule.id for rule in RULES]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))
    assert all(rule_id.startswith("MCL") for rule_id in ids)
    assert set(RULES_BY_ID) == set(ids)
    assert all(rule.summary for rule in RULES)


@pytest.mark.parametrize(
    "dotted",
    [
        "schema_version",
        "name",
        "version",
        "license",
        "owner.name",
        "owner.contact",
        "intended_use",
        "limitations",
        "training_data.source",
        "evaluation.metrics",
    ],
)
def test_mcl001_missing_required_field(dotted, make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, dotted, MISSING))
    found = findings_for(lint_card(card), "MCL001")
    assert [finding.path for finding in found] == [dotted]
    assert found[0].severity is Severity.ERROR


def test_mcl001_treats_empty_values_as_blank(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "limitations", []))
    assert findings_for(lint_card(card), "MCL001")


@pytest.mark.parametrize(
    ("dotted", "value", "expected"),
    [
        ("schema_version", 1.0, "expected string, got float"),
        ("owner", "Caden", "expected object, got str"),
        ("limitations", "none", "expected array, got str"),
        ("version", True, "expected string, got boolean"),
    ],
)
def test_mcl002_type_contract(
    dotted, value, expected, make_card, card_data, mutate, lint_card
) -> None:
    card = make_card(mutate(card_data, dotted, value))
    found = findings_for(lint_card(card), "MCL002")
    assert [finding.message for finding in found] == [expected]


def test_mcl003_rejects_non_semver(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "version", "1.4"))
    found = findings_for(lint_card(card), "MCL003")
    assert found[0].severity is Severity.ERROR
    assert "not a semantic version" in found[0].message


@pytest.mark.parametrize("version", ["0.1.0", "1.4.2-rc.1", "2.0.0+build.5"])
def test_mcl003_accepts_semver(version, make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "version", version))
    assert findings_for(lint_card(card), "MCL003") == []


def test_mcl004_flags_unknown_license(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "license", "PatentPending-1.0"))
    found = findings_for(lint_card(card), "MCL004")
    assert found[0].severity is Severity.WARNING


def test_mcl005_requires_deidentification_for_pii(make_card, card_data, mutate, lint_card) -> None:
    card_data["training_data"]["contains_pii"] = True
    card = make_card(card_data)
    found = findings_for(lint_card(card), "MCL005")
    assert found[0].path == "training_data.deidentification"
    assert found[0].severity is Severity.ERROR


def test_mcl005_passes_when_deidentification_documented(
    make_card, card_data, mutate, lint_card
) -> None:
    mutate(card_data, "training_data.contains_pii", True)
    mutate(card_data, "training_data.deidentification", "k-anonymity on zip codes")
    assert findings_for(lint_card(make_card(card_data)), "MCL005") == []


def test_mcl005_ignores_blank_deidentification(make_card, card_data, mutate, lint_card) -> None:
    mutate(card_data, "training_data.contains_pii", True)
    mutate(card_data, "training_data.deidentification", "")
    assert findings_for(lint_card(make_card(card_data)), "MCL005")


def test_mcl006_flags_non_email_contact(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "owner.contact", "risk-team"))
    found = findings_for(lint_card(card), "MCL006")
    assert "is not an email address" in found[0].message


def test_mcl007_requires_policy_metrics(make_card, card_data, lint_card) -> None:
    card = make_card(card_data)
    policy = Policy(required_metrics=("accuracy", "roc_auc"))
    found = findings_for(lint_card(card, policy), "MCL007")
    assert len(found) == 1
    assert "roc_auc" in found[0].message


def test_mcl007_ignores_non_list_metrics(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "evaluation.metrics", "accuracy"))
    assert findings_for(lint_card(card, Policy(required_metrics=("accuracy",))), "MCL007") == []


def test_mcl008_rejects_malformed_review_date(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "review.due", "31/01/2027"))
    found = findings_for(lint_card(card), "MCL008")
    assert "not an ISO-8601 date" in found[0].message


def test_mcl008_flags_overdue_review(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "review.due", "2026-01-01"))
    found = findings_for(lint_card(card, today=date(2026, 1, 15)), "MCL008")
    assert "overdue" in found[0].message


def test_mcl008_accepts_future_review(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "review.due", "2026-02-01"))
    assert findings_for(lint_card(card, today=date(2026, 1, 15)), "MCL008") == []


def test_mcl008_ignores_absent_review(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "review", MISSING))
    assert findings_for(lint_card(card), "MCL008") == []


def test_mcl009_flags_unknown_top_level_field(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "traning_data_version", "3"))
    found = findings_for(lint_card(card), "MCL009")
    assert found[0].path == "traning_data_version"
    assert found[0].severity is Severity.WARNING


def test_mcl010_accepts_url_and_dataset_id(make_card, card_data, mutate, lint_card) -> None:
    for source in ("https://example.org/data.csv", "imdb/plain_text", "s3://bucket/key"):
        mutate(card_data, "training_data.source", source)
        assert findings_for(lint_card(make_card(card_data)), "MCL010") == [], source


def test_mcl010_flags_unresolvable_source(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "training_data.source", "internal share drive"))
    found = findings_for(lint_card(card), "MCL010")
    assert "neither a URL nor an 'org/dataset' identifier" in found[0].message


def test_mcl011_flags_stub_limitations(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "limitations", ["none", "only trained on CIFAR-10"]))
    found = findings_for(lint_card(card), "MCL011")
    assert found[0].path == "limitations[0]"


def test_mcl011_ignores_non_list_limitations(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "limitations", "none"))
    assert findings_for(lint_card(card), "MCL011") == []


def test_mcl011_ignores_non_string_entries(make_card, card_data, mutate, lint_card) -> None:
    card = make_card(mutate(card_data, "limitations", [42]))
    assert findings_for(lint_card(card), "MCL011") == []
