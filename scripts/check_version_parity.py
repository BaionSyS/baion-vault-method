#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from typing import Any


def read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def matched_version(path: Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"))
    return match.group(1) if match else "<missing>"


def collect_versions(root: Path) -> tuple[str, dict[str, str]]:
    expected = str(read_toml(root / "pyproject.toml")["project"]["version"])
    values = {
        "pyproject.toml": expected,
        "src/bvm_lint/__init__.py": matched_version(
            root / "src/bvm_lint/__init__.py",
            r'__version__\s*=\s*"([^"]+)"',
        ),
        "CITATION.cff": matched_version(
            root / "CITATION.cff",
            r"(?m)^version:\s*['\"]?([^\s'\"]+)['\"]?\s*$",
        ),
        "README.md": matched_version(
            root / "README.md",
            r"shields\.io/badge/version-(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)-[0-9A-Fa-f]+",
        ),
        "SPEC.md": matched_version(
            root / "SPEC.md",
            r"(?m)^\*\*Version:\*\*\s*([^\s]+)\s*$",
        ),
        "CHANGELOG.md": matched_version(
            root / "CHANGELOG.md",
            r"(?m)^## \[([^]\n]+)\]",
        ),
        "examples/tutorial-vault/vault.toml": str(
            read_toml(root / "examples/tutorial-vault/vault.toml").get("method_version", "<missing>")
        ),
        "templates/vault.toml": str(
            read_toml(root / "templates/vault.toml").get("method_version", "<missing>")
        ),
    }
    return expected, values


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    try:
        expected, values = collect_versions(root)
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        print(f"VERSION PARITY FAIL (cannot read release metadata: {exc})")
        return 1

    failures = [f"{path}: {value}" for path, value in values.items() if value != expected]
    if failures:
        print(f"VERSION PARITY FAIL (expected {expected})")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"VERSION PARITY PASS ({expected})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
