"""Tests for the manifest loader."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from modelcard_lint.manifest import MISSING, ManifestError, load_manifest


def _write(tmp_path: Path, payload: object, name: str = "card.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_manifest_returns_card_for_json_object(tmp_path: Path) -> None:
    path = _write(tmp_path, {"name": "demo"})
    card = load_manifest(path)
    assert card.raw == {"name": "demo"}
    assert card.path == path


def test_load_manifest_accepts_str_path(tmp_path: Path) -> None:
    path = _write(tmp_path, {"name": "demo"})
    assert load_manifest(str(path)).raw == {"name": "demo"}


def test_missing_file_raises_manifest_error(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="manifest not found"):
        load_manifest(tmp_path / "absent.json")


def test_unreadable_path_raises_manifest_error(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="cannot read manifest"):
        load_manifest(tmp_path)


def test_invalid_json_reports_position(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ManifestError, match=r"broken\.json:1:2: invalid JSON"):
        load_manifest(path)


def test_non_object_document_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, ["a", "b"])
    with pytest.raises(ManifestError, match="must be a JSON object, got list"):
        load_manifest(path)


def test_get_walks_nested_mappings(make_card, card_data) -> None:
    card = make_card(card_data)
    assert card.get("owner.name") == "Caden Wate"
    assert card.get("training_data.contains_pii") is False


def test_get_returns_missing_sentinel_for_unknown_path(make_card, card_data) -> None:
    card = make_card(card_data)
    assert card.get("owner.nickname") is MISSING
    assert card.get("nope.not.here") is MISSING


def test_get_distinguishes_null_from_absent(make_card, card_data) -> None:
    card = make_card(card_data)
    card.raw["owner"]["nickname"] = None
    assert card.get("owner.nickname") is None
    assert card.get("owner.nickname") is not MISSING
    assert card.get("owner.other", "fallback") == "fallback"


def test_get_traverses_non_mapping_values(make_card, card_data) -> None:
    card = make_card(card_data)
    assert card.get("name.deeper") is MISSING


def test_has_reports_presence_and_null(make_card, card_data) -> None:
    card = make_card(card_data)
    assert card.has("version") is True
    assert card.has("owner.missing") is False
    card.raw["owner"]["nickname"] = None
    assert card.has("owner.nickname") is False


def test_model_card_is_immutable(make_card, card_data) -> None:
    card = make_card(card_data)
    with pytest.raises(dataclasses.FrozenInstanceError):
        card.path = Path("other.json")  # type: ignore[misc]
