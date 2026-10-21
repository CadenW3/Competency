"""Tests for policy loading and validation."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from modelcard_lint.policy import (
    DEFAULT_KNOWN_FIELDS,
    DEFAULT_REQUIRED_FIELDS,
    Policy,
    PolicyError,
    load_policy,
)
from modelcard_lint.types import Severity


def _write(tmp_path: Path, payload: object, name: str = "policy.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_default_policy_exposes_stock_values() -> None:
    policy = Policy()
    assert policy.required_fields == DEFAULT_REQUIRED_FIELDS
    assert "owner.contact" in policy.required_fields
    assert policy.known_fields == DEFAULT_KNOWN_FIELDS
    assert policy.required_metrics == ()
    assert policy.strict is False
    assert policy.severity_overrides == {}


def test_severity_for_prefers_override() -> None:
    policy = Policy(severity_overrides={"MCL004": Severity.ERROR})
    assert policy.severity_for("MCL004", Severity.WARNING) is Severity.ERROR
    assert policy.severity_for("MCL001", Severity.ERROR) is Severity.ERROR


def test_from_mapping_applies_overrides() -> None:
    policy = Policy.from_mapping(
        {
            "required_fields": ["name"],
            "required_metrics": ["accuracy"],
            "severity_overrides": {"MCL009": "error"},
            "strict": True,
        }
    )
    assert policy.required_fields == ("name",)
    assert policy.required_metrics == ("accuracy",)
    assert policy.severity_overrides["MCL009"] is Severity.ERROR
    assert policy.strict is True
    assert policy.known_fields == DEFAULT_KNOWN_FIELDS


def test_from_mapping_rejects_unknown_key() -> None:
    with pytest.raises(PolicyError, match="unknown key"):
        Policy.from_mapping({"required_feilds": ["name"]})


def test_from_mapping_rejects_non_string_list() -> None:
    with pytest.raises(PolicyError, match="must be a list of non-empty strings"):
        Policy.from_mapping({"required_fields": "name"})


def test_from_mapping_rejects_empty_entries() -> None:
    with pytest.raises(PolicyError, match="must be a list of non-empty strings"):
        Policy.from_mapping({"required_fields": [""]})


def test_from_mapping_rejects_non_object_overrides() -> None:
    with pytest.raises(PolicyError, match="'severity_overrides' must be an object"):
        Policy.from_mapping({"severity_overrides": ["MCL001"]})


def test_from_mapping_rejects_non_string_severity() -> None:
    with pytest.raises(PolicyError, match="must be a string"):
        Policy.from_mapping({"severity_overrides": {"MCL001": 2}})


def test_from_mapping_rejects_unknown_severity() -> None:
    with pytest.raises(PolicyError, match="unknown severity"):
        Policy.from_mapping({"severity_overrides": {"MCL001": "fatal"}})


def test_from_mapping_rejects_non_boolean_strict() -> None:
    with pytest.raises(PolicyError, match="'strict' must be a boolean"):
        Policy.from_mapping({"strict": "yes"})


def test_load_policy_reads_document(tmp_path: Path) -> None:
    path = _write(tmp_path, {"required_metrics": ["accuracy"]})
    assert load_policy(path).required_metrics == ("accuracy",)


def test_load_policy_missing_file(tmp_path: Path) -> None:
    with pytest.raises(PolicyError, match="policy not found"):
        load_policy(tmp_path / "absent.json")


def test_load_policy_unreadable_path(tmp_path: Path) -> None:
    with pytest.raises(PolicyError, match="cannot read policy"):
        load_policy(tmp_path)


def test_load_policy_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("[", encoding="utf-8")
    with pytest.raises(PolicyError, match="invalid JSON"):
        load_policy(path)


def test_load_policy_requires_object(tmp_path: Path) -> None:
    path = _write(tmp_path, ["name"])
    with pytest.raises(PolicyError, match="must be a JSON object"):
        load_policy(path)


def test_policy_is_immutable() -> None:
    policy = Policy()
    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.strict = True
