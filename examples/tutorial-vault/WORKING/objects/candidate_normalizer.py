"""Candidate normalizer with an independent code path for the tutorial probe."""
from __future__ import annotations

import json
from typing import Any


class CandidateDuplicateKeyError(ValueError):
    pass


class UniqueObjectBuilder:
    def __call__(self, pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for item in pairs:
            key, value = item
            if key in output:
                raise CandidateDuplicateKeyError(key)
            output.update({key: value})
        return output


def normalize(text: str) -> str:
    decoder = json.JSONDecoder(object_pairs_hook=UniqueObjectBuilder())
    value = decoder.decode(text)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
