"""Loading model-card manifests into an immutable, dotted-path-addressable view.

The loader is deliberately dumb: it parses JSON and preserves the raw mapping,
because the schema is owned by the :mod:`modelcard_lint.rules` layer. A loader
that also enforced the schema would duplicate rule logic and make error
messages harder to trace back to a single rule id.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MISSING = object()
"""Sentinel returned by :meth:`ModelCard.get` when a dotted path is absent."""


class ManifestError(ValueError):
    """Raised when a manifest cannot be read or parsed as a JSON object."""


@dataclass(frozen=True, slots=True)
class ModelCard:
    """An immutable view over one parsed model-card manifest.

    Attributes:
        path: Location the manifest was read from (or the synthetic path used
            by tests and in-memory callers).
        raw: The parsed JSON object, preserved verbatim.
    """

    path: Path
    raw: Mapping[str, Any]

    def get(self, dotted: str, default: Any = MISSING) -> Any:
        """Return the value stored at a dotted ``path.to.field`` location.

        Args:
            dotted: Dotted path such as ``"training_data.source"``.
            default: Value returned when the path is missing. Defaults to the
                module-level :data:`MISSING` sentinel so callers can tell an
                absent field apart from an explicit ``null``.

        Returns:
            The value at ``dotted``, or ``default`` when any segment is absent.
        """
        node: Any = self.raw
        for part in dotted.split("."):
            if not isinstance(node, Mapping) or part not in node:
                return default
            node = node[part]
        return node

    def has(self, dotted: str) -> bool:
        """Return whether ``dotted`` resolves to a present value.

        Args:
            dotted: Dotted path such as ``"owner.contact"``.

        Returns:
            ``True`` when the path exists and its value is not ``None``.
        """
        return self.get(dotted) is not MISSING and self.get(dotted) is not None


def load_manifest(path: str | Path) -> ModelCard:
    """Read ``path`` and return the parsed :class:`ModelCard`.

    Args:
        path: Path to a JSON model-card manifest.

    Returns:
        The parsed card.

    Raises:
        ManifestError: If the file is missing, unreadable, not valid UTF-8, not
            valid JSON, or not a JSON object at the top level.
    """
    manifest_path = Path(path)
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ManifestError(f"{manifest_path}: manifest not found") from exc
    except OSError as exc:
        raise ManifestError(f"{manifest_path}: cannot read manifest ({exc.strerror})") from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ManifestError(
            f"{manifest_path}:{exc.lineno}:{exc.colno}: invalid JSON ({exc.msg})"
        ) from exc

    if not isinstance(data, dict):
        raise ManifestError(
            f"{manifest_path}: manifest must be a JSON object, got {type(data).__name__}"
        )
    return ModelCard(path=manifest_path, raw=data)
