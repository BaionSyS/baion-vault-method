#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

CODE_RE = re.compile(r"`(BVM\d{3})`")


class DuplicateKeyError(ValueError):
    pass


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError(f"nonstandard JSON constant: {value}")


def load_strict_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=strict_object,
        parse_constant=reject_constant,
    )


def difference(label: str, expected: set[str], actual: set[str]) -> str | None:
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if not missing and not extra:
        return None
    parts: list[str] = []
    if missing:
        parts.append("missing " + ", ".join(missing))
    if extra:
        parts.append("extra " + ", ".join(extra))
    return f"{label}: " + "; ".join(parts)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    sys.path.insert(0, str(root / "src"))

    from bvm_lint.codes import EXPLANATIONS  # pylint: disable=import-outside-toplevel

    failures: list[str] = []
    diagnostics_path = root / "schemas/diagnostics.json"
    docs_path = root / "docs/linter-reference.md"

    try:
        diagnostics = load_strict_json(diagnostics_path)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
        failures.append(f"cannot load {diagnostics_path.relative_to(root)}: {exc}")
        diagnostics = None

    if diagnostics is not None:
        if not isinstance(diagnostics, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in diagnostics.items()
        ):
            failures.append("schemas/diagnostics.json must be a string-to-string object")
        elif diagnostics != EXPLANATIONS:
            expected_keys = set(EXPLANATIONS)
            actual_keys = set(diagnostics)
            key_diff = difference("diagnostic code set", expected_keys, actual_keys)
            if key_diff:
                failures.append(key_diff)
            for code in sorted(expected_keys & actual_keys):
                if diagnostics[code] != EXPLANATIONS[code]:
                    failures.append(f"{code}: schemas/diagnostics.json description differs from code")

    try:
        docs_codes = set(CODE_RE.findall(docs_path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError) as exc:
        failures.append(f"cannot read {docs_path.relative_to(root)}: {exc}")
    else:
        docs_diff = difference("docs/linter-reference.md code set", set(EXPLANATIONS), docs_codes)
        if docs_diff:
            failures.append(docs_diff)

    if failures:
        print("DIAGNOSTIC PARITY CHECK FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"DIAGNOSTIC PARITY CHECK PASS ({len(EXPLANATIONS)} codes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
