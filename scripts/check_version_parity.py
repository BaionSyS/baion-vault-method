#!/usr/bin/env python3
# check_version_parity -- verify release-version and method-version coherence
# Spec: SPEC.md section 3 (vault.toml contract); CHANGELOG.md release records
# Two version tracks, deliberately distinct since v0.2.0: the RELEASE version
# names what ships from this repository (checker, lab, docs); the METHOD
# version names the specification contract that vaults declare conformance to.
# They were one string at v0.1.0 only by coincidence -- the checker and the
# spec were born together. Welding them broke at v0.2.0: bumping templates'
# method_version out of the 0.1.x series makes bvm-lint reject its own
# templates (BVM002, lint.py series gate).
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from typing import Any

# The method series bvm-lint accepts (lint.py: semver_tuple(...)[:2] gate).
# A new series requires a corresponding schema and checker contract, per
# SPEC.md section 3 -- bump this only alongside that contract work.
METHOD_SERIES = (0, 1)


def read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def matched_version(path: Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"))
    return match.group(1) if match else "<missing>"


def collect_release_versions(root: Path) -> tuple[str, dict[str, str]]:
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
        "CHANGELOG.md": matched_version(
            root / "CHANGELOG.md",
            r"(?m)^## \[([^]\n]+)\]",
        ),
    }
    return expected, values


def collect_method_versions(root: Path) -> tuple[str, dict[str, str]]:
    expected = matched_version(
        root / "SPEC.md",
        r"(?m)^\*\*Version:\*\*\s*([^\s]+)\s*$",
    )
    values = {
        "SPEC.md": expected,
        "examples/tutorial-vault/vault.toml": str(
            read_toml(root / "examples/tutorial-vault/vault.toml").get("method_version", "<missing>")
        ),
        "templates/vault.toml": str(
            read_toml(root / "templates/vault.toml").get("method_version", "<missing>")
        ),
    }
    return expected, values


def in_method_series(version: str) -> bool:
    parts = version.split(".")
    try:
        return (int(parts[0]), int(parts[1])) == METHOD_SERIES
    except (IndexError, ValueError):
        return False


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    try:
        release_expected, release_values = collect_release_versions(root)
        method_expected, method_values = collect_method_versions(root)
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        print(f"VERSION PARITY FAIL (cannot read release metadata: {exc})")
        return 1

    failures = [
        f"- release: {path}: {value} (expected {release_expected})"
        for path, value in release_values.items()
        if value != release_expected
    ]
    failures += [
        f"- method: {path}: {value} (expected {method_expected})"
        for path, value in method_values.items()
        if value != method_expected
    ]
    if not in_method_series(method_expected):
        series = ".".join(str(part) for part in METHOD_SERIES)
        failures.append(
            f"- method: SPEC.md declares {method_expected}, outside the {series}.x "
            f"series bvm-lint accepts (BVM002 contract)"
        )

    if failures:
        print("VERSION PARITY FAIL")
        for failure in failures:
            print(failure)
        return 1
    print(f"VERSION PARITY PASS (release {release_expected}, method {method_expected})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
