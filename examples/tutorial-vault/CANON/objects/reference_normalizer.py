"""Canonical normalizer used by the fictional tutorial project."""
from __future__ import annotations

import json
from typing import Any


class DuplicateKeyError(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object key: {key}")
        result[key] = value
    return result


def normalize(text: str) -> str:
    value = json.loads(text, object_pairs_hook=_unique_object)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
